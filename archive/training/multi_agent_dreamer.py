"""
multi_agent_dreamer.py — 다중 에이전트 독립적 World Model 학습 시스템

투수와 타자 각각에 대해 완전히 분리된 뇌(RSSM + Actor + Critic)를 가집니다.
시뮬레이션에서 얻은 (pitcher_obs, batter_obs)를 각각 자신의 Replay Buffer에 저장하고
독립적으로 자신의 모델을 학습하여 치팅(전지적 정보 공유)을 방지합니다.
"""

import os
import time
import datetime
import cv2
import numpy as np
from pathlib import Path
from collections import deque
from typing import Dict, List, Tuple, Optional
from torch.utils.tensorboard import SummaryWriter
import shutil

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from envs.multi_agent_env import MultiAgentBaseballEnv, EnvConfig
from training.multi_agent_world_model import (
    BaseballVisionRSSM, compute_vision_world_model_loss, symexp
)
from training.world_model_trainer import LatentActor, LatentCritic
from training.logger import DashboardLogger


class MultiAgentReplayBuffer:
    def __init__(self, capacity: int = 5000, seq_len: int = 50):
        self.capacity = capacity
        self.seq_len = seq_len
        self.episodes = []
        self.write_ptr = 0
        self.size = 0

    def add_episode(self, episode: Dict):
        """
        episode = {
            "pitcher": {"obs_seq": {...}, "action_seq": [...], "reward_seq": [...], "done_seq": [...]},
            "batter":  {"obs_seq": {...}, "action_seq": [...], "reward_seq": [...], "done_seq": [...]},
            "fielder": {"obs_seq": {...}, "action_seq": [...], "reward_seq": [...], "done_seq": [...]},
        }
        """
        if len(self.episodes) < self.capacity:
            self.episodes.append(episode)
        else:
            self.episodes[self.write_ptr] = episode
        self.write_ptr = (self.write_ptr + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, agent_name: str, batch_size: int) -> Optional[Dict[str, torch.Tensor]]:
        if self.size < batch_size:
            return None

        obs_batch = {"vision": [], "proprioception": []}
        act_batch, rew_batch, done_batch = [], [], []

        indices = np.random.choice(self.size, batch_size, replace=True)

        for idx in indices:
            ep = self.episodes[idx][agent_name]
            T = len(ep["action_seq"])
            start = np.random.randint(0, max(1, T - self.seq_len + 1))
            end = start + self.seq_len

            def _slice(arr):
                if len(arr) >= end:
                    return arr[start:end]
                pad_len = end - len(arr)
                reps = (pad_len,) + (1,) * (arr.ndim - 1)
                padded = np.concatenate([arr[start:], np.tile(arr[-1:], reps)], axis=0)
                return padded[:self.seq_len]

            obs_batch["vision"].append(_slice(ep["obs_seq"]["vision"]))
            obs_batch["proprioception"].append(_slice(ep["obs_seq"]["proprioception"]))
            act_batch.append(_slice(ep["action_seq"]))
            rew_batch.append(_slice(ep["reward_seq"]))
            done_batch.append(_slice(ep["done_seq"]))

        # Image Data: shape is (B, T, 64, 64, 3) -> convert to (B, T, 3, 64, 64) and normalize
        vision_np = np.array(obs_batch["vision"])
        vision_tensor = torch.tensor(vision_np, dtype=torch.float32).permute(0, 1, 4, 2, 3) / 255.0

        batch = {
            "obs": {
                "vision": vision_tensor,
                "proprioception": torch.tensor(np.array(obs_batch["proprioception"]), dtype=torch.float32)
            },
            "actions": torch.tensor(np.array(act_batch), dtype=torch.float32),
            "rewards": torch.tensor(np.array(rew_batch), dtype=torch.float32),
            "dones": torch.tensor(np.array(done_batch), dtype=torch.float32),
        }
        return batch


