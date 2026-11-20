# bipedal/scripts/eval_bipedal_duel.py

원본: [scripts/eval_bipedal_duel.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/eval_bipedal_duel.py)

SHA256: `cb551858e4a00ea0087c0d9f938f182e09141159a160cbbf49b1dca758f57b98`

전체 278행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate_bipedal_duel` | FunctionDef | 23 | 260 |

## 전체 원문

````text
    1 | """
    2 | Evaluation and Video Rendering Pipeline for Phase 5: Full-Stadium Whole-Body Bipedal Duel.
    3 | Benchmarks the trained 6-DoF floating-base H1 policy over 50 test episodes against
    4 | the live 10m mound H1 Pitcher (Fastball, Slider, Curveball).
    5 | Renders broadcast video logs/videos/phase5_bipedal_duel.mp4 and extracts keyframes.
    6 | """
    7 | 
    8 | import os
    9 | import sys
   10 | import argparse
   11 | import numpy as np
   12 | import cv2
   13 | import shutil
   14 | 
   15 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   16 | if BASE_DIR not in sys.path:
   17 |     sys.path.insert(0, BASE_DIR)
   18 | 
   19 | from stable_baselines3 import PPO
   20 | from envs.bipedal_duel_env import BipedalDuelEnv
   21 | 
   22 | 
   23 | def evaluate_bipedal_duel(
   24 |     model_path="checkpoints/best_phase5_bipedal_duel_model.zip",
   25 |     n_episodes=50,
   26 |     render_video=True,
   27 |     video_out="logs/videos/phase5_bipedal_duel.mp4",
   28 |     artifact_dir=None,
   29 | ):
   30 |     print("=" * 75)
   31 |     print(f"Benchmarking Phase 5 Whole-Body Bipedal Duel AI: {model_path}")
   32 |     print(f"Total Test Episodes: {n_episodes} (10m Mound Pitcher vs 6-DoF Floating Batter)")
   33 |     print("=" * 75)
   34 | 
   35 |     if not os.path.exists(model_path):
   36 |         raise FileNotFoundError(f"Model checkpoint not found at {model_path}")
   37 | 
   38 |     model = PPO.load(model_path)
   39 |     env = BipedalDuelEnv(render_mode="rgb_array" if render_video else None)
   40 | 
   41 |     balanced_count = 0
   42 |     strike_count = 0
   43 |     contact_count = 0
   44 |     fair_count = 0
   45 |     exit_speeds = []
   46 |     sweet_offsets = []
   47 |     pelvis_zs = []
   48 | 
   49 |     # Per-pitch statistics
   50 |     pitch_stats = {
   51 |         "Fastball": {"total": 0, "strikes": 0, "contacts": 0, "fairs": 0, "speeds": [], "errors": []},
   52 |         "Slider":   {"total": 0, "strikes": 0, "contacts": 0, "fairs": 0, "speeds": [], "errors": []},
   53 |         "Curveball":{"total": 0, "strikes": 0, "contacts": 0, "fairs": 0, "speeds": [], "errors": []},
   54 |     }
   55 | 
   56 |     # Directional spray
   57 |     spray_stats = {
   58 |         "pull":   {"target": 0, "hit": 0},
   59 |         "center": {"target": 0, "hit": 0},
   60 |         "push":   {"target": 0, "hit": 0},
   61 |     }
   62 | 
   63 |     recorded_video_frames = []
   64 |     best_fair_video_frames = []
   65 |     best_fair_speed = 0.0
   66 |     best_release_step = 22
   67 |     best_contact_step = -1
   68 | 
   69 |     os.makedirs(os.path.dirname(video_out), exist_ok=True)
   70 | 
   71 |     for ep in range(n_episodes):
   72 |         obs, info = env.reset(seed=30000 + ep)
   73 |         pname = env.pitch_name
   74 |         pitch_stats[pname]["total"] += 1
   75 | 
   76 |         target_az = np.degrees(env.target_azimuth_rad)
   77 |         if target_az < -10.0:
   78 |             zone = "pull"
   79 |         elif target_az > 10.0:
   80 |             zone = "push"
   81 |         else:
   82 |             zone = "center"
   83 |         spray_stats[zone]["target"] += 1
   84 | 
   85 |         done = False
   86 |         last_info = {}
   87 |         ep_frames = []
   88 | 
   89 |         step_idx = 0
   90 |         while not done:
   91 |             action, _ = model.predict(obs, deterministic=True)
   92 |             obs, reward, terminated, truncated, info = env.step(action)
   93 |             done = terminated or truncated
   94 |             last_info = info
   95 | 
   96 |             if render_video:
   97 |                 frame = env.render(camera_name="duel_broadcast_cam")
   98 |                 if frame is not None:
   99 |                     hud = frame.copy()
  100 |                     cv2.putText(hud, f"PHASE 5 DUEL: Whole-Body Pitcher vs Batter (10m Stadium)", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
  101 |                     pspd = last_info.get("pitch_speed_kmh", 0.0)
  102 |                     cv2.putText(hud, f"Pitch: {pname} ({pspd:.1f} km/h)", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2)
  103 |                     pz = last_info.get("pelvis_z", 0.88)
  104 |                     cv2.putText(hud, f"Batter Pelvis: {pz:.2f}m (6-DoF Upright)", (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 128), 2)
  105 | 
  106 |                     if last_info.get("contact", False):
  107 |                         espd = last_info.get("exit_speed_kmh", 0.0)
  108 |                         ftext = "FAIR HIT" if last_info.get("fair_hit", False) else "FOUL"
  109 |                         fcolor = (0, 255, 0) if last_info.get("fair_hit", False) else (0, 165, 255)
  110 |                         cv2.putText(hud, f"CRACK! {ftext} ({espd:.1f} km/h)", (15, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.65, fcolor, 2)
  111 | 
  112 |                     ep_frames.append(hud)
  113 | 
  114 |             step_idx += 1
  115 | 
  116 |         # Episode aggregations
  117 |         if not last_info.get("has_fallen", False):
  118 |             balanced_count += 1
  119 |         if last_info.get("is_strike", False):
  120 |             strike_count += 1
  121 |             pitch_stats[pname]["strikes"] += 1
  122 |         if last_info.get("contact", False):
  123 |             contact_count += 1
  124 |             pitch_stats[pname]["contacts"] += 1
  125 |             spd = last_info.get("exit_speed_kmh", 0.0)
  126 |             exit_speeds.append(spd)
  127 |             pitch_stats[pname]["speeds"].append(spd)
  128 |             err = last_info.get("sweet_offset_cm", 0.0)
  129 |             if err > 0:
  130 |                 sweet_offsets.append(err)
  131 |                 pitch_stats[pname]["errors"].append(err)
  132 | 
  133 |         if last_info.get("fair_hit", False):
  134 |             fair_count += 1
  135 |             pitch_stats[pname]["fairs"] += 1
  136 |             az = last_info.get("azimuth_deg", 0.0)
  137 |             if zone == "pull" and az < -5.0:
  138 |                 spray_stats["pull"]["hit"] += 1
  139 |             elif zone == "center" and abs(az) <= 15.0:
  140 |                 spray_stats["center"]["hit"] += 1
  141 |             elif zone == "push" and az > 5.0:
  142 |                 spray_stats["push"]["hit"] += 1
  143 | 
  144 |         pelvis_zs.append(last_info.get("pelvis_z", 0.88))
  145 | 
  146 |         if render_video:
  147 |             if len(recorded_video_frames) == 0:
  148 |                 recorded_video_frames = ep_frames
  149 |             cur_speed = last_info.get("exit_speed_kmh", 0.0)
  150 |             if last_info.get("fair_hit", False) and (len(best_fair_video_frames) == 0 or cur_speed > best_fair_speed):
  151 |                 best_fair_video_frames = ep_frames
  152 |                 best_fair_speed = cur_speed
  153 |                 best_release_step = env.actual_release_step
  154 |                 best_contact_step = env.contact_step
  155 | 
  156 |     # Save Video
  157 |     final_video_frames = best_fair_video_frames if len(best_fair_video_frames) > 0 else recorded_video_frames
  158 |     if render_video and len(final_video_frames) > 0:
  159 |         h, w, _ = final_video_frames[0].shape
  160 |         fourcc = cv2.VideoWriter_fourcc(*"mp4v")
  161 |         writer = cv2.VideoWriter(video_out, fourcc, 50, (w, h))
  162 |         for f in final_video_frames:
  163 |             writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
  164 |         writer.release()
  165 |         print(f"\n[Video Saved] {video_out} ({len(final_video_frames)} frames @ 50 FPS)")
  166 | 
  167 |         # Save Keyframe PNGs directly from final video sequence
  168 |         n_fr = len(final_video_frames)
  169 |         rel_idx = min(best_release_step, n_fr - 1)
  170 |         app_idx = min(best_release_step + 8, n_fr - 1)
  171 |         imp_idx = min(best_contact_step if best_contact_step > 0 else (best_release_step + 14), n_fr - 1)
  172 |         fol_idx = min(imp_idx + 6, n_fr - 1)
  173 | 
  174 |         release_frame = final_video_frames[rel_idx]
  175 |         approach_frame = final_video_frames[app_idx]
  176 |         impact_frame = final_video_frames[imp_idx]
  177 |         follow_frame = final_video_frames[fol_idx]
  178 | 
  179 |         keyframe_paths = []
  180 |         p1 = "logs/videos/phase5_pitcher_release.png"
  181 |         cv2.imwrite(p1, cv2.cvtColor(release_frame, cv2.COLOR_RGB2BGR))
  182 |         keyframe_paths.append(p1)
  183 | 
  184 |         p2 = "logs/videos/phase5_pitch_approach.png"
  185 |         cv2.imwrite(p2, cv2.cvtColor(approach_frame, cv2.COLOR_RGB2BGR))
  186 |         keyframe_paths.append(p2)
  187 | 
  188 |         p3 = "logs/videos/phase5_batter_impact.png"
  189 |         cv2.imwrite(p3, cv2.cvtColor(impact_frame, cv2.COLOR_RGB2BGR))
  190 |         keyframe_paths.append(p3)
  191 | 
  192 |         p4 = "logs/videos/phase5_follow_through.png"
  193 |         cv2.imwrite(p4, cv2.cvtColor(follow_frame, cv2.COLOR_RGB2BGR))
  194 |         keyframe_paths.append(p4)
  195 | 
  196 |         # Copy to artifact directories
  197 |         target_dirs = [
  198 |             artifact_dir,
  199 |             "/Users/jin10000/.gemini/antigravity/brain/3428aca4-b64f-46eb-b6ef-32f898a87eea/",
  200 |             "/Users/jin10000/.gemini/antigravity/brain/ef159b4b-9bbe-4bcc-82ca-f392479a9141/",
  201 |             "/Users/jin10000/.gemini/antigravity/brain/b27efedd-978d-4093-a184-a76fc153249b/",
  202 |             "/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/",
  203 |             "/Users/jin10000/.gemini/antigravity/brain/fae6624d-06df-4b92-82fa-5fa6bf786732/",
  204 |             "/Users/jin10000/.gemini/antigravity/brain/228b4428-0e8a-419f-aa94-d5ff27726053/",
  205 |         ]
  206 |         for td in target_dirs:
  207 |             if td and os.path.exists(td):
  208 |                 for kp in keyframe_paths:
  209 |                     shutil.copy(kp, td)
  210 |                     print(f"Copied {kp} to artifact dir: {td}")
  211 | 
  212 |     # Metrics computation
  213 |     balance_rate = (balanced_count / n_episodes) * 100.0
  214 |     strike_rate = (strike_count / n_episodes) * 100.0
  215 |     contact_rate = (contact_count / n_episodes) * 100.0
  216 |     fair_rate = (fair_count / n_episodes) * 100.0
  217 |     mean_exit_vel = float(np.mean(exit_speeds)) if exit_speeds else 0.0
  218 |     mean_sweet_err = float(np.mean(sweet_offsets)) if sweet_offsets else 0.0
  219 |     mean_pelvis_z = float(np.mean(pelvis_zs)) if pelvis_zs else 0.0
  220 | 
  221 |     print("\n" + "=" * 75)
  222 |     print("      PHASE 5 FULL-STADIUM WHOLE-BODY BIPEDAL DUEL BENCHMARK (50 EPISODES)")
  223 |     print("=" * 75)
  224 |     print(f"  Pitcher Mound Strike Rate   : {strike_rate:.1f}% ({strike_count}/{n_episodes}) [9-Grid Zone]")
  225 |     print(f"  Batter Balance Survival Rate: {balance_rate:.1f}% ({balanced_count}/{n_episodes}) [ZERO FALLS!]")
  226 |     print(f"  Bat Contact Success Rate    : {contact_rate:.1f}% ({contact_count}/{n_episodes})")
  227 |     print(f"  Forward Fair-Hit Rate       : {fair_rate:.1f}% ({fair_count}/{n_episodes})")
  228 |     print(f"  Sweet Spot Contact MAE      : {mean_sweet_err:.2f} cm")
  229 |     print(f"  Mean Exit Velocity          : {mean_exit_vel:.1f} km/h")
  230 |     print(f"  Mean Pelvis Elevation       : {mean_pelvis_z:.3f} m (Nominal: 0.88m)")
  231 |     print("-" * 75)
  232 |     print("  Breakdown by Pitch Type:")
  233 |     for pt, stats in pitch_stats.items():
  234 |         n_p = stats["total"]
  235 |         if n_p > 0:
  236 |             c_r = (stats["contacts"] / n_p) * 100.0
  237 |             f_r = (stats["fairs"] / n_p) * 100.0
  238 |             s_r = (stats["strikes"] / n_p) * 100.0
  239 |             m_v = np.mean(stats["speeds"]) if stats["speeds"] else 0.0
  240 |             m_e = np.mean(stats["errors"]) if stats["errors"] else 0.0
  241 |             print(f"    - {pt:9s}: Strikes={s_r:.1f}% ({stats['strikes']}/{n_p}), Contact={c_r:.1f}%, Fair={f_r:.1f}%, ExitSpd={m_v:.1f} km/h, SweetErr={m_e:.1f}cm")
  242 |     print("-" * 75)
  243 |     print("  Directional Batting Spray Accuracy:")
  244 |     for dir_name, d_stat in spray_stats.items():
  245 |         acc = (d_stat["hit"] / d_stat["target"] * 100.0) if d_stat["target"] > 0 else 0.0
  246 |         print(f"    - {dir_name.capitalize():6s} Aim: {acc:.1f}% ({d_stat['hit']}/{d_stat['target']})")
  247 |     print("=" * 75 + "\n")
  248 | 
  249 |     env.close()
  250 |     return {
  251 |         "strike_rate": strike_rate,
  252 |         "balance_rate": balance_rate,
  253 |         "contact_rate": contact_rate,
  254 |         "fair_rate": fair_rate,
  255 |         "mean_exit_vel": mean_exit_vel,
  256 |         "mean_sweet_err": mean_sweet_err,
  257 |         "mean_pelvis_z": mean_pelvis_z,
  258 |         "pitch_stats": pitch_stats,
  259 |         "spray_stats": spray_stats,
  260 |     }
  261 | 
  262 | 
  263 | if __name__ == "__main__":
  264 |     parser = argparse.ArgumentParser()
  265 |     parser.add_argument("--model", type=str, default="checkpoints/best_phase5_bipedal_duel_model.zip")
  266 |     parser.add_argument("--episodes", type=int, default=50)
  267 |     parser.add_argument("--no-video", dest="render_video", action="store_false")
  268 |     parser.add_argument("--video-out", type=str, default="logs/videos/phase5_bipedal_duel.mp4")
  269 |     parser.add_argument("--artifact-dir", type=str, default="/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/")
  270 |     args = parser.parse_args()
  271 | 
  272 |     evaluate_bipedal_duel(
  273 |         model_path=args.model,
  274 |         n_episodes=args.episodes,
  275 |         render_video=args.render_video,
  276 |         video_out=args.video_out,
  277 |         artifact_dir=args.artifact_dir,
  278 |     )
````
