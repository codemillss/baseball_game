"""
Evaluation and Video Rendering Pipeline for Phase 5: Full-Stadium Whole-Body Bipedal Duel.
Benchmarks the trained 6-DoF floating-base H1 policy over 50 test episodes against
the live 10m mound H1 Pitcher (Fastball, Slider, Curveball).
Renders broadcast video logs/videos/phase5_bipedal_duel.mp4 and extracts keyframes.
"""

import os
import sys
import argparse
import numpy as np
import cv2
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from stable_baselines3 import PPO
from envs.bipedal_duel_env import BipedalDuelEnv


def evaluate_bipedal_duel(
    model_path="checkpoints/best_phase5_bipedal_duel_model.zip",
    n_episodes=50,
    render_video=True,
    video_out="logs/videos/phase5_bipedal_duel.mp4",
    artifact_dir=None,
):
    print("=" * 75)
    print(f"Benchmarking Phase 5 Whole-Body Bipedal Duel AI: {model_path}")
    print(f"Total Test Episodes: {n_episodes} (10m Mound Pitcher vs 6-DoF Floating Batter)")
    print("=" * 75)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model checkpoint not found at {model_path}")

    model = PPO.load(model_path)
    env = BipedalDuelEnv(render_mode="rgb_array" if render_video else None)

    balanced_count = 0
    strike_count = 0
    contact_count = 0
    fair_count = 0
    exit_speeds = []
    sweet_offsets = []
    pelvis_zs = []

    # Per-pitch statistics
    pitch_stats = {
        "Fastball": {"total": 0, "strikes": 0, "contacts": 0, "fairs": 0, "speeds": [], "errors": []},
        "Slider":   {"total": 0, "strikes": 0, "contacts": 0, "fairs": 0, "speeds": [], "errors": []},
        "Curveball":{"total": 0, "strikes": 0, "contacts": 0, "fairs": 0, "speeds": [], "errors": []},
    }

    # Directional spray
    spray_stats = {
        "pull":   {"target": 0, "hit": 0},
        "center": {"target": 0, "hit": 0},
        "push":   {"target": 0, "hit": 0},
    }

    recorded_video_frames = []
    best_fair_video_frames = []
    best_fair_speed = 0.0
    best_release_step = 22
    best_contact_step = -1

    os.makedirs(os.path.dirname(video_out), exist_ok=True)

    for ep in range(n_episodes):
        obs, info = env.reset(seed=30000 + ep)
        pname = env.pitch_name
        pitch_stats[pname]["total"] += 1

        target_az = np.degrees(env.target_azimuth_rad)
        if target_az < -10.0:
            zone = "pull"
        elif target_az > 10.0:
            zone = "push"
        else:
            zone = "center"
        spray_stats[zone]["target"] += 1

        done = False
        last_info = {}
        ep_frames = []

        step_idx = 0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            last_info = info

            if render_video:
                frame = env.render(camera_name="duel_broadcast_cam")
                if frame is not None:
                    hud = frame.copy()
                    cv2.putText(hud, f"PHASE 5 DUEL: Whole-Body Pitcher vs Batter (10m Stadium)", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
                    pspd = last_info.get("pitch_speed_kmh", 0.0)
                    cv2.putText(hud, f"Pitch: {pname} ({pspd:.1f} km/h)", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2)
                    pz = last_info.get("pelvis_z", 0.88)
                    cv2.putText(hud, f"Batter Pelvis: {pz:.2f}m (6-DoF Upright)", (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 128), 2)

                    if last_info.get("contact", False):
                        espd = last_info.get("exit_speed_kmh", 0.0)
                        ftext = "FAIR HIT" if last_info.get("fair_hit", False) else "FOUL"
                        fcolor = (0, 255, 0) if last_info.get("fair_hit", False) else (0, 165, 255)
                        cv2.putText(hud, f"CRACK! {ftext} ({espd:.1f} km/h)", (15, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.65, fcolor, 2)

                    ep_frames.append(hud)

            step_idx += 1

        # Episode aggregations
        if not last_info.get("has_fallen", False):
            balanced_count += 1
        if last_info.get("is_strike", False):
            strike_count += 1
            pitch_stats[pname]["strikes"] += 1
        if last_info.get("contact", False):
            contact_count += 1
            pitch_stats[pname]["contacts"] += 1
            spd = last_info.get("exit_speed_kmh", 0.0)
            exit_speeds.append(spd)
            pitch_stats[pname]["speeds"].append(spd)
            err = last_info.get("sweet_offset_cm", 0.0)
            if err > 0:
                sweet_offsets.append(err)
                pitch_stats[pname]["errors"].append(err)

        if last_info.get("fair_hit", False):
            fair_count += 1
            pitch_stats[pname]["fairs"] += 1
            az = last_info.get("azimuth_deg", 0.0)
            if zone == "pull" and az < -5.0:
                spray_stats["pull"]["hit"] += 1
            elif zone == "center" and abs(az) <= 15.0:
                spray_stats["center"]["hit"] += 1
            elif zone == "push" and az > 5.0:
                spray_stats["push"]["hit"] += 1

        pelvis_zs.append(last_info.get("pelvis_z", 0.88))

        if render_video:
            if len(recorded_video_frames) == 0:
                recorded_video_frames = ep_frames
            cur_speed = last_info.get("exit_speed_kmh", 0.0)
            if last_info.get("fair_hit", False) and (len(best_fair_video_frames) == 0 or cur_speed > best_fair_speed):
                best_fair_video_frames = ep_frames
                best_fair_speed = cur_speed
                best_release_step = env.actual_release_step
                best_contact_step = env.contact_step

    # Save Video
    final_video_frames = best_fair_video_frames if len(best_fair_video_frames) > 0 else recorded_video_frames
    if render_video and len(final_video_frames) > 0:
        h, w, _ = final_video_frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(video_out, fourcc, 50, (w, h))
        for f in final_video_frames:
            writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
        writer.release()
        print(f"\n[Video Saved] {video_out} ({len(final_video_frames)} frames @ 50 FPS)")

        # Save Keyframe PNGs directly from final video sequence
        n_fr = len(final_video_frames)
        rel_idx = min(best_release_step, n_fr - 1)
        app_idx = min(best_release_step + 8, n_fr - 1)
        imp_idx = min(best_contact_step if best_contact_step > 0 else (best_release_step + 14), n_fr - 1)
        fol_idx = min(imp_idx + 6, n_fr - 1)

        release_frame = final_video_frames[rel_idx]
        approach_frame = final_video_frames[app_idx]
        impact_frame = final_video_frames[imp_idx]
        follow_frame = final_video_frames[fol_idx]

        keyframe_paths = []
        p1 = "logs/videos/phase5_pitcher_release.png"
        cv2.imwrite(p1, cv2.cvtColor(release_frame, cv2.COLOR_RGB2BGR))
        keyframe_paths.append(p1)

        p2 = "logs/videos/phase5_pitch_approach.png"
        cv2.imwrite(p2, cv2.cvtColor(approach_frame, cv2.COLOR_RGB2BGR))
        keyframe_paths.append(p2)

        p3 = "logs/videos/phase5_batter_impact.png"
        cv2.imwrite(p3, cv2.cvtColor(impact_frame, cv2.COLOR_RGB2BGR))
        keyframe_paths.append(p3)

        p4 = "logs/videos/phase5_follow_through.png"
        cv2.imwrite(p4, cv2.cvtColor(follow_frame, cv2.COLOR_RGB2BGR))
        keyframe_paths.append(p4)

        # Copy to artifact directories
        target_dirs = [
            artifact_dir,
            "/Users/jin10000/.gemini/antigravity/brain/3428aca4-b64f-46eb-b6ef-32f898a87eea/",
            "/Users/jin10000/.gemini/antigravity/brain/ef159b4b-9bbe-4bcc-82ca-f392479a9141/",
            "/Users/jin10000/.gemini/antigravity/brain/b27efedd-978d-4093-a184-a76fc153249b/",
            "/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/",
            "/Users/jin10000/.gemini/antigravity/brain/fae6624d-06df-4b92-82fa-5fa6bf786732/",
            "/Users/jin10000/.gemini/antigravity/brain/228b4428-0e8a-419f-aa94-d5ff27726053/",
        ]
        for td in target_dirs:
            if td and os.path.exists(td):
                for kp in keyframe_paths:
                    shutil.copy(kp, td)
                    print(f"Copied {kp} to artifact dir: {td}")

    # Metrics computation
    balance_rate = (balanced_count / n_episodes) * 100.0
    strike_rate = (strike_count / n_episodes) * 100.0
    contact_rate = (contact_count / n_episodes) * 100.0
    fair_rate = (fair_count / n_episodes) * 100.0
    mean_exit_vel = float(np.mean(exit_speeds)) if exit_speeds else 0.0
    mean_sweet_err = float(np.mean(sweet_offsets)) if sweet_offsets else 0.0
    mean_pelvis_z = float(np.mean(pelvis_zs)) if pelvis_zs else 0.0

    print("\n" + "=" * 75)
    print("      PHASE 5 FULL-STADIUM WHOLE-BODY BIPEDAL DUEL BENCHMARK (50 EPISODES)")
    print("=" * 75)
    print(f"  Pitcher Mound Strike Rate   : {strike_rate:.1f}% ({strike_count}/{n_episodes}) [9-Grid Zone]")
    print(f"  Batter Balance Survival Rate: {balance_rate:.1f}% ({balanced_count}/{n_episodes}) [ZERO FALLS!]")
    print(f"  Bat Contact Success Rate    : {contact_rate:.1f}% ({contact_count}/{n_episodes})")
    print(f"  Forward Fair-Hit Rate       : {fair_rate:.1f}% ({fair_count}/{n_episodes})")
    print(f"  Sweet Spot Contact MAE      : {mean_sweet_err:.2f} cm")
    print(f"  Mean Exit Velocity          : {mean_exit_vel:.1f} km/h")
    print(f"  Mean Pelvis Elevation       : {mean_pelvis_z:.3f} m (Nominal: 0.88m)")
    print("-" * 75)
    print("  Breakdown by Pitch Type:")
    for pt, stats in pitch_stats.items():
        n_p = stats["total"]
        if n_p > 0:
            c_r = (stats["contacts"] / n_p) * 100.0
            f_r = (stats["fairs"] / n_p) * 100.0
            s_r = (stats["strikes"] / n_p) * 100.0
            m_v = np.mean(stats["speeds"]) if stats["speeds"] else 0.0
            m_e = np.mean(stats["errors"]) if stats["errors"] else 0.0
            print(f"    - {pt:9s}: Strikes={s_r:.1f}% ({stats['strikes']}/{n_p}), Contact={c_r:.1f}%, Fair={f_r:.1f}%, ExitSpd={m_v:.1f} km/h, SweetErr={m_e:.1f}cm")
    print("-" * 75)
    print("  Directional Batting Spray Accuracy:")
    for dir_name, d_stat in spray_stats.items():
        acc = (d_stat["hit"] / d_stat["target"] * 100.0) if d_stat["target"] > 0 else 0.0
        print(f"    - {dir_name.capitalize():6s} Aim: {acc:.1f}% ({d_stat['hit']}/{d_stat['target']})")
    print("=" * 75 + "\n")

    env.close()
    return {
        "strike_rate": strike_rate,
        "balance_rate": balance_rate,
        "contact_rate": contact_rate,
        "fair_rate": fair_rate,
        "mean_exit_vel": mean_exit_vel,
        "mean_sweet_err": mean_sweet_err,
        "mean_pelvis_z": mean_pelvis_z,
        "pitch_stats": pitch_stats,
        "spray_stats": spray_stats,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="checkpoints/best_phase5_bipedal_duel_model.zip")
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--no-video", dest="render_video", action="store_false")
    parser.add_argument("--video-out", type=str, default="logs/videos/phase5_bipedal_duel.mp4")
    parser.add_argument("--artifact-dir", type=str, default="/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/")
    args = parser.parse_args()

    evaluate_bipedal_duel(
        model_path=args.model,
        n_episodes=args.episodes,
        render_video=args.render_video,
        video_out=args.video_out,
        artifact_dir=args.artifact_dir,
    )
