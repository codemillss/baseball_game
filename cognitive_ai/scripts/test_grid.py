import os
import sys
import numpy as np
import mujoco

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.teeball_env import TeeBallEnv

def test_grid():
    env = TeeBallEnv()
    test_zs = np.linspace(0.65, 0.95, 13) # 13 heights from 0.65m to 0.95m
    test_actions = np.linspace(-1.0, 1.0, 21) # 21 actions from -1.0 to 1.0
    
    print("Testing grid of ball heights and actions...")
    
    success_map = {}
    
    for z in test_zs:
        success_map[round(z, 3)] = []
        for a in test_actions:
            env.reset()
            # Override ball z
            env.data.qpos[env.ball_qpos_adr+2] = z
            mujoco.mj_forward(env.model, env.data)
            
            action = np.array([a], dtype=np.float32)
            done = False
            hit = False
            while not done:
                obs, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                if reward > 50:
                    hit = True
                    break
            if hit:
                success_map[round(z, 3)].append(round(a, 2))
                
    print("\n--- Grid Reachability Results ---")
    reachable_count = 0
    for z, actions in success_map.items():
        if len(actions) > 0:
            reachable_count += 1
            print(f"Ball Z={z:.3f}m : Reachable with actions {actions[:3]}... (Total {len(actions)} valid actions)")
        else:
            print(f"Ball Z={z:.3f}m : ❌ UNREACHABLE with any action")
            
    print(f"\nOverall Reachability: {reachable_count}/{len(test_zs)} ({(reachable_count/len(test_zs))*100:.1f}%)")

if __name__ == "__main__":
    test_grid()
