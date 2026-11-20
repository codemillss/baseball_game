# baseball/cognitive_ai/scripts/check_ball_phys.py

원본: [cognitive_ai/scripts/check_ball_phys.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/check_ball_phys.py)

SHA256: `78b240e94d83c88bf573ebac8ec0df31e182ff68159b4ca8374cc1c3c6abbd26`

전체 20행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

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
   10 | mujoco.mj_resetData(model, data)
   11 | data.qpos[ball_qpos_adr:ball_qpos_adr+3] = [0.0, 4.0, 1.0]
   12 | data.qvel[ball_qvel_adr:ball_qvel_adr+3] = [0.0, -8.0, 1.6]
   13 | mujoco.mj_forward(model, data)
   14 | 
   15 | for step in range(120):
   16 |     mujoco.mj_step(model, data)
   17 |     pos = data.qpos[ball_qpos_adr:ball_qpos_adr+3]
   18 |     vel = data.qvel[ball_qvel_adr:ball_qvel_adr+3]
   19 |     if step % 10 == 0:
   20 |         print(f"Frame {step:3d} (t={step*0.005:.3f}s): Y={pos[1]:.2f}m, Z={pos[2]:.2f}m, Vy={vel[1]:.2f}m/s, Vz={vel[2]:.2f}m/s")
````
