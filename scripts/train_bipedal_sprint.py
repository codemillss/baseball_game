"""
Training Pipeline for Phase 6: Continuous Multi-Step Bipedal Base Running to 1st Base.
Trains and fine-tunes the 19-DoF Unitree H1 Humanoid with full 6-DoF floating base pelvis
to execute:
- Stage 1: Whole-body bipedal athletic swing and contact against live incoming pitches.
- Stage 2: Dynamic prop handover of dropped_bat to field turf at release (t = 0.52s).
- Stage 3: Continuous multi-step bipedal sprint locomotion toward 1st Base (6.5m, 6.5m).
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

from envs.bipedal_sprint_env import BipedalSprintEnv


class BipedalSprintCallback(BaseCallback):
    """Tracks balance survival rate, contact rate, fair hit rate, bat release, and sprint distance."""
    def __init__(self, eval_env, eval_freq=2000, n_eval_episodes=20, log_dir="logs", verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.log_dir = log_dir
        self.best_score = -999.0
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "phase6_bipedal_sprint_progress.csv")
        with open(self.log_file, "w") as f:
            f.write("timesteps,balance_rate,contact_rate,fair_hit_rate,release_rate,mean_distance,mean_exit_vel,mean_sweet_err,mean_pelvis_z\n")

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq != 0:
            return True

        balanced = 0
        contacts = 0
        fair_hits = 0
        releases = 0
        dists = []
        exit_speeds = []
        sweet_offsets = []
        pelvis_zs = []

        for ep in range(self.n_eval_episodes):
            obs, _ = self.eval_env.reset(seed=30000 + ep)
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
                exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
                sweet_offsets.append(last_info.get("sweet_spot_offset", 0.0) * 100.0)
            if last_info.get("fair_hit", False):
                fair_hits += 1
            if last_info.get("bat_released", False):
                releases += 1
            dists.append(last_info.get("dist_traveled", 0.0))
            pelvis_zs.append(last_info.get("pelvis_z", 0.0))

        balance_rate = (balanced / self.n_eval_episodes) * 100.0
        contact_rate = (contacts / self.n_eval_episodes) * 100.0
        fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
        release_rate = (releases / self.n_eval_episodes) * 100.0
        mean_dist = float(np.mean(dists)) if dists else 0.0
        mean_spd = float(np.mean(exit_speeds)) if exit_speeds else 0.0
        mean_sweet_err = float(np.mean(sweet_offsets)) if sweet_offsets else 15.0
        mean_z = float(np.mean(pelvis_zs)) if pelvis_zs else 0.0

        if self.verbose > 0:
            print(f"\n--- [Phase 6 Bipedal Sprint Eval @ Step {self.n_calls}] ---")
            print(f"  Balance Survival Rate : {balance_rate:.1f}% ({balanced}/{self.n_eval_episodes}) [Target >= 95%]")
            print(f"  Contact Success Rate  : {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
            print(f"  Forward Fair-Hit Rate : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
            print(f"  Bat Release Success   : {release_rate:.1f}% ({releases}/{self.n_eval_episodes})")
            print(f"  Mean Sprint Distance  : {mean_dist:+.2f} m (Max: {np.max(dists):+.2f} m)")
            print(f"  Sweet Spot Contact MAE: {mean_sweet_err:.2f} cm")
            print(f"  Mean Exit Velocity    : {mean_spd:.1f} km/h")
            print(f"  Mean Pelvis Elevation : {mean_z:.3f} m")

        with open(self.log_file, "a") as f:
            f.write(f"{self.n_calls},{balance_rate:.2f},{contact_rate:.2f},{fair_rate:.2f},{release_rate:.2f},{mean_dist:.2f},{mean_spd:.2f},{mean_sweet_err:.2f},{mean_z:.3f}\n")

        # Multi-objective composite score prioritizing zero falls, contact, fair hits, and forward sprint distance
        score = (balance_rate * 2.0) + (contact_rate * 1.5) + (fair_rate * 2.0) + (mean_dist * 30.0) - (mean_sweet_err * 2.0)
        if score > self.best_score and balance_rate >= 90.0:
            self.best_score = score
            save_path = os.path.join("checkpoints", "best_phase6_bipedal_sprint_model.zip")
            self.model.save(save_path)
            if self.verbose > 0:
                print(f"  >>> New Best Model Saved! Score: {score:.2f} -> {save_path}")

        return True


def train(total_timesteps=40000, seed=42):
    print("=" * 70)
    print("Initializing Phase 6: Continuous Multi-Step Bipedal Base Running to 1st Base")
    print(f"Total Timesteps: {total_timesteps} | Seed: {seed}")
    print("=" * 70)

    os.makedirs("checkpoints", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    def make_env(s):
        def _thunk():
            env = BipedalSprintEnv()
            env.reset(seed=s)
            return Monitor(env)
        return _thunk

    train_env = DummyVecEnv([make_env(seed)])
    eval_env = BipedalSprintEnv()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using compute device: {device}")

    # Check for warm-start checkpoint from Phase 5 duel
    warmstart_path = os.path.join("checkpoints", "best_phase5_bipedal_duel_model.zip")
    if os.path.exists(warmstart_path):
        print(f"Warm-starting from Phase 5 Duel Checkpoint: {warmstart_path}")
        try:
            model = PPO.load(
                warmstart_path,
                env=train_env,
                device=device,
                learning_rate=3e-4,
                n_steps=1024,
                batch_size=64,
                ent_coef=0.005,
                tensorboard_log="logs/tb_phase6",
            )
        except Exception as e:
            print(f"Warm-start loading encountered shape mismatch ({e}), initializing fresh policy.")
            model = PPO(
                "MlpPolicy",
                train_env,
                device=device,
                learning_rate=3e-4,
                n_steps=1024,
                batch_size=64,
                n_epochs=10,
                gamma=0.99,
                gae_lambda=0.95,
                clip_range=0.2,
                ent_coef=0.005,
                policy_kwargs=dict(net_arch=dict(pi=[128, 128], vf=[128, 128])),
                verbose=1,
                tensorboard_log="logs/tb_phase6",
                seed=seed,
            )
    else:
        model = PPO(
            "MlpPolicy",
            train_env,
            device=device,
            learning_rate=3e-4,
            n_steps=1024,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.005,
            policy_kwargs=dict(net_arch=dict(pi=[128, 128], vf=[128, 128])),
            verbose=1,
            tensorboard_log="logs/tb_phase6",
            seed=seed,
        )

    callback = BipedalSprintCallback(eval_env, eval_freq=2048, n_eval_episodes=20, log_dir="logs", verbose=1)
    model.learn(total_timesteps=total_timesteps, callback=callback)

    final_path = os.path.join("checkpoints", "final_phase6_bipedal_sprint_model.zip")
    model.save(final_path)
    print(f"Phase 6 Training Complete. Final model saved to {final_path}")

    # Ensure best model exists
    best_path = os.path.join("checkpoints", "best_phase6_bipedal_sprint_model.zip")
    if not os.path.exists(best_path):
        model.save(best_path)
        print(f"Saved best model checkpoint to {best_path}")

    train_env.close()
    eval_env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=40000, help="Total training timesteps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    train(total_timesteps=args.timesteps, seed=args.seed)
