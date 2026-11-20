# baseball/cognitive_ai/scripts/test_scaling.py

원본: [cognitive_ai/scripts/test_scaling.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_scaling.py)

SHA256: `b363bd53d8253749ca0623e0a256b496775d98d44e4f2aec15af9bda03af6b74`

전체 51행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test_scaling` | FunctionDef | 9 | 48 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | import numpy as np
    4 | import mujoco
    5 | 
    6 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    7 | from cognitive_ai.envs.teeball_env import TeeBallEnv
    8 | 
    9 | def test_scaling():
   10 |     env = TeeBallEnv()
   11 |     test_zs = np.linspace(0.65, 0.95, 13)
   12 |     
   13 |     # We want action in [-1, 1] to map to a wider, centered pitch_adj range
   14 |     # Let's test pitch_adj = -0.3 + action * 0.7 (maps -1..1 to -1.0..+0.4)
   15 |     
   16 |     reachable = 0
   17 |     mapping = {}
   18 |     for z in test_zs:
   19 |         valid_actions = []
   20 |         for a in np.linspace(-1.0, 1.0, 41):
   21 |             env.reset()
   22 |             env.data.qpos[env.ball_qpos_adr+2] = z
   23 |             mujoco.mj_forward(env.model, env.data)
   24 |             
   25 |             # Custom pitch_adj mapping
   26 |             pitch_adj = -0.3 + a * 0.75
   27 |             env.current_keyframes = env.base_keyframes.copy()
   28 |             env.current_keyframes[3, 1] += pitch_adj
   29 |             env.current_keyframes[4, 1] += pitch_adj
   30 |             
   31 |             done = False
   32 |             hit = False
   33 |             while not done:
   34 |                 obs, reward, terminated, truncated, _ = env.step(np.array([a], dtype=np.float32))
   35 |                 done = terminated or truncated
   36 |                 if reward > 50:
   37 |                     hit = True
   38 |                     break
   39 |             if hit:
   40 |                 valid_actions.append(round(a, 2))
   41 |         mapping[round(z, 3)] = valid_actions
   42 |         if len(valid_actions) > 0:
   43 |             reachable += 1
   44 |             print(f"Z={z:.3f}m -> Reachable! ({len(valid_actions)} actions)")
   45 |         else:
   46 |             print(f"Z={z:.3f}m -> ❌ Miss")
   47 |             
   48 |     print(f"\nNew Reachability: {reachable}/{len(test_zs)} ({(reachable/len(test_zs))*100:.1f}%)")
   49 | 
   50 | if __name__ == "__main__":
   51 |     test_scaling()
````
