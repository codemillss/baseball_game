# bipedal/scripts/train_pitcher.py

원본: [scripts/train_pitcher.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/train_pitcher.py)

SHA256: `ebeb1ca17eb94bbc3309344d50c40d0d96ffe864076c8443a8a42f4b6e6aa6d1`

전체 189행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `PitcherMetricsCallback` | ClassDef | 26 | 111 |
| `__init__` | FunctionDef | 31 | 42 |
| `_on_step` | FunctionDef | 44 | 111 |
| `train_pitcher` | FunctionDef | 114 | 179 |
| `make_env` | FunctionDef | 123 | 129 |
| `_init` | FunctionDef | 124 | 128 |

## 전체 원문

````text
    1 | """
    2 | Training Pipeline for Goal-Conditioned Humanoid Pitcher Precision.
    3 | Uses Stable-Baselines3 PPO with real-time strike rate tracking,
    4 | corner-command evaluation, and multi-pitch performance logging.
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
   23 | from envs.pitcher_precision_env import PitcherPrecisionEnv
   24 | 
   25 | 
   26 | class PitcherMetricsCallback(BaseCallback):
   27 |     """
   28 |     Custom callback to log strike rate, targeting error (MAE in cm),
   29 |     and per-pitch-type performance during PPO training.
   30 |     """
   31 |     def __init__(self, eval_env, eval_freq=2000, n_eval_episodes=30, log_dir="logs", verbose=1):
   32 |         super().__init__(verbose)
   33 |         self.eval_env = eval_env
   34 |         self.eval_freq = eval_freq
   35 |         self.n_eval_episodes = n_eval_episodes
   36 |         self.log_dir = log_dir
   37 |         self.best_strike_rate = -1.0
   38 |         self.best_error_cm = 999.0
   39 |         os.makedirs(log_dir, exist_ok=True)
   40 |         self.log_file = os.path.join(log_dir, "pitcher_training_progress.csv")
   41 |         with open(self.log_file, "w") as f:
   42 |             f.write("timesteps,strike_rate,mean_error_cm,fastball_strike,slider_strike,curve_strike,mean_speed_kmh\n")
   43 | 
   44 |     def _on_step(self) -> bool:
   45 |         if self.n_calls % self.eval_freq != 0:
   46 |             return True
   47 | 
   48 |         strikes = 0
   49 |         reached = 0
   50 |         errors_cm = []
   51 |         speeds_kmh = []
   52 | 
   53 |         type_strikes = {0: 0, 1: 0, 2: 0}
   54 |         type_totals = {0: 0, 1: 0, 2: 0}
   55 | 
   56 |         for ep in range(self.n_eval_episodes):
   57 |             obs, _ = self.eval_env.reset(seed=5000 + ep)
   58 |             done = False
   59 |             last_info = {}
   60 | 
   61 |             ptype = self.eval_env.pitch_type
   62 |             type_totals[ptype] += 1
   63 | 
   64 |             while not done:
   65 |                 action, _ = self.model.predict(obs, deterministic=True)
   66 |                 obs, reward, terminated, truncated, info = self.eval_env.step(action)
   67 |                 done = terminated or truncated
   68 |                 last_info = info
   69 | 
   70 |             if last_info.get("reached_plate", False):
   71 |                 reached += 1
   72 |                 dist_cm = last_info.get("dist_error_cm", 99.0)
   73 |                 errors_cm.append(dist_cm)
   74 |                 speeds_kmh.append(last_info.get("release_speed_kmh", 0.0))
   75 | 
   76 |                 if last_info.get("is_strike", False):
   77 |                     strikes += 1
   78 |                     type_strikes[ptype] += 1
   79 | 
   80 |         strike_rate = (strikes / self.n_eval_episodes) * 100.0
   81 |         mean_err = np.mean(errors_cm) if errors_cm else 99.0
   82 |         mean_spd = np.mean(speeds_kmh) if speeds_kmh else 0.0
   83 | 
   84 |         fb_rate = (type_strikes[0] / max(1, type_totals[0])) * 100.0
   85 |         sl_rate = (type_strikes[1] / max(1, type_totals[1])) * 100.0
   86 |         cb_rate = (type_strikes[2] / max(1, type_totals[2])) * 100.0
   87 | 
   88 |         if self.verbose > 0:
   89 |             print(f"\n--- [Pitcher Eval @ Step {self.n_calls}] ---")
   90 |             print(f"  Strike Rate       : {strike_rate:.1f}% ({strikes}/{self.n_eval_episodes})")
   91 |             print(f"  Target Error MAE  : {mean_err:.2f} cm")
   92 |             print(f"  Fastball Strike   : {fb_rate:.1f}% ({type_strikes[0]}/{type_totals[0]})")
   93 |             print(f"  Slider Strike     : {sl_rate:.1f}% ({type_strikes[1]}/{type_totals[1]})")
   94 |             print(f"  Curveball Strike  : {cb_rate:.1f}% ({type_strikes[2]}/{type_totals[2]})")
   95 |             print(f"  Mean Pitch Speed  : {mean_spd:.1f} km/h")
   96 | 
   97 |         with open(self.log_file, "a") as f:
   98 |             f.write(f"{self.n_calls},{strike_rate:.2f},{mean_err:.2f},{fb_rate:.2f},{sl_rate:.2f},{cb_rate:.2f},{mean_spd:.2f}\n")
   99 | 
  100 |         # Save Best Checkpoint (Prioritize Strike Rate, tie-break with low target error)
  101 |         score = strike_rate - 0.5 * mean_err
  102 |         if strike_rate >= self.best_strike_rate and mean_err < self.best_error_cm:
  103 |             self.best_strike_rate = strike_rate
  104 |             self.best_error_cm = mean_err
  105 |             ckpt_path = os.path.join("checkpoints", "best_pitcher_model.zip")
  106 |             os.makedirs("checkpoints", exist_ok=True)
  107 |             self.model.save(ckpt_path)
  108 |             if self.verbose > 0:
  109 |                 print(f"  >>> New Best Pitcher Model Saved to {ckpt_path}! (Strike: {strike_rate:.1f}%, MAE: {mean_err:.2f}cm)")
  110 | 
  111 |         return True
  112 | 
  113 | 
  114 | def train_pitcher(total_timesteps=40000, seed=42, n_envs=4):
  115 |     print("=" * 60)
  116 |     print("Initiating Goal-Conditioned Pitcher Precision PPO Training")
  117 |     print(f"Total Timesteps: {total_timesteps}, Parallel Envs: {n_envs}, Seed: {seed}")
  118 |     print("=" * 60)
  119 | 
  120 |     torch.manual_seed(seed)
  121 |     np.random.seed(seed)
  122 | 
  123 |     def make_env(env_seed):
  124 |         def _init():
  125 |             env = PitcherPrecisionEnv()
  126 |             env = Monitor(env)
  127 |             env.reset(seed=env_seed)
  128 |             return env
  129 |         return _init
  130 | 
  131 |     vec_env = DummyVecEnv([make_env(seed + i * 100) for i in range(n_envs)])
  132 |     eval_env = PitcherPrecisionEnv()
  133 | 
  134 |     os.makedirs("checkpoints", exist_ok=True)
  135 |     os.makedirs("logs", exist_ok=True)
  136 | 
  137 |     callback = PitcherMetricsCallback(
  138 |         eval_env=eval_env,
  139 |         eval_freq=1000,
  140 |         n_eval_episodes=30,
  141 |         log_dir="logs",
  142 |         verbose=1,
  143 |     )
  144 | 
  145 |     policy_kwargs = dict(
  146 |         net_arch=[128, 128],
  147 |         activation_fn=torch.nn.Tanh,
  148 |     )
  149 | 
  150 |     model = PPO(
  151 |         "MlpPolicy",
  152 |         vec_env,
  153 |         learning_rate=3e-4,
  154 |         n_steps=512,
  155 |         batch_size=64,
  156 |         n_epochs=10,
  157 |         gamma=0.99,
  158 |         gae_lambda=0.95,
  159 |         clip_range=0.2,
  160 |         ent_coef=0.01,
  161 |         policy_kwargs=policy_kwargs,
  162 |         verbose=0,
  163 |         seed=seed,
  164 |     )
  165 | 
  166 |     print("\nStarting PPO optimization loop...")
  167 |     model.learn(total_timesteps=total_timesteps, callback=callback)
  168 | 
  169 |     final_path = os.path.join("checkpoints", "final_pitcher_model.zip")
  170 |     model.save(final_path)
  171 |     print(f"\nTraining Complete! Final model saved to {final_path}")
  172 | 
  173 |     # If best_pitcher_model doesn't exist, copy final
  174 |     best_path = os.path.join("checkpoints", "best_pitcher_model.zip")
  175 |     if not os.path.exists(best_path):
  176 |         model.save(best_path)
  177 | 
  178 |     vec_env.close()
  179 |     eval_env.close()
  180 | 
  181 | 
  182 | if __name__ == "__main__":
  183 |     parser = argparse.ArgumentParser()
  184 |     parser.add_argument("--timesteps", type=int, default=30000)
  185 |     parser.add_argument("--seed", type=int, default=42)
  186 |     parser.add_argument("--envs", type=int, default=4)
  187 |     args = parser.parse_args()
  188 | 
  189 |     train_pitcher(total_timesteps=args.timesteps, seed=args.seed, n_envs=args.envs)
````
