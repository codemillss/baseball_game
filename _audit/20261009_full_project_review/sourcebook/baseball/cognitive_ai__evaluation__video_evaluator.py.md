# baseball/cognitive_ai/evaluation/video_evaluator.py

원본: [cognitive_ai/evaluation/video_evaluator.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/video_evaluator.py)

SHA256: `12ff8023269c1a057be6d792d1f9e625111b5349a1e5a037a37463ced288ac0a`

전체 141행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `VideoEvaluator` | ClassDef | 13 | 126 |
| `__init__` | FunctionDef | 20 | 33 |
| `record_and_evaluate` | FunctionDef | 35 | 126 |

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
    9 | # Add parent directory
   10 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
   11 | from cognitive_ai.envs.teeball_env import TeeBallEnv
   12 | 
   13 | class VideoEvaluator:
   14 |     """
   15 |     AI Autonomous Video Evaluation & Diagnostic System
   16 |     - Records offscreen 3D simulation video (MP4)
   17 |     - Extracts contact frames and metrics
   18 |     - Analyzes physics, kinematics, and failure modes
   19 |     """
   20 |     def __init__(
   21 |         self,
   22 |         xml_path: str = "shared_assets/h1_baseball.xml",
   23 |         video_dir: str = "data/eval_videos",
   24 |         width: int = 640,
   25 |         height: int = 480,
   26 |         fps: int = 30,
   27 |     ):
   28 |         self.xml_path = xml_path
   29 |         self.video_dir = Path(video_dir)
   30 |         self.video_dir.mkdir(parents=True, exist_ok=True)
   31 |         self.width = width
   32 |         self.height = height
   33 |         self.fps = fps
   34 | 
   35 |     def record_and_evaluate(
   36 |         self,
   37 |         model_path: str,
   38 |         num_episodes: int = 3,
   39 |         camera_name: str = "side_cam",
   40 |         output_filename: str = "latest_evaluation.mp4"
   41 |     ) -> dict:
   42 |         """
   43 |         Runs evaluation episodes, records video, and computes diagnostic metrics.
   44 |         """
   45 |         env = TeeBallEnv(xml_path=self.xml_path, render_mode=None)
   46 |         renderer = mujoco.Renderer(env.model, height=self.height, width=self.width)
   47 |         
   48 |         # Load model
   49 |         model = PPO.load(model_path)
   50 |         
   51 |         video_path = self.video_dir / output_filename
   52 |         fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   53 |         writer = cv2.VideoWriter(str(video_path), fourcc, self.fps, (self.width, self.height))
   54 |         
   55 |         metrics = {
   56 |             "num_episodes": num_episodes,
   57 |             "hits": 0,
   58 |             "misses": 0,
   59 |             "hit_details": [],
   60 |             "video_path": str(video_path),
   61 |         }
   62 |         
   63 |         for ep in range(num_episodes):
   64 |             obs, _ = env.reset()
   65 |             done = False
   66 |             step = 0
   67 |             ep_frames = []
   68 |             ep_hit = False
   69 |             contact_step = None
   70 |             
   71 |             ball_initial_z = float(obs[2])
   72 |             
   73 |             while not done and step < 80:
   74 |                 action, _ = model.predict(obs, deterministic=True)
   75 |                 obs, reward, terminated, truncated, _ = env.step(action)
   76 |                 done = terminated or truncated
   77 |                 step += 1
   78 |                 
   79 |                 # Render frame
   80 |                 renderer.update_scene(env.data, camera=camera_name)
   81 |                 rgb_frame = renderer.render()
   82 |                 
   83 |                 # Convert RGB to BGR for OpenCV
   84 |                 bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
   85 |                 
   86 |                 # Add HUD / Telemetry overlay
   87 |                 cv2.putText(bgr_frame, f"Ep {ep+1} | Step {step} | SWING", (20, 30),
   88 |                             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
   89 |                 cv2.putText(bgr_frame, f"Ball Z: {ball_initial_z:.2f}m | Action Z: {float(action[0]):.2f}", (20, 60),
   90 |                             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
   91 |                 
   92 |                 if reward > 50 and not ep_hit:
   93 |                     ep_hit = True
   94 |                     contact_step = step
   95 |                     cv2.putText(bgr_frame, "💥 CONTACT / HIT!", (self.width // 2 - 100, 100),
   96 |                                 cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
   97 |                 elif ep_hit:
   98 |                     cv2.putText(bgr_frame, "💥 HIT!", (20, 90),
   99 |                                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
  100 |                                 
  101 |                 writer.write(bgr_frame)
  102 |                 ep_frames.append(bgr_frame)
  103 |                 
  104 |             if ep_hit:
  105 |                 metrics["hits"] += 1
  106 |             else:
  107 |                 metrics["misses"] += 1
  108 |                 
  109 |             metrics["hit_details"].append({
  110 |                 "episode": ep + 1,
  111 |                 "ball_z": round(ball_initial_z, 3),
  112 |                 "hit": ep_hit,
  113 |                 "contact_step": contact_step,
  114 |                 "total_steps": step,
  115 |             })
  116 |             
  117 |             # Add brief pause frame between episodes
  118 |             black_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
  119 |             for _ in range(10):
  120 |                 writer.write(black_frame)
  121 |                 
  122 |         writer.release()
  123 |         env.close()
  124 |         
  125 |         metrics["hit_rate"] = (metrics["hits"] / num_episodes) * 100.0
  126 |         return metrics
  127 | 
  128 | if __name__ == "__main__":
  129 |     evaluator = VideoEvaluator()
  130 |     model_file = "checkpoints/teeball_best_model/best_model"
  131 |     if not os.path.exists(model_file + ".zip"):
  132 |         model_file = "checkpoints/teeball_final_model"
  133 |         
  134 |     print(f"🎬 Recording evaluation video for: {model_file}...")
  135 |     results = evaluator.record_and_evaluate(model_file, num_episodes=5)
  136 |     print("\n📊 Evaluation Summary:")
  137 |     print(f"  - Hit Rate: {results['hit_rate']:.1f}% ({results['hits']}/{results['num_episodes']})")
  138 |     print(f"  - Video saved to: {results['video_path']}")
  139 |     for d in results['hit_details']:
  140 |         status = "✅ HIT" if d['hit'] else "❌ MISS"
  141 |         print(f"    Episode {d['episode']}: Ball Z={d['ball_z']}m -> {status} (Step {d['contact_step']})")
````
