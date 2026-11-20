# bipedal/scripts/eval_hardened_batter.py

원본: [scripts/eval_hardened_batter.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/eval_hardened_batter.py)

SHA256: `0eeeed75200244d3850a9dc51d60b67c335dadf542b8fe3330ad23fafb284411`

전체 157행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate_hardened_batter` | FunctionDef | 21 | 147 |

## 전체 원문

````text
    1 | """
    2 | Evaluation and Video Rendering for Phase 2: Sim-to-Real Hardened Batting.
    3 | Benchmarks the policy across 50 test episodes under latency buffers,
    4 | motor torque saturation, and domain randomization (bat mass +/-10%, sensor jitter).
    5 | """
    6 | 
    7 | import os
    8 | import sys
    9 | import argparse
   10 | import numpy as np
   11 | import cv2
   12 | 
   13 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   14 | if BASE_DIR not in sys.path:
   15 |     sys.path.insert(0, BASE_DIR)
   16 | 
   17 | from stable_baselines3 import PPO
   18 | from envs.hardened_batting_env import HardenedBattingEnv
   19 | 
   20 | 
   21 | def evaluate_hardened_batter(model_path="checkpoints/best_phase2_hardened_model.zip", n_episodes=50, render_videos=True):
   22 |     print("=" * 60)
   23 |     print(f"Benchmarking Phase 2 Hardened Batter AI: {model_path}")
   24 |     print(f"Total Test Episodes: {n_episodes} (with Latency + Domain Randomization)")
   25 |     print("=" * 60)
   26 | 
   27 |     if not os.path.exists(model_path):
   28 |         raise FileNotFoundError(f"Model checkpoint not found at {model_path}")
   29 | 
   30 |     model = PPO.load(model_path)
   31 |     env = HardenedBattingEnv(
   32 |         render_mode="rgb_array" if render_videos else None,
   33 |         latency_steps=1,
   34 |         enable_domain_randomization=True
   35 |     )
   36 | 
   37 |     contacts = 0
   38 |     fair_hits = 0
   39 |     sweet_offsets = []
   40 |     az_errors = []
   41 |     la_errors = []
   42 |     exit_speeds = []
   43 | 
   44 |     pull_cnt, pull_hit = 0, 0
   45 |     center_cnt, center_hit = 0, 0
   46 |     push_cnt, push_hit = 0, 0
   47 | 
   48 |     video_frames = {"pull": [], "center": [], "push": []}
   49 |     video_saved = {"pull": False, "center": False, "push": False}
   50 | 
   51 |     os.makedirs("logs/videos", exist_ok=True)
   52 | 
   53 |     for ep in range(n_episodes):
   54 |         obs, _ = env.reset(seed=12000 + ep)
   55 |         done = False
   56 |         last_info = {}
   57 |         frames = []
   58 | 
   59 |         target_az = np.degrees(env.target_azimuth_rad)
   60 |         if target_az < -10.0:
   61 |             cat = "pull"
   62 |             pull_cnt += 1
   63 |         elif target_az > 10.0:
   64 |             cat = "push"
   65 |             push_cnt += 1
   66 |         else:
   67 |             cat = "center"
   68 |             center_cnt += 1
   69 | 
   70 |         while not done:
   71 |             action, _ = model.predict(obs, deterministic=True)
   72 |             obs, reward, terminated, truncated, info = env.step(action)
   73 |             done = terminated or truncated
   74 |             last_info = info
   75 | 
   76 |             if render_videos and not video_saved[cat]:
   77 |                 frame = env.render()
   78 |                 if frame is not None:
   79 |                     hud = frame.copy()
   80 |                     bat_m = float(env.model.body_mass[env.bat_body_id])
   81 |                     cv2.putText(hud, f"Phase 2 Hardened (Latency: 20ms, Mass: {bat_m:.2f}kg)", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
   82 |                     cv2.putText(hud, f"Goal: {cat.upper()} ({target_az:+.1f} deg)", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
   83 |                     if info.get("contact", False):
   84 |                         spd = info.get("exit_speed_kmh", 0.0)
   85 |                         cv2.putText(hud, f"IMPACT! Speed: {spd:.1f} km/h", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
   86 |                     frames.append(hud)
   87 | 
   88 |         if last_info.get("contact", False):
   89 |             contacts += 1
   90 |             sweet_offsets.append(last_info.get("sweet_spot_offset_cm", 99.0))
   91 |             exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
   92 | 
   93 |             if last_info.get("fair_hit", False):
   94 |                 fair_hits += 1
   95 |                 az_err = last_info.get("azimuth_error_deg", 99.0)
   96 |                 la_err = last_info.get("launch_error_deg", 99.0)
   97 |                 az_errors.append(az_err)
   98 |                 la_errors.append(la_err)
   99 | 
  100 |                 if az_err < 25.0:
  101 |                     if cat == "pull":
  102 |                         pull_hit += 1
  103 |                     elif cat == "push":
  104 |                         push_hit += 1
  105 |                     else:
  106 |                         center_hit += 1
  107 | 
  108 |         if render_videos and not video_saved[cat] and len(frames) > 0 and last_info.get("fair_hit", False):
  109 |             video_frames[cat] = frames
  110 |             video_saved[cat] = True
  111 | 
  112 |     if render_videos:
  113 |         for cat in ["pull", "center", "push"]:
  114 |             if len(video_frames[cat]) > 0:
  115 |                 out_path = f"logs/videos/phase2_{cat}_hit.mp4"
  116 |                 h, w, _ = video_frames[cat][0].shape
  117 |                 fourcc = cv2.VideoWriter_fourcc(*"mp4v")
  118 |                 writer = cv2.VideoWriter(out_path, fourcc, 50, (w, h))
  119 |                 for f in video_frames[cat]:
  120 |                     writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
  121 |                 writer.release()
  122 |                 print(f"Saved hardened video: {out_path} ({len(video_frames[cat])} frames)")
  123 | 
  124 |     contact_rate = (contacts / n_episodes) * 100.0
  125 |     fair_rate = (fair_hits / n_episodes) * 100.0
  126 |     mean_offset = np.mean(sweet_offsets) if sweet_offsets else 99.0
  127 |     mean_az_err = np.mean(az_errors) if az_errors else 99.0
  128 |     mean_la_err = np.mean(la_errors) if la_errors else 99.0
  129 |     mean_spd = np.mean(exit_speeds) if exit_speeds else 0.0
  130 | 
  131 |     print("\n" + "=" * 70)
  132 |     print("      PHASE 2 HARDENED BATTER SIM-TO-REAL BENCHMARK")
  133 |     print("=" * 70)
  134 |     print(f"Contact Success Rate   : {contact_rate:.1f}% ({contacts}/{n_episodes})")
  135 |     print(f"Forward Fair-Hit Rate  : {fair_rate:.1f}% ({fair_hits}/{n_episodes})")
  136 |     print(f"Sweet Spot Offset (MAE): {mean_offset:.2f} cm")
  137 |     print(f"Azimuth Error (MAE)    : {mean_az_err:.2f}°")
  138 |     print(f"Launch Angle Error     : {mean_la_err:.2f}°")
  139 |     print(f"Mean Exit Velocity     : {mean_spd:.1f} km/h")
  140 |     print("-" * 70)
  141 |     print(f"  Pull-hit Accuracy    : {(pull_hit / max(1, pull_cnt))*100:.1f}% ({pull_hit}/{pull_cnt})")
  142 |     print(f"  Center-hit Accuracy  : {(center_hit / max(1, center_cnt))*100:.1f}% ({center_hit}/{center_cnt})")
  143 |     print(f"  Push-hit Accuracy    : {(push_hit / max(1, push_cnt))*100:.1f}% ({push_hit}/{push_cnt})")
  144 |     print("=" * 70)
  145 | 
  146 |     env.close()
  147 |     return contact_rate, fair_rate, mean_az_err
  148 | 
  149 | 
  150 | if __name__ == "__main__":
  151 |     parser = argparse.ArgumentParser()
  152 |     parser.add_argument("--model", type=str, default="checkpoints/best_phase2_hardened_model.zip")
  153 |     parser.add_argument("--episodes", type=int, default=50)
  154 |     parser.add_argument("--no-video", action="store_true")
  155 |     args = parser.parse_args()
  156 | 
  157 |     evaluate_hardened_batter(model_path=args.model, n_episodes=args.episodes, render_videos=not args.no_video)
````