class SingleAgentBrain:
    """Pitcher 또는 Batter 한 명분의 뇌 (RSSM + Actor + Critic)."""
    def __init__(self, name: str, prop_dim: int, action_dim: int, device: torch.device):
        self.name = name
        self.device = device
        self.config = {
            "name": name,
            "prop_dim": prop_dim,
            "action_dim": action_dim
        }
        self.rssm = BaseballVisionRSSM(prop_dim, action_dim).to(device)
        self.actor = LatentActor(self.rssm.state_dim, action_dim).to(device)
        self.critic = LatentCritic(self.rssm.state_dim).to(device)
        self.target_critic = LatentCritic(self.rssm.state_dim).to(device)
        self.target_critic.load_state_dict(self.critic.state_dict())
        for p in self.target_critic.parameters():
            p.requires_grad = False
        
        self.wm_opt = optim.Adam(self.rssm.parameters(), lr=1e-4)
        self.actor_opt = optim.Adam(self.actor.parameters(), lr=3e-4)
        self.critic_opt = optim.Adam(self.critic.parameters(), lr=3e-4)

    def save_weights(self, path: str, episode: int = 0):
        torch.save({
            "model_config": self.config,
            "rssm": self.rssm.state_dict(),
            "actor": self.actor.state_dict(),
            "critic": self.critic.state_dict(),
            "wm_opt": self.wm_opt.state_dict(),
            "actor_opt": self.actor_opt.state_dict(),
            "critic_opt": self.critic_opt.state_dict(),
            "episode": episode
        }, path)
        
    def load_weights(self, path: str):
        checkpoint = torch.load(path, map_location=self.device)
        self.rssm.load_state_dict(checkpoint["rssm"])
        self.actor.load_state_dict(checkpoint["actor"])
        self.critic.load_state_dict(checkpoint["critic"])
        
        # Load optimizers if they exist in the checkpoint
        if "wm_opt" in checkpoint:
            self.wm_opt.load_state_dict(checkpoint["wm_opt"])
            self.actor_opt.load_state_dict(checkpoint["actor_opt"])
            self.critic_opt.load_state_dict(checkpoint["critic_opt"])
            
        print(f"Loaded {self.name} weights from episode {checkpoint.get('episode', 'unknown')}")

    def train_wm(self, batch: Dict) -> Dict:
        obs_seq = {k: v.to(self.device) for k, v in batch["obs"].items()}
        action_seq = batch["actions"].to(self.device)
        reward_seq = batch["rewards"].to(self.device)
        done_seq = batch["dones"].to(self.device)

        B = action_seq.shape[0]
        h0, z0 = self.rssm.initial_state(B, self.device)
        h_seq, z_seq, post_logits, prior_logits = self.rssm.observe_sequence(obs_seq, action_seq, h0, z0)
        
        losses = compute_vision_world_model_loss(
            self.rssm, h_seq, z_seq, post_logits, prior_logits,
            obs_seq, reward_seq, continue_target=(1.0 - done_seq)
        )
        
        self.wm_opt.zero_grad()
        losses["total"].backward()
        nn.utils.clip_grad_norm_(self.rssm.parameters(), 10.0)
        self.wm_opt.step()
        
        return {f"{self.name}_wm_loss": losses["total"].item()}

    def train_actor_critic(self, h0: torch.Tensor, z0: torch.Tensor, H: int = 15) -> Dict:
        B = h0.shape[0]
        h, z = h0, z0
        states, actions, rewards, continues, values = [], [], [], [], []
        
        for _ in range(H):
            s = self.rssm.get_state(h, z)
            a, _ = self.actor.get_action(s)
            
            r = symexp(self.rssm.predict_reward(h, z))
            c = self.rssm.predict_continue(h, z)
            v = self.target_critic(s)
            
            states.append(s); actions.append(a); rewards.append(r); continues.append(c); values.append(v)
            h, z, _ = self.rssm.imagine(a, h, z)
            
        states_t = torch.stack(states, dim=1)
        rewards_t = torch.stack(rewards, dim=1)
        continues_t = torch.stack(continues, dim=1)
        values_t = torch.stack(values, dim=1)
        
        with torch.no_grad():
            pass # We need gradients for targets to backprop to Actor!
        
        targets = torch.zeros_like(rewards_t)
        last = values_t[:, -1]
        for t in reversed(range(H)):
            bootstrap = (1 - 0.95) * values_t[:, t] + 0.95 * last
            targets[:, t] = rewards_t[:, t] + 0.99 * continues_t[:, t] * bootstrap
            last = targets[:, t]

        critic_loss = F.mse_loss(self.critic(states_t.detach().reshape(B*H, -1)).reshape(B, H), targets.detach())
        self.critic_opt.zero_grad()
        critic_loss.backward()
        nn.utils.clip_grad_norm_(self.critic.parameters(), 10.0)
        self.critic_opt.step()

        actor_loss = -targets.mean()
        self.actor_opt.zero_grad()
        actor_loss.backward()
        nn.utils.clip_grad_norm_(self.actor.parameters(), 10.0)
        self.actor_opt.step()
        
        # Update Target Critic
        ema = 0.98
        for p_tgt, p_src in zip(self.target_critic.parameters(), self.critic.parameters()):
            p_tgt.data.mul_(ema).add_(p_src.data, alpha=1 - ema)
        
        return {f"{self.name}_actor_loss": actor_loss.item(), f"{self.name}_imag_rew": rewards_t.mean().item()}


