# baseball/cognitive_ai/scripts/test_grid.py

원본: [cognitive_ai/scripts/test_grid.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_grid.py)

SHA256: `2edd577dbbed3f244ab8495c5acb8053b0f206734c145ab5a9f3e5212f790ac1`

전체 50행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test_grid` | FunctionDef | 9 | 47 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | import numpy as np
    4 | import mujoco
    5 | 
    6 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    7 | from cognitive_ai.envs.teeball_env import TeeBallEnv
    8 | 
    9 | def test_grid():
   10 |     env = TeeBallEnv()
   11 |     test_zs = np.linspace(0.65, 0.95, 13) # 13 heights from 0.65m to 0.95m
   12 |     test_actions = np.linspace(-1.0, 1.0, 21) # 21 actions from -1.0 to 1.0
   13 |     
   14 |     print("Testing grid of ball heights and actions...")
   15 |     
   16 |     success_map = {}
   17 |     
   18 |     for z in test_zs:
   19 |         success_map[round(z, 3)] = []
   20 |         for a in test_actions:
   21 |             env.reset()
   22 |             # Override ball z
   23 |             env.data.qpos[env.ball_qpos_adr+2] = z
   24 |             mujoco.mj_forward(env.model, env.data)
   25 |             
   26 |             action = np.array([a], dtype=np.float32)
   27 |             done = False
   28 |             hit = False
   29 |             while not done:
   30 |                 obs, reward, terminated, truncated, _ = env.step(action)
   31 |                 done = terminated or truncated
   32 |                 if reward > 50:
   33 |                     hit = True
   34 |                     break
   35 |             if hit:
   36 |                 success_map[round(z, 3)].append(round(a, 2))
   37 |                 
   38 |     print("\n--- Grid Reachability Results ---")
   39 |     reachable_count = 0
   40 |     for z, actions in success_map.items():
   41 |         if len(actions) > 0:
   42 |             reachable_count += 1
   43 |             print(f"Ball Z={z:.3f}m : Reachable with actions {actions[:3]}... (Total {len(actions)} valid actions)")
   44 |         else:
   45 |             print(f"Ball Z={z:.3f}m : ❌ UNREACHABLE with any action")
   46 |             
   47 |     print(f"\nOverall Reachability: {reachable_count}/{len(test_zs)} ({(reachable_count/len(test_zs))*100:.1f}%)")
   48 | 
   49 | if __name__ == "__main__":
   50 |     test_grid()
````
