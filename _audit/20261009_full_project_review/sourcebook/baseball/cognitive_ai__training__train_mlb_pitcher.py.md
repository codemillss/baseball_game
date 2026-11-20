# baseball/cognitive_ai/training/train_mlb_pitcher.py

원본: [cognitive_ai/training/train_mlb_pitcher.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_mlb_pitcher.py)

SHA256: `27a2ab55be695e0faedd8f33f66c49e9051e98cf524e99ffa5738c1f4e1b96e8`

전체 49행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `train_pitcher` | FunctionDef | 10 | 46 |
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
    8 | from cognitive_ai.envs.pitcher_env import PitcherEnv
    9 | 
   10 | def train_pitcher():
   11 |     print("🚀 Training Humanoid Pitcher Policy (Release & Strike Zone Control)...")
   12 |     os.makedirs("./checkpoints/mlb_pitcher_best", exist_ok=True)
   13 |     
   14 |     def make_env():
   15 |         return PitcherEnv()
   16 |         
   17 |     vec_env = DummyVecEnv([make_env])
   18 |     vec_env = VecNormalize(vec_env, norm_obs=True, norm_reward=False, clip_obs=10.)
   19 |     
   20 |     eval_env = DummyVecEnv([make_env])
   21 |     eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
   22 |     
   23 |     eval_cb = EvalCallback(
   24 |         eval_env,
   25 |         best_model_save_path='./checkpoints/mlb_pitcher_best',
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
   38 |         n_epochs=10,
   39 |         ent_coef=0.01,
   40 |         gamma=0.99
   41 |     )
   42 |     
   43 |     model.learn(total_timesteps=200000, callback=eval_cb)
   44 |     model.save("./checkpoints/pitcher_final_model")
   45 |     vec_env.save("./checkpoints/mlb_pitcher_vec_normalize.pkl")
   46 |     print("🎉 Pitcher Training Complete!")
   47 | 
   48 | if __name__ == "__main__":
   49 |     train_pitcher()
````
