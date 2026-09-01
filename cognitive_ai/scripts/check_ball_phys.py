import mujoco
import numpy as np

model = mujoco.MjModel.from_xml_path("shared_assets/h1_baseball.xml")
data = mujoco.MjData(model)

ball_qpos_adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
ball_qvel_adr = model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]

mujoco.mj_resetData(model, data)
data.qpos[ball_qpos_adr:ball_qpos_adr+3] = [0.0, 4.0, 1.0]
data.qvel[ball_qvel_adr:ball_qvel_adr+3] = [0.0, -8.0, 1.6]
mujoco.mj_forward(model, data)

for step in range(120):
    mujoco.mj_step(model, data)
    pos = data.qpos[ball_qpos_adr:ball_qpos_adr+3]
    vel = data.qvel[ball_qvel_adr:ball_qvel_adr+3]
    if step % 10 == 0:
        print(f"Frame {step:3d} (t={step*0.005:.3f}s): Y={pos[1]:.2f}m, Z={pos[2]:.2f}m, Vy={vel[1]:.2f}m/s, Vz={vel[2]:.2f}m/s")
