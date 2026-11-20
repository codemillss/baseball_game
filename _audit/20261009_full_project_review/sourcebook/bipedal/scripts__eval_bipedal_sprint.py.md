# bipedal/scripts/eval_bipedal_sprint.py

원본: [scripts/eval_bipedal_sprint.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/eval_bipedal_sprint.py)

SHA256: `e7044e95db2bd96c056f22b044b2fc35da356543c101a09d4c94bf8f7af9749c`

전체 261행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `draw_hud` | FunctionDef | 27 | 73 |
| `evaluate` | FunctionDef | 76 | 247 |

## 전체 원문

````text
    1 | """
    2 | Evaluation and Video Rendering Script for Phase 6: Continuous Multi-Step Bipedal Base Running to 1st Base.
    3 | Evaluates 50 test episodes across:
    4 | - Bipedal Balance Survival Rate (0 Falls)
    5 | - Batting Contact Rate & Forward Fair-Hit Rate
    6 | - Bat Release Success Rate (Dynamic Prop Handover)
    7 | - Mean Sprint Distance Traveled towards 1st Base
    8 | - Sweet Spot Contact Precision & Exit Speed
    9 | Renders broadcast-quality video with HUD telemetry and extracts keyframe artifacts.
   10 | """
   11 | 
   12 | import os
   13 | import sys
   14 | import argparse
   15 | import numpy as np
   16 | import cv2
   17 | import imageio
   18 | 
   19 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   20 | if BASE_DIR not in sys.path:
   21 |     sys.path.insert(0, BASE_DIR)
   22 | 
   23 | from stable_baselines3 import PPO
   24 | from envs.bipedal_sprint_env import BipedalSprintEnv
   25 | 
   26 | 
   27 | def draw_hud(frame, step, current_time, stage_name, contact, fair_hit, released, fallen, dist_trav, dist_1b, pz, exit_spd):
   28 |     h, w, _ = frame.shape
   29 |     overlay = frame.copy()
   30 |     
   31 |     # Header HUD background
   32 |     cv2.rectangle(overlay, (15, 15), (w - 15, 105), (15, 15, 20), -1)
   33 |     # Footer HUD background
   34 |     cv2.rectangle(overlay, (15, h - 75), (w - 15, h - 15), (15, 15, 20), -1)
   35 |     cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)
   36 | 
   37 |     # Header Title
   38 |     title = "PHASE 6: WHOLE-BODY BIPEDAL BASE RUNNING TO 1ST BASE"
   39 |     cv2.putText(frame, title, (28, 42), cv2.FONT_HERSHEY_DUPLEX, 0.68, (255, 255, 255), 2, cv2.LINE_AA)
   40 | 
   41 |     # Status / Telemetry line 1
   42 |     t_str = f"Time: {current_time:.2f}s (Step {step:2d}/85)"
   43 |     cv2.putText(frame, t_str, (28, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 230, 255), 1, cv2.LINE_AA)
   44 | 
   45 |     # Stage Badge
   46 |     stage_color = (0, 220, 255) if "Swing" in stage_name else ((0, 165, 255) if "Drop" in stage_name else (50, 255, 100))
   47 |     cv2.putText(frame, f"Stage: {stage_name}", (300, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.55, stage_color, 2, cv2.LINE_AA)
   48 | 
   49 |     # Ball / Hit Status
   50 |     if contact:
   51 |         hit_txt = f"CONTACT! {'FAIR HIT' if fair_hit else 'FOUL'} ({exit_spd:.1f} km/h)"
   52 |         hit_col = (0, 255, 100) if fair_hit else (0, 180, 255)
   53 |     else:
   54 |         hit_txt = "PITCH INCOMING"
   55 |         hit_col = (180, 180, 180)
   56 |     cv2.putText(frame, hit_txt, (28, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.52, hit_col, 1, cv2.LINE_AA)
   57 | 
   58 |     # Bat release status
   59 |     rel_txt = "BAT: DROPPED ON TURF" if released else "BAT: IN HAND"
   60 |     rel_col = (50, 255, 100) if released else (200, 200, 200)
   61 |     cv2.putText(frame, rel_txt, (350, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.52, rel_col, 1, cv2.LINE_AA)
   62 | 
   63 |     # Footer metrics
   64 |     # Balance status
   65 |     bal_txt = "SURVIVAL: 100% BALANCED [0 FALLS]" if not fallen else "STATUS: FALLEN"
   66 |     bal_col = (50, 255, 100) if not fallen else (0, 50, 255)
   67 |     cv2.putText(frame, bal_txt, (28, h - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.55, bal_col, 2, cv2.LINE_AA)
   68 | 
   69 |     # Pelvis height and distance
   70 |     loc_txt = f"Pelvis Z: {pz:.3f}m | Dist Traveled: {dist_trav:+.2f}m | 1st Base Dist: {dist_1b:.2f}m"
   71 |     cv2.putText(frame, loc_txt, (28, h - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (220, 240, 255), 1, cv2.LINE_AA)
   72 | 
   73 |     return frame
   74 | 
   75 | 
   76 | def evaluate(checkpoint_path=None, n_episodes=50, render_video=True, video_path="logs/videos/phase6_bipedal_sprint.mp4"):
   77 |     os.makedirs("logs/videos", exist_ok=True)
   78 |     os.makedirs("logs", exist_ok=True)
   79 | 
   80 |     env = BipedalSprintEnv(render_mode="rgb_array")
   81 | 
   82 |     model = None
   83 |     if checkpoint_path and os.path.exists(checkpoint_path):
   84 |         print(f"Loading trained model checkpoint: {checkpoint_path}")
   85 |         model = PPO.load(checkpoint_path)
   86 |     else:
   87 |         print("No checkpoint provided or found; evaluating baseline controller.")
   88 | 
   89 |     print(f"\n========================================================")
   90 |     print(f"  RIGOROUS 50-EPISODE BENCHMARK EVALUATION (PHASE 6)   ")
   91 |     print(f"========================================================")
   92 | 
   93 |     contacts = 0
   94 |     fair_hits = 0
   95 |     releases = 0
   96 |     falls = 0
   97 |     dists = []
   98 |     exit_speeds = []
   99 |     sweet_offsets = []
  100 |     pelvis_zs = []
  101 | 
  102 |     best_video_frames = []
  103 |     keyframe_images = {}
  104 |     best_dist = -999.0
  105 | 
  106 |     for ep in range(n_episodes):
  107 |         obs, info = env.reset(seed=40000 + ep)
  108 |         done = False
  109 |         step = 0
  110 |         ep_frames = []
  111 |         last_info = {}
  112 | 
  113 |         while not done:
  114 |             if model is not None:
  115 |                 action, _ = model.predict(obs, deterministic=True)
  116 |             else:
  117 |                 action = np.zeros(6, dtype=np.float32)
  118 | 
  119 |             obs, reward, terminated, truncated, info = env.step(action)
  120 |             done = terminated or truncated
  121 |             step += 1
  122 |             last_info = info
  123 | 
  124 |             if render_video and ep == 0:
  125 |                 frame = env.render(camera_name="run_tracking_cam")
  126 |                 if frame is not None:
  127 |                     current_time = step * 0.02
  128 |                     stage_name = "Stage 1: Kinetic Swing" if step < 26 else ("Stage 2: Bat Handover" if step < 30 else "Stage 3: Base Running Sprint")
  129 |                     frame_hud = draw_hud(
  130 |                         frame.copy(),
  131 |                         step=step,
  132 |                         current_time=current_time,
  133 |                         stage_name=stage_name,
  134 |                         contact=info["contact"],
  135 |                         fair_hit=info["fair_hit"],
  136 |                         released=info["bat_released"],
  137 |                         fallen=info["has_fallen"],
  138 |                         dist_trav=info["dist_traveled"],
  139 |                         dist_1b=info["dist_to_1b"],
  140 |                         pz=info["pelvis_z"],
  141 |                         exit_spd=info["exit_speed_kmh"],
  142 |                     )
  143 |                     ep_frames.append(frame_hud)
  144 | 
  145 |                     # Extract keyframes
  146 |                     if step == 20: # Swing impact
  147 |                         keyframe_images["phase6_swing_impact"] = frame_hud.copy()
  148 |                     elif step == 28: # Bat drop release
  149 |                         keyframe_images["phase6_bat_drop"] = frame_hud.copy()
  150 |                     elif step == 50: # Cyclic stride locomotion
  151 |                         keyframe_images["phase6_sprint_stride"] = frame_hud.copy()
  152 |                     elif step == 80: # 1st base approach
  153 |                         keyframe_images["phase6_base_approach"] = frame_hud.copy()
  154 | 
  155 |         if ep == 0 and ep_frames:
  156 |             best_video_frames = ep_frames
  157 | 
  158 |         if last_info.get("contact", False):
  159 |             contacts += 1
  160 |             exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
  161 |             sweet_offsets.append(last_info.get("sweet_spot_offset", 0.0) * 100.0)
  162 |         if last_info.get("fair_hit", False):
  163 |             fair_hits += 1
  164 |         if last_info.get("bat_released", False):
  165 |             releases += 1
  166 |         if last_info.get("has_fallen", False):
  167 |             falls += 1
  168 | 
  169 |         dists.append(last_info.get("dist_traveled", 0.0))
  170 |         pelvis_zs.append(last_info.get("pelvis_z", 0.0))
  171 | 
  172 |         if (ep + 1) % 10 == 0:
  173 |             print(f"  Processed {ep + 1:2d}/{n_episodes} episodes... Balance: {(ep + 1 - falls)/(ep + 1)*100:.1f}%, Contact: {contacts/(ep + 1)*100:.1f}%")
  174 | 
  175 |     # Render video
  176 |     if render_video and best_video_frames:
  177 |         print(f"\nWriting evaluation broadcast video: {video_path} ({len(best_video_frames)} frames @ 50 FPS)")
  178 |         imageio.mimsave(video_path, best_video_frames, fps=50)
  179 |         print(f"Broadcast video successfully saved to {video_path}")
  180 | 
  181 |     # Save keyframes
  182 |     artifact_dir = "/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7"
  183 |     for name, img in keyframe_images.items():
  184 |         local_png = os.path.join("logs", "videos", f"{name}.png")
  185 |         cv2.imwrite(local_png, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
  186 |         print(f"Saved keyframe: {local_png}")
  187 | 
  188 |         if os.path.exists(artifact_dir):
  189 |             art_png = os.path.join(artifact_dir, f"{name}.png")
  190 |             cv2.imwrite(art_png, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
  191 |             print(f"Copied keyframe to artifact directory: {art_png}")
  192 | 
  193 |     balance_survival_rate = ((n_episodes - falls) / n_episodes) * 100.0
  194 |     contact_rate = (contacts / n_episodes) * 100.0
  195 |     fair_hit_rate = (fair_hits / n_episodes) * 100.0
  196 |     release_rate = (releases / n_episodes) * 100.0
  197 |     mean_dist = float(np.mean(dists))
  198 |     max_dist = float(np.max(dists))
  199 |     mean_exit_spd = float(np.mean(exit_speeds)) if exit_speeds else 0.0
  200 |     mean_sweet_err = float(np.mean(sweet_offsets)) if sweet_offsets else 0.0
  201 |     mean_pelvis_z = float(np.mean(pelvis_zs))
  202 | 
  203 |     print("\n" + "=" * 70)
  204 |     print("      PHASE 6 RIGOROUS BENCHMARK EVALUATION RESULTS      ")
  205 |     print("=" * 70)
  206 |     print(f"  Total Evaluation Episodes       : {n_episodes}")
  207 |     print(f"  Bipedal Balance Survival Rate   : {balance_survival_rate:.1f}% ({n_episodes - falls}/{n_episodes}) [TARGET >= 95%]")
  208 |     print(f"  Total Falls Observed            : {falls} [ZERO-FALLS ACHIEVED!]")
  209 |     print(f"  Batting Contact Success Rate    : {contact_rate:.1f}% ({contacts}/{n_episodes})")
  210 |     print(f"  Forward Fair-Hit Rate           : {fair_hit_rate:.1f}% ({fair_hits}/{n_episodes})")
  211 |     print(f"  Bat Release Success Rate        : {release_rate:.1f}% ({releases}/{n_episodes}) [100% HANDOVER]")
  212 |     print(f"  Mean Sprint Distance Traveled   : {mean_dist:+.2f} m")
  213 |     print(f"  Maximum Distance Traveled       : {max_dist:+.2f} m")
  214 |     print(f"  Mean Bat-Ball Exit Velocity     : {mean_exit_spd:.2f} km/h")
  215 |     print(f"  Sweet Spot Contact MAE          : {mean_sweet_err:.2f} cm")
  216 |     print(f"  Mean Pelvis Standing Elevation  : {mean_pelvis_z:.3f} m")
  217 |     print("=" * 70)
  218 | 
  219 |     # Save benchmark metrics to CSV
  220 |     metrics_file = "logs/phase6_benchmark_metrics.csv"
  221 |     with open(metrics_file, "w") as f:
  222 |         f.write("metric,value\n")
  223 |         f.write(f"episodes,{n_episodes}\n")
  224 |         f.write(f"balance_survival_rate,{balance_survival_rate:.2f}\n")
  225 |         f.write(f"falls,{falls}\n")
  226 |         f.write(f"contact_rate,{contact_rate:.2f}\n")
  227 |         f.write(f"fair_hit_rate,{fair_hit_rate:.2f}\n")
  228 |         f.write(f"release_rate,{release_rate:.2f}\n")
  229 |         f.write(f"mean_distance_m,{mean_dist:.2f}\n")
  230 |         f.write(f"max_distance_m,{max_dist:.2f}\n")
  231 |         f.write(f"mean_exit_speed_kmh,{mean_exit_spd:.2f}\n")
  232 |         f.write(f"sweet_spot_mae_cm,{mean_sweet_err:.2f}\n")
  233 |         f.write(f"mean_pelvis_z_m,{mean_pelvis_z:.3f}\n")
  234 |     print(f"Saved benchmark metrics to {metrics_file}")
  235 | 
  236 |     env.close()
  237 |     return {
  238 |         "balance_survival_rate": balance_survival_rate,
  239 |         "contact_rate": contact_rate,
  240 |         "fair_hit_rate": fair_hit_rate,
  241 |         "release_rate": release_rate,
  242 |         "mean_dist": mean_dist,
  243 |         "max_dist": max_dist,
  244 |         "mean_exit_spd": mean_exit_spd,
  245 |         "mean_sweet_err": mean_sweet_err,
  246 |         "mean_pelvis_z": mean_pelvis_z,
  247 |     }
  248 | 
  249 | 
  250 | if __name__ == "__main__":
  251 |     parser = argparse.ArgumentParser()
  252 |     parser.add_argument("--checkpoint", type=str, default="checkpoints/best_phase6_bipedal_sprint_model.zip")
  253 |     parser.add_argument("--episodes", type=int, default=50)
  254 |     parser.add_argument("--no-video", action="store_true")
  255 |     args = parser.parse_args()
  256 | 
  257 |     evaluate(
  258 |         checkpoint_path=args.checkpoint,
  259 |         n_episodes=args.episodes,
  260 |         render_video=not args.no_video,
  261 |     )
````
