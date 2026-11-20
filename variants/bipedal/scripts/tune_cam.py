import mujoco
import numpy as np
import cv2

# Modify camera in XML
with open("models/h1_battery_pitch_catch.xml", "r") as f:
    xml = f.read()

# Replace battery_broadcast_cam with properly targeted camera
new_cam = '<camera name="battery_broadcast_cam" pos="-6.5 4.5 3.0" xyaxes="0.99 0.15 0 -0.05 0.32 0.95" fovy="62" />'
# Wait, let's calculate exact lookat matrix:
pos = np.array([-6.5, 4.5, 3.2])
target = np.array([0.0, 4.5, 0.8])
fwd = target - pos
fwd /= np.linalg.norm(fwd)
up = np.array([0, 0, 1])
right = np.cross(fwd, up)
right /= np.linalg.norm(right)
real_up = np.cross(right, fwd)
real_up /= np.linalg.norm(real_up)

xyaxes_str = f"{right[0]:.4f} {right[1]:.4f} {right[2]:.4f} {real_up[0]:.4f} {real_up[1]:.4f} {real_up[2]:.4f}"
print("Computed xyaxes:", xyaxes_str)

# Update xml
import re
xml = re.sub(r'<camera name="battery_broadcast_cam"[^>]*>', f'<camera name="battery_broadcast_cam" pos="-6.5 4.5 3.2" xyaxes="{xyaxes_str}" fovy="64" />', xml)

with open("models/h1_battery_pitch_catch.xml", "w") as f:
    f.write(xml)

# Test render
m = mujoco.MjModel.from_xml_path("models/h1_battery_pitch_catch.xml")
d = mujoco.MjData(m)

# Catcher squat
c_joint_names = [
    "c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle",
    "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle",
    "c_torso",
    "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow",
    "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"
]
c_adrs = [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in c_joint_names]
q_squat_legs = [0.00, 0.18, -1.15, 1.88, -0.75, 0.00, -0.18, -1.15, 1.88, -0.75, 0.00]
best_arm = [-0.5, -0.3, -0.3, 0.2]
q_right = [-0.60, -0.20, 0.0, 1.50]
for i, adr in enumerate(c_adrs):
    d.qpos[adr] = (q_squat_legs + best_arm + q_right)[i]

# Pitcher pose
p_joint_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
p_adrs = [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in p_joint_names]
p_pose0 = [0.20, -0.20, -0.40, 0.30, 1.00]
for i, adr in enumerate(p_adrs):
    d.qpos[adr] = p_pose0[i]

mujoco.mj_forward(m, d)
renderer = mujoco.Renderer(m, height=480, width=640)
cam_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_CAMERA, "battery_broadcast_cam")
renderer.update_scene(d, camera=cam_id)
img = renderer.render()
cv2.imwrite("logs/test_battery_broadcast_cam.png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
print("Rendered battery_broadcast_cam successfully.")

