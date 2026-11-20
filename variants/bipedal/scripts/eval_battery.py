import os
import sys
sys.path.append(os.path.abspath("."))

import argparse
import csv
import numpy as np
import cv2
from stable_baselines3 import PPO
from envs.battery_pitch_catch_env import BatteryPitchCatchEnv

def evaluate(episodes=50, render_video=True):
    os.makedirs("logs/videos", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    env = BatteryPitchCatchEnv(render_mode="rgb_array")

    model_path = "checkpoints/best_battery_model.zip"
    if not os.path.exists(model_path):
        model_path = "checkpoints/final_battery_model.zip"

    model = None
    if os.path.exists(model_path):
        print(f"Loading trained policy from {model_path}...")
        model = PPO.load(model_path, env=env)
    else:
        print("Model checkpoint not found, running with zero action baseline.")

    records = []
    video_frames = []
    capture_frames = {}

    print(f"\n--- Starting Battery Benchmark: {episodes} Episodes ---")
    for ep in range(episodes):
        obs, info = env.reset(seed=ep * 100 + 42)
        done = False
        ep_reward = 0.0
        step = 0

        while not done:
            if model is not None:
                action, _ = model.predict(obs, deterministic=True)
            else:
                action = np.zeros(5, dtype=np.float32)

            obs, reward, terminated, truncated, step_info = env.step(action)
            ep_reward += reward
            step += 1

            if render_video and ep == 0:
                frame = env.render()
                ball_pos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
                mitt_pos = env.data.site_xpos[env.c_mitt_site_id]
                dist_mitt = float(np.linalg.norm(ball_pos - mitt_pos))
                c_z = float(env.data.qpos[env.c_pelvis_qpos_adr + 2])

                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (640, 75), (20, 20, 20), -1)
                cv2.rectangle(overlay, (0, 415), (640, 480), (20, 20, 20), -1)
                cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

                ptype = step_info["pitch_type"]
                pspd = step_info["pitch_speed_kmh"]
                pz = step_info["plate_cross_z"]
                perr = step_info["framing_error_cm"]

                cv2.putText(frame, "BATTERY DUEL: 10M PITCHER & 6-DoF CATCHER SQUAT", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
                t_cur = (step * 0.02)
                p_text = f"Time: {t_cur:.2f}s | {ptype} ({pspd:.1f} km/h) | Plate Z: {pz:.2f}m"
                cv2.putText(frame, p_text, (15, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)

                c_status = "STABLE SQUAT" if not step_info["catcher_fallen"] else "FALLEN"
                b_status = "CAUGHT IN MITT!" if step_info["ball_caught"] else f"In-Flight (Mitt Dist: {dist_mitt*100:.1f}cm)"
                call_text = "CALL: STRIKE" if step_info["is_strike"] else "CALL: BALL"
                cv2.putText(frame, f"CATCHER: {c_status} (Z={c_z:.2f}m) | {call_text}", (15, 442), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 2)
                res_col = (0, 255, 200) if step_info["ball_caught"] else (200, 200, 200)
                cv2.putText(frame, f"RESULT: {b_status} | Framing Err: {perr:.1f}cm", (15, 468), cv2.FONT_HERSHEY_SIMPLEX, 0.44, res_col, 1)

                video_frames.append(frame)

                if step == 2:
                    capture_frames["release"] = frame.copy()
                elif step == 12:
                    capture_frames["approach"] = frame.copy()
                elif step_info["ball_caught"] and "catch" not in capture_frames:
                    capture_frames["catch"] = frame.copy()

            done = terminated or truncated

        if render_video and ep == 0 and "catch" not in capture_frames and len(video_frames) > 0:
            capture_frames["catch"] = video_frames[-1].copy()

        records.append({
            "episode": ep + 1,
            "pitch_type": step_info["pitch_type"],
            "pitch_speed_kmh": float(step_info["pitch_speed_kmh"]),
            "ball_caught": bool(step_info["ball_caught"]),
            "is_strike": bool(step_info["is_strike"]),
            "framing_error_cm": float(step_info["framing_error_cm"]),
            "catcher_fallen": bool(step_info["catcher_fallen"]),
            "catcher_pelvis_z": float(step_info["catcher_pelvis_z"]),
            "plate_cross_x": float(step_info["plate_cross_x"]),
            "plate_cross_z": float(step_info["plate_cross_z"]),
            "ep_reward": float(ep_reward)
        })

    csv_path = "logs/battery_benchmark_metrics.csv"
    keys = records[0].keys()
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)
    print(f"\nSaved benchmark metrics to {csv_path}")

    total_eps = len(records)
    falls = sum(1 for r in records if r["catcher_fallen"])
    catches = sum(1 for r in records if r["ball_caught"])
    strikes = sum(1 for r in records if r["is_strike"])
    survival_rate = (1.0 - falls / total_eps) * 100.0
    catch_rate = (catches / total_eps) * 100.0
    strike_rate = (strikes / total_eps) * 100.0
    mean_framing_err = np.mean([r["framing_error_cm"] for r in records if r["ball_caught"]]) if catches > 0 else np.mean([r["framing_error_cm"] for r in records])
    mean_speed = np.mean([r["pitch_speed_kmh"] for r in records])
    mean_z = np.mean([r["catcher_pelvis_z"] for r in records])

    print("=" * 60)
    print("--- 50-EPISODE BATTERY BENCHMARK SUMMARY ---")
    print(f"Total Episodes:                {total_eps}")
    print(f"Catcher Squat Survival Rate:   {survival_rate:.1f}% ({total_eps - falls}/{total_eps})")
    print(f"Ball Catch Success Rate:       {catch_rate:.1f}% ({catches}/{total_eps})")
    print(f"Strike Zone Adherence Rate:    {strike_rate:.1f}% ({strikes}/{total_eps})")
    print(f"Mean Framing Error MAE:        {mean_framing_err:.2f} cm")
    print(f"Mean Pitch Speed:              {mean_speed:.1f} km/h")
    print(f"Mean Catcher Squat Pelvis Z:   {mean_z:.3f} m")
    print("=" * 60)

    # Breakdown by pitch type
    for ptype in ["Fastball", "Slider", "Curveball"]:
        p_recs = [r for r in records if r["pitch_type"] == ptype]
        if len(p_recs) > 0:
            p_cat = sum(1 for r in p_recs if r["ball_caught"]) / len(p_recs) * 100.0
            p_str = sum(1 for r in p_recs if r["is_strike"]) / len(p_recs) * 100.0
            p_sp = np.mean([r["pitch_speed_kmh"] for r in p_recs])
            p_er = np.mean([r["framing_error_cm"] for r in p_recs])
            print(f"[{ptype:>9}] Count: {len(p_recs):2d} | Catch: {p_cat:5.1f}% | Strike: {p_str:5.1f}% | Spd: {p_sp:4.1f} km/h | Err: {p_er:4.1f} cm")

    if render_video and len(video_frames) > 0:
        vid_path = "logs/videos/battery_pitch_catch.mp4"
        h, w, _ = video_frames[0].shape
        out = cv2.VideoWriter(vid_path, cv2.VideoWriter_fourcc(*"mp4v"), 50, (w, h))
        for f in video_frames:
            out.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
        out.release()
        print(f"\nSaved 50 FPS video to {vid_path}")

    keyframe_map = {
        "release": "logs/videos/battery_pitch_release.png",
        "approach": "logs/videos/battery_pitch_approach.png",
        "catch": "logs/videos/battery_mitt_catch.png"
    }
    for k, path in keyframe_map.items():
        if k in capture_frames:
            cv2.imwrite(path, cv2.cvtColor(capture_frames[k], cv2.COLOR_RGB2BGR))
            print(f"Saved keyframe: {path}")

    env.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=50)
    args = parser.parse_args()
    evaluate(episodes=args.episodes)