class MultiAgentDreamerTrainer:
    def __init__(self, env: MultiAgentBaseballEnv):
        self.env = env
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        self.pitcher = SingleAgentBrain("pitcher", prop_dim=15, action_dim=8, device=self.device)
        self.batter = SingleAgentBrain("batter", prop_dim=18, action_dim=9, device=self.device)
        self.fielder = SingleAgentBrain("fielder", prop_dim=6, action_dim=3, device=self.device)
        self.buffer = MultiAgentReplayBuffer()

    @torch.no_grad()
    def collect_episode(self, record_video: bool = False, run_dir: str = "") -> Dict:
        obs, info = self.env.reset()
        h_p, z_p = self.pitcher.rssm.initial_state(1, self.device)
        h_b, z_b = self.batter.rssm.initial_state(1, self.device)
        h_f, z_f = self.fielder.rssm.initial_state(1, self.device)

        ep_data = {
            "pitcher": {"obs_seq": {"vision": [], "proprioception": []}, "action_seq": [], "reward_seq": [], "done_seq": []},
            "batter":  {"obs_seq": {"vision": [], "proprioception": []}, "action_seq": [], "reward_seq": [], "done_seq": []},
            "fielder": {"obs_seq": {"vision": [], "proprioception": []}, "action_seq": [], "reward_seq": [], "done_seq": []}
        }
        
        # High-Res Video Setup
        video_frames = []
        video_renderer = None
        if record_video:
            import mujoco
            video_renderer = mujoco.Renderer(self.env.model, height=480, width=640)
            
        done = False
        while not done:
            def prep_obs(o):
                v = torch.tensor(o["vision"], dtype=torch.float32, device=self.device).permute(2, 0, 1).unsqueeze(0) / 255.0
                p = torch.tensor(o["proprioception"], dtype=torch.float32, device=self.device).unsqueeze(0)
                return {"vision": v, "proprioception": p}

            obs_p = prep_obs(obs["pitcher"])
            obs_b = prep_obs(obs["batter"])
            obs_f = prep_obs(obs["fielder"])

            a_p_dummy = torch.zeros(1, 8, device=self.device)
            a_b_dummy = torch.zeros(1, 9, device=self.device)
            a_f_dummy = torch.zeros(1, 3, device=self.device)
            
            if ep_data["pitcher"]["action_seq"]:
                a_p_dummy = torch.tensor(ep_data["pitcher"]["action_seq"][-1], dtype=torch.float32, device=self.device).unsqueeze(0)
                a_b_dummy = torch.tensor(ep_data["batter"]["action_seq"][-1], dtype=torch.float32, device=self.device).unsqueeze(0)
                a_f_dummy = torch.tensor(ep_data["fielder"]["action_seq"][-1], dtype=torch.float32, device=self.device).unsqueeze(0)

            h_p, z_p, _ = self.pitcher.rssm.observe(obs_p, a_p_dummy, h_p, z_p)
            h_b, z_b, _ = self.batter.rssm.observe(obs_b, a_b_dummy, h_b, z_b)
            h_f, z_f, _ = self.fielder.rssm.observe(obs_f, a_f_dummy, h_f, z_f)

            if record_video and video_renderer is not None:
                import cv2
                cameras = [("batter_cam", "Batter"), ("pitcher_cam", "Pitcher"), 
                           ("fielder_cam", "Fielder"), ("broadcaster_cam", "Broadcaster")]
                m_frames = []
                for cam_name, label in cameras:
                    video_renderer.update_scene(self.env.data, camera=cam_name)
                    frame = video_renderer.render().copy()
                    cv2.putText(frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
                    m_frames.append(frame)
                top = np.hstack((m_frames[0], m_frames[1]))
                bot = np.hstack((m_frames[2], m_frames[3]))
                grid = np.vstack((top, bot))
                video_frames.append(grid)

            act_p, _ = self.pitcher.actor.get_action(self.pitcher.rssm.get_state(h_p, z_p))
            act_b, _ = self.batter.actor.get_action(self.batter.rssm.get_state(h_b, z_b))
            act_f, _ = self.fielder.actor.get_action(self.fielder.rssm.get_state(h_f, z_f))

            act_p_np = act_p.squeeze(0).cpu().numpy()
            act_b_np = act_b.squeeze(0).cpu().numpy()
            act_f_np = act_f.squeeze(0).cpu().numpy()

            next_obs, rewards, terminated, truncated, info = self.env.step({"pitcher": act_p_np, "batter": act_b_np, "fielder": act_f_np})
            
            if hasattr(self, 'viewer') and self.viewer is not None:
                import time
                self.viewer.sync()
                time.sleep(0.02) # Slow down to ~50 FPS so human can see it
            
            for agent in ["pitcher", "batter", "fielder"]:
                ep_data[agent]["obs_seq"]["vision"].append(obs[agent]["vision"])
                ep_data[agent]["obs_seq"]["proprioception"].append(obs[agent]["proprioception"])
                act = act_p_np if agent == "pitcher" else act_b_np if agent == "batter" else act_f_np
                ep_data[agent]["action_seq"].append(act)
                ep_data[agent]["reward_seq"].append(float(rewards[agent]))
                ep_data[agent]["done_seq"].append(1.0 if terminated[agent] else 0.0)

            done = terminated["__all__"] or truncated["__all__"]
            obs = next_obs

        if record_video and video_frames:
            import cv2
            import os
            import shutil
            import json
            import time
            
            vid_name = f"ep_{int(time.time())}.mp4"
            vid_path = os.path.join(run_dir, vid_name)
            h, w, _ = video_frames[0].shape
            out = cv2.VideoWriter(vid_path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (w, h))
            for f in video_frames:
                out.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
            out.release()
            
            os.makedirs("videos", exist_ok=True)
            dash_vid = f"videos/{vid_name}"
            shutil.copy(vid_path, dash_vid)
            with open("videos/video_manifest.json", "w") as f:
                json.dump({"latest_video": vid_name}, f)
            print(f"🎬 High-Res Video saved at {vid_path}")
            
        for agent in ["pitcher", "batter", "fielder"]:
            for k in ["vision", "proprioception"]:
                ep_data[agent]["obs_seq"][k] = np.array(ep_data[agent]["obs_seq"][k])
            ep_data[agent]["action_seq"] = np.array(ep_data[agent]["action_seq"])
            ep_data[agent]["reward_seq"] = np.array(ep_data[agent]["reward_seq"])
            ep_data[agent]["done_seq"] = np.array(ep_data[agent]["done_seq"])

        return ep_data

    def train_step(self):
        metrics = {}
        for brain in [self.pitcher, self.batter, self.fielder]:
            batch = self.buffer.sample(brain.name, batch_size=4)
            if batch is not None:
                m_wm = brain.train_wm(batch)
                metrics.update(m_wm)
                
                # Actor Critic update
                h0, z0 = brain.rssm.initial_state(4, self.device)
                m_ac = brain.train_actor_critic(h0, z0)
                metrics.update(m_ac)
        return metrics

def run(curriculum_phase="batter_drills", render_live=False):
    """
    curriculum_phase: "pitcher_drills", "batter_drills", "fielder_drills", "full_game"
    render_live: if True, opens a real-time mujoco viewer window (slows down training)
    """
    print(f"🚀 Starting Multi-Agent Dreamer Training... (Phase: {curriculum_phase})")
    
    if curriculum_phase == "tee_ball_drills":
        # Phase 0: Stationary ball on tee, easy shaping rewards
        config = EnvConfig(mode="batter_only", is_tee_ball=True, pitch_speed_y=0.0)
    elif curriculum_phase == "batter_drills":
        # Phase 1: Batter isolated training: Slow batting machine, no pitcher actions, big strike zone
        config = EnvConfig(mode="batter_only", is_tee_ball=False, pitch_speed_y=-25.0, strike_zone_scale=3.0)
    elif curriculum_phase == "pitcher_drills":
        # Pitcher isolated training: Just aim, no batter swinging
        config = EnvConfig(mode="pitcher_only", is_tee_ball=False, pitch_speed_y=-25.0)
    elif curriculum_phase == "fielder_drills":
        # Fielder isolated training: Auto pop-fly
        config = EnvConfig(mode="fielder_only", is_tee_ball=False)
    else:
        # Full competitive play
        config = EnvConfig(mode="full", is_tee_ball=False, strike_zone_scale=1.0)
        
    env = MultiAgentBaseballEnv(config=config)
    trainer = MultiAgentDreamerTrainer(env)
    
    run_dir = f"runs/{curriculum_phase}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(run_dir, exist_ok=True)
    writer = SummaryWriter(log_dir=run_dir)
    dash_logger = DashboardLogger()
    print(f"📁 Logs and Videos will be saved in: {run_dir} (and Dashboard)")
    
    # Optional Live Viewer Setup
    import contextlib
    if render_live:
        import mujoco.viewer
        viewer_context = mujoco.viewer.launch_passive(env.model, env.data)
    else:
        viewer_context = contextlib.nullcontext()
        
    with viewer_context as viewer:
        if render_live:
            trainer.viewer = viewer
            
        for ep in range(1, 1000):
            record_vid = (ep % 20 == 0)
            ep_data = trainer.collect_episode(record_video=record_vid, run_dir=run_dir)
            trainer.buffer.add_episode(ep_data)
            
            # Log episode rewards
            ep_rewards = {agent: sum(ep_data[agent]["reward_seq"]) for agent in ["pitcher", "batter", "fielder"]}
            for agent, rew in ep_rewards.items():
                writer.add_scalar(f"Reward/{agent}", rew, ep)
            
            metrics = {}
            if trainer.buffer.size > 2:
                for _ in range(5):
                    metrics = trainer.train_step()
            
            if ep % 5 == 0:
                print(f"[Ep {ep:3d}] Rewards: {ep_rewards} | Metrics: {metrics}")
                dash_stats = {}
                
                kor_agent = {"pitcher": "투수", "batter": "타자", "fielder": "수비수"}
                
                for agent, rew in ep_rewards.items():
                    writer.add_scalar(f"보상(Reward)/{kor_agent[agent]}", rew, ep)
                    dash_stats[f"reward_{agent}"] = rew
                    
                for k, v in metrics.items():
                    if "pitcher" in k: kor_prefix = "투수"
                    elif "batter" in k: kor_prefix = "타자"
                    elif "fielder" in k: kor_prefix = "수비수"
                    else: kor_prefix = "기타"
                    
                    if "wm_loss" in k: kor_suffix = "월드모델(WM)"
                    elif "actor_loss" in k: kor_suffix = "액터(Actor)"
                    elif "imag_rew" in k: kor_suffix = "상상_보상(Imagined)"
                    else: kor_suffix = k
                    
                    writer.add_scalar(f"손실(Loss)/{kor_prefix}_{kor_suffix}", v, ep)
                    dash_stats[k] = v
                    
                dash_logger.log_episode_stats(ep, dash_stats)
                    
            # Save video every 20 episodes
            if ep % 20 == 0:
                pass # Video is now recorded and saved inside collect_episode()
            
        # Save model weights every 50 episodes
        if ep % 50 == 0:
            for brain in [trainer.pitcher, trainer.batter, trainer.fielder]:
                model_path = os.path.join(run_dir, f"{brain.name}_ep_{ep:04d}.pt")
                brain.save_weights(model_path, episode=ep)
            print(f"💾 Model weights saved to {run_dir}")
            
    # Final save
    for brain in [trainer.pitcher, trainer.batter, trainer.fielder]:
        brain.save_weights(os.path.join(run_dir, f"{brain.name}_final.pt"), episode=ep)
        
    writer.close()
    print("✅ Training complete.")

if __name__ == "__main__":
    run()
