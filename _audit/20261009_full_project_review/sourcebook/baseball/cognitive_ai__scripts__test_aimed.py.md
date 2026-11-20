# baseball/cognitive_ai/scripts/test_aimed.py

원본: [cognitive_ai/scripts/test_aimed.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_aimed.py)

SHA256: `d4619d4b2c9b6a6313f9a1e6e512a77f5f351f259c70027d19db27a7d5b4d148`

전체 43행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test_aimed_toss` | FunctionDef | 9 | 40 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | import numpy as np
    4 | import mujoco
    5 | 
    6 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    7 | from cognitive_ai.envs.soft_toss_env import SoftTossEnv
    8 | 
    9 | def test_aimed_toss():
   10 |     env = SoftTossEnv()
   11 |     
   12 |     # Ball aims at X=-0.15 at plate (Y=0.55)
   13 |     # Start at Y=4.0, X=0.0 -> delta_y = -3.45, delta_x = -0.15
   14 |     # vx = vy * (delta_x / delta_y) = -8.0 * (-0.15 / -3.45) = -0.347 m/s
   15 |     
   16 |     for trig_y in np.linspace(1.2, 2.0, 17):
   17 |         hits = 0
   18 |         min_dists = []
   19 |         for vz in [1.5, 1.7, 1.9]:
   20 |             env.reset()
   21 |             env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3] = [0.0, 4.0, 1.0]
   22 |             env.data.qvel[env.ball_qvel_adr:env.ball_qvel_adr+3] = [-0.35, -8.0, vz]
   23 |             
   24 |             for step in range(45):
   25 |                 ball_y = env.data.qpos[env.ball_qpos_adr+1]
   26 |                 ball_z = env.data.qpos[env.ball_qpos_adr+2]
   27 |                 
   28 |                 trigger = 1.0 if ball_y <= trig_y else -1.0
   29 |                 target_z = (ball_z - 0.80) / 0.15
   30 |                 action = np.array([trigger, target_z], dtype=np.float32)
   31 |                 
   32 |                 obs, reward, term, trunc, _ = env.step(action)
   33 |                 if reward > 50:
   34 |                     hits += 1
   35 |                     break
   36 |                 if term or trunc:
   37 |                     min_dists.append(env.min_dist)
   38 |                     break
   39 |         avg_d = np.mean(min_dists) if min_dists else 0.0
   40 |         print(f"Trigger Y = {trig_y:.2f}m -> Hit: {hits}/3, Min Dist: {avg_d:.3f}m")
   41 | 
   42 | if __name__ == "__main__":
   43 |     test_aimed_toss()
````
