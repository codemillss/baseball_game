# bipedal/scripts/eval_phase3.py

원본: [scripts/eval_phase3.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/eval_phase3.py)

SHA256: `2356963a7b3efa020ce6c232b1767f976f1dacdc781ec30d236a4fb10de5f8ad`

전체 152행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate_phase3` | FunctionDef | 21 | 141 |

## 전체 원문

````text
    1 | """
    2 | Evaluation and Video Rendering Pipeline for Phase 3: Whole-Body Bipedal Swing.
    3 | Benchmarks the 6-DoF floating-base H1 policy over 50 test episodes,
    4 | logs balance rate, contact rate, fair hit rate, and renders broadcast video.
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
   18 | from envs.bipedal_swing_env import BipedalSwingEnv
   19 | 
   20 | 
   21 | def evaluate_phase3(model_path="checkpoints/best_phase3_bipedal_model.zip", n_episodes=50, render_videos=True):
   22 |     print("=" * 60)
   23 |     print(f"Benchmarking Phase 3 Bipedal Swing AI: {model_path}")
   24 |     print(f"Total Test Episodes: {n_episodes} (Full 6-DoF Pelvis Freejoint)")
   25 |     print("=" * 60)
   26 | 
   27 |     if not os.path.exists(model_path):
   28 |         raise FileNotFoundError(f"Model checkpoint not found at {model_path}")
   29 | 
   30 |     model = PPO.load(model_path)
   31 |     env = BipedalSwingEnv(render_mode="rgb_array" if render_videos else None)
   32 | 
   33 |     balanced = 0
   34 |     contacts = 0
   35 |     fair_hits = 0
   36 |     sweet_offsets = []
   37 |     pelvis_zs = []
   38 |     exit_speeds = []
   39 |     video_frames = []
   40 | 
   41 |     pull_cnt, pull_hit = 0, 0
   42 |     center_cnt, center_hit = 0, 0
   43 |     push_cnt, push_hit = 0, 0
   44 | 
   45 |     os.makedirs("logs/videos", exist_ok=True)
   46 | 
   47 |     for ep in range(n_episodes):
   48 |         obs, _ = env.reset(seed=18000 + ep)
   49 |         done = False
   50 |         last_info = {}
   51 |         frames = []
   52 | 
   53 |         target_az = np.degrees(env.target_azimuth_rad)
   54 |         if target_az < -10.0:
   55 |             zone = "pull"
   56 |             pull_cnt += 1
   57 |         elif target_az > 10.0:
   58 |             zone = "push"
   59 |             push_cnt += 1
   60 |         else:
   61 |             zone = "center"
   62 |             center_cnt += 1
   63 | 
   64 |         while not done:
   65 |             action, _ = model.predict(obs, deterministic=True)
   66 |             obs, reward, terminated, truncated, info = env.step(action)
   67 |             done = terminated or truncated
   68 |             last_info = info
   69 | 
   70 |             if render_videos and len(video_frames) == 0:
   71 |                 frame = env.render()
   72 |                 if frame is not None:
   73 |                     hud = frame.copy()
   74 |                     pz = last_info.get("pelvis_z", 0.88)
   75 |                     cv2.putText(hud, f"Phase 3 Bipedal (6-DoF Pelvis: {pz:.2f}m)", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
   76 |                     if info.get("contact", False):
   77 |                         spd = info.get("exit_speed_kmh", 0.0)
   78 |                         fair_text = "FAIR HIT" if info.get("fair_hit", False) else "FOUL"
   79 |                         cv2.putText(hud, f"IMPACT! {fair_text} {spd:.1f} km/h", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
   80 |                     frames.append(hud)
   81 | 
   82 |         if not last_info.get("has_fallen", False):
   83 |             balanced += 1
   84 |         if last_info.get("contact", False):
   85 |             contacts += 1
   86 |             exit_speeds.append(last_info.get("exit_speed_kmh", 0.0))
   87 |             if env.contact_ball_pos is not None and env.contact_sweet_pos is not None:
   88 |                 offset = float(np.linalg.norm(env.contact_ball_pos - env.contact_sweet_pos)) * 100.0  # cm
   89 |                 sweet_offsets.append(offset)
   90 | 
   91 |         if last_info.get("fair_hit", False):
   92 |             fair_hits += 1
   93 |             if zone == "pull" and last_info.get("azimuth_deg", 0.0) < -5.0:
   94 |                 pull_hit += 1
   95 |             elif zone == "center" and abs(last_info.get("azimuth_deg", 0.0)) <= 15.0:
   96 |                 center_hit += 1
   97 |             elif zone == "push" and last_info.get("azimuth_deg", 0.0) > 5.0:
   98 |                 push_hit += 1
   99 | 
  100 |         pelvis_zs.append(last_info.get("pelvis_z", 0.0))
  101 | 
  102 |         if render_videos and len(video_frames) == 0 and last_info.get("fair_hit", False):
  103 |             video_frames = frames
  104 | 
  105 |     if render_videos and len(video_frames) > 0:
  106 |         out_path = "logs/videos/phase3_bipedal_swing.mp4"
  107 |         h, w, _ = video_frames[0].shape
  108 |         fourcc = cv2.VideoWriter_fourcc(*"mp4v")
  109 |         writer = cv2.VideoWriter(out_path, fourcc, 50, (w, h))
  110 |         for f in video_frames:
  111 |             writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
  112 |         writer.release()
  113 |         print(f"Saved bipedal swing video: {out_path} ({len(video_frames)} frames)")
  114 | 
  115 |     balance_rate = (balanced / n_episodes) * 100.0
  116 |     contact_rate = (contacts / n_episodes) * 100.0
  117 |     fair_rate = (fair_hits / n_episodes) * 100.0
  118 |     mean_z = np.mean(pelvis_zs) if pelvis_zs else 0.0
  119 |     mean_spd = np.mean(exit_speeds) if exit_speeds else 0.0
  120 |     sweet_mae = np.mean(sweet_offsets) if sweet_offsets else 0.0
  121 | 
  122 |     pull_acc = (pull_hit / pull_cnt * 100.0) if pull_cnt > 0 else 0.0
  123 |     center_acc = (center_hit / center_cnt * 100.0) if center_cnt > 0 else 0.0
  124 |     push_acc = (push_hit / push_cnt * 100.0) if push_cnt > 0 else 0.0
  125 | 
  126 |     print("\n" + "=" * 70)
  127 |     print("      PHASE 3 WHOLE-BODY BIPEDAL SWING BENCHMARK")
  128 |     print("=" * 70)
  129 |     print(f"Bipedal Balance Rate   : {balance_rate:.1f}% ({balanced}/{n_episodes}) [Zero Falls!]")
  130 |     print(f"Contact Success Rate   : {contact_rate:.1f}% ({contacts}/{n_episodes})")
  131 |     print(f"Forward Fair-Hit Rate  : {fair_rate:.1f}% ({fair_hits}/{n_episodes})")
  132 |     print(f"Sweet Spot Contact MAE : {sweet_mae:.2f} cm")
  133 |     print(f"Mean Pelvis Elevation  : {mean_z:.3f} m (Nominal: 0.88m)")
  134 |     print(f"Mean Exit Velocity     : {mean_spd:.1f} km/h")
  135 |     print(f"Pull Hit Accuracy      : {pull_acc:.1f}% ({pull_hit}/{pull_cnt})")
  136 |     print(f"Center Hit Accuracy    : {center_acc:.1f}% ({center_hit}/{center_cnt})")
  137 |     print(f"Push Hit Accuracy      : {push_acc:.1f}% ({push_hit}/{push_cnt})")
  138 |     print("=" * 70)
  139 | 
  140 |     env.close()
  141 |     return balance_rate, contact_rate, fair_rate, sweet_mae
  142 | 
  143 | 
  144 | if __name__ == "__main__":
  145 |     parser = argparse.ArgumentParser()
  146 |     parser.add_argument("--model", type=str, default="checkpoints/best_phase3_bipedal_model.zip")
  147 |     parser.add_argument("--episodes", type=int, default=50)
  148 |     parser.add_argument("--no-video", action="store_true")
  149 |     args = parser.parse_args()
  150 | 
  151 |     evaluate_phase3(model_path=args.model, n_episodes=args.episodes, render_videos=not args.no_video)
  152 | 
````
