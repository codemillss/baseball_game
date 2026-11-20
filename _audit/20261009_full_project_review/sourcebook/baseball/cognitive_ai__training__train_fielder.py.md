# baseball/cognitive_ai/training/train_fielder.py

원본: [cognitive_ai/training/train_fielder.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_fielder.py)

SHA256: `a6222c1355a674121bf9ae567351d0552e52e5ed66be7841656459ca2d154a75`

전체 39행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `main` | FunctionDef | 11 | 36 |

## 전체 원문

````text
    1 | import sys
    2 | import os
    3 | sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    4 | 
    5 | from stable_baselines3 import PPO
    6 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    7 | from stable_baselines3.common.callbacks import EvalCallback
    8 | 
    9 | from cognitive_ai.envs.fielder_env import FielderEnv
   10 | 
   11 | def main():
   12 |     env = DummyVecEnv([lambda: FielderEnv()])
   13 |     env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
   14 |     
   15 |     os.makedirs("checkpoints/fielder", exist_ok=True)
   16 |     
   17 |     model = PPO(
   18 |         "MlpPolicy",
   19 |         env,
   20 |         learning_rate=3e-4,
   21 |         n_steps=2048,
   22 |         batch_size=256,
   23 |         n_epochs=10,
   24 |         gamma=0.99,
   25 |         gae_lambda=0.95,
   26 |         clip_range=0.2,
   27 |         ent_coef=0.01,
   28 |         verbose=1,
   29 |         device="cpu"
   30 |     )
   31 |     
   32 |     model.learn(total_timesteps=300000)
   33 |     
   34 |     model.save("checkpoints/fielder/best_model")
   35 |     env.save("checkpoints/fielder/vec_normalize.pkl")
   36 |     print("Fielder training complete!")
   37 | 
   38 | if __name__ == "__main__":
   39 |     main()
````
