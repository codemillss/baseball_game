# baseball/cognitive_ai/scripts/test_teeball.py

원본: [cognitive_ai/scripts/test_teeball.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_teeball.py)

SHA256: `2907fccb0982d3e3f70ef8448ccf6daa310607ba2cc1bdbe5576d3038815075b`

전체 45행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test_heuristic_swing` | FunctionDef | 10 | 42 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | import time
    4 | import numpy as np
    5 | 
    6 | # Add parent directory to path
    7 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    8 | from cognitive_ai.envs.teeball_env import TeeBallEnv
    9 | 
   10 | def test_heuristic_swing():
   11 |     print("🚀 Starting Tee-ball Heuristic Test...")
   12 |     env = TeeBallEnv(xml_path="shared_assets/h1_baseball.xml", render_mode="human")
   13 |     
   14 |     for ep in range(3):
   15 |         obs = env.reset()
   16 |         ball_z = obs[0][2] if isinstance(obs, tuple) else obs[2]
   17 |         print(f"Episode {ep+1}: Ball height is {ball_z:.2f}m")
   18 |         
   19 |         # Calculate heuristic target_z_delta based on ball height
   20 |         # Base contact height is ~0.8m
   21 |         z_delta = (ball_z - 0.8) * 1.5 
   22 |         z_delta = np.clip(z_delta, -1.0, 1.0)
   23 |         
   24 |         for step in range(60):
   25 |             # Trigger swing at step 10
   26 |             trigger = 1.0 if step == 10 else -1.0
   27 |             action = np.array([trigger, z_delta], dtype=np.float32)
   28 |             
   29 |             obs_out, reward, terminated, truncated, _ = env.step(action)
   30 |             
   31 |             if reward > 0:
   32 |                 print(f"💥 Hit the ball at step {step}! Reward: {reward}")
   33 |             
   34 |             time.sleep(0.02)
   35 |             
   36 |             if terminated or truncated:
   37 |                 print("Episode ended.")
   38 |                 break
   39 |                 
   40 |         time.sleep(1)
   41 |         
   42 |     env.close()
   43 | 
   44 | if __name__ == "__main__":
   45 |     test_heuristic_swing()
````
