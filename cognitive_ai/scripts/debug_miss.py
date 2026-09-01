import os
import sys
import numpy as np
import mujoco

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.soft_toss_env import SoftTossEnv

def debug_miss():
    env = SoftTossEnv()
    env.reset()
    
    # Soft toss at vy = -8.0 m/s
    trig_y = 1.50
    for step in range(45):
        ball_pos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3].copy()
        trigger = 1.0 if ball_pos[1] <= trig_y else -1.0
        
        obs, reward, term, trunc, _ = env.step(np.array([trigger, 0.0], dtype=np.float32))
        
        if env.swing_active:
            bat_pos = env.data.geom_xpos[env.bat_geom_id]
            diff = bat_pos - ball_pos
            print(f"Step {step:2d} (Swing {env.swing_progress:.2f}): Bat=({bat_pos[0]:.2f}, {bat_pos[1]:.2f}, {bat_pos[2]:.2f}), Ball=({ball_pos[0]:.2f}, {ball_pos[1]:.2f}, {ball_pos[2]:.2f}), Diff=({diff[0]:.2f}, {diff[1]:.2f}, {diff[2]:.2f}), Dist={np.linalg.norm(diff):.3f}m")
            
        if reward > 50:
            print("💥 HIT!")
            break
        if term or trunc:
            break

if __name__ == "__main__":
    debug_miss()
