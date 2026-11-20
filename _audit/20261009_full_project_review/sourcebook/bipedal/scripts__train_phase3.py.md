# bipedal/scripts/train_phase3.py

원본: [scripts/train_phase3.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/train_phase3.py)

SHA256: `0d26d4d01b09414efd4231fbf69bdf1ba2d0de0a5b828d631b1183a703884430`

전체 155행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BipedalSwingCallback` | ClassDef | 26 | 91 |
| `__init__` | FunctionDef | 28 | 38 |
| `_on_step` | FunctionDef | 40 | 91 |
| `train_bipedal_swing` | FunctionDef | 94 | 145 |
| `make_env` | FunctionDef | 103 | 109 |
| `_init` | FunctionDef | 104 | 108 |

## 전체 원문

````text
    1 | """
    2 | Training Pipeline for Phase 3: Whole-Body Kinetic Chain Bipedal Swing.
    3 | Trains H1 Humanoid to maintain 6-DoF floating base balance on two feet
    4 | while executing athletic swings at incoming pitches.
    5 | """
    6 | 
    7 | import os
    8 | import sys
    9 | import argparse
   10 | import numpy as np
   11 | import torch
   12 | 
   13 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   14 | if BASE_DIR not in sys.path:
   15 |     sys.path.insert(0, BASE_DIR)
   16 | 
   17 | import gymnasium as gym
   18 | from stable_baselines3 import PPO
   19 | from stable_baselines3.common.vec_env import DummyVecEnv
   20 | from stable_baselines3.common.callbacks import BaseCallback
   21 | from stable_baselines3.common.monitor import Monitor
   22 | 
   23 | from envs.bipedal_swing_env import BipedalSwingEnv
   24 | 
   25 | 
   26 | class BipedalSwingCallback(BaseCallback):
   27 |     """Logs bipedal balance, fall rate, and contact performance."""
   28 |     def __init__(self, eval_env, eval_freq=1000, n_eval_episodes=25, log_dir="logs", verbose=1):
   29 |         super().__init__(verbose)
   30 |         self.eval_env = eval_env
   31 |         self.eval_freq = eval_freq
   32 |         self.n_eval_episodes = n_eval_episodes
   33 |         self.log_dir = log_dir
   34 |         self.best_balance_score = -999.0
   35 |         os.makedirs(log_dir, exist_ok=True)
   36 |         self.log_file = os.path.join(log_dir, "phase3_bipedal_progress.csv")
   37 |         with open(self.log_file, "w") as f:
   38 |             f.write("timesteps,balance_rate,contact_rate,fair_hit_rate,mean_pelvis_z\n")
   39 | 
   40 |     def _on_step(self) -> bool:
   41 |         if self.n_calls % self.eval_freq != 0:
   42 |             return True
   43 | 
   44 |         balanced = 0
   45 |         contacts = 0
   46 |         fair_hits = 0
   47 |         pelvis_zs = []
   48 | 
   49 |         for ep in range(self.n_eval_episodes):
   50 |             obs, _ = self.eval_env.reset(seed=15000 + ep)
   51 |             done = False
   52 |             last_info = {}
   53 | 
   54 |             while not done:
   55 |                 action, _ = self.model.predict(obs, deterministic=True)
   56 |                 obs, reward, terminated, truncated, info = self.eval_env.step(action)
   57 |                 done = terminated or truncated
   58 |                 last_info = info
   59 | 
   60 |             if not last_info.get("has_fallen", False):
   61 |                 balanced += 1
   62 |             if last_info.get("contact", False):
   63 |                 contacts += 1
   64 |             if last_info.get("fair_hit", False):
   65 |                 fair_hits += 1
   66 |             pelvis_zs.append(last_info.get("pelvis_z", 0.0))
   67 | 
   68 |         balance_rate = (balanced / self.n_eval_episodes) * 100.0
   69 |         contact_rate = (contacts / self.n_eval_episodes) * 100.0
   70 |         fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
   71 |         mean_z = np.mean(pelvis_zs) if pelvis_zs else 0.0
   72 | 
   73 |         if self.verbose > 0:
   74 |             print(f"\n--- [Phase 3 Bipedal Eval @ Step {self.n_calls}] ---")
   75 |             print(f"  Balance Rate  : {balance_rate:.1f}% ({balanced}/{self.n_eval_episodes})")
   76 |             print(f"  Contact Rate  : {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
   77 |             print(f"  Fair-Hit Rate : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
   78 |             print(f"  Mean Pelvis Z : {mean_z:.3f} m")
   79 | 
   80 |         with open(self.log_file, "a") as f:
   81 |             f.write(f"{self.n_calls},{balance_rate:.2f},{contact_rate:.2f},{fair_rate:.2f},{mean_z:.3f}\n")
   82 | 
   83 |         score = balance_rate + 0.5 * contact_rate + 0.5 * fair_rate
   84 |         if score > self.best_balance_score:
   85 |             self.best_balance_score = score
   86 |             ckpt_path = os.path.join("checkpoints", "best_phase3_bipedal_model.zip")
   87 |             self.model.save(ckpt_path)
   88 |             if self.verbose > 0:
   89 |                 print(f"  >>> New Best Bipedal Model Saved to {ckpt_path}! (Score: {score:.1f})")
   90 | 
   91 |         return True
   92 | 
   93 | 
   94 | def train_bipedal_swing(total_timesteps=25000, seed=42, n_envs=4):
   95 |     print("=" * 60)
   96 |     print("Initiating Phase 3 Whole-Body Bipedal Swing PPO Training")
   97 |     print(f"Total Timesteps: {total_timesteps}, Parallel Envs: {n_envs}, Seed: {seed}")
   98 |     print("=" * 60)
   99 | 
  100 |     torch.manual_seed(seed)
  101 |     np.random.seed(seed)
  102 | 
  103 |     def make_env(env_seed):
  104 |         def _init():
  105 |             env = BipedalSwingEnv()
  106 |             env = Monitor(env)
  107 |             env.reset(seed=env_seed)
  108 |             return env
  109 |         return _init
  110 | 
  111 |     vec_env = DummyVecEnv([make_env(seed + i * 100) for i in range(n_envs)])
  112 |     eval_env = BipedalSwingEnv()
  113 | 
  114 |     callback = BipedalSwingCallback(
  115 |         eval_env=eval_env,
  116 |         eval_freq=1000,
  117 |         n_eval_episodes=25,
  118 |         log_dir="logs",
  119 |         verbose=1,
  120 |     )
  121 | 
  122 |     policy_kwargs = dict(net_arch=[128, 128], activation_fn=torch.nn.Tanh)
  123 |     model = PPO(
  124 |         "MlpPolicy",
  125 |         vec_env,
  126 |         learning_rate=3e-4,
  127 |         n_steps=512,
  128 |         batch_size=64,
  129 |         n_epochs=10,
  130 |         policy_kwargs=policy_kwargs,
  131 |         seed=seed,
  132 |     )
  133 | 
  134 |     print("Starting Bipedal PPO optimization...")
  135 |     model.learn(total_timesteps=total_timesteps, callback=callback)
  136 | 
  137 |     final_path = os.path.join("checkpoints", "final_phase3_bipedal_model.zip")
  138 |     model.save(final_path)
  139 |     best_path = os.path.join("checkpoints", "best_phase3_bipedal_model.zip")
  140 |     if not os.path.exists(best_path):
  141 |         model.save(best_path)
  142 | 
  143 |     print(f"Phase 3 Complete! Final model saved to {final_path}")
  144 |     vec_env.close()
  145 |     eval_env.close()
  146 | 
  147 | 
  148 | if __name__ == "__main__":
  149 |     parser = argparse.ArgumentParser()
  150 |     parser.add_argument("--timesteps", type=int, default=20000)
  151 |     parser.add_argument("--seed", type=int, default=42)
  152 |     parser.add_argument("--envs", type=int, default=4)
  153 |     args = parser.parse_args()
  154 | 
  155 |     train_bipedal_swing(total_timesteps=args.timesteps, seed=args.seed, n_envs=args.envs)
````
