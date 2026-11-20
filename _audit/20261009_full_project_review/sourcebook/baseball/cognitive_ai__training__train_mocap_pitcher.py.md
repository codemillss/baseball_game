# baseball/cognitive_ai/training/train_mocap_pitcher.py

원본: [cognitive_ai/training/train_mocap_pitcher.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_mocap_pitcher.py)

SHA256: `bb2531fb4121d4623375a02c2187a424654cbdcb7e7815e5562e027f499c7656`

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
   11 |     print("🚀 Fine-tuning MoCap Pitcher Policy (Ohtani Style Kinematics)...")
   12 |     os.makedirs("./checkpoints/mocap_pitcher_best", exist_ok=True)
   13 |     
   14 |     def make_env():
   15 |         return PitcherEnv()
   16 |         
   17 |     vec_env = DummyVecEnv([make_env])
   18 |     # Load old VecNormalize
   19 |     vec_env = VecNormalize.load("./checkpoints/mlb_pitcher_vec_normalize.pkl", vec_env)
   20 |     vec_env.training = True
   21 |     vec_env.norm_reward = False
   22 |     
   23 |     eval_env = DummyVecEnv([make_env])
   24 |     eval_env = VecNormalize.load("./checkpoints/mlb_pitcher_vec_normalize.pkl", eval_env)
   25 |     eval_env.training = False
   26 |     eval_env.norm_reward = False
   27 |     
   28 |     eval_cb = EvalCallback(
   29 |         eval_env,
   30 |         best_model_save_path='./checkpoints/mocap_pitcher_best',
   31 |         eval_freq=2000,
   32 |         n_eval_episodes=25,
   33 |         deterministic=True
   34 |     )
   35 |     
   36 |     # Load old pre-trained model!
   37 |     print("Loading pre-trained mlb_pitcher_best...")
   38 |     model = PPO.load("./checkpoints/mlb_pitcher_best/best_model", env=vec_env, custom_objects={
   39 |         "learning_rate": 5e-4, # Lower LR for fine-tuning
   40 |         "ent_coef": 0.05       # Slight exploration to find new aim points
   41 |     })
   42 |     
   43 |     # Fine-tune for only 50k steps (since it already knows how to pitch!)
   44 |     model.learn(total_timesteps=60000, callback=eval_cb)
   45 |     vec_env.save("./checkpoints/mocap_pitcher_vec_normalize.pkl")
   46 |     print("🎉 MoCap Pitcher Fine-tuning Complete!")
   47 | 
   48 | if __name__ == "__main__":
   49 |     train_pitcher()
````
