# baseball/cognitive_ai/scripts/test_direct.py

원본: [cognitive_ai/scripts/test_direct.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_direct.py)

SHA256: `6cf2956b8aef62aa7c35df8e5ab46f087f615f3f3f01c414ea10f87b315a1965`

전체 57행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test_kinematics_direct` | FunctionDef | 9 | 54 |

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
    9 | def test_kinematics_direct():
   10 |     env = TeeBallEnv()
   11 |     test_zs = np.linspace(0.65, 0.95, 13)
   12 |     
   13 |     print("Directly testing keyframe kinematics for ball heights:")
   14 |     
   15 |     reachable = 0
   16 |     for z in test_zs:
   17 |         valid_adj = []
   18 |         for adj in np.linspace(-1.5, 1.0, 51):
   19 |             env.reset()
   20 |             env.data.qpos[env.ball_qpos_adr+2] = z
   21 |             mujoco.mj_forward(env.model, env.data)
   22 |             
   23 |             # Set keyframe
   24 |             kfs = env.base_keyframes.copy()
   25 |             kfs[3, 1] += adj # Contact shoulder pitch
   26 |             kfs[4, 1] += adj # Follow-through shoulder pitch
   27 |             
   28 |             # Run swing
   29 |             hit = False
   30 |             for p in np.linspace(0, 1, 30):
   31 |                 # Update kinematics
   32 |                 num_kfs = len(kfs)
   33 |                 scaled = p * (num_kfs - 1)
   34 |                 idx1 = int(np.floor(scaled))
   35 |                 idx2 = min(idx1 + 1, num_kfs - 1)
   36 |                 t = scaled - idx1
   37 |                 current_angles = (1-t)*kfs[idx1] + t*kfs[idx2]
   38 |                 
   39 |                 for i, adr in enumerate(env.qpos_adrs):
   40 |                     env.data.qpos[adr] = current_angles[i]
   41 |                 mujoco.mj_forward(env.model, env.data)
   42 |                 
   43 |                 if env._check_contact():
   44 |                     hit = True
   45 |                     break
   46 |             if hit:
   47 |                 valid_adj.append(round(adj, 2))
   48 |         if len(valid_adj) > 0:
   49 |             reachable += 1
   50 |             print(f"Z={z:.3f}m -> ✅ Reachable! (Pitch adj range: {valid_adj[0]} to {valid_adj[-1]})")
   51 |         else:
   52 |             print(f"Z={z:.3f}m -> ❌ Miss")
   53 |             
   54 |     print(f"\nDirect Reachability: {reachable}/{len(test_zs)} ({(reachable/len(test_zs))*100:.1f}%)")
   55 | 
   56 | if __name__ == "__main__":
   57 |     test_kinematics_direct()
````
