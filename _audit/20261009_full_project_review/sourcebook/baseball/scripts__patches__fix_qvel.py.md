# baseball/scripts/patches/fix_qvel.py

원본: [scripts/patches/fix_qvel.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/fix_qvel.py)

SHA256: `9ec9566687bf1a7d6cf740ad88a3dc16c3f602dfa140a26446613658970ef691`

전체 51행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import re
    2 | 
    3 | with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    4 |     content = f.read()
    5 | 
    6 | # Replace p_qvel_adrs init
    7 | patch1 = """
    8 |         self.p_valid_indices = []
    9 |         self.p_qpos_adrs = []
   10 |         self.p_qvel_adrs = []
   11 |         for i, n in enumerate(self.p_joint_names):
   12 |             jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
   13 |             if jid != -1:
   14 |                 self.p_valid_indices.append(i)
   15 |                 self.p_qpos_adrs.append(self.model.jnt_qposadr[jid])
   16 |                 self.p_qvel_adrs.append(self.model.jnt_dofadr[jid])
   17 | """
   18 | content = re.sub(r'self\.p_valid_indices = \[\].*?self\.p_qvel_adrs = \[.*?\]', patch1, content, flags=re.DOTALL)
   19 | 
   20 | # Replace b_qvel_adrs init
   21 | patch2 = """
   22 |         self.b_valid_indices = []
   23 |         self.b_qpos_adrs = []
   24 |         self.b_qvel_adrs = []
   25 |         for i, n in enumerate(self.b_joint_names):
   26 |             jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
   27 |             if jid != -1:
   28 |                 self.b_valid_indices.append(i)
   29 |                 self.b_qpos_adrs.append(self.model.jnt_qposadr[jid])
   30 |                 self.b_qvel_adrs.append(self.model.jnt_dofadr[jid])
   31 | """
   32 | content = re.sub(r'self\.b_valid_indices = \[\].*?self\.b_qpos_adrs\.append\(self\.model\.jnt_qposadr\[jid\]\)', patch2, content, flags=re.DOTALL)
   33 | 
   34 | # Update pitcher kinematics
   35 | old_p_kin = """        for valid_i, adr in zip(self.p_valid_indices, self.p_qpos_adrs):
   36 |             self.data.qpos[adr] = angles[valid_i]"""
   37 | new_p_kin = """        for valid_i, qpos_adr, qvel_adr in zip(self.p_valid_indices, self.p_qpos_adrs, self.p_qvel_adrs):
   38 |             self.data.qpos[qpos_adr] = angles[valid_i]
   39 |             self.data.qvel[qvel_adr] = 0.0"""
   40 | content = content.replace(old_p_kin, new_p_kin)
   41 | 
   42 | # Update batter kinematics
   43 | old_b_kin = """        for valid_i, adr in zip(self.b_valid_indices, self.b_qpos_adrs):
   44 |             self.data.qpos[adr] = angles[valid_i]"""
   45 | new_b_kin = """        for valid_i, qpos_adr, qvel_adr in zip(self.b_valid_indices, self.b_qpos_adrs, self.b_qvel_adrs):
   46 |             self.data.qpos[qpos_adr] = angles[valid_i]
   47 |             self.data.qvel[qvel_adr] = 0.0"""
   48 | content = content.replace(old_b_kin, new_b_kin)
   49 | 
   50 | with open("cognitive_ai/envs/baseball_match_env.py", "w") as f:
   51 |     f.write(content)
````
