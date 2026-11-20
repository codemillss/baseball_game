"""
Evaluation and Video Rendering Pipeline for Goal-Conditioned Pitcher AI.
Evaluates the trained policy over 50 test episodes, logs quantitative metrics,
and renders multi-angle videos for Fastball, Slider, and Curveball pitches.
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
from envs.pitcher_precision_env import PitcherPrecisionEnv


def evaluate_pitcher(model_path="checkpoints/best_pitcher_model.zip", n_episodes=50, render_videos=True):
    print("=" * 60)
    print(f"Benchmarking Pitcher AI: {model_path}")
    print(f"Total Test Episodes: {n_episodes}")
    print("=" * 60)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model checkpoint not found at {model_path}")

    model = PPO.load(model_path)
    env = PitcherPrecisionEnv(render_mode="rgb_array" if render_videos else None)

    strikes = 0
    reached = 0
    errors_cm = []
    speeds_kmh = []

    type_stats = {
        0: {"name": "Fastball", "total": 0, "strikes": 0, "errors": [], "speeds": []},
        1: {"name": "Slider",   "total": 0, "strikes": 0, "errors": [], "speeds": []},
        2: {"name": "Curveball","total": 0, "strikes": 0, "errors": [], "speeds": []},
    }

    # Video storage
    video_frames = {0: [], 1: [], 2: []}
    video_saved = {0: False, 1: False, 2: False}

    os.makedirs("logs/videos", exist_ok=True)

    for ep in range(n_episodes):
        obs, _ = env.reset(seed=9000 + ep)
        ptype = env.pitch_type
        type_stats[ptype]["total"] += 1
        done = False
        last_info = {}
        frames = []

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            last_info = info

            if render_videos and not video_saved[ptype]:
                frame = env.render()
                if frame is not None:
                    # Draw HUD overlay
                    hud = frame.copy()
                    ptype_name = type_stats[ptype]["name"]
                    tx, tz = env.target_x, env.target_z
                    bpos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
                    spd = info.get("release_speed_kmh", 0.0)

                    cv2.putText(hud, f"Pitch: {ptype_name}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    cv2.putText(hud, f"Target: [{tx:+.2f}, {tz:.2f}]m", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                    cv2.putText(hud, f"Speed : {spd:.1f} km/h", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
                    frames.append(hud)

        if last_info.get("reached_plate", False):
            reached += 1
            err = last_info.get("dist_error_cm", 99.0)
            spd = last_info.get("release_speed_kmh", 0.0)
            errors_cm.append(err)
            speeds_kmh.append(spd)
            type_stats[ptype]["errors"].append(err)
            type_stats[ptype]["speeds"].append(spd)

            if last_info.get("is_strike", False):
                strikes += 1
                type_stats[ptype]["strikes"] += 1

        if render_videos and not video_saved[ptype] and len(frames) > 0:
            video_frames[ptype] = frames
            video_saved[ptype] = True

    # Save representative videos
    if render_videos:
        for ptype, name in [(0, "fastball"), (1, "slider"), (2, "curveball")]:
            if len(video_frames[ptype]) > 0:
                out_path = f"logs/videos/pitcher_{name}.mp4"
                h, w, _ = video_frames[ptype][0].shape
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(out_path, fourcc, 50, (w, h))
                for f in video_frames[ptype]:
                    writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
                writer.release()
                print(f"Saved evaluation video: {out_path} ({len(video_frames[ptype])} frames)")

    # Print Quantitative Summary Table
    overall_strike_rate = (strikes / n_episodes) * 100.0
    overall_mae = np.mean(errors_cm) if errors_cm else 99.0
    overall_speed = np.mean(speeds_kmh) if speeds_kmh else 0.0

    print("\n" + "=" * 70)
    print("           PITCHER EVALUATION BENCHMARK RESULTS")
    print("=" * 70)
    print(f"Overall Strike Rate     : {overall_strike_rate:.1f}% ({strikes}/{n_episodes})")
    print(f"Mean Target Error (MAE) : {overall_mae:.2f} cm")
    print(f"Mean Pitch Speed        : {overall_speed:.1f} km/h")
    print("-" * 70)
    for pt in [0, 1, 2]:
        s = type_stats[pt]
        rate = (s["strikes"] / max(1, s["total"])) * 100.0
        mae = np.mean(s["errors"]) if s["errors"] else 99.0
        spd = np.mean(s["speeds"]) if s["speeds"] else 0.0
        print(f"  {s['name']:10s} Strike Rate : {rate:5.1f}% ({s['strikes']:2d}/{s['total']:2d}) | MAE: {mae:5.2f} cm | Speed: {spd:5.1f} km/h")
    print("=" * 70)

    env.close()
    return overall_strike_rate, overall_mae


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="checkpoints/best_pitcher_model.zip")
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--no-video", action="store_true")
    args = parser.parse_args()

    evaluate_pitcher(model_path=args.model, n_episodes=args.episodes, render_videos=not args.no_video)
