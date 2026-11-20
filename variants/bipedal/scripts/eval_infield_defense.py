"""
Evaluation and Video Rendering Script for Phase 7: Full Infield Bipedal Defense & 1st Base Out/Safe Play.
Evaluates 50 benchmark episodes across:
- Strike Rate
- Contact Success Rate (Target >= 80%)
- Forward Fair-Hit Rate (Target >= 60%)
- Batter Balance Survival Rate (Target 100%)
- Fielder Balance Survival Rate (Target 100%)
- Fielder Intercept Rate (Target ~50-60%)
- 3D Umpire Calls (OUT vs SAFE)
- Mean Batted Ball Exit Velocity (Target 32 - 48 km/h)
- Mean Runner Sprint Velocity (Target 20 - 25 km/h)

Renders 50 FPS broadcast video with comprehensive TV-style HUD overlay and extracts 4 keyframe artifacts.
"""

import os
import sys
import argparse
import shutil
import numpy as np
import cv2
import imageio

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from stable_baselines3 import PPO
from envs.infield_defense_env import InfieldDefenseEnv


def draw_hud(frame, step, current_time, pitch_name, contact, fair_hit, released, fielded, def_comp, runner_reached, decision, b_fall, f_fall, rz, fz, exit_spd, run_spd, t_defense, t_runner):
    h, w, _ = frame.shape
    overlay = frame.copy()

    # Top Header HUD background
    cv2.rectangle(overlay, (15, 12), (w - 15, 115), (15, 18, 24), -1)
    # Bottom Telemetry HUD background
    cv2.rectangle(overlay, (15, h - 85), (w - 15, h - 12), (15, 18, 24), -1)
    cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)

    # Header Title
    title = "PHASE 7: FULL INFIELD BIPEDAL DEFENSE & 1ST BASE OUT/SAFE PLAY"
    cv2.putText(frame, title, (28, 40), cv2.FONT_HERSHEY_DUPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)

    # Pitch & Stage Info
    if current_time < 0.52:
        stage_str = f"STAGE 1: PITCH & SWING ({pitch_name})"
        stage_col = (0, 220, 255)
    elif current_time < 0.65:
        stage_str = "STAGE 2: BAT DROP PROP HANDOVER"
        stage_col = (0, 165, 255)
    elif current_time < 1.45:
        stage_str = "STAGE 3: BIPEDAL SPRINT VS INFIELD FIELDING"
        stage_col = (50, 255, 120)
    else:
        stage_str = "STAGE 4: 1ST BASE RACE & 3D UMPIRE DECISION"
        stage_col = (255, 200, 50)

    cv2.putText(frame, f"Time: {current_time:.2f}s (Step {step:2d}/100) | {stage_str}", (28, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (220, 235, 255), 1, cv2.LINE_AA)

    # Ball / Play Status
    if contact:
        hit_str = f"HIT: FAIR GROUND/LINER (Exit {exit_spd:.1f} km/h)"
        hit_col = (50, 255, 100)
    else:
        hit_str = f"PITCH: {pitch_name.upper()} IN-FLIGHT"
        hit_col = (200, 200, 200)
    cv2.putText(frame, hit_str, (28, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.48, hit_col, 1, cv2.LINE_AA)

    field_str = "DEFENSE: BALL FIELDED IN GLOVE" if fielded else "DEFENSE: PURSUING BALL"
    field_col = (0, 215, 255) if fielded else (180, 180, 180)
    cv2.putText(frame, field_str, (420, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.48, field_col, 1, cv2.LINE_AA)

    # Umpire Call Badge (Prominent Right Corner)
    dec_col = (50, 255, 100) if decision == "SAFE" else ((0, 60, 255) if decision == "OUT" else (180, 180, 180))
    cv2.rectangle(frame, (w - 220, 48), (w - 28, 105), (30, 35, 45), -1)
    cv2.rectangle(frame, (w - 220, 48), (w - 28, 105), dec_col, 2)
    cv2.putText(frame, "UMPIRE CALL", (w - 200, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(frame, decision, (w - 185, 96), cv2.FONT_HERSHEY_DUPLEX, 0.85, dec_col, 2, cv2.LINE_AA)

    # Footer HUD Telemetry
    # Line 1: Balance Survival for both Humanoids
    b_stat = "RUNNER: 100% BALANCED" if not b_fall else "RUNNER: FALLEN"
    f_stat = "FIELDER: 100% BALANCED" if not f_fall else "FIELDER: FALLEN"
    b_c = (50, 255, 100) if not b_fall else (0, 50, 255)
    f_c = (50, 255, 100) if not f_fall else (0, 50, 255)

    cv2.putText(frame, f"{b_stat} (Z={rz:.2f}m)  |  {f_stat} (Z={fz:.2f}m)", (28, h - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (240, 240, 255), 1, cv2.LINE_AA)

    # Line 2: Race Telemetry T_runner vs T_defense
    t_def_str = f"{t_defense:.2f}s" if t_defense < 900.0 else "--"
    t_run_str = f"{t_runner:.2f}s" if t_runner < 900.0 else "--"
    race_str = f"Runner Sprint: {run_spd:.1f} km/h (T_1B={t_run_str}) | Defense Catch/Touch: T_def={t_def_str}"
    cv2.putText(frame, race_str, (28, h - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 230, 255), 1, cv2.LINE_AA)

    return frame


def evaluate(
    checkpoint_path=None,
    n_episodes=50,
    render_video=True,
    video_path="logs/videos/phase7_infield_defense.mp4",
    artifact_dir=None,
):
    os.makedirs("logs/videos", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    env = InfieldDefenseEnv(render_mode="rgb_array")

    model = None
    if checkpoint_path and os.path.exists(checkpoint_path):
        print(f"Loading trained policy checkpoint: {checkpoint_path}")
        model = PPO.load(checkpoint_path)
    else:
        # Check default locations
        default_best = os.path.join("checkpoints", "best_phase7_infield_defense_model.zip")
        if os.path.exists(default_best):
            print(f"Loading default best checkpoint: {default_best}")
            model = PPO.load(default_best)
        else:
            print("No checkpoint provided or found; evaluating baseline controller.")

    print("=" * 65)
    print("      PHASE 7 BENCHMARK EVALUATION (50 EPISODES)       ")
    print("=" * 65)

    ep_records = []
    video_frames = []
    best_candidate_frames = []
    best_ep_score = -999.0
    keyframe_candidates = {}

    csv_path = os.path.join("logs", "phase7_benchmark_metrics.csv")
    csv_header = "episode,pitch_type,pitch_name,pitch_speed_kmh,contact,fair_hit,fielded,def_completed,runner_reached_1b,umpire_call,exit_velocity_kmh,runner_speed_kmh,batter_pelvis_z,fielder_pelvis_z,t_defense,t_runner,batter_fallen,fielder_fallen\n"

    with open(csv_path, "w") as f:
        f.write(csv_header)

    for ep in range(n_episodes):
        obs, info = env.reset(seed=60000 + ep)
        done = False
        step = 0
        ep_frames = []
        cur_ep_keyframes = {}

        while not done:
            if model is not None:
                action, _ = model.predict(obs, deterministic=True)
            else:
                action = np.zeros(8, dtype=np.float32)

            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            step += 1
            current_time = env.current_step * env.dt

            if render_video:
                frame = env.render()
                if frame is not None:
                    annotated = draw_hud(
                        frame.copy(),
                        step=env.current_step,
                        current_time=current_time,
                        pitch_name=env.pitch_name,
                        contact=info["contact"],
                        fair_hit=info["fair_hit"],
                        released=info["bat_released"],
                        fielded=info["ball_fielded"],
                        def_comp=info["defense_completed"],
                        runner_reached=info["runner_reached_1b"],
                        decision=info["umpire_decision"],
                        b_fall=info["batter_fallen"],
                        f_fall=info["fielder_fallen"],
                        rz=info["runner_pelvis_z"],
                        fz=info["fielder_pelvis_z"],
                        exit_spd=info["exit_speed_kmh"],
                        run_spd=info["runner_speed_kmh"],
                        t_defense=info["t_defense"],
                        t_runner=info["t_runner"],
                    )
                    ep_frames.append(annotated)

                    # Capture Keyframe candidates
                    # 1. Pitch & Swing (t ~ 0.42 - 0.48s)
                    if 0.42 <= current_time <= 0.48 and "pitch_and_swing" not in cur_ep_keyframes:
                        cur_ep_keyframes["pitch_and_swing"] = annotated.copy()
                    # 2. Bat Drop & Sprint Launch (t ~ 0.54 - 0.64s)
                    if 0.54 <= current_time <= 0.64 and "bat_drop_and_sprint" not in cur_ep_keyframes:
                        cur_ep_keyframes["bat_drop_and_sprint"] = annotated.copy()
                    # 3. Fielder Intercept Scoop (t ~ 0.90 - 1.25s)
                    if 0.90 <= current_time <= 1.25 and "fielder_intercept" not in cur_ep_keyframes and (info["ball_fielded"] or current_time >= 1.05):
                        cur_ep_keyframes["fielder_intercept"] = annotated.copy()
                    # 4. 1st Base Umpire Call (t >= 1.45s)
                    if current_time >= 1.45 and "umpire_call" not in cur_ep_keyframes and info["umpire_decision"] in ["OUT", "SAFE"]:
                        cur_ep_keyframes["umpire_call"] = annotated.copy()

        # Fallback to ensure umpire_call is captured if decided
        if "umpire_call" not in cur_ep_keyframes and ep_frames and info["umpire_decision"] in ["OUT", "SAFE"]:
            cur_ep_keyframes["umpire_call"] = ep_frames[-1].copy()

        rec = {
            "ep": ep,
            "pitch_type": env.pitch_type,
            "pitch_name": env.pitch_name,
            "pitch_speed_kmh": info["pitch_speed_kmh"],
            "contact": info["contact"],
            "fair": info["fair_hit"],
            "fielded": info["ball_fielded"],
            "def_comp": info["defense_completed"],
            "runner_reached": info["runner_reached_1b"],
            "decision": info["umpire_decision"],
            "exit_kmh": info["exit_speed_kmh"],
            "run_kmh": info["runner_speed_kmh"],
            "rz": info["runner_pelvis_z"],
            "fz": info["fielder_pelvis_z"],
            "t_def": info["t_defense"],
            "t_run": info["t_runner"],
            "b_fall": info["batter_fallen"],
            "f_fall": info["fielder_fallen"],
        }
        ep_records.append(rec)

        with open(csv_path, "a") as f:
            f.write(
                f"{ep},{rec['pitch_type']},{rec['pitch_name']},{rec['pitch_speed_kmh']:.2f},"
                f"{rec['contact']},{rec['fair']},{rec['fielded']},{rec['def_comp']},{rec['runner_reached']},"
                f"{rec['decision']},{rec['exit_kmh']:.2f},{rec['run_kmh']:.2f},{rec['rz']:.3f},{rec['fz']:.3f},"
                f"{rec['t_def']:.3f},{rec['t_run']:.3f},{rec['b_fall']},{rec['f_fall']}\n"
            )

        # Select representative episode for full video rendering
        ep_score = (2.0 if rec["contact"] else 0.0) + (2.0 if rec["fair"] else 0.0) + (3.0 if rec["fielded"] else 0.0)
        if ep_score > best_ep_score and len(cur_ep_keyframes) >= 3:
            best_ep_score = ep_score
            best_candidate_frames = ep_frames
            keyframe_candidates = cur_ep_keyframes

    # Aggregate Benchmark Metrics
    n = len(ep_records)
    n_strikes = sum(1 for r in ep_records if not r["contact"])
    n_contacts = sum(1 for r in ep_records if r["contact"])
    n_fairs = sum(1 for r in ep_records if r["fair"])
    b_survived = sum(1 for r in ep_records if not r["b_fall"])
    f_survived = sum(1 for r in ep_records if not r["f_fall"])
    n_fielded = sum(1 for r in ep_records if r["fielded"])
    n_outs = sum(1 for r in ep_records if r["decision"] == "OUT")
    n_safes = sum(1 for r in ep_records if r["decision"] == "SAFE")

    mean_exit = float(np.mean([r["exit_kmh"] for r in ep_records if r["contact"]])) if n_contacts > 0 else 0.0
    mean_run = float(np.mean([r["run_kmh"] for r in ep_records]))

    print("\n" + "=" * 65)
    print("               PHASE 7 BENCHMARK REPORT                ")
    print("=" * 65)
    print(f"Total Benchmark Episodes : {n}")
    print(f"Strike Rate              : {n_strikes/n*100:.1f}% ({n_strikes}/{n})")
    print(f"Contact Rate             : {n_contacts/n*100:.1f}% ({n_contacts}/{n}) [Target >= 80%]")
    print(f"Forward Fair-Hit Rate    : {n_fairs/n*100:.1f}% ({n_fairs}/{n}) [Target >= 60%]")
    print(f"Batter Balance Survival  : {b_survived/n*100:.1f}% ({b_survived}/{n}) [Target 100%]")
    print(f"Fielder Balance Survival : {f_survived/n*100:.1f}% ({f_survived}/{n}) [Target 100%]")
    print(f"Fielder Intercept Rate   : {n_fielded/n*100:.1f}% ({n_fielded}/{n}) [Target ~50-60%]")
    print(f"OUT Decision Rate        : {n_outs/n*100:.1f}% ({n_outs}/{n})")
    print(f"SAFE Decision Rate       : {n_safes/n*100:.1f}% ({n_safes}/{n})")
    print(f"Mean Exit Velocity       : {mean_exit:.1f} km/h (32 - 48 km/h target)")
    print(f"Mean Runner Sprint Speed : {mean_run:.1f} km/h (20 - 25 km/h target)")
    print("=" * 65)

    # Save Video
    if render_video and best_candidate_frames:
        print(f"\nWriting 50 FPS broadcast video to: {video_path}")
        imageio.mimwrite(video_path, best_candidate_frames, fps=50, quality=9)
        print(f"Video saved successfully ({len(best_candidate_frames)} frames).")

    # Save Keyframe Artifacts
    keyframe_names = [
        ("pitch_and_swing", "phase7_pitch_and_swing.png"),
        ("bat_drop_and_sprint", "phase7_bat_drop_and_sprint.png"),
        ("fielder_intercept", "phase7_fielder_intercept.png"),
        ("umpire_call", "phase7_umpire_call.png"),
    ]

    saved_artifacts = []
    for k_key, filename in keyframe_names:
        img = keyframe_candidates.get(k_key)
        if img is not None:
            local_path = os.path.join("logs", filename)
            cv2.imwrite(local_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            saved_artifacts.append(local_path)
            print(f"Saved keyframe artifact: {local_path}")

            if artifact_dir and os.path.exists(artifact_dir):
                dest_path = os.path.join(artifact_dir, filename)
                shutil.copyfile(local_path, dest_path)
                print(f"Copied to session artifact directory: {dest_path}")

            cur_media_dir = "/Users/jin10000/.gemini/antigravity/brain/4b45c499-400c-4ec2-b810-7e844a40041f/.tempmediaStorage"
            if os.path.exists(cur_media_dir):
                media_dest = os.path.join(cur_media_dir, filename)
                shutil.copyfile(local_path, media_dest)
                print(f"Copied to media artifact directory: {media_dest}")

    env.close()
    return rec


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Phase 7 Infield Defense")
    parser.add_argument("--episodes", type=int, default=50, help="Number of evaluation episodes")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/best_phase7_infield_defense_model.zip")
    parser.add_argument("--artifact-dir", type=str, default="/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7")
    args = parser.parse_args()

    evaluate(
        checkpoint_path=args.checkpoint,
        n_episodes=args.episodes,
        artifact_dir=args.artifact_dir,
    )
