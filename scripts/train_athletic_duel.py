import os
import sys
sys.path.append(os.path.abspath("."))

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from envs.athletic_duel_env import AthleticDuelEnv

def train():
    os.makedirs("checkpoints", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    env = AthleticDuelEnv()
    eval_env = AthleticDuelEnv()

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path="checkpoints/best_athletic_duel",
        log_path="logs/athletic_duel_eval",
        eval_freq=2500,
        n_eval_episodes=20,
        deterministic=True,
        render=False
    )

    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=1024,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.005,
        verbose=1,
        tensorboard_log="logs/athletic_duel_tb/"
    )

    total_timesteps = 25000
    print(f"Starting Athletic Duel PPO training for {total_timesteps} steps...")
    model.learn(total_timesteps=total_timesteps, callback=eval_callback)

    model.save("checkpoints/final_athletic_duel_model.zip")
    print("Training finished. Final model saved to checkpoints/final_athletic_duel_model.zip")

    best_path = "checkpoints/best_athletic_duel/best_model.zip"
    if os.path.exists(best_path):
        import shutil
        shutil.copy(best_path, "checkpoints/best_athletic_duel_model.zip")
        print("Best model copied to checkpoints/best_athletic_duel_model.zip")
    else:
        import shutil
        shutil.copy("checkpoints/final_athletic_duel_model.zip", "checkpoints/best_athletic_duel_model.zip")

if __name__ == "__main__":
    train()
