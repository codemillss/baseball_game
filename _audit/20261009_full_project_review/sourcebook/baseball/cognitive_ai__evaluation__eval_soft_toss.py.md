# baseball/cognitive_ai/evaluation/eval_soft_toss.py

원본: [cognitive_ai/evaluation/eval_soft_toss.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/eval_soft_toss.py)

SHA256: `7ec4468db48465b3366db866779ff8ed79d7472ebd8a7a65432d55570cfb9cae`

전체 93행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate_soft_toss` | FunctionDef | 12 | 90 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | import numpy as np
    4 | import mujoco
    5 | import cv2
    6 | from pathlib import Path
    7 | from stable_baselines3 import PPO
    8 | 
    9 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
   10 | from cognitive_ai.envs.soft_toss_env import SoftTossEnv
   11 | 
   12 | def evaluate_soft_toss(
   13 |     model_path: str = "checkpoints/soft_toss_best_model/best_model",
   14 |     num_episodes: int = 10,
   15 |     output_filename: str = "soft_toss_evaluation.mp4"
   16 | ):
   17 |     if not os.path.exists(model_path + ".zip"):
   18 |         model_path = "checkpoints/soft_toss_final_model"
   19 |         
   20 |     print(f"🎬 Evaluating Soft-Toss Model: {model_path} ({num_episodes} episodes)...")
   21 |     
   22 |     env = SoftTossEnv()
   23 |     renderer = mujoco.Renderer(env.model, height=480, width=640)
   24 |     model = PPO.load(model_path)
   25 |     
   26 |     video_dir = Path("data/eval_videos")
   27 |     video_dir.mkdir(parents=True, exist_ok=True)
   28 |     video_path = video_dir / output_filename
   29 |     
   30 |     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   31 |     writer = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
   32 |     
   33 |     hits = 0
   34 |     details = []
   35 |     
   36 |     for ep in range(num_episodes):
   37 |         obs, _ = env.reset()
   38 |         done = False
   39 |         step = 0
   40 |         ep_hit = False
   41 |         contact_step = None
   42 |         
   43 |         while not done and step < 60:
   44 |             action, _ = model.predict(obs, deterministic=True)
   45 |             obs, reward, terminated, truncated, _ = env.step(action)
   46 |             done = terminated or truncated
   47 |             step += 1
   48 |             
   49 |             renderer.update_scene(env.data, camera="side_cam")
   50 |             rgb_frame = renderer.render()
   51 |             bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
   52 |             
   53 |             # HUD overlay
   54 |             ball_pos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
   55 |             trigger_text = "SWING!" if action[0] > 0 else "WATCHING"
   56 |             cv2.putText(bgr_frame, f"Ep {ep+1} | Step {step} | {trigger_text}", (20, 30),
   57 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
   58 |             cv2.putText(bgr_frame, f"Ball Y: {ball_pos[1]:.2f}m | Z: {ball_pos[2]:.2f}m | Act Z: {action[1]:.2f}", (20, 60),
   59 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
   60 |             
   61 |             if reward > 50 and not ep_hit:
   62 |                 ep_hit = True
   63 |                 contact_step = step
   64 |                 cv2.putText(bgr_frame, "💥 CONTACT / HIT!", (200, 120),
   65 |                             cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
   66 |             elif ep_hit:
   67 |                 cv2.putText(bgr_frame, "💥 HIT!", (20, 90),
   68 |                             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
   69 |                             
   70 |             writer.write(bgr_frame)
   71 |             
   72 |         if ep_hit:
   73 |             hits += 1
   74 |             
   75 |         status = "✅ HIT" if ep_hit else "❌ MISS"
   76 |         print(f"  Episode {ep+1:2d}: {status} (Contact Step: {contact_step}, Final Ball Z: {ball_pos[2]:.2f}m)")
   77 |         details.append({"episode": ep+1, "hit": ep_hit, "step": contact_step, "ball_z": float(ball_pos[2])})
   78 |         
   79 |         # Black frame transition
   80 |         black = np.zeros((480, 640, 3), dtype=np.uint8)
   81 |         for _ in range(8):
   82 |             writer.write(black)
   83 |             
   84 |     writer.release()
   85 |     env.close()
   86 |     
   87 |     hit_rate = (hits / num_episodes) * 100.0
   88 |     print(f"\n📊 Soft-Toss Evaluation Result: {hit_rate:.1f}% ({hits}/{num_episodes})")
   89 |     print(f"🎥 Video saved to: {video_path}")
   90 |     return hit_rate, str(video_path), details
   91 | 
   92 | if __name__ == "__main__":
   93 |     evaluate_soft_toss()
````
