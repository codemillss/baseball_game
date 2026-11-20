# baseball/cognitive_ai/evaluation/eval_breaking_ball.py

원본: [cognitive_ai/evaluation/eval_breaking_ball.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/eval_breaking_ball.py)

SHA256: `38eae59c31e59cbce878a9fa2cb2180447987e7b7cf7c6a7b8be0fe564e13422`

전체 109행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate_breaking_balls` | FunctionDef | 13 | 106 |
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
   11 | from cognitive_ai.envs.breaking_ball_env import BreakingBallEnv
   12 | 
   13 | def evaluate_breaking_balls(
   14 |     model_path="checkpoints/breaking_ball_best/best_model",
   15 |     norm_path="checkpoints/breaking_ball_vec_normalize.pkl",
   16 |     num_episodes=15,
   17 |     output_filename="breaking_ball_evaluation.mp4"
   18 | ):
   19 |     print(f"\n🎬 Evaluating 3D Breaking Ball Model: {model_path} ({num_episodes} episodes)...")
   20 |     
   21 |     def make_env():
   22 |         return BreakingBallEnv()
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
   41 |     pitch_stats = {"FASTBALL": {"hits": 0, "total": 0}, "SLIDER": {"hits": 0, "total": 0}, "CURVE": {"hits": 0, "total": 0}}
   42 |     total_hits = 0
   43 |     
   44 |     for ep in range(num_episodes):
   45 |         obs = vec_env.reset()
   46 |         done = False
   47 |         step = 0
   48 |         ep_hit = False
   49 |         contact_step = None
   50 |         p_type = raw_env.pitch_type
   51 |         pitch_stats[p_type]["total"] += 1
   52 |         
   53 |         while not done and step < 60:
   54 |             action, _ = model.predict(obs, deterministic=True)
   55 |             obs, rewards, dones, infos = vec_env.step(action)
   56 |             done = dones[0]
   57 |             step += 1
   58 |             
   59 |             if "episode" in infos[0]:
   60 |                 if infos[0]["episode"]["r"] > 50:
   61 |                     ep_hit = True
   62 |                     contact_step = step
   63 |             elif rewards[0] > 50:
   64 |                 ep_hit = True
   65 |                 contact_step = step
   66 |                 
   67 |             renderer.update_scene(raw_env.data, camera="side_cam")
   68 |             rgb_frame = renderer.render()
   69 |             bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
   70 |             
   71 |             ball_pos = raw_env.data.qpos[raw_env.ball_qpos_adr:raw_env.ball_qpos_adr+3]
   72 |             trigger_text = "SWING!" if action[0][0] > 0 else "WATCHING"
   73 |             
   74 |             # HUD overlay
   75 |             cv2.putText(bgr_frame, f"Ep {ep+1} | Pitch: {p_type} | {trigger_text}", (20, 30),
   76 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
   77 |             cv2.putText(bgr_frame, f"Ball X: {ball_pos[0]:.2f}m | Z: {ball_pos[2]:.2f}m | Yaw: {action[0][2]:.2f}", (20, 60),
   78 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
   79 |             
   80 |             if ep_hit and step == contact_step:
   81 |                 cv2.putText(bgr_frame, f"💥 {p_type} HIT!", (180, 120),
   82 |                             cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
   83 |                             
   84 |             writer.write(bgr_frame)
   85 |             
   86 |         if ep_hit:
   87 |             total_hits += 1
   88 |             pitch_stats[p_type]["hits"] += 1
   89 |             
   90 |         status = "✅ HIT" if ep_hit else "❌ MISS"
   91 |         print(f"  Episode {ep+1:2d} [{p_type:8s}]: {status} (Contact Step: {contact_step})")
   92 |         
   93 |         black = np.zeros((480, 640, 3), dtype=np.uint8)
   94 |         for _ in range(6):
   95 |             writer.write(black)
   96 |             
   97 |     writer.release()
   98 |     vec_env.close()
   99 |     
  100 |     hit_rate = (total_hits / num_episodes) * 100.0
  101 |     print(f"\n📊 Overall Breaking Ball Result: {hit_rate:.1f}% ({total_hits}/{num_episodes})")
  102 |     for pt, s in pitch_stats.items():
  103 |         if s["total"] > 0:
  104 |             print(f"   • {pt:8s}: {s['hits']/s['total']*100:.1f}% ({s['hits']}/{s['total']})")
  105 |     print(f"🎥 Video saved to: {video_path}")
  106 |     return hit_rate, str(video_path)
  107 | 
  108 | if __name__ == "__main__":
  109 |     evaluate_breaking_balls()
````
