"""
Evaluation and Video Rendering for Phase 2: Sim-to-Real Hardened Batting.
Benchmarks the policy across 50 test episodes under latency buffers,
motor torque saturation, and domain randomization (bat mass +/-10%, sensor jitter).
"""

import os
import sys
import argparse
import numpy as np
import cv2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from stable_baselines3 import PPO
from envs.hardened_batting_env import HardenedBattingEnv


def evaluate_hardened_batter(model_path="checkpoints/best_phase2_hardened_model.zip", n_episodes=50, render_videos=True):
    print("=" * 60)
    print(f"Benchmarking Phase 2 Hardened Batter AI: {model_path}")
    print(f"Total Test Episodes: {n_episodes} (with Latency + Domain Randomization)")
    print("=" * 60)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model checkpoint not found at {model_path}")

    model = PPO.load(model_path)
    env = HardenedBattingEnv(
        render_mode="rgb_array" if render_videos else None,
        latency_steps=1,
        enable_domain_randomization=True
    )

    contacts = 0
    fair_hits = 0
    sweet_offsets = []
    az_errors = []
    la_errors = []
    exit_speeds = []

    pull_cnt, pull_hit = 0, 0
    center_cnt, center_hit = 0, 0
    push_cnt, push_hit = 0, 0

    video_frames = {"pull": [], "center": [], "push": []}
    video_saved = {"pull": False, "center": False, "push": False}

    os.makedirs("logs/videos", exist_ok=True)

    for ep in range(n_episodes):
        obs, _ = env.reset(seed=12000 + ep)
        done = False
        last_info = {}
        frames = []

        target_az = np.degrees(env.target_azimuth_rad)
        if target_az < -10.0:
            cat = "pull"
            pull_cnt += 1
        elif target_az > 10.0:
            cat = "push"
            push_cnt += 1
        else:
            cat = "center"
            center_cnt += 1

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            last_info = info

            if render_videos and not video_saved[cat]:
                frame = env.render()
                if frame is not None:
                    hud = frame.copy()
                    bat_m = float(env.model.body_mass[env.bat_body_id])
                    cv2.putText(hud, f"Phase 2 Hardened (Latency: 20ms, Mass: {bat_m:.2f}kg)", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
                    cv2.putText(hud, f"Goal: {cat.upper()} ({target_az:+.1f} deg)", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                    if info.get("contact", False):
                        spd = info.get("exit_speed_kmh", 0.0)
                        cv2.putText(hud, f"IMPACT! Speed: {spd:.1f} km/h", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
                    frames.append(hud)

        if last_info.get("contact", False):
            contacts += 1
            sweet_offsets.append(last_info.get("sweet_spot_offset_cm", 99.0))
            exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))

            if last_info.get("fair_hit", False):
                fair_hits += 1
                az_err = last_info.get("azimuth_error_deg", 99.0)
                la_err = last_info.get("launch_error_deg", 99.0)
                az_errors.append(az_err)
                la_errors.append(la_err)

                if az_err < 25.0:
                    if cat == "pull":
                        pull_hit += 1
                    elif cat == "push":
                        push_hit += 1
                    else:
                        center_hit += 1

        if render_videos and not video_saved[cat] and len(frames) > 0 and last_info.get("fair_hit", False):
            video_frames[cat] = frames
            video_saved[cat] = True

    if render_videos:
        for cat in ["pull", "center", "push"]:
            if len(video_frames[cat]) > 0:
                out_path = f"logs/videos/phase2_{cat}_hit.mp4"
                h, w, _ = video_frames[cat][0].shape
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(out_path, fourcc, 50, (w, h))
                for f in video_frames[cat]:
                    writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
                writer.release()
                print(f"Saved hardened video: {out_path} ({len(video_frames[cat])} frames)")

    contact_rate = (contacts / n_episodes) * 100.0
    fair_rate = (fair_hits / n_episodes) * 100.0
    mean_offset = np.mean(sweet_offsets) if sweet_offsets else 99.0
    mean_az_err = np.mean(az_errors) if az_errors else 99.0
    mean_la_err = np.mean(la_errors) if la_errors else 99.0
    mean_spd = np.mean(exit_speeds) if exit_speeds else 0.0

    print("\n" + "=" * 70)
    print("      PHASE 2 HARDENED BATTER SIM-TO-REAL BENCHMARK")
    print("=" * 70)
    print(f"Contact Success Rate   : {contact_rate:.1f}% ({contacts}/{n_episodes})")
    print(f"Forward Fair-Hit Rate  : {fair_rate:.1f}% ({fair_hits}/{n_episodes})")
    print(f"Sweet Spot Offset (MAE): {mean_offset:.2f} cm")
    print(f"Azimuth Error (MAE)    : {mean_az_err:.2f}°")
    print(f"Launch Angle Error     : {mean_la_err:.2f}°")
    print(f"Mean Exit Velocity     : {mean_spd:.1f} km/h")
    print("-" * 70)
    print(f"  Pull-hit Accuracy    : {(pull_hit / max(1, pull_cnt))*100:.1f}% ({pull_hit}/{pull_cnt})")
    print(f"  Center-hit Accuracy  : {(center_hit / max(1, center_cnt))*100:.1f}% ({center_hit}/{center_cnt})")
    print(f"  Push-hit Accuracy    : {(push_hit / max(1, push_cnt))*100:.1f}% ({push_hit}/{push_cnt})")
    print("=" * 70)

    env.close()
    return contact_rate, fair_rate, mean_az_err


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="checkpoints/best_phase2_hardened_model.zip")
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--no-video", action="store_true")
    args = parser.parse_args()

    evaluate_hardened_batter(model_path=args.model, n_episodes=args.episodes, render_videos=not args.no_video)
