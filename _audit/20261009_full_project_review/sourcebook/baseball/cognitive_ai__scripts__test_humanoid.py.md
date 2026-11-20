# baseball/cognitive_ai/scripts/test_humanoid.py

원본: [cognitive_ai/scripts/test_humanoid.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_humanoid.py)

SHA256: `e959968d967c06152303647eea8414b25739f4550ac1009f764e346d8f90a691`

전체 32행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `test_humanoid` | FunctionDef | 6 | 29 |

## 전체 원문

````text
    1 | import mujoco
    2 | from mujoco import viewer
    3 | import time
    4 | import numpy as np
    5 | 
    6 | def test_humanoid():
    7 |     model = mujoco.MjModel.from_xml_path('shared_assets/humanoid_stadium.xml')
    8 |     data = mujoco.MjData(model)
    9 |     
   10 |     print("Testing Humanoid Baseball Environment...")
   11 |     
   12 |     with viewer.launch_passive(model, data) as v:
   13 |         t = 0
   14 |         while v.is_running():
   15 |             # Slowly rotate spine and move right arm to simulate a swing
   16 |             spine_twist = np.sin(t * 2) * 1.5
   17 |             r_shoulder_y = np.cos(t * 2) * 1.5 - 1.0 # Lift arm up/down
   18 |             
   19 |             # Find actuator addresses
   20 |             spine_adr = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "a_spine_twist")
   21 |             rsy_adr = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "a_r_shoulder_y")
   22 |             
   23 |             data.ctrl[spine_adr] = spine_twist
   24 |             data.ctrl[rsy_adr] = r_shoulder_y
   25 |             
   26 |             mujoco.mj_step(model, data)
   27 |             v.sync()
   28 |             time.sleep(0.01)
   29 |             t += 0.01
   30 | 
   31 | if __name__ == "__main__":
   32 |     test_humanoid()
````
