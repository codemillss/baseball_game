import os
import sys
sys.path.append(os.path.abspath("."))

import argparse
import csv
import shutil
import numpy as np
import cv2
import imageio
from stable_baselines3 import PPO
from envs.athletic_duel_env import AthleticDuelEnv

ARTIFACTS_DIR = "/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7"

def evaluate(episodes=50, render_video=True):
    os.makedirs("logs/videos", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    env = AthleticDuelEnv(render_mode="rgb_array")

    model_path = "checkpoints/best_athletic_duel_model.zip"
    if not os.path.exists(model_path):
        model_path = "checkpoints/final_athletic_duel_model.zip"

    model = None
    if os.path.exists(model_path):
        print(f"Loading trained policy from {model_path}...")
        model = PPO.load(model_path, env=env)
    else:
        print("Model checkpoint not found, running with zero action baseline.")

    records = []
    print(f"\n--- Starting Athletic Duel Benchmark: {episodes} Episodes ---")
    
    # Track episodes for video/gif rendering
    best_hit_ep = -1
    best_hit_speed = -1.0

    for ep in range(episodes):
        obs, info = env.reset(seed=ep * 100 + 42)
        done = False
        ep_reward = 0.0
        step = 0
        last_step_info = None

        while not done:
            if model is not None:
                action, _ = model.predict(obs, deterministic=True)
            else:
                action = np.zeros(6, dtype=np.float32)

            obs, reward, terminated, truncated, step_info = env.step(action)
            ep_reward += reward
            step += 1
            last_step_info = step_info
            done = terminated or truncated

        if step_info["is_hit"] and step_info["exit_velocity_kmh"] > best_hit_speed:
            best_hit_speed = step_info["exit_velocity_kmh"]
            best_hit_ep = ep

        records.append({
            "episode": ep + 1,
            "pitch_type": step_info["pitch_type"],
            "pitch_speed_kmh": float(step_info["pitch_speed_kmh"]),
            "is_strike": bool(step_info["is_strike"]),
            "is_hit": bool(step_info["is_hit"]),
            "is_fair": bool(step_info["is_fair"]),
            "sweet_spot_error_cm": float(step_info["sweet_spot_error_cm"]),
            "exit_velocity_kmh": float(step_info["exit_velocity_kmh"]),
            "exit_heading_deg": float(step_info["exit_heading_deg"]),
            "batter_fallen": bool(step_info["batter_fallen"]),
            "catcher_fallen": bool(step_info["catcher_fallen"]),
            "catcher_caught": bool(step_info["catcher_caught"]),
            "batter_pelvis_z": float(step_info["batter_pelvis_z"]),
            "catcher_pelvis_z": float(step_info["catcher_pelvis_z"]),
            "plate_cross_x": float(step_info["plate_cross_x"]),
            "plate_cross_z": float(step_info["plate_cross_z"]),
            "left_foot_lift_cm": float(step_info["left_foot_lift_cm"]),
            "hand_distance_cm": float(step_info["hand_distance_cm"]),
            "torso_rotation_deg": float(step_info["torso_rotation_deg"]),
            "catcher_drift_cm": float(step_info["catcher_drift_cm"]),
            "ep_reward": float(ep_reward)
        })

    csv_path = "logs/athletic_duel_metrics.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    print(f"\nSaved benchmark metrics to {csv_path}")

    # Summary
    n_total = len(records)
    b_surv = sum(not r["batter_fallen"] for r in records) / n_total * 100
    c_surv = sum(not r["catcher_fallen"] for r in records) / n_total * 100
    hits = sum(r["is_hit"] for r in records) / n_total * 100
    fairs = sum(r["is_fair"] for r in records) / n_total * 100
    strikes = sum(r["is_strike"] for r in records) / n_total * 100
    caught = sum(r["catcher_caught"] for r in records if not r["is_hit"])
    unhit = sum(not r["is_hit"] for r in records)
    catch_rate = (caught / unhit * 100) if unhit > 0 else 100.0

    hit_errs = [r["sweet_spot_error_cm"] for r in records if r["is_hit"]]
    mean_sw_err = np.mean(hit_errs) if len(hit_errs) > 0 else 0.0
    hit_vels = [r["exit_velocity_kmh"] for r in records if r["is_hit"]]
    mean_exit_v = np.mean(hit_vels) if len(hit_vels) > 0 else 0.0

    mean_l_lift = np.mean([r["left_foot_lift_cm"] for r in records])
    mean_h_dist = np.mean([r["hand_distance_cm"] for r in records])
    mean_c_drift = np.mean([r["catcher_drift_cm"] for r in records])

    print("=" * 65)
    print("--- 50-EPISODE ATHLETIC DUEL BENCHMARK SUMMARY ---")
    print(f"Total Episodes:                 {n_total}")
    print(f"Batter Balance Survival Rate:   {b_surv:.1f}% ({sum(not r['batter_fallen'] for r in records)}/{n_total})")
    print(f"Catcher Squat Survival Rate:    {c_surv:.1f}% ({sum(not r['catcher_fallen'] for r in records)}/{n_total})")
    print(f"Bat Contact Rate:               {hits:.1f}% ({sum(r['is_hit'] for r in records)}/{n_total})")
    print(f"Fair-Hit Rate:                  {fairs:.1f}% ({sum(r['is_fair'] for r in records)}/{n_total})")
    print(f"Strike Zone Adherence Rate:     {strikes:.1f}% ({sum(r['is_strike'] for r in records)}/{n_total})")
    print(f"Catcher Catch on Taken Pitches: {catch_rate:.1f}% ({caught}/{unhit})")
    print(f"Mean Sweet Spot Error MAE:      {mean_sw_err:.2f} cm")
    print(f"Mean Exit Velocity:             {mean_exit_v:.1f} km/h")
    print(f"Mean Lead Foot Lift:            {mean_l_lift:.2f} cm (Target: < 0.20 cm)")
    print(f"Mean Hand Distance:             {mean_h_dist:.2f} cm (Target: < 0.50 cm)")
    print(f"Mean Catcher Squat Drift:       {mean_c_drift:.2f} cm (Target: < 5.00 cm)")
    print("=" * 65)

    for ptype in ["Fastball", "Slider", "Curveball"]:
        sub = [r for r in records if r["pitch_type"] == ptype]
        if sub:
            c_cnt = len(sub)
            s_hit = sum(r["is_hit"] for r in sub) / c_cnt * 100
            s_fair = sum(r["is_fair"] for r in sub) / c_cnt * 100
            s_spd = np.mean([r["pitch_speed_kmh"] for r in sub])
            s_errs = [r["sweet_spot_error_cm"] for r in sub if r["is_hit"]]
            s_err = np.mean(s_errs) if s_errs else 0.0
            print(f"[{ptype:>9s}] Count: {c_cnt:2d} | Hit: {s_hit:5.1f}% | Fair: {s_fair:5.1f}% | Spd: {s_spd:4.1f} km/h | Err: {s_err:4.1f} cm")

    # Render Multi-Camera Video and Animated GIFs
    if render_video:
        target_ep = best_hit_ep if best_hit_ep >= 0 else 0
        print(f"\nRendering multi-camera demonstration using Episode {target_ep + 1} (Seed {target_ep * 100 + 42})...")

        obs, info = env.reset(seed=target_ep * 100 + 42)
        done = False
        step = 0

        video_frames = []
        dugout_frames = []
        cf_frames = []
        catcher_frames = []
        capture_frames = {}

        while not done:
            if model is not None:
                action, _ = model.predict(obs, deterministic=True)
            else:
                action = np.zeros(6, dtype=np.float32)

            obs, reward, terminated, truncated, step_info = env.step(action)
            step += 1

            # Multi-camera rendering
            f_dugout = env.render(camera_name="duel_broadcast_cam")
            f_cf = env.render(camera_name="cf_broadcast_cam")
            f_catcher = env.render(camera_name="catcher_framing_cam")

            dugout_frames.append(f_dugout)
            cf_frames.append(f_cf)
            catcher_frames.append(f_catcher)

            # HUD overlay for main broadcast MP4
            frame = f_dugout.copy()
            b_z = step_info["batter_pelvis_z"]
            c_z = step_info["catcher_pelvis_z"]

            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (640, 75), (20, 20, 20), -1)
            cv2.rectangle(overlay, (0, 415), (640, 480), (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

            ptype = step_info["pitch_type"]
            pspd = step_info["pitch_speed_kmh"]
            pz = step_info["plate_cross_z"]

            cv2.putText(frame, "ATHLETIC DUEL: 10M PITCHER & DEEP-KNEE BATTER", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            t_cur = (step * 0.02)
            p_text = f"Time: {t_cur:.2f}s | {ptype} ({pspd:.1f} km/h) | Plate Z: {pz:.2f}m"
            cv2.putText(frame, p_text, (15, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)

            b_status = f"BATTER: Athletic Stance (Z={b_z:.2f}m)"
            if step_info["is_hit"]:
                b_status += f" | CRACK! Exit: {step_info['exit_velocity_kmh']:.1f} km/h"
            elif step_info["batter_fallen"]:
                b_status += " | FALLEN"
            else:
                b_status += " | Ready"

            cv2.putText(frame, b_status, (15, 442), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 2)

            c_status = f"CATCHER: Rock-Solid Squat (Z={c_z:.2f}m)"
            if step_info["catcher_caught"]:
                c_status += " | CAUGHT IN MITT!"
            cv2.putText(frame, c_status, (15, 468), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 200) if step_info["is_hit"] or step_info["catcher_caught"] else (200, 200, 200), 1)

            video_frames.append(frame)

            if step == 2:
                capture_frames["release"] = frame.copy()
            elif step == 12:
                capture_frames["approach"] = frame.copy()
            elif step_info["is_hit"] and "impact" not in capture_frames:
                capture_frames["impact"] = frame.copy()
            elif step_info["is_hit"] and step == (env.contact_step + 6) and "follow_through" not in capture_frames:
                capture_frames["follow_through"] = frame.copy()

            done = terminated or truncated

        if "impact" not in capture_frames and len(video_frames) > 20:
            capture_frames["impact"] = video_frames[20].copy()
        if "follow_through" not in capture_frames and len(video_frames) > 25:
            capture_frames["follow_through"] = video_frames[-1].copy()

        # 1. Save 50 FPS MP4 video
        vid_path = "logs/videos/athletic_duel.mp4"
        h, w, _ = video_frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(vid_path, fourcc, 50, (w, h))
        for vf in video_frames:
            writer.write(cv2.cvtColor(vf, cv2.COLOR_RGB2BGR))
        writer.release()
        print(f"Saved 50 FPS video to {vid_path}")

        # 2. Save Keyframe PNGs
        keyframe_names = [
            ("release", "athletic_pitch_release.png"),
            ("approach", "athletic_pitch_approach.png"),
            ("impact", "athletic_bat_impact.png"),
            ("follow_through", "athletic_follow_through.png")
        ]
        for k, name in keyframe_names:
            if k in capture_frames:
                out_p = f"logs/videos/{name}"
                cv2.imwrite(out_p, cv2.cvtColor(capture_frames[k], cv2.COLOR_RGB2BGR))
                print(f"Saved keyframe: {out_p}")
                shutil.copy(out_p, os.path.join(ARTIFACTS_DIR, name))

        # 3. Generate the 3 Animated GIFs (Downsampled to 25 FPS for web efficiency)
        gifs = [
            ("cf_broadcast.gif", cf_frames),
            ("dugout_dual.gif", dugout_frames),
            ("catcher_framing_catch.gif", catcher_frames)
        ]
        for gif_name, f_list in gifs:
            if len(f_list) > 0:
                out_gif = os.path.join("logs/videos", gif_name)
                # Subsample by 2 for smooth 25 FPS GIF
                sub_frames = f_list[::2]
                imageio.mimsave(out_gif, sub_frames, fps=25, loop=0)
                print(f"Saved animated GIF: {out_gif} ({len(sub_frames)} frames)")
                shutil.copy(out_gif, os.path.join(ARTIFACTS_DIR, gif_name))

        # Copy mp4 and metrics csv to artifact directory as well
        shutil.copy(vid_path, os.path.join(ARTIFACTS_DIR, "athletic_duel.mp4"))
        shutil.copy(csv_path, os.path.join(ARTIFACTS_DIR, "athletic_duel_metrics.csv"))
        print(f"Copied all video/gif artifacts to {ARTIFACTS_DIR}")

    env.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=50)
    args = parser.parse_args()
    evaluate(episodes=args.episodes)
