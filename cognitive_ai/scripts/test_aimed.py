import os
import sys
import numpy as np
import mujoco

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.soft_toss_env import SoftTossEnv

def test_aimed_toss():
    env = SoftTossEnv()
    
    # Ball aims at X=-0.15 at plate (Y=0.55)
    # Start at Y=4.0, X=0.0 -> delta_y = -3.45, delta_x = -0.15
    # vx = vy * (delta_x / delta_y) = -8.0 * (-0.15 / -3.45) = -0.347 m/s
    
    for trig_y in np.linspace(1.2, 2.0, 17):
        hits = 0
        min_dists = []
        for vz in [1.5, 1.7, 1.9]:
            env.reset()
            env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3] = [0.0, 4.0, 1.0]
            env.data.qvel[env.ball_qvel_adr:env.ball_qvel_adr+3] = [-0.35, -8.0, vz]
            
            for step in range(45):
                ball_y = env.data.qpos[env.ball_qpos_adr+1]
                ball_z = env.data.qpos[env.ball_qpos_adr+2]
                
                trigger = 1.0 if ball_y <= trig_y else -1.0
                target_z = (ball_z - 0.80) / 0.15
                action = np.array([trigger, target_z], dtype=np.float32)
                
                obs, reward, term, trunc, _ = env.step(action)
                if reward > 50:
                    hits += 1
                    break
                if term or trunc:
                    min_dists.append(env.min_dist)
                    break
        avg_d = np.mean(min_dists) if min_dists else 0.0
        print(f"Trigger Y = {trig_y:.2f}m -> Hit: {hits}/3, Min Dist: {avg_d:.3f}m")

if __name__ == "__main__":
    test_aimed_toss()
