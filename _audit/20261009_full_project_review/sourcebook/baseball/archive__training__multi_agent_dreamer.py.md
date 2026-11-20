# baseball/archive/training/multi_agent_dreamer.py

원본: [archive/training/multi_agent_dreamer.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/multi_agent_dreamer.py)

SHA256: `c44afb4b0bdef7a1bb9349defdba1ca6eb35943b444ff8210fbe5a58e86290b2`

전체 467행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `MultiAgentReplayBuffer` | ClassDef | 33 | 98 |
| `__init__` | FunctionDef | 34 | 39 |
| `add_episode` | FunctionDef | 41 | 54 |
| `sample` | FunctionDef | 56 | 98 |
| `_slice` | FunctionDef | 71 | 77 |
| `SingleAgentBrain` | ClassDef | 101 | 219 |
| `__init__` | FunctionDef | 103 | 121 |
| `save_weights` | FunctionDef | 123 | 133 |
| `load_weights` | FunctionDef | 135 | 147 |
| `train_wm` | FunctionDef | 149 | 169 |
| `train_actor_critic` | FunctionDef | 171 | 219 |
| `MultiAgentDreamerTrainer` | ClassDef | 222 | 361 |
| `__init__` | FunctionDef | 223 | 231 |
| `collect_episode` | FunctionDef | 234 | 347 |
| `prep_obs` | FunctionDef | 255 | 258 |
| `train_step` | FunctionDef | 349 | 361 |
| `run` | FunctionDef | 363 | 464 |

## 전체 원문

