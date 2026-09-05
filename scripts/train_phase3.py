"""
Training Pipeline for Phase 3: Whole-Body Kinetic Chain Bipedal Swing.
Trains H1 Humanoid to maintain 6-DoF floating base balance on two feet
while executing athletic swings at incoming pitches.
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

from envs.bipedal_swing_env import BipedalSwingEnv


class BipedalSwingCallback(BaseCallback):
    """Logs bipedal balance, fall rate, and contact performance."""
    def __init__(self, eval_env, eval_freq=1000, n_eval_episodes=25, log_dir="logs", verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.log_dir = log_dir
        self.best_balance_score = -999.0
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "phase3_bipedal_progress.csv")
        with open(self.log_file, "w") as f:
            f.write("timesteps,balance_rate,contact_rate,fair_hit_rate,mean_pelvis_z\n")

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq != 0:
            return True

        balanced = 0
        contacts = 0
        fair_hits = 0
        pelvis_zs = []

        for ep in range(self.n_eval_episodes):
            obs, _ = self.eval_env.reset(seed=15000 + ep)
            done = False
            last_info = {}

            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = self.eval_env.step(action)
                done = terminated or truncated
                last_info = info

            if not last_info.get("has_fallen", False):
                balanced += 1
            if last_info.get("contact", False):
                contacts += 1
            if last_info.get("fair_hit", False):
                fair_hits += 1
            pelvis_zs.append(last_info.get("pelvis_z", 0.0))

        balance_rate = (balanced / self.n_eval_episodes) * 100.0
        contact_rate = (contacts / self.n_eval_episodes) * 100.0
        fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
        mean_z = np.mean(pelvis_zs) if pelvis_zs else 0.0

        if self.verbose > 0:
            print(f"\n--- [Phase 3 Bipedal Eval @ Step {self.n_calls}] ---")
            print(f"  Balance Rate  : {balance_rate:.1f}% ({balanced}/{self.n_eval_episodes})")
            print(f"  Contact Rate  : {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
            print(f"  Fair-Hit Rate : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
            print(f"  Mean Pelvis Z : {mean_z:.3f} m")

        with open(self.log_file, "a") as f:
            f.write(f"{self.n_calls},{balance_rate:.2f},{contact_rate:.2f},{fair_rate:.2f},{mean_z:.3f}\n")

        score = balance_rate + 0.5 * contact_rate + 0.5 * fair_rate
        if score > self.best_balance_score:
            self.best_balance_score = score
            ckpt_path = os.path.join("checkpoints", "best_phase3_bipedal_model.zip")
            self.model.save(ckpt_path)
            if self.verbose > 0:
                print(f"  >>> New Best Bipedal Model Saved to {ckpt_path}! (Score: {score:.1f})")

        return True


def train_bipedal_swing(total_timesteps=25000, seed=42, n_envs=4):
    print("=" * 60)
    print("Initiating Phase 3 Whole-Body Bipedal Swing PPO Training")
    print(f"Total Timesteps: {total_timesteps}, Parallel Envs: {n_envs}, Seed: {seed}")
    print("=" * 60)

    torch.manual_seed(seed)
    np.random.seed(seed)

    def make_env(env_seed):
        def _init():
            env = BipedalSwingEnv()
            env = Monitor(env)
            env.reset(seed=env_seed)
            return env
        return _init

    vec_env = DummyVecEnv([make_env(seed + i * 100) for i in range(n_envs)])
    eval_env = BipedalSwingEnv()

    callback = BipedalSwingCallback(
        eval_env=eval_env,
        eval_freq=1000,
        n_eval_episodes=25,
        log_dir="logs",
        verbose=1,
    )

    policy_kwargs = dict(net_arch=[128, 128], activation_fn=torch.nn.Tanh)
    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=3e-4,
        n_steps=512,
        batch_size=64,
        n_epochs=10,
        policy_kwargs=policy_kwargs,
        seed=seed,
    )

    print("Starting Bipedal PPO optimization...")
    model.learn(total_timesteps=total_timesteps, callback=callback)

    final_path = os.path.join("checkpoints", "final_phase3_bipedal_model.zip")
    model.save(final_path)
    best_path = os.path.join("checkpoints", "best_phase3_bipedal_model.zip")
    if not os.path.exists(best_path):
        model.save(best_path)

    print(f"Phase 3 Complete! Final model saved to {final_path}")
    vec_env.close()
    eval_env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--envs", type=int, default=4)
    args = parser.parse_args()

    train_bipedal_swing(total_timesteps=args.timesteps, seed=args.seed, n_envs=args.envs)
