# baseball/cognitive_ai/training/train_mega_architecture.py

원본: [cognitive_ai/training/train_mega_architecture.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_mega_architecture.py)

SHA256: `74998e864cb921fff6781a4a79ca15c75c333821e2bfb2e617f3d133e82e1469`

전체 112행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `linear_schedule` | FunctionDef | 16 | 27 |
| `func` | FunctionDef | 22 | 26 |
| `make_batter_env` | FunctionDef | 29 | 34 |
| `_init` | FunctionDef | 30 | 33 |
| `make_pitcher_env` | FunctionDef | 36 | 41 |
| `_init` | FunctionDef | 37 | 40 |
| `train_mega_batter` | FunctionDef | 43 | 74 |
| `train_mega_pitcher` | FunctionDef | 76 | 102 |

## 전체 원문

````text
    1 | import sys
    2 | import os
    3 | import argparse
    4 | sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    5 | 
    6 | from stable_baselines3 import PPO
    7 | from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize, VecFrameStack
    8 | from stable_baselines3.common.callbacks import EvalCallback
    9 | from stable_baselines3.common.utils import set_random_seed
   10 | from typing import Callable
   11 | 
   12 | # Import environments
   13 | from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
   14 | from cognitive_ai.envs.pitcher_env import PitcherEnv
   15 | 
   16 | def linear_schedule(initial_value: float) -> Callable[[float], float]:
   17 |     """
   18 |     Linear learning rate schedule.
   19 |     :param initial_value: Initial learning rate.
   20 |     :return: schedule that computes current learning rate depending on remaining progress
   21 |     """
   22 |     def func(progress_remaining: float) -> float:
   23 |         """
   24 |         Progress will decrease from 1 (beginning) to 0.
   25 |         """
   26 |         return progress_remaining * initial_value
   27 |     return func
   28 | 
   29 | def make_batter_env(seed, rank):
   30 |     def _init():
   31 |         env = BatterMatchTrainingEnv()
   32 |         env.reset(seed=seed + rank)
   33 |         return env
   34 |     return _init
   35 | 
   36 | def make_pitcher_env(seed, rank):
   37 |     def _init():
   38 |         env = PitcherEnv()
   39 |         env.reset(seed=seed + rank)
   40 |         return env
   41 |     return _init
   42 | 
   43 | def train_mega_batter():
   44 |     print("==================================================")
   45 |     print("🔥 STARTING MEGA TRAINING: BATTER (FRAME STACKING) 🔥")
   46 |     print("==================================================")
   47 |     
   48 |     num_envs = 16
   49 |     env = SubprocVecEnv([make_batter_env(42, i) for i in range(num_envs)])
   50 |     env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
   51 |     
   52 |     # NEW ARCHITECTURE: Frame Stacking (4 frames) to detect curveball spin/acceleration
   53 |     env = VecFrameStack(env, n_stack=4)
   54 |     
   55 |     eval_env = SubprocVecEnv([make_batter_env(42, 99)])
   56 |     eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=True, clip_obs=10.)
   57 |     eval_env = VecFrameStack(eval_env, n_stack=4)
   58 |     
   59 |     os.makedirs("checkpoints/mega_batter", exist_ok=True)
   60 |     
   61 |     # Auto-evaluator callback
   62 |     eval_callback = EvalCallback(eval_env, best_model_save_path='checkpoints/mega_batter/',
   63 |                                  log_path='checkpoints/mega_batter/logs/', eval_freq=20000,
   64 |                                  deterministic=True, render=False)
   65 |     
   66 |     model = PPO("MlpPolicy", env, verbose=1, 
   67 |                 n_steps=2048, batch_size=512, 
   68 |                 learning_rate=linear_schedule(5e-4), # Annealing LR
   69 |                 clip_range=0.2, ent_coef=0.01,
   70 |                 tensorboard_log="checkpoints/mega_batter/tb_logs/")
   71 |                 
   72 |     model.learn(total_timesteps=2_000_000, callback=eval_callback)
   73 |     env.save("checkpoints/mega_batter/vec_normalize.pkl")
   74 |     print("Mega Batter Training Complete!")
   75 | 
   76 | def train_mega_pitcher():
   77 |     print("==================================================")
   78 |     print("🔥 STARTING MEGA TRAINING: PITCHER (ANNEALING) 🔥")
   79 |     print("==================================================")
   80 |     
   81 |     num_envs = 16
   82 |     env = SubprocVecEnv([make_pitcher_env(42, i) for i in range(num_envs)])
   83 |     env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
   84 |     
   85 |     eval_env = SubprocVecEnv([make_pitcher_env(42, 99)])
   86 |     eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=True, clip_obs=10.)
   87 |     
   88 |     os.makedirs("checkpoints/mega_pitcher", exist_ok=True)
   89 |     
   90 |     eval_callback = EvalCallback(eval_env, best_model_save_path='checkpoints/mega_pitcher/',
   91 |                                  log_path='checkpoints/mega_pitcher/logs/', eval_freq=20000,
   92 |                                  deterministic=True, render=False)
   93 |                                  
   94 |     model = PPO("MlpPolicy", env, verbose=1, 
   95 |                 n_steps=1024, batch_size=256, 
   96 |                 learning_rate=linear_schedule(3e-4), 
   97 |                 clip_range=0.2, ent_coef=0.01,
   98 |                 tensorboard_log="checkpoints/mega_pitcher/tb_logs/")
   99 |                 
  100 |     model.learn(total_timesteps=2_000_000, callback=eval_callback)
  101 |     env.save("checkpoints/mega_pitcher/vec_normalize.pkl")
  102 |     print("Mega Pitcher Training Complete!")
  103 | 
  104 | if __name__ == "__main__":
  105 |     parser = argparse.ArgumentParser()
  106 |     parser.add_argument("--role", type=str, choices=["batter", "pitcher", "both"], default="both")
  107 |     args = parser.parse_args()
  108 |     
  109 |     if args.role in ["pitcher", "both"]:
  110 |         train_mega_pitcher()
  111 |     if args.role in ["batter", "both"]:
  112 |         train_mega_batter()
````
