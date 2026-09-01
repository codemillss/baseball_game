import re

with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    content = f.read()

# Add _apply_aerodynamics helper
helper_code = """
    def _apply_aerodynamics(self):
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        speed = np.linalg.norm(ball_vel)
        if speed < 1.0: return
        
        c_d = 0.005 
        F_drag = -c_d * speed * ball_vel
        
        F_magnus = np.zeros(3)
        if hasattr(self, 'target_pitch_type'):
            c_l = 0.005 * speed
            if self.target_pitch_type == 0:
                F_magnus = np.array([0.0, 0.0, c_l])
            elif self.target_pitch_type == 1:
                F_magnus = np.array([-c_l, 0.0, -c_l*0.5])
            elif self.target_pitch_type == 2:
                F_magnus = np.array([0.0, 0.0, -c_l*1.5])
                
        self.data.xfrc_applied[self.ball_body_id][:3] = F_drag + F_magnus

    def step(self, pitcher_action, batter_action):
"""

content = content.replace("    def step(self, pitcher_action, batter_action):", helper_code)

# Insert the call to _apply_aerodynamics inside step() right before mj_step
step_code = """        # Apply physics
        if not self.has_hit:
            self._apply_aerodynamics()
            
        mujoco.mj_step(self.model, self.data)
"""
content = content.replace("        mujoco.mj_step(self.model, self.data)", step_code)

# Enhance hit physics: if contact just happened this frame, add exit velocity multiplier
hit_code = """            if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \\
               (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
                if not self.has_hit:
                    # Apply trampoline effect (COR) to exit velocity
                    self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] *= 1.35
                self.has_hit = True"""
                
old_hit = """            if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \\
               (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
                self.has_hit = True"""
                
content = content.replace(old_hit, hit_code)

with open("cognitive_ai/envs/baseball_match_env.py", "w") as f:
    f.write(content)
