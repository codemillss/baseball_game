# baseball/scripts/patches/check_obs.py

원본: [scripts/patches/check_obs.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/check_obs.py)

SHA256: `e4cc740c20f658e9106e7b20760dd303f91aa7d28e98c85465b91cf2d9e2c5f3`

전체 18행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import numpy as np
    2 | import mujoco
    3 | from cognitive_ai.envs.pitcher_env import PitcherEnv
    4 | from cognitive_ai.envs.baseball_match_env import BaseballMatchEnv
    5 | 
    6 | p_env = PitcherEnv()
    7 | p_env.reset()
    8 | obs1 = p_env._get_obs()
    9 | 
   10 | b_env = BaseballMatchEnv()
   11 | b_env.reset()
   12 | obs2, _ = b_env.get_observations()
   13 | 
   14 | print(f"PitcherEnv obs shape: {obs1.shape}")
   15 | print(f"BaseballMatchEnv obs shape: {obs2.shape}")
   16 | 
   17 | print("PitcherEnv Obs:", obs1)
   18 | print("BaseballMatchEnv Obs:", obs2)
````
