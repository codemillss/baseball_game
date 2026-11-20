"""
Training Pipeline for Goal-Conditioned Humanoid Pitcher Precision.
Uses Stable-Baselines3 PPO with real-time strike rate tracking,
corner-command evaluation, and multi-pitch performance logging.
"""

import os
import sys
import argparse
import numpy as np
import torch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

from envs.pitcher_precision_env import PitcherPrecisionEnv


class PitcherMetricsCallback(BaseCallback):
    """
    Custom callback to log strike rate, targeting error (MAE in cm),
    and per-pitch-type performance during PPO training.
    """
    def __init__(self, eval_env, eval_freq=2000, n_eval_episodes=30, log_dir="logs", verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.log_dir = log_dir
        self.best_strike_rate = -1.0
        self.best_error_cm = 999.0
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "pitcher_training_progress.csv")
        with open(self.log_file, "w") as f:
            f.write("timesteps,strike_rate,mean_error_cm,fastball_strike,slider_strike,curve_strike,mean_speed_kmh\n")

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq != 0:
            return True

        strikes = 0
        reached = 0
        errors_cm = []
        speeds_kmh = []

        type_strikes = {0: 0, 1: 0, 2: 0}
        type_totals = {0: 0, 1: 0, 2: 0}

        for ep in range(self.n_eval_episodes):
            obs, _ = self.eval_env.reset(seed=5000 + ep)
            done = False
            last_info = {}

            ptype = self.eval_env.pitch_type
            type_totals[ptype] += 1

            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = self.eval_env.step(action)
                done = terminated or truncated
                last_info = info

            if last_info.get("reached_plate", False):
                reached += 1
                dist_cm = last_info.get("dist_error_cm", 99.0)
                errors_cm.append(dist_cm)
                speeds_kmh.append(last_info.get("release_speed_kmh", 0.0))

                if last_info.get("is_strike", False):
                    strikes += 1
                    type_strikes[ptype] += 1

        strike_rate = (strikes / self.n_eval_episodes) * 100.0
        mean_err = np.mean(errors_cm) if errors_cm else 99.0
        mean_spd = np.mean(speeds_kmh) if speeds_kmh else 0.0

        fb_rate = (type_strikes[0] / max(1, type_totals[0])) * 100.0
        sl_rate = (type_strikes[1] / max(1, type_totals[1])) * 100.0
        cb_rate = (type_strikes[2] / max(1, type_totals[2])) * 100.0

        if self.verbose > 0:
            print(f"\n--- [Pitcher Eval @ Step {self.n_calls}] ---")
            print(f"  Strike Rate       : {strike_rate:.1f}% ({strikes}/{self.n_eval_episodes})")
            print(f"  Target Error MAE  : {mean_err:.2f} cm")
            print(f"  Fastball Strike   : {fb_rate:.1f}% ({type_strikes[0]}/{type_totals[0]})")
            print(f"  Slider Strike     : {sl_rate:.1f}% ({type_strikes[1]}/{type_totals[1]})")
            print(f"  Curveball Strike  : {cb_rate:.1f}% ({type_strikes[2]}/{type_totals[2]})")
            print(f"  Mean Pitch Speed  : {mean_spd:.1f} km/h")

        with open(self.log_file, "a") as f:
            f.write(f"{self.n_calls},{strike_rate:.2f},{mean_err:.2f},{fb_rate:.2f},{sl_rate:.2f},{cb_rate:.2f},{mean_spd:.2f}\n")

        # Save Best Checkpoint (Prioritize Strike Rate, tie-break with low target error)
        score = strike_rate - 0.5 * mean_err
        if strike_rate >= self.best_strike_rate and mean_err < self.best_error_cm:
            self.best_strike_rate = strike_rate
            self.best_error_cm = mean_err
            ckpt_path = os.path.join("checkpoints", "best_pitcher_model.zip")
            os.makedirs("checkpoints", exist_ok=True)
            self.model.save(ckpt_path)
            if self.verbose > 0:
                print(f"  >>> New Best Pitcher Model Saved to {ckpt_path}! (Strike: {strike_rate:.1f}%, MAE: {mean_err:.2f}cm)")

        return True


def train_pitcher(total_timesteps=40000, seed=42, n_envs=4):
    print("=" * 60)
    print("Initiating Goal-Conditioned Pitcher Precision PPO Training")
    print(f"Total Timesteps: {total_timesteps}, Parallel Envs: {n_envs}, Seed: {seed}")
    print("=" * 60)

    torch.manual_seed(seed)
    np.random.seed(seed)

    def make_env(env_seed):
        def _init():
            env = PitcherPrecisionEnv()
            env = Monitor(env)
            env.reset(seed=env_seed)
            return env
        return _init

    vec_env = DummyVecEnv([make_env(seed + i * 100) for i in range(n_envs)])
    eval_env = PitcherPrecisionEnv()

    os.makedirs("checkpoints", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    callback = PitcherMetricsCallback(
        eval_env=eval_env,
        eval_freq=1000,
        n_eval_episodes=30,
        log_dir="logs",
        verbose=1,
    )

    policy_kwargs = dict(
        net_arch=[128, 128],
        activation_fn=torch.nn.Tanh,
    )

    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=3e-4,
        n_steps=512,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        policy_kwargs=policy_kwargs,
        verbose=0,
        seed=seed,
    )

    print("\nStarting PPO optimization loop...")
    model.learn(total_timesteps=total_timesteps, callback=callback)

    final_path = os.path.join("checkpoints", "final_pitcher_model.zip")
    model.save(final_path)
    print(f"\nTraining Complete! Final model saved to {final_path}")

    # If best_pitcher_model doesn't exist, copy final
    best_path = os.path.join("checkpoints", "best_pitcher_model.zip")
    if not os.path.exists(best_path):
        model.save(best_path)

    vec_env.close()
    eval_env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=30000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--envs", type=int, default=4)
    args = parser.parse_args()

    train_pitcher(total_timesteps=args.timesteps, seed=args.seed, n_envs=args.envs)
