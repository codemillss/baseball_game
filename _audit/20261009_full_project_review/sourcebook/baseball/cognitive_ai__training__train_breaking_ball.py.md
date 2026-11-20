# baseball/cognitive_ai/training/train_breaking_ball.py

원본: [cognitive_ai/training/train_breaking_ball.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_breaking_ball.py)

SHA256: `bb1af2c30ce65a8ce73c56e4e47e773100959c9559a9407a9b5d079cf23974e7`

전체 48행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `train_breaking_balls` | FunctionDef | 10 | 45 |
| `make_env` | FunctionDef | 14 | 15 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    4 | 
    5 | from stable_baselines3 import PPO
    6 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    7 | from stable_baselines3.common.callbacks import EvalCallback
    8 | from cognitive_ai.envs.breaking_ball_env import BreakingBallEnv
    9 | 
   10 | def train_breaking_balls():
   11 |     print("🚀 Training 3D Swing Policy on Breaking Balls (Fastball, Slider, Curveball)...")
   12 |     os.makedirs("./checkpoints/breaking_ball_best", exist_ok=True)
   13 |     
   14 |     def make_env():
   15 |         return BreakingBallEnv()
   16 |         
   17 |     vec_env = DummyVecEnv([make_env])
   18 |     vec_env = VecNormalize(vec_env, norm_obs=True, norm_reward=False, clip_obs=10.)
   19 |     
   20 |     eval_env = DummyVecEnv([make_env])
   21 |     eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
   22 |     
   23 |     eval_cb = EvalCallback(
   24 |         eval_env,
   25 |         best_model_save_path='./checkpoints/breaking_ball_best',
   26 |         eval_freq=2000,
   27 |         n_eval_episodes=25,
   28 |         deterministic=True
   29 |     )
   30 |     
   31 |     model = PPO(
   32 |         "MlpPolicy",
   33 |         vec_env,
   34 |         verbose=1,
   35 |         learning_rate=1e-3,
   36 |         n_steps=1024,
   37 |         batch_size=64,
   38 |         ent_coef=0.01,
   39 |         gamma=0.99
   40 |     )
   41 |     
   42 |     model.learn(total_timesteps=100000, callback=eval_cb)
   43 |     model.save("./checkpoints/breaking_ball_final_model")
   44 |     vec_env.save("./checkpoints/breaking_ball_vec_normalize.pkl")
   45 |     print("🎉 Breaking Ball Training Complete!")
   46 | 
   47 | if __name__ == "__main__":
   48 |     train_breaking_balls()
````
