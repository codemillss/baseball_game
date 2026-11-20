# baseball/scripts/patches/print_act.py

원본: [scripts/patches/print_act.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/print_act.py)

SHA256: `dcf7535ffd50ced88c44646cf9513896fa040c0980eea5067ef0c20fb795e974`

전체 26행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | from stable_baselines3 import PPO
    2 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    3 | from cognitive_ai.envs.baseball_match_env import BaseballMatchEnv
    4 | from cognitive_ai.envs.pitcher_env import PitcherEnv
    5 | import numpy as np
    6 | 
    7 | p_model = PPO.load("checkpoints/mocap_pitcher_best/best_model")
    8 | 
    9 | env = BaseballMatchEnv()
   10 | env.target_x = 0.0
   11 | env.target_z = 0.8
   12 | env.target_pitch_type = 0
   13 | obs = env.get_observations()
   14 | p_obs = obs["pitcher"]
   15 | print(f"p_obs: {p_obs}")
   16 | 
   17 | dummy = PitcherEnv()
   18 | p_norm = VecNormalize.load("checkpoints/mocap_pitcher_vec_normalize.pkl", DummyVecEnv([lambda: dummy]))
   19 | p_norm.training = False
   20 | 
   21 | # We must reshape p_obs to (1, 16)
   22 | p_norm_obs = p_norm.normalize_obs(p_obs.reshape(1, -1))
   23 | print(f"p_norm_obs: {p_norm_obs}")
   24 | 
   25 | p_action, _ = p_model.predict(p_norm_obs, deterministic=True)
   26 | print(f"p_action: {p_action}")
````
