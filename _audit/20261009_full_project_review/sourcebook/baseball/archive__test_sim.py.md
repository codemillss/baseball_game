# baseball/archive/test_sim.py

원본: [archive/test_sim.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/test_sim.py)

SHA256: `dd3971847e66ec8727420f40edd5258f371b32a87e3ddd7e5722f88ac320185e`

전체 16행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import numpy as np
    2 | from envs.multi_agent_env import MultiAgentBaseballEnv, EnvConfig
    3 | 
    4 | config = EnvConfig(mode="batter_only", is_tee_ball=False, pitch_speed_y=-25.0)
    5 | env = MultiAgentBaseballEnv(config=config, render_mode="rgb_array")
    6 | env.reset()
    7 | 
    8 | print("Initial Ball Pos:", env.data.xpos[env.ball_body_id])
    9 | for i in range(10):
   10 |     actions = {
   11 |         "pitcher": np.zeros(8, dtype=np.float32),
   12 |         "batter": np.zeros(9, dtype=np.float32),
   13 |         "fielder": np.zeros(3, dtype=np.float32)
   14 |     }
   15 |     env.step(actions)
   16 |     print(f"Step {i+1} Ball Pos:", env.data.xpos[env.ball_body_id], "Vel:", env.data.qvel[env.ball_qvel_adr:env.ball_qvel_adr+3])
````
