"""
Evaluation and Video Rendering Pipeline for Phase 4: Hit-and-Run Locomotion Transition.
Benchmarks the 19-DoF floating-base H1 policy over 50 test episodes,
logs balance rate, contact rate, fair hit rate, bat release, sprint distance,
and renders tracking broadcast video.
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
from envs.hit_and_run_env import HitAndRunEnv


def evaluate_hit_and_run(model_path="checkpoints/best_phase4_hit_and_run_model.zip", n_episodes=50, render_videos=True):
    print("=" * 65)
    print(f"Benchmarking Phase 4 Hit-and-Run Transition AI: {model_path}")
    print(f"Total Test Episodes: {n_episodes} (Full 6-DoF Pelvis Freejoint + Bat Drop)")
    print("=" * 65)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model checkpoint not found at {model_path}")

    model = PPO.load(model_path)
    env = HitAndRunEnv(render_mode="rgb_array" if render_videos else None)

    balanced = 0
    contacts = 0
    fair_hits = 0
    bat_releases = 0
    distances_traveled = []
    exit_speeds = []
    video_frames = []

    os.makedirs("logs/videos", exist_ok=True)

    for ep in range(n_episodes):
        obs, _ = env.reset(seed=22000 + ep)
        done = False
        last_info = {}
        frames = []

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            last_info = info

            if render_videos and len(video_frames) == 0:
                frame = env.render(camera_name="run_tracking_cam")
                if frame is not None:
                    hud = frame.copy()
                    pz = last_info.get("pelvis_z", 0.88)
                    d_1b = last_info.get("dist_to_1b", 9.8)
                    d_tr = last_info.get("dist_traveled", 0.0)
                    cv2.putText(hud, f"Phase 4 Hit & Run (Pelvis: {pz:.2f}m | 1B Dist: {d_1b:.2f}m)", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 255, 255), 2)
                    
                    if last_info.get("contact", False):
                        spd = last_info.get("exit_speed_kmh", 0.0)
                        fair_str = "FAIR" if last_info.get("fair_hit", False) else "FOUL"
                        cv2.putText(hud, f"HIT: {fair_str} ({spd:.1f} km/h)", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 255, 0), 2)
                    
                    if last_info.get("bat_released", False):
                        cv2.putText(hud, f"BAT DROPPED! SPRINT TO 1ST BASE (+{d_tr:.2f}m)", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (255, 128, 0), 2)

                    frames.append(hud)

        if not last_info.get("has_fallen", False):
            balanced += 1
        if last_info.get("contact", False):
            contacts += 1
            exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
        if last_info.get("fair_hit", False):
            fair_hits += 1
        if last_info.get("bat_released", False):
            bat_releases += 1
        distances_traveled.append(last_info.get("dist_traveled", 0.0))

        if render_videos and len(video_frames) == 0 and last_info.get("fair_hit", False) and last_info.get("bat_released", False):
            video_frames = frames

    if render_videos and len(video_frames) > 0:
        out_path = "logs/videos/phase4_hit_and_run.mp4"
        h, w, _ = video_frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(out_path, fourcc, 50, (w, h))
        for f in video_frames:
            writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
        writer.release()
        print(f"Saved Hit & Run video: {out_path} ({len(video_frames)} frames)")

    balance_rate = (balanced / n_episodes) * 100.0
    contact_rate = (contacts / n_episodes) * 100.0
    fair_rate = (fair_hits / n_episodes) * 100.0
    bat_rel_rate = (bat_releases / n_episodes) * 100.0
    mean_dist = float(np.mean(distances_traveled)) if distances_traveled else 0.0
    mean_spd = float(np.mean(exit_speeds)) if exit_speeds else 0.0

    print("\n" + "=" * 70)
    print("      PHASE 4 HIT-AND-RUN LOCOMOTION TRANSITION BENCHMARK")
    print("=" * 70)
    print(f"Bipedal Balance Rate     : {balance_rate:.1f}% ({balanced}/{n_episodes})")
    print(f"Contact Success Rate     : {contact_rate:.1f}% ({contacts}/{n_episodes})")
    print(f"Forward Fair-Hit Rate    : {fair_rate:.1f}% ({fair_hits}/{n_episodes})")
    print(f"Bat Release Rate         : {bat_rel_rate:.1f}% ({bat_releases}/{n_episodes})")
    print(f"Mean 1B Sprint Distance  : {mean_dist:.2f} m")
    print(f"Mean Ball Exit Velocity  : {mean_spd:.1f} km/h")
    print("=" * 70)

    env.close()
    return balance_rate, contact_rate, fair_rate, bat_rel_rate, mean_dist


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="checkpoints/best_phase4_hit_and_run_model.zip")
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--no-video", action="store_true")
    args = parser.parse_args()

    evaluate_hit_and_run(model_path=args.model, n_episodes=args.episodes, render_videos=not args.no_video)
