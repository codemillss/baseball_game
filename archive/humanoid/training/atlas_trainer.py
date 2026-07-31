import os
import sys
import time
import numpy as np
import torch
import torch.nn.functional as F
from collections import deque
from pathlib import Path
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from humanoid.envs.atlas_baseball_env import AtlasBaseballEnv
from humanoid.training.atlas_networks import AtlasBatterPolicy, AtlasValueNetwork, get_device
from training.curriculum_manager import CurriculumManager
from training.health_monitor import TrainingHealthMonitor
from training.episode_recorder import EpisodeRecorder
from training.reward_audit import RewardAuditSystem
from training.logger import DashboardLogger

def obs_to_tensor(obs_dict: Dict[str, np.ndarray], device: torch.device) -> Dict[str, torch.Tensor]:
    return {k: torch.tensor(v, dtype=torch.float32, device=device).unsqueeze(0) for k, v in obs_dict.items()}

def batch_obs_to_tensor(obs_list: list, device: torch.device) -> Dict[str, torch.Tensor]:
    keys = obs_list[0].keys()
    res = {}
    for k in keys:
        arr = np.array([o[k] for o in obs_list])
        res[k] = torch.tensor(arr, dtype=torch.float32, device=device)
    return res

def run_atlas_training(total_episodes: int = 500, initial_stage: int = 1, record_interval: int = 50):
    device = get_device()
    print("=" * 70)
    print(f" ⚾ Boston Dynamics Atlas (30-DOF) Grounded Baseball PPO Training")
    print(f"   Device: {device} | Episodes: {total_episodes}")
    print(f"   Robot: Boston Dynamics Atlas (3D Mesh Model)")
    print("=" * 70)

    env = AtlasBaseballEnv(render_mode="rgb_array")
    env.set_curriculum_stage(initial_stage)

    act_dim = env.action_space.shape[0] # 30
    policy = AtlasBatterPolicy(action_dim=act_dim, hidden_dim=256, num_layers=2).to(device)
    value_net = AtlasValueNetwork(hidden_dim=256).to(device)

    optimizer = torch.optim.Adam(
        list(policy.parameters()) + list(value_net.parameters()),
        lr=1e-4
    )

    curriculum = CurriculumManager(initial_stage=initial_stage)
    monitor = TrainingHealthMonitor()
    recorder = EpisodeRecorder()
    auditor = RewardAuditSystem()
    dashboard_logger = DashboardLogger()

    reward_window = deque(maxlen=50)
    balance_window = deque(maxlen=50)
    best_contact_rate = 0.0
    start_time = time.time()

    for ep in range(1, total_episodes + 1):
        obs, info = env.reset()
        done = False
        hidden = None

        obs_list, act_list, rew_list, log_prob_list, val_list, next_vision_list = [], [], [], [], [], []
        frames = []

        should_record = (ep % record_interval == 0 or ep == 1)

        while not done:
            if should_record:
                frame = env.render()
                if frame is not None:
                    frames.append(frame)

            obs_t = obs_to_tensor(obs, device)

            with torch.no_grad():
                action_t, log_prob_t, _, hidden = policy.get_action(obs_t, hidden)
                val_t = value_net(obs_t)

            action = action_t.squeeze(0).cpu().numpy()
            log_prob = log_prob_t.squeeze(0).cpu().item()
            value = val_t.squeeze().cpu().item()

            next_obs, reward, terminated, truncated, step_info = env.step(action)
            done = terminated or truncated

            obs_list.append(obs)
            act_list.append(action)
            rew_list.append(reward)
            log_prob_list.append(log_prob)
            val_list.append(value)
            next_vision_list.append(next_obs["vision"])

            obs = next_obs

        ep_reward = sum(rew_list)
        reward_window.append(ep_reward)
        contacted = step_info.get("has_contacted", False)
        balance_reward = step_info.get("balance_reward", 0.0)
        balance_window.append(balance_reward)

        curriculum.record_episode(contacted, step_info)

        # Video recording
        if should_record:
            video_path = recorder.record_episode(env, policy, ep, device)
            if video_path:
                print(f"  🎬 Atlas Episode Video Saved: {video_path}")
                dashboard_logger.log_video(ep, curriculum.current_stage, str(video_path))

        # PPO Update
        if len(obs_list) > 1:
            batch_obs = batch_obs_to_tensor(obs_list, device)
            act_tensor = torch.tensor(np.array(act_list), dtype=torch.float32, device=device)
            old_log_probs = torch.tensor(np.array(log_prob_list), dtype=torch.float32, device=device)
            next_vision_tensor = torch.tensor(np.array(next_vision_list), dtype=torch.float32, device=device)

            returns = []
            discounted = 0.0
            for r in reversed(rew_list):
                discounted = r + 0.99 * discounted
                returns.insert(0, discounted)
            returns_tensor = torch.tensor(returns, dtype=torch.float32, device=device)
            values_tensor = torch.tensor(np.array(val_list), dtype=torch.float32, device=device)

            advantages = returns_tensor - values_tensor
            if advantages.std() > 1e-8:
                advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

            for _ in range(3):
                new_log_probs, entropy, _ = policy.evaluate_actions(batch_obs, act_tensor)
                new_values = value_net(batch_obs).squeeze(-1)

                ratios = torch.exp(new_log_probs - old_log_probs)
                surr1 = ratios * advantages
                surr2 = torch.clamp(ratios, 0.8, 1.2) * advantages
                policy_loss = -torch.min(surr1, surr2).mean()

                value_loss = F.mse_loss(new_values, returns_tensor)
                entropy_loss = -entropy.mean()

                loss = policy_loss + 0.5 * value_loss + 0.01 * entropy_loss
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(list(policy.parameters()) + list(value_net.parameters()), max_norm=1.0)
                optimizer.step()

        if ep % 20 == 0 or ep == total_episodes:
            cr = curriculum.get_contact_rate()
            avg_rew = np.mean(list(reward_window)) if reward_window else 0.0
            avg_bal = np.mean(list(balance_window)) if balance_window else 0.0
            elapsed = time.time() - start_time
            stage = curriculum.current_stage

            print(
                f"  [EP {ep:4d}/{total_episodes}] "
                f"Stage {stage} | "
                f"CR={cr:.1%} | "
                f"Reward={avg_rew:+.2f} | "
                f"Balance={avg_bal:.2f} | "
                f"{elapsed:.0f}s"
            )
            ge = env.game_engine
            inning_str = f"{ge.inning}회{'초' if ge.is_top else '말'}"
            print("  " + "=" * 54)
            print(f"   🤖 BOSTON DYNAMICS ATLAS STATUS | {inning_str} | OUT: {ge.outs}")
            print(f"   ⚾ Ball: {ge.balls}  Strike: {ge.strikes} | Score: HOME {ge.score_home} - {ge.score_away} AWAY")
            print("  " + "=" * 54)

            metrics = {
                "contact_rate": cr,
                "reward": avg_rew,
                "balance_reward": avg_bal,
            }
            dashboard_logger.log_episode_stats(ep, metrics)

    save_dir = Path(__file__).parent.parent / "checkpoints"
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / "atlas_baseball_policy.pt"

    torch.save({
        "policy_state_dict": policy.state_dict(),
        "value_state_dict": value_net.state_dict(),
        "episodes": total_episodes,
    }, save_path)

    print("\n" + "=" * 70)
    print(f" 🏆 Boston Dynamics Atlas PPO Training Complete!")
    print(f"    Checkpoint Saved: {save_path}")
    print("=" * 70)

if __name__ == "__main__":
    run_atlas_training(total_episodes=500, initial_stage=1, record_interval=50)
