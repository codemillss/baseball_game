"""
Phase 2 Training: Sim-to-Real Physically Hardened Batting.
Transfers weights from Phase 1 and hardens the policy against:
- 20ms EtherCAT communication delay (latency buffer)
- Strict low-level motor torque saturation
- Domain randomization (bat mass +/- 10%, restitution variation, vision noise)
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

from envs.hardened_batting_env import HardenedBattingEnv


class HardenedBattingCallback(BaseCallback):
    """Logs contact, fair-hit, and directional accuracy under Sim-to-Real perturbations."""
    def __init__(self, eval_env, eval_freq=1500, n_eval_episodes=25, log_dir="logs", verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.log_dir = log_dir
        self.best_fair_rate = 0.0
        self.best_az_mae = 999.0
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "phase2_hardened_progress.csv")
        with open(self.log_file, "w") as f:
            f.write("timesteps,contact_rate,fair_hit_rate,azimuth_mae,launch_mae,exit_speed_kmh\n")

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq != 0:
            return True

        contacts = 0
        fair_hits = 0
        az_errors = []
        la_errors = []
        exit_speeds = []

        for ep in range(self.n_eval_episodes):
            obs, _ = self.eval_env.reset(seed=8000 + ep)
            done = False
            last_info = {}

            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = self.eval_env.step(action)
                done = terminated or truncated
                last_info = info

            if last_info.get("contact", False):
                contacts += 1
                exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
                if last_info.get("fair_hit", False):
                    fair_hits += 1
                    az_errors.append(last_info.get("azimuth_error_deg", 99.0))
                    la_errors.append(last_info.get("launch_error_deg", 99.0))

        contact_rate = (contacts / self.n_eval_episodes) * 100.0
        fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
        az_mae = np.mean(az_errors) if az_errors else 99.0
        la_mae = np.mean(la_errors) if la_errors else 99.0
        mean_spd = np.mean(exit_speeds) if exit_speeds else 0.0

        if self.verbose > 0:
            print(f"\n--- [Phase 2 Hardened Eval @ Step {self.n_calls}] ---")
            print(f"  Contact Rate  : {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
            print(f"  Fair-Hit Rate : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
            print(f"  Azimuth MAE   : {az_mae:.2f}°")
            print(f"  Launch MAE    : {la_mae:.2f}°")
            print(f"  Exit Velocity : {mean_spd:.1f} km/h")

        with open(self.log_file, "a") as f:
            f.write(f"{self.n_calls},{contact_rate:.2f},{fair_rate:.2f},{az_mae:.2f},{la_mae:.2f},{mean_spd:.2f}\n")

        if fair_rate >= self.best_fair_rate and az_mae <= self.best_az_mae:
            self.best_fair_rate = fair_rate
            self.best_az_mae = az_mae
            ckpt_path = os.path.join("checkpoints", "best_phase2_hardened_model.zip")
            self.model.save(ckpt_path)
            if self.verbose > 0:
                print(f"  >>> New Best Hardened Model Saved: {ckpt_path} (Fair: {fair_rate:.1f}%, Az MAE: {az_mae:.2f}°)")

        return True


def train_hardened_batter(total_timesteps=30000, seed=42, n_envs=4, pretrained="checkpoints/best_phase1_model.zip"):
    print("=" * 60)
    print("Initiating Phase 2 Sim-to-Real Hardened Batting Training")
    print(f"Total Timesteps: {total_timesteps}, Envs: {n_envs}, Pretrained: {pretrained}")
    print("=" * 60)

    torch.manual_seed(seed)
    np.random.seed(seed)

    def make_env(env_seed):
        def _init():
            env = HardenedBattingEnv(latency_steps=1, enable_domain_randomization=True)
            env = Monitor(env)
            env.reset(seed=env_seed)
            return env
        return _init

    vec_env = DummyVecEnv([make_env(seed + i * 100) for i in range(n_envs)])
    eval_env = HardenedBattingEnv(latency_steps=1, enable_domain_randomization=True)

    callback = HardenedBattingCallback(
        eval_env=eval_env,
        eval_freq=1000,
        n_eval_episodes=25,
        log_dir="logs",
        verbose=1,
    )

    if os.path.exists(pretrained):
        print(f"Loading pretrained Phase 1 weights from {pretrained} for Sim-to-Real hardening...")
        model = PPO.load(pretrained, env=vec_env, learning_rate=1.5e-4, seed=seed)
    else:
        print("No pretrained model found. Initializing from scratch...")
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

    print("Starting fine-tuning under Sim-to-Real perturbations...")
    model.learn(total_timesteps=total_timesteps, callback=callback)

    final_path = os.path.join("checkpoints", "final_phase2_hardened_model.zip")
    model.save(final_path)
    best_path = os.path.join("checkpoints", "best_phase2_hardened_model.zip")
    if not os.path.exists(best_path):
        model.save(best_path)

    print(f"Phase 2 Training Complete! Final saved to {final_path}")
    vec_env.close()
    eval_env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=25000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--envs", type=int, default=4)
    parser.add_argument("--pretrained", type=str, default="checkpoints/best_phase1_model.zip")
    args = parser.parse_args()

    train_hardened_batter(total_timesteps=args.timesteps, seed=args.seed, n_envs=args.envs, pretrained=args.pretrained)
