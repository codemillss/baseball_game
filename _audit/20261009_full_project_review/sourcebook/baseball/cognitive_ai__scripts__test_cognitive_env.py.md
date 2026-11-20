# baseball/cognitive_ai/scripts/test_cognitive_env.py

원본: [cognitive_ai/scripts/test_cognitive_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_cognitive_env.py)

SHA256: `80fde76a8ba2a23d5bed161cab91eed8bb349b6a855d6d75eac90c1580da9fa0`

전체 27행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test` | FunctionDef | 10 | 24 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | import numpy as np
    3 | import os
    4 | import sys
    5 | 
    6 | # Add parent dir to path so we can import envs
    7 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    8 | from cognitive_ai.envs.cognitive_baseball_env import CognitiveBaseballEnv
    9 | 
   10 | def test():
   11 |     print("Testing Cognitive Baseball Env...")
   12 |     env = CognitiveBaseballEnv(xml_path="shared_assets/stadium_3d.xml", render_mode="human")
   13 |     obs, info = env.reset()
   14 |     
   15 |     for i in range(50):
   16 |         # Action: swing immediately, aim slightly up, swing fast
   17 |         action = np.array([1.0, 0.5, 0.8], dtype=np.float32)
   18 |         obs, reward, term, trunc, info = env.step(action)
   19 |         if term or trunc:
   20 |             print(f"Episode ended at step {i} with reward {reward}")
   21 |             break
   22 |             
   23 |     print("Test finished successfully!")
   24 |     env.close()
   25 | 
   26 | if __name__ == "__main__":
   27 |     test()
````
