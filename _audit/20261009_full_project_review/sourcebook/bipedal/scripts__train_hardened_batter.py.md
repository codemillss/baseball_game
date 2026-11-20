# bipedal/scripts/train_hardened_batter.py

원본: [scripts/train_hardened_batter.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/train_hardened_batter.py)

SHA256: `87440195f02557796e5244d3ade94b100cb4f87acfbbf91c765358bfaa66ef45`

전체 167행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `HardenedBattingCallback` | ClassDef | 28 | 97 |
| `__init__` | FunctionDef | 30 | 41 |
| `_on_step` | FunctionDef | 43 | 97 |
| `train_hardened_batter` | FunctionDef | 100 | 156 |
| `make_env` | FunctionDef | 109 | 115 |
| `_init` | FunctionDef | 110 | 114 |

## 전체 원문

````text
    1 | """
    2 | Phase 2 Training: Sim-to-Real Physically Hardened Batting.
    3 | Transfers weights from Phase 1 and hardens the policy against:
    4 | - 20ms EtherCAT communication delay (latency buffer)
    5 | - Strict low-level motor torque saturation
    6 | - Domain randomization (bat mass +/- 10%, restitution variation, vision noise)
    7 | """
    8 | 
    9 | import os
   10 | import sys
   11 | import argparse
   12 | import numpy as np
   13 | import torch
   14 | 
   15 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   16 | if BASE_DIR not in sys.path:
   17 |     sys.path.insert(0, BASE_DIR)
   18 | 
   19 | import gymnasium as gym
   20 | from stable_baselines3 import PPO
   21 | from stable_baselines3.common.vec_env import DummyVecEnv
   22 | from stable_baselines3.common.callbacks import BaseCallback
   23 | from stable_baselines3.common.monitor import Monitor
   24 | 
   25 | from envs.hardened_batting_env import HardenedBattingEnv
   26 | 
   27 | 
   28 | class HardenedBattingCallback(BaseCallback):
   29 |     """Logs contact, fair-hit, and directional accuracy under Sim-to-Real perturbations."""
   30 |     def __init__(self, eval_env, eval_freq=1500, n_eval_episodes=25, log_dir="logs", verbose=1):
   31 |         super().__init__(verbose)
   32 |         self.eval_env = eval_env
   33 |         self.eval_freq = eval_freq
   34 |         self.n_eval_episodes = n_eval_episodes
   35 |         self.log_dir = log_dir
   36 |         self.best_fair_rate = 0.0
   37 |         self.best_az_mae = 999.0
   38 |         os.makedirs(log_dir, exist_ok=True)
   39 |         self.log_file = os.path.join(log_dir, "phase2_hardened_progress.csv")
   40 |         with open(self.log_file, "w") as f:
   41 |             f.write("timesteps,contact_rate,fair_hit_rate,azimuth_mae,launch_mae,exit_speed_kmh\n")
   42 | 
   43 |     def _on_step(self) -> bool:
   44 |         if self.n_calls % self.eval_freq != 0:
   45 |             return True
   46 | 
   47 |         contacts = 0
   48 |         fair_hits = 0
   49 |         az_errors = []
   50 |         la_errors = []
   51 |         exit_speeds = []
   52 | 
   53 |         for ep in range(self.n_eval_episodes):
   54 |             obs, _ = self.eval_env.reset(seed=8000 + ep)
   55 |             done = False
   56 |             last_info = {}
   57 | 
   58 |             while not done:
   59 |                 action, _ = self.model.predict(obs, deterministic=True)
   60 |                 obs, reward, terminated, truncated, info = self.eval_env.step(action)
   61 |                 done = terminated or truncated
   62 |                 last_info = info
   63 | 
   64 |             if last_info.get("contact", False):
   65 |                 contacts += 1
   66 |                 exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
   67 |                 if last_info.get("fair_hit", False):
   68 |                     fair_hits += 1
   69 |                     az_errors.append(last_info.get("azimuth_error_deg", 99.0))
   70 |                     la_errors.append(last_info.get("launch_error_deg", 99.0))
   71 | 
   72 |         contact_rate = (contacts / self.n_eval_episodes) * 100.0
   73 |         fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
   74 |         az_mae = np.mean(az_errors) if az_errors else 99.0
   75 |         la_mae = np.mean(la_errors) if la_errors else 99.0
   76 |         mean_spd = np.mean(exit_speeds) if exit_speeds else 0.0
   77 | 
   78 |         if self.verbose > 0:
   79 |             print(f"\n--- [Phase 2 Hardened Eval @ Step {self.n_calls}] ---")
   80 |             print(f"  Contact Rate  : {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
   81 |             print(f"  Fair-Hit Rate : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
   82 |             print(f"  Azimuth MAE   : {az_mae:.2f}°")
   83 |             print(f"  Launch MAE    : {la_mae:.2f}°")
   84 |             print(f"  Exit Velocity : {mean_spd:.1f} km/h")
   85 | 
   86 |         with open(self.log_file, "a") as f:
   87 |             f.write(f"{self.n_calls},{contact_rate:.2f},{fair_rate:.2f},{az_mae:.2f},{la_mae:.2f},{mean_spd:.2f}\n")
   88 | 
   89 |         if fair_rate >= self.best_fair_rate and az_mae <= self.best_az_mae:
   90 |             self.best_fair_rate = fair_rate
   91 |             self.best_az_mae = az_mae
   92 |             ckpt_path = os.path.join("checkpoints", "best_phase2_hardened_model.zip")
   93 |             self.model.save(ckpt_path)
   94 |             if self.verbose > 0:
   95 |                 print(f"  >>> New Best Hardened Model Saved: {ckpt_path} (Fair: {fair_rate:.1f}%, Az MAE: {az_mae:.2f}°)")
   96 | 
   97 |         return True
   98 | 
   99 | 
  100 | def train_hardened_batter(total_timesteps=30000, seed=42, n_envs=4, pretrained="checkpoints/best_phase1_model.zip"):
  101 |     print("=" * 60)
  102 |     print("Initiating Phase 2 Sim-to-Real Hardened Batting Training")
  103 |     print(f"Total Timesteps: {total_timesteps}, Envs: {n_envs}, Pretrained: {pretrained}")
  104 |     print("=" * 60)
  105 | 
  106 |     torch.manual_seed(seed)
  107 |     np.random.seed(seed)
  108 | 
  109 |     def make_env(env_seed):
  110 |         def _init():
  111 |             env = HardenedBattingEnv(latency_steps=1, enable_domain_randomization=True)
  112 |             env = Monitor(env)
  113 |             env.reset(seed=env_seed)
  114 |             return env
  115 |         return _init
  116 | 
  117 |     vec_env = DummyVecEnv([make_env(seed + i * 100) for i in range(n_envs)])
  118 |     eval_env = HardenedBattingEnv(latency_steps=1, enable_domain_randomization=True)
  119 | 
  120 |     callback = HardenedBattingCallback(
  121 |         eval_env=eval_env,
  122 |         eval_freq=1000,
  123 |         n_eval_episodes=25,
  124 |         log_dir="logs",
  125 |         verbose=1,
  126 |     )
  127 | 
  128 |     if os.path.exists(pretrained):
  129 |         print(f"Loading pretrained Phase 1 weights from {pretrained} for Sim-to-Real hardening...")
  130 |         model = PPO.load(pretrained, env=vec_env, learning_rate=1.5e-4, seed=seed)
  131 |     else:
  132 |         print("No pretrained model found. Initializing from scratch...")
  133 |         policy_kwargs = dict(net_arch=[128, 128], activation_fn=torch.nn.Tanh)
  134 |         model = PPO(
  135 |             "MlpPolicy",
  136 |             vec_env,
  137 |             learning_rate=3e-4,
  138 |             n_steps=512,
  139 |             batch_size=64,
  140 |             n_epochs=10,
  141 |             policy_kwargs=policy_kwargs,
  142 |             seed=seed,
  143 |         )
  144 | 
  145 |     print("Starting fine-tuning under Sim-to-Real perturbations...")
  146 |     model.learn(total_timesteps=total_timesteps, callback=callback)
  147 | 
  148 |     final_path = os.path.join("checkpoints", "final_phase2_hardened_model.zip")
  149 |     model.save(final_path)
  150 |     best_path = os.path.join("checkpoints", "best_phase2_hardened_model.zip")
  151 |     if not os.path.exists(best_path):
  152 |         model.save(best_path)
  153 | 
  154 |     print(f"Phase 2 Training Complete! Final saved to {final_path}")
  155 |     vec_env.close()
  156 |     eval_env.close()
  157 | 
  158 | 
  159 | if __name__ == "__main__":
  160 |     parser = argparse.ArgumentParser()
  161 |     parser.add_argument("--timesteps", type=int, default=25000)
  162 |     parser.add_argument("--seed", type=int, default=42)
  163 |     parser.add_argument("--envs", type=int, default=4)
  164 |     parser.add_argument("--pretrained", type=str, default="checkpoints/best_phase1_model.zip")
  165 |     args = parser.parse_args()
  166 | 
  167 |     train_hardened_batter(total_timesteps=args.timesteps, seed=args.seed, n_envs=args.envs, pretrained=args.pretrained)
````
