# baseball/cognitive_ai/envs/catcher_env.py

원본: [cognitive_ai/envs/catcher_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/catcher_env.py)

SHA256: `5667e7ec30bbbe9c1dc85ab26b33fe43a580ceb4e6039227f660549ea08000b1`

전체 96행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `CatcherEnv` | ClassDef | 6 | 96 |
| `__init__` | FunctionDef | 7 | 26 |
| `_get_obs` | FunctionDef | 28 | 38 |
| `reset` | FunctionDef | 40 | 59 |
| `step` | FunctionDef | 61 | 96 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | import mujoco
    3 | import numpy as np
    4 | import os
    5 | 
    6 | class CatcherEnv(gym.Env):
    7 |     def __init__(self, render_mode=None):
    8 |         self.model = mujoco.MjModel.from_xml_path("shared_assets/h1_catcher.xml")
    9 |         self.data = mujoco.MjData(self.model)
   10 |         self.render_mode = render_mode
   11 |         
   12 |         self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(12,), dtype=np.float32)
   13 |         # obs: base_qpos(3), base_qvel(3), arm_qpos(9), arm_qvel(9), ball_pos(3), ball_vel(3) => 30
   14 |         self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(30,), dtype=np.float32)
   15 |         
   16 |         self.glove_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "glove_box")
   17 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   18 |         self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   19 |         self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   20 |         
   21 |         self.actuator_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in [
   22 |             "catcher_x", "catcher_y", "catcher_yaw",
   23 |             "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
   24 |             "torso_yaw", "torso_pitch", "torso_roll", "left_hip_yaw", "left_hip_roll" # fillers
   25 |         ]]
   26 |         self.max_steps = 150
   27 | 
   28 |     def _get_obs(self):
   29 |         base_qpos = self.data.qpos[:3]
   30 |         base_qvel = self.data.qvel[:3]
   31 |         arm_qpos = self.data.qpos[3:12]
   32 |         arm_qvel = self.data.qvel[3:12]
   33 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
   34 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
   35 |         
   36 |         return np.concatenate([
   37 |             base_qpos, base_qvel, arm_qpos, arm_qvel, ball_pos, ball_vel
   38 |         ]).astype(np.float32)
   39 | 
   40 |     def reset(self, seed=None, options=None):
   41 |         super().reset(seed=seed)
   42 |         mujoco.mj_resetData(self.model, self.data)
   43 |         
   44 |         self.current_step = 0
   45 |         
   46 |         # Pitch ball from mound (y=18.4) to home (y=0)
   47 |         # Add some random variance to pitch location (Strike zone + wild pitches)
   48 |         target_x = np.random.uniform(-0.5, 0.5)
   49 |         target_z = np.random.uniform(0.1, 1.5)
   50 |         
   51 |         vx = target_x / 0.4  # arrives in ~0.4 sec
   52 |         vy = -18.4 / 0.4
   53 |         vz = (target_z - 1.5 + 0.5 * 9.81 * 0.4**2) / 0.4
   54 |         
   55 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0, 18.4, 1.5]
   56 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
   57 |         
   58 |         mujoco.mj_forward(self.model, self.data)
   59 |         return self._get_obs(), {}
   60 | 
   61 |     def step(self, action):
   62 |         for i, act_id in enumerate(self.actuator_ids[:10]): # Only use first 10 for actual arm/base
   63 |             if act_id != -1:
   64 |                 self.data.ctrl[act_id] = action[i]
   65 |                 
   66 |         for _ in range(10): # 10 sub-steps
   67 |             mujoco.mj_step(self.model, self.data)
   68 |             
   69 |         self.current_step += 1
   70 |         
   71 |         glove_pos = self.data.geom_xpos[self.glove_geom_id]
   72 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
   73 |         
   74 |         dist = np.linalg.norm(glove_pos - ball_pos)
   75 |         
   76 |         reward = -dist * 0.1
   77 |         terminated = False
   78 |         caught = False
   79 |         
   80 |         for i in range(self.data.ncon):
   81 |             contact = self.data.contact[i]
   82 |             if (contact.geom1 == self.glove_geom_id and contact.geom2 == self.ball_geom_id) or \
   83 |                (contact.geom2 == self.glove_geom_id and contact.geom1 == self.ball_geom_id):
   84 |                 reward += 1000.0
   85 |                 terminated = True
   86 |                 caught = True
   87 |                 break
   88 |                 
   89 |         if ball_pos[1] < -2.0 or ball_pos[2] < 0.1:
   90 |             terminated = True
   91 |             reward -= 50.0
   92 |             
   93 |         truncated = self.current_step >= self.max_steps
   94 |         info = {"catch": caught, "dist": dist}
   95 |         
   96 |         return self._get_obs(), float(reward), terminated, truncated, info
````
