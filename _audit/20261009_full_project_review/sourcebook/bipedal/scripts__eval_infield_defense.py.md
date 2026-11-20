# bipedal/scripts/eval_infield_defense.py

원본: [scripts/eval_infield_defense.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/eval_infield_defense.py)

SHA256: `7b7da00502d50a0e1135033fc1d73ef64b8f7e085bbfb4c782465a0e1ab4cbcc`

전체 320행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `draw_hud` | FunctionDef | 33 | 98 |
| `evaluate` | FunctionDef | 101 | 306 |

## 전체 원문

````text
    1 | """
    2 | Evaluation and Video Rendering Script for Phase 7: Full Infield Bipedal Defense & 1st Base Out/Safe Play.
    3 | Evaluates 50 benchmark episodes across:
    4 | - Strike Rate
    5 | - Contact Success Rate (Target >= 80%)
    6 | - Forward Fair-Hit Rate (Target >= 60%)
    7 | - Batter Balance Survival Rate (Target 100%)
    8 | - Fielder Balance Survival Rate (Target 100%)
    9 | - Fielder Intercept Rate (Target ~50-60%)
   10 | - 3D Umpire Calls (OUT vs SAFE)
   11 | - Mean Batted Ball Exit Velocity (Target 32 - 48 km/h)
   12 | - Mean Runner Sprint Velocity (Target 20 - 25 km/h)
   13 | 
   14 | Renders 50 FPS broadcast video with comprehensive TV-style HUD overlay and extracts 4 keyframe artifacts.
   15 | """
   16 | 
   17 | import os
   18 | import sys
   19 | import argparse
   20 | import shutil
   21 | import numpy as np
   22 | import cv2
   23 | import imageio
   24 | 
   25 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   26 | if BASE_DIR not in sys.path:
   27 |     sys.path.insert(0, BASE_DIR)
   28 | 
   29 | from stable_baselines3 import PPO
   30 | from envs.infield_defense_env import InfieldDefenseEnv
   31 | 
   32 | 
   33 | def draw_hud(frame, step, current_time, pitch_name, contact, fair_hit, released, fielded, def_comp, runner_reached, decision, b_fall, f_fall, rz, fz, exit_spd, run_spd, t_defense, t_runner):
   34 |     h, w, _ = frame.shape
   35 |     overlay = frame.copy()
   36 | 
   37 |     # Top Header HUD background
   38 |     cv2.rectangle(overlay, (15, 12), (w - 15, 115), (15, 18, 24), -1)
   39 |     # Bottom Telemetry HUD background
   40 |     cv2.rectangle(overlay, (15, h - 85), (w - 15, h - 12), (15, 18, 24), -1)
   41 |     cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)
   42 | 
   43 |     # Header Title
   44 |     title = "PHASE 7: FULL INFIELD BIPEDAL DEFENSE & 1ST BASE OUT/SAFE PLAY"
   45 |     cv2.putText(frame, title, (28, 40), cv2.FONT_HERSHEY_DUPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
   46 | 
   47 |     # Pitch & Stage Info
   48 |     if current_time < 0.52:
   49 |         stage_str = f"STAGE 1: PITCH & SWING ({pitch_name})"
   50 |         stage_col = (0, 220, 255)
   51 |     elif current_time < 0.65:
   52 |         stage_str = "STAGE 2: BAT DROP PROP HANDOVER"
   53 |         stage_col = (0, 165, 255)
   54 |     elif current_time < 1.45:
   55 |         stage_str = "STAGE 3: BIPEDAL SPRINT VS INFIELD FIELDING"
   56 |         stage_col = (50, 255, 120)
   57 |     else:
   58 |         stage_str = "STAGE 4: 1ST BASE RACE & 3D UMPIRE DECISION"
   59 |         stage_col = (255, 200, 50)
   60 | 
   61 |     cv2.putText(frame, f"Time: {current_time:.2f}s (Step {step:2d}/100) | {stage_str}", (28, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (220, 235, 255), 1, cv2.LINE_AA)
   62 | 
   63 |     # Ball / Play Status
   64 |     if contact:
   65 |         hit_str = f"HIT: FAIR GROUND/LINER (Exit {exit_spd:.1f} km/h)"
   66 |         hit_col = (50, 255, 100)
   67 |     else:
   68 |         hit_str = f"PITCH: {pitch_name.upper()} IN-FLIGHT"
   69 |         hit_col = (200, 200, 200)
   70 |     cv2.putText(frame, hit_str, (28, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.48, hit_col, 1, cv2.LINE_AA)
   71 | 
   72 |     field_str = "DEFENSE: BALL FIELDED IN GLOVE" if fielded else "DEFENSE: PURSUING BALL"
   73 |     field_col = (0, 215, 255) if fielded else (180, 180, 180)
   74 |     cv2.putText(frame, field_str, (420, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.48, field_col, 1, cv2.LINE_AA)
   75 | 
   76 |     # Umpire Call Badge (Prominent Right Corner)
   77 |     dec_col = (50, 255, 100) if decision == "SAFE" else ((0, 60, 255) if decision == "OUT" else (180, 180, 180))
   78 |     cv2.rectangle(frame, (w - 220, 48), (w - 28, 105), (30, 35, 45), -1)
   79 |     cv2.rectangle(frame, (w - 220, 48), (w - 28, 105), dec_col, 2)
   80 |     cv2.putText(frame, "UMPIRE CALL", (w - 200, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1, cv2.LINE_AA)
   81 |     cv2.putText(frame, decision, (w - 185, 96), cv2.FONT_HERSHEY_DUPLEX, 0.85, dec_col, 2, cv2.LINE_AA)
   82 | 
   83 |     # Footer HUD Telemetry
   84 |     # Line 1: Balance Survival for both Humanoids
   85 |     b_stat = "RUNNER: 100% BALANCED" if not b_fall else "RUNNER: FALLEN"
   86 |     f_stat = "FIELDER: 100% BALANCED" if not f_fall else "FIELDER: FALLEN"
   87 |     b_c = (50, 255, 100) if not b_fall else (0, 50, 255)
   88 |     f_c = (50, 255, 100) if not f_fall else (0, 50, 255)
   89 | 
   90 |     cv2.putText(frame, f"{b_stat} (Z={rz:.2f}m)  |  {f_stat} (Z={fz:.2f}m)", (28, h - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (240, 240, 255), 1, cv2.LINE_AA)
   91 | 
   92 |     # Line 2: Race Telemetry T_runner vs T_defense
   93 |     t_def_str = f"{t_defense:.2f}s" if t_defense < 900.0 else "--"
   94 |     t_run_str = f"{t_runner:.2f}s" if t_runner < 900.0 else "--"
   95 |     race_str = f"Runner Sprint: {run_spd:.1f} km/h (T_1B={t_run_str}) | Defense Catch/Touch: T_def={t_def_str}"
   96 |     cv2.putText(frame, race_str, (28, h - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 230, 255), 1, cv2.LINE_AA)
   97 | 
   98 |     return frame
   99 | 
  100 | 
  101 | def evaluate(
  102 |     checkpoint_path=None,
  103 |     n_episodes=50,
  104 |     render_video=True,
  105 |     video_path="logs/videos/phase7_infield_defense.mp4",
  106 |     artifact_dir=None,
  107 | ):
  108 |     os.makedirs("logs/videos", exist_ok=True)
  109 |     os.makedirs("logs", exist_ok=True)
  110 | 
  111 |     env = InfieldDefenseEnv(render_mode="rgb_array")
  112 | 
  113 |     model = None
  114 |     if checkpoint_path and os.path.exists(checkpoint_path):
  115 |         print(f"Loading trained policy checkpoint: {checkpoint_path}")
  116 |         model = PPO.load(checkpoint_path)
  117 |     else:
  118 |         # Check default locations
  119 |         default_best = os.path.join("checkpoints", "best_phase7_infield_defense_model.zip")
  120 |         if os.path.exists(default_best):
  121 |             print(f"Loading default best checkpoint: {default_best}")
  122 |             model = PPO.load(default_best)
  123 |         else:
  124 |             print("No checkpoint provided or found; evaluating baseline controller.")
  125 | 
  126 |     print("=" * 65)
  127 |     print("      PHASE 7 BENCHMARK EVALUATION (50 EPISODES)       ")
  128 |     print("=" * 65)
  129 | 
  130 |     ep_records = []
  131 |     video_frames = []
  132 |     best_candidate_frames = []
  133 |     best_ep_score = -999.0
  134 |     keyframe_candidates = {}
  135 | 
  136 |     csv_path = os.path.join("logs", "phase7_benchmark_metrics.csv")
  137 |     csv_header = "episode,pitch_type,pitch_name,pitch_speed_kmh,contact,fair_hit,fielded,def_completed,runner_reached_1b,umpire_call,exit_velocity_kmh,runner_speed_kmh,batter_pelvis_z,fielder_pelvis_z,t_defense,t_runner,batter_fallen,fielder_fallen\n"
  138 | 
  139 |     with open(csv_path, "w") as f:
  140 |         f.write(csv_header)
  141 | 
  142 |     for ep in range(n_episodes):
  143 |         obs, info = env.reset(seed=60000 + ep)
  144 |         done = False
  145 |         step = 0
  146 |         ep_frames = []
  147 |         cur_ep_keyframes = {}
  148 | 
  149 |         while not done:
  150 |             if model is not None:
  151 |                 action, _ = model.predict(obs, deterministic=True)
  152 |             else:
  153 |                 action = np.zeros(8, dtype=np.float32)
  154 | 
  155 |             obs, reward, terminated, truncated, info = env.step(action)
  156 |             done = terminated or truncated
  157 |             step += 1
  158 |             current_time = env.current_step * env.dt
  159 | 
  160 |             if render_video:
  161 |                 frame = env.render()
  162 |                 if frame is not None:
  163 |                     annotated = draw_hud(
  164 |                         frame.copy(),
  165 |                         step=env.current_step,
  166 |                         current_time=current_time,
  167 |                         pitch_name=env.pitch_name,
  168 |                         contact=info["contact"],
  169 |                         fair_hit=info["fair_hit"],
  170 |                         released=info["bat_released"],
  171 |                         fielded=info["ball_fielded"],
  172 |                         def_comp=info["defense_completed"],
  173 |                         runner_reached=info["runner_reached_1b"],
  174 |                         decision=info["umpire_decision"],
  175 |                         b_fall=info["batter_fallen"],
  176 |                         f_fall=info["fielder_fallen"],
  177 |                         rz=info["runner_pelvis_z"],
  178 |                         fz=info["fielder_pelvis_z"],
  179 |                         exit_spd=info["exit_speed_kmh"],
  180 |                         run_spd=info["runner_speed_kmh"],
  181 |                         t_defense=info["t_defense"],
  182 |                         t_runner=info["t_runner"],
  183 |                     )
  184 |                     ep_frames.append(annotated)
  185 | 
  186 |                     # Capture Keyframe candidates
  187 |                     # 1. Pitch & Swing (t ~ 0.42 - 0.48s)
  188 |                     if 0.42 <= current_time <= 0.48 and "pitch_and_swing" not in cur_ep_keyframes:
  189 |                         cur_ep_keyframes["pitch_and_swing"] = annotated.copy()
  190 |                     # 2. Bat Drop & Sprint Launch (t ~ 0.54 - 0.64s)
  191 |                     if 0.54 <= current_time <= 0.64 and "bat_drop_and_sprint" not in cur_ep_keyframes:
  192 |                         cur_ep_keyframes["bat_drop_and_sprint"] = annotated.copy()
  193 |                     # 3. Fielder Intercept Scoop (t ~ 0.90 - 1.25s)
  194 |                     if 0.90 <= current_time <= 1.25 and "fielder_intercept" not in cur_ep_keyframes and (info["ball_fielded"] or current_time >= 1.05):
  195 |                         cur_ep_keyframes["fielder_intercept"] = annotated.copy()
  196 |                     # 4. 1st Base Umpire Call (t >= 1.45s)
  197 |                     if current_time >= 1.45 and "umpire_call" not in cur_ep_keyframes and info["umpire_decision"] in ["OUT", "SAFE"]:
  198 |                         cur_ep_keyframes["umpire_call"] = annotated.copy()
  199 | 
  200 |         # Fallback to ensure umpire_call is captured if decided
  201 |         if "umpire_call" not in cur_ep_keyframes and ep_frames and info["umpire_decision"] in ["OUT", "SAFE"]:
  202 |             cur_ep_keyframes["umpire_call"] = ep_frames[-1].copy()
  203 | 
  204 |         rec = {
  205 |             "ep": ep,
  206 |             "pitch_type": env.pitch_type,
  207 |             "pitch_name": env.pitch_name,
  208 |             "pitch_speed_kmh": info["pitch_speed_kmh"],
  209 |             "contact": info["contact"],
  210 |             "fair": info["fair_hit"],
  211 |             "fielded": info["ball_fielded"],
  212 |             "def_comp": info["defense_completed"],
  213 |             "runner_reached": info["runner_reached_1b"],
  214 |             "decision": info["umpire_decision"],
  215 |             "exit_kmh": info["exit_speed_kmh"],
  216 |             "run_kmh": info["runner_speed_kmh"],
  217 |             "rz": info["runner_pelvis_z"],
  218 |             "fz": info["fielder_pelvis_z"],
  219 |             "t_def": info["t_defense"],
  220 |             "t_run": info["t_runner"],
  221 |             "b_fall": info["batter_fallen"],
  222 |             "f_fall": info["fielder_fallen"],
  223 |         }
  224 |         ep_records.append(rec)
  225 | 
  226 |         with open(csv_path, "a") as f:
  227 |             f.write(
  228 |                 f"{ep},{rec['pitch_type']},{rec['pitch_name']},{rec['pitch_speed_kmh']:.2f},"
  229 |                 f"{rec['contact']},{rec['fair']},{rec['fielded']},{rec['def_comp']},{rec['runner_reached']},"
  230 |                 f"{rec['decision']},{rec['exit_kmh']:.2f},{rec['run_kmh']:.2f},{rec['rz']:.3f},{rec['fz']:.3f},"
  231 |                 f"{rec['t_def']:.3f},{rec['t_run']:.3f},{rec['b_fall']},{rec['f_fall']}\n"
  232 |             )
  233 | 
  234 |         # Select representative episode for full video rendering
  235 |         ep_score = (2.0 if rec["contact"] else 0.0) + (2.0 if rec["fair"] else 0.0) + (3.0 if rec["fielded"] else 0.0)
  236 |         if ep_score > best_ep_score and len(cur_ep_keyframes) >= 3:
  237 |             best_ep_score = ep_score
  238 |             best_candidate_frames = ep_frames
  239 |             keyframe_candidates = cur_ep_keyframes
  240 | 
  241 |     # Aggregate Benchmark Metrics
  242 |     n = len(ep_records)
  243 |     n_strikes = sum(1 for r in ep_records if not r["contact"])
  244 |     n_contacts = sum(1 for r in ep_records if r["contact"])
  245 |     n_fairs = sum(1 for r in ep_records if r["fair"])
  246 |     b_survived = sum(1 for r in ep_records if not r["b_fall"])
  247 |     f_survived = sum(1 for r in ep_records if not r["f_fall"])
  248 |     n_fielded = sum(1 for r in ep_records if r["fielded"])
  249 |     n_outs = sum(1 for r in ep_records if r["decision"] == "OUT")
  250 |     n_safes = sum(1 for r in ep_records if r["decision"] == "SAFE")
  251 | 
  252 |     mean_exit = float(np.mean([r["exit_kmh"] for r in ep_records if r["contact"]])) if n_contacts > 0 else 0.0
  253 |     mean_run = float(np.mean([r["run_kmh"] for r in ep_records]))
  254 | 
  255 |     print("\n" + "=" * 65)
  256 |     print("               PHASE 7 BENCHMARK REPORT                ")
  257 |     print("=" * 65)
  258 |     print(f"Total Benchmark Episodes : {n}")
  259 |     print(f"Strike Rate              : {n_strikes/n*100:.1f}% ({n_strikes}/{n})")
  260 |     print(f"Contact Rate             : {n_contacts/n*100:.1f}% ({n_contacts}/{n}) [Target >= 80%]")
  261 |     print(f"Forward Fair-Hit Rate    : {n_fairs/n*100:.1f}% ({n_fairs}/{n}) [Target >= 60%]")
  262 |     print(f"Batter Balance Survival  : {b_survived/n*100:.1f}% ({b_survived}/{n}) [Target 100%]")
  263 |     print(f"Fielder Balance Survival : {f_survived/n*100:.1f}% ({f_survived}/{n}) [Target 100%]")
  264 |     print(f"Fielder Intercept Rate   : {n_fielded/n*100:.1f}% ({n_fielded}/{n}) [Target ~50-60%]")
  265 |     print(f"OUT Decision Rate        : {n_outs/n*100:.1f}% ({n_outs}/{n})")
  266 |     print(f"SAFE Decision Rate       : {n_safes/n*100:.1f}% ({n_safes}/{n})")
  267 |     print(f"Mean Exit Velocity       : {mean_exit:.1f} km/h (32 - 48 km/h target)")
  268 |     print(f"Mean Runner Sprint Speed : {mean_run:.1f} km/h (20 - 25 km/h target)")
  269 |     print("=" * 65)
  270 | 
  271 |     # Save Video
  272 |     if render_video and best_candidate_frames:
  273 |         print(f"\nWriting 50 FPS broadcast video to: {video_path}")
  274 |         imageio.mimwrite(video_path, best_candidate_frames, fps=50, quality=9)
  275 |         print(f"Video saved successfully ({len(best_candidate_frames)} frames).")
  276 | 
  277 |     # Save Keyframe Artifacts
  278 |     keyframe_names = [
  279 |         ("pitch_and_swing", "phase7_pitch_and_swing.png"),
  280 |         ("bat_drop_and_sprint", "phase7_bat_drop_and_sprint.png"),
  281 |         ("fielder_intercept", "phase7_fielder_intercept.png"),
  282 |         ("umpire_call", "phase7_umpire_call.png"),
  283 |     ]
  284 | 
  285 |     saved_artifacts = []
  286 |     for k_key, filename in keyframe_names:
  287 |         img = keyframe_candidates.get(k_key)
  288 |         if img is not None:
  289 |             local_path = os.path.join("logs", filename)
  290 |             cv2.imwrite(local_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
  291 |             saved_artifacts.append(local_path)
  292 |             print(f"Saved keyframe artifact: {local_path}")
  293 | 
  294 |             if artifact_dir and os.path.exists(artifact_dir):
  295 |                 dest_path = os.path.join(artifact_dir, filename)
  296 |                 shutil.copyfile(local_path, dest_path)
  297 |                 print(f"Copied to session artifact directory: {dest_path}")
  298 | 
  299 |             cur_media_dir = "/Users/jin10000/.gemini/antigravity/brain/4b45c499-400c-4ec2-b810-7e844a40041f/.tempmediaStorage"
  300 |             if os.path.exists(cur_media_dir):
  301 |                 media_dest = os.path.join(cur_media_dir, filename)
  302 |                 shutil.copyfile(local_path, media_dest)
  303 |                 print(f"Copied to media artifact directory: {media_dest}")
  304 | 
  305 |     env.close()
  306 |     return rec
  307 | 
  308 | 
  309 | if __name__ == "__main__":
  310 |     parser = argparse.ArgumentParser(description="Evaluate Phase 7 Infield Defense")
  311 |     parser.add_argument("--episodes", type=int, default=50, help="Number of evaluation episodes")
  312 |     parser.add_argument("--checkpoint", type=str, default="checkpoints/best_phase7_infield_defense_model.zip")
  313 |     parser.add_argument("--artifact-dir", type=str, default="/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7")
  314 |     args = parser.parse_args()
  315 | 
  316 |     evaluate(
  317 |         checkpoint_path=args.checkpoint,
  318 |         n_episodes=args.episodes,
  319 |         artifact_dir=args.artifact_dir,
  320 |     )
````
