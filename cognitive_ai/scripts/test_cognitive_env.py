import gymnasium as gym
import numpy as np
import os
import sys

# Add parent dir to path so we can import envs
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.cognitive_baseball_env import CognitiveBaseballEnv

def test():
    print("Testing Cognitive Baseball Env...")
    env = CognitiveBaseballEnv(xml_path="shared_assets/stadium_3d.xml", render_mode="human")
    obs, info = env.reset()
    
    for i in range(50):
        # Action: swing immediately, aim slightly up, swing fast
        action = np.array([1.0, 0.5, 0.8], dtype=np.float32)
        obs, reward, term, trunc, info = env.step(action)
        if term or trunc:
            print(f"Episode ended at step {i} with reward {reward}")
            break
            
    print("Test finished successfully!")
    env.close()

if __name__ == "__main__":
    test()
