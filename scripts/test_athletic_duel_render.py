import os
import mujoco
import cv2
import numpy as np

model = mujoco.MjModel.from_xml_path("models/h1_athletic_duel.xml")
data = mujoco.MjData(model)

renderer = mujoco.Renderer(model, height=480, width=640)

# Set Pitcher
p_pose = [0.20, -0.20, -0.40, 0.30, 1.00]
p_names = ['p_torso', 'p_right_shoulder_pitch', 'p_right_shoulder_roll', 'p_right_shoulder_yaw', 'p_right_elbow']
for i, name in enumerate(p_names):
    adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)]
    data.qpos[adr] = p_pose[i]

# Set Catcher deep squat
c_pelvis_adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "c_pelvis_joint")]
data.qpos[c_pelvis_adr:c_pelvis_adr+3] = [0.0, -0.95, 0.54]
data.qpos[c_pelvis_adr+3:c_pelvis_adr+7] = [0.7071068, 0, 0, 0.7071068]
c_legs = [0.0, 0.0, -1.15, 1.88, -0.75, 0.0, 0.0, -1.15, 1.88, -0.75]
c_leg_names = ["c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle", "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle"]
for i, name in enumerate(c_leg_names):
    adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)]
    data.qpos[adr] = c_legs[i]
c_upper = [0.0, -0.50, -0.30, -0.30, 0.20, -0.60, -0.20, 0.0, 1.50]
c_upper_names = ["c_torso", "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow", "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"]
for i, name in enumerate(c_upper_names):
    adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)]
    data.qpos[adr] = c_upper[i]

# Set Batter deep-knee athletic stance
b_pelvis_adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "b_pelvis_joint")]
# Pelvis lowered from 1.00m to 0.86m, facing +X (toward plate/pitcher)
data.qpos[b_pelvis_adr:b_pelvis_adr+3] = [-0.75, 0.00, 0.86]
data.qpos[b_pelvis_adr+3:b_pelvis_adr+7] = [1.0, 0.0, 0.0, 0.0]

# Knee bent ~42 deg (0.72 rad), hip flexed -0.48 rad, ankle dorsiflexed -0.24 rad
b_legs = [0.0, 0.12, -0.48, 0.72, -0.24, 0.0, -0.12, -0.48, 0.72, -0.24]
b_leg_names = ["b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle", "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle"]
for i, name in enumerate(b_leg_names):
    adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)]
    data.qpos[adr] = b_legs[i]

# Torso slightly coiled (-0.35 rad), bat cocked up by right shoulder
b_upper_names = ["b_torso", "b_left_shoulder_pitch", "b_left_shoulder_roll", "b_left_shoulder_yaw", "b_left_elbow", "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"]
b_upper = [-0.35, -0.65, 0.45, 0.85, 1.25, -0.85, -0.55, -0.75, 1.45]
for i, name in enumerate(b_upper_names):
    adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)]
    data.qpos[adr] = b_upper[i]

# Ball in pitcher hand
hp_now = data.site_xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")]
ball_adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
data.qpos[ball_adr:ball_adr+3] = hp_now

mujoco.mj_forward(model, data)

for cam_name in ["duel_broadcast_cam", "umpire_cam", "batter_side_cam"]:
    cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, cam_name)
    renderer.update_scene(data, camera=cam_id)
    img = renderer.render()
    out_file = f"logs/videos/preview_{cam_name}.png"
    cv2.imwrite(out_file, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print(f"Rendered {out_file}")

renderer.close()
