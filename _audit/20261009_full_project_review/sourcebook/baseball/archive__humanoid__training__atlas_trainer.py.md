# baseball/archive/humanoid/training/atlas_trainer.py

원본: [archive/humanoid/training/atlas_trainer.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/humanoid/training/atlas_trainer.py)

SHA256: `02f612570455acce74ceae7a625a528f0bb57cdf7cb832b5599462b12686b01a`

전체 198행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `obs_to_tensor` | FunctionDef | 21 | 22 |
| `batch_obs_to_tensor` | FunctionDef | 24 | 30 |
| `run_atlas_training` | FunctionDef | 32 | 195 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | import time
    4 | import numpy as np
    5 | import torch
    6 | import torch.nn.functional as F
    7 | from collections import deque
    8 | from pathlib import Path
    9 | from typing import Dict, Any
   10 | 
   11 | sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
   12 | 
   13 | from humanoid.envs.atlas_baseball_env import AtlasBaseballEnv
   14 | from humanoid.training.atlas_networks import AtlasBatterPolicy, AtlasValueNetwork, get_device
   15 | from training.curriculum_manager import CurriculumManager
   16 | from training.health_monitor import TrainingHealthMonitor
   17 | from training.episode_recorder import EpisodeRecorder
   18 | from training.reward_audit import RewardAuditSystem
   19 | from training.logger import DashboardLogger
   20 | 
   21 | def obs_to_tensor(obs_dict: Dict[str, np.ndarray], device: torch.device) -> Dict[str, torch.Tensor]:
   22 |     return {k: torch.tensor(v, dtype=torch.float32, device=device).unsqueeze(0) for k, v in obs_dict.items()}
   23 | 
   24 | def batch_obs_to_tensor(obs_list: list, device: torch.device) -> Dict[str, torch.Tensor]:
   25 |     keys = obs_list[0].keys()
   26 |     res = {}
   27 |     for k in keys:
   28 |         arr = np.array([o[k] for o in obs_list])
   29 |         res[k] = torch.tensor(arr, dtype=torch.float32, device=device)
   30 |     return res
   31 | 
   32 | def run_atlas_training(total_episodes: int = 500, initial_stage: int = 1, record_interval: int = 50):
   33 |     device = get_device()
   34 |     print("=" * 70)
   35 |     print(f" ⚾ Boston Dynamics Atlas (30-DOF) Grounded Baseball PPO Training")
   36 |     print(f"   Device: {device} | Episodes: {total_episodes}")
   37 |     print(f"   Robot: Boston Dynamics Atlas (3D Mesh Model)")
   38 |     print("=" * 70)
   39 | 
   40 |     env = AtlasBaseballEnv(render_mode="rgb_array")
   41 |     env.set_curriculum_stage(initial_stage)
   42 | 
   43 |     act_dim = env.action_space.shape[0] # 30
   44 |     policy = AtlasBatterPolicy(action_dim=act_dim, hidden_dim=256, num_layers=2).to(device)
   45 |     value_net = AtlasValueNetwork(hidden_dim=256).to(device)
   46 | 
   47 |     optimizer = torch.optim.Adam(
   48 |         list(policy.parameters()) + list(value_net.parameters()),
   49 |         lr=1e-4
   50 |     )
   51 | 
   52 |     curriculum = CurriculumManager(initial_stage=initial_stage)
   53 |     monitor = TrainingHealthMonitor()
   54 |     recorder = EpisodeRecorder()
   55 |     auditor = RewardAuditSystem()
   56 |     dashboard_logger = DashboardLogger()
   57 | 
   58 |     reward_window = deque(maxlen=50)
   59 |     balance_window = deque(maxlen=50)
   60 |     best_contact_rate = 0.0
   61 |     start_time = time.time()
   62 | 
   63 |     for ep in range(1, total_episodes + 1):
   64 |         obs, info = env.reset()
   65 |         done = False
   66 |         hidden = None
   67 | 
   68 |         obs_list, act_list, rew_list, log_prob_list, val_list, next_vision_list = [], [], [], [], [], []
   69 |         frames = []
   70 | 
   71 |         should_record = (ep % record_interval == 0 or ep == 1)
   72 | 
   73 |         while not done:
   74 |             if should_record:
   75 |                 frame = env.render()
   76 |                 if frame is not None:
   77 |                     frames.append(frame)
   78 | 
   79 |             obs_t = obs_to_tensor(obs, device)
   80 | 
   81 |             with torch.no_grad():
   82 |                 action_t, log_prob_t, _, hidden = policy.get_action(obs_t, hidden)
   83 |                 val_t = value_net(obs_t)
   84 | 
   85 |             action = action_t.squeeze(0).cpu().numpy()
   86 |             log_prob = log_prob_t.squeeze(0).cpu().item()
   87 |             value = val_t.squeeze().cpu().item()
   88 | 
   89 |             next_obs, reward, terminated, truncated, step_info = env.step(action)
   90 |             done = terminated or truncated
   91 | 
   92 |             obs_list.append(obs)
   93 |             act_list.append(action)
   94 |             rew_list.append(reward)
   95 |             log_prob_list.append(log_prob)
   96 |             val_list.append(value)
   97 |             next_vision_list.append(next_obs["vision"])
   98 | 
   99 |             obs = next_obs
  100 | 
  101 |         ep_reward = sum(rew_list)
  102 |         reward_window.append(ep_reward)
  103 |         contacted = step_info.get("has_contacted", False)
  104 |         balance_reward = step_info.get("balance_reward", 0.0)
  105 |         balance_window.append(balance_reward)
  106 | 
  107 |         curriculum.record_episode(contacted, step_info)
  108 | 
  109 |         # Video recording
  110 |         if should_record:
  111 |             video_path = recorder.record_episode(env, policy, ep, device)
  112 |             if video_path:
  113 |                 print(f"  🎬 Atlas Episode Video Saved: {video_path}")
  114 |                 dashboard_logger.log_video(ep, curriculum.current_stage, str(video_path))
  115 | 
  116 |         # PPO Update
  117 |         if len(obs_list) > 1:
  118 |             batch_obs = batch_obs_to_tensor(obs_list, device)
  119 |             act_tensor = torch.tensor(np.array(act_list), dtype=torch.float32, device=device)
  120 |             old_log_probs = torch.tensor(np.array(log_prob_list), dtype=torch.float32, device=device)
  121 |             next_vision_tensor = torch.tensor(np.array(next_vision_list), dtype=torch.float32, device=device)
  122 | 
  123 |             returns = []
  124 |             discounted = 0.0
  125 |             for r in reversed(rew_list):
  126 |                 discounted = r + 0.99 * discounted
  127 |                 returns.insert(0, discounted)
  128 |             returns_tensor = torch.tensor(returns, dtype=torch.float32, device=device)
  129 |             values_tensor = torch.tensor(np.array(val_list), dtype=torch.float32, device=device)
  130 | 
  131 |             advantages = returns_tensor - values_tensor
  132 |             if advantages.std() > 1e-8:
  133 |                 advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
  134 | 
  135 |             for _ in range(3):
  136 |                 new_log_probs, entropy, _ = policy.evaluate_actions(batch_obs, act_tensor)
  137 |                 new_values = value_net(batch_obs).squeeze(-1)
  138 | 
  139 |                 ratios = torch.exp(new_log_probs - old_log_probs)
  140 |                 surr1 = ratios * advantages
  141 |                 surr2 = torch.clamp(ratios, 0.8, 1.2) * advantages
  142 |                 policy_loss = -torch.min(surr1, surr2).mean()
  143 | 
  144 |                 value_loss = F.mse_loss(new_values, returns_tensor)
  145 |                 entropy_loss = -entropy.mean()
  146 | 
  147 |                 loss = policy_loss + 0.5 * value_loss + 0.01 * entropy_loss
  148 |                 optimizer.zero_grad()
  149 |                 loss.backward()
  150 |                 torch.nn.utils.clip_grad_norm_(list(policy.parameters()) + list(value_net.parameters()), max_norm=1.0)
  151 |                 optimizer.step()
  152 | 
  153 |         if ep % 20 == 0 or ep == total_episodes:
  154 |             cr = curriculum.get_contact_rate()
  155 |             avg_rew = np.mean(list(reward_window)) if reward_window else 0.0
  156 |             avg_bal = np.mean(list(balance_window)) if balance_window else 0.0
  157 |             elapsed = time.time() - start_time
  158 |             stage = curriculum.current_stage
  159 | 
  160 |             print(
  161 |                 f"  [EP {ep:4d}/{total_episodes}] "
  162 |                 f"Stage {stage} | "
  163 |                 f"CR={cr:.1%} | "
  164 |                 f"Reward={avg_rew:+.2f} | "
  165 |                 f"Balance={avg_bal:.2f} | "
  166 |                 f"{elapsed:.0f}s"
  167 |             )
  168 |             ge = env.game_engine
  169 |             inning_str = f"{ge.inning}회{'초' if ge.is_top else '말'}"
  170 |             print("  " + "=" * 54)
  171 |             print(f"   🤖 BOSTON DYNAMICS ATLAS STATUS | {inning_str} | OUT: {ge.outs}")
  172 |             print(f"   ⚾ Ball: {ge.balls}  Strike: {ge.strikes} | Score: HOME {ge.score_home} - {ge.score_away} AWAY")
  173 |             print("  " + "=" * 54)
  174 | 
  175 |             metrics = {
  176 |                 "contact_rate": cr,
  177 |                 "reward": avg_rew,
  178 |                 "balance_reward": avg_bal,
  179 |             }
  180 |             dashboard_logger.log_episode_stats(ep, metrics)
  181 | 
  182 |     save_dir = Path(__file__).parent.parent / "checkpoints"
  183 |     save_dir.mkdir(parents=True, exist_ok=True)
  184 |     save_path = save_dir / "atlas_baseball_policy.pt"
  185 | 
  186 |     torch.save({
  187 |         "policy_state_dict": policy.state_dict(),
  188 |         "value_state_dict": value_net.state_dict(),
  189 |         "episodes": total_episodes,
  190 |     }, save_path)
  191 | 
  192 |     print("\n" + "=" * 70)
  193 |     print(f" 🏆 Boston Dynamics Atlas PPO Training Complete!")
  194 |     print(f"    Checkpoint Saved: {save_path}")
  195 |     print("=" * 70)
  196 | 
  197 | if __name__ == "__main__":
  198 |     run_atlas_training(total_episodes=500, initial_stage=1, record_interval=50)
````
