import mujoco
import numpy as np

model = mujoco.MjModel.from_xml_path("shared_assets/h1_baseball.xml")
data = mujoco.MjData(model)

bat_geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
joint_names = [
    "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
    "left_hip_roll", "left_hip_pitch", "left_knee", "right_hip_roll", "right_hip_pitch", "right_knee"
]
qpos_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in joint_names]

base_keyframes = np.array([
    [-0.5, -1.0, 0.0, 0.5, 1.5,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stance
    [-1.0, -1.2, 0.0, 0.8, 2.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Load
    [0.0, -0.5, 0.0, 0.0, 1.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stride
    [1.5, 0.5, 0.0, -0.5, 0.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Contact
    [2.0, 1.0, 0.0, -1.0, 1.5,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8]  # Follow-through
])

print("Sweeping bat trajectory:")
for p in np.linspace(0, 1, 11):
    num_kfs = len(base_keyframes)
    scaled = p * (num_kfs - 1)
    idx1 = int(np.floor(scaled))
    idx2 = min(idx1 + 1, num_kfs - 1)
    t = scaled - idx1
    angles = (1-t)*base_keyframes[idx1] + t*base_keyframes[idx2]
    
    mujoco.mj_resetData(model, data)
    for i, adr in enumerate(qpos_adrs):
        data.qpos[adr] = angles[i]
    mujoco.mj_forward(model, data)
    
    pos = data.geom_xpos[bat_geom_id]
    print(f"Progress {p:.1f}: Bat pos = X={pos[0]:.2f}, Y={pos[1]:.2f}, Z={pos[2]:.2f}")
