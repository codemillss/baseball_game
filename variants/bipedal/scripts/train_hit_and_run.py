"""
Training Pipeline for Phase 4: Hit-and-Run Locomotion Transition.
Trains the 19-DoF H1 Humanoid to:
1. Execute an athletic bipedal swing and make crisp contact on incoming pitches.
2. Unlatch the equality weld to drop the bat cleanly on turf.
3. Transition dynamic bipedal running locomotion toward 1st Base (x=6.5, y=6.5) without falling.
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
from envs.hit_and_run_env import HitAndRunEnv


class HitAndRunCallback(BaseCallback):
    def __init__(self, eval_env, eval_freq=1000, n_eval_episodes=20, log_dir="logs", verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.log_dir = log_dir
        self.best_score = -999.0
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "phase4_hit_and_run_progress.csv")
        with open(self.log_file, "w") as f:
            f.write("timesteps,balance_rate,contact_rate,fair_hit_rate,bat_rel_rate,mean_dist_traveled\n")

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq != 0:
            return True

        balanced = 0
        contacts = 0
        fair_hits = 0
        bat_releases = 0
        dist_traveled_list = []

        for ep in range(self.n_eval_episodes):
            obs, _ = self.eval_env.reset(seed=20000 + ep)
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
            if last_info.get("bat_released", False):
                bat_releases += 1
            dist_traveled_list.append(last_info.get("dist_traveled", 0.0))

        balance_rate = (balanced / self.n_eval_episodes) * 100.0
        contact_rate = (contacts / self.n_eval_episodes) * 100.0
        fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
        bat_rel_rate = (bat_releases / self.n_eval_episodes) * 100.0
        mean_dist = float(np.mean(dist_traveled_list)) if dist_traveled_list else 0.0

        if self.verbose > 0:
            print(f"\n--- [Phase 4 Hit & Run Eval @ Step {self.n_calls}] ---")
            print(f"  Balance Rate     : {balance_rate:.1f}% ({balanced}/{self.n_eval_episodes})")
            print(f"  Contact Rate     : {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
            print(f"  Fair-Hit Rate    : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
            print(f"  Bat Release Rate : {bat_rel_rate:.1f}% ({bat_releases}/{self.n_eval_episodes})")
            print(f"  Mean 1B Sprint   : {mean_dist:.2f} m")

        with open(self.log_file, "a") as f:
            f.write(f"{self.n_calls},{balance_rate:.2f},{contact_rate:.2f},{fair_rate:.2f},{bat_rel_rate:.2f},{mean_dist:.3f}\n")

        score = balance_rate + 0.5 * contact_rate + 0.3 * fair_rate + 10.0 * max(0.0, mean_dist)
        if score > self.best_score:
            self.best_score = score
            ckpt_path = os.path.join("checkpoints", "best_phase4_hit_and_run_model.zip")
            self.model.save(ckpt_path)
            if self.verbose > 0:
                print(f"  >>> New Best Hit & Run Model Saved to {ckpt_path}! (Score: {score:.1f})")

        return True


def train_hit_and_run(total_timesteps=30000, seed=42, n_envs=4):
    print("=" * 60)
    print("Initiating Phase 4 Hit-and-Run Locomotion Transition PPO Training")
    print(f"Total Timesteps: {total_timesteps}, Parallel Envs: {n_envs}, Seed: {seed}")
    print("=" * 60)

    torch.manual_seed(seed)
    np.random.seed(seed)

    def make_env(rank):
        def _init():
            return HitAndRunEnv()
        return _init

    vec_env = DummyVecEnv([make_env(i) for i in range(n_envs)])
    eval_env = HitAndRunEnv()

    os.makedirs("checkpoints", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    callback = HitAndRunCallback(
        eval_env=eval_env,
        eval_freq=1000,
        n_eval_episodes=20,
        log_dir="logs",
        verbose=1
    )

    policy_kwargs = dict(
        net_arch=dict(pi=[128, 128], vf=[128, 128]),
        activation_fn=torch.nn.Tanh
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
        ent_coef=0.005,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs=policy_kwargs,
        verbose=0,
        seed=seed
    )

    model.learn(total_timesteps=total_timesteps, callback=callback)

    final_path = os.path.join("checkpoints", "final_phase4_hit_and_run_model.zip")
    model.save(final_path)
    print(f"Training Finished! Final model saved to {final_path}")

    vec_env.close()
    eval_env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=30000)
    parser.add_argument("--envs", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    train_hit_and_run(total_timesteps=args.timesteps, seed=args.seed, n_envs=args.envs)
