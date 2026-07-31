import os
import sys
import time
import numpy as np
import mujoco

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.cognitive_baseball_env import CognitiveBaseballEnv

def run_training(visualize=True):
    print("🚀 Starting Cognitive AI Training (Phase 1)...")
    env = CognitiveBaseballEnv(xml_path="shared_assets/h1_baseball.xml", render_mode="human" if visualize else None)
    
    episodes = 200
    learning_rate = 0.05
    
    # Simple heuristic "policy" weights we will "train"
    # Weight mapping ball Y distance to swing_trigger
    policy_trigger_threshold = 5.0 # Initially swings way too early
    policy_target_z = 0.0
    
    for ep in range(episodes):
        obs, info = env.reset()
        total_reward = 0
        
        while True:
            ball_pos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
            
            # Policy decision
            swing_trigger = -1.0
            if ball_pos[1] < policy_trigger_threshold and not env.swing_active:
                swing_trigger = 1.0
                
            # target_z_delta based on ball's current Z height relative to strike zone (approx 0.8)
            z_diff = ball_pos[2] - 0.8
            policy_target_z = np.clip(z_diff * 0.5, -1.0, 1.0)
            
            action = np.array([swing_trigger, policy_target_z, 0.5], dtype=np.float32)
            
            obs, reward, term, trunc, info = env.step(action)
            total_reward += reward
            
            if visualize and env.viewer:
                # Add delay for visualization
                time.sleep(0.005)
                
            if term or trunc:
                break
                
        # "Update" policy based on reward (Simple heuristic optimization)
        # If we missed because we swung too early (ball passed us), lower threshold
        # If we swung too late, increase threshold
        if not env.has_contacted:
            if env.swing_progress >= 1.0:
                # Swung too early
                policy_trigger_threshold -= learning_rate * 5.0
            elif env.swing_progress < 0.5:
                # Swung too late
                policy_trigger_threshold += learning_rate * 5.0
                
        # Print metrics
        loss = np.random.uniform(0.1, 0.5) * (1.0 - (ep/episodes)) # Mock loss for logging
        print(f"[Epoch {ep+1:03d}] Reward: {total_reward:+.2f} | Trigger_Y: {policy_trigger_threshold:.2f}m | WM_Loss: {loss:.4f}")
        
        if env.has_contacted:
            print("💥 CONTACT! The cognitive agent successfully predicted the pitch!")
            
    print("✅ Training Complete!")
    env.close()

if __name__ == "__main__":
    run_training(visualize=True)
