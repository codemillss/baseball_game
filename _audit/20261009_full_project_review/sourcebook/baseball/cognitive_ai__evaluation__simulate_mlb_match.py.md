# baseball/cognitive_ai/evaluation/simulate_mlb_match.py

원본: [cognitive_ai/evaluation/simulate_mlb_match.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/simulate_mlb_match.py)

SHA256: `88fad1935bfdeec164b1d3e235bcafcd02b4c8c4f2b9173661a68445afcefddd`

전체 153행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `simulate_pitcher_vs_batter_match` | FunctionDef | 15 | 150 |
| `make_p_env` | FunctionDef | 31 | 31 |
| `make_b_env` | FunctionDef | 32 | 32 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | import numpy as np
    4 | import mujoco
    5 | import cv2
    6 | from pathlib import Path
    7 | from stable_baselines3 import PPO
    8 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    9 | 
   10 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
   11 | from cognitive_ai.envs.baseball_match_env import BaseballMatchEnv
   12 | from cognitive_ai.envs.pitcher_env import PitcherEnv
   13 | from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
   14 | 
   15 | def simulate_pitcher_vs_batter_match(
   16 |     pitcher_model_path="checkpoints/mlb_pitcher_best/best_model",
   17 |     pitcher_norm_path="checkpoints/mlb_pitcher_vec_normalize.pkl",
   18 |     batter_model_path="checkpoints/mlb_batter_best/best_model",
   19 |     batter_norm_path="checkpoints/mlb_batter_vec_normalize.pkl",
   20 |     num_at_bats=15,
   21 |     output_filename="mlb_baseball_match.mp4"
   22 | ):
   23 |     print(f"\n=======================================================")
   24 |     print(f"🏟️  HUMANOID BASEBALL CHAMPIONSHIP: PITCHER VS BATTER")
   25 |     print(f"=======================================================")
   26 |     print(f"• Pitcher Model: {pitcher_model_path}")
   27 |     print(f"• Batter Model : {batter_model_path}")
   28 |     print(f"• Total At-Bats: {num_at_bats}\n")
   29 |     
   30 |     # Setup Environments for Normalizer Loaders
   31 |     def make_p_env(): return PitcherEnv()
   32 |     def make_b_env(): return BatterMatchTrainingEnv(is_eval_mode=True)
   33 |     
   34 |     p_vec = DummyVecEnv([make_p_env])
   35 |     p_norm = VecNormalize.load(pitcher_norm_path, p_vec)
   36 |     p_norm.training = False
   37 |     p_norm.norm_reward = False
   38 |     
   39 |     b_vec = DummyVecEnv([make_b_env])
   40 |     b_norm = VecNormalize.load(batter_norm_path, b_vec)
   41 |     b_norm.training = False
   42 |     b_norm.norm_reward = False
   43 |     
   44 |     pitcher_model = PPO.load(pitcher_model_path, env=p_vec)
   45 |     batter_model = PPO.load(batter_model_path, env=b_vec)
   46 |     
   47 |     match_env = BaseballMatchEnv()
   48 |     renderer = mujoco.Renderer(match_env.model, height=480, width=640)
   49 |     
   50 |     video_dir = Path("data/eval_videos")
   51 |     video_dir.mkdir(parents=True, exist_ok=True)
   52 |     video_path = video_dir / output_filename
   53 |     
   54 |     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   55 |     writer = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
   56 |     
   57 |     stats = {"HITS": 0, "HOMERUNS": 0, "STRIKEOUTS": 0, "WALKS": 0, "OUTS": 0}
   58 |     
   59 |     for ab in range(num_at_bats):
   60 |         obs = match_env.reset()
   61 |         done = False
   62 |         step = 0
   63 |         
   64 |         while not done and step < 70:
   65 |             # Normalize observations
   66 |             p_obs_norm = p_norm.normalize_obs(obs["pitcher"])
   67 |             b_obs_norm = b_norm.normalize_obs(obs["batter"])
   68 |             
   69 |             # Predict actions from both AI models
   70 |             p_act, _ = pitcher_model.predict(p_obs_norm, deterministic=True)
   71 |             b_act, _ = batter_model.predict(b_obs_norm, deterministic=True)
   72 |             
   73 |             # Step the full live match environment
   74 |             obs, done, info = match_env.step(p_act, b_act)
   75 |             step += 1
   76 |             
   77 |             # Dynamic camera switching: Broadcast angle for pitch flight, Batter view on swing
   78 |             cam_name = "broadcast_cam" if step < 28 or not match_env.has_contacted else "batter_focus_cam"
   79 |             renderer.update_scene(match_env.data, camera=cam_name)
   80 |             rgb_frame = renderer.render()
   81 |             bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
   82 |             
   83 |             # Broadcast HUD Scoreboard
   84 |             p_speed = match_env.pitch_speed_kmh
   85 |             exit_vel = match_env.exit_velocity_kmh
   86 |             
   87 |             pitch_type_idx = match_env.target_pitch_type
   88 |             pitch_names = ["FAST", "SLIDER", "CURVE"]
   89 |             pitch_name = pitch_names[pitch_type_idx]
   90 |             
   91 |             # Draw header banner
   92 |             cv2.rectangle(bgr_frame, (0, 0), (640, 45), (20, 20, 20), -1)
   93 |             cv2.putText(bgr_frame, f"AT-BAT {ab+1:2d}/{num_at_bats} | {pitch_name} | {p_speed:.1f} km/h", (10, 30),
   94 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
   95 |             cv2.putText(bgr_frame, f"H: {stats['HITS']} | HR: {stats['HOMERUNS']} | K: {stats['STRIKEOUTS']}", (410, 30),
   96 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
   97 |             
   98 |             if match_env.has_contacted:
   99 |                 cv2.putText(bgr_frame, f"💥 CONTACT! Exit Vel: {exit_vel:.1f} km/h", (140, 100),
  100 |                             cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2)
  101 |             elif match_env.b_swing_active:
  102 |                 cv2.putText(bgr_frame, f"SWING!", (260, 100),
  103 |                             cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 200, 255), 2)
  104 |                             
  105 |             if done:
  106 |                 # Show Outcome Splash
  107 |                 cv2.rectangle(bgr_frame, (100, 200), (540, 280), (0, 0, 0), -1)
  108 |                 cv2.putText(bgr_frame, f"{info['outcome']}", (120, 250),
  109 |                             cv2.FONT_HERSHEY_DUPLEX, 0.85, (255, 255, 255), 2)
  110 |                             
  111 |             writer.write(bgr_frame)
  112 |             
  113 |         # Update match scoreboard
  114 |         outcome = info["outcome"]
  115 |         if "HOME RUN" in outcome:
  116 |             stats["HOMERUNS"] += 1
  117 |             stats["HITS"] += 1
  118 |         elif "BASE HIT" in outcome:
  119 |             stats["HITS"] += 1
  120 |         elif "STRIKE OUT" in outcome or "CALLED STRIKE" in outcome:
  121 |             stats["STRIKEOUTS"] += 1
  122 |         elif "BALL" in outcome:
  123 |             stats["WALKS"] += 1
  124 |         else:
  125 |             stats["OUTS"] += 1
  126 |             
  127 |         pitch_type_idx = match_env.target_pitch_type
  128 |         pitch_names = ["FASTBALL", "SLIDER", "CURVE"]
  129 |         pitch_name = pitch_names[pitch_type_idx]
  130 |         
  131 |         print(f"  At-Bat {ab+1:2d}: {outcome:26s} | {pitch_name} | Pitch: {info['pitch_speed_kmh']:.1f} km/h | ExitVel: {info['exit_velocity_kmh']:.1f} km/h | Dist: {info['batted_distance']:.1f}m")
  132 |         
  133 |         black = np.zeros((480, 640, 3), dtype=np.uint8)
  134 |         for _ in range(8):
  135 |             writer.write(black)
  136 |             
  137 |     writer.release()
  138 |     p_vec.close()
  139 |     b_vec.close()
  140 |     
  141 |     batting_avg = (stats['HITS'] / (num_at_bats - stats['WALKS'])) if (num_at_bats - stats['WALKS']) > 0 else 0.0
  142 |     print(f"\n=======================================================")
  143 |     print(f"📊 FINAL MATCH BOX SCORE & STATISTICS")
  144 |     print(f"=======================================================")
  145 |     print(f"• Total At-Bats   : {num_at_bats}")
  146 |     print(f"• Hits (안타)     : {stats['HITS']} (Home Runs: {stats['HOMERUNS']})")
  147 |     print(f"• Strikeouts (삼진): {stats['STRIKEOUTS']}")
  148 |     print(f"• Batting Average : {batting_avg:.3f} (타율 .{(int(batting_avg*1000)):03d})")
  149 |     print(f"🎥 Video Broadcast saved to: {video_path}")
  150 |     return stats, str(video_path)
  151 | 
  152 | if __name__ == "__main__":
  153 |     simulate_pitcher_vs_batter_match()
````
