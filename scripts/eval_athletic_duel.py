import os
import sys
sys.path.append(os.path.abspath("."))

import argparse
import csv
import numpy as np
import cv2
from stable_baselines3 import PPO
from envs.athletic_duel_env import AthleticDuelEnv

def evaluate(episodes=50, render_video=True):
    os.makedirs("logs/videos", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

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
    video_frames = []
    capture_frames = {}

    print(f"\n--- Starting Athletic Duel Benchmark: {episodes} Episodes ---")
    for ep in range(episodes):
        obs, info = env.reset(seed=ep * 100 + 42)
        done = False
        ep_reward = 0.0
        step = 0

        while not done:
            if model is not None:
                action, _ = model.predict(obs, deterministic=True)
            else:
                action = np.zeros(6, dtype=np.float32)

            obs, reward, terminated, truncated, step_info = env.step(action)
            ep_reward += reward
            step += 1

            if render_video and ep == 0:
                frame = env.render()
                ball_pos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
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

                c_status = f"CATCHER: Squat (Z={c_z:.2f}m)"
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
                elif step_info["is_hit"] and step == (env.contact_step + 5) and "follow_through" not in capture_frames:
                    capture_frames["follow_through"] = frame.copy()

            done = terminated or truncated

        if render_video and ep == 0:
            if "impact" not in capture_frames and len(video_frames) > 20:
                capture_frames["impact"] = video_frames[20].copy()
            if "follow_through" not in capture_frames and len(video_frames) > 25:
                capture_frames["follow_through"] = video_frames[-1].copy()

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
            "ep_reward": float(ep_reward)
        })

    env.close()

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

    print("=" * 60)
    print("--- 50-EPISODE ATHLETIC DUEL BENCHMARK SUMMARY ---")
    print(f"Total Episodes:                {n_total}")
    print(f"Batter Balance Survival Rate:  {b_surv:.1f}% ({sum(not r['batter_fallen'] for r in records)}/{n_total})")
    print(f"Catcher Squat Survival Rate:   {c_surv:.1f}% ({sum(not r['catcher_fallen'] for r in records)}/{n_total})")
    print(f"Bat Contact Rate:              {hits:.1f}% ({sum(r['is_hit'] for r in records)}/{n_total})")
    print(f"Fair-Hit Rate:                 {fairs:.1f}% ({sum(r['is_fair'] for r in records)}/{n_total})")
    print(f"Strike Zone Adherence Rate:    {strikes:.1f}% ({sum(r['is_strike'] for r in records)}/{n_total})")
    print(f"Catcher Catch on Taken Pitches:{catch_rate:.1f}% ({caught}/{unhit})")
    print(f"Mean Sweet Spot Error MAE:     {mean_sw_err:.2f} cm")
    print(f"Mean Exit Velocity:            {mean_exit_v:.1f} km/h")
    print("=" * 60)

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

    if render_video and len(video_frames) > 0:
        vid_path = "logs/videos/athletic_duel.mp4"
        h, w, _ = video_frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(vid_path, fourcc, 50, (w, h))
        for vf in video_frames:
            writer.write(cv2.cvtColor(vf, cv2.COLOR_RGB2BGR))
        writer.release()
        print(f"\nSaved 50 FPS video to {vid_path}")

        for k, name in [("release", "athletic_pitch_release.png"),
                        ("approach", "athletic_pitch_approach.png"),
                        ("impact", "athletic_bat_impact.png"),
                        ("follow_through", "athletic_follow_through.png")]:
            if k in capture_frames:
                out_p = f"logs/videos/{name}"
                cv2.imwrite(out_p, cv2.cvtColor(capture_frames[k], cv2.COLOR_RGB2BGR))
                print(f"Saved keyframe: {out_p}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=50)
    args = parser.parse_args()
    evaluate(episodes=args.episodes)
