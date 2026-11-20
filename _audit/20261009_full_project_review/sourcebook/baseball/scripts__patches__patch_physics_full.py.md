# baseball/scripts/patches/patch_physics_full.py

원본: [scripts/patches/patch_physics_full.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/patch_physics_full.py)

SHA256: `36849b3942f830dd49685d707ce52823f7ea51cfda762b66a95e760210d7cbb6`

전체 57행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import re
    2 | 
    3 | with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    4 |     content = f.read()
    5 | 
    6 | # Add _apply_aerodynamics helper
    7 | helper_code = """
    8 |     def _apply_aerodynamics(self):
    9 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
   10 |         speed = np.linalg.norm(ball_vel)
   11 |         if speed < 1.0: return
   12 |         
   13 |         c_d = 0.005 
   14 |         F_drag = -c_d * speed * ball_vel
   15 |         
   16 |         F_magnus = np.zeros(3)
   17 |         if hasattr(self, 'target_pitch_type'):
   18 |             c_l = 0.005 * speed
   19 |             if self.target_pitch_type == 0:
   20 |                 F_magnus = np.array([0.0, 0.0, c_l])
   21 |             elif self.target_pitch_type == 1:
   22 |                 F_magnus = np.array([-c_l, 0.0, -c_l*0.5])
   23 |             elif self.target_pitch_type == 2:
   24 |                 F_magnus = np.array([0.0, 0.0, -c_l*1.5])
   25 |                 
   26 |         self.data.xfrc_applied[self.ball_body_id][:3] = F_drag + F_magnus
   27 | 
   28 |     def step(self, pitcher_action, batter_action):
   29 | """
   30 | 
   31 | content = content.replace("    def step(self, pitcher_action, batter_action):", helper_code)
   32 | 
   33 | # Insert the call to _apply_aerodynamics inside step() right before mj_step
   34 | step_code = """        # Apply physics
   35 |         if not self.has_hit:
   36 |             self._apply_aerodynamics()
   37 |             
   38 |         mujoco.mj_step(self.model, self.data)
   39 | """
   40 | content = content.replace("        mujoco.mj_step(self.model, self.data)", step_code)
   41 | 
   42 | # Enhance hit physics: if contact just happened this frame, add exit velocity multiplier
   43 | hit_code = """            if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \\
   44 |                (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
   45 |                 if not self.has_hit:
   46 |                     # Apply trampoline effect (COR) to exit velocity
   47 |                     self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] *= 1.35
   48 |                 self.has_hit = True"""
   49 |                 
   50 | old_hit = """            if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \\
   51 |                (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
   52 |                 self.has_hit = True"""
   53 |                 
   54 | content = content.replace(old_hit, hit_code)
   55 | 
   56 | with open("cognitive_ai/envs/baseball_match_env.py", "w") as f:
   57 |     f.write(content)
````
