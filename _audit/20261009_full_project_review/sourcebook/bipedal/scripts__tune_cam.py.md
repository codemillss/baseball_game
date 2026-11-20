# bipedal/scripts/tune_cam.py

원본: [scripts/tune_cam.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/tune_cam.py)

SHA256: `7fb33c79f40a465af488ff805363596ac46ca39144b66b0a3c8092ef3077eb9b`

전체 65행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | import numpy as np
    3 | import cv2
    4 | 
    5 | # Modify camera in XML
    6 | with open("models/h1_battery_pitch_catch.xml", "r") as f:
    7 |     xml = f.read()
    8 | 
    9 | # Replace battery_broadcast_cam with properly targeted camera
   10 | new_cam = '<camera name="battery_broadcast_cam" pos="-6.5 4.5 3.0" xyaxes="0.99 0.15 0 -0.05 0.32 0.95" fovy="62" />'
   11 | # Wait, let's calculate exact lookat matrix:
   12 | pos = np.array([-6.5, 4.5, 3.2])
   13 | target = np.array([0.0, 4.5, 0.8])
   14 | fwd = target - pos
   15 | fwd /= np.linalg.norm(fwd)
   16 | up = np.array([0, 0, 1])
   17 | right = np.cross(fwd, up)
   18 | right /= np.linalg.norm(right)
   19 | real_up = np.cross(right, fwd)
   20 | real_up /= np.linalg.norm(real_up)
   21 | 
   22 | xyaxes_str = f"{right[0]:.4f} {right[1]:.4f} {right[2]:.4f} {real_up[0]:.4f} {real_up[1]:.4f} {real_up[2]:.4f}"
   23 | print("Computed xyaxes:", xyaxes_str)
   24 | 
   25 | # Update xml
   26 | import re
   27 | xml = re.sub(r'<camera name="battery_broadcast_cam"[^>]*>', f'<camera name="battery_broadcast_cam" pos="-6.5 4.5 3.2" xyaxes="{xyaxes_str}" fovy="64" />', xml)
   28 | 
   29 | with open("models/h1_battery_pitch_catch.xml", "w") as f:
   30 |     f.write(xml)
   31 | 
   32 | # Test render
   33 | m = mujoco.MjModel.from_xml_path("models/h1_battery_pitch_catch.xml")
   34 | d = mujoco.MjData(m)
   35 | 
   36 | # Catcher squat
   37 | c_joint_names = [
   38 |     "c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle",
   39 |     "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle",
   40 |     "c_torso",
   41 |     "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow",
   42 |     "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"
   43 | ]
   44 | c_adrs = [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in c_joint_names]
   45 | q_squat_legs = [0.00, 0.18, -1.15, 1.88, -0.75, 0.00, -0.18, -1.15, 1.88, -0.75, 0.00]
   46 | best_arm = [-0.5, -0.3, -0.3, 0.2]
   47 | q_right = [-0.60, -0.20, 0.0, 1.50]
   48 | for i, adr in enumerate(c_adrs):
   49 |     d.qpos[adr] = (q_squat_legs + best_arm + q_right)[i]
   50 | 
   51 | # Pitcher pose
   52 | p_joint_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
   53 | p_adrs = [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in p_joint_names]
   54 | p_pose0 = [0.20, -0.20, -0.40, 0.30, 1.00]
   55 | for i, adr in enumerate(p_adrs):
   56 |     d.qpos[adr] = p_pose0[i]
   57 | 
   58 | mujoco.mj_forward(m, d)
   59 | renderer = mujoco.Renderer(m, height=480, width=640)
   60 | cam_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_CAMERA, "battery_broadcast_cam")
   61 | renderer.update_scene(d, camera=cam_id)
   62 | img = renderer.render()
   63 | cv2.imwrite("logs/test_battery_broadcast_cam.png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
   64 | print("Rendered battery_broadcast_cam successfully.")
   65 | 
````
