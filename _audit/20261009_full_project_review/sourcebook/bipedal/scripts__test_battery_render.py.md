# bipedal/scripts/test_battery_render.py

원본: [scripts/test_battery_render.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/test_battery_render.py)

SHA256: `bd0df27eff8d2f38169d5b419d8f956beb1823f9c483f7a10867ef6ec9287c7e`

전체 61행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | import numpy as np
    3 | import cv2
    4 | 
    5 | model = mujoco.MjModel.from_xml_path("models/h1_battery_pitch_catch.xml")
    6 | data = mujoco.MjData(model)
    7 | 
    8 | # Catcher joints
    9 | c_joint_names = [
   10 |     "c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle",
   11 |     "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle",
   12 |     "c_torso",
   13 |     "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow",
   14 |     "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"
   15 | ]
   16 | c_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in c_joint_names]
   17 | 
   18 | # Deep catcher squat posture:
   19 | # knees bent, hips back, low center of mass at z=0.52m
   20 | q_squat = [
   21 |     0.00,  0.18, -1.15, 1.88, -0.75,  # Left leg
   22 |     0.00, -0.18, -1.15, 1.88, -0.75,  # Right leg
   23 |     0.00,                             # Torso
   24 |     0.35,  0.25,  0.00, 0.85,         # Left arm (mitt presenting target at z~0.82m)
   25 |    -0.60, -0.20,  0.00, 1.50          # Right arm (protected behind back)
   26 | ]
   27 | for i, adr in enumerate(c_adrs):
   28 |     data.qpos[adr] = q_squat[i]
   29 | 
   30 | # Pitcher keyframes (pose 0)
   31 | p_joint_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
   32 | p_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in p_joint_names]
   33 | p_pose0 = [0.20, -0.20, -0.40, 0.30, 1.00]
   34 | for i, adr in enumerate(p_adrs):
   35 |     data.qpos[adr] = p_pose0[i]
   36 | 
   37 | # Ball in pitcher hand
   38 | hand_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "p_hand_site")
   39 | mujoco.mj_forward(model, data)
   40 | hand_pos = data.site_xpos[hand_site_id].copy()
   41 | ball_qpos_adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   42 | data.qpos[ball_qpos_adr:ball_qpos_adr+3] = hand_pos
   43 | 
   44 | mujoco.mj_forward(model, data)
   45 | 
   46 | # Mitt pos
   47 | mitt_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "c_mitt_site")
   48 | mitt_pos = data.site_xpos[mitt_site_id].copy()
   49 | print("Catcher mitt position in world:", mitt_pos)
   50 | print("Pitcher hand position in world:", hand_pos)
   51 | 
   52 | renderer = mujoco.Renderer(model, height=480, width=640)
   53 | 
   54 | # Render cameras:
   55 | for cam_name in ["battery_broadcast_cam", "umpire_cam", "catcher_closeup"]:
   56 |     cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, cam_name)
   57 |     renderer.update_scene(data, camera=cam_id)
   58 |     img = renderer.render()
   59 |     cv2.imwrite(f"logs/test_{cam_name}.png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
   60 |     print(f"Saved logs/test_{cam_name}.png")
   61 | 
````
