# bipedal/scripts/eval_battery.py

원본: [scripts/eval_battery.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/eval_battery.py)

SHA256: `5b8471331c75c8f2cbf67dce0ba393d25d4aabf7e5bce58ffa24c9cfb45c15a4`

전체 172행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate` | FunctionDef | 12 | 166 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | sys.path.append(os.path.abspath("."))
    4 | 
    5 | import argparse
    6 | import csv
    7 | import numpy as np
    8 | import cv2
    9 | from stable_baselines3 import PPO
   10 | from envs.battery_pitch_catch_env import BatteryPitchCatchEnv
   11 | 
   12 | def evaluate(episodes=50, render_video=True):
   13 |     os.makedirs("logs/videos", exist_ok=True)
   14 |     os.makedirs("logs", exist_ok=True)
   15 | 
   16 |     env = BatteryPitchCatchEnv(render_mode="rgb_array")
   17 | 
   18 |     model_path = "checkpoints/best_battery_model.zip"
   19 |     if not os.path.exists(model_path):
   20 |         model_path = "checkpoints/final_battery_model.zip"
   21 | 
   22 |     model = None
   23 |     if os.path.exists(model_path):
   24 |         print(f"Loading trained policy from {model_path}...")
   25 |         model = PPO.load(model_path, env=env)
   26 |     else:
   27 |         print("Model checkpoint not found, running with zero action baseline.")
   28 | 
   29 |     records = []
   30 |     video_frames = []
   31 |     capture_frames = {}
   32 | 
   33 |     print(f"\n--- Starting Battery Benchmark: {episodes} Episodes ---")
   34 |     for ep in range(episodes):
   35 |         obs, info = env.reset(seed=ep * 100 + 42)
   36 |         done = False
   37 |         ep_reward = 0.0
   38 |         step = 0
   39 | 
   40 |         while not done:
   41 |             if model is not None:
   42 |                 action, _ = model.predict(obs, deterministic=True)
   43 |             else:
   44 |                 action = np.zeros(5, dtype=np.float32)
   45 | 
   46 |             obs, reward, terminated, truncated, step_info = env.step(action)
   47 |             ep_reward += reward
   48 |             step += 1
   49 | 
   50 |             if render_video and ep == 0:
   51 |                 frame = env.render()
   52 |                 ball_pos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
   53 |                 mitt_pos = env.data.site_xpos[env.c_mitt_site_id]
   54 |                 dist_mitt = float(np.linalg.norm(ball_pos - mitt_pos))
   55 |                 c_z = float(env.data.qpos[env.c_pelvis_qpos_adr + 2])
   56 | 
   57 |                 overlay = frame.copy()
   58 |                 cv2.rectangle(overlay, (0, 0), (640, 75), (20, 20, 20), -1)
   59 |                 cv2.rectangle(overlay, (0, 415), (640, 480), (20, 20, 20), -1)
   60 |                 cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
   61 | 
   62 |                 ptype = step_info["pitch_type"]
   63 |                 pspd = step_info["pitch_speed_kmh"]
   64 |                 pz = step_info["plate_cross_z"]
   65 |                 perr = step_info["framing_error_cm"]
   66 | 
   67 |                 cv2.putText(frame, "BATTERY DUEL: 10M PITCHER & 6-DoF CATCHER SQUAT", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
   68 |                 t_cur = (step * 0.02)
   69 |                 p_text = f"Time: {t_cur:.2f}s | {ptype} ({pspd:.1f} km/h) | Plate Z: {pz:.2f}m"
   70 |                 cv2.putText(frame, p_text, (15, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)
   71 | 
   72 |                 c_status = "STABLE SQUAT" if not step_info["catcher_fallen"] else "FALLEN"
   73 |                 b_status = "CAUGHT IN MITT!" if step_info["ball_caught"] else f"In-Flight (Mitt Dist: {dist_mitt*100:.1f}cm)"
   74 |                 call_text = "CALL: STRIKE" if step_info["is_strike"] else "CALL: BALL"
   75 |                 cv2.putText(frame, f"CATCHER: {c_status} (Z={c_z:.2f}m) | {call_text}", (15, 442), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 2)
   76 |                 res_col = (0, 255, 200) if step_info["ball_caught"] else (200, 200, 200)
   77 |                 cv2.putText(frame, f"RESULT: {b_status} | Framing Err: {perr:.1f}cm", (15, 468), cv2.FONT_HERSHEY_SIMPLEX, 0.44, res_col, 1)
   78 | 
   79 |                 video_frames.append(frame)
   80 | 
   81 |                 if step == 2:
   82 |                     capture_frames["release"] = frame.copy()
   83 |                 elif step == 12:
   84 |                     capture_frames["approach"] = frame.copy()
   85 |                 elif step_info["ball_caught"] and "catch" not in capture_frames:
   86 |                     capture_frames["catch"] = frame.copy()
   87 | 
   88 |             done = terminated or truncated
   89 | 
   90 |         if render_video and ep == 0 and "catch" not in capture_frames and len(video_frames) > 0:
   91 |             capture_frames["catch"] = video_frames[-1].copy()
   92 | 
   93 |         records.append({
   94 |             "episode": ep + 1,
   95 |             "pitch_type": step_info["pitch_type"],
   96 |             "pitch_speed_kmh": float(step_info["pitch_speed_kmh"]),
   97 |             "ball_caught": bool(step_info["ball_caught"]),
   98 |             "is_strike": bool(step_info["is_strike"]),
   99 |             "framing_error_cm": float(step_info["framing_error_cm"]),
  100 |             "catcher_fallen": bool(step_info["catcher_fallen"]),
  101 |             "catcher_pelvis_z": float(step_info["catcher_pelvis_z"]),
  102 |             "plate_cross_x": float(step_info["plate_cross_x"]),
  103 |             "plate_cross_z": float(step_info["plate_cross_z"]),
  104 |             "ep_reward": float(ep_reward)
  105 |         })
  106 | 
  107 |     csv_path = "logs/battery_benchmark_metrics.csv"
  108 |     keys = records[0].keys()
  109 |     with open(csv_path, "w", newline="") as f:
  110 |         writer = csv.DictWriter(f, fieldnames=keys)
  111 |         writer.writeheader()
  112 |         writer.writerows(records)
  113 |     print(f"\nSaved benchmark metrics to {csv_path}")
  114 | 
  115 |     total_eps = len(records)
  116 |     falls = sum(1 for r in records if r["catcher_fallen"])
  117 |     catches = sum(1 for r in records if r["ball_caught"])
  118 |     strikes = sum(1 for r in records if r["is_strike"])
  119 |     survival_rate = (1.0 - falls / total_eps) * 100.0
  120 |     catch_rate = (catches / total_eps) * 100.0
  121 |     strike_rate = (strikes / total_eps) * 100.0
  122 |     mean_framing_err = np.mean([r["framing_error_cm"] for r in records if r["ball_caught"]]) if catches > 0 else np.mean([r["framing_error_cm"] for r in records])
  123 |     mean_speed = np.mean([r["pitch_speed_kmh"] for r in records])
  124 |     mean_z = np.mean([r["catcher_pelvis_z"] for r in records])
  125 | 
  126 |     print("=" * 60)
  127 |     print("--- 50-EPISODE BATTERY BENCHMARK SUMMARY ---")
  128 |     print(f"Total Episodes:                {total_eps}")
  129 |     print(f"Catcher Squat Survival Rate:   {survival_rate:.1f}% ({total_eps - falls}/{total_eps})")
  130 |     print(f"Ball Catch Success Rate:       {catch_rate:.1f}% ({catches}/{total_eps})")
  131 |     print(f"Strike Zone Adherence Rate:    {strike_rate:.1f}% ({strikes}/{total_eps})")
  132 |     print(f"Mean Framing Error MAE:        {mean_framing_err:.2f} cm")
  133 |     print(f"Mean Pitch Speed:              {mean_speed:.1f} km/h")
  134 |     print(f"Mean Catcher Squat Pelvis Z:   {mean_z:.3f} m")
  135 |     print("=" * 60)
  136 | 
  137 |     # Breakdown by pitch type
  138 |     for ptype in ["Fastball", "Slider", "Curveball"]:
  139 |         p_recs = [r for r in records if r["pitch_type"] == ptype]
  140 |         if len(p_recs) > 0:
  141 |             p_cat = sum(1 for r in p_recs if r["ball_caught"]) / len(p_recs) * 100.0
  142 |             p_str = sum(1 for r in p_recs if r["is_strike"]) / len(p_recs) * 100.0
  143 |             p_sp = np.mean([r["pitch_speed_kmh"] for r in p_recs])
  144 |             p_er = np.mean([r["framing_error_cm"] for r in p_recs])
  145 |             print(f"[{ptype:>9}] Count: {len(p_recs):2d} | Catch: {p_cat:5.1f}% | Strike: {p_str:5.1f}% | Spd: {p_sp:4.1f} km/h | Err: {p_er:4.1f} cm")
  146 | 
  147 |     if render_video and len(video_frames) > 0:
  148 |         vid_path = "logs/videos/battery_pitch_catch.mp4"
  149 |         h, w, _ = video_frames[0].shape
  150 |         out = cv2.VideoWriter(vid_path, cv2.VideoWriter_fourcc(*"mp4v"), 50, (w, h))
  151 |         for f in video_frames:
  152 |             out.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
  153 |         out.release()
  154 |         print(f"\nSaved 50 FPS video to {vid_path}")
  155 | 
  156 |     keyframe_map = {
  157 |         "release": "logs/videos/battery_pitch_release.png",
  158 |         "approach": "logs/videos/battery_pitch_approach.png",
  159 |         "catch": "logs/videos/battery_mitt_catch.png"
  160 |     }
  161 |     for k, path in keyframe_map.items():
  162 |         if k in capture_frames:
  163 |             cv2.imwrite(path, cv2.cvtColor(capture_frames[k], cv2.COLOR_RGB2BGR))
  164 |             print(f"Saved keyframe: {path}")
  165 | 
  166 |     env.close()
  167 | 
  168 | if __name__ == "__main__":
  169 |     parser = argparse.ArgumentParser()
  170 |     parser.add_argument("--episodes", type=int, default=50)
  171 |     args = parser.parse_args()
  172 |     evaluate(episodes=args.episodes)
````
