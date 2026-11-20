# baseball/scripts/patches/debug_match.py

원본: [scripts/patches/debug_match.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/debug_match.py)

SHA256: `c6dbf4fd838332a3c133414eec24088d7928906e4a8ff111e4063570bf3e17ce`

전체 35행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `make_b_env` | FunctionDef | 6 | 11 |

## 전체 원문

````text
    1 | from stable_baselines3 import PPO
    2 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    3 | from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
    4 | import numpy as np
    5 | 
    6 | def make_b_env(): 
    7 |     return BatterMatchTrainingEnv(
    8 |         pitcher_model_path="checkpoints/mocap_pitcher_best/best_model",
    9 |         pitcher_norm_path="checkpoints/mocap_pitcher_vec_normalize.pkl",
   10 |         is_eval_mode=True
   11 |     )
   12 | 
   13 | b_vec = DummyVecEnv([make_b_env])
   14 | b_norm = VecNormalize.load("checkpoints/mocap_batter_vec_normalize.pkl", b_vec)
   15 | b_norm.training = False
   16 | b_norm.norm_reward = False
   17 | 
   18 | b_model = PPO.load("checkpoints/mocap_batter_best/best_model", env=b_norm)
   19 | 
   20 | b_env = b_vec.envs[0].match_env
   21 | 
   22 | obs = b_vec.reset()
   23 | done = False
   24 | 
   25 | step = 0
   26 | while not done:
   27 |     action, _ = b_model.predict(obs, deterministic=True)
   28 |     obs, reward, dones, infos = b_vec.step(action)
   29 |     done = dones[0]
   30 |     info = infos[0]
   31 |     
   32 |     print(f"Step {step}: p_throw_progress={b_env.p_throw_progress:.3f}, is_rel={b_env.is_released}, pitch_speed={b_env.pitch_speed_kmh:.1f}, ball_y={b_env.data.qpos[b_env.ball_qpos_adr+1]:.1f}")
   33 |     step += 1
   34 | 
   35 | print("Done! Outcome:", info.get('outcome'))
````
