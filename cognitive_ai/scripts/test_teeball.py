import os
import sys
import time
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.teeball_env import TeeBallEnv

def test_heuristic_swing():
    print("🚀 Starting Tee-ball Heuristic Test...")
    env = TeeBallEnv(xml_path="shared_assets/h1_baseball.xml", render_mode="human")
    
    for ep in range(3):
        obs = env.reset()
        ball_z = obs[0][2] if isinstance(obs, tuple) else obs[2]
        print(f"Episode {ep+1}: Ball height is {ball_z:.2f}m")
        
        # Calculate heuristic target_z_delta based on ball height
        # Base contact height is ~0.8m
        z_delta = (ball_z - 0.8) * 1.5 
        z_delta = np.clip(z_delta, -1.0, 1.0)
        
        for step in range(60):
            # Trigger swing at step 10
            trigger = 1.0 if step == 10 else -1.0
            action = np.array([trigger, z_delta], dtype=np.float32)
            
            obs_out, reward, terminated, truncated, _ = env.step(action)
            
            if reward > 0:
                print(f"💥 Hit the ball at step {step}! Reward: {reward}")
            
            time.sleep(0.02)
            
            if terminated or truncated:
                print("Episode ended.")
                break
                
        time.sleep(1)
        
    env.close()

if __name__ == "__main__":
    test_heuristic_swing()
