# bipedal/scripts/train_athletic_duel.py

원본: [scripts/train_athletic_duel.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/train_athletic_duel.py)

SHA256: `8b319088b473c408373873b0d21aef4944459edcebf9741f5869b56fd7eec343`

전체 75행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `train` | FunctionDef | 10 | 72 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | sys.path.append(os.path.abspath("."))
    4 | 
    5 | import gymnasium as gym
    6 | from stable_baselines3 import PPO
    7 | from stable_baselines3.common.callbacks import EvalCallback
    8 | from envs.athletic_duel_env import AthleticDuelEnv
    9 | 
   10 | def train():
   11 |     os.makedirs("checkpoints", exist_ok=True)
   12 |     os.makedirs("logs", exist_ok=True)
   13 | 
   14 |     env = AthleticDuelEnv()
   15 |     eval_env = AthleticDuelEnv()
   16 | 
   17 |     eval_callback = EvalCallback(
   18 |         eval_env,
   19 |         best_model_save_path="checkpoints/best_athletic_duel",
   20 |         log_path="logs/athletic_duel_eval",
   21 |         eval_freq=2500,
   22 |         n_eval_episodes=20,
   23 |         deterministic=True,
   24 |         render=False
   25 |     )
   26 | 
   27 |     # Fine-tune from previous best checkpoint if available
   28 |     prev_ckpt = "checkpoints/best_athletic_duel_model.zip"
   29 |     if os.path.exists(prev_ckpt):
   30 |         print(f"Fine-tuning from previous best checkpoint: {prev_ckpt}")
   31 |         model = PPO.load(prev_ckpt, env=env,
   32 |                          learning_rate=1.5e-4,   # lower LR for fine-tuning
   33 |                          n_steps=1024,
   34 |                          batch_size=64,
   35 |                          n_epochs=10,
   36 |                          gamma=0.99,
   37 |                          gae_lambda=0.95,
   38 |                          clip_range=0.15,
   39 |                          ent_coef=0.003,
   40 |                          verbose=1,
   41 |                          tensorboard_log="logs/athletic_duel_tb/")
   42 |     else:
   43 |         model = PPO(
   44 |             "MlpPolicy",
   45 |             env,
   46 |             learning_rate=3e-4,
   47 |             n_steps=1024,
   48 |             batch_size=64,
   49 |             n_epochs=10,
   50 |             gamma=0.99,
   51 |             gae_lambda=0.95,
   52 |             clip_range=0.2,
   53 |             ent_coef=0.005,
   54 |             verbose=1,
   55 |             tensorboard_log="logs/athletic_duel_tb/"
   56 |         )
   57 | 
   58 |     total_timesteps = 50000
   59 |     print(f"Starting Athletic Duel PPO training for {total_timesteps} steps...")
   60 |     model.learn(total_timesteps=total_timesteps, callback=eval_callback, reset_num_timesteps=False)
   61 | 
   62 |     model.save("checkpoints/final_athletic_duel_model.zip")
   63 |     print("Training finished. Final model saved to checkpoints/final_athletic_duel_model.zip")
   64 | 
   65 |     best_path = "checkpoints/best_athletic_duel/best_model.zip"
   66 |     if os.path.exists(best_path):
   67 |         import shutil
   68 |         shutil.copy(best_path, "checkpoints/best_athletic_duel_model.zip")
   69 |         print("Best model copied to checkpoints/best_athletic_duel_model.zip")
   70 |     else:
   71 |         import shutil
   72 |         shutil.copy("checkpoints/final_athletic_duel_model.zip", "checkpoints/best_athletic_duel_model.zip")
   73 | 
   74 | if __name__ == "__main__":
   75 |     train()
````
