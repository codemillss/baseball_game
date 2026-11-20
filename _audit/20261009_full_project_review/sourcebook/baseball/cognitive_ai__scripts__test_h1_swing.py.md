# baseball/cognitive_ai/scripts/test_h1_swing.py

원본: [cognitive_ai/scripts/test_h1_swing.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_h1_swing.py)

SHA256: `74be66a4fc9047a92535b614490d2419174bc91918b76686c2478dde989debb2`

전체 57행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test_h1_swing` | FunctionDef | 6 | 54 |

## 전체 원문

````text
    1 | import mujoco
    2 | from mujoco import viewer
    3 | import time
    4 | import numpy as np
    5 | 
    6 | def test_h1_swing():
    7 |     model = mujoco.MjModel.from_xml_path('shared_assets/h1_baseball.xml')
    8 |     data = mujoco.MjData(model)
    9 |     
   10 |     # We will override these joints kinematically
   11 |     j_names = ["root_y", "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"]
   12 |     j_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in j_names]
   13 |     
   14 |     # Dummy keyframes [root_y, torso, rs_p, rs_r, rs_y, r_elbow]
   15 |     # Stance -> Load -> Stride -> Contact -> Follow-through
   16 |     # root_y is kept 0 to prevent the robot from flying (No-stride swing)
   17 |     keyframes = np.array([
   18 |         [0.0, -0.5, -1.0, 0.0, 0.5, 1.5],   # Stance
   19 |         [0.0, -1.0, -1.2, 0.0, 0.8, 2.0],   # Load
   20 |         [0.0, 0.0, -0.5, 0.0, 0.0, 1.0],    # Stride (Hip turn only)
   21 |         [0.0, 1.5, 0.5, 0.0, -0.5, 0.0],    # Contact
   22 |         [0.0, 2.0, 1.0, 0.0, -1.0, 1.5]     # Follow-through
   23 |     ])
   24 |     
   25 |     print("Testing H1 Humanoid Baseball Environment...")
   26 |     
   27 |     with viewer.launch_passive(model, data) as v:
   28 |         # Give it a second to settle equality constraints
   29 |         for _ in range(100):
   30 |             mujoco.mj_step(model, data)
   31 |             
   32 |         t = 0
   33 |         while v.is_running():
   34 |             # Oscillate progress 0 -> 1 -> 0
   35 |             progress = (np.sin(t) + 1) / 2
   36 |             
   37 |             num_kfs = len(keyframes)
   38 |             scaled = progress * (num_kfs - 1)
   39 |             idx1 = int(np.floor(scaled))
   40 |             idx2 = min(idx1 + 1, num_kfs - 1)
   41 |             alpha = scaled - idx1
   42 |             
   43 |             current = (1-alpha)*keyframes[idx1] + alpha*keyframes[idx2]
   44 |             
   45 |             for i, adr in enumerate(j_adrs):
   46 |                 data.qpos[adr] = current[i]
   47 |                 jnt_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, j_names[i])
   48 |                 vel_adr = model.jnt_dofadr[jnt_id]
   49 |                 data.qvel[vel_adr] = 0.0
   50 |                 
   51 |             mujoco.mj_step(model, data)
   52 |             v.sync()
   53 |             time.sleep(0.01)
   54 |             t += 0.02
   55 | 
   56 | if __name__ == "__main__":
   57 |     test_h1_swing()
````
