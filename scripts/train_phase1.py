"""
Training Pipeline for Phase 1: Directional Hitting & Precision Contact.
Uses Stable-Baselines3 PPO with customized evaluation callbacks and quantitative metric logging.
"""

import os
import sys
import argparse
import numpy as np
import torch

# Ensure repository root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

import envs


class BattingMetricsCallback(BaseCallback):
    """
    Custom callback to log contact rate, fair hit rate, sweet spot precision,
    and directional spray error during training.
    """
    def __init__(self, eval_env, eval_freq=4000, n_eval_episodes=25, log_dir="logs", verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.log_dir = log_dir
        self.best_score = -999.0
        self.best_contact_rate = 0.0
        self.best_azimuth_mae = 999.0
        os.makedirs(log_dir, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq != 0:
            return True

        contacts = 0
        fair_hits = 0
        sweet_offsets = []
        azimuth_errors = []
        launch_errors = []
        exit_speeds = []

        pull_success, pull_total = 0, 0
        center_success, center_total = 0, 0
        push_success, push_total = 0, 0

        for ep in range(self.n_eval_episodes):
            obs, _ = self.eval_env.reset(seed=2000 + ep)
            done = False
            ep_contact = False
            ep_fair = False
            ep_info = {}

            target_az_deg = np.degrees(obs[7])
            if target_az_deg < -10.0:
                cat = "pull"
                pull_total += 1
            elif target_az_deg > 10.0:
                cat = "push"
                push_total += 1
            else:
                cat = "center"
                center_total += 1

            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = self.eval_env.step(action)
                done = terminated or truncated
                if info.get("contact", False):
                    ep_contact = True
                    ep_info = info
                if info.get("fair_hit", False):
                    ep_fair = True

            if ep_contact:
                contacts += 1
                sweet_offsets.append(ep_info.get("sweet_spot_offset_cm", 99.0))
                exit_speeds.append(ep_info.get("exit_speed_ms", 0.0))
                
                if ep_fair:
                    fair_hits += 1
                    az_err = ep_info.get("azimuth_error_deg", 99.0)
                    la_err = ep_info.get("launch_error_deg", 99.0)
                    azimuth_errors.append(az_err)
                    launch_errors.append(la_err)

                    if az_err < 25.0:
                        if cat == "pull":
                            pull_success += 1
                        elif cat == "push":
                            push_success += 1
                        else:
                            center_success += 1

        contact_rate = (contacts / self.n_eval_episodes) * 100.0
        fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
        mean_sweet = float(np.mean(sweet_offsets)) if sweet_offsets else 99.0
        mean_az_err = float(np.mean(azimuth_errors)) if azimuth_errors else 99.0
        mean_la_err = float(np.mean(launch_errors)) if launch_errors else 99.0
        mean_exit_speed = float(np.mean(exit_speeds)) if exit_speeds else 0.0

        pull_acc = (pull_success / max(1, pull_total)) * 100.0
        center_acc = (center_success / max(1, center_total)) * 100.0
        push_acc = (push_success / max(1, push_total)) * 100.0

        if self.verbose > 0:
            print(f"\n========================================================")
            print(f"📊 EVALUATION [Step {self.n_calls} / {self.n_eval_episodes} Episodes]")
            print(f"  • Contact Rate:          {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
            print(f"  • Fair-Ball Hit Rate:    {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
            print(f"  • Sweet Spot Offset:     {mean_sweet:.2f} cm")
            print(f"  • Azimuth Error (MAE):   {mean_az_err:.2f}°")
            print(f"  • Launch Angle Error:    {mean_la_err:.2f}°")
            print(f"  • Mean Exit Velocity:    {mean_exit_speed:.1f} m/s ({mean_exit_speed*3.6:.1f} km/h)")
            print(f"  • Spray Control: Pull={pull_acc:.0f}%, Center={center_acc:.0f}%, Push={push_acc:.0f}%")
            print(f"========================================================\n")

        # Holistic objective: prioritize fair hit rate and lower azimuth error
        composite_score = fair_rate - 0.25 * mean_az_err
        if composite_score >= self.best_score:
            self.best_score = composite_score
            self.best_contact_rate = contact_rate
            self.best_azimuth_mae = mean_az_err
            best_path = os.path.join(self.log_dir, "..", "checkpoints", "best_phase1_model.zip")
            self.model.save(best_path)
            if self.verbose > 0:
                print(f"🏆 New best model saved to {best_path} (Fair: {fair_rate:.1f}%, AzErr: {mean_az_err:.1f}°)")

        return True


def make_env(rank, seed=0):
    def _init():
        env = gym.make("DirectionalBatting-v0")
        env.reset(seed=seed + rank)
        return Monitor(env)
    return _init


def train():
    parser = argparse.ArgumentParser(description="Train Phase 1 Directional Batting Agent")
    parser.add_argument("--timesteps", type=int, default=50000, help="Total training timesteps")
    parser.add_argument("--n-envs", type=int, default=4, help="Number of parallel environments")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--eval-freq", type=int, default=4000, help="Evaluation frequency in timesteps")
    parser.add_argument("--lr", type=float, default=3e-4, help="PPO learning rate")
    args = parser.parse_args()

    # Set seeds
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    checkpoints_dir = os.path.join(BASE_DIR, "checkpoints")
    logs_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(checkpoints_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    print("🚀 Initializing Vectorized Environments...")
    if args.n_envs > 1:
        vec_env = DummyVecEnv([make_env(i, args.seed) for i in range(args.n_envs)])
    else:
        vec_env = DummyVecEnv([make_env(0, args.seed)])

    eval_env = gym.make("DirectionalBatting-v0")

    policy_kwargs = dict(
        net_arch=dict(pi=[128, 128], vf=[128, 128]),
        activation_fn=torch.nn.Tanh,
    )

    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=args.lr,
        n_steps=1024,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs=policy_kwargs,
        tensorboard_log=os.path.join(logs_dir, "tb"),
        verbose=1,
        seed=args.seed,
    )

    metrics_callback = BattingMetricsCallback(
        eval_env=eval_env,
        eval_freq=args.eval_freq,
        n_eval_episodes=25,
        log_dir=logs_dir,
        verbose=1,
    )

    print(f"🔥 Starting PPO Training for {args.timesteps} timesteps on H1 Humanoid...")
    model.learn(
        total_timesteps=args.timesteps,
        callback=metrics_callback,
        progress_bar=False,
    )

    final_model_path = os.path.join(checkpoints_dir, "final_phase1_model.zip")
    model.save(final_model_path)
    print(f"✅ Training completed! Final model saved to: {final_model_path}")

    vec_env.close()
    eval_env.close()


if __name__ == "__main__":
    train()
