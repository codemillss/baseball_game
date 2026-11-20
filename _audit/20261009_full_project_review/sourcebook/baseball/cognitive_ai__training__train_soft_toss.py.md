# baseball/cognitive_ai/training/train_soft_toss.py

원본: [cognitive_ai/training/train_soft_toss.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_soft_toss.py)

SHA256: `fe10c7065ce5684b236102af04fc215f8ceeb908ac2c113986d93278ec5221e3`

전체 51행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `train_soft_toss` | FunctionDef | 10 | 48 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | from stable_baselines3 import PPO
    4 | from stable_baselines3.common.callbacks import EvalCallback
    5 | from stable_baselines3.common.monitor import Monitor
    6 | 
    7 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    8 | from cognitive_ai.envs.soft_toss_env import SoftTossEnv
    9 | 
   10 | def train_soft_toss():
   11 |     print("🚀 Starting Phase 1-B: Soft-Toss Batting RL Training (25~30 km/h)...")
   12 |     
   13 |     os.makedirs("./checkpoints/soft_toss_best_model", exist_ok=True)
   14 |     os.makedirs("./runs/soft_toss_eval", exist_ok=True)
   15 |     
   16 |     env = SoftTossEnv()
   17 |     env = Monitor(env)
   18 |     
   19 |     eval_callback = EvalCallback(
   20 |         env,
   21 |         best_model_save_path='./checkpoints/soft_toss_best_model',
   22 |         log_path='./runs/soft_toss_eval',
   23 |         eval_freq=2000,
   24 |         n_eval_episodes=20,
   25 |         deterministic=True
   26 |     )
   27 |     
   28 |     # 2-layer MLP policy for 6-dim input -> 2-dim action
   29 |     model = PPO(
   30 |         "MlpPolicy",
   31 |         env,
   32 |         verbose=1,
   33 |         learning_rate=1e-3,
   34 |         n_steps=1024,
   35 |         batch_size=64,
   36 |         gamma=0.99,
   37 |         gae_lambda=0.95,
   38 |         clip_range=0.2,
   39 |         ent_coef=0.01,
   40 |         tensorboard_log="./runs/soft_toss_tensorboard/"
   41 |     )
   42 |     
   43 |     print("🧠 Training starting for 60,000 steps...")
   44 |     model.learn(total_timesteps=60000, callback=eval_callback)
   45 |     
   46 |     model.save("./checkpoints/soft_toss_final_model")
   47 |     print("✅ Soft-Toss Training Complete! Model saved to ./checkpoints/soft_toss_final_model")
   48 |     env.close()
   49 | 
   50 | if __name__ == "__main__":
   51 |     train_soft_toss()
````
