# bipedal/scripts/train_bipedal_sprint.py

원본: [scripts/train_bipedal_sprint.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/train_bipedal_sprint.py)

SHA256: `a303f1c3940663b26def479d6164e9e9a3827cfc32459a5251056c79e9d03474`

전체 213행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BipedalSprintCallback` | ClassDef | 29 | 112 |
| `__init__` | FunctionDef | 31 | 41 |
| `_on_step` | FunctionDef | 43 | 112 |
| `train` | FunctionDef | 115 | 204 |
| `make_env` | FunctionDef | 124 | 129 |
| `_thunk` | FunctionDef | 125 | 128 |

## 전체 원문

````text
    1 | """
    2 | Training Pipeline for Phase 6: Continuous Multi-Step Bipedal Base Running to 1st Base.
    3 | Trains and fine-tunes the 19-DoF Unitree H1 Humanoid with full 6-DoF floating base pelvis
    4 | to execute:
    5 | - Stage 1: Whole-body bipedal athletic swing and contact against live incoming pitches.
    6 | - Stage 2: Dynamic prop handover of dropped_bat to field turf at release (t = 0.52s).
    7 | - Stage 3: Continuous multi-step bipedal sprint locomotion toward 1st Base (6.5m, 6.5m).
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
   26 | from envs.bipedal_sprint_env import BipedalSprintEnv
   27 | 
   28 | 
   29 | class BipedalSprintCallback(BaseCallback):
   30 |     """Tracks balance survival rate, contact rate, fair hit rate, bat release, and sprint distance."""
   31 |     def __init__(self, eval_env, eval_freq=2000, n_eval_episodes=20, log_dir="logs", verbose=1):
   32 |         super().__init__(verbose)
   33 |         self.eval_env = eval_env
   34 |         self.eval_freq = eval_freq
   35 |         self.n_eval_episodes = n_eval_episodes
   36 |         self.log_dir = log_dir
   37 |         self.best_score = -999.0
   38 |         os.makedirs(log_dir, exist_ok=True)
   39 |         self.log_file = os.path.join(log_dir, "phase6_bipedal_sprint_progress.csv")
   40 |         with open(self.log_file, "w") as f:
   41 |             f.write("timesteps,balance_rate,contact_rate,fair_hit_rate,release_rate,mean_distance,mean_exit_vel,mean_sweet_err,mean_pelvis_z\n")
   42 | 
   43 |     def _on_step(self) -> bool:
   44 |         if self.n_calls % self.eval_freq != 0:
   45 |             return True
   46 | 
   47 |         balanced = 0
   48 |         contacts = 0
   49 |         fair_hits = 0
   50 |         releases = 0
   51 |         dists = []
   52 |         exit_speeds = []
   53 |         sweet_offsets = []
   54 |         pelvis_zs = []
   55 | 
   56 |         for ep in range(self.n_eval_episodes):
   57 |             obs, _ = self.eval_env.reset(seed=30000 + ep)
   58 |             done = False
   59 |             last_info = {}
   60 | 
   61 |             while not done:
   62 |                 action, _ = self.model.predict(obs, deterministic=True)
   63 |                 obs, reward, terminated, truncated, info = self.eval_env.step(action)
   64 |                 done = terminated or truncated
   65 |                 last_info = info
   66 | 
   67 |             if not last_info.get("has_fallen", False):
   68 |                 balanced += 1
   69 |             if last_info.get("contact", False):
   70 |                 contacts += 1
   71 |                 exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
   72 |                 sweet_offsets.append(last_info.get("sweet_spot_offset", 0.0) * 100.0)
   73 |             if last_info.get("fair_hit", False):
   74 |                 fair_hits += 1
   75 |             if last_info.get("bat_released", False):
   76 |                 releases += 1
   77 |             dists.append(last_info.get("dist_traveled", 0.0))
   78 |             pelvis_zs.append(last_info.get("pelvis_z", 0.0))
   79 | 
   80 |         balance_rate = (balanced / self.n_eval_episodes) * 100.0
   81 |         contact_rate = (contacts / self.n_eval_episodes) * 100.0
   82 |         fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
   83 |         release_rate = (releases / self.n_eval_episodes) * 100.0
   84 |         mean_dist = float(np.mean(dists)) if dists else 0.0
   85 |         mean_spd = float(np.mean(exit_speeds)) if exit_speeds else 0.0
   86 |         mean_sweet_err = float(np.mean(sweet_offsets)) if sweet_offsets else 15.0
   87 |         mean_z = float(np.mean(pelvis_zs)) if pelvis_zs else 0.0
   88 | 
   89 |         if self.verbose > 0:
   90 |             print(f"\n--- [Phase 6 Bipedal Sprint Eval @ Step {self.n_calls}] ---")
   91 |             print(f"  Balance Survival Rate : {balance_rate:.1f}% ({balanced}/{self.n_eval_episodes}) [Target >= 95%]")
   92 |             print(f"  Contact Success Rate  : {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
   93 |             print(f"  Forward Fair-Hit Rate : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
   94 |             print(f"  Bat Release Success   : {release_rate:.1f}% ({releases}/{self.n_eval_episodes})")
   95 |             print(f"  Mean Sprint Distance  : {mean_dist:+.2f} m (Max: {np.max(dists):+.2f} m)")
   96 |             print(f"  Sweet Spot Contact MAE: {mean_sweet_err:.2f} cm")
   97 |             print(f"  Mean Exit Velocity    : {mean_spd:.1f} km/h")
   98 |             print(f"  Mean Pelvis Elevation : {mean_z:.3f} m")
   99 | 
  100 |         with open(self.log_file, "a") as f:
  101 |             f.write(f"{self.n_calls},{balance_rate:.2f},{contact_rate:.2f},{fair_rate:.2f},{release_rate:.2f},{mean_dist:.2f},{mean_spd:.2f},{mean_sweet_err:.2f},{mean_z:.3f}\n")
  102 | 
  103 |         # Multi-objective composite score prioritizing zero falls, contact, fair hits, and forward sprint distance
  104 |         score = (balance_rate * 2.0) + (contact_rate * 1.5) + (fair_rate * 2.0) + (mean_dist * 30.0) - (mean_sweet_err * 2.0)
  105 |         if score > self.best_score and balance_rate >= 90.0:
  106 |             self.best_score = score
  107 |             save_path = os.path.join("checkpoints", "best_phase6_bipedal_sprint_model.zip")
  108 |             self.model.save(save_path)
  109 |             if self.verbose > 0:
  110 |                 print(f"  >>> New Best Model Saved! Score: {score:.2f} -> {save_path}")
  111 | 
  112 |         return True
  113 | 
  114 | 
  115 | def train(total_timesteps=40000, seed=42):
  116 |     print("=" * 70)
  117 |     print("Initializing Phase 6: Continuous Multi-Step Bipedal Base Running to 1st Base")
  118 |     print(f"Total Timesteps: {total_timesteps} | Seed: {seed}")
  119 |     print("=" * 70)
  120 | 
  121 |     os.makedirs("checkpoints", exist_ok=True)
  122 |     os.makedirs("logs", exist_ok=True)
  123 | 
  124 |     def make_env(s):
  125 |         def _thunk():
  126 |             env = BipedalSprintEnv()
  127 |             env.reset(seed=s)
  128 |             return Monitor(env)
  129 |         return _thunk
  130 | 
  131 |     train_env = DummyVecEnv([make_env(seed)])
  132 |     eval_env = BipedalSprintEnv()
  133 | 
  134 |     device = "cuda" if torch.cuda.is_available() else "cpu"
  135 |     print(f"Using compute device: {device}")
  136 | 
  137 |     # Check for warm-start checkpoint from Phase 5 duel
  138 |     warmstart_path = os.path.join("checkpoints", "best_phase5_bipedal_duel_model.zip")
  139 |     if os.path.exists(warmstart_path):
  140 |         print(f"Warm-starting from Phase 5 Duel Checkpoint: {warmstart_path}")
  141 |         try:
  142 |             model = PPO.load(
  143 |                 warmstart_path,
  144 |                 env=train_env,
  145 |                 device=device,
  146 |                 learning_rate=3e-4,
  147 |                 n_steps=1024,
  148 |                 batch_size=64,
  149 |                 ent_coef=0.005,
  150 |                 tensorboard_log="logs/tb_phase6",
  151 |             )
  152 |         except Exception as e:
  153 |             print(f"Warm-start loading encountered shape mismatch ({e}), initializing fresh policy.")
  154 |             model = PPO(
  155 |                 "MlpPolicy",
  156 |                 train_env,
  157 |                 device=device,
  158 |                 learning_rate=3e-4,
  159 |                 n_steps=1024,
  160 |                 batch_size=64,
  161 |                 n_epochs=10,
  162 |                 gamma=0.99,
  163 |                 gae_lambda=0.95,
  164 |                 clip_range=0.2,
  165 |                 ent_coef=0.005,
  166 |                 policy_kwargs=dict(net_arch=dict(pi=[128, 128], vf=[128, 128])),
  167 |                 verbose=1,
  168 |                 tensorboard_log="logs/tb_phase6",
  169 |                 seed=seed,
  170 |             )
  171 |     else:
  172 |         model = PPO(
  173 |             "MlpPolicy",
  174 |             train_env,
  175 |             device=device,
  176 |             learning_rate=3e-4,
  177 |             n_steps=1024,
  178 |             batch_size=64,
  179 |             n_epochs=10,
  180 |             gamma=0.99,
  181 |             gae_lambda=0.95,
  182 |             clip_range=0.2,
  183 |             ent_coef=0.005,
  184 |             policy_kwargs=dict(net_arch=dict(pi=[128, 128], vf=[128, 128])),
  185 |             verbose=1,
  186 |             tensorboard_log="logs/tb_phase6",
  187 |             seed=seed,
  188 |         )
  189 | 
  190 |     callback = BipedalSprintCallback(eval_env, eval_freq=2048, n_eval_episodes=20, log_dir="logs", verbose=1)
  191 |     model.learn(total_timesteps=total_timesteps, callback=callback)
  192 | 
  193 |     final_path = os.path.join("checkpoints", "final_phase6_bipedal_sprint_model.zip")
  194 |     model.save(final_path)
  195 |     print(f"Phase 6 Training Complete. Final model saved to {final_path}")
  196 | 
  197 |     # Ensure best model exists
  198 |     best_path = os.path.join("checkpoints", "best_phase6_bipedal_sprint_model.zip")
  199 |     if not os.path.exists(best_path):
  200 |         model.save(best_path)
  201 |         print(f"Saved best model checkpoint to {best_path}")
  202 | 
  203 |     train_env.close()
  204 |     eval_env.close()
  205 | 
  206 | 
  207 | if __name__ == "__main__":
  208 |     parser = argparse.ArgumentParser()
  209 |     parser.add_argument("--timesteps", type=int, default=40000, help="Total training timesteps")
  210 |     parser.add_argument("--seed", type=int, default=42, help="Random seed")
  211 |     args = parser.parse_args()
  212 | 
  213 |     train(total_timesteps=args.timesteps, seed=args.seed)
````
