# baseball/cognitive_ai/scripts/check_contact_pos.py

원본: [cognitive_ai/scripts/check_contact_pos.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/check_contact_pos.py)

SHA256: `c82f577ee4d2c4d9bc03056014a71efe0f781a49c806b22f6db1c7d7b1e680bb`

전체 23행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | import numpy as np
    3 | 
    4 | model = mujoco.MjModel.from_xml_path("shared_assets/h1_baseball.xml")
    5 | data = mujoco.MjData(model)
    6 | 
    7 | bat_geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
    8 | joint_names = [
    9 |     "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
   10 |     "left_hip_roll", "left_hip_pitch", "left_knee", "right_hip_roll", "right_hip_pitch", "right_knee"
   11 | ]
   12 | qpos_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in joint_names]
   13 | 
   14 | # Keyframe 3 (Contact)
   15 | contact_kf = np.array([1.5, 0.5 - 0.8, 0.0, -0.5, 0.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8])
   16 | 
   17 | mujoco.mj_resetData(model, data)
   18 | for i, adr in enumerate(qpos_adrs):
   19 |     data.qpos[adr] = contact_kf[i]
   20 | mujoco.mj_forward(model, data)
   21 | 
   22 | bat_pos = data.geom_xpos[bat_geom_id]
   23 | print(f"Bat Barrel Center Position at Contact: X={bat_pos[0]:.3f}, Y={bat_pos[1]:.3f}, Z={bat_pos[2]:.3f}")
````
