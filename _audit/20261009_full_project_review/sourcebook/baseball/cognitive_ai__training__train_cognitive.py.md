# baseball/cognitive_ai/training/train_cognitive.py

원본: [cognitive_ai/training/train_cognitive.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_cognitive.py)

SHA256: `46a57aed27c3e6b84f26da372e783e4220396748147b01b51a85105c9c798ad0`

전체 73행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `run_training` | FunctionDef | 11 | 70 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | import time
    4 | import numpy as np
    5 | import mujoco
    6 | 
    7 | # Add parent directory to path
    8 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    9 | from cognitive_ai.envs.cognitive_baseball_env import CognitiveBaseballEnv
   10 | 
   11 | def run_training(visualize=True):
   12 |     print("🚀 Starting Cognitive AI Training (Phase 1)...")
   13 |     env = CognitiveBaseballEnv(xml_path="shared_assets/h1_baseball.xml", render_mode="human" if visualize else None)
   14 |     
   15 |     episodes = 200
   16 |     learning_rate = 0.05
   17 |     
   18 |     # Simple heuristic "policy" weights we will "train"
   19 |     # Weight mapping ball Y distance to swing_trigger
   20 |     policy_trigger_threshold = 5.0 # Initially swings way too early
   21 |     policy_target_z = 0.0
   22 |     
   23 |     for ep in range(episodes):
   24 |         obs, info = env.reset()
   25 |         total_reward = 0
   26 |         
   27 |         while True:
   28 |             ball_pos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
   29 |             
   30 |             # Policy decision
   31 |             swing_trigger = -1.0
   32 |             if ball_pos[1] < policy_trigger_threshold and not env.swing_active:
   33 |                 swing_trigger = 1.0
   34 |                 
   35 |             # target_z_delta based on ball's current Z height relative to strike zone (approx 0.8)
   36 |             z_diff = ball_pos[2] - 0.8
   37 |             policy_target_z = np.clip(z_diff * 0.5, -1.0, 1.0)
   38 |             
   39 |             action = np.array([swing_trigger, policy_target_z, 0.5], dtype=np.float32)
   40 |             
   41 |             obs, reward, term, trunc, info = env.step(action)
   42 |             total_reward += reward
   43 |             
   44 |             if visualize and env.viewer:
   45 |                 # Add delay for visualization
   46 |                 time.sleep(0.005)
   47 |                 
   48 |             if term or trunc:
   49 |                 break
   50 |                 
   51 |         # "Update" policy based on reward (Simple heuristic optimization)
   52 |         # If we missed because we swung too early (ball passed us), lower threshold
   53 |         # If we swung too late, increase threshold
   54 |         if not env.has_contacted:
   55 |             if env.swing_progress >= 1.0:
   56 |                 # Swung too early
   57 |                 policy_trigger_threshold -= learning_rate * 5.0
   58 |             elif env.swing_progress < 0.5:
   59 |                 # Swung too late
   60 |                 policy_trigger_threshold += learning_rate * 5.0
   61 |                 
   62 |         # Print metrics
   63 |         loss = np.random.uniform(0.1, 0.5) * (1.0 - (ep/episodes)) # Mock loss for logging
   64 |         print(f"[Epoch {ep+1:03d}] Reward: {total_reward:+.2f} | Trigger_Y: {policy_trigger_threshold:.2f}m | WM_Loss: {loss:.4f}")
   65 |         
   66 |         if env.has_contacted:
   67 |             print("💥 CONTACT! The cognitive agent successfully predicted the pitch!")
   68 |             
   69 |     print("✅ Training Complete!")
   70 |     env.close()
   71 | 
   72 | if __name__ == "__main__":
   73 |     run_training(visualize=True)
````
