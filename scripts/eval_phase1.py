"""
Evaluation & Quantitative Benchmark Script for Phase 1 Directional Batting.
Evaluates:
- Contact Success Rate (%) & Fair-Ball Forward Hit Rate (%)
- Sweet Spot Precision Offset (cm)
- Azimuth Directional Error (MAE in degrees)
- Launch Angle Error (MAE in degrees)
- Exit Velocity Distribution (m/s and km/h)
- Field Spray Chart Breakdown (Pull vs Center vs Push accuracy)
- High-definition multi-camera MP4 video recordings of fair hits.
"""

import os
import sys
import argparse
import numpy as np
import imageio

# Ensure repository root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from stable_baselines3 import PPO
import gymnasium as gym
import envs


def evaluate_policy(
    model_path="checkpoints/best_phase1_model.zip",
    n_episodes=50,
    render_video=True,
    video_dir="logs/videos",
    seed=42,
):
    os.makedirs(video_dir, exist_ok=True)

    print(f"📂 Loading model from: {model_path}")
    if os.path.exists(model_path):
        model = PPO.load(model_path)
    else:
        print(f"⚠️ Model path {model_path} not found. Using baseline actions.")
        model = None

    env = gym.make("DirectionalBatting-v0", render_mode="rgb_array")

    contacts = 0
    fair_hits = 0
    sweet_offsets = []
    azimuth_errors = []
    launch_errors = []
    exit_velocities = []

    pull_targets, pull_success = 0, 0
    center_targets, center_success = 0, 0
    push_targets, push_success = 0, 0

    record_categories = {"pull": None, "center": None, "push": None}

    print(f"🔬 Running {n_episodes} Quantitative Evaluation Episodes (Seed: {seed})...")

    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False
        frames = []
        ep_contact = False
        ep_fair = False
        ep_info = {}

        target_azimuth_rad = obs[7]
        target_azimuth_deg = float(np.degrees(target_azimuth_rad))

        if target_azimuth_deg < -10.0:
            category = "pull"
            pull_targets += 1
        elif target_azimuth_deg > 10.0:
            category = "push"
            push_targets += 1
        else:
            category = "center"
            center_targets += 1

        while not done:
            if render_video and record_categories[category] is None:
                frame = env.render()
                if frame is not None:
                    frames.append(frame)

            if model is not None:
                action, _ = model.predict(obs, deterministic=True)
            else:
                action = np.zeros(5, dtype=np.float32)

            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            if info.get("contact", False):
                ep_contact = True
                ep_info = info
            if info.get("fair_hit", False):
                ep_fair = True

        if ep_contact:
            contacts += 1
            sweet_offsets.append(ep_info.get("sweet_spot_offset_cm", 99.0))
            exit_velocities.append(ep_info.get("exit_speed_ms", 0.0))

            if ep_fair:
                fair_hits += 1
                az_err = ep_info.get("azimuth_error_deg", 99.0)
                la_err = ep_info.get("launch_error_deg", 99.0)
                azimuth_errors.append(az_err)
                launch_errors.append(la_err)

                # Directional spray alignment criterion: within 25° of target
                if az_err < 25.0:
                    if category == "pull":
                        pull_success += 1
                    elif category == "push":
                        push_success += 1
                    else:
                        center_success += 1

                # Save video if this is the first fair hit for this category
                if render_video and record_categories[category] is None and len(frames) > 0:
                    record_categories[category] = frames

    # Save rendered video clips
    for cat_name, cat_frames in record_categories.items():
        if cat_frames is not None and len(cat_frames) > 0:
            vid_path = os.path.join(video_dir, f"phase1_{cat_name}_hit.mp4")
            imageio.mimsave(vid_path, cat_frames, fps=30)
            print(f"🎥 Saved demonstration video: {vid_path}")

    # Compute Aggregate Metrics
    contact_rate = (contacts / n_episodes) * 100.0
    fair_rate = (fair_hits / n_episodes) * 100.0
    mean_sweet = float(np.mean(sweet_offsets)) if sweet_offsets else 0.0
    std_sweet = float(np.std(sweet_offsets)) if sweet_offsets else 0.0
    mean_az_err = float(np.mean(azimuth_errors)) if azimuth_errors else 0.0
    std_az_err = float(np.std(azimuth_errors)) if azimuth_errors else 0.0
    mean_la_err = float(np.mean(launch_errors)) if launch_errors else 0.0
    std_la_err = float(np.std(launch_errors)) if launch_errors else 0.0
    mean_vel = float(np.mean(exit_velocities)) if exit_velocities else 0.0
    max_vel = float(np.max(exit_velocities)) if exit_velocities else 0.0

    pull_acc = (pull_success / max(1, pull_targets)) * 100.0
    center_acc = (center_success / max(1, center_targets)) * 100.0
    push_acc = (push_success / max(1, push_targets)) * 100.0

    print("\n" + "=" * 65)
    print("🏆 PHASE 1 QUANTITATIVE BENCHMARK REPORT")
    print("=" * 65)
    print(f"Episodes Evaluated:         {n_episodes}")
    print(f"Contact Success Rate:       {contact_rate:.1f}% ({contacts}/{n_episodes})")
    print(f"Fair-Ball Forward Hit Rate: {fair_rate:.1f}% ({fair_hits}/{n_episodes})")
    print(f"Sweet Spot Offset:          {mean_sweet:.2f} ± {std_sweet:.2f} cm")
    print(f"Azimuth Error (MAE):        {mean_az_err:.2f}° ± {std_az_err:.2f}°")
    print(f"Launch Angle Error (MAE):   {mean_la_err:.2f}° ± {std_la_err:.2f}°")
    print(f"Mean Exit Velocity:         {mean_vel:.1f} m/s ({mean_vel*3.6:.1f} km/h)")
    print(f"Peak Exit Velocity:         {max_vel:.1f} m/s ({max_vel*3.6:.1f} km/h)")
    print("-" * 65)
    print("🎯 DIRECTIONAL SPRAY CONTROL ACCURACY (Target vs Actual):")
    print(f"  • Pull Hit (Left Field):   {pull_acc:.1f}% ({pull_success}/{pull_targets})")
    print(f"  • Center Field Line Drive: {center_acc:.1f}% ({center_success}/{center_targets})")
    print(f"  • Push Hit (Right Field):  {push_acc:.1f}% ({push_success}/{push_targets})")
    print("=" * 65 + "\n")

    env.close()
    return {
        "contact_rate": contact_rate,
        "fair_rate": fair_rate,
        "sweet_offset_cm": mean_sweet,
        "azimuth_mae_deg": mean_az_err,
        "launch_mae_deg": mean_la_err,
        "mean_exit_vel_ms": mean_vel,
        "max_exit_vel_ms": max_vel,
        "pull_acc": pull_acc,
        "center_acc": center_acc,
        "push_acc": push_acc,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="checkpoints/best_phase1_model.zip")
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--video-dir", type=str, default="logs/videos")
    args = parser.parse_args()

    evaluate_policy(
        model_path=args.model,
        n_episodes=args.episodes,
        video_dir=args.video_dir,
        seed=args.seed,
    )
