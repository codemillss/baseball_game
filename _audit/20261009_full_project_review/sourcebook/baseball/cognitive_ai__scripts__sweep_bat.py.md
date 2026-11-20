# baseball/cognitive_ai/scripts/sweep_bat.py

원본: [cognitive_ai/scripts/sweep_bat.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/sweep_bat.py)

SHA256: `3ac378e266e22fa706c859addac25f61347096e79243d60e6ee6310b9e215f10`

전체 37행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

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
   14 | base_keyframes = np.array([
   15 |     [-0.5, -1.0, 0.0, 0.5, 1.5,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stance
   16 |     [-1.0, -1.2, 0.0, 0.8, 2.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Load
   17 |     [0.0, -0.5, 0.0, 0.0, 1.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stride
   18 |     [1.5, 0.5, 0.0, -0.5, 0.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Contact
   19 |     [2.0, 1.0, 0.0, -1.0, 1.5,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8]  # Follow-through
   20 | ])
   21 | 
   22 | print("Sweeping bat trajectory:")
   23 | for p in np.linspace(0, 1, 11):
   24 |     num_kfs = len(base_keyframes)
   25 |     scaled = p * (num_kfs - 1)
   26 |     idx1 = int(np.floor(scaled))
   27 |     idx2 = min(idx1 + 1, num_kfs - 1)
   28 |     t = scaled - idx1
   29 |     angles = (1-t)*base_keyframes[idx1] + t*base_keyframes[idx2]
   30 |     
   31 |     mujoco.mj_resetData(model, data)
   32 |     for i, adr in enumerate(qpos_adrs):
   33 |         data.qpos[adr] = angles[i]
   34 |     mujoco.mj_forward(model, data)
   35 |     
   36 |     pos = data.geom_xpos[bat_geom_id]
   37 |     print(f"Progress {p:.1f}: Bat pos = X={pos[0]:.2f}, Y={pos[1]:.2f}, Z={pos[2]:.2f}")
````
