"""
Training Pipeline for Phase 7: Full Infield Bipedal Defense & 1st Base Out/Safe Play.
Trains the 8-DoF multi-robot coordination policy for:
- Pitcher throwing dynamic pitches (Fastball, Slider, Curveball)
- Batter-Runner kinetic swing, dynamic prop drop handover, and 1st base sprint
- 1st Baseman Infielder fielding intercept footwork, glove scoop, and base covering
- 3D Umpire Decision Engine measuring T_runner vs T_defense -> OUT vs SAFE
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

from envs.infield_defense_env import InfieldDefenseEnv


class InfieldDefenseCallback(BaseCallback):
    """Tracks batter and fielder balance survival, contact rate, fair hit rate, fielding rate, and sprint speed."""
    def __init__(self, eval_env, eval_freq=2048, n_eval_episodes=20, log_dir="logs", verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.log_dir = log_dir
        self.best_score = -999.0
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "phase7_infield_defense_progress.csv")
        with open(self.log_file, "w") as f:
            f.write("timesteps,batter_survival,fielder_survival,contact_rate,fair_hit_rate,fielded_rate,out_rate,safe_rate,mean_exit_vel,mean_runner_spd\n")

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq != 0:
            return True

        b_survived = 0
        f_survived = 0
        contacts = 0
        fair_hits = 0
        fielded = 0
        outs = 0
        safes = 0
        exit_speeds = []
        runner_speeds = []

        for ep in range(self.n_eval_episodes):
            obs, _ = self.eval_env.reset(seed=50000 + ep)
            done = False
            last_info = {}

            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = self.eval_env.step(action)
                done = terminated or truncated
                last_info = info

            if not last_info.get("batter_fallen", False):
                b_survived += 1
            if not last_info.get("fielder_fallen", False):
                f_survived += 1
            if last_info.get("contact", False):
                contacts += 1
                exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
            if last_info.get("fair_hit", False):
                fair_hits += 1
            if last_info.get("ball_fielded", False):
                fielded += 1
            if last_info.get("umpire_decision") == "OUT":
                outs += 1
            elif last_info.get("umpire_decision") == "SAFE":
                safes += 1
            runner_speeds.append(last_info.get("runner_speed_kmh", 0.0))

        b_rate = (b_survived / self.n_eval_episodes) * 100.0
        f_rate = (f_survived / self.n_eval_episodes) * 100.0
        c_rate = (contacts / self.n_eval_episodes) * 100.0
        fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
        field_rate = (fielded / self.n_eval_episodes) * 100.0
        out_rate = (outs / self.n_eval_episodes) * 100.0
        safe_rate = (safes / self.n_eval_episodes) * 100.0
        mean_exit = float(np.mean(exit_speeds)) if exit_speeds else 0.0
        mean_runner = float(np.mean(runner_speeds)) if runner_speeds else 0.0

        if self.verbose > 0:
            print(f"\n--- [Phase 7 Infield Defense Eval @ Step {self.n_calls}] ---")
            print(f"  Batter Survival Rate  : {b_rate:.1f}% ({b_survived}/{self.n_eval_episodes}) [Target 100%]")
            print(f"  Fielder Survival Rate : {f_rate:.1f}% ({f_survived}/{self.n_eval_episodes}) [Target 100%]")
            print(f"  Contact Rate          : {c_rate:.1f}% ({contacts}/{self.n_eval_episodes}) [Target >= 80%]")
            print(f"  Fair Hit Rate         : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes}) [Target >= 60%]")
            print(f"  Fielder Intercept Rate: {field_rate:.1f}% ({fielded}/{self.n_eval_episodes}) [Target ~50-60%]")
            print(f"  Play Calls (OUT/SAFE) : OUT {out_rate:.1f}% | SAFE {safe_rate:.1f}%")
            print(f"  Mean Exit Velocity    : {mean_exit:.1f} km/h")
            print(f"  Mean Runner Sprint Spd: {mean_runner:.1f} km/h")

        with open(self.log_file, "a") as f:
            f.write(f"{self.n_calls},{b_rate:.2f},{f_rate:.2f},{c_rate:.2f},{fair_rate:.2f},{field_rate:.2f},{out_rate:.2f},{safe_rate:.2f},{mean_exit:.2f},{mean_runner:.2f}\n")

        # Multi-objective composite score
        score = (b_rate * 2.0) + (f_rate * 2.0) + (c_rate * 1.5) + (fair_rate * 1.5) + (field_rate * 1.0)
        if score > self.best_score and b_rate >= 95.0 and f_rate >= 95.0:
            self.best_score = score
            save_path = os.path.join("checkpoints", "best_phase7_infield_defense_model.zip")
            self.model.save(save_path)
            if self.verbose > 0:
                print(f"  >>> New Best Model Saved! Score: {score:.2f} -> {save_path}")

        return True


def train(total_timesteps=40000, seed=42):
    print("=" * 70)
    print("Initializing Phase 7: Full Infield Bipedal Defense & 1st Base Out/Safe Play")
    print(f"Total Timesteps: {total_timesteps} | Seed: {seed}")
    print("=" * 70)

    os.makedirs("checkpoints", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    def make_env(s):
        def _thunk():
            env = InfieldDefenseEnv()
            env.reset(seed=s)
            return Monitor(env)
        return _thunk

    train_env = DummyVecEnv([make_env(seed)])
    eval_env = InfieldDefenseEnv()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using compute device: {device}")

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
        tensorboard_log="logs/tb_phase7",
        seed=seed,
    )

    callback = InfieldDefenseCallback(eval_env, eval_freq=2048, n_eval_episodes=20, log_dir="logs", verbose=1)
    model.learn(total_timesteps=total_timesteps, callback=callback)

    final_path = os.path.join("checkpoints", "final_phase7_infield_defense_model.zip")
    model.save(final_path)
    print(f"Phase 7 Training Complete. Final model saved to {final_path}")

    # Ensure best model exists
    best_path = os.path.join("checkpoints", "best_phase7_infield_defense_model.zip")
    if not os.path.exists(best_path):
        model.save(best_path)
        print(f"Saved initial model to {best_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Phase 7 Infield Defense Policy")
    parser.add_argument("--timesteps", type=int, default=30000, help="Total training timesteps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    train(total_timesteps=args.timesteps, seed=args.seed)
