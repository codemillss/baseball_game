# bipedal/scripts/tune_catcher_arm.py

원본: [scripts/tune_catcher_arm.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/tune_catcher_arm.py)

SHA256: `68d151428265afbcae488d3959c842dc2513c8054dab879eb560f1580f49b13b`

전체 69행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | import numpy as np
    3 | import cv2
    4 | 
    5 | model = mujoco.MjModel.from_xml_path("models/h1_battery_pitch_catch.xml")
    6 | data = mujoco.MjData(model)
    7 | 
    8 | c_joint_names = [
    9 |     "c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle",
   10 |     "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle",
   11 |     "c_torso",
   12 |     "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow",
   13 |     "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"
   14 | ]
   15 | c_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in c_joint_names]
   16 | 
   17 | # Squat legs
   18 | q_squat_legs = [
   19 |     0.00,  0.18, -1.15, 1.88, -0.75,
   20 |     0.00, -0.18, -1.15, 1.88, -0.75,
   21 |     0.00
   22 | ]
   23 | 
   24 | # Pitcher pose
   25 | p_joint_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
   26 | p_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in p_joint_names]
   27 | p_pose0 = [0.20, -0.20, -0.40, 0.30, 1.00]
   28 | for i, adr in enumerate(p_adrs):
   29 |     data.qpos[adr] = p_pose0[i]
   30 | 
   31 | # Let's grid search or optimize left arm angles so mitt_site is close to [0.0, -0.65, 0.82]
   32 | target_mitt = np.array([0.0, -0.65, 0.82])
   33 | best_err = 999.0
   34 | best_arm = None
   35 | 
   36 | # pitch, roll, yaw, elbow
   37 | for p in np.linspace(-0.5, 0.8, 14):
   38 |     for r in np.linspace(-0.3, 0.8, 12):
   39 |         for y in np.linspace(-0.5, 0.8, 14):
   40 |             for e in np.linspace(0.2, 1.8, 17):
   41 |                 q_arm = [p, r, y, e]
   42 |                 q_right = [-0.60, -0.20, 0.0, 1.50]
   43 |                 full_q = q_squat_legs + q_arm + q_right
   44 |                 for i, adr in enumerate(c_adrs):
   45 |                     data.qpos[adr] = full_q[i]
   46 |                 mujoco.mj_forward(model, data)
   47 |                 mitt_pos = data.site_xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "c_mitt_site")]
   48 |                 err = np.linalg.norm(mitt_pos - target_mitt)
   49 |                 if err < best_err:
   50 |                     best_err = err
   51 |                     best_arm = q_arm
   52 | 
   53 | print(f"Best arm angles: {best_arm}, error: {best_err:.4f} m")
   54 | 
   55 | # Apply best arm and render
   56 | full_q = q_squat_legs + best_arm + [-0.60, -0.20, 0.0, 1.50]
   57 | for i, adr in enumerate(c_adrs):
   58 |     data.qpos[adr] = full_q[i]
   59 | mujoco.mj_forward(model, data)
   60 | mitt_pos = data.site_xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "c_mitt_site")]
   61 | print(f"Final mitt position: {mitt_pos}")
   62 | 
   63 | renderer = mujoco.Renderer(model, height=480, width=640)
   64 | cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, "umpire_cam")
   65 | renderer.update_scene(data, camera=cam_id)
   66 | img = renderer.render()
   67 | cv2.imwrite("logs/test_umpire_mitt_centered.png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
   68 | print("Saved logs/test_umpire_mitt_centered.png")
   69 | 
````
