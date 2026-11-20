# bipedal/scripts/test_athletic_duel_render.py

원본: [scripts/test_athletic_duel_render.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/test_athletic_duel_render.py)

SHA256: `2bff660265f7bb5e39a9970b919bac6f405cff5dda32f6d4d0d2443a3e5816dd`

전체 68행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import os
    2 | import mujoco
    3 | import cv2
    4 | import numpy as np
    5 | 
    6 | model = mujoco.MjModel.from_xml_path("models/h1_athletic_duel.xml")
    7 | data = mujoco.MjData(model)
    8 | 
    9 | renderer = mujoco.Renderer(model, height=480, width=640)
   10 | 
   11 | # Set Pitcher
   12 | p_pose = [0.20, -0.20, -0.40, 0.30, 1.00]
   13 | p_names = ['p_torso', 'p_right_shoulder_pitch', 'p_right_shoulder_roll', 'p_right_shoulder_yaw', 'p_right_elbow']
   14 | for i, name in enumerate(p_names):
   15 |     adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)]
   16 |     data.qpos[adr] = p_pose[i]
   17 | 
   18 | # Set Catcher deep squat
   19 | c_pelvis_adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "c_pelvis_joint")]
   20 | data.qpos[c_pelvis_adr:c_pelvis_adr+3] = [0.0, -0.95, 0.54]
   21 | data.qpos[c_pelvis_adr+3:c_pelvis_adr+7] = [0.7071068, 0, 0, 0.7071068]
   22 | c_legs = [0.0, 0.0, -1.15, 1.88, -0.75, 0.0, 0.0, -1.15, 1.88, -0.75]
   23 | c_leg_names = ["c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle", "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle"]
   24 | for i, name in enumerate(c_leg_names):
   25 |     adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)]
   26 |     data.qpos[adr] = c_legs[i]
   27 | c_upper = [0.0, -0.50, -0.30, -0.30, 0.20, -0.60, -0.20, 0.0, 1.50]
   28 | c_upper_names = ["c_torso", "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow", "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"]
   29 | for i, name in enumerate(c_upper_names):
   30 |     adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)]
   31 |     data.qpos[adr] = c_upper[i]
   32 | 
   33 | # Set Batter deep-knee athletic stance
   34 | b_pelvis_adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "b_pelvis_joint")]
   35 | # Pelvis lowered from 1.00m to 0.86m, facing +X (toward plate/pitcher)
   36 | data.qpos[b_pelvis_adr:b_pelvis_adr+3] = [-0.75, 0.00, 0.86]
   37 | data.qpos[b_pelvis_adr+3:b_pelvis_adr+7] = [1.0, 0.0, 0.0, 0.0]
   38 | 
   39 | # Knee bent ~42 deg (0.72 rad), hip flexed -0.48 rad, ankle dorsiflexed -0.24 rad
   40 | b_legs = [0.0, 0.12, -0.48, 0.72, -0.24, 0.0, -0.12, -0.48, 0.72, -0.24]
   41 | b_leg_names = ["b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle", "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle"]
   42 | for i, name in enumerate(b_leg_names):
   43 |     adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)]
   44 |     data.qpos[adr] = b_legs[i]
   45 | 
   46 | # Torso slightly coiled (-0.35 rad), bat cocked up by right shoulder
   47 | b_upper_names = ["b_torso", "b_left_shoulder_pitch", "b_left_shoulder_roll", "b_left_shoulder_yaw", "b_left_elbow", "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"]
   48 | b_upper = [-0.35, -0.65, 0.45, 0.85, 1.25, -0.85, -0.55, -0.75, 1.45]
   49 | for i, name in enumerate(b_upper_names):
   50 |     adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)]
   51 |     data.qpos[adr] = b_upper[i]
   52 | 
   53 | # Ball in pitcher hand
   54 | hp_now = data.site_xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")]
   55 | ball_adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   56 | data.qpos[ball_adr:ball_adr+3] = hp_now
   57 | 
   58 | mujoco.mj_forward(model, data)
   59 | 
   60 | for cam_name in ["duel_broadcast_cam", "umpire_cam", "batter_side_cam"]:
   61 |     cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, cam_name)
   62 |     renderer.update_scene(data, camera=cam_id)
   63 |     img = renderer.render()
   64 |     out_file = f"logs/videos/preview_{cam_name}.png"
   65 |     cv2.imwrite(out_file, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
   66 |     print(f"Rendered {out_file}")
   67 | 
   68 | renderer.close()
````
