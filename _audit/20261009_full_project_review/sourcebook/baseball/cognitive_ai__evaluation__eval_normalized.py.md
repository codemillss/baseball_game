# baseball/cognitive_ai/evaluation/eval_normalized.py

원본: [cognitive_ai/evaluation/eval_normalized.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/eval_normalized.py)

SHA256: `a410627c5f295f38383c694ba7ce2fcab3f3bb2e1cac678ca8745c09ea934db3`

전체 113행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `eval_normalized` | FunctionDef | 13 | 110 |
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
   11 | from cognitive_ai.envs.soft_toss_env import SoftTossEnv
   12 | 
   13 | def eval_normalized(
   14 |     model_path="checkpoints/soft_toss_best_model/best_model",
   15 |     norm_path="checkpoints/soft_toss_vec_normalize.pkl",
   16 |     num_episodes=10,
   17 |     output_filename="soft_toss_normalized_eval.mp4"
   18 | ):
   19 |     print(f"🎬 Evaluating Normalized Soft-Toss Agent: {model_path}...")
   20 |     
   21 |     def make_env():
   22 |         return SoftTossEnv()
   23 |         
   24 |     vec_env = DummyVecEnv([make_env])
   25 |     if os.path.exists(norm_path):
   26 |         vec_env = VecNormalize.load(norm_path, vec_env)
   27 |         vec_env.training = False
   28 |         vec_env.norm_reward = False
   29 |         
   30 |     model = PPO.load(model_path, env=vec_env)
   31 |     
   32 |     # Renderer for video
   33 |     raw_env = vec_env.envs[0]
   34 |     renderer = mujoco.Renderer(raw_env.model, height=480, width=640)
   35 |     
   36 |     video_dir = Path("data/eval_videos")
   37 |     video_dir.mkdir(parents=True, exist_ok=True)
   38 |     video_path = video_dir / output_filename
   39 |     
   40 |     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   41 |     writer = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
   42 |     
   43 |     hits = 0
   44 |     details = []
   45 |     
   46 |     for ep in range(num_episodes):
   47 |         obs = vec_env.reset()
   48 |         done = False
   49 |         step = 0
   50 |         ep_hit = False
   51 |         contact_step = None
   52 |         
   53 |         while not done and step < 50:
   54 |             action, _ = model.predict(obs, deterministic=True)
   55 |             obs, rewards, dones, infos = vec_env.step(action)
   56 |             done = dones[0]
   57 |             step += 1
   58 |             
   59 |             # Check if this step was contact
   60 |             if "episode" in infos[0]:
   61 |                 ep_rew = infos[0]["episode"]["r"]
   62 |                 if ep_rew > 50:
   63 |                     ep_hit = True
   64 |                     contact_step = step
   65 |             elif rewards[0] > 50:
   66 |                 ep_hit = True
   67 |                 contact_step = step
   68 |                 
   69 |             renderer.update_scene(raw_env.data, camera="side_cam")
   70 |             rgb_frame = renderer.render()
   71 |             bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
   72 |             
   73 |             ball_pos = raw_env.data.qpos[raw_env.ball_qpos_adr:raw_env.ball_qpos_adr+3]
   74 |             trigger_text = "SWING!" if action[0][0] > 0 else "WATCHING"
   75 |             cv2.putText(bgr_frame, f"Ep {ep+1} | Step {step} | {trigger_text}", (20, 30),
   76 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
   77 |             cv2.putText(bgr_frame, f"Ball Y: {ball_pos[1]:.2f}m | Z: {ball_pos[2]:.2f}m | Act Z: {action[0][1]:.2f}", (20, 60),
   78 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
   79 |             
   80 |             if rewards[0] > 50 and not ep_hit:
   81 |                 ep_hit = True
   82 |                 contact_step = step
   83 |                 cv2.putText(bgr_frame, "💥 CONTACT / HIT!", (200, 120),
   84 |                             cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
   85 |             elif ep_hit:
   86 |                 cv2.putText(bgr_frame, "💥 HIT!", (20, 90),
   87 |                             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
   88 |                             
   89 |             writer.write(bgr_frame)
   90 |             
   91 |         if ep_hit or raw_env.has_contacted:
   92 |             hits += 1
   93 |             ep_hit = True
   94 |             
   95 |         status = "✅ HIT" if ep_hit else "❌ MISS"
   96 |         print(f"  Episode {ep+1:2d}: {status} (Contact Step: {contact_step}, Ball Z: {ball_pos[2]:.2f}m)")
   97 |         details.append({"episode": ep+1, "hit": ep_hit, "step": contact_step, "ball_z": float(ball_pos[2])})
   98 |         
   99 |         # Black frame transition
  100 |         black = np.zeros((480, 640, 3), dtype=np.uint8)
  101 |         for _ in range(8):
  102 |             writer.write(black)
  103 |             
  104 |     writer.release()
  105 |     vec_env.close()
  106 |     
  107 |     hit_rate = (hits / num_episodes) * 100.0
  108 |     print(f"\n📊 Normalized Soft-Toss Evaluation Result: {hit_rate:.1f}% ({hits}/{num_episodes})")
  109 |     print(f"🎥 Video saved to: {video_path}")
  110 |     return hit_rate, str(video_path), details
  111 | 
  112 | if __name__ == "__main__":
  113 |     eval_normalized()
````
