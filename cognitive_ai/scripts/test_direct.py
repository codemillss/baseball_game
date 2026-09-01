import os
import sys
import numpy as np
import mujoco

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.teeball_env import TeeBallEnv

def test_kinematics_direct():
    env = TeeBallEnv()
    test_zs = np.linspace(0.65, 0.95, 13)
    
    print("Directly testing keyframe kinematics for ball heights:")
    
    reachable = 0
    for z in test_zs:
        valid_adj = []
        for adj in np.linspace(-1.5, 1.0, 51):
            env.reset()
            env.data.qpos[env.ball_qpos_adr+2] = z
            mujoco.mj_forward(env.model, env.data)
            
            # Set keyframe
            kfs = env.base_keyframes.copy()
            kfs[3, 1] += adj # Contact shoulder pitch
            kfs[4, 1] += adj # Follow-through shoulder pitch
            
            # Run swing
            hit = False
            for p in np.linspace(0, 1, 30):
                # Update kinematics
                num_kfs = len(kfs)
                scaled = p * (num_kfs - 1)
                idx1 = int(np.floor(scaled))
                idx2 = min(idx1 + 1, num_kfs - 1)
                t = scaled - idx1
                current_angles = (1-t)*kfs[idx1] + t*kfs[idx2]
                
                for i, adr in enumerate(env.qpos_adrs):
                    env.data.qpos[adr] = current_angles[i]
                mujoco.mj_forward(env.model, env.data)
                
                if env._check_contact():
                    hit = True
                    break
            if hit:
                valid_adj.append(round(adj, 2))
        if len(valid_adj) > 0:
            reachable += 1
            print(f"Z={z:.3f}m -> ✅ Reachable! (Pitch adj range: {valid_adj[0]} to {valid_adj[-1]})")
        else:
            print(f"Z={z:.3f}m -> ❌ Miss")
            
    print(f"\nDirect Reachability: {reachable}/{len(test_zs)} ({(reachable/len(test_zs))*100:.1f}%)")

if __name__ == "__main__":
    test_kinematics_direct()
