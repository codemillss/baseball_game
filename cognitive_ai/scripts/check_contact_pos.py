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

# Keyframe 3 (Contact)
contact_kf = np.array([1.5, 0.5 - 0.8, 0.0, -0.5, 0.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8])

mujoco.mj_resetData(model, data)
for i, adr in enumerate(qpos_adrs):
    data.qpos[adr] = contact_kf[i]
mujoco.mj_forward(model, data)

bat_pos = data.geom_xpos[bat_geom_id]
print(f"Bat Barrel Center Position at Contact: X={bat_pos[0]:.3f}, Y={bat_pos[1]:.3f}, Z={bat_pos[2]:.3f}")
