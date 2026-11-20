# bipedal/scripts/train_hit_and_run.py

원본: [scripts/train_hit_and_run.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/train_hit_and_run.py)

SHA256: `cdd744d2e7ada72c0bf9e64d0ab1231d8a7b30e8948aefb7d308872c5f7b7184`

전체 166행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `HitAndRunCallback` | ClassDef | 26 | 95 |
| `__init__` | FunctionDef | 27 | 37 |
| `_on_step` | FunctionDef | 39 | 95 |
| `train_hit_and_run` | FunctionDef | 98 | 156 |
| `make_env` | FunctionDef | 107 | 110 |
| `_init` | FunctionDef | 108 | 109 |

## 전체 원문

````text
    1 | """
    2 | Training Pipeline for Phase 4: Hit-and-Run Locomotion Transition.
    3 | Trains the 19-DoF H1 Humanoid to:
    4 | 1. Execute an athletic bipedal swing and make crisp contact on incoming pitches.
    5 | 2. Unlatch the equality weld to drop the bat cleanly on turf.
    6 | 3. Transition dynamic bipedal running locomotion toward 1st Base (x=6.5, y=6.5) without falling.
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
   23 | from envs.hit_and_run_env import HitAndRunEnv
   24 | 
   25 | 
   26 | class HitAndRunCallback(BaseCallback):
   27 |     def __init__(self, eval_env, eval_freq=1000, n_eval_episodes=20, log_dir="logs", verbose=1):
   28 |         super().__init__(verbose)
   29 |         self.eval_env = eval_env
   30 |         self.eval_freq = eval_freq
   31 |         self.n_eval_episodes = n_eval_episodes
   32 |         self.log_dir = log_dir
   33 |         self.best_score = -999.0
   34 |         os.makedirs(log_dir, exist_ok=True)
   35 |         self.log_file = os.path.join(log_dir, "phase4_hit_and_run_progress.csv")
   36 |         with open(self.log_file, "w") as f:
   37 |             f.write("timesteps,balance_rate,contact_rate,fair_hit_rate,bat_rel_rate,mean_dist_traveled\n")
   38 | 
   39 |     def _on_step(self) -> bool:
   40 |         if self.n_calls % self.eval_freq != 0:
   41 |             return True
   42 | 
   43 |         balanced = 0
   44 |         contacts = 0
   45 |         fair_hits = 0
   46 |         bat_releases = 0
   47 |         dist_traveled_list = []
   48 | 
   49 |         for ep in range(self.n_eval_episodes):
   50 |             obs, _ = self.eval_env.reset(seed=20000 + ep)
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
   66 |             if last_info.get("bat_released", False):
   67 |                 bat_releases += 1
   68 |             dist_traveled_list.append(last_info.get("dist_traveled", 0.0))
   69 | 
   70 |         balance_rate = (balanced / self.n_eval_episodes) * 100.0
   71 |         contact_rate = (contacts / self.n_eval_episodes) * 100.0
   72 |         fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
   73 |         bat_rel_rate = (bat_releases / self.n_eval_episodes) * 100.0
   74 |         mean_dist = float(np.mean(dist_traveled_list)) if dist_traveled_list else 0.0
   75 | 
   76 |         if self.verbose > 0:
   77 |             print(f"\n--- [Phase 4 Hit & Run Eval @ Step {self.n_calls}] ---")
   78 |             print(f"  Balance Rate     : {balance_rate:.1f}% ({balanced}/{self.n_eval_episodes})")
   79 |             print(f"  Contact Rate     : {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
   80 |             print(f"  Fair-Hit Rate    : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
   81 |             print(f"  Bat Release Rate : {bat_rel_rate:.1f}% ({bat_releases}/{self.n_eval_episodes})")
   82 |             print(f"  Mean 1B Sprint   : {mean_dist:.2f} m")
   83 | 
   84 |         with open(self.log_file, "a") as f:
   85 |             f.write(f"{self.n_calls},{balance_rate:.2f},{contact_rate:.2f},{fair_rate:.2f},{bat_rel_rate:.2f},{mean_dist:.3f}\n")
   86 | 
   87 |         score = balance_rate + 0.5 * contact_rate + 0.3 * fair_rate + 10.0 * max(0.0, mean_dist)
   88 |         if score > self.best_score:
   89 |             self.best_score = score
   90 |             ckpt_path = os.path.join("checkpoints", "best_phase4_hit_and_run_model.zip")
   91 |             self.model.save(ckpt_path)
   92 |             if self.verbose > 0:
   93 |                 print(f"  >>> New Best Hit & Run Model Saved to {ckpt_path}! (Score: {score:.1f})")
   94 | 
   95 |         return True
   96 | 
   97 | 
   98 | def train_hit_and_run(total_timesteps=30000, seed=42, n_envs=4):
   99 |     print("=" * 60)
  100 |     print("Initiating Phase 4 Hit-and-Run Locomotion Transition PPO Training")
  101 |     print(f"Total Timesteps: {total_timesteps}, Parallel Envs: {n_envs}, Seed: {seed}")
  102 |     print("=" * 60)
  103 | 
  104 |     torch.manual_seed(seed)
  105 |     np.random.seed(seed)
  106 | 
  107 |     def make_env(rank):
  108 |         def _init():
  109 |             return HitAndRunEnv()
  110 |         return _init
  111 | 
  112 |     vec_env = DummyVecEnv([make_env(i) for i in range(n_envs)])
  113 |     eval_env = HitAndRunEnv()
  114 | 
  115 |     os.makedirs("checkpoints", exist_ok=True)
  116 |     os.makedirs("logs", exist_ok=True)
  117 | 
  118 |     callback = HitAndRunCallback(
  119 |         eval_env=eval_env,
  120 |         eval_freq=1000,
  121 |         n_eval_episodes=20,
  122 |         log_dir="logs",
  123 |         verbose=1
  124 |     )
  125 | 
  126 |     policy_kwargs = dict(
  127 |         net_arch=dict(pi=[128, 128], vf=[128, 128]),
  128 |         activation_fn=torch.nn.Tanh
  129 |     )
  130 | 
  131 |     model = PPO(
  132 |         "MlpPolicy",
  133 |         vec_env,
  134 |         learning_rate=3e-4,
  135 |         n_steps=512,
  136 |         batch_size=64,
  137 |         n_epochs=10,
  138 |         gamma=0.99,
  139 |         gae_lambda=0.95,
  140 |         clip_range=0.2,
  141 |         ent_coef=0.005,
  142 |         vf_coef=0.5,
  143 |         max_grad_norm=0.5,
  144 |         policy_kwargs=policy_kwargs,
  145 |         verbose=0,
  146 |         seed=seed
  147 |     )
  148 | 
  149 |     model.learn(total_timesteps=total_timesteps, callback=callback)
  150 | 
  151 |     final_path = os.path.join("checkpoints", "final_phase4_hit_and_run_model.zip")
  152 |     model.save(final_path)
  153 |     print(f"Training Finished! Final model saved to {final_path}")
  154 | 
  155 |     vec_env.close()
  156 |     eval_env.close()
  157 | 
  158 | 
  159 | if __name__ == "__main__":
  160 |     parser = argparse.ArgumentParser()
  161 |     parser.add_argument("--timesteps", type=int, default=30000)
  162 |     parser.add_argument("--envs", type=int, default=4)
  163 |     parser.add_argument("--seed", type=int, default=42)
  164 |     args = parser.parse_args()
  165 | 
  166 |     train_hit_and_run(total_timesteps=args.timesteps, seed=args.seed, n_envs=args.envs)
````
