# baseball/cognitive_ai/evaluation/eval_pitcher.py

원본: [cognitive_ai/evaluation/eval_pitcher.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/eval_pitcher.py)

SHA256: `b833f6d81f33381ef126d96f07d8218a0742c164828b66347918deef328d4d9a`

전체 109행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate_pitcher` | FunctionDef | 13 | 106 |
| `make_env` | FunctionDef | 21 | 22 |

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
   11 | from cognitive_ai.envs.pitcher_env import PitcherEnv
   12 | 
   13 | def evaluate_pitcher(
   14 |     model_path="checkpoints/pitcher_best/best_model",
   15 |     norm_path="checkpoints/pitcher_vec_normalize.pkl",
   16 |     num_episodes=15,
   17 |     output_filename="pitcher_evaluation.mp4"
   18 | ):
   19 |     print(f"\n🎬 Evaluating Embodied Pitcher Model: {model_path} ({num_episodes} episodes)...")
   20 |     
   21 |     def make_env():
   22 |         return PitcherEnv()
   23 |         
   24 |     vec_env = DummyVecEnv([make_env])
   25 |     if os.path.exists(norm_path):
   26 |         vec_env = VecNormalize.load(norm_path, vec_env)
   27 |         vec_env.training = False
   28 |         vec_env.norm_reward = False
   29 |         
   30 |     model = PPO.load(model_path, env=vec_env)
   31 |     raw_env = vec_env.envs[0]
   32 |     renderer = mujoco.Renderer(raw_env.model, height=480, width=640)
   33 |     
   34 |     video_dir = Path("data/eval_videos")
   35 |     video_dir.mkdir(parents=True, exist_ok=True)
   36 |     video_path = video_dir / output_filename
   37 |     
   38 |     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   39 |     writer = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
   40 |     
   41 |     strikes = 0
   42 |     total_speed = 0.0
   43 |     
   44 |     for ep in range(num_episodes):
   45 |         obs = vec_env.reset()
   46 |         done = False
   47 |         step = 0
   48 |         is_strike = False
   49 |         final_speed = 0.0
   50 |         final_dist = 999.0
   51 |         
   52 |         while not done and step < 70:
   53 |             action, _ = model.predict(obs, deterministic=True)
   54 |             obs, rewards, dones, infos = vec_env.step(action)
   55 |             done = dones[0]
   56 |             info = infos[0]
   57 |             step += 1
   58 |             
   59 |             # Switch camera view dynamically: Behind pitcher during windup, catcher during arrival
   60 |             cam_name = "side_cam" if step < 25 else "catcher_cam"
   61 |             renderer.update_scene(raw_env.data, camera=cam_name)
   62 |             rgb_frame = renderer.render()
   63 |             bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
   64 |             
   65 |             ball_pos = raw_env.data.qpos[raw_env.ball_qpos_adr:raw_env.ball_qpos_adr+3]
   66 |             speed = raw_env.release_speed_kmh
   67 |             final_speed = speed
   68 |             
   69 |             rel_text = "RELEASED" if raw_env.is_released else "WINDUP"
   70 |             
   71 |             # HUD overlay
   72 |             cv2.putText(bgr_frame, f"Ep {ep+1:2d} | State: {rel_text} | Speed: {speed:.1f} km/h", (20, 30),
   73 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
   74 |             cv2.putText(bgr_frame, f"Target: ({raw_env.target_x:.2f}, {raw_env.target_z:.2f}) | Ball Y: {ball_pos[1]:.2f}m", (20, 60),
   75 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
   76 |             
   77 |             if "release_speed_kmh" in info:
   78 |                 final_speed = info["release_speed_kmh"]
   79 |             if "min_dist" in info:
   80 |                 final_dist = info["min_dist"]
   81 |             if "reached_plate" in info:
   82 |                 is_strike = (info["reached_plate"] and info["min_dist"] <= 0.20)
   83 |                 
   84 |             writer.write(bgr_frame)
   85 |             
   86 |         if is_strike:
   87 |             strikes += 1
   88 |         total_speed += final_speed
   89 |         
   90 |         status = "🔥 STRIKE" if is_strike else "⚠️ BALL"
   91 |         print(f"  Episode {ep+1:2d}: {status} | Speed={final_speed:.1f} km/h, MissDist={final_dist*100:.1f} cm")
   92 |         
   93 |         black = np.zeros((480, 640, 3), dtype=np.uint8)
   94 |         for _ in range(6):
   95 |             writer.write(black)
   96 |             
   97 |     writer.release()
   98 |     vec_env.close()
   99 |     
  100 |     strike_rate = (strikes / num_episodes) * 100.0
  101 |     avg_speed = total_speed / num_episodes
  102 |     print(f"\n📊 Overall Pitcher Results:")
  103 |     print(f"   • Strike Rate : {strike_rate:.1f}% ({strikes}/{num_episodes})")
  104 |     print(f"   • Avg Velocity: {avg_speed:.1f} km/h")
  105 |     print(f"🎥 Video saved to: {video_path}")
  106 |     return strike_rate, str(video_path)
  107 | 
  108 | if __name__ == "__main__":
  109 |     evaluate_pitcher()
````
