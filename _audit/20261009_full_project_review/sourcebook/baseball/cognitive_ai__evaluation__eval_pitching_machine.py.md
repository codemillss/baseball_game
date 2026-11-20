# baseball/cognitive_ai/evaluation/eval_pitching_machine.py

원본: [cognitive_ai/evaluation/eval_pitching_machine.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/eval_pitching_machine.py)

SHA256: `4c2e761847ad1691d5bcea16ca28e96d48c1bfe7c6237bb0bf8f4436dd654552`

전체 109행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `evaluate_pitching_speed` | FunctionDef | 13 | 103 |
| `make_env` | FunctionDef | 25 | 26 |

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
   11 | from cognitive_ai.envs.pitching_machine_env import PitchingMachineEnv
   12 | 
   13 | def evaluate_pitching_speed(
   14 |     speed_kmh: int = 50,
   15 |     model_path: str = "checkpoints/pitching_50kmh_best/best_model",
   16 |     norm_path: str = "checkpoints/pitching_50kmh_vec_normalize.pkl",
   17 |     num_episodes: int = 10,
   18 |     output_filename: str = None
   19 | ):
   20 |     if output_filename is None:
   21 |         output_filename = f"pitching_{speed_kmh}kmh_eval.mp4"
   22 |         
   23 |     print(f"\n🎬 Evaluating {speed_kmh} km/h Pitching ({num_episodes} episodes)...")
   24 |     
   25 |     def make_env():
   26 |         return PitchingMachineEnv(target_speed_kmh=speed_kmh)
   27 |         
   28 |     vec_env = DummyVecEnv([make_env])
   29 |     if os.path.exists(norm_path):
   30 |         vec_env = VecNormalize.load(norm_path, vec_env)
   31 |         vec_env.training = False
   32 |         vec_env.norm_reward = False
   33 |         
   34 |     model = PPO.load(model_path, env=vec_env)
   35 |     raw_env = vec_env.envs[0]
   36 |     renderer = mujoco.Renderer(raw_env.model, height=480, width=640)
   37 |     
   38 |     video_dir = Path("data/eval_videos")
   39 |     video_dir.mkdir(parents=True, exist_ok=True)
   40 |     video_path = video_dir / output_filename
   41 |     
   42 |     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   43 |     writer = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
   44 |     
   45 |     hits = 0
   46 |     details = []
   47 |     
   48 |     for ep in range(num_episodes):
   49 |         obs = vec_env.reset()
   50 |         done = False
   51 |         step = 0
   52 |         ep_hit = False
   53 |         contact_step = None
   54 |         
   55 |         while not done and step < 55:
   56 |             action, _ = model.predict(obs, deterministic=True)
   57 |             obs, rewards, dones, infos = vec_env.step(action)
   58 |             done = dones[0]
   59 |             step += 1
   60 |             
   61 |             if "episode" in infos[0]:
   62 |                 if infos[0]["episode"]["r"] > 50:
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
   75 |             cv2.putText(bgr_frame, f"Speed: {speed_kmh}km/h | Ep {ep+1} | Step {step} | {trigger_text}", (20, 30),
   76 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
   77 |             cv2.putText(bgr_frame, f"Ball Y: {ball_pos[1]:.2f}m | Z: {ball_pos[2]:.2f}m | Act Z: {action[0][1]:.2f}", (20, 60),
   78 |                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
   79 |             
   80 |             if ep_hit and step == contact_step:
   81 |                 cv2.putText(bgr_frame, f"💥 {speed_kmh}km/h HIT!", (180, 120),
   82 |                             cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
   83 |                             
   84 |             writer.write(bgr_frame)
   85 |             
   86 |         if ep_hit:
   87 |             hits += 1
   88 |             
   89 |         status = "✅ HIT" if ep_hit else "❌ MISS"
   90 |         print(f"  Episode {ep+1:2d}: {status} (Contact Step: {contact_step})")
   91 |         details.append({"episode": ep+1, "hit": ep_hit, "step": contact_step})
   92 |         
   93 |         black = np.zeros((480, 640, 3), dtype=np.uint8)
   94 |         for _ in range(6):
   95 |             writer.write(black)
   96 |             
   97 |     writer.release()
   98 |     vec_env.close()
   99 |     
  100 |     hit_rate = (hits / num_episodes) * 100.0
  101 |     print(f"\n📊 {speed_kmh} km/h Evaluation Result: {hit_rate:.1f}% ({hits}/{num_episodes})")
  102 |     print(f"🎥 Video saved to: {video_path}")
  103 |     return hit_rate, str(video_path), details
  104 | 
  105 | if __name__ == "__main__":
  106 |     speed = int(sys.argv[1]) if len(sys.argv) > 1 else 50
  107 |     m_path = f"checkpoints/pitching_{speed}kmh_best/best_model"
  108 |     n_path = f"checkpoints/pitching_{speed}kmh_vec_normalize.pkl"
  109 |     evaluate_pitching_speed(speed_kmh=speed, model_path=m_path, norm_path=n_path)
````