````text
    1 | """
    2 | multi_agent_dreamer.py — 다중 에이전트 독립적 World Model 학습 시스템
    3 | 
    4 | 투수와 타자 각각에 대해 완전히 분리된 뇌(RSSM + Actor + Critic)를 가집니다.
    5 | 시뮬레이션에서 얻은 (pitcher_obs, batter_obs)를 각각 자신의 Replay Buffer에 저장하고
    6 | 독립적으로 자신의 모델을 학습하여 치팅(전지적 정보 공유)을 방지합니다.
    7 | """
    8 | 
    9 | import os
   10 | import time
   11 | import datetime
   12 | import cv2
   13 | import numpy as np
   14 | from pathlib import Path
   15 | from collections import deque
   16 | from typing import Dict, List, Tuple, Optional
   17 | from torch.utils.tensorboard import SummaryWriter
   18 | import shutil
   19 | 
   20 | import torch
   21 | import torch.nn as nn
   22 | import torch.nn.functional as F
   23 | import torch.optim as optim
   24 | 
   25 | from envs.multi_agent_env import MultiAgentBaseballEnv, EnvConfig
   26 | from training.multi_agent_world_model import (
   27 |     BaseballVisionRSSM, compute_vision_world_model_loss, symexp
   28 | )
   29 | from training.world_model_trainer import LatentActor, LatentCritic
   30 | from training.logger import DashboardLogger
   31 | 
   32 | 
   33 | class MultiAgentReplayBuffer:
   34 |     def __init__(self, capacity: int = 5000, seq_len: int = 50):
   35 |         self.capacity = capacity
   36 |         self.seq_len = seq_len
   37 |         self.episodes = []
   38 |         self.write_ptr = 0
   39 |         self.size = 0
   40 | 
   41 |     def add_episode(self, episode: Dict):
   42 |         """
   43 |         episode = {
   44 |             "pitcher": {"obs_seq": {...}, "action_seq": [...], "reward_seq": [...], "done_seq": [...]},
   45 |             "batter":  {"obs_seq": {...}, "action_seq": [...], "reward_seq": [...], "done_seq": [...]},
   46 |             "fielder": {"obs_seq": {...}, "action_seq": [...], "reward_seq": [...], "done_seq": [...]},
   47 |         }
   48 |         """
   49 |         if len(self.episodes) < self.capacity:
   50 |             self.episodes.append(episode)
   51 |         else:
   52 |             self.episodes[self.write_ptr] = episode
   53 |         self.write_ptr = (self.write_ptr + 1) % self.capacity
   54 |         self.size = min(self.size + 1, self.capacity)
   55 | 
   56 |     def sample(self, agent_name: str, batch_size: int) -> Optional[Dict[str, torch.Tensor]]:
   57 |         if self.size < batch_size:
   58 |             return None
   59 | 
   60 |         obs_batch = {"vision": [], "proprioception": []}
   61 |         act_batch, rew_batch, done_batch = [], [], []
   62 | 
   63 |         indices = np.random.choice(self.size, batch_size, replace=True)
   64 | 
   65 |         for idx in indices:
   66 |             ep = self.episodes[idx][agent_name]
   67 |             T = len(ep["action_seq"])
   68 |             start = np.random.randint(0, max(1, T - self.seq_len + 1))
   69 |             end = start + self.seq_len
   70 | 
   71 |             def _slice(arr):
   72 |                 if len(arr) >= end:
   73 |                     return arr[start:end]
   74 |                 pad_len = end - len(arr)
   75 |                 reps = (pad_len,) + (1,) * (arr.ndim - 1)
   76 |                 padded = np.concatenate([arr[start:], np.tile(arr[-1:], reps)], axis=0)
   77 |                 return padded[:self.seq_len]
   78 | 
   79 |             obs_batch["vision"].append(_slice(ep["obs_seq"]["vision"]))
   80 |             obs_batch["proprioception"].append(_slice(ep["obs_seq"]["proprioception"]))
   81 |             act_batch.append(_slice(ep["action_seq"]))
   82 |             rew_batch.append(_slice(ep["reward_seq"]))
   83 |             done_batch.append(_slice(ep["done_seq"]))
   84 | 
   85 |         # Image Data: shape is (B, T, 64, 64, 3) -> convert to (B, T, 3, 64, 64) and normalize
   86 |         vision_np = np.array(obs_batch["vision"])
   87 |         vision_tensor = torch.tensor(vision_np, dtype=torch.float32).permute(0, 1, 4, 2, 3) / 255.0
   88 | 
   89 |         batch = {
   90 |             "obs": {
   91 |                 "vision": vision_tensor,
   92 |                 "proprioception": torch.tensor(np.array(obs_batch["proprioception"]), dtype=torch.float32)
   93 |             },
   94 |             "actions": torch.tensor(np.array(act_batch), dtype=torch.float32),
   95 |             "rewards": torch.tensor(np.array(rew_batch), dtype=torch.float32),
   96 |             "dones": torch.tensor(np.array(done_batch), dtype=torch.float32),
   97 |         }
   98 |         return batch
   99 | 
  100 | 
  101 | class SingleAgentBrain:
  102 |     """Pitcher 또는 Batter 한 명분의 뇌 (RSSM + Actor + Critic)."""
  103 |     def __init__(self, name: str, prop_dim: int, action_dim: int, device: torch.device):
  104 |         self.name = name
  105 |         self.device = device
  106 |         self.config = {
  107 |             "name": name,
  108 |             "prop_dim": prop_dim,
  109 |             "action_dim": action_dim
  110 |         }
  111 |         self.rssm = BaseballVisionRSSM(prop_dim, action_dim).to(device)
  112 |         self.actor = LatentActor(self.rssm.state_dim, action_dim).to(device)
  113 |         self.critic = LatentCritic(self.rssm.state_dim).to(device)
  114 |         self.target_critic = LatentCritic(self.rssm.state_dim).to(device)
  115 |         self.target_critic.load_state_dict(self.critic.state_dict())
  116 |         for p in self.target_critic.parameters():
  117 |             p.requires_grad = False
  118 |         
  119 |         self.wm_opt = optim.Adam(self.rssm.parameters(), lr=1e-4)
  120 |         self.actor_opt = optim.Adam(self.actor.parameters(), lr=3e-4)
  121 |         self.critic_opt = optim.Adam(self.critic.parameters(), lr=3e-4)
  122 | 
  123 |     def save_weights(self, path: str, episode: int = 0):
  124 |         torch.save({
  125 |             "model_config": self.config,
  126 |             "rssm": self.rssm.state_dict(),
  127 |             "actor": self.actor.state_dict(),
  128 |             "critic": self.critic.state_dict(),
  129 |             "wm_opt": self.wm_opt.state_dict(),
  130 |             "actor_opt": self.actor_opt.state_dict(),
  131 |             "critic_opt": self.critic_opt.state_dict(),
  132 |             "episode": episode
  133 |         }, path)
  134 |         
  135 |     def load_weights(self, path: str):
  136 |         checkpoint = torch.load(path, map_location=self.device)
  137 |         self.rssm.load_state_dict(checkpoint["rssm"])
  138 |         self.actor.load_state_dict(checkpoint["actor"])
  139 |         self.critic.load_state_dict(checkpoint["critic"])
  140 |         
  141 |         # Load optimizers if they exist in the checkpoint
  142 |         if "wm_opt" in checkpoint:
  143 |             self.wm_opt.load_state_dict(checkpoint["wm_opt"])
  144 |             self.actor_opt.load_state_dict(checkpoint["actor_opt"])
  145 |             self.critic_opt.load_state_dict(checkpoint["critic_opt"])
  146 |             
  147 |         print(f"Loaded {self.name} weights from episode {checkpoint.get('episode', 'unknown')}")
  148 | 
  149 |     def train_wm(self, batch: Dict) -> Dict:
  150 |         obs_seq = {k: v.to(self.device) for k, v in batch["obs"].items()}
  151 |         action_seq = batch["actions"].to(self.device)
  152 |         reward_seq = batch["rewards"].to(self.device)
  153 |         done_seq = batch["dones"].to(self.device)
  154 | 
  155 |         B = action_seq.shape[0]
  156 |         h0, z0 = self.rssm.initial_state(B, self.device)
  157 |         h_seq, z_seq, post_logits, prior_logits = self.rssm.observe_sequence(obs_seq, action_seq, h0, z0)
  158 |         
  159 |         losses = compute_vision_world_model_loss(
  160 |             self.rssm, h_seq, z_seq, post_logits, prior_logits,
  161 |             obs_seq, reward_seq, continue_target=(1.0 - done_seq)
  162 |         )
  163 |         
  164 |         self.wm_opt.zero_grad()
  165 |         losses["total"].backward()
  166 |         nn.utils.clip_grad_norm_(self.rssm.parameters(), 10.0)
  167 |         self.wm_opt.step()
  168 |         
  169 |         return {f"{self.name}_wm_loss": losses["total"].item()}
  170 | 
  171 |     def train_actor_critic(self, h0: torch.Tensor, z0: torch.Tensor, H: int = 15) -> Dict:
  172 |         B = h0.shape[0]
  173 |         h, z = h0, z0
  174 |         states, actions, rewards, continues, values = [], [], [], [], []
  175 |         
  176 |         for _ in range(H):
  177 |             s = self.rssm.get_state(h, z)
  178 |             a, _ = self.actor.get_action(s)
  179 |             
  180 |             r = symexp(self.rssm.predict_reward(h, z))
  181 |             c = self.rssm.predict_continue(h, z)
  182 |             v = self.target_critic(s)
  183 |             
  184 |             states.append(s); actions.append(a); rewards.append(r); continues.append(c); values.append(v)
  185 |             h, z, _ = self.rssm.imagine(a, h, z)
  186 |             
  187 |         states_t = torch.stack(states, dim=1)
  188 |         rewards_t = torch.stack(rewards, dim=1)
  189 |         continues_t = torch.stack(continues, dim=1)
  190 |         values_t = torch.stack(values, dim=1)
  191 |         
  192 |         with torch.no_grad():
  193 |             pass # We need gradients for targets to backprop to Actor!
  194 |         
  195 |         targets = torch.zeros_like(rewards_t)
  196 |         last = values_t[:, -1]
  197 |         for t in reversed(range(H)):
  198 |             bootstrap = (1 - 0.95) * values_t[:, t] + 0.95 * last
  199 |             targets[:, t] = rewards_t[:, t] + 0.99 * continues_t[:, t] * bootstrap
  200 |             last = targets[:, t]
  201 | 
  202 |         critic_loss = F.mse_loss(self.critic(states_t.detach().reshape(B*H, -1)).reshape(B, H), targets.detach())
  203 |         self.critic_opt.zero_grad()
  204 |         critic_loss.backward()
  205 |         nn.utils.clip_grad_norm_(self.critic.parameters(), 10.0)
  206 |         self.critic_opt.step()
  207 | 
  208 |         actor_loss = -targets.mean()
  209 |         self.actor_opt.zero_grad()
  210 |         actor_loss.backward()
  211 |         nn.utils.clip_grad_norm_(self.actor.parameters(), 10.0)
  212 |         self.actor_opt.step()
  213 |         
  214 |         # Update Target Critic
  215 |         ema = 0.98
  216 |         for p_tgt, p_src in zip(self.target_critic.parameters(), self.critic.parameters()):
  217 |             p_tgt.data.mul_(ema).add_(p_src.data, alpha=1 - ema)
  218 |         
  219 |         return {f"{self.name}_actor_loss": actor_loss.item(), f"{self.name}_imag_rew": rewards_t.mean().item()}
  220 | 
  221 | 
  222 | class MultiAgentDreamerTrainer:
  223 |     def __init__(self, env: MultiAgentBaseballEnv):
  224 |         self.env = env
  225 |         self.device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
  226 |         print(f"Using device: {self.device}")
  227 |         
  228 |         self.pitcher = SingleAgentBrain("pitcher", prop_dim=15, action_dim=8, device=self.device)
  229 |         self.batter = SingleAgentBrain("batter", prop_dim=18, action_dim=9, device=self.device)
  230 |         self.fielder = SingleAgentBrain("fielder", prop_dim=6, action_dim=3, device=self.device)
  231 |         self.buffer = MultiAgentReplayBuffer()
  232 | 
  233 |     @torch.no_grad()
  234 |     def collect_episode(self, record_video: bool = False, run_dir: str = "") -> Dict:
  235 |         obs, info = self.env.reset()
  236 |         h_p, z_p = self.pitcher.rssm.initial_state(1, self.device)
  237 |         h_b, z_b = self.batter.rssm.initial_state(1, self.device)
  238 |         h_f, z_f = self.fielder.rssm.initial_state(1, self.device)
  239 | 
  240 |         ep_data = {
  241 |             "pitcher": {"obs_seq": {"vision": [], "proprioception": []}, "action_seq": [], "reward_seq": [], "done_seq": []},
  242 |             "batter":  {"obs_seq": {"vision": [], "proprioception": []}, "action_seq": [], "reward_seq": [], "done_seq": []},
  243 |             "fielder": {"obs_seq": {"vision": [], "proprioception": []}, "action_seq": [], "reward_seq": [], "done_seq": []}
  244 |         }
  245 |         
  246 |         # High-Res Video Setup
  247 |         video_frames = []
  248 |         video_renderer = None
  249 |         if record_video:
  250 |             import mujoco
  251 |             video_renderer = mujoco.Renderer(self.env.model, height=480, width=640)
  252 |             
  253 |         done = False
  254 |         while not done:
  255 |             def prep_obs(o):
  256 |                 v = torch.tensor(o["vision"], dtype=torch.float32, device=self.device).permute(2, 0, 1).unsqueeze(0) / 255.0
  257 |                 p = torch.tensor(o["proprioception"], dtype=torch.float32, device=self.device).unsqueeze(0)
  258 |                 return {"vision": v, "proprioception": p}
  259 | 
  260 |             obs_p = prep_obs(obs["pitcher"])
  261 |             obs_b = prep_obs(obs["batter"])
  262 |             obs_f = prep_obs(obs["fielder"])
  263 | 
  264 |             a_p_dummy = torch.zeros(1, 8, device=self.device)
  265 |             a_b_dummy = torch.zeros(1, 9, device=self.device)
  266 |             a_f_dummy = torch.zeros(1, 3, device=self.device)
  267 |             
  268 |             if ep_data["pitcher"]["action_seq"]:
  269 |                 a_p_dummy = torch.tensor(ep_data["pitcher"]["action_seq"][-1], dtype=torch.float32, device=self.device).unsqueeze(0)
  270 |                 a_b_dummy = torch.tensor(ep_data["batter"]["action_seq"][-1], dtype=torch.float32, device=self.device).unsqueeze(0)
  271 |                 a_f_dummy = torch.tensor(ep_data["fielder"]["action_seq"][-1], dtype=torch.float32, device=self.device).unsqueeze(0)
  272 | 
  273 |             h_p, z_p, _ = self.pitcher.rssm.observe(obs_p, a_p_dummy, h_p, z_p)
  274 |             h_b, z_b, _ = self.batter.rssm.observe(obs_b, a_b_dummy, h_b, z_b)
  275 |             h_f, z_f, _ = self.fielder.rssm.observe(obs_f, a_f_dummy, h_f, z_f)
  276 | 
  277 |             if record_video and video_renderer is not None:
  278 |                 import cv2
  279 |                 cameras = [("batter_cam", "Batter"), ("pitcher_cam", "Pitcher"), 
  280 |                            ("fielder_cam", "Fielder"), ("broadcaster_cam", "Broadcaster")]
  281 |                 m_frames = []
  282 |                 for cam_name, label in cameras:
  283 |                     video_renderer.update_scene(self.env.data, camera=cam_name)
  284 |                     frame = video_renderer.render().copy()
  285 |                     cv2.putText(frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
  286 |                     m_frames.append(frame)
  287 |                 top = np.hstack((m_frames[0], m_frames[1]))
  288 |                 bot = np.hstack((m_frames[2], m_frames[3]))
  289 |                 grid = np.vstack((top, bot))
  290 |                 video_frames.append(grid)
  291 | 
  292 |             act_p, _ = self.pitcher.actor.get_action(self.pitcher.rssm.get_state(h_p, z_p))
  293 |             act_b, _ = self.batter.actor.get_action(self.batter.rssm.get_state(h_b, z_b))
  294 |             act_f, _ = self.fielder.actor.get_action(self.fielder.rssm.get_state(h_f, z_f))
  295 | 
  296 |             act_p_np = act_p.squeeze(0).cpu().numpy()
  297 |             act_b_np = act_b.squeeze(0).cpu().numpy()
  298 |             act_f_np = act_f.squeeze(0).cpu().numpy()
  299 | 
  300 |             next_obs, rewards, terminated, truncated, info = self.env.step({"pitcher": act_p_np, "batter": act_b_np, "fielder": act_f_np})
  301 |             
  302 |             if hasattr(self, 'viewer') and self.viewer is not None:
  303 |                 import time
  304 |                 self.viewer.sync()
  305 |                 time.sleep(0.02) # Slow down to ~50 FPS so human can see it
  306 |             
  307 |             for agent in ["pitcher", "batter", "fielder"]:
  308 |                 ep_data[agent]["obs_seq"]["vision"].append(obs[agent]["vision"])
  309 |                 ep_data[agent]["obs_seq"]["proprioception"].append(obs[agent]["proprioception"])
  310 |                 act = act_p_np if agent == "pitcher" else act_b_np if agent == "batter" else act_f_np
  311 |                 ep_data[agent]["action_seq"].append(act)
  312 |                 ep_data[agent]["reward_seq"].append(float(rewards[agent]))
  313 |                 ep_data[agent]["done_seq"].append(1.0 if terminated[agent] else 0.0)
  314 | 
  315 |             done = terminated["__all__"] or truncated["__all__"]
  316 |             obs = next_obs
  317 | 
  318 |         if record_video and video_frames:
  319 |             import cv2
  320 |             import os
  321 |             import shutil
  322 |             import json
  323 |             import time
  324 |             
  325 |             vid_name = f"ep_{int(time.time())}.mp4"
  326 |             vid_path = os.path.join(run_dir, vid_name)
  327 |             h, w, _ = video_frames[0].shape
  328 |             out = cv2.VideoWriter(vid_path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (w, h))
  329 |             for f in video_frames:
  330 |                 out.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
  331 |             out.release()
  332 |             
  333 |             os.makedirs("videos", exist_ok=True)
  334 |             dash_vid = f"videos/{vid_name}"
  335 |             shutil.copy(vid_path, dash_vid)
  336 |             with open("videos/video_manifest.json", "w") as f:
  337 |                 json.dump({"latest_video": vid_name}, f)
  338 |             print(f"🎬 High-Res Video saved at {vid_path}")
  339 |             
  340 |         for agent in ["pitcher", "batter", "fielder"]:
  341 |             for k in ["vision", "proprioception"]:
  342 |                 ep_data[agent]["obs_seq"][k] = np.array(ep_data[agent]["obs_seq"][k])
  343 |             ep_data[agent]["action_seq"] = np.array(ep_data[agent]["action_seq"])
  344 |             ep_data[agent]["reward_seq"] = np.array(ep_data[agent]["reward_seq"])
  345 |             ep_data[agent]["done_seq"] = np.array(ep_data[agent]["done_seq"])
  346 | 
  347 |         return ep_data
  348 | 
  349 |     def train_step(self):
  350 |         metrics = {}
  351 |         for brain in [self.pitcher, self.batter, self.fielder]:
  352 |             batch = self.buffer.sample(brain.name, batch_size=4)
  353 |             if batch is not None:
  354 |                 m_wm = brain.train_wm(batch)
  355 |                 metrics.update(m_wm)
  356 |                 
  357 |                 # Actor Critic update
  358 |                 h0, z0 = brain.rssm.initial_state(4, self.device)
  359 |                 m_ac = brain.train_actor_critic(h0, z0)
  360 |                 metrics.update(m_ac)
  361 |         return metrics
  362 | 
  363 | def run(curriculum_phase="batter_drills", render_live=False):
  364 |     """
  365 |     curriculum_phase: "pitcher_drills", "batter_drills", "fielder_drills", "full_game"
  366 |     render_live: if True, opens a real-time mujoco viewer window (slows down training)
  367 |     """
  368 |     print(f"🚀 Starting Multi-Agent Dreamer Training... (Phase: {curriculum_phase})")
  369 |     
  370 |     if curriculum_phase == "tee_ball_drills":
  371 |         # Phase 0: Stationary ball on tee, easy shaping rewards
  372 |         config = EnvConfig(mode="batter_only", is_tee_ball=True, pitch_speed_y=0.0)
  373 |     elif curriculum_phase == "batter_drills":
  374 |         # Phase 1: Batter isolated training: Slow batting machine, no pitcher actions, big strike zone
  375 |         config = EnvConfig(mode="batter_only", is_tee_ball=False, pitch_speed_y=-25.0, strike_zone_scale=3.0)
  376 |     elif curriculum_phase == "pitcher_drills":
  377 |         # Pitcher isolated training: Just aim, no batter swinging
  378 |         config = EnvConfig(mode="pitcher_only", is_tee_ball=False, pitch_speed_y=-25.0)
  379 |     elif curriculum_phase == "fielder_drills":
  380 |         # Fielder isolated training: Auto pop-fly
  381 |         config = EnvConfig(mode="fielder_only", is_tee_ball=False)
  382 |     else:
  383 |         # Full competitive play
  384 |         config = EnvConfig(mode="full", is_tee_ball=False, strike_zone_scale=1.0)
  385 |         
  386 |     env = MultiAgentBaseballEnv(config=config)
  387 |     trainer = MultiAgentDreamerTrainer(env)
  388 |     
  389 |     run_dir = f"runs/{curriculum_phase}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
  390 |     os.makedirs(run_dir, exist_ok=True)
  391 |     writer = SummaryWriter(log_dir=run_dir)
  392 |     dash_logger = DashboardLogger()
  393 |     print(f"📁 Logs and Videos will be saved in: {run_dir} (and Dashboard)")
  394 |     
  395 |     # Optional Live Viewer Setup
  396 |     import contextlib
  397 |     if render_live:
  398 |         import mujoco.viewer
  399 |         viewer_context = mujoco.viewer.launch_passive(env.model, env.data)
  400 |     else:
  401 |         viewer_context = contextlib.nullcontext()
  402 |         
  403 |     with viewer_context as viewer:
  404 |         if render_live:
  405 |             trainer.viewer = viewer
  406 |             
  407 |         for ep in range(1, 1000):
  408 |             record_vid = (ep % 20 == 0)
  409 |             ep_data = trainer.collect_episode(record_video=record_vid, run_dir=run_dir)
  410 |             trainer.buffer.add_episode(ep_data)
  411 |             
  412 |             # Log episode rewards
  413 |             ep_rewards = {agent: sum(ep_data[agent]["reward_seq"]) for agent in ["pitcher", "batter", "fielder"]}
  414 |             for agent, rew in ep_rewards.items():
  415 |                 writer.add_scalar(f"Reward/{agent}", rew, ep)
  416 |             
  417 |             metrics = {}
  418 |             if trainer.buffer.size > 2:
  419 |                 for _ in range(5):
  420 |                     metrics = trainer.train_step()
  421 |             
  422 |             if ep % 5 == 0:
  423 |                 print(f"[Ep {ep:3d}] Rewards: {ep_rewards} | Metrics: {metrics}")
  424 |                 dash_stats = {}
  425 |                 
  426 |                 kor_agent = {"pitcher": "투수", "batter": "타자", "fielder": "수비수"}
  427 |                 
  428 |                 for agent, rew in ep_rewards.items():
  429 |                     writer.add_scalar(f"보상(Reward)/{kor_agent[agent]}", rew, ep)
  430 |                     dash_stats[f"reward_{agent}"] = rew
  431 |                     
  432 |                 for k, v in metrics.items():
  433 |                     if "pitcher" in k: kor_prefix = "투수"
  434 |                     elif "batter" in k: kor_prefix = "타자"
  435 |                     elif "fielder" in k: kor_prefix = "수비수"
  436 |                     else: kor_prefix = "기타"
  437 |                     
  438 |                     if "wm_loss" in k: kor_suffix = "월드모델(WM)"
  439 |                     elif "actor_loss" in k: kor_suffix = "액터(Actor)"
  440 |                     elif "imag_rew" in k: kor_suffix = "상상_보상(Imagined)"
  441 |                     else: kor_suffix = k
  442 |                     
  443 |                     writer.add_scalar(f"손실(Loss)/{kor_prefix}_{kor_suffix}", v, ep)
  444 |                     dash_stats[k] = v
  445 |                     
  446 |                 dash_logger.log_episode_stats(ep, dash_stats)
  447 |                     
  448 |             # Save video every 20 episodes
  449 |             if ep % 20 == 0:
  450 |                 pass # Video is now recorded and saved inside collect_episode()
  451 |             
  452 |         # Save model weights every 50 episodes
  453 |         if ep % 50 == 0:
  454 |             for brain in [trainer.pitcher, trainer.batter, trainer.fielder]:
  455 |                 model_path = os.path.join(run_dir, f"{brain.name}_ep_{ep:04d}.pt")
  456 |                 brain.save_weights(model_path, episode=ep)
  457 |             print(f"💾 Model weights saved to {run_dir}")
  458 |             
  459 |     # Final save
  460 |     for brain in [trainer.pitcher, trainer.batter, trainer.fielder]:
  461 |         brain.save_weights(os.path.join(run_dir, f"{brain.name}_final.pt"), episode=ep)
  462 |         
  463 |     writer.close()
  464 |     print("✅ Training complete.")
  465 | 
  466 | if __name__ == "__main__":
  467 |     run()
````
