# baseball/cognitive_ai/scripts/test_trigger.py

원본: [cognitive_ai/scripts/test_trigger.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_trigger.py)

SHA256: `80e06f688873ce5f71b01e33643065aab4f6640cee954b6b3e4151e54a82a875`

전체 39행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test_trigger_y` | FunctionDef | 9 | 36 |

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
    9 | def test_trigger_y():
   10 |     env = SoftTossEnv()
   11 |     
   12 |     print("Testing trigger_y values for Soft-Toss...")
   13 |     
   14 |     for trig_y in np.linspace(1.5, 3.0, 16):
   15 |         hits = 0
   16 |         for _ in range(5):
   17 |             env.reset()
   18 |             # Ball travels at ~8m/s
   19 |             for step in range(45):
   20 |                 ball_y = env.data.qpos[env.ball_qpos_adr+1]
   21 |                 ball_z = env.data.qpos[env.ball_qpos_adr+2]
   22 |                 
   23 |                 # If ball has reached trigger_y, swing!
   24 |                 trigger = 1.0 if ball_y <= trig_y else -1.0
   25 |                 
   26 |                 # Z action using our Phase 1-A formula: (ball_z - 0.80) / 0.15
   27 |                 target_z = (ball_z - 0.80) / 0.15
   28 |                 action = np.array([trigger, target_z], dtype=np.float32)
   29 |                 
   30 |                 obs, reward, term, trunc, _ = env.step(action)
   31 |                 if reward > 50:
   32 |                     hits += 1
   33 |                     break
   34 |                 if term or trunc:
   35 |                     break
   36 |         print(f"Trigger Y = {trig_y:.2f}m -> Hit Rate: {hits}/5 ({(hits/5)*100:.0f}%)")
   37 | 
   38 | if __name__ == "__main__":
   39 |     test_trigger_y()
````
