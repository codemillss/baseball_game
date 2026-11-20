# baseball/archive/simulate_swing.py

원본: [archive/simulate_swing.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/simulate_swing.py)

SHA256: `f21c8d772e0fb6708d099af9ee1b8348fe8d97632544862a5ad114d63a0c5bef`

전체 60행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | import cv2
    3 | import os
    4 | import numpy as np
    5 | 
    6 | model = mujoco.MjModel.from_xml_path('assets/stadium_3d.xml')
    7 | data = mujoco.MjData(model)
    8 | 
    9 | # 7 DOFs: [shoulder_yaw, shoulder_pitch, shoulder_roll, elbow_flex, wrist_yaw, wrist_pitch, wrist_roll]
   10 | keyframes = [
   11 |     # 1. Stance (Ready)
   12 |     [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
   13 |     
   14 |     # 2. Load (Cocking back)
   15 |     [-0.3, 0.1, -0.1, -0.3, -0.2, 0.0, 0.0],
   16 |     
   17 |     # 3. Initiation (Dropping bat into zone)
   18 |     [0.5, -0.2, 0.2, 0.3, 0.2, 0.5, 0.0],
   19 |     
   20 |     # 4. Contact (Bat extended forward to hit the ball)
   21 |     [1.5, -0.4, 0.3, 1.2, 0.5, 0.8, -0.2],
   22 |     
   23 |     # 5. Follow-through (Bat wraps around)
   24 |     [2.2, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0]
   25 | ]
   26 | 
   27 | out_dir = "/Users/jmjeon/.gemini/antigravity-ide/brain/4bdec9f3-e0a2-4d05-aab9-6d6fb58bd3c2"
   28 | renderer = mujoco.Renderer(model, height=480, width=640)
   29 | 
   30 | # Custom camera to see the full swing clearly
   31 | custom_cam = mujoco.MjvCamera()
   32 | custom_cam.type = mujoco.mjtCamera.mjCAMERA_FREE
   33 | custom_cam.lookat[:] = [0, 0, 1.0] # Look at home plate
   34 | custom_cam.distance = 3.5
   35 | custom_cam.azimuth = 135 # Front-side view
   36 | custom_cam.elevation = -10
   37 | 
   38 | # The first 7 qpos are the arm joints, assuming no other free joints before them.
   39 | # Let's find the exact qpos addresses for the 7 joints.
   40 | joint_names = ["shoulder_yaw", "shoulder_pitch", "shoulder_roll", "elbow_flex", "wrist_yaw", "wrist_pitch", "wrist_roll"]
   41 | qpos_adrs = []
   42 | for jname in joint_names:
   43 |     jnt_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, jname)
   44 |     qpos_adrs.append(model.jnt_qposadr[jnt_id])
   45 | 
   46 | for idx, kf in enumerate(keyframes):
   47 |     # Set joint angles
   48 |     for adr, angle in zip(qpos_adrs, kf):
   49 |         data.qpos[adr] = angle
   50 |         
   51 |     mujoco.mj_forward(model, data)
   52 |     
   53 |     # Render
   54 |     renderer.update_scene(data, camera=custom_cam)
   55 |     img = renderer.render()
   56 |     img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
   57 |     
   58 |     filename = os.path.join(out_dir, f"swing_frame_{idx+1}.png")
   59 |     cv2.imwrite(filename, img_bgr)
   60 |     print(f"Saved {filename}")
````
