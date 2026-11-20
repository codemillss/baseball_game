# baseball/cognitive_ai/scripts/test_trajectory.py

원본: [cognitive_ai/scripts/test_trajectory.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_trajectory.py)

SHA256: `48bb7df23c255464d8fd25438952c4b867931b3262b4b56f6488659c03486636`

전체 23행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | import numpy as np
    3 | 
    4 | model = mujoco.MjModel.from_xml_path("shared_assets/h1_baseball.xml")
    5 | data = mujoco.MjData(model)
    6 | 
    7 | ball_qpos_adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
    8 | ball_qvel_adr = model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
    9 | 
   10 | # Soft toss from 4m
   11 | for vz in [1.0, 1.4, 1.8]:
   12 |     mujoco.mj_resetData(model, data)
   13 |     data.qpos[ball_qpos_adr:ball_qpos_adr+3] = [0.0, 4.0, 1.1]
   14 |     data.qvel[ball_qvel_adr:ball_qvel_adr+3] = [0.0, -8.0, vz]
   15 |     mujoco.mj_forward(model, data)
   16 |     
   17 |     print(f"\n--- Testing Vz = {vz} ---")
   18 |     for step in range(60): # 60 * 0.005 = 0.30s
   19 |         mujoco.mj_step(model, data)
   20 |         pos = data.qpos[ball_qpos_adr:ball_qpos_adr+3]
   21 |         if abs(pos[1] - 0.4) < 0.1: # Home plate reach
   22 |             print(f"Ball reached plate at step {step} (t={step*0.005:.3f}s): Y={pos[1]:.2f}m, Z={pos[2]:.2f}m")
   23 |             break
````
