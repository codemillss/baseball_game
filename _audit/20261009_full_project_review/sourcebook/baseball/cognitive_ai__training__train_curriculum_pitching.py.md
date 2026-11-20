# baseball/cognitive_ai/training/train_curriculum_pitching.py

원본: [cognitive_ai/training/train_curriculum_pitching.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_curriculum_pitching.py)

SHA256: `d68da7821fa393a213e52a72a8f2264c7532b5a095d5c6991443fc0b9ac32df7`

전체 92행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `train_curriculum` | FunctionDef | 10 | 89 |
| `make_env_50` | FunctionDef | 21 | 22 |
| `make_env_80` | FunctionDef | 61 | 62 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    4 | 
    5 | from stable_baselines3 import PPO
    6 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    7 | from stable_baselines3.common.callbacks import EvalCallback
    8 | from cognitive_ai.envs.pitching_machine_env import PitchingMachineEnv
    9 | 
   10 | def train_curriculum():
   11 |     os.makedirs("./checkpoints/pitching_50kmh_best", exist_ok=True)
   12 |     os.makedirs("./checkpoints/pitching_80kmh_best", exist_ok=True)
   13 |     
   14 |     # ----------------------------------------------------
   15 |     # STAGE 1: 50~55 km/h Training (10m Distance)
   16 |     # ----------------------------------------------------
   17 |     print("\n" + "="*50)
   18 |     print("🚀 STAGE 1: Training on 50~55 km/h Pitches (10m Distance)...")
   19 |     print("="*50)
   20 |     
   21 |     def make_env_50():
   22 |         return PitchingMachineEnv(target_speed_kmh=50)
   23 |         
   24 |     vec_env_50 = DummyVecEnv([make_env_50])
   25 |     vec_env_50 = VecNormalize(vec_env_50, norm_obs=True, norm_reward=False, clip_obs=10.)
   26 |     
   27 |     eval_env_50 = DummyVecEnv([make_env_50])
   28 |     eval_env_50 = VecNormalize(eval_env_50, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
   29 |     
   30 |     eval_cb_50 = EvalCallback(
   31 |         eval_env_50,
   32 |         best_model_save_path='./checkpoints/pitching_50kmh_best',
   33 |         eval_freq=2000,
   34 |         n_eval_episodes=20,
   35 |         deterministic=True
   36 |     )
   37 |     
   38 |     model_50 = PPO(
   39 |         "MlpPolicy",
   40 |         vec_env_50,
   41 |         verbose=1,
   42 |         learning_rate=1e-3,
   43 |         n_steps=1024,
   44 |         batch_size=64,
   45 |         ent_coef=0.005,
   46 |         gamma=0.99
   47 |     )
   48 |     
   49 |     model_50.learn(total_timesteps=60000, callback=eval_cb_50)
   50 |     model_50.save("./checkpoints/pitching_50kmh_final_model")
   51 |     vec_env_50.save("./checkpoints/pitching_50kmh_vec_normalize.pkl")
   52 |     print("✅ Stage 1 (50 km/h) Complete!")
   53 |     
   54 |     # ----------------------------------------------------
   55 |     # STAGE 2: 75~80 km/h Fine-tuning (15m Distance)
   56 |     # ----------------------------------------------------
   57 |     print("\n" + "="*50)
   58 |     print("🚀 STAGE 2: Transferring & Training on 75~80 km/h Pitches (15m Distance)...")
   59 |     print("="*50)
   60 |     
   61 |     def make_env_80():
   62 |         return PitchingMachineEnv(target_speed_kmh=80)
   63 |         
   64 |     vec_env_80 = DummyVecEnv([make_env_80])
   65 |     vec_env_80 = VecNormalize(vec_env_80, norm_obs=True, norm_reward=False, clip_obs=10.)
   66 |     
   67 |     eval_env_80 = DummyVecEnv([make_env_80])
   68 |     eval_env_80 = VecNormalize(eval_env_80, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
   69 |     
   70 |     eval_cb_80 = EvalCallback(
   71 |         eval_env_80,
   72 |         best_model_save_path='./checkpoints/pitching_80kmh_best',
   73 |         eval_freq=2000,
   74 |         n_eval_episodes=20,
   75 |         deterministic=True
   76 |     )
   77 |     
   78 |     # Load Stage 1 weights and transfer to 80 km/h
   79 |     model_80 = PPO.load(
   80 |         "./checkpoints/pitching_50kmh_best/best_model",
   81 |         env=vec_env_80,
   82 |         learning_rate=1e-3,
   83 |         ent_coef=0.01
   84 |     )
   85 |     
   86 |     model_80.learn(total_timesteps=80000, callback=eval_cb_80)
   87 |     model_80.save("./checkpoints/pitching_80kmh_final_model")
   88 |     vec_env_80.save("./checkpoints/pitching_80kmh_vec_normalize.pkl")
   89 |     print("🎉 STAGE 2 (80 km/h) Curriculum Training Complete!")
   90 | 
   91 | if __name__ == "__main__":
   92 |     train_curriculum()
````
