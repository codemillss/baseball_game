# baseball/scripts/patches/patch_env_joints.py

원본: [scripts/patches/patch_env_joints.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/patch_env_joints.py)

SHA256: `ee433f7ef402b85360a950b6140600f561f1e8c90dab603d76501ff2a346dd8c`

전체 49행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import re
    2 | 
    3 | with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    4 |     content = f.read()
    5 | 
    6 | # Fix p_qpos_adrs filtering
    7 | # Replace:
    8 | # self.p_qpos_adrs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.p_joint_names]
    9 | # with list comprehension that filters out -1
   10 | patch_p = """
   11 |         self.p_valid_indices = []
   12 |         self.p_qpos_adrs = []
   13 |         for i, n in enumerate(self.p_joint_names):
   14 |             jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
   15 |             if jid != -1:
   16 |                 self.p_valid_indices.append(i)
   17 |                 self.p_qpos_adrs.append(self.model.jnt_qposadr[jid])
   18 | """
   19 | content = re.sub(r'self\.p_qpos_adrs = \[.*?\]', patch_p, content, count=1, flags=re.DOTALL)
   20 | 
   21 | # Fix b_qpos_adrs filtering
   22 | patch_b = """
   23 |         self.b_valid_indices = []
   24 |         self.b_qpos_adrs = []
   25 |         for i, n in enumerate(self.b_joint_names):
   26 |             jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
   27 |             if jid != -1:
   28 |                 self.b_valid_indices.append(i)
   29 |                 self.b_qpos_adrs.append(self.model.jnt_qposadr[jid])
   30 | """
   31 | content = re.sub(r'self\.b_qpos_adrs = \[.*?\]', patch_b, content, count=1, flags=re.DOTALL)
   32 | 
   33 | # Update kinematics logic to use valid_indices
   34 | # For Pitcher
   35 | old_p_kin = """        for i, adr in enumerate(self.p_qpos_adrs):
   36 |             self.data.qpos[adr] = angles[i]"""
   37 | new_p_kin = """        for valid_i, adr in zip(self.p_valid_indices, self.p_qpos_adrs):
   38 |             self.data.qpos[adr] = angles[valid_i]"""
   39 | content = content.replace(old_p_kin, new_p_kin)
   40 | 
   41 | # For Batter
   42 | old_b_kin = """        for i, adr in enumerate(self.b_qpos_adrs):
   43 |             self.data.qpos[adr] = angles[i]"""
   44 | new_b_kin = """        for valid_i, adr in zip(self.b_valid_indices, self.b_qpos_adrs):
   45 |             self.data.qpos[adr] = angles[valid_i]"""
   46 | content = content.replace(old_b_kin, new_b_kin)
   47 | 
   48 | with open("cognitive_ai/envs/baseball_match_env.py", "w") as f:
   49 |     f.write(content)
````
