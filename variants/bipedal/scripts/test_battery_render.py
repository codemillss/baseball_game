import mujoco
import numpy as np
import cv2

model = mujoco.MjModel.from_xml_path("models/h1_battery_pitch_catch.xml")
data = mujoco.MjData(model)

# Catcher joints
c_joint_names = [
    "c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle",
    "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle",
    "c_torso",
    "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow",
    "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"
]
c_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in c_joint_names]

# Deep catcher squat posture:
# knees bent, hips back, low center of mass at z=0.52m
q_squat = [
    0.00,  0.18, -1.15, 1.88, -0.75,  # Left leg
    0.00, -0.18, -1.15, 1.88, -0.75,  # Right leg
    0.00,                             # Torso
    0.35,  0.25,  0.00, 0.85,         # Left arm (mitt presenting target at z~0.82m)
   -0.60, -0.20,  0.00, 1.50          # Right arm (protected behind back)
]
for i, adr in enumerate(c_adrs):
    data.qpos[adr] = q_squat[i]

# Pitcher keyframes (pose 0)
p_joint_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
p_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in p_joint_names]
p_pose0 = [0.20, -0.20, -0.40, 0.30, 1.00]
for i, adr in enumerate(p_adrs):
    data.qpos[adr] = p_pose0[i]

# Ball in pitcher hand
hand_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "p_hand_site")
mujoco.mj_forward(model, data)
hand_pos = data.site_xpos[hand_site_id].copy()
ball_qpos_adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
data.qpos[ball_qpos_adr:ball_qpos_adr+3] = hand_pos

mujoco.mj_forward(model, data)

# Mitt pos
mitt_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "c_mitt_site")
mitt_pos = data.site_xpos[mitt_site_id].copy()
print("Catcher mitt position in world:", mitt_pos)
print("Pitcher hand position in world:", hand_pos)

renderer = mujoco.Renderer(model, height=480, width=640)

# Render cameras:
for cam_name in ["battery_broadcast_cam", "umpire_cam", "catcher_closeup"]:
    cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, cam_name)
    renderer.update_scene(data, camera=cam_id)
    img = renderer.render()
    cv2.imwrite(f"logs/test_{cam_name}.png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print(f"Saved logs/test_{cam_name}.png")

