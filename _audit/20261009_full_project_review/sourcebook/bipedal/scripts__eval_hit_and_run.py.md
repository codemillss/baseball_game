# bipedal/scripts/eval_hit_and_run.py

원본: [scripts/eval_hit_and_run.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/eval_hit_and_run.py)

SHA256: `6178e61f865da857ae96196f519e53489ed737bb673c99ccf01bbd6fb7a56908`

전체 128행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate_hit_and_run` | FunctionDef | 22 | 118 |

## 전체 원문

````text
    1 | """
    2 | Evaluation and Video Rendering Pipeline for Phase 4: Hit-and-Run Locomotion Transition.
    3 | Benchmarks the 19-DoF floating-base H1 policy over 50 test episodes,
    4 | logs balance rate, contact rate, fair hit rate, bat release, sprint distance,
    5 | and renders tracking broadcast video.
    6 | """
    7 | 
    8 | import os
    9 | import sys
   10 | import argparse
   11 | import numpy as np
   12 | import cv2
   13 | 
   14 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   15 | if BASE_DIR not in sys.path:
   16 |     sys.path.insert(0, BASE_DIR)
   17 | 
   18 | from stable_baselines3 import PPO
   19 | from envs.hit_and_run_env import HitAndRunEnv
   20 | 
   21 | 
   22 | def evaluate_hit_and_run(model_path="checkpoints/best_phase4_hit_and_run_model.zip", n_episodes=50, render_videos=True):
   23 |     print("=" * 65)
   24 |     print(f"Benchmarking Phase 4 Hit-and-Run Transition AI: {model_path}")
   25 |     print(f"Total Test Episodes: {n_episodes} (Full 6-DoF Pelvis Freejoint + Bat Drop)")
   26 |     print("=" * 65)
   27 | 
   28 |     if not os.path.exists(model_path):
   29 |         raise FileNotFoundError(f"Model checkpoint not found at {model_path}")
   30 | 
   31 |     model = PPO.load(model_path)
   32 |     env = HitAndRunEnv(render_mode="rgb_array" if render_videos else None)
   33 | 
   34 |     balanced = 0
   35 |     contacts = 0
   36 |     fair_hits = 0
   37 |     bat_releases = 0
   38 |     distances_traveled = []
   39 |     exit_speeds = []
   40 |     video_frames = []
   41 | 
   42 |     os.makedirs("logs/videos", exist_ok=True)
   43 | 
   44 |     for ep in range(n_episodes):
   45 |         obs, _ = env.reset(seed=22000 + ep)
   46 |         done = False
   47 |         last_info = {}
   48 |         frames = []
   49 | 
   50 |         while not done:
   51 |             action, _ = model.predict(obs, deterministic=True)
   52 |             obs, reward, terminated, truncated, info = env.step(action)
   53 |             done = terminated or truncated
   54 |             last_info = info
   55 | 
   56 |             if render_videos and len(video_frames) == 0:
   57 |                 frame = env.render(camera_name="run_tracking_cam")
   58 |                 if frame is not None:
   59 |                     hud = frame.copy()
   60 |                     pz = last_info.get("pelvis_z", 0.88)
   61 |                     d_1b = last_info.get("dist_to_1b", 9.8)
   62 |                     d_tr = last_info.get("dist_traveled", 0.0)
   63 |                     cv2.putText(hud, f"Phase 4 Hit & Run (Pelvis: {pz:.2f}m | 1B Dist: {d_1b:.2f}m)", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 255, 255), 2)
   64 |                     
   65 |                     if last_info.get("contact", False):
   66 |                         spd = last_info.get("exit_speed_kmh", 0.0)
   67 |                         fair_str = "FAIR" if last_info.get("fair_hit", False) else "FOUL"
   68 |                         cv2.putText(hud, f"HIT: {fair_str} ({spd:.1f} km/h)", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 255, 0), 2)
   69 |                     
   70 |                     if last_info.get("bat_released", False):
   71 |                         cv2.putText(hud, f"BAT DROPPED! SPRINT TO 1ST BASE (+{d_tr:.2f}m)", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (255, 128, 0), 2)
   72 | 
   73 |                     frames.append(hud)
   74 | 
   75 |         if not last_info.get("has_fallen", False):
   76 |             balanced += 1
   77 |         if last_info.get("contact", False):
   78 |             contacts += 1
   79 |             exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
   80 |         if last_info.get("fair_hit", False):
   81 |             fair_hits += 1
   82 |         if last_info.get("bat_released", False):
   83 |             bat_releases += 1
   84 |         distances_traveled.append(last_info.get("dist_traveled", 0.0))
   85 | 
   86 |         if render_videos and len(video_frames) == 0 and last_info.get("fair_hit", False) and last_info.get("bat_released", False):
   87 |             video_frames = frames
   88 | 
   89 |     if render_videos and len(video_frames) > 0:
   90 |         out_path = "logs/videos/phase4_hit_and_run.mp4"
   91 |         h, w, _ = video_frames[0].shape
   92 |         fourcc = cv2.VideoWriter_fourcc(*"mp4v")
   93 |         writer = cv2.VideoWriter(out_path, fourcc, 50, (w, h))
   94 |         for f in video_frames:
   95 |             writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
   96 |         writer.release()
   97 |         print(f"Saved Hit & Run video: {out_path} ({len(video_frames)} frames)")
   98 | 
   99 |     balance_rate = (balanced / n_episodes) * 100.0
  100 |     contact_rate = (contacts / n_episodes) * 100.0
  101 |     fair_rate = (fair_hits / n_episodes) * 100.0
  102 |     bat_rel_rate = (bat_releases / n_episodes) * 100.0
  103 |     mean_dist = float(np.mean(distances_traveled)) if distances_traveled else 0.0
  104 |     mean_spd = float(np.mean(exit_speeds)) if exit_speeds else 0.0
  105 | 
  106 |     print("\n" + "=" * 70)
  107 |     print("      PHASE 4 HIT-AND-RUN LOCOMOTION TRANSITION BENCHMARK")
  108 |     print("=" * 70)
  109 |     print(f"Bipedal Balance Rate     : {balance_rate:.1f}% ({balanced}/{n_episodes})")
  110 |     print(f"Contact Success Rate     : {contact_rate:.1f}% ({contacts}/{n_episodes})")
  111 |     print(f"Forward Fair-Hit Rate    : {fair_rate:.1f}% ({fair_hits}/{n_episodes})")
  112 |     print(f"Bat Release Rate         : {bat_rel_rate:.1f}% ({bat_releases}/{n_episodes})")
  113 |     print(f"Mean 1B Sprint Distance  : {mean_dist:.2f} m")
  114 |     print(f"Mean Ball Exit Velocity  : {mean_spd:.1f} km/h")
  115 |     print("=" * 70)
  116 | 
  117 |     env.close()
  118 |     return balance_rate, contact_rate, fair_rate, bat_rel_rate, mean_dist
  119 | 
  120 | 
  121 | if __name__ == "__main__":
  122 |     parser = argparse.ArgumentParser()
  123 |     parser.add_argument("--model", type=str, default="checkpoints/best_phase4_hit_and_run_model.zip")
  124 |     parser.add_argument("--episodes", type=int, default=50)
  125 |     parser.add_argument("--no-video", action="store_true")
  126 |     args = parser.parse_args()
  127 | 
  128 |     evaluate_hit_and_run(model_path=args.model, n_episodes=args.episodes, render_videos=not args.no_video)
````
