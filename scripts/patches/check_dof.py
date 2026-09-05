import mujoco
model = mujoco.MjModel.from_xml_path("shared_assets/h1_baseball_match.xml")
for i in range(model.nv):
    print(f"DOF {i}: {mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, model.dof_jntid[i])}")
