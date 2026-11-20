# baseball/cognitive_ai/training/train_teeball.py

원본: [cognitive_ai/training/train_teeball.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_teeball.py)

SHA256: `aae1e81d666790e7ee1ed9ce5c6873859792c54bed62127c41b1f6e72cbf6eda`

전체 54행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `train_teeball` | FunctionDef | 12 | 51 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | import time
    4 | from stable_baselines3 import PPO
    5 | from stable_baselines3.common.callbacks import EvalCallback, StopTrainingOnRewardThreshold
    6 | from stable_baselines3.common.monitor import Monitor
    7 | 
    8 | # Add parent directory to path
    9 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
   10 | from cognitive_ai.envs.teeball_env import TeeBallEnv
   11 | 
   12 | def train_teeball():
   13 |     print("🚀 Starting Phase 1-A: Tee-ball RL Training...")
   14 |     
   15 |     # 1. Create and wrap the environment
   16 |     env = TeeBallEnv(xml_path="shared_assets/h1_baseball.xml", render_mode=None)
   17 |     env = Monitor(env) # For tracking rewards and episode lengths
   18 |     
   19 |     # 2. Set up the PPO agent
   20 |     model = PPO(
   21 |         "MlpPolicy",
   22 |         env,
   23 |         verbose=1,
   24 |         learning_rate=3e-4,
   25 |         n_steps=1024,
   26 |         batch_size=64,
   27 |         gamma=0.99,
   28 |         tensorboard_log="./runs/teeball_tensorboard/"
   29 |     )
   30 |     
   31 |     # 3. Callbacks for evaluation and early stopping
   32 |     eval_callback = EvalCallback(
   33 |         env,
   34 |         best_model_save_path='./checkpoints/teeball_best_model',
   35 |         log_path='./runs/teeball_eval',
   36 |         eval_freq=2000,
   37 |         deterministic=True,
   38 |         render=False
   39 |     )
   40 |     
   41 |     # 4. Train the agent
   42 |     print("🧠 Training starting... (Use Ctrl+C to stop early)")
   43 |     try:
   44 |         model.learn(total_timesteps=50000, callback=eval_callback)
   45 |     except KeyboardInterrupt:
   46 |         print("Training interrupted manually.")
   47 |     finally:
   48 |         # Save the final model
   49 |         model.save("./checkpoints/teeball_final_model")
   50 |         print("✅ Model saved to ./checkpoints/teeball_final_model")
   51 |         env.close()
   52 | 
   53 | if __name__ == "__main__":
   54 |     train_teeball()
````
