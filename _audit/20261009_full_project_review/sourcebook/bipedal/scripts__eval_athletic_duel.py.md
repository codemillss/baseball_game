# bipedal/scripts/eval_athletic_duel.py

원본: [scripts/eval_athletic_duel.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/eval_athletic_duel.py)

SHA256: `84c1ae8ef815008776b8c4921a7fbf65ea4edcc557cc9114865ee6dc84bbddb1`

전체 299행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate` | FunctionDef | 16 | 293 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | sys.path.append(os.path.abspath("."))
    4 | 
    5 | import argparse
    6 | import csv
    7 | import shutil
    8 | import numpy as np
    9 | import cv2
   10 | import imageio
   11 | from stable_baselines3 import PPO
   12 | from envs.athletic_duel_env import AthleticDuelEnv
   13 | 
   14 | ARTIFACTS_DIR = "/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7"
   15 | 
   16 | def evaluate(episodes=50, render_video=True):
   17 |     os.makedirs("logs/videos", exist_ok=True)
   18 |     os.makedirs("logs", exist_ok=True)
   19 |     os.makedirs(ARTIFACTS_DIR, exist_ok=True)
   20 | 
   21 |     env = AthleticDuelEnv(render_mode="rgb_array")
   22 | 
   23 |     model_path = "checkpoints/best_athletic_duel_model.zip"
   24 |     if not os.path.exists(model_path):
   25 |         model_path = "checkpoints/final_athletic_duel_model.zip"
   26 | 
   27 |     model = None
   28 |     if os.path.exists(model_path):
   29 |         print(f"Loading trained policy from {model_path}...")
   30 |         model = PPO.load(model_path, env=env)
   31 |     else:
   32 |         print("Model checkpoint not found, running with zero action baseline.")
   33 | 
   34 |     records = []
   35 |     print(f"\n--- Starting Athletic Duel Benchmark: {episodes} Episodes ---")
   36 |     
   37 |     # Track episodes for video/gif rendering
   38 |     best_hit_ep = -1
   39 |     best_hit_speed = -1.0
   40 |     best_caught_ep = -1
   41 |     best_framing_err = 999.0
   42 | 
   43 |     for ep in range(episodes):
   44 |         obs, info = env.reset(seed=ep * 100 + 42)
   45 |         done = False
   46 |         ep_reward = 0.0
   47 |         step = 0
   48 |         last_step_info = None
   49 | 
   50 |         while not done:
   51 |             if model is not None:
   52 |                 action, _ = model.predict(obs, deterministic=True)
   53 |             else:
   54 |                 action = np.zeros(6, dtype=np.float32)
   55 | 
   56 |             obs, reward, terminated, truncated, step_info = env.step(action)
   57 |             ep_reward += reward
   58 |             step += 1
   59 |             last_step_info = step_info
   60 |             done = terminated or truncated
   61 | 
   62 |         if step_info["is_hit"] and step_info["exit_velocity_kmh"] > best_hit_speed:
   63 |             best_hit_speed = step_info["exit_velocity_kmh"]
   64 |             best_hit_ep = ep
   65 |         if not step_info["is_hit"] and step_info["catcher_caught"]:
   66 |             if best_caught_ep == -1 or step_info.get("sweet_spot_error_cm", 999.0) < best_framing_err:
   67 |                 best_caught_ep = ep
   68 |                 best_framing_err = step_info.get("sweet_spot_error_cm", 999.0)
   69 | 
   70 |         records.append({
   71 |             "episode": ep + 1,
   72 |             "pitch_type": step_info["pitch_type"],
   73 |             "pitch_speed_kmh": float(step_info["pitch_speed_kmh"]),
   74 |             "is_strike": bool(step_info["is_strike"]),
   75 |             "is_hit": bool(step_info["is_hit"]),
   76 |             "is_fair": bool(step_info["is_fair"]),
   77 |             "sweet_spot_error_cm": float(step_info["sweet_spot_error_cm"]),
   78 |             "exit_velocity_kmh": float(step_info["exit_velocity_kmh"]),
   79 |             "exit_heading_deg": float(step_info["exit_heading_deg"]),
   80 |             "batter_fallen": bool(step_info["batter_fallen"]),
   81 |             "catcher_fallen": bool(step_info["catcher_fallen"]),
   82 |             "catcher_caught": bool(step_info["catcher_caught"]),
   83 |             "batter_pelvis_z": float(step_info["batter_pelvis_z"]),
   84 |             "catcher_pelvis_z": float(step_info["catcher_pelvis_z"]),
   85 |             "plate_cross_x": float(step_info["plate_cross_x"]),
   86 |             "plate_cross_z": float(step_info["plate_cross_z"]),
   87 |             "left_foot_lift_cm": float(step_info["left_foot_lift_cm"]),
   88 |             "hand_distance_cm": float(step_info["hand_distance_cm"]),
   89 |             "torso_rotation_deg": float(step_info["torso_rotation_deg"]),
   90 |             "catcher_drift_cm": float(step_info["catcher_drift_cm"]),
   91 |             "ep_reward": float(ep_reward)
   92 |         })
   93 | 
   94 |     csv_path = "logs/athletic_duel_metrics.csv"
   95 |     with open(csv_path, "w", newline="") as f:
   96 |         writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
   97 |         writer.writeheader()
   98 |         writer.writerows(records)
   99 |     print(f"\nSaved benchmark metrics to {csv_path}")
  100 | 
  101 |     # Summary
  102 |     n_total = len(records)
  103 |     b_surv = sum(not r["batter_fallen"] for r in records) / n_total * 100
  104 |     c_surv = sum(not r["catcher_fallen"] for r in records) / n_total * 100
  105 |     hits = sum(r["is_hit"] for r in records) / n_total * 100
  106 |     fairs = sum(r["is_fair"] for r in records) / n_total * 100
  107 |     strikes = sum(r["is_strike"] for r in records) / n_total * 100
  108 |     caught = sum(r["catcher_caught"] for r in records if not r["is_hit"])
  109 |     unhit = sum(not r["is_hit"] for r in records)
  110 |     catch_rate = (caught / unhit * 100) if unhit > 0 else 100.0
  111 | 
  112 |     hit_errs = [r["sweet_spot_error_cm"] for r in records if r["is_hit"]]
  113 |     mean_sw_err = np.mean(hit_errs) if len(hit_errs) > 0 else 0.0
  114 |     hit_vels = [r["exit_velocity_kmh"] for r in records if r["is_hit"]]
  115 |     mean_exit_v = np.mean(hit_vels) if len(hit_vels) > 0 else 0.0
  116 | 
  117 |     mean_l_lift = np.mean([r["left_foot_lift_cm"] for r in records])
  118 |     mean_h_dist = np.mean([r["hand_distance_cm"] for r in records])
  119 |     mean_c_drift = np.mean([r["catcher_drift_cm"] for r in records])
  120 | 
  121 |     print("=" * 65)
  122 |     print("--- 50-EPISODE ATHLETIC DUEL BENCHMARK SUMMARY ---")
  123 |     print(f"Total Episodes:                 {n_total}")
  124 |     print(f"Batter Balance Survival Rate:   {b_surv:.1f}% ({sum(not r['batter_fallen'] for r in records)}/{n_total})")
  125 |     print(f"Catcher Squat Survival Rate:    {c_surv:.1f}% ({sum(not r['catcher_fallen'] for r in records)}/{n_total})")
  126 |     print(f"Bat Contact Rate:               {hits:.1f}% ({sum(r['is_hit'] for r in records)}/{n_total})")
  127 |     print(f"Fair-Hit Rate:                  {fairs:.1f}% ({sum(r['is_fair'] for r in records)}/{n_total})")
  128 |     print(f"Strike Zone Adherence Rate:     {strikes:.1f}% ({sum(r['is_strike'] for r in records)}/{n_total})")
  129 |     print(f"Catcher Catch on Taken Pitches: {catch_rate:.1f}% ({caught}/{unhit})")
  130 |     print(f"Mean Sweet Spot Error MAE:      {mean_sw_err:.2f} cm")
  131 |     print(f"Mean Exit Velocity:             {mean_exit_v:.1f} km/h")
  132 |     print(f"Mean Lead Foot Lift:            {mean_l_lift:.2f} cm (Target: < 0.20 cm)")
  133 |     print(f"Mean Hand Distance:             {mean_h_dist:.2f} cm (Target: < 0.50 cm)")
  134 |     print(f"Mean Catcher Squat Drift:       {mean_c_drift:.2f} cm (Target: < 5.00 cm)")
  135 |     print("=" * 65)
  136 | 
  137 |     for ptype in ["Fastball", "Slider", "Curveball"]:
  138 |         sub = [r for r in records if r["pitch_type"] == ptype]
  139 |         if sub:
  140 |             c_cnt = len(sub)
  141 |             s_hit = sum(r["is_hit"] for r in sub) / c_cnt * 100
  142 |             s_fair = sum(r["is_fair"] for r in sub) / c_cnt * 100
  143 |             s_spd = np.mean([r["pitch_speed_kmh"] for r in sub])
  144 |             s_errs = [r["sweet_spot_error_cm"] for r in sub if r["is_hit"]]
  145 |             s_err = np.mean(s_errs) if s_errs else 0.0
  146 |             print(f"[{ptype:>9s}] Count: {c_cnt:2d} | Hit: {s_hit:5.1f}% | Fair: {s_fair:5.1f}% | Spd: {s_spd:4.1f} km/h | Err: {s_err:4.1f} cm")
  147 | 
  148 |     # Render Multi-Camera Video and Animated GIFs
  149 |     if render_video:
  150 |         target_ep = best_hit_ep if best_hit_ep >= 0 else 0
  151 |         print(f"\nRendering multi-camera demonstration using Episode {target_ep + 1} (Seed {target_ep * 100 + 42})...")
  152 | 
  153 |         obs, info = env.reset(seed=target_ep * 100 + 42)
  154 |         done = False
  155 |         step = 0
  156 | 
  157 |         video_frames = []
  158 |         dugout_frames = []
  159 |         cf_frames = []
  160 |         catcher_frames = []
  161 |         capture_frames = {}
  162 | 
  163 |         while not done:
  164 |             if model is not None:
  165 |                 action, _ = model.predict(obs, deterministic=True)
  166 |             else:
  167 |                 action = np.zeros(6, dtype=np.float32)
  168 | 
  169 |             obs, reward, terminated, truncated, step_info = env.step(action)
  170 |             step += 1
  171 | 
  172 |             # Multi-camera rendering
  173 |             f_dugout = env.render(camera_name="duel_broadcast_cam")
  174 |             f_cf = env.render(camera_name="cf_broadcast_cam")
  175 |             f_catcher = env.render(camera_name="catcher_framing_cam")
  176 | 
  177 |             dugout_frames.append(f_dugout)
  178 |             cf_frames.append(f_cf)
  179 |             catcher_frames.append(f_catcher)
  180 | 
  181 |             # HUD overlay for main broadcast MP4
  182 |             frame = f_dugout.copy()
  183 |             b_z = step_info["batter_pelvis_z"]
  184 |             c_z = step_info["catcher_pelvis_z"]
  185 | 
  186 |             overlay = frame.copy()
  187 |             cv2.rectangle(overlay, (0, 0), (640, 75), (20, 20, 20), -1)
  188 |             cv2.rectangle(overlay, (0, 415), (640, 480), (20, 20, 20), -1)
  189 |             cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
  190 | 
  191 |             ptype = step_info["pitch_type"]
  192 |             pspd = step_info["pitch_speed_kmh"]
  193 |             pz = step_info["plate_cross_z"]
  194 | 
  195 |             cv2.putText(frame, "ATHLETIC DUEL: 10M PITCHER & DEEP-KNEE BATTER", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
  196 |             t_cur = (step * 0.02)
  197 |             p_text = f"Time: {t_cur:.2f}s | {ptype} ({pspd:.1f} km/h) | Plate Z: {pz:.2f}m"
  198 |             cv2.putText(frame, p_text, (15, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)
  199 | 
  200 |             b_status = f"BATTER: Athletic Stance (Z={b_z:.2f}m)"
  201 |             if step_info["is_hit"]:
  202 |                 b_status += f" | CRACK! Exit: {step_info['exit_velocity_kmh']:.1f} km/h"
  203 |             elif step_info["batter_fallen"]:
  204 |                 b_status += " | FALLEN"
  205 |             else:
  206 |                 b_status += " | Ready"
  207 | 
  208 |             cv2.putText(frame, b_status, (15, 442), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 2)
  209 | 
  210 |             c_status = f"CATCHER: Rock-Solid Squat (Z={c_z:.2f}m)"
  211 |             if step_info["catcher_caught"]:
  212 |                 c_status += " | CAUGHT IN MITT!"
  213 |             cv2.putText(frame, c_status, (15, 468), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 200) if step_info["is_hit"] or step_info["catcher_caught"] else (200, 200, 200), 1)
  214 | 
  215 |             video_frames.append(frame)
  216 | 
  217 |             if step == 2:
  218 |                 capture_frames["release"] = frame.copy()
  219 |             elif step == 12:
  220 |                 capture_frames["approach"] = frame.copy()
  221 |             elif step_info["is_hit"] and "impact" not in capture_frames:
  222 |                 capture_frames["impact"] = frame.copy()
  223 |             elif step_info["is_hit"] and step == (env.contact_step + 6) and "follow_through" not in capture_frames:
  224 |                 capture_frames["follow_through"] = frame.copy()
  225 | 
  226 |             done = terminated or truncated
  227 | 
  228 |         if "impact" not in capture_frames and len(video_frames) > 20:
  229 |             capture_frames["impact"] = video_frames[20].copy()
  230 |         if "follow_through" not in capture_frames and len(video_frames) > 25:
  231 |             capture_frames["follow_through"] = video_frames[-1].copy()
  232 | 
  233 |         # 1. Save 50 FPS MP4 video
  234 |         vid_path = "logs/videos/athletic_duel.mp4"
  235 |         h, w, _ = video_frames[0].shape
  236 |         fourcc = cv2.VideoWriter_fourcc(*"mp4v")
  237 |         writer = cv2.VideoWriter(vid_path, fourcc, 50, (w, h))
  238 |         for vf in video_frames:
  239 |             writer.write(cv2.cvtColor(vf, cv2.COLOR_RGB2BGR))
  240 |         writer.release()
  241 |         print(f"Saved 50 FPS video to {vid_path}")
  242 | 
  243 |         # 2. Save Keyframe PNGs
  244 |         keyframe_names = [
  245 |             ("release", "athletic_pitch_release.png"),
  246 |             ("approach", "athletic_pitch_approach.png"),
  247 |             ("impact", "athletic_bat_impact.png"),
  248 |             ("follow_through", "athletic_follow_through.png")
  249 |         ]
  250 |         for k, name in keyframe_names:
  251 |             if k in capture_frames:
  252 |                 out_p = f"logs/videos/{name}"
  253 |                 cv2.imwrite(out_p, cv2.cvtColor(capture_frames[k], cv2.COLOR_RGB2BGR))
  254 |                 print(f"Saved keyframe: {out_p}")
  255 |                 shutil.copy(out_p, os.path.join(ARTIFACTS_DIR, name))
  256 | 
  257 |         # If best_caught_ep is available, render a clean catch sequence for catcher_framing_catch.gif
  258 |         caught_gif_frames = catcher_frames
  259 |         if best_caught_ep >= 0 and best_caught_ep != target_ep:
  260 |             c_obs, _ = env.reset(seed=best_caught_ep * 100 + 42)
  261 |             c_done = False
  262 |             caught_gif_frames = []
  263 |             while not c_done:
  264 |                 if model is not None:
  265 |                     c_act, _ = model.predict(c_obs, deterministic=True)
  266 |                 else:
  267 |                     c_act = np.zeros(6, dtype=np.float32)
  268 |                 c_obs, _, c_term, c_trunc, _ = env.step(c_act)
  269 |                 f_c = env.render(camera_name="catcher_framing_cam")
  270 |                 caught_gif_frames.append(f_c)
  271 |                 c_done = c_term or c_trunc
  272 | 
  273 |         # 3. Generate the 3 Animated GIFs (Downsampled to 25 FPS for web efficiency)
  274 |         gifs = [
  275 |             ("cf_broadcast.gif", cf_frames),
  276 |             ("dugout_dual.gif", dugout_frames),
  277 |             ("catcher_framing_catch.gif", caught_gif_frames)
  278 |         ]
  279 |         for gif_name, f_list in gifs:
  280 |             if len(f_list) > 0:
  281 |                 out_gif = os.path.join("logs/videos", gif_name)
  282 |                 # Subsample by 2 for smooth 25 FPS GIF
  283 |                 sub_frames = f_list[::2]
  284 |                 imageio.mimsave(out_gif, sub_frames, fps=25, loop=0)
  285 |                 print(f"Saved animated GIF: {out_gif} ({len(sub_frames)} frames)")
  286 |                 shutil.copy(out_gif, os.path.join(ARTIFACTS_DIR, gif_name))
  287 | 
  288 |         # Copy mp4 and metrics csv to artifact directory as well
  289 |         shutil.copy(vid_path, os.path.join(ARTIFACTS_DIR, "athletic_duel.mp4"))
  290 |         shutil.copy(csv_path, os.path.join(ARTIFACTS_DIR, "athletic_duel_metrics.csv"))
  291 |         print(f"Copied all video/gif artifacts to {ARTIFACTS_DIR}")
  292 | 
  293 |     env.close()
  294 | 
  295 | if __name__ == "__main__":
  296 |     parser = argparse.ArgumentParser()
  297 |     parser.add_argument("--episodes", type=int, default=50)
  298 |     args = parser.parse_args()
  299 |     evaluate(episodes=args.episodes)
````
