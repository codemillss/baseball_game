import mujoco
import numpy as np
import cv2

model = mujoco.MjModel.from_xml_path("models/h1_battery_pitch_catch.xml")
data = mujoco.MjData(model)

c_joint_names = [
    "c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle",
    "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle",
    "c_torso",
    "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow",
    "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"
]
c_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in c_joint_names]

# Squat legs
q_squat_legs = [
    0.00,  0.18, -1.15, 1.88, -0.75,
    0.00, -0.18, -1.15, 1.88, -0.75,
    0.00
]

# Pitcher pose
p_joint_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
p_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in p_joint_names]
p_pose0 = [0.20, -0.20, -0.40, 0.30, 1.00]
for i, adr in enumerate(p_adrs):
    data.qpos[adr] = p_pose0[i]

# Let's grid search or optimize left arm angles so mitt_site is close to [0.0, -0.65, 0.82]
target_mitt = np.array([0.0, -0.65, 0.82])
best_err = 999.0
best_arm = None

# pitch, roll, yaw, elbow
for p in np.linspace(-0.5, 0.8, 14):
    for r in np.linspace(-0.3, 0.8, 12):
        for y in np.linspace(-0.5, 0.8, 14):
            for e in np.linspace(0.2, 1.8, 17):
                q_arm = [p, r, y, e]
                q_right = [-0.60, -0.20, 0.0, 1.50]
                full_q = q_squat_legs + q_arm + q_right
                for i, adr in enumerate(c_adrs):
                    data.qpos[adr] = full_q[i]
                mujoco.mj_forward(model, data)
                mitt_pos = data.site_xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "c_mitt_site")]
                err = np.linalg.norm(mitt_pos - target_mitt)
                if err < best_err:
                    best_err = err
                    best_arm = q_arm

print(f"Best arm angles: {best_arm}, error: {best_err:.4f} m")

# Apply best arm and render
full_q = q_squat_legs + best_arm + [-0.60, -0.20, 0.0, 1.50]
for i, adr in enumerate(c_adrs):
    data.qpos[adr] = full_q[i]
mujoco.mj_forward(model, data)
mitt_pos = data.site_xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "c_mitt_site")]
print(f"Final mitt position: {mitt_pos}")

renderer = mujoco.Renderer(model, height=480, width=640)
cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, "umpire_cam")
renderer.update_scene(data, camera=cam_id)
img = renderer.render()
cv2.imwrite("logs/test_umpire_mitt_centered.png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
print("Saved logs/test_umpire_mitt_centered.png")

