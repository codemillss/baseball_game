import os
import sys
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.soft_toss_env import SoftTossEnv

def train_soft_toss():
    print("🚀 Starting Phase 1-B: Soft-Toss Batting RL Training (25~30 km/h)...")
    
    os.makedirs("./checkpoints/soft_toss_best_model", exist_ok=True)
    os.makedirs("./runs/soft_toss_eval", exist_ok=True)
    
    env = SoftTossEnv()
    env = Monitor(env)
    
    eval_callback = EvalCallback(
        env,
        best_model_save_path='./checkpoints/soft_toss_best_model',
        log_path='./runs/soft_toss_eval',
        eval_freq=2000,
        n_eval_episodes=20,
        deterministic=True
    )
    
    # 2-layer MLP policy for 6-dim input -> 2-dim action
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=1e-3,
        n_steps=1024,
        batch_size=64,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        tensorboard_log="./runs/soft_toss_tensorboard/"
    )
    
    print("🧠 Training starting for 60,000 steps...")
    model.learn(total_timesteps=60000, callback=eval_callback)
    
    model.save("./checkpoints/soft_toss_final_model")
    print("✅ Soft-Toss Training Complete! Model saved to ./checkpoints/soft_toss_final_model")
    env.close()

if __name__ == "__main__":
    train_soft_toss()
