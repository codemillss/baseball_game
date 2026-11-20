# baseball/cognitive_ai/scripts/debug_miss.py

원본: [cognitive_ai/scripts/debug_miss.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/debug_miss.py)

SHA256: `6a49d7bc73ba4ec921af60a94931c8d51f3048406a143c4d08010fd90ec6823b`

전체 33행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `debug_miss` | FunctionDef | 9 | 30 |

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
    9 | def debug_miss():
   10 |     env = SoftTossEnv()
   11 |     env.reset()
   12 |     
   13 |     # Soft toss at vy = -8.0 m/s
   14 |     trig_y = 1.50
   15 |     for step in range(45):
   16 |         ball_pos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3].copy()
   17 |         trigger = 1.0 if ball_pos[1] <= trig_y else -1.0
   18 |         
   19 |         obs, reward, term, trunc, _ = env.step(np.array([trigger, 0.0], dtype=np.float32))
   20 |         
   21 |         if env.swing_active:
   22 |             bat_pos = env.data.geom_xpos[env.bat_geom_id]
   23 |             diff = bat_pos - ball_pos
   24 |             print(f"Step {step:2d} (Swing {env.swing_progress:.2f}): Bat=({bat_pos[0]:.2f}, {bat_pos[1]:.2f}, {bat_pos[2]:.2f}), Ball=({ball_pos[0]:.2f}, {ball_pos[1]:.2f}, {ball_pos[2]:.2f}), Diff=({diff[0]:.2f}, {diff[1]:.2f}, {diff[2]:.2f}), Dist={np.linalg.norm(diff):.3f}m")
   25 |             
   26 |         if reward > 50:
   27 |             print("💥 HIT!")
   28 |             break
   29 |         if term or trunc:
   30 |             break
   31 | 
   32 | if __name__ == "__main__":
   33 |     debug_miss()
````
