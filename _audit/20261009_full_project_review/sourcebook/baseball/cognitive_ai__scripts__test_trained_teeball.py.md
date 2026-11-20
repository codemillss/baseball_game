# baseball/cognitive_ai/scripts/test_trained_teeball.py

원본: [cognitive_ai/scripts/test_trained_teeball.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_trained_teeball.py)

SHA256: `6cdb2aee027878d6d58c5817788bc31d7d42005148ded364d93067393de7b7f5`

전체 54행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `watch_trained_agent` | FunctionDef | 10 | 51 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | import time
    4 | from stable_baselines3 import PPO
    5 | 
    6 | # Add parent directory to path
    7 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    8 | from cognitive_ai.envs.teeball_env import TeeBallEnv
    9 | 
   10 | def watch_trained_agent():
   11 |     print("🚀 Loading Trained Tee-ball Agent...")
   12 |     
   13 |     # Load the best model or final model
   14 |     model_path = "checkpoints/teeball_best_model/best_model"
   15 |     if not os.path.exists(model_path + ".zip"):
   16 |         model_path = "checkpoints/teeball_final_model"
   17 |         
   18 |     if not os.path.exists(model_path + ".zip"):
   19 |         print(f"❌ Model not found at {model_path}. Run training first.")
   20 |         return
   21 |         
   22 |     model = PPO.load(model_path)
   23 |     env = TeeBallEnv(xml_path="shared_assets/h1_baseball.xml", render_mode="human")
   24 |     
   25 |     print("⚾ Agent loaded! Starting simulation... (Close window or Ctrl+C to stop)")
   26 |     
   27 |     ep = 0
   28 |     try:
   29 |         while True:
   30 |             ep += 1
   31 |             obs, _ = env.reset()
   32 |             done = False
   33 |             step = 0
   34 |             
   35 |             while not done:
   36 |                 action, _states = model.predict(obs, deterministic=True)
   37 |                 obs, reward, terminated, truncated, _ = env.step(action)
   38 |                 done = terminated or truncated
   39 |                 step += 1
   40 |                 
   41 |                 # Smooth viewing
   42 |                 time.sleep(0.02)
   43 |                 
   44 |                 if reward > 50:
   45 |                     print(f"💥 [Episode {ep}] HIT THE BALL! (Ball Z: {obs[2]:.2f}m, Step: {step})")
   46 |                     
   47 |             time.sleep(0.5)
   48 |     except KeyboardInterrupt:
   49 |         print("\nSimulation stopped.")
   50 |     finally:
   51 |         env.close()
   52 | 
   53 | if __name__ == "__main__":
   54 |     watch_trained_agent()
````
