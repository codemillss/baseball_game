import os
import sys
import time
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback, StopTrainingOnRewardThreshold
from stable_baselines3.common.monitor import Monitor

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.teeball_env import TeeBallEnv

def train_teeball():
    print("🚀 Starting Phase 1-A: Tee-ball RL Training...")
    
    # 1. Create and wrap the environment
    env = TeeBallEnv(xml_path="shared_assets/h1_baseball.xml", render_mode=None)
    env = Monitor(env) # For tracking rewards and episode lengths
    
    # 2. Set up the PPO agent
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=1024,
        batch_size=64,
        gamma=0.99,
        tensorboard_log="./runs/teeball_tensorboard/"
    )
    
    # 3. Callbacks for evaluation and early stopping
    eval_callback = EvalCallback(
        env,
        best_model_save_path='./checkpoints/teeball_best_model',
        log_path='./runs/teeball_eval',
        eval_freq=2000,
        deterministic=True,
        render=False
    )
    
    # 4. Train the agent
    print("🧠 Training starting... (Use Ctrl+C to stop early)")
    try:
        model.learn(total_timesteps=50000, callback=eval_callback)
    except KeyboardInterrupt:
        print("Training interrupted manually.")
    finally:
        # Save the final model
        model.save("./checkpoints/teeball_final_model")
        print("✅ Model saved to ./checkpoints/teeball_final_model")
        env.close()

if __name__ == "__main__":
    train_teeball()
