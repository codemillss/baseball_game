# bipedal/scripts/eval_pitcher.py

원본: [scripts/eval_pitcher.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/eval_pitcher.py)

SHA256: `3da65a8552183a264680527543460691b5b34c748e4af495145347c0c947ff79`

전체 140행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate_pitcher` | FunctionDef | 21 | 130 |

## 전체 원문

````text
    1 | """
    2 | Evaluation and Video Rendering Pipeline for Goal-Conditioned Pitcher AI.
    3 | Evaluates the trained policy over 50 test episodes, logs quantitative metrics,
    4 | and renders multi-angle videos for Fastball, Slider, and Curveball pitches.
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
   18 | from envs.pitcher_precision_env import PitcherPrecisionEnv
   19 | 
   20 | 
   21 | def evaluate_pitcher(model_path="checkpoints/best_pitcher_model.zip", n_episodes=50, render_videos=True):
   22 |     print("=" * 60)
   23 |     print(f"Benchmarking Pitcher AI: {model_path}")
   24 |     print(f"Total Test Episodes: {n_episodes}")
   25 |     print("=" * 60)
   26 | 
   27 |     if not os.path.exists(model_path):
   28 |         raise FileNotFoundError(f"Model checkpoint not found at {model_path}")
   29 | 
   30 |     model = PPO.load(model_path)
   31 |     env = PitcherPrecisionEnv(render_mode="rgb_array" if render_videos else None)
   32 | 
   33 |     strikes = 0
   34 |     reached = 0
   35 |     errors_cm = []
   36 |     speeds_kmh = []
   37 | 
   38 |     type_stats = {
   39 |         0: {"name": "Fastball", "total": 0, "strikes": 0, "errors": [], "speeds": []},
   40 |         1: {"name": "Slider",   "total": 0, "strikes": 0, "errors": [], "speeds": []},
   41 |         2: {"name": "Curveball","total": 0, "strikes": 0, "errors": [], "speeds": []},
   42 |     }
   43 | 
   44 |     # Video storage
   45 |     video_frames = {0: [], 1: [], 2: []}
   46 |     video_saved = {0: False, 1: False, 2: False}
   47 | 
   48 |     os.makedirs("logs/videos", exist_ok=True)
   49 | 
   50 |     for ep in range(n_episodes):
   51 |         obs, _ = env.reset(seed=9000 + ep)
   52 |         ptype = env.pitch_type
   53 |         type_stats[ptype]["total"] += 1
   54 |         done = False
   55 |         last_info = {}
   56 |         frames = []
   57 | 
   58 |         while not done:
   59 |             action, _ = model.predict(obs, deterministic=True)
   60 |             obs, reward, terminated, truncated, info = env.step(action)
   61 |             done = terminated or truncated
   62 |             last_info = info
   63 | 
   64 |             if render_videos and not video_saved[ptype]:
   65 |                 frame = env.render()
   66 |                 if frame is not None:
   67 |                     # Draw HUD overlay
   68 |                     hud = frame.copy()
   69 |                     ptype_name = type_stats[ptype]["name"]
   70 |                     tx, tz = env.target_x, env.target_z
   71 |                     bpos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
   72 |                     spd = info.get("release_speed_kmh", 0.0)
   73 | 
   74 |                     cv2.putText(hud, f"Pitch: {ptype_name}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
   75 |                     cv2.putText(hud, f"Target: [{tx:+.2f}, {tz:.2f}]m", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
   76 |                     cv2.putText(hud, f"Speed : {spd:.1f} km/h", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
   77 |                     frames.append(hud)
   78 | 
   79 |         if last_info.get("reached_plate", False):
   80 |             reached += 1
   81 |             err = last_info.get("dist_error_cm", 99.0)
   82 |             spd = last_info.get("release_speed_kmh", 0.0)
   83 |             errors_cm.append(err)
   84 |             speeds_kmh.append(spd)
   85 |             type_stats[ptype]["errors"].append(err)
   86 |             type_stats[ptype]["speeds"].append(spd)
   87 | 
   88 |             if last_info.get("is_strike", False):
   89 |                 strikes += 1
   90 |                 type_stats[ptype]["strikes"] += 1
   91 | 
   92 |         if render_videos and not video_saved[ptype] and len(frames) > 0:
   93 |             video_frames[ptype] = frames
   94 |             video_saved[ptype] = True
   95 | 
   96 |     # Save representative videos
   97 |     if render_videos:
   98 |         for ptype, name in [(0, "fastball"), (1, "slider"), (2, "curveball")]:
   99 |             if len(video_frames[ptype]) > 0:
  100 |                 out_path = f"logs/videos/pitcher_{name}.mp4"
  101 |                 h, w, _ = video_frames[ptype][0].shape
  102 |                 fourcc = cv2.VideoWriter_fourcc(*"mp4v")
  103 |                 writer = cv2.VideoWriter(out_path, fourcc, 50, (w, h))
  104 |                 for f in video_frames[ptype]:
  105 |                     writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
  106 |                 writer.release()
  107 |                 print(f"Saved evaluation video: {out_path} ({len(video_frames[ptype])} frames)")
  108 | 
  109 |     # Print Quantitative Summary Table
  110 |     overall_strike_rate = (strikes / n_episodes) * 100.0
  111 |     overall_mae = np.mean(errors_cm) if errors_cm else 99.0
  112 |     overall_speed = np.mean(speeds_kmh) if speeds_kmh else 0.0
  113 | 
  114 |     print("\n" + "=" * 70)
  115 |     print("           PITCHER EVALUATION BENCHMARK RESULTS")
  116 |     print("=" * 70)
  117 |     print(f"Overall Strike Rate     : {overall_strike_rate:.1f}% ({strikes}/{n_episodes})")
  118 |     print(f"Mean Target Error (MAE) : {overall_mae:.2f} cm")
  119 |     print(f"Mean Pitch Speed        : {overall_speed:.1f} km/h")
  120 |     print("-" * 70)
  121 |     for pt in [0, 1, 2]:
  122 |         s = type_stats[pt]
  123 |         rate = (s["strikes"] / max(1, s["total"])) * 100.0
  124 |         mae = np.mean(s["errors"]) if s["errors"] else 99.0
  125 |         spd = np.mean(s["speeds"]) if s["speeds"] else 0.0
  126 |         print(f"  {s['name']:10s} Strike Rate : {rate:5.1f}% ({s['strikes']:2d}/{s['total']:2d}) | MAE: {mae:5.2f} cm | Speed: {spd:5.1f} km/h")
  127 |     print("=" * 70)
  128 | 
  129 |     env.close()
  130 |     return overall_strike_rate, overall_mae
  131 | 
  132 | 
  133 | if __name__ == "__main__":
  134 |     parser = argparse.ArgumentParser()
  135 |     parser.add_argument("--model", type=str, default="checkpoints/best_pitcher_model.zip")
  136 |     parser.add_argument("--episodes", type=int, default=50)
  137 |     parser.add_argument("--no-video", action="store_true")
  138 |     args = parser.parse_args()
  139 | 
  140 |     evaluate_pitcher(model_path=args.model, n_episodes=args.episodes, render_videos=not args.no_video)
````
