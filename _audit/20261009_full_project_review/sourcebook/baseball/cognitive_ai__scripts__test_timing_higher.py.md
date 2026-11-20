# baseball/cognitive_ai/scripts/test_timing_higher.py

원본: [cognitive_ai/scripts/test_timing_higher.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_timing_higher.py)

SHA256: `8ce7c61053feed0d9bada7cbea2ee88499f06f8f701261d870955dfaace04abc`

전체 38행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test_timing_higher` | FunctionDef | 9 | 35 |

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
    9 | def test_timing_higher():
   10 |     env = SoftTossEnv()
   11 |     
   12 |     print("Testing trigger distance around Y=1.4m ~ 2.2m...")
   13 |     
   14 |     for trig_y in np.linspace(1.4, 2.2, 17):
   15 |         hits = 0
   16 |         min_dists = []
   17 |         for _ in range(10):
   18 |             env.reset()
   19 |             for step in range(45):
   20 |                 ball_y = env.data.qpos[env.ball_qpos_adr+1]
   21 |                 ball_z = env.data.qpos[env.ball_qpos_adr+2]
   22 |                 
   23 |                 trigger = 1.0 if ball_y <= trig_y else -1.0
   24 |                 target_z = (ball_z - 0.80) / 0.15
   25 |                 action = np.array([trigger, target_z], dtype=np.float32)
   26 |                 
   27 |                 obs, reward, term, trunc, _ = env.step(action)
   28 |                 if reward > 50:
   29 |                     hits += 1
   30 |                     break
   31 |                 if term or trunc:
   32 |                     min_dists.append(env.min_dist)
   33 |                     break
   34 |         avg_min_dist = np.mean(min_dists) if min_dists else 0.0
   35 |         print(f"Trigger Y = {trig_y:.2f}m -> Hit Rate: {hits}/10 ({(hits/10)*100:.0f}%), Avg Min Dist: {avg_min_dist:.3f}m")
   36 | 
   37 | if __name__ == "__main__":
   38 |     test_timing_higher()
````
