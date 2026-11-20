# bipedal/scripts/train_bipedal_duel.py

원본: [scripts/train_bipedal_duel.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/train_bipedal_duel.py)

SHA256: `f754b77fdf93f7a4a7c9454c6837884c46ee9bc094ef2eda65f01e83e6427810`

전체 192행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BipedalDuelCallback` | ClassDef | 26 | 110 |
| `__init__` | FunctionDef | 28 | 38 |
| `_on_step` | FunctionDef | 40 | 110 |
| `train_bipedal_duel` | FunctionDef | 113 | 181 |
| `make_env` | FunctionDef | 122 | 128 |
| `_init` | FunctionDef | 123 | 127 |

## 전체 원문

````text
    1 | """
    2 | Training Pipeline for Phase 5: Full-Stadium Whole-Body Bipedal Pitcher vs Batter Closed-Loop Duel.
    3 | Fine-tunes the 6-DoF floating-base Whole-Body H1 Batter against the live 10m mound H1 Pitcher
    4 | throwing Fastballs (80-88 km/h), Sliders (70-78 km/h), and Curveballs (62-70 km/h).
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
   23 | from envs.bipedal_duel_env import BipedalDuelEnv
   24 | 
   25 | 
   26 | class BipedalDuelCallback(BaseCallback):
   27 |     """Logs balance survival rate, strike rate, contact rate, fair hit rate, and exit velocity."""
   28 |     def __init__(self, eval_env, eval_freq=1000, n_eval_episodes=25, log_dir="logs", verbose=1):
   29 |         super().__init__(verbose)
   30 |         self.eval_env = eval_env
   31 |         self.eval_freq = eval_freq
   32 |         self.n_eval_episodes = n_eval_episodes
   33 |         self.log_dir = log_dir
   34 |         self.best_score = -999.0
   35 |         os.makedirs(log_dir, exist_ok=True)
   36 |         self.log_file = os.path.join(log_dir, "phase5_bipedal_duel_progress.csv")
   37 |         with open(self.log_file, "w") as f:
   38 |             f.write("timesteps,balance_rate,strike_rate,contact_rate,fair_hit_rate,mean_exit_vel,mean_sweet_err,mean_pelvis_z\n")
   39 | 
   40 |     def _on_step(self) -> bool:
   41 |         if self.n_calls % self.eval_freq != 0:
   42 |             return True
   43 | 
   44 |         balanced = 0
   45 |         strikes = 0
   46 |         contacts = 0
   47 |         fair_hits = 0
   48 |         exit_speeds = []
   49 |         sweet_offsets = []
   50 |         pelvis_zs = []
   51 | 
   52 |         for ep in range(self.n_eval_episodes):
   53 |             obs, _ = self.eval_env.reset(seed=25000 + ep)
   54 |             done = False
   55 |             last_info = {}
   56 | 
   57 |             while not done:
   58 |                 action, _ = self.model.predict(obs, deterministic=True)
   59 |                 obs, reward, terminated, truncated, info = self.eval_env.step(action)
   60 |                 done = terminated or truncated
   61 |                 last_info = info
   62 | 
   63 |             if not last_info.get("has_fallen", False):
   64 |                 balanced += 1
   65 |             if last_info.get("is_strike", False):
   66 |                 strikes += 1
   67 |             if last_info.get("contact", False):
   68 |                 contacts += 1
   69 |                 exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
   70 |                 err = last_info.get("sweet_offset_cm", 0.0)
   71 |                 if err > 0:
   72 |                     sweet_offsets.append(err)
   73 |             if last_info.get("fair_hit", False):
   74 |                 fair_hits += 1
   75 |             pelvis_zs.append(last_info.get("pelvis_z", 0.0))
   76 | 
   77 |         balance_rate = (balanced / self.n_eval_episodes) * 100.0
   78 |         strike_rate = (strikes / self.n_eval_episodes) * 100.0
   79 |         contact_rate = (contacts / self.n_eval_episodes) * 100.0
   80 |         fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
   81 |         mean_spd = float(np.mean(exit_speeds)) if exit_speeds else 0.0
   82 |         mean_sweet_err = float(np.mean(sweet_offsets)) if sweet_offsets else 15.0
   83 |         mean_z = float(np.mean(pelvis_zs)) if pelvis_zs else 0.0
   84 | 
   85 |         if self.verbose > 0:
   86 |             print(f"\n--- [Phase 5 Bipedal Duel Eval @ Step {self.n_calls}] ---")
   87 |             print(f"  Balance Survival Rate : {balance_rate:.1f}% ({balanced}/{self.n_eval_episodes}) [Zero Falls!]")
   88 |             print(f"  Mound Pitcher Strike  : {strike_rate:.1f}% ({strikes}/{self.n_eval_episodes})")
   89 |             print(f"  Contact Success Rate  : {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
   90 |             print(f"  Forward Fair-Hit Rate : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
   91 |             print(f"  Sweet Spot Contact MAE: {mean_sweet_err:.2f} cm")
   92 |             print(f"  Mean Exit Velocity    : {mean_spd:.1f} km/h")
   93 |             print(f"  Mean Pelvis Elevation : {mean_z:.3f} m")
   94 | 
   95 |         with open(self.log_file, "a") as f:
   96 |             f.write(f"{self.n_calls},{balance_rate:.2f},{strike_rate:.2f},{contact_rate:.2f},{fair_rate:.2f},{mean_spd:.2f},{mean_sweet_err:.2f},{mean_z:.3f}\n")
   97 | 
   98 |         # Prioritize zero falls (>= 95% balance) and reward high contact, fair hit rates, and low sweet spot error
   99 |         balance_weight = balance_rate if balance_rate >= 95.0 else (balance_rate * 0.1)
  100 |         sweet_bonus = max(0.0, 15.0 - mean_sweet_err) * 10.0
  101 |         score = balance_weight + 3.0 * contact_rate + 3.5 * fair_rate + sweet_bonus + 0.1 * mean_spd
  102 |         if score > self.best_score:
  103 |             self.best_score = score
  104 |             os.makedirs("checkpoints", exist_ok=True)
  105 |             ckpt_path = os.path.join("checkpoints", "best_phase5_bipedal_duel_model.zip")
  106 |             self.model.save(ckpt_path)
  107 |             if self.verbose > 0:
  108 |                 print(f"  >>> New Best Phase 5 Duel Model Saved to {ckpt_path}! (Score: {score:.1f})")
  109 | 
  110 |         return True
  111 | 
  112 | 
  113 | def train_bipedal_duel(total_timesteps=20000, seed=42, n_envs=4, warm_start=True):
  114 |     print("=" * 70)
  115 |     print("Initiating Phase 5 Full-Stadium Whole-Body Bipedal Duel PPO Training")
  116 |     print(f"Timesteps: {total_timesteps}, Envs: {n_envs}, Seed: {seed}, WarmStart: {warm_start}")
  117 |     print("=" * 70)
  118 | 
  119 |     torch.manual_seed(seed)
  120 |     np.random.seed(seed)
  121 | 
  122 |     def make_env(env_seed):
  123 |         def _init():
  124 |             env = BipedalDuelEnv()
  125 |             env = Monitor(env)
  126 |             env.reset(seed=env_seed)
  127 |             return env
  128 |         return _init
  129 | 
  130 |     vec_env = DummyVecEnv([make_env(seed + i * 100) for i in range(n_envs)])
  131 |     eval_env = BipedalDuelEnv()
  132 | 
  133 |     callback = BipedalDuelCallback(
  134 |         eval_env=eval_env,
  135 |         eval_freq=1000,
  136 |         n_eval_episodes=25,
  137 |         log_dir="logs",
  138 |         verbose=1,
  139 |     )
  140 | 
  141 |     base_ckpt = os.path.join("checkpoints", "best_phase5_bipedal_duel_model.zip")
  142 |     if not os.path.exists(base_ckpt):
  143 |         base_ckpt = os.path.join("checkpoints", "best_phase3_bipedal_model.zip")
  144 |     if warm_start and os.path.exists(base_ckpt):
  145 |         print(f"Warm-starting from checkpoint: {base_ckpt}")
  146 |         model = PPO.load(
  147 |             base_ckpt,
  148 |             env=vec_env,
  149 |             learning_rate=2.5e-4,
  150 |             n_steps=512,
  151 |             batch_size=64,
  152 |             n_epochs=10,
  153 |             seed=seed,
  154 |         )
  155 |     else:
  156 |         print("Training policy from scratch...")
  157 |         policy_kwargs = dict(net_arch=[128, 128], activation_fn=torch.nn.Tanh)
  158 |         model = PPO(
  159 |             "MlpPolicy",
  160 |             vec_env,
  161 |             learning_rate=3e-4,
  162 |             n_steps=512,
  163 |             batch_size=64,
  164 |             n_epochs=10,
  165 |             policy_kwargs=policy_kwargs,
  166 |             seed=seed,
  167 |         )
  168 | 
  169 |     print("Starting Bipedal Pitcher-Batter Closed-Loop Optimization...")
  170 |     model.learn(total_timesteps=total_timesteps, callback=callback)
  171 | 
  172 |     final_path = os.path.join("checkpoints", "final_phase5_bipedal_duel_model.zip")
  173 |     model.save(final_path)
  174 |     best_path = os.path.join("checkpoints", "best_phase5_bipedal_duel_model.zip")
  175 |     if not os.path.exists(best_path):
  176 |         model.save(best_path)
  177 | 
  178 |     print(f"\nPhase 5 Training Complete! Final model saved to {final_path}")
  179 |     print(f"Best model saved to {best_path}")
  180 |     vec_env.close()
  181 |     eval_env.close()
  182 | 
  183 | 
  184 | if __name__ == "__main__":
  185 |     parser = argparse.ArgumentParser()
  186 |     parser.add_argument("--timesteps", type=int, default=20000)
  187 |     parser.add_argument("--seed", type=int, default=42)
  188 |     parser.add_argument("--envs", type=int, default=4)
  189 |     parser.add_argument("--no-warm-start", dest="warm_start", action="store_false")
  190 |     args = parser.parse_args()
  191 | 
  192 |     train_bipedal_duel(total_timesteps=args.timesteps, seed=args.seed, n_envs=args.envs, warm_start=args.warm_start)
````
