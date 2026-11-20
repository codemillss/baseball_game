# baseball/cognitive_ai/training/train_mocap_batter.py

원본: [cognitive_ai/training/train_mocap_batter.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_mocap_batter.py)

SHA256: `f47541a80e17cce77693293aa861696c43c09e33755977cddcb9eb5b10f188e0`

전체 51행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `train_batter` | FunctionDef | 10 | 48 |
| `make_env` | FunctionDef | 15 | 19 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    4 | 
    5 | from stable_baselines3 import PPO
    6 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    7 | from stable_baselines3.common.callbacks import EvalCallback
    8 | from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
    9 | 
   10 | def train_batter():
   11 |     print("🚀 Fine-tuning MoCap Batter Policy (Ohtani Style Kinematics)...")
   12 |     os.makedirs("./checkpoints/mocap_batter_best", exist_ok=True)
   13 |     
   14 |     # We load the mocap_pitcher_best so the Batter faces the MoCap pitcher!
   15 |     def make_env():
   16 |         return BatterMatchTrainingEnv(
   17 |             pitcher_model_path="checkpoints/mocap_pitcher_best/best_model",
   18 |             pitcher_norm_path="checkpoints/mocap_pitcher_vec_normalize.pkl"
   19 |         )
   20 |         
   21 |     vec_env = DummyVecEnv([make_env])
   22 |     vec_env = VecNormalize.load("./checkpoints/mlb_batter_vec_normalize.pkl", vec_env)
   23 |     vec_env.training = True
   24 |     vec_env.norm_reward = False
   25 |     
   26 |     eval_env = DummyVecEnv([make_env])
   27 |     eval_env = VecNormalize.load("./checkpoints/mlb_batter_vec_normalize.pkl", eval_env)
   28 |     eval_env.training = False
   29 |     eval_env.norm_reward = False
   30 |     
   31 |     eval_cb = EvalCallback(
   32 |         eval_env,
   33 |         best_model_save_path='./checkpoints/mocap_batter_best',
   34 |         eval_freq=2000,
   35 |         n_eval_episodes=25,
   36 |         deterministic=True
   37 |     )
   38 |     
   39 |     print("Loading pre-trained mlb_batter_best...")
   40 |     model = PPO.load("./checkpoints/mlb_batter_best/best_model", env=vec_env, custom_objects={
   41 |         "learning_rate": 5e-4,
   42 |         "ent_coef": 0.05
   43 |     })
   44 |     
   45 |     # Fine-tune for 60k steps
   46 |     model.learn(total_timesteps=60000, callback=eval_cb)
   47 |     vec_env.save("./checkpoints/mocap_batter_vec_normalize.pkl")
   48 |     print("🎉 MoCap Batter Fine-tuning Complete!")
   49 | 
   50 | if __name__ == "__main__":
   51 |     train_batter()
````
