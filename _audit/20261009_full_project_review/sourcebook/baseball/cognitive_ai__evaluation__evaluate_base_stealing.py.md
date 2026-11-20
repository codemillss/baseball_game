# baseball/cognitive_ai/evaluation/evaluate_base_stealing.py

원본: [cognitive_ai/evaluation/evaluate_base_stealing.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/evaluate_base_stealing.py)

SHA256: `c08984cd6048668145ac9125d5b2bd22e40be03e11de7b4bd878d896609c72f7`

전체 80행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `main` | FunctionDef | 13 | 77 |

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
   10 | from cognitive_ai.envs.catcher_env import CatcherEnv
   11 | from cognitive_ai.envs.runner_env import RunnerEnv
   12 | 
   13 | def main():
   14 |     print("Initializing Catcher and Runner Environments...")
   15 |     c_vec = DummyVecEnv([lambda: CatcherEnv()])
   16 |     c_vec = VecNormalize.load("checkpoints/catcher/vec_normalize.pkl", c_vec)
   17 |     c_vec.training = False
   18 |     c_vec.norm_reward = False
   19 |     
   20 |     r_vec = DummyVecEnv([lambda: RunnerEnv()])
   21 |     r_vec = VecNormalize.load("checkpoints/runner/vec_normalize.pkl", r_vec)
   22 |     r_vec.training = False
   23 |     r_vec.norm_reward = False
   24 | 
   25 |     print("Loading AI Models...")
   26 |     c_model = PPO.load("checkpoints/catcher/best_model")
   27 |     r_model = PPO.load("checkpoints/runner/best_model")
   28 | 
   29 |     c_env = c_vec.envs[0]
   30 |     r_env = r_vec.envs[0]
   31 |     
   32 |     # We will render using Runner's environment, but we will step both.
   33 |     # Actually, rendering both in one environment requires merging them into h1_baseball_match.xml!
   34 |     # For now, let's just do a quick unit test video of the Runner reaching 2nd base.
   35 |     renderer = mujoco.Renderer(r_env.model, 480, 640)
   36 |     
   37 |     os.makedirs("data/eval_videos", exist_ok=True)
   38 |     video_path = "data/eval_videos/phase_8_3_base_stealing.mp4"
   39 |     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   40 |     out = cv2.VideoWriter(video_path, fourcc, 60.0, (640, 480))
   41 | 
   42 |     print("=======================================================")
   43 |     print("🏃 RUNNER: STEALING 2ND BASE TEST")
   44 |     print("=======================================================")
   45 | 
   46 |     for i in range(1):
   47 |         r_norm_obs = r_vec.reset()
   48 |         done = False
   49 |         
   50 |         while not done:
   51 |             action, _ = r_model.predict(r_norm_obs, deterministic=True)
   52 |             r_norm_obs, reward, dones, infos = r_vec.step(action)
   53 |             done = dones[0]
   54 |             info = infos[0]
   55 |             
   56 |             renderer.update_scene(r_env.data, camera="tracking_cam")
   57 |             frame = renderer.render()
   58 |             
   59 |             dist = info.get("dist", 0.0)
   60 |             cv2.putText(frame, f"STEALING 2ND BASE | Dist: {dist:.1f}m", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
   61 |             
   62 |             if done:
   63 |                 if dist < 1.0:
   64 |                     cv2.putText(frame, "SAFE! (Base Stolen)", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
   65 |                 else:
   66 |                     cv2.putText(frame, "OUT! (Failed to reach)", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
   67 |                     
   68 |             out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
   69 |             if done:
   70 |                 for _ in range(60):
   71 |                     out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
   72 |                     
   73 |         print(f"Runner Attempt {i+1} Final Dist: {dist:.1f}m")
   74 | 
   75 |     out.release()
   76 |     print("=======================================================")
   77 |     print(f"🎥 Video saved to: {video_path}")
   78 | 
   79 | if __name__ == "__main__":
   80 |     main()
````
