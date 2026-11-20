# baseball/cognitive_ai/training/train_catcher.py

원본: [cognitive_ai/training/train_catcher.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_catcher.py)

SHA256: `0c06a7057c454e196e7362235eada6f49ee6ea227ee3e15b7e3e44d1249e8f26`

전체 26행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `make_env` | FunctionDef | 9 | 10 |

## 전체 원문

````text
    1 | import sys
    2 | import os
    3 | sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    4 | 
    5 | from stable_baselines3 import PPO
    6 | from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize
    7 | from cognitive_ai.envs.catcher_env import CatcherEnv
    8 | 
    9 | def make_env():
   10 |     return CatcherEnv()
   11 | 
   12 | if __name__ == "__main__":
   13 |     num_envs = 16
   14 |     env = SubprocVecEnv([make_env for _ in range(num_envs)])
   15 |     env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
   16 |     
   17 |     model = PPO("MlpPolicy", env, verbose=1, n_steps=512, batch_size=256,
   18 |                 learning_rate=3e-4, clip_range=0.2, ent_coef=0.01)
   19 |                 
   20 |     print("Training Catcher...")
   21 |     model.learn(total_timesteps=100_000)
   22 |     
   23 |     os.makedirs("checkpoints/catcher", exist_ok=True)
   24 |     model.save("checkpoints/catcher/best_model")
   25 |     env.save("checkpoints/catcher/vec_normalize.pkl")
   26 |     print("Catcher training complete!")
````
