# bipedal/scripts/train_infield_defense.py

원본: [scripts/train_infield_defense.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/train_infield_defense.py)

SHA256: `fcfbb65ccd42604116ff53d3be2b3afdecd5f2695d34d074debbb3d2c453fdf9`

전체 181행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `InfieldDefenseCallback` | ClassDef | 29 | 118 |
| `__init__` | FunctionDef | 31 | 41 |
| `_on_step` | FunctionDef | 43 | 118 |
| `train` | FunctionDef | 121 | 172 |
| `make_env` | FunctionDef | 130 | 135 |
| `_thunk` | FunctionDef | 131 | 134 |

## 전체 원문

````text
    1 | """
    2 | Training Pipeline for Phase 7: Full Infield Bipedal Defense & 1st Base Out/Safe Play.
    3 | Trains the 8-DoF multi-robot coordination policy for:
    4 | - Pitcher throwing dynamic pitches (Fastball, Slider, Curveball)
    5 | - Batter-Runner kinetic swing, dynamic prop drop handover, and 1st base sprint
    6 | - 1st Baseman Infielder fielding intercept footwork, glove scoop, and base covering
    7 | - 3D Umpire Decision Engine measuring T_runner vs T_defense -> OUT vs SAFE
    8 | """
    9 | 
   10 | import os
   11 | import sys
   12 | import argparse
   13 | import numpy as np
   14 | import torch
   15 | 
   16 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   17 | if BASE_DIR not in sys.path:
   18 |     sys.path.insert(0, BASE_DIR)
   19 | 
   20 | import gymnasium as gym
   21 | from stable_baselines3 import PPO
   22 | from stable_baselines3.common.vec_env import DummyVecEnv
   23 | from stable_baselines3.common.callbacks import BaseCallback
   24 | from stable_baselines3.common.monitor import Monitor
   25 | 
   26 | from envs.infield_defense_env import InfieldDefenseEnv
   27 | 
   28 | 
   29 | class InfieldDefenseCallback(BaseCallback):
   30 |     """Tracks batter and fielder balance survival, contact rate, fair hit rate, fielding rate, and sprint speed."""
   31 |     def __init__(self, eval_env, eval_freq=2048, n_eval_episodes=20, log_dir="logs", verbose=1):
   32 |         super().__init__(verbose)
   33 |         self.eval_env = eval_env
   34 |         self.eval_freq = eval_freq
   35 |         self.n_eval_episodes = n_eval_episodes
   36 |         self.log_dir = log_dir
   37 |         self.best_score = -999.0
   38 |         os.makedirs(log_dir, exist_ok=True)
   39 |         self.log_file = os.path.join(log_dir, "phase7_infield_defense_progress.csv")
   40 |         with open(self.log_file, "w") as f:
   41 |             f.write("timesteps,batter_survival,fielder_survival,contact_rate,fair_hit_rate,fielded_rate,out_rate,safe_rate,mean_exit_vel,mean_runner_spd\n")
   42 | 
   43 |     def _on_step(self) -> bool:
   44 |         if self.n_calls % self.eval_freq != 0:
   45 |             return True
   46 | 
   47 |         b_survived = 0
   48 |         f_survived = 0
   49 |         contacts = 0
   50 |         fair_hits = 0
   51 |         fielded = 0
   52 |         outs = 0
   53 |         safes = 0
   54 |         exit_speeds = []
   55 |         runner_speeds = []
   56 | 
   57 |         for ep in range(self.n_eval_episodes):
   58 |             obs, _ = self.eval_env.reset(seed=50000 + ep)
   59 |             done = False
   60 |             last_info = {}
   61 | 
   62 |             while not done:
   63 |                 action, _ = self.model.predict(obs, deterministic=True)
   64 |                 obs, reward, terminated, truncated, info = self.eval_env.step(action)
   65 |                 done = terminated or truncated
   66 |                 last_info = info
   67 | 
   68 |             if not last_info.get("batter_fallen", False):
   69 |                 b_survived += 1
   70 |             if not last_info.get("fielder_fallen", False):
   71 |                 f_survived += 1
   72 |             if last_info.get("contact", False):
   73 |                 contacts += 1
   74 |                 exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
   75 |             if last_info.get("fair_hit", False):
   76 |                 fair_hits += 1
   77 |             if last_info.get("ball_fielded", False):
   78 |                 fielded += 1
   79 |             if last_info.get("umpire_decision") == "OUT":
   80 |                 outs += 1
   81 |             elif last_info.get("umpire_decision") == "SAFE":
   82 |                 safes += 1
   83 |             runner_speeds.append(last_info.get("runner_speed_kmh", 0.0))
   84 | 
   85 |         b_rate = (b_survived / self.n_eval_episodes) * 100.0
   86 |         f_rate = (f_survived / self.n_eval_episodes) * 100.0
   87 |         c_rate = (contacts / self.n_eval_episodes) * 100.0
   88 |         fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
   89 |         field_rate = (fielded / self.n_eval_episodes) * 100.0
   90 |         out_rate = (outs / self.n_eval_episodes) * 100.0
   91 |         safe_rate = (safes / self.n_eval_episodes) * 100.0
   92 |         mean_exit = float(np.mean(exit_speeds)) if exit_speeds else 0.0
   93 |         mean_runner = float(np.mean(runner_speeds)) if runner_speeds else 0.0
   94 | 
   95 |         if self.verbose > 0:
   96 |             print(f"\n--- [Phase 7 Infield Defense Eval @ Step {self.n_calls}] ---")
   97 |             print(f"  Batter Survival Rate  : {b_rate:.1f}% ({b_survived}/{self.n_eval_episodes}) [Target 100%]")
   98 |             print(f"  Fielder Survival Rate : {f_rate:.1f}% ({f_survived}/{self.n_eval_episodes}) [Target 100%]")
   99 |             print(f"  Contact Rate          : {c_rate:.1f}% ({contacts}/{self.n_eval_episodes}) [Target >= 80%]")
  100 |             print(f"  Fair Hit Rate         : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes}) [Target >= 60%]")
  101 |             print(f"  Fielder Intercept Rate: {field_rate:.1f}% ({fielded}/{self.n_eval_episodes}) [Target ~50-60%]")
  102 |             print(f"  Play Calls (OUT/SAFE) : OUT {out_rate:.1f}% | SAFE {safe_rate:.1f}%")
  103 |             print(f"  Mean Exit Velocity    : {mean_exit:.1f} km/h")
  104 |             print(f"  Mean Runner Sprint Spd: {mean_runner:.1f} km/h")
  105 | 
  106 |         with open(self.log_file, "a") as f:
  107 |             f.write(f"{self.n_calls},{b_rate:.2f},{f_rate:.2f},{c_rate:.2f},{fair_rate:.2f},{field_rate:.2f},{out_rate:.2f},{safe_rate:.2f},{mean_exit:.2f},{mean_runner:.2f}\n")
  108 | 
  109 |         # Multi-objective composite score
  110 |         score = (b_rate * 2.0) + (f_rate * 2.0) + (c_rate * 1.5) + (fair_rate * 1.5) + (field_rate * 1.0)
  111 |         if score > self.best_score and b_rate >= 95.0 and f_rate >= 95.0:
  112 |             self.best_score = score
  113 |             save_path = os.path.join("checkpoints", "best_phase7_infield_defense_model.zip")
  114 |             self.model.save(save_path)
  115 |             if self.verbose > 0:
  116 |                 print(f"  >>> New Best Model Saved! Score: {score:.2f} -> {save_path}")
  117 | 
  118 |         return True
  119 | 
  120 | 
  121 | def train(total_timesteps=40000, seed=42):
  122 |     print("=" * 70)
  123 |     print("Initializing Phase 7: Full Infield Bipedal Defense & 1st Base Out/Safe Play")
  124 |     print(f"Total Timesteps: {total_timesteps} | Seed: {seed}")
  125 |     print("=" * 70)
  126 | 
  127 |     os.makedirs("checkpoints", exist_ok=True)
  128 |     os.makedirs("logs", exist_ok=True)
  129 | 
  130 |     def make_env(s):
  131 |         def _thunk():
  132 |             env = InfieldDefenseEnv()
  133 |             env.reset(seed=s)
  134 |             return Monitor(env)
  135 |         return _thunk
  136 | 
  137 |     train_env = DummyVecEnv([make_env(seed)])
  138 |     eval_env = InfieldDefenseEnv()
  139 | 
  140 |     device = "cuda" if torch.cuda.is_available() else "cpu"
  141 |     print(f"Using compute device: {device}")
  142 | 
  143 |     model = PPO(
  144 |         "MlpPolicy",
  145 |         train_env,
  146 |         device=device,
  147 |         learning_rate=3e-4,
  148 |         n_steps=1024,
  149 |         batch_size=64,
  150 |         n_epochs=10,
  151 |         gamma=0.99,
  152 |         gae_lambda=0.95,
  153 |         clip_range=0.2,
  154 |         ent_coef=0.005,
  155 |         policy_kwargs=dict(net_arch=dict(pi=[128, 128], vf=[128, 128])),
  156 |         verbose=1,
  157 |         tensorboard_log="logs/tb_phase7",
  158 |         seed=seed,
  159 |     )
  160 | 
  161 |     callback = InfieldDefenseCallback(eval_env, eval_freq=2048, n_eval_episodes=20, log_dir="logs", verbose=1)
  162 |     model.learn(total_timesteps=total_timesteps, callback=callback)
  163 | 
  164 |     final_path = os.path.join("checkpoints", "final_phase7_infield_defense_model.zip")
  165 |     model.save(final_path)
  166 |     print(f"Phase 7 Training Complete. Final model saved to {final_path}")
  167 | 
  168 |     # Ensure best model exists
  169 |     best_path = os.path.join("checkpoints", "best_phase7_infield_defense_model.zip")
  170 |     if not os.path.exists(best_path):
  171 |         model.save(best_path)
  172 |         print(f"Saved initial model to {best_path}")
  173 | 
  174 | 
  175 | if __name__ == "__main__":
  176 |     parser = argparse.ArgumentParser(description="Train Phase 7 Infield Defense Policy")
  177 |     parser.add_argument("--timesteps", type=int, default=30000, help="Total training timesteps")
  178 |     parser.add_argument("--seed", type=int, default=42, help="Random seed")
  179 |     args = parser.parse_args()
  180 | 
  181 |     train(total_timesteps=args.timesteps, seed=args.seed)
````
