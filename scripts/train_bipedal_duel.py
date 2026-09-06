"""
Training Pipeline for Phase 5: Full-Stadium Whole-Body Bipedal Pitcher vs Batter Closed-Loop Duel.
Fine-tunes the 6-DoF floating-base Whole-Body H1 Batter against the live 10m mound H1 Pitcher
throwing Fastballs (80-88 km/h), Sliders (70-78 km/h), and Curveballs (62-70 km/h).
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

from envs.bipedal_duel_env import BipedalDuelEnv


class BipedalDuelCallback(BaseCallback):
    """Logs balance survival rate, strike rate, contact rate, fair hit rate, and exit velocity."""
    def __init__(self, eval_env, eval_freq=1000, n_eval_episodes=25, log_dir="logs", verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.log_dir = log_dir
        self.best_score = -999.0
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "phase5_bipedal_duel_progress.csv")
        with open(self.log_file, "w") as f:
            f.write("timesteps,balance_rate,strike_rate,contact_rate,fair_hit_rate,mean_exit_vel,mean_pelvis_z\n")

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq != 0:
            return True

        balanced = 0
        strikes = 0
        contacts = 0
        fair_hits = 0
        exit_speeds = []
        pelvis_zs = []

        for ep in range(self.n_eval_episodes):
            obs, _ = self.eval_env.reset(seed=25000 + ep)
            done = False
            last_info = {}

            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = self.eval_env.step(action)
                done = terminated or truncated
                last_info = info

            if not last_info.get("has_fallen", False):
                balanced += 1
            if last_info.get("is_strike", False):
                strikes += 1
            if last_info.get("contact", False):
                contacts += 1
                exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
            if last_info.get("fair_hit", False):
                fair_hits += 1
            pelvis_zs.append(last_info.get("pelvis_z", 0.0))

        balance_rate = (balanced / self.n_eval_episodes) * 100.0
        strike_rate = (strikes / self.n_eval_episodes) * 100.0
        contact_rate = (contacts / self.n_eval_episodes) * 100.0
        fair_rate = (fair_hits / self.n_eval_episodes) * 100.0
        mean_spd = float(np.mean(exit_speeds)) if exit_speeds else 0.0
        mean_z = float(np.mean(pelvis_zs)) if pelvis_zs else 0.0

        if self.verbose > 0:
            print(f"\n--- [Phase 5 Bipedal Duel Eval @ Step {self.n_calls}] ---")
            print(f"  Balance Survival Rate : {balance_rate:.1f}% ({balanced}/{self.n_eval_episodes}) [Zero Falls!]")
            print(f"  Mound Pitcher Strike  : {strike_rate:.1f}% ({strikes}/{self.n_eval_episodes})")
            print(f"  Contact Success Rate  : {contact_rate:.1f}% ({contacts}/{self.n_eval_episodes})")
            print(f"  Forward Fair-Hit Rate : {fair_rate:.1f}% ({fair_hits}/{self.n_eval_episodes})")
            print(f"  Mean Exit Velocity    : {mean_spd:.1f} km/h")
            print(f"  Mean Pelvis Elevation : {mean_z:.3f} m")

        with open(self.log_file, "a") as f:
            f.write(f"{self.n_calls},{balance_rate:.2f},{strike_rate:.2f},{contact_rate:.2f},{fair_rate:.2f},{mean_spd:.2f},{mean_z:.3f}\n")

        # Prioritize zero falls (>= 95% balance) and reward high contact & fair hit rates
        balance_weight = balance_rate if balance_rate >= 95.0 else (balance_rate * 0.1)
        score = balance_weight + 2.0 * contact_rate + 2.0 * fair_rate + 0.1 * mean_spd
        if score > self.best_score:
            self.best_score = score
            os.makedirs("checkpoints", exist_ok=True)
            ckpt_path = os.path.join("checkpoints", "best_phase5_bipedal_duel_model.zip")
            self.model.save(ckpt_path)
            if self.verbose > 0:
                print(f"  >>> New Best Phase 5 Duel Model Saved to {ckpt_path}! (Score: {score:.1f})")

        return True


def train_bipedal_duel(total_timesteps=20000, seed=42, n_envs=4, warm_start=True):
    print("=" * 70)
    print("Initiating Phase 5 Full-Stadium Whole-Body Bipedal Duel PPO Training")
    print(f"Timesteps: {total_timesteps}, Envs: {n_envs}, Seed: {seed}, WarmStart: {warm_start}")
    print("=" * 70)

    torch.manual_seed(seed)
    np.random.seed(seed)

    def make_env(env_seed):
        def _init():
            env = BipedalDuelEnv()
            env = Monitor(env)
            env.reset(seed=env_seed)
            return env
        return _init

    vec_env = DummyVecEnv([make_env(seed + i * 100) for i in range(n_envs)])
    eval_env = BipedalDuelEnv()

    callback = BipedalDuelCallback(
        eval_env=eval_env,
        eval_freq=1000,
        n_eval_episodes=25,
        log_dir="logs",
        verbose=1,
    )

    base_ckpt = os.path.join("checkpoints", "best_phase3_bipedal_model.zip")
    if warm_start and os.path.exists(base_ckpt):
        print(f"Warm-starting from Phase 3 checkpoint: {base_ckpt}")
        model = PPO.load(
            base_ckpt,
            env=vec_env,
            learning_rate=2e-4,
            n_steps=512,
            batch_size=64,
            n_epochs=10,
            seed=seed,
        )
    else:
        print("Training policy from scratch...")
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

    print("Starting Bipedal Pitcher-Batter Closed-Loop Optimization...")
    model.learn(total_timesteps=total_timesteps, callback=callback)

    final_path = os.path.join("checkpoints", "final_phase5_bipedal_duel_model.zip")
    model.save(final_path)
    best_path = os.path.join("checkpoints", "best_phase5_bipedal_duel_model.zip")
    if not os.path.exists(best_path):
        model.save(best_path)

    print(f"\nPhase 5 Training Complete! Final model saved to {final_path}")
    print(f"Best model saved to {best_path}")
    vec_env.close()
    eval_env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--envs", type=int, default=4)
    parser.add_argument("--no-warm-start", dest="warm_start", action="store_false")
    args = parser.parse_args()

    train_bipedal_duel(total_timesteps=args.timesteps, seed=args.seed, n_envs=args.envs, warm_start=args.warm_start)
