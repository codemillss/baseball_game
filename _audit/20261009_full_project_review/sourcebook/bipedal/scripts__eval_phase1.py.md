# bipedal/scripts/eval_phase1.py

원본: [scripts/eval_phase1.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/eval_phase1.py)

SHA256: `0739b1bbc15238ab43522d621b46c036a7a8456c2f676b4c6a3d2f865247eb82`

전체 197행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate_policy` | FunctionDef | 29 | 181 |

## 전체 원문

````text
    1 | """
    2 | Evaluation & Quantitative Benchmark Script for Phase 1 Directional Batting.
    3 | Evaluates:
    4 | - Contact Success Rate (%) & Fair-Ball Forward Hit Rate (%)
    5 | - Sweet Spot Precision Offset (cm)
    6 | - Azimuth Directional Error (MAE in degrees)
    7 | - Launch Angle Error (MAE in degrees)
    8 | - Exit Velocity Distribution (m/s and km/h)
    9 | - Field Spray Chart Breakdown (Pull vs Center vs Push accuracy)
   10 | - High-definition multi-camera MP4 video recordings of fair hits.
   11 | """
   12 | 
   13 | import os
   14 | import sys
   15 | import argparse
   16 | import numpy as np
   17 | import imageio
   18 | 
   19 | # Ensure repository root is in sys.path
   20 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   21 | if BASE_DIR not in sys.path:
   22 |     sys.path.insert(0, BASE_DIR)
   23 | 
   24 | from stable_baselines3 import PPO
   25 | import gymnasium as gym
   26 | import envs
   27 | 
   28 | 
   29 | def evaluate_policy(
   30 |     model_path="checkpoints/best_phase1_model.zip",
   31 |     n_episodes=50,
   32 |     render_video=True,
   33 |     video_dir="logs/videos",
   34 |     seed=42,
   35 | ):
   36 |     os.makedirs(video_dir, exist_ok=True)
   37 | 
   38 |     print(f"📂 Loading model from: {model_path}")
   39 |     if os.path.exists(model_path):
   40 |         model = PPO.load(model_path)
   41 |     else:
   42 |         print(f"⚠️ Model path {model_path} not found. Using baseline actions.")
   43 |         model = None
   44 | 
   45 |     env = gym.make("DirectionalBatting-v0", render_mode="rgb_array")
   46 | 
   47 |     contacts = 0
   48 |     fair_hits = 0
   49 |     sweet_offsets = []
   50 |     azimuth_errors = []
   51 |     launch_errors = []
   52 |     exit_velocities = []
   53 | 
   54 |     pull_targets, pull_success = 0, 0
   55 |     center_targets, center_success = 0, 0
   56 |     push_targets, push_success = 0, 0
   57 | 
   58 |     record_categories = {"pull": None, "center": None, "push": None}
   59 | 
   60 |     print(f"🔬 Running {n_episodes} Quantitative Evaluation Episodes (Seed: {seed})...")
   61 | 
   62 |     for ep in range(n_episodes):
   63 |         obs, _ = env.reset(seed=seed + ep)
   64 |         done = False
   65 |         frames = []
   66 |         ep_contact = False
   67 |         ep_fair = False
   68 |         ep_info = {}
   69 | 
   70 |         target_azimuth_rad = obs[7]
   71 |         target_azimuth_deg = float(np.degrees(target_azimuth_rad))
   72 | 
   73 |         if target_azimuth_deg < -10.0:
   74 |             category = "pull"
   75 |             pull_targets += 1
   76 |         elif target_azimuth_deg > 10.0:
   77 |             category = "push"
   78 |             push_targets += 1
   79 |         else:
   80 |             category = "center"
   81 |             center_targets += 1
   82 | 
   83 |         while not done:
   84 |             if render_video and record_categories[category] is None:
   85 |                 frame = env.render()
   86 |                 if frame is not None:
   87 |                     frames.append(frame)
   88 | 
   89 |             if model is not None:
   90 |                 action, _ = model.predict(obs, deterministic=True)
   91 |             else:
   92 |                 action = np.zeros(5, dtype=np.float32)
   93 | 
   94 |             obs, reward, terminated, truncated, info = env.step(action)
   95 |             done = terminated or truncated
   96 | 
   97 |             if info.get("contact", False):
   98 |                 ep_contact = True
   99 |                 ep_info = info
  100 |             if info.get("fair_hit", False):
  101 |                 ep_fair = True
  102 | 
  103 |         if ep_contact:
  104 |             contacts += 1
  105 |             sweet_offsets.append(ep_info.get("sweet_spot_offset_cm", 99.0))
  106 |             exit_velocities.append(ep_info.get("exit_speed_ms", 0.0))
  107 | 
  108 |             if ep_fair:
  109 |                 fair_hits += 1
  110 |                 az_err = ep_info.get("azimuth_error_deg", 99.0)
  111 |                 la_err = ep_info.get("launch_error_deg", 99.0)
  112 |                 azimuth_errors.append(az_err)
  113 |                 launch_errors.append(la_err)
  114 | 
  115 |                 # Directional spray alignment criterion: within 25° of target
  116 |                 if az_err < 25.0:
  117 |                     if category == "pull":
  118 |                         pull_success += 1
  119 |                     elif category == "push":
  120 |                         push_success += 1
  121 |                     else:
  122 |                         center_success += 1
  123 | 
  124 |                 # Save video if this is the first fair hit for this category
  125 |                 if render_video and record_categories[category] is None and len(frames) > 0:
  126 |                     record_categories[category] = frames
  127 | 
  128 |     # Save rendered video clips
  129 |     for cat_name, cat_frames in record_categories.items():
  130 |         if cat_frames is not None and len(cat_frames) > 0:
  131 |             vid_path = os.path.join(video_dir, f"phase1_{cat_name}_hit.mp4")
  132 |             imageio.mimsave(vid_path, cat_frames, fps=30)
  133 |             print(f"🎥 Saved demonstration video: {vid_path}")
  134 | 
  135 |     # Compute Aggregate Metrics
  136 |     contact_rate = (contacts / n_episodes) * 100.0
  137 |     fair_rate = (fair_hits / n_episodes) * 100.0
  138 |     mean_sweet = float(np.mean(sweet_offsets)) if sweet_offsets else 0.0
  139 |     std_sweet = float(np.std(sweet_offsets)) if sweet_offsets else 0.0
  140 |     mean_az_err = float(np.mean(azimuth_errors)) if azimuth_errors else 0.0
  141 |     std_az_err = float(np.std(azimuth_errors)) if azimuth_errors else 0.0
  142 |     mean_la_err = float(np.mean(launch_errors)) if launch_errors else 0.0
  143 |     std_la_err = float(np.std(launch_errors)) if launch_errors else 0.0
  144 |     mean_vel = float(np.mean(exit_velocities)) if exit_velocities else 0.0
  145 |     max_vel = float(np.max(exit_velocities)) if exit_velocities else 0.0
  146 | 
  147 |     pull_acc = (pull_success / max(1, pull_targets)) * 100.0
  148 |     center_acc = (center_success / max(1, center_targets)) * 100.0
  149 |     push_acc = (push_success / max(1, push_targets)) * 100.0
  150 | 
  151 |     print("\n" + "=" * 65)
  152 |     print("🏆 PHASE 1 QUANTITATIVE BENCHMARK REPORT")
  153 |     print("=" * 65)
  154 |     print(f"Episodes Evaluated:         {n_episodes}")
  155 |     print(f"Contact Success Rate:       {contact_rate:.1f}% ({contacts}/{n_episodes})")
  156 |     print(f"Fair-Ball Forward Hit Rate: {fair_rate:.1f}% ({fair_hits}/{n_episodes})")
  157 |     print(f"Sweet Spot Offset:          {mean_sweet:.2f} ± {std_sweet:.2f} cm")
  158 |     print(f"Azimuth Error (MAE):        {mean_az_err:.2f}° ± {std_az_err:.2f}°")
  159 |     print(f"Launch Angle Error (MAE):   {mean_la_err:.2f}° ± {std_la_err:.2f}°")
  160 |     print(f"Mean Exit Velocity:         {mean_vel:.1f} m/s ({mean_vel*3.6:.1f} km/h)")
  161 |     print(f"Peak Exit Velocity:         {max_vel:.1f} m/s ({max_vel*3.6:.1f} km/h)")
  162 |     print("-" * 65)
  163 |     print("🎯 DIRECTIONAL SPRAY CONTROL ACCURACY (Target vs Actual):")
  164 |     print(f"  • Pull Hit (Left Field):   {pull_acc:.1f}% ({pull_success}/{pull_targets})")
  165 |     print(f"  • Center Field Line Drive: {center_acc:.1f}% ({center_success}/{center_targets})")
  166 |     print(f"  • Push Hit (Right Field):  {push_acc:.1f}% ({push_success}/{push_targets})")
  167 |     print("=" * 65 + "\n")
  168 | 
  169 |     env.close()
  170 |     return {
  171 |         "contact_rate": contact_rate,
  172 |         "fair_rate": fair_rate,
  173 |         "sweet_offset_cm": mean_sweet,
  174 |         "azimuth_mae_deg": mean_az_err,
  175 |         "launch_mae_deg": mean_la_err,
  176 |         "mean_exit_vel_ms": mean_vel,
  177 |         "max_exit_vel_ms": max_vel,
  178 |         "pull_acc": pull_acc,
  179 |         "center_acc": center_acc,
  180 |         "push_acc": push_acc,
  181 |     }
  182 | 
  183 | 
  184 | if __name__ == "__main__":
  185 |     parser = argparse.ArgumentParser()
  186 |     parser.add_argument("--model", type=str, default="checkpoints/best_phase1_model.zip")
  187 |     parser.add_argument("--episodes", type=int, default=50)
  188 |     parser.add_argument("--seed", type=int, default=42)
  189 |     parser.add_argument("--video-dir", type=str, default="logs/videos")
  190 |     args = parser.parse_args()
  191 | 
  192 |     evaluate_policy(
  193 |         model_path=args.model,
  194 |         n_episodes=args.episodes,
  195 |         video_dir=args.video_dir,
  196 |         seed=args.seed,
  197 |     )
````
