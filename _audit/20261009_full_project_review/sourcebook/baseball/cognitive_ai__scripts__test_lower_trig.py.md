# baseball/cognitive_ai/scripts/test_lower_trig.py

원본: [cognitive_ai/scripts/test_lower_trig.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_lower_trig.py)

SHA256: `033b6de02a340312768b8cafff0cf947c0691410b09c3e03059e8efb2e3b8265`

전체 35행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test_lower_trig` | FunctionDef | 9 | 32 |

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
    9 | def test_lower_trig():
   10 |     env = SoftTossEnv()
   11 |     for trig_y in np.linspace(0.40, 0.80, 9):
   12 |         hits = 0
   13 |         min_dists = []
   14 |         for _ in range(10):
   15 |             env.reset()
   16 |             for step in range(45):
   17 |                 ball_y = env.data.qpos[env.ball_qpos_adr+1]
   18 |                 ball_z = env.data.qpos[env.ball_qpos_adr+2]
   19 |                 
   20 |                 trigger = 1.0 if ball_y <= trig_y else -1.0
   21 |                 target_z = (ball_z - 0.80) / 0.15
   22 |                 action = np.array([trigger, target_z], dtype=np.float32)
   23 |                 
   24 |                 obs, reward, term, trunc, _ = env.step(action)
   25 |                 if reward > 50:
   26 |                     hits += 1
   27 |                     break
   28 |                 if term or trunc:
   29 |                     min_dists.append(env.min_dist)
   30 |                     break
   31 |         avg_d = np.mean(min_dists) if min_dists else 0.0
   32 |         print(f"Trigger Y = {trig_y:.2f}m -> Hit: {hits}/10 ({(hits/10)*100:.0f}%), Min Dist: {avg_d:.3f}m")
   33 | 
   34 | if __name__ == "__main__":
   35 |     test_lower_trig()
````
