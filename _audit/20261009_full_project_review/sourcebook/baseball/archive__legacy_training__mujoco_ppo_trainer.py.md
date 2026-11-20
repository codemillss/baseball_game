# baseball/archive/legacy_training/mujoco_ppo_trainer.py

원본: [archive/legacy_training/mujoco_ppo_trainer.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_training/mujoco_ppo_trainer.py)

SHA256: `32e97e41923a94c2059a63bd290e0d72fa68aa81cf8573eae3e49d520e9dc204`

전체 200행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `MuJoCoPPOTrainer` | ClassDef | 24 | 191 |
| `__init__` | FunctionDef | 27 | 69 |
| `train` | FunctionDef | 71 | 191 |
| `main` | FunctionDef | 194 | 196 |

## 전체 원문

````text
    1 | """
    2 | mujoco_ppo_trainer.py — Stage 2 PPO Fine-Tuner with Domain Randomization
    3 | 
    4 | Stage 1에서 BC로 pre-training된 Base Policy를 로드하여,
    5 | Domain Randomization(구속 ±10%, 공 질량, 바람/마찰력 변동)이 적용된 
    6 | MuJoCo 3D 야구 환경에서 PPO 파인튜닝을 진행합니다.
    7 | """
    8 | 
    9 | import os
   10 | import json
   11 | from pathlib import Path
   12 | from typing import Optional, Dict, List
   13 | 
   14 | import numpy as np
   15 | import torch
   16 | import torch.nn.functional as F
   17 | import torch.optim as optim
   18 | 
   19 | from envs.mujoco_baseball_env import MuJoCoBaseballEnv
   20 | from training.networks import BatterPolicy, ValueNetwork, get_device
   21 | from simulator.dashboard import save_training_metrics
   22 | 
   23 | 
   24 | class MuJoCoPPOTrainer:
   25 |     """Stage 2 MuJoCo 3D PPO Fine-tuner."""
   26 | 
   27 |     def __init__(
   28 |         self,
   29 |         bc_checkpoint_path: Optional[str] = None,
   30 |         max_episodes: int = 50,
   31 |         lr: float = 3e-4,
   32 |     ):
   33 |         if bc_checkpoint_path is None:
   34 |             bc_checkpoint_path = str(Path(__file__).parent.parent / "checkpoints" / "bc_batter_policy.pt")
   35 | 
   36 |         self.bc_checkpoint_path = bc_checkpoint_path
   37 |         self.max_episodes = max_episodes
   38 |         self.lr = lr
   39 |         self.device = get_device()
   40 | 
   41 |         # 환경
   42 |         self.env = MuJoCoBaseballEnv()
   43 | 
   44 |         # Policy & Value
   45 |         self.obs_dim = self.env.observation_space.shape[0]
   46 |         self.action_dim = self.env.action_space.shape[0]
   47 | 
   48 |         self.policy = BatterPolicy(
   49 |             obs_dim=self.obs_dim,
   50 |             action_dim=self.action_dim,
   51 |             hidden_dim=128,
   52 |             num_layers=2,
   53 |         ).to(self.device)
   54 | 
   55 |         self.value_net = ValueNetwork(obs_dim=self.obs_dim).to(self.device)
   56 | 
   57 |         # BC 가중치 로드
   58 |         if os.path.exists(self.bc_checkpoint_path):
   59 |             ckpt = torch.load(self.bc_checkpoint_path, map_location=self.device)
   60 |             state_dict = ckpt.get('policy_state_dict', ckpt)
   61 |             self.policy.load_state_dict(state_dict)
   62 |             print(f"✅ BC Base Policy 성공적으로 로드됨: {self.bc_checkpoint_path}")
   63 |         else:
   64 |             print("⚠️ BC 체크포인트 없음 - 무작위 가중치로 시작합니다.")
   65 | 
   66 |         self.optimizer = optim.Adam(
   67 |             list(self.policy.parameters()) + list(self.value_net.parameters()),
   68 |             lr=self.lr,
   69 |         )
   70 | 
   71 |     def train(self) -> str:
   72 |         """Stage 2 PPO Fine-Tuning을 실행합니다."""
   73 |         print(f"🚀 Stage 2: MuJoCo 3D PPO Fine-Tuning 시작 ({self.max_episodes} episodes)...")
   74 |         print(f"   Device: {self.device} | Domain Randomization: Enabled (Speed ±10%)")
   75 | 
   76 |         total_contacts = 0
   77 |         total_reward = 0.0
   78 | 
   79 |         for ep in range(1, self.max_episodes + 1):
   80 |             obs, info = self.env.reset()
   81 |             done = False
   82 |             ep_reward = 0.0
   83 | 
   84 |             # Rollout 버퍼
   85 |             obs_list = []
   86 |             act_list = []
   87 |             rew_list = []
   88 |             log_prob_list = []
   89 |             val_list = []
   90 | 
   91 |             hidden = None
   92 |             contacted = False
   93 | 
   94 |             while not done:
   95 |                 obs_t = torch.tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)
   96 | 
   97 |                 with torch.no_grad():
   98 |                     action_t, log_prob_t, _, hidden = self.policy.get_action(obs_t, hidden)
   99 |                     val_t = self.value_net(obs_t)
  100 | 
  101 |                 action = action_t.squeeze(0).cpu().numpy()
  102 |                 log_prob = log_prob_t.squeeze(0).cpu().item()
  103 |                 value = val_t.squeeze(0).cpu().item()
  104 | 
  105 |                 next_obs, reward, terminated, truncated, step_info = self.env.step(action)
  106 |                 done = terminated or truncated
  107 | 
  108 |                 obs_list.append(obs)
  109 |                 act_list.append(action)
  110 |                 rew_list.append(reward)
  111 |                 log_prob_list.append(log_prob)
  112 |                 val_list.append(value)
  113 | 
  114 |                 ep_reward += reward
  115 |                 if step_info.get('has_contacted', False):
  116 |                     contacted = True
  117 | 
  118 |                 obs = next_obs
  119 | 
  120 |             if contacted:
  121 |                 total_contacts += 1
  122 |             total_reward += ep_reward
  123 | 
  124 |             # PPO Gradient Update
  125 |             if len(obs_list) > 0:
  126 |                 obs_tensor = torch.tensor(np.array(obs_list), dtype=torch.float32, device=self.device)
  127 |                 act_tensor = torch.tensor(np.array(act_list), dtype=torch.float32, device=self.device)
  128 |                 old_log_probs = torch.tensor(np.array(log_prob_list), dtype=torch.float32, device=self.device)
  129 |                 rewards_arr = np.array(rew_list)
  130 |                 values_arr = np.array(val_list)
  131 | 
  132 |                 # Return & Advantage 계산
  133 |                 returns = []
  134 |                 discounted = 0.0
  135 |                 for r in reversed(rewards_arr):
  136 |                     discounted = r + 0.99 * discounted
  137 |                     returns.insert(0, discounted)
  138 |                 returns_tensor = torch.tensor(returns, dtype=torch.float32, device=self.device)
  139 |                 advantages = returns_tensor - torch.tensor(values_arr, dtype=torch.float32, device=self.device)
  140 |                 advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
  141 | 
  142 |                 # PPO 4-epoch Optimization
  143 |                 for _ in range(4):
  144 |                     new_log_probs, entropy = self.policy.evaluate_actions(obs_tensor, act_tensor)
  145 |                     new_values = self.value_net(obs_tensor).squeeze(-1)
  146 | 
  147 |                     ratios = torch.exp(new_log_probs - old_log_probs)
  148 |                     surr1 = ratios * advantages
  149 |                     surr2 = torch.clamp(ratios, 0.8, 1.2) * advantages
  150 |                     policy_loss = -torch.min(surr1, surr2).mean()
  151 | 
  152 |                     value_loss = F.mse_loss(new_values, returns_tensor)
  153 |                     entropy_loss = -entropy.mean()
  154 | 
  155 |                     loss = policy_loss + 0.5 * value_loss + 0.01 * entropy_loss
  156 | 
  157 |                     self.optimizer.zero_grad()
  158 |                     loss.backward()
  159 |                     torch.nn.utils.clip_grad_norm_(list(self.policy.parameters()) + list(self.value_net.parameters()), 0.5)
  160 |                     self.optimizer.step()
  161 | 
  162 |             # 대시보드 공유 메트릭 기록
  163 |             if ep % 10 == 0 or ep == self.max_episodes:
  164 |                 win_rate_b = total_contacts / ep
  165 |                 avg_rew = total_reward / ep
  166 |                 print(f"   [EP {ep:3d}/{self.max_episodes}] Contact Rate: {win_rate_b:.1%} | Avg Reward: {avg_rew:+.2f}")
  167 | 
  168 |                 save_training_metrics({
  169 |                     'episode': ep,
  170 |                     'pitcher_win_rate': 1.0 - win_rate_b,
  171 |                     'batter_win_rate': win_rate_b,
  172 |                     'pitcher_reward': -avg_rew,
  173 |                     'batter_reward': avg_rew,
  174 |                     'home_run_rate': win_rate_b * 0.2,
  175 |                     'strikeout_rate': 1.0 - win_rate_b,
  176 |                 })
  177 | 
  178 |         # 체크포인트 저장
  179 |         save_dir = Path(__file__).parent.parent / "checkpoints"
  180 |         save_dir.mkdir(parents=True, exist_ok=True)
  181 |         save_path = save_dir / f"mujoco_ppo_ep{self.max_episodes}.pt"
  182 | 
  183 |         torch.save({
  184 |             'policy_state_dict': self.policy.state_dict(),
  185 |             'value_state_dict': self.value_net.state_dict(),
  186 |             'episodes': self.max_episodes,
  187 |             'contact_rate': total_contacts / self.max_episodes,
  188 |         }, save_path)
  189 | 
  190 |         print(f"\n💾 Stage 2 MuJoCo PPO 체크포인트 저장 완료: {save_path}")
  191 |         return str(save_path)
  192 | 
  193 | 
  194 | def main():
  195 |     trainer = MuJoCoPPOTrainer(max_episodes=30)
  196 |     trainer.train()
  197 | 
  198 | 
  199 | if __name__ == '__main__':
  200 |     main()
````
