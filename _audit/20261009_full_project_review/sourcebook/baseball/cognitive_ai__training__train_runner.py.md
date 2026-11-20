# baseball/cognitive_ai/training/train_runner.py

원본: [cognitive_ai/training/train_runner.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_runner.py)

SHA256: `51fe424fb261ad0919a2b48fadca3d1e9b1a5a45a0ff0ebfbcb02069c0dc6e83`

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
    7 | from cognitive_ai.envs.runner_env import RunnerEnv
    8 | 
    9 | def make_env():
   10 |     return RunnerEnv()
   11 | 
   12 | if __name__ == "__main__":
   13 |     num_envs = 16
   14 |     env = SubprocVecEnv([make_env for _ in range(num_envs)])
   15 |     env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
   16 |     
   17 |     model = PPO("MlpPolicy", env, verbose=1, n_steps=512, batch_size=256,
   18 |                 learning_rate=3e-4, clip_range=0.2, ent_coef=0.01)
   19 |                 
   20 |     print("Training Runner...")
   21 |     model.learn(total_timesteps=100_000)
   22 |     
   23 |     os.makedirs("checkpoints/runner", exist_ok=True)
   24 |     model.save("checkpoints/runner/best_model")
   25 |     env.save("checkpoints/runner/vec_normalize.pkl")
   26 |     print("Runner training complete!")
````
