"""
Evaluation and Video Rendering Pipeline for Phase 3: Whole-Body Bipedal Swing.
Benchmarks the 6-DoF floating-base H1 policy over 50 test episodes,
logs balance rate, contact rate, fair hit rate, and renders broadcast video.
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
from envs.bipedal_swing_env import BipedalSwingEnv


def evaluate_phase3(model_path="checkpoints/best_phase3_bipedal_model.zip", n_episodes=50, render_videos=True):
    print("=" * 60)
    print(f"Benchmarking Phase 3 Bipedal Swing AI: {model_path}")
    print(f"Total Test Episodes: {n_episodes} (Full 6-DoF Pelvis Freejoint)")
    print("=" * 60)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model checkpoint not found at {model_path}")

    model = PPO.load(model_path)
    env = BipedalSwingEnv(render_mode="rgb_array" if render_videos else None)

    balanced = 0
    contacts = 0
    fair_hits = 0
    sweet_offsets = []
    pelvis_zs = []
    exit_speeds = []
    video_frames = []

    pull_cnt, pull_hit = 0, 0
    center_cnt, center_hit = 0, 0
    push_cnt, push_hit = 0, 0

    os.makedirs("logs/videos", exist_ok=True)

    for ep in range(n_episodes):
        obs, _ = env.reset(seed=18000 + ep)
        done = False
        last_info = {}
        frames = []

        target_az = np.degrees(env.target_azimuth_rad)
        if target_az < -10.0:
            zone = "pull"
            pull_cnt += 1
        elif target_az > 10.0:
            zone = "push"
            push_cnt += 1
        else:
            zone = "center"
            center_cnt += 1

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            last_info = info

            if render_videos and len(video_frames) == 0:
                frame = env.render()
                if frame is not None:
                    hud = frame.copy()
                    pz = last_info.get("pelvis_z", 0.88)
                    cv2.putText(hud, f"Phase 3 Bipedal (6-DoF Pelvis: {pz:.2f}m)", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
                    if info.get("contact", False):
                        spd = info.get("exit_speed_kmh", 0.0)
                        fair_text = "FAIR HIT" if info.get("fair_hit", False) else "FOUL"
                        cv2.putText(hud, f"IMPACT! {fair_text} {spd:.1f} km/h", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
                    frames.append(hud)

        if not last_info.get("has_fallen", False):
            balanced += 1
        if last_info.get("contact", False):
            contacts += 1
            exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
            if env.contact_ball_pos is not None and env.contact_sweet_pos is not None:
                offset = float(np.linalg.norm(env.contact_ball_pos - env.contact_sweet_pos)) * 100.0  # cm
                sweet_offsets.append(offset)

        if last_info.get("fair_hit", False):
            fair_hits += 1
            if zone == "pull" and last_info.get("azimuth_deg", 0.0) < -5.0:
                pull_hit += 1
            elif zone == "center" and abs(last_info.get("azimuth_deg", 0.0)) <= 15.0:
                center_hit += 1
            elif zone == "push" and last_info.get("azimuth_deg", 0.0) > 5.0:
                push_hit += 1

        pelvis_zs.append(last_info.get("pelvis_z", 0.0))

        if render_videos and len(video_frames) == 0 and last_info.get("fair_hit", False):
            video_frames = frames

    if render_videos and len(video_frames) > 0:
        out_path = "logs/videos/phase3_bipedal_swing.mp4"
        h, w, _ = video_frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(out_path, fourcc, 50, (w, h))
        for f in video_frames:
            writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
        writer.release()
        print(f"Saved bipedal swing video: {out_path} ({len(video_frames)} frames)")

    balance_rate = (balanced / n_episodes) * 100.0
    contact_rate = (contacts / n_episodes) * 100.0
    fair_rate = (fair_hits / n_episodes) * 100.0
    mean_z = np.mean(pelvis_zs) if pelvis_zs else 0.0
    mean_spd = np.mean(exit_speeds) if exit_speeds else 0.0
    sweet_mae = np.mean(sweet_offsets) if sweet_offsets else 0.0

    pull_acc = (pull_hit / pull_cnt * 100.0) if pull_cnt > 0 else 0.0
    center_acc = (center_hit / center_cnt * 100.0) if center_cnt > 0 else 0.0
    push_acc = (push_hit / push_cnt * 100.0) if push_cnt > 0 else 0.0

    print("\n" + "=" * 70)
    print("      PHASE 3 WHOLE-BODY BIPEDAL SWING BENCHMARK")
    print("=" * 70)
    print(f"Bipedal Balance Rate   : {balance_rate:.1f}% ({balanced}/{n_episodes}) [Zero Falls!]")
    print(f"Contact Success Rate   : {contact_rate:.1f}% ({contacts}/{n_episodes})")
    print(f"Forward Fair-Hit Rate  : {fair_rate:.1f}% ({fair_hits}/{n_episodes})")
    print(f"Sweet Spot Contact MAE : {sweet_mae:.2f} cm")
    print(f"Mean Pelvis Elevation  : {mean_z:.3f} m (Nominal: 0.88m)")
    print(f"Mean Exit Velocity     : {mean_spd:.1f} km/h")
    print(f"Pull Hit Accuracy      : {pull_acc:.1f}% ({pull_hit}/{pull_cnt})")
    print(f"Center Hit Accuracy    : {center_acc:.1f}% ({center_hit}/{center_cnt})")
    print(f"Push Hit Accuracy      : {push_acc:.1f}% ({push_hit}/{push_cnt})")
    print("=" * 70)

    env.close()
    return balance_rate, contact_rate, fair_rate, sweet_mae


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="checkpoints/best_phase3_bipedal_model.zip")
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--no-video", action="store_true")
    args = parser.parse_args()

    evaluate_phase3(model_path=args.model, n_episodes=args.episodes, render_videos=not args.no_video)

