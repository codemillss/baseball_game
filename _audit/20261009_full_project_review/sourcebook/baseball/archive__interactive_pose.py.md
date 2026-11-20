# baseball/archive/interactive_pose.py

원본: [archive/interactive_pose.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/interactive_pose.py)

SHA256: `597a274f31793850784182ae61ab7a79f26fa2a13b9c274f1d3b2f6b9408ecc0`

전체 32행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `key_callback` | FunctionDef | 9 | 19 |

## 전체 원문

````text
    1 | import mujoco
    2 | from mujoco import viewer
    3 | import time
    4 | import numpy as np
    5 | 
    6 | model = mujoco.MjModel.from_xml_path('assets/stadium_3d.xml')
    7 | data = mujoco.MjData(model)
    8 | 
    9 | def key_callback(keycode):
   10 |     # Print joint angles when 'P' is pressed
   11 |     if chr(keycode).lower() == 'p':
   12 |         print("\n--- Current Joint Angles (qpos) ---")
   13 |         for i in range(model.nq):
   14 |             # Try to get joint name based on qpos adr mapping
   15 |             for j in range(model.njnt):
   16 |                 if model.jnt_qposadr[j] == i:
   17 |                     joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, j)
   18 |                     print(f"{joint_name}: {data.qpos[i]:.4f}")
   19 |         print("-----------------------------------")
   20 | 
   21 | with viewer.launch_passive(model, data, key_callback=key_callback) as v:
   22 |     print("Interactive Viewer Launched!")
   23 |     print("1. Physics is intentionally PAUSED so you can pose the robot.")
   24 |     print("2. Open the 'Joints' panel on the right side.")
   25 |     print("3. Adjust the sliders. The robot will move immediately.")
   26 |     print("4. Press 'P' on your keyboard to print the current joint angles!")
   27 |     
   28 |     while v.is_running():
   29 |         # Update geometry based on user's GUI slider changes
   30 |         mujoco.mj_forward(model, data)
   31 |         v.sync()
   32 |         time.sleep(0.01)
````
