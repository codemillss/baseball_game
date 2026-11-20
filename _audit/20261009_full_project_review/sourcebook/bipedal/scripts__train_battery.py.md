# bipedal/scripts/train_battery.py

원본: [scripts/train_battery.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/train_battery.py)

SHA256: `fb2b1ff3274f3e1959fbfb086ece58fc983a766e1d658b8050faef8bbc638c78`

전체 59행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `train` | FunctionDef | 10 | 56 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | sys.path.append(os.path.abspath("."))
    4 | 
    5 | import gymnasium as gym
    6 | from stable_baselines3 import PPO
    7 | from stable_baselines3.common.callbacks import EvalCallback
    8 | from envs.battery_pitch_catch_env import BatteryPitchCatchEnv
    9 | 
   10 | def train():
   11 |     os.makedirs("checkpoints", exist_ok=True)
   12 |     os.makedirs("logs", exist_ok=True)
   13 | 
   14 |     env = BatteryPitchCatchEnv()
   15 |     eval_env = BatteryPitchCatchEnv()
   16 | 
   17 |     eval_callback = EvalCallback(
   18 |         eval_env,
   19 |         best_model_save_path="checkpoints/best_battery",
   20 |         log_path="logs/battery_eval",
   21 |         eval_freq=2500,
   22 |         n_eval_episodes=20,
   23 |         deterministic=True,
   24 |         render=False
   25 |     )
   26 | 
   27 |     model = PPO(
   28 |         "MlpPolicy",
   29 |         env,
   30 |         learning_rate=3e-4,
   31 |         n_steps=1024,
   32 |         batch_size=64,
   33 |         n_epochs=10,
   34 |         gamma=0.99,
   35 |         gae_lambda=0.95,
   36 |         clip_range=0.2,
   37 |         ent_coef=0.005,
   38 |         verbose=1,
   39 |         tensorboard_log="logs/battery_tensorboard/"
   40 |     )
   41 | 
   42 |     total_timesteps = 30000
   43 |     print(f"Starting Battery PPO training for {total_timesteps} steps...")
   44 |     model.learn(total_timesteps=total_timesteps, callback=eval_callback)
   45 | 
   46 |     model.save("checkpoints/final_battery_model.zip")
   47 |     print("Training finished. Final model saved to checkpoints/final_battery_model.zip")
   48 | 
   49 |     best_path = "checkpoints/best_battery/best_model.zip"
   50 |     if os.path.exists(best_path):
   51 |         import shutil
   52 |         shutil.copy(best_path, "checkpoints/best_battery_model.zip")
   53 |         print("Best model copied to checkpoints/best_battery_model.zip")
   54 |     else:
   55 |         import shutil
   56 |         shutil.copy("checkpoints/final_battery_model.zip", "checkpoints/best_battery_model.zip")
   57 | 
   58 | if __name__ == "__main__":
   59 |     train()
````
