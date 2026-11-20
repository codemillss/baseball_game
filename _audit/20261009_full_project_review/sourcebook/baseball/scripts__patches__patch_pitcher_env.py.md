# baseball/scripts/patches/patch_pitcher_env.py

원본: [scripts/patches/patch_pitcher_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/patch_pitcher_env.py)

SHA256: `a50d6d3e120bd8d1a3f8ca51fc8cb4a18b1e9f4e9999821ead13e1b82071fbcd`

전체 24행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import re
    2 | 
    3 | with open("cognitive_ai/envs/pitcher_env.py", "r") as f:
    4 |     content = f.read()
    5 | 
    6 | patch_p = """
    7 |         self.valid_indices = []
    8 |         self.qpos_adrs = []
    9 |         for i, n in enumerate(self.joint_names):
   10 |             jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
   11 |             if jid != -1:
   12 |                 self.valid_indices.append(i)
   13 |                 self.qpos_adrs.append(self.model.jnt_qposadr[jid])
   14 | """
   15 | content = re.sub(r'self\.qpos_adrs = \[.*?\]', patch_p, content, count=1, flags=re.DOTALL)
   16 | 
   17 | old_kin = """        for i, adr in enumerate(self.qpos_adrs):
   18 |             self.data.qpos[adr] = angles[i]"""
   19 | new_kin = """        for valid_i, adr in zip(self.valid_indices, self.qpos_adrs):
   20 |             self.data.qpos[adr] = angles[valid_i]"""
   21 | content = content.replace(old_kin, new_kin)
   22 | 
   23 | with open("cognitive_ai/envs/pitcher_env.py", "w") as f:
   24 |     f.write(content)
````
