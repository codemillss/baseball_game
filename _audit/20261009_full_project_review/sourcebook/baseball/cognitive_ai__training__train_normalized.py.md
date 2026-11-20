# baseball/cognitive_ai/training/train_normalized.py

원본: [cognitive_ai/training/train_normalized.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_normalized.py)

SHA256: `a6894c724091114c7cecfdc2099ae92d84ff5bb17719909414bdf360b9383480`

전체 46행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `train_normalized` | FunctionDef | 9 | 43 |
| `make_env` | FunctionDef | 12 | 13 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    4 | from stable_baselines3 import PPO
    5 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    6 | from stable_baselines3.common.callbacks import EvalCallback
    7 | from cognitive_ai.envs.soft_toss_env import SoftTossEnv
    8 | 
    9 | def train_normalized():
   10 |     print("🚀 Training Soft-Toss with VecNormalize...")
   11 |     
   12 |     def make_env():
   13 |         return SoftTossEnv()
   14 |         
   15 |     vec_env = DummyVecEnv([make_env])
   16 |     vec_env = VecNormalize(vec_env, norm_obs=True, norm_reward=False, clip_obs=10.)
   17 |     
   18 |     eval_env = DummyVecEnv([make_env])
   19 |     eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
   20 |     
   21 |     eval_callback = EvalCallback(
   22 |         eval_env,
   23 |         best_model_save_path='./checkpoints/soft_toss_best_model',
   24 |         eval_freq=2000,
   25 |         n_eval_episodes=20,
   26 |         deterministic=True
   27 |     )
   28 |     
   29 |     model = PPO(
   30 |         "MlpPolicy",
   31 |         vec_env,
   32 |         verbose=1,
   33 |         learning_rate=1e-3,
   34 |         n_steps=1024,
   35 |         batch_size=64,
   36 |         ent_coef=0.005,
   37 |         gamma=0.99
   38 |     )
   39 |     
   40 |     model.learn(total_timesteps=80000, callback=eval_callback)
   41 |     model.save("./checkpoints/soft_toss_final_model")
   42 |     vec_env.save("./checkpoints/soft_toss_vec_normalize.pkl")
   43 |     print("✅ Training Complete with VecNormalize!")
   44 | 
   45 | if __name__ == "__main__":
   46 |     train_normalized()
````
