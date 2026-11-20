# baseball/cognitive_ai/scripts/test_accurate.py

원본: [cognitive_ai/scripts/test_accurate.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_accurate.py)

SHA256: `6976e1db62e75fc846ef703c154cecef15155fd6805007acaa9cba456a005cab`

전체 41행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test_accurate_contact` | FunctionDef | 9 | 38 |

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
    9 | def test_accurate_contact():
   10 |     env = SoftTossEnv()
   11 |     
   12 |     # Ball travels along X=0.0 to Y=0.20
   13 |     # Let's test trigger distances when ball reaches Y=0.20
   14 |     
   15 |     print("Testing trigger distances with ball crossing Y=0.20m:")
   16 |     for trig_y in np.linspace(1.2, 2.2, 11):
   17 |         hits = 0
   18 |         min_dists = []
   19 |         for _ in range(5):
   20 |             env.reset()
   21 |             # Ball spawns at Y=4.0, X=0.0
   22 |             for step in range(45):
   23 |                 ball_y = env.data.qpos[env.ball_qpos_adr+1]
   24 |                 ball_z = env.data.qpos[env.ball_qpos_adr+2]
   25 |                 
   26 |                 trigger = 1.0 if ball_y <= trig_y else -1.0
   27 |                 target_z = (ball_z - 0.80) / 0.15
   28 |                 action = np.array([trigger, target_z], dtype=np.float32)
   29 |                 
   30 |                 obs, reward, term, trunc, _ = env.step(action)
   31 |                 if reward > 50:
   32 |                     hits += 1
   33 |                     break
   34 |                 if term or trunc:
   35 |                     min_dists.append(env.min_dist)
   36 |                     break
   37 |         avg_d = np.mean(min_dists) if min_dists else 0.0
   38 |         print(f"Trigger Y = {trig_y:.2f}m -> Hit Rate: {hits}/5 ({(hits/5)*100:.0f}%), Min Dist: {avg_d:.3f}m")
   39 | 
   40 | if __name__ == "__main__":
   41 |     test_accurate_contact()
````
