import os
import sys
import numpy as np
import mujoco

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.teeball_env import TeeBallEnv

def test_scaling():
    env = TeeBallEnv()
    test_zs = np.linspace(0.65, 0.95, 13)
    
    # We want action in [-1, 1] to map to a wider, centered pitch_adj range
    # Let's test pitch_adj = -0.3 + action * 0.7 (maps -1..1 to -1.0..+0.4)
    
    reachable = 0
    mapping = {}
    for z in test_zs:
        valid_actions = []
        for a in np.linspace(-1.0, 1.0, 41):
            env.reset()
            env.data.qpos[env.ball_qpos_adr+2] = z
            mujoco.mj_forward(env.model, env.data)
            
            # Custom pitch_adj mapping
            pitch_adj = -0.3 + a * 0.75
            env.current_keyframes = env.base_keyframes.copy()
            env.current_keyframes[3, 1] += pitch_adj
            env.current_keyframes[4, 1] += pitch_adj
            
            done = False
            hit = False
            while not done:
                obs, reward, terminated, truncated, _ = env.step(np.array([a], dtype=np.float32))
                done = terminated or truncated
                if reward > 50:
                    hit = True
                    break
            if hit:
                valid_actions.append(round(a, 2))
        mapping[round(z, 3)] = valid_actions
        if len(valid_actions) > 0:
            reachable += 1
            print(f"Z={z:.3f}m -> Reachable! ({len(valid_actions)} actions)")
        else:
            print(f"Z={z:.3f}m -> ❌ Miss")
            
    print(f"\nNew Reachability: {reachable}/{len(test_zs)} ({(reachable/len(test_zs))*100:.1f}%)")

if __name__ == "__main__":
    test_scaling()
