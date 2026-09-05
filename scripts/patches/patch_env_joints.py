import re

with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    content = f.read()

# Fix p_qpos_adrs filtering
# Replace:
# self.p_qpos_adrs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.p_joint_names]
# with list comprehension that filters out -1
patch_p = """
        self.p_valid_indices = []
        self.p_qpos_adrs = []
        for i, n in enumerate(self.p_joint_names):
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
            if jid != -1:
                self.p_valid_indices.append(i)
                self.p_qpos_adrs.append(self.model.jnt_qposadr[jid])
"""
content = re.sub(r'self\.p_qpos_adrs = \[.*?\]', patch_p, content, count=1, flags=re.DOTALL)

# Fix b_qpos_adrs filtering
patch_b = """
        self.b_valid_indices = []
        self.b_qpos_adrs = []
        for i, n in enumerate(self.b_joint_names):
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
            if jid != -1:
                self.b_valid_indices.append(i)
                self.b_qpos_adrs.append(self.model.jnt_qposadr[jid])
"""
content = re.sub(r'self\.b_qpos_adrs = \[.*?\]', patch_b, content, count=1, flags=re.DOTALL)

# Update kinematics logic to use valid_indices
# For Pitcher
old_p_kin = """        for i, adr in enumerate(self.p_qpos_adrs):
            self.data.qpos[adr] = angles[i]"""
new_p_kin = """        for valid_i, adr in zip(self.p_valid_indices, self.p_qpos_adrs):
            self.data.qpos[adr] = angles[valid_i]"""
content = content.replace(old_p_kin, new_p_kin)

# For Batter
old_b_kin = """        for i, adr in enumerate(self.b_qpos_adrs):
            self.data.qpos[adr] = angles[i]"""
new_b_kin = """        for valid_i, adr in zip(self.b_valid_indices, self.b_qpos_adrs):
            self.data.qpos[adr] = angles[valid_i]"""
content = content.replace(old_b_kin, new_b_kin)

with open("cognitive_ai/envs/baseball_match_env.py", "w") as f:
    f.write(content)
