import os
import sys
import numpy as np
import mujoco

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.soft_toss_env import SoftTossEnv

def test_timing_precise():
    env = SoftTossEnv()
    
    print("Testing precise trigger distance around Y=0.8m ~ 1.2m...")
    
    for trig_y in np.linspace(0.8, 1.4, 13):
        hits = 0
        min_dists = []
        for _ in range(10):
            env.reset()
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
        avg_min_dist = np.mean(min_dists) if min_dists else 0.0
        print(f"Trigger Y = {trig_y:.2f}m -> Hit Rate: {hits}/10 ({(hits/10)*100:.0f}%), Avg Min Dist: {avg_min_dist:.3f}m")

if __name__ == "__main__":
    test_timing_precise()
