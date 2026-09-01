import re

with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    content = f.read()

# Replace p_qvel_adrs init
patch1 = """
        self.p_valid_indices = []
        self.p_qpos_adrs = []
        self.p_qvel_adrs = []
        for i, n in enumerate(self.p_joint_names):
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
            if jid != -1:
                self.p_valid_indices.append(i)
                self.p_qpos_adrs.append(self.model.jnt_qposadr[jid])
                self.p_qvel_adrs.append(self.model.jnt_dofadr[jid])
"""
content = re.sub(r'self\.p_valid_indices = \[\].*?self\.p_qvel_adrs = \[.*?\]', patch1, content, flags=re.DOTALL)

# Replace b_qvel_adrs init
patch2 = """
        self.b_valid_indices = []
        self.b_qpos_adrs = []
        self.b_qvel_adrs = []
        for i, n in enumerate(self.b_joint_names):
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
            if jid != -1:
                self.b_valid_indices.append(i)
                self.b_qpos_adrs.append(self.model.jnt_qposadr[jid])
                self.b_qvel_adrs.append(self.model.jnt_dofadr[jid])
"""
content = re.sub(r'self\.b_valid_indices = \[\].*?self\.b_qpos_adrs\.append\(self\.model\.jnt_qposadr\[jid\]\)', patch2, content, flags=re.DOTALL)

# Update pitcher kinematics
old_p_kin = """        for valid_i, adr in zip(self.p_valid_indices, self.p_qpos_adrs):
            self.data.qpos[adr] = angles[valid_i]"""
new_p_kin = """        for valid_i, qpos_adr, qvel_adr in zip(self.p_valid_indices, self.p_qpos_adrs, self.p_qvel_adrs):
            self.data.qpos[qpos_adr] = angles[valid_i]
            self.data.qvel[qvel_adr] = 0.0"""
content = content.replace(old_p_kin, new_p_kin)

# Update batter kinematics
old_b_kin = """        for valid_i, adr in zip(self.b_valid_indices, self.b_qpos_adrs):
            self.data.qpos[adr] = angles[valid_i]"""
new_b_kin = """        for valid_i, qpos_adr, qvel_adr in zip(self.b_valid_indices, self.b_qpos_adrs, self.b_qvel_adrs):
            self.data.qpos[qpos_adr] = angles[valid_i]
            self.data.qvel[qvel_adr] = 0.0"""
content = content.replace(old_b_kin, new_b_kin)

with open("cognitive_ai/envs/baseball_match_env.py", "w") as f:
    f.write(content)
