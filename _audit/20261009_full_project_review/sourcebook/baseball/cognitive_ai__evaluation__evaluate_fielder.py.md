# baseball/cognitive_ai/evaluation/evaluate_fielder.py

원본: [cognitive_ai/evaluation/evaluate_fielder.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/evaluate_fielder.py)

SHA256: `1778586c2ce07b487451ef25b0bb2c8917cea2f220017db69e53767d20d899ea`

전체 76행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `main` | FunctionDef | 13 | 73 |

## 전체 원문

````text
    1 | import sys
    2 | import os
    3 | sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    4 | 
    5 | from stable_baselines3 import PPO
    6 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    7 | import mujoco
    8 | import numpy as np
    9 | import cv2
   10 | 
   11 | from cognitive_ai.envs.fielder_env import FielderEnv
   12 | 
   13 | def main():
   14 |     env = DummyVecEnv([lambda: FielderEnv()])
   15 |     env = VecNormalize.load("checkpoints/fielder/vec_normalize.pkl", env)
   16 |     env.training = False
   17 |     env.norm_reward = False
   18 |     
   19 |     model = PPO.load("checkpoints/fielder/best_model", env=env)
   20 |     
   21 |     f_env = env.envs[0]
   22 |     renderer = mujoco.Renderer(f_env.model, 480, 640)
   23 |     
   24 |     os.makedirs("data/eval_videos", exist_ok=True)
   25 |     video_path = "data/eval_videos/phase_7_1_wheeled_fielder.mp4"
   26 |     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   27 |     out = cv2.VideoWriter(video_path, fourcc, 60.0, (640, 480))
   28 |     
   29 |     print("=======================================================")
   30 |     print("🏟️  WHEELED FIELDER CATCH TEST")
   31 |     print("=======================================================")
   32 |     
   33 |     catches = 0
   34 |     attempts = 5
   35 |     
   36 |     for i in range(attempts):
   37 |         obs = env.reset()
   38 |         done = False
   39 |         
   40 |         while not done:
   41 |             action, _ = model.predict(obs, deterministic=True)
   42 |             obs, reward, dones, infos = env.step(action)
   43 |             done = dones[0]
   44 |             info = infos[0]
   45 |             
   46 |             renderer.update_scene(f_env.data, camera="tracking_cam")
   47 |             frame = renderer.render()
   48 |             
   49 |             # Add text overlay
   50 |             text = f"Attempt: {i+1}/5 | Dist: {info.get('dist', 0.0):.2f}m"
   51 |             cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
   52 |             
   53 |             if done:
   54 |                 if info.get('catch', False):
   55 |                     cv2.putText(frame, "CATCH!", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
   56 |                     catches += 1
   57 |                 else:
   58 |                     cv2.putText(frame, "DROP!", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
   59 |                     
   60 |             out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
   61 |             
   62 |             if done:
   63 |                 # hold final frame for 1 second
   64 |                 for _ in range(60):
   65 |                     out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
   66 |                     
   67 |         result = "✅ CATCH" if info.get('catch', False) else "❌ DROP"
   68 |         print(f"  Attempt {i+1}: {result} | Final Dist: {info.get('dist', 0.0):.2f}m")
   69 |         
   70 |     out.release()
   71 |     print("=======================================================")
   72 |     print(f"📊 FINAL SCORE: {catches}/{attempts} Catches")
   73 |     print(f"🎥 Video saved to: {video_path}")
   74 | 
   75 | if __name__ == "__main__":
   76 |     main()
````
