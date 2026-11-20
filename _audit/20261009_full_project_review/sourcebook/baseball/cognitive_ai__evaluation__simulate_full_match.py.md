# baseball/cognitive_ai/evaluation/simulate_full_match.py

원본: [cognitive_ai/evaluation/simulate_full_match.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/simulate_full_match.py)

SHA256: `18ab2e4e227b5716a9ce5b192466001abd806b2b4c916a945b56d70342548f9f`

전체 106행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `main` | FunctionDef | 13 | 103 |
| `make_b_env` | FunctionDef | 20 | 24 |

## 전체 원문

````text
    1 | import sys
    2 | import os
    3 | sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    4 | 
    5 | import numpy as np
    6 | import cv2
    7 | import mujoco
    8 | from stable_baselines3 import PPO
    9 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
   10 | from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
   11 | from cognitive_ai.envs.baseball_rules import BaseballUmpire
   12 | 
   13 | def main():
   14 |     print("Initializing Match Environment with Umpire and Broadcast Director...")
   15 |     pitcher_model_path = "checkpoints/mocap_pitcher_best/best_model"
   16 |     pitcher_norm_path = "checkpoints/mocap_pitcher_vec_normalize.pkl"
   17 |     batter_model_path = "checkpoints/mocap_batter_best/best_model"
   18 |     batter_norm_path = "checkpoints/mocap_batter_vec_normalize.pkl"
   19 | 
   20 |     def make_b_env(): return BatterMatchTrainingEnv(
   21 |         pitcher_model_path=pitcher_model_path,
   22 |         pitcher_norm_path=pitcher_norm_path,
   23 |         is_eval_mode=True
   24 |     )
   25 |     
   26 |     b_vec = DummyVecEnv([make_b_env])
   27 |     b_vec = VecNormalize.load(batter_norm_path, b_vec)
   28 |     b_vec.training = False
   29 |     b_vec.norm_reward = False
   30 | 
   31 |     print("Loading AI Models...")
   32 |     b_model = PPO.load(batter_model_path)
   33 | 
   34 |     env = b_vec.envs[0].match_env
   35 |     umpire = BaseballUmpire()
   36 | 
   37 |     renderer = mujoco.Renderer(env.data.model, 480, 640)
   38 |     os.makedirs("data/eval_videos", exist_ok=True)
   39 |     video_path = "data/eval_videos/phase_8_1_broadcast_match.mp4"
   40 |     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   41 |     out = cv2.VideoWriter(video_path, fourcc, 60.0, (640, 480))
   42 | 
   43 |     attempts = 3
   44 |     print("=======================================================")
   45 |     print("🎬 AI BROADCAST DIRECTOR: LIVE MATCH")
   46 |     print("=======================================================")
   47 | 
   48 |     for i in range(attempts):
   49 |         b_norm_obs = b_vec.reset()
   50 |         
   51 |         done = False
   52 |         ball_trajectory = []
   53 |         hit_detected = False
   54 |         outcome = "PENDING"
   55 |         
   56 |         while not done:
   57 |             b_action, _ = b_model.predict(b_norm_obs, deterministic=True)
   58 |             # Force swing to see hitting rules occasionally? 
   59 |             # Or let it swing naturally.
   60 |             b_norm_obs, reward, dones, infos = b_vec.step(b_action)
   61 |             done = dones[0]
   62 |             info = infos[0]
   63 |             
   64 |             ball_pos = env.data.xpos[env.ball_body_id].copy()
   65 |             ball_trajectory.append(ball_pos)
   66 |             
   67 |             if getattr(env, 'has_hit', False) or env.batted_distance > 0:
   68 |                 hit_detected = True
   69 |                 
   70 |             # Dynamic Camera
   71 |             if not hit_detected:
   72 |                 active_cam = "catcher_cam"
   73 |             else:
   74 |                 active_cam = "broadcast_cam"
   75 |                 
   76 |             renderer.update_scene(env.data, camera=active_cam)
   77 |             frame = renderer.render()
   78 |             
   79 |             cv2.putText(frame, f"AT-BAT {i+1} | CAM: {active_cam}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
   80 |             
   81 |             if done:
   82 |                 min_dist_to_center = min([np.sqrt(p[0]**2 + (p[2]-0.8)**2) for p in ball_trajectory if abs(p[1]) < 0.3]) if any(abs(p[1]) < 0.3 for p in ball_trajectory) else 999.0
   83 |                 if hit_detected:
   84 |                     outcome = umpire.check_hit_outcome(ball_pos)
   85 |                 else:
   86 |                     outcome = umpire.check_pitch_outcome(ball_trajectory)
   87 |                     if info.get("swing", False) or getattr(env, 'has_swung', False):
   88 |                         outcome = "STRIKE (Swinging)"
   89 |                 
   90 |                 color = (0, 255, 0) if "FAIR" in outcome or "HOME RUN" in outcome else (0, 0, 255)
   91 |                 cv2.putText(frame, f"UMPIRE: {outcome} (Dist: {min_dist_to_center:.2f})", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
   92 |                 
   93 |             out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
   94 |             
   95 |             if done:
   96 |                 for _ in range(60):
   97 |                     out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
   98 |                     
   99 |         print(f"At-Bat {i+1}: {outcome} | Min Dist to SZ Center: {min_dist_to_center:.2f}m")
  100 | 
  101 |     out.release()
  102 |     print("=======================================================")
  103 |     print(f"🎥 Video saved to: {video_path}")
  104 | 
  105 | if __name__ == "__main__":
  106 |     main()
````
