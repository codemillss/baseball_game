import mujoco
import numpy as np

model = mujoco.MjModel.from_xml_path("shared_assets/h1_baseball.xml")
data = mujoco.MjData(model)

ball_qpos_adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
ball_qvel_adr = model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]

# Soft toss from 4m
for vz in [1.0, 1.4, 1.8]:
    mujoco.mj_resetData(model, data)
    data.qpos[ball_qpos_adr:ball_qpos_adr+3] = [0.0, 4.0, 1.1]
    data.qvel[ball_qvel_adr:ball_qvel_adr+3] = [0.0, -8.0, vz]
    mujoco.mj_forward(model, data)
    
    print(f"\n--- Testing Vz = {vz} ---")
    for step in range(60): # 60 * 0.005 = 0.30s
        mujoco.mj_step(model, data)
        pos = data.qpos[ball_qpos_adr:ball_qpos_adr+3]
        if abs(pos[1] - 0.4) < 0.1: # Home plate reach
            print(f"Ball reached plate at step {step} (t={step*0.005:.3f}s): Y={pos[1]:.2f}m, Z={pos[2]:.2f}m")
            break
