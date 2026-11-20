# baseball/cognitive_ai/envs/runner_env.py

원본: [cognitive_ai/envs/runner_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/runner_env.py)

SHA256: `3976159d16ab178df44836bac8d12460aa138059bc98a63a1dc87dca872495b1`

전체 83행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `RunnerEnv` | ClassDef | 6 | 83 |
| `__init__` | FunctionDef | 7 | 27 |
| `_get_obs` | FunctionDef | 29 | 38 |
| `reset` | FunctionDef | 40 | 52 |
| `step` | FunctionDef | 54 | 83 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | import mujoco
    3 | import numpy as np
    4 | import os
    5 | 
    6 | class RunnerEnv(gym.Env):
    7 |     def __init__(self, render_mode=None):
    8 |         self.model = mujoco.MjModel.from_xml_path("shared_assets/h1_runner.xml")
    9 |         self.data = mujoco.MjData(self.model)
   10 |         self.render_mode = render_mode
   11 |         
   12 |         # Action: runner_x, runner_y, runner_yaw (3)
   13 |         self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
   14 |         
   15 |         # Obs: base_pos(3), base_vel(3), relative_target(2) -> 8
   16 |         self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(8,), dtype=np.float32)
   17 |         
   18 |         self.actuator_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in [
   19 |             "runner_x", "runner_y", "runner_yaw"
   20 |         ]]
   21 |         
   22 |         # 1st base
   23 |         self.start_pos = np.array([19.4, 19.4])
   24 |         # 2nd base
   25 |         self.target_pos = np.array([0.0, 38.8])
   26 |         
   27 |         self.max_steps = 300
   28 | 
   29 |     def _get_obs(self):
   30 |         base_pos = self.data.qpos[:3]
   31 |         base_vel = self.data.qvel[:3]
   32 |         
   33 |         curr_xy = base_pos[:2]
   34 |         rel_target = self.target_pos - curr_xy
   35 |         
   36 |         return np.concatenate([
   37 |             base_pos, base_vel, rel_target
   38 |         ]).astype(np.float32)
   39 | 
   40 |     def reset(self, seed=None, options=None):
   41 |         super().reset(seed=seed)
   42 |         mujoco.mj_resetData(self.model, self.data)
   43 |         
   44 |         self.current_step = 0
   45 |         
   46 |         # Set pos to 1st base
   47 |         self.data.qpos[0] = self.start_pos[0]
   48 |         self.data.qpos[1] = self.start_pos[1]
   49 |         self.data.qpos[2] = 2.35 # yaw pointing to 2nd base approx (3*pi/4)
   50 |         
   51 |         mujoco.mj_forward(self.model, self.data)
   52 |         return self._get_obs(), {}
   53 | 
   54 |     def step(self, action):
   55 |         for i, act_id in enumerate(self.actuator_ids):
   56 |             if act_id != -1:
   57 |                 self.data.ctrl[act_id] = action[i]
   58 |                 
   59 |         for _ in range(10): # 10 sub-steps
   60 |             mujoco.mj_step(self.model, self.data)
   61 |             
   62 |         self.current_step += 1
   63 |         
   64 |         curr_xy = self.data.qpos[:2]
   65 |         dist = np.linalg.norm(self.target_pos - curr_xy)
   66 |         
   67 |         # Reward for moving closer
   68 |         reward = -dist * 0.05
   69 |         
   70 |         # Speed reward
   71 |         vel = self.data.qvel[:2]
   72 |         speed_towards = np.dot(vel, (self.target_pos - curr_xy) / max(dist, 1e-4))
   73 |         reward += speed_towards * 0.1
   74 |         
   75 |         terminated = False
   76 |         if dist < 1.0:
   77 |             reward += 1000.0
   78 |             terminated = True
   79 |             
   80 |         truncated = self.current_step >= self.max_steps
   81 |         info = {"dist": dist}
   82 |         
   83 |         return self._get_obs(), float(reward), terminated, truncated, info
````
