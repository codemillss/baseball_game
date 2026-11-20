# bipedal/scripts/train_phase1.py

원본: [scripts/train_phase1.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/train_phase1.py)

SHA256: `764472b0281dc7a73f357171bb6566860f2fdf2b288cf9ce46f48905c29aa6d9`

전체 224행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BattingMetricsCallback` | ClassDef | 26 | 139 |
| `__init__` | FunctionDef | 31 | 40 |
| `_on_step` | FunctionDef | 42 | 139 |
| `make_env` | FunctionDef | 142 | 147 |
| `_init` | FunctionDef | 143 | 146 |
| `train` | FunctionDef | 150 | 220 |

## 전체 원문

````text
    1 | """
    2 | Training Pipeline for Phase 1: Directional Hitting & Precision Contact.
    3 | Uses Stable-Baselines3 PPO with customized evaluation callbacks and quantitative metric logging.
    4 | """
    5 | 
    6 | import os
    7 | import sys
    8 | import argparse
    9 | import numpy as np
   10 | import torch
   11 | 
   12 | # Ensure repository root is in sys.path
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
   23 | import envs
   24 | 
   25 | 
   26 | class BattingMetricsCallback(BaseCallback):
   27 |     """
   28 |     Custom callback to log contact rate, fair hit rate, sweet spot precision,
   29 |     and directional spray error during training.
   30 |     """
   31 |     def __init__(self, eval_env, eval_freq=4000, n_eval_episodes=25, log_dir="logs", verbose=1):
   32 |         super().__init__(verbose)
   33 |         self.eval_env = eval_env
   34 |         self.eval_freq = eval_freq
   35 |         self.n_eval_episodes = n_eval_episodes
   36 |         self.log_dir = log_dir
   37 |         self.best_score = -999.0
   38 |         self.best_contact_rate = 0.0
   39 |         self.best_azimuth_mae = 999.0
   40 |         os.makedirs(log_dir, exist_ok=True)
   41 | 
   42 |     def _on_step(self) -> bool:
   43 |         if self.n_calls % self.eval_freq != 0:
   44 |             return True
   45 | 
   46 |         contacts = 0
   47 |         fair_hits = 0
   48 |         sweet_offsets = []
   49 |         azimuth_errors = []
   50 |         launch_errors = []
   51 |         exit_speeds = []
   52 | 
   53 |         pull_success, pull_total = 0, 0
   54 |         center_success, center_total = 0, 0
   55 |         push_success, push_total = 0, 0
   56 | 
   57 |         for ep in range(self.n_eval_episodes):
   58 |             obs, _ = self.eval_env.reset(seed=2000 + ep)
   59 |             done = False
   60 |             ep_contact = False
   61 |             ep_fair = False
   62 |             ep_info = {}
   63 | 
   64 |             target_az_deg = np.degrees(obs[7])
   65 |             if target_az_deg < -10.0:
   66 |                 cat = "pull"
   67 |                 pull_total += 1
   68 |             elif target_az_deg > 10.0:
   69 |                 cat = "push"
   70 |                 push_total += 1
   71 |             else:
   72 |                 cat = "center"
   73 |                 center_total += 1
   74 | 
   75 |             while not done:
   76 |                 action, _ = self.model.predict(obs, deterministic=True)
   77 |                 obs, reward, terminated, truncated, info = self.eval_env.step(action)
   78 |                 done = terminated or truncated
   79 |                 if info.get("contact", False):
   80 |                     ep_contact = True
   81 |                     ep_info = info
   82 |                 if info.get("fair_hit", False):
   83 |                     ep_fair = True
   84 | 
   85 |             if ep_contact:
   86 |                 contacts += 1
   87 |                 sweet_offsets.append(ep_info.get("sweet_spot_offset_cm", 99.0))
   88 |                 exit_speeds.append(ep_info.get("exit_speed_ms", 0.0))
   89 |                 
   90 |                 if ep_fair:
   91 |                     fair_hits += 1
   92 |                     az_err = ep_info.get("azimuth_error_deg", 99.0)
   93 |                     la_err = ep_info.get("launch_error_deg", 99.0)
   94 |                     azimuth_errors.append(az_err)
   95 |                     launch_errors.append(la_err)
   96 | 
   97 |                     if az_err < 25.0:
   98 |                         if cat == "pull":
   99 |                             pull_success += 1
  100 |                         elif cat == "push":
  101 |                             push_success += 1
  102 |                         else:
  103 |                             center_success += 1
  104 | 
  105 |         contact_rate = (contacts / self.n_eval_episodes) * 100.0
  106 |         fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
  107 |         mean_sweet = float(np.mean(sweet_offsets)) if sweet_offsets else 99.0
  108 |         mean_az_err = float(np.mean(azimuth_errors)) if azimuth_errors else 99.0
  109 |         mean_la_err = float(np.mean(launch_errors)) if launch_errors else 99.0
  110 |         mean_exit_speed = float(np.mean(exit_speeds)) if exit_speeds else 0.0
  111 | 
  112 |         pull_acc = (pull_success / max(1, pull_total)) * 100.0
  113 |         center_acc = (center_success / max(1, center_total)) * 100.0
  114 |         push_acc = (push_success / max(1, push_total)) * 100.0
  115 | 
  116 |         if self.verbose > 0:
  117 |             print(f"\n========================================================")
  118 |             print(f"📊 EVALUATION [Step {self.n_calls} / {self.n_eval_episodes} Episodes]")
  119 |             print(f"  • Contact Rate:          {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
  120 |             print(f"  • Fair-Ball Hit Rate:    {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
  121 |             print(f"  • Sweet Spot Offset:     {mean_sweet:.2f} cm")
  122 |             print(f"  • Azimuth Error (MAE):   {mean_az_err:.2f}°")
  123 |             print(f"  • Launch Angle Error:    {mean_la_err:.2f}°")
  124 |             print(f"  • Mean Exit Velocity:    {mean_exit_speed:.1f} m/s ({mean_exit_speed*3.6:.1f} km/h)")
  125 |             print(f"  • Spray Control: Pull={pull_acc:.0f}%, Center={center_acc:.0f}%, Push={push_acc:.0f}%")
  126 |             print(f"========================================================\n")
  127 | 
  128 |         # Holistic objective: prioritize fair hit rate and lower azimuth error
  129 |         composite_score = fair_rate - 0.25 * mean_az_err
  130 |         if composite_score >= self.best_score:
  131 |             self.best_score = composite_score
  132 |             self.best_contact_rate = contact_rate
  133 |             self.best_azimuth_mae = mean_az_err
  134 |             best_path = os.path.join(self.log_dir, "..", "checkpoints", "best_phase1_model.zip")
  135 |             self.model.save(best_path)
  136 |             if self.verbose > 0:
  137 |                 print(f"🏆 New best model saved to {best_path} (Fair: {fair_rate:.1f}%, AzErr: {mean_az_err:.1f}°)")
  138 | 
  139 |         return True
  140 | 
  141 | 
  142 | def make_env(rank, seed=0):
  143 |     def _init():
  144 |         env = gym.make("DirectionalBatting-v0")
  145 |         env.reset(seed=seed + rank)
  146 |         return Monitor(env)
  147 |     return _init
  148 | 
  149 | 
  150 | def train():
  151 |     parser = argparse.ArgumentParser(description="Train Phase 1 Directional Batting Agent")
  152 |     parser.add_argument("--timesteps", type=int, default=50000, help="Total training timesteps")
  153 |     parser.add_argument("--n-envs", type=int, default=4, help="Number of parallel environments")
  154 |     parser.add_argument("--seed", type=int, default=42, help="Random seed")
  155 |     parser.add_argument("--eval-freq", type=int, default=4000, help="Evaluation frequency in timesteps")
  156 |     parser.add_argument("--lr", type=float, default=3e-4, help="PPO learning rate")
  157 |     args = parser.parse_args()
  158 | 
  159 |     # Set seeds
  160 |     np.random.seed(args.seed)
  161 |     torch.manual_seed(args.seed)
  162 | 
  163 |     checkpoints_dir = os.path.join(BASE_DIR, "checkpoints")
  164 |     logs_dir = os.path.join(BASE_DIR, "logs")
  165 |     os.makedirs(checkpoints_dir, exist_ok=True)
  166 |     os.makedirs(logs_dir, exist_ok=True)
  167 | 
  168 |     print("🚀 Initializing Vectorized Environments...")
  169 |     if args.n_envs > 1:
  170 |         vec_env = DummyVecEnv([make_env(i, args.seed) for i in range(args.n_envs)])
  171 |     else:
  172 |         vec_env = DummyVecEnv([make_env(0, args.seed)])
  173 | 
  174 |     eval_env = gym.make("DirectionalBatting-v0")
  175 | 
  176 |     policy_kwargs = dict(
  177 |         net_arch=dict(pi=[128, 128], vf=[128, 128]),
  178 |         activation_fn=torch.nn.Tanh,
  179 |     )
  180 | 
  181 |     model = PPO(
  182 |         "MlpPolicy",
  183 |         vec_env,
  184 |         learning_rate=args.lr,
  185 |         n_steps=1024,
  186 |         batch_size=64,
  187 |         n_epochs=10,
  188 |         gamma=0.99,
  189 |         gae_lambda=0.95,
  190 |         clip_range=0.2,
  191 |         ent_coef=0.01,
  192 |         vf_coef=0.5,
  193 |         max_grad_norm=0.5,
  194 |         policy_kwargs=policy_kwargs,
  195 |         tensorboard_log=os.path.join(logs_dir, "tb"),
  196 |         verbose=1,
  197 |         seed=args.seed,
  198 |     )
  199 | 
  200 |     metrics_callback = BattingMetricsCallback(
  201 |         eval_env=eval_env,
  202 |         eval_freq=args.eval_freq,
  203 |         n_eval_episodes=25,
  204 |         log_dir=logs_dir,
  205 |         verbose=1,
  206 |     )
  207 | 
  208 |     print(f"🔥 Starting PPO Training for {args.timesteps} timesteps on H1 Humanoid...")
  209 |     model.learn(
  210 |         total_timesteps=args.timesteps,
  211 |         callback=metrics_callback,
  212 |         progress_bar=False,
  213 |     )
  214 | 
  215 |     final_model_path = os.path.join(checkpoints_dir, "final_phase1_model.zip")
  216 |     model.save(final_model_path)
  217 |     print(f"✅ Training completed! Final model saved to: {final_model_path}")
  218 | 
  219 |     vec_env.close()
  220 |     eval_env.close()
  221 | 
  222 | 
  223 | if __name__ == "__main__":
  224 |     train()
````
