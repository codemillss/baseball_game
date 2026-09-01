import re

with open("cognitive_ai/envs/pitcher_env.py", "r") as f:
    content = f.read()

patch_p = """
        self.valid_indices = []
        self.qpos_adrs = []
        for i, n in enumerate(self.joint_names):
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
            if jid != -1:
                self.valid_indices.append(i)
                self.qpos_adrs.append(self.model.jnt_qposadr[jid])
"""
content = re.sub(r'self\.qpos_adrs = \[.*?\]', patch_p, content, count=1, flags=re.DOTALL)

old_kin = """        for i, adr in enumerate(self.qpos_adrs):
            self.data.qpos[adr] = angles[i]"""
new_kin = """        for valid_i, adr in zip(self.valid_indices, self.qpos_adrs):
            self.data.qpos[adr] = angles[valid_i]"""
content = content.replace(old_kin, new_kin)

with open("cognitive_ai/envs/pitcher_env.py", "w") as f:
    f.write(content)
