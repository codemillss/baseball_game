import os
import sys
import numpy as np
import mujoco

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.soft_toss_env import SoftTossEnv

def test_trigger_y():
    env = SoftTossEnv()
    
    print("Testing trigger_y values for Soft-Toss...")
    
    for trig_y in np.linspace(1.5, 3.0, 16):
        hits = 0
        for _ in range(5):
            env.reset()
            # Ball travels at ~8m/s
            for step in range(45):
                ball_y = env.data.qpos[env.ball_qpos_adr+1]
                ball_z = env.data.qpos[env.ball_qpos_adr+2]
                
                # If ball has reached trigger_y, swing!
                trigger = 1.0 if ball_y <= trig_y else -1.0
                
                # Z action using our Phase 1-A formula: (ball_z - 0.80) / 0.15
                target_z = (ball_z - 0.80) / 0.15
                action = np.array([trigger, target_z], dtype=np.float32)
                
                obs, reward, term, trunc, _ = env.step(action)
                if reward > 50:
                    hits += 1
                    break
                if term or trunc:
                    break
        print(f"Trigger Y = {trig_y:.2f}m -> Hit Rate: {hits}/5 ({(hits/5)*100:.0f}%)")

if __name__ == "__main__":
    test_trigger_y()
