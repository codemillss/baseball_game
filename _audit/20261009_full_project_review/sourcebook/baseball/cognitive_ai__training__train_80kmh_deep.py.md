# baseball/cognitive_ai/training/train_80kmh_deep.py

원본: [cognitive_ai/training/train_80kmh_deep.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_80kmh_deep.py)

SHA256: `215bce4175c35cb5e28b1d8c8c4dfde8f3be6281cb965a2500cbc45f70be1de9`

전체 48행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `train_80kmh_deep` | FunctionDef | 10 | 45 |
| `make_env` | FunctionDef | 13 | 14 |

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
   10 | def train_80kmh_deep():
   11 |     print("🚀 Deep Training on 80 km/h Pitches (150k steps)...")
   12 |     
   13 |     def make_env():
   14 |         return PitchingMachineEnv(target_speed_kmh=80)
   15 |         
   16 |     vec_env = DummyVecEnv([make_env])
   17 |     vec_env = VecNormalize(vec_env, norm_obs=True, norm_reward=False, clip_obs=10.)
   18 |     
   19 |     eval_env = DummyVecEnv([make_env])
   20 |     eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
   21 |     
   22 |     eval_cb = EvalCallback(
   23 |         eval_env,
   24 |         best_model_save_path='./checkpoints/pitching_80kmh_deep_best',
   25 |         eval_freq=2500,
   26 |         n_eval_episodes=30,
   27 |         deterministic=True
   28 |     )
   29 |     
   30 |     model = PPO(
   31 |         "MlpPolicy",
   32 |         vec_env,
   33 |         verbose=1,
   34 |         learning_rate=5e-4,
   35 |         n_steps=2048,
   36 |         batch_size=64,
   37 |         n_epochs=10,
   38 |         ent_coef=0.01,
   39 |         gamma=0.99
   40 |     )
   41 |     
   42 |     model.learn(total_timesteps=150000, callback=eval_cb)
   43 |     model.save("./checkpoints/pitching_80kmh_deep_final")
   44 |     vec_env.save("./checkpoints/pitching_80kmh_deep_norm.pkl")
   45 |     print("✅ Deep 80 km/h Training Complete!")
   46 | 
   47 | if __name__ == "__main__":
   48 |     train_80kmh_deep()
````
