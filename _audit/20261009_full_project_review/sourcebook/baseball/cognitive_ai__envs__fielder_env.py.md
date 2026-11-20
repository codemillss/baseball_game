# baseball/cognitive_ai/envs/fielder_env.py

원본: [cognitive_ai/envs/fielder_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/fielder_env.py)

SHA256: `5b4a05e4123371192964ac0666b3417b5c8258d4182690f3a7dacaa7959d8535`

전체 151행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `FielderEnv` | ClassDef | 6 | 150 |
| `__init__` | FunctionDef | 7 | 42 |
| `reset` | FunctionDef | 44 | 77 |
| `_get_obs` | FunctionDef | 79 | 101 |
| `step` | FunctionDef | 103 | 150 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | from gymnasium import spaces
    3 | import numpy as np
    4 | import mujoco
    5 | 
    6 | class FielderEnv(gym.Env):
    7 |     def __init__(self):
    8 |         super().__init__()
    9 |         
   10 |         self.model = mujoco.MjModel.from_xml_path("shared_assets/h1_fielder.xml")
   11 |         self.data = mujoco.MjData(self.model)
   12 |         
   13 |         self.frame_skip = 4
   14 |         self.dt = self.model.opt.timestep * self.frame_skip
   15 |         
   16 |         # 12 Actions: 3 base + 9 upper body
   17 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(12,), dtype=np.float32)
   18 |         
   19 |         # Observation space: 
   20 |         # Ball pos (3), Ball vel (3)
   21 |         # Base pos (x, y) (2), Base yaw (1), Base vel (x, y, yaw) (3)
   22 |         # Upper body pos (9), Upper body vel (9)
   23 |         # Total: 3+3 + 2+1+3 + 9+9 = 30
   24 |         self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(30,), dtype=np.float32)
   25 |         
   26 |         self.upper_joints = [
   27 |             "torso",
   28 |             "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
   29 |             "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"
   30 |         ]
   31 |         
   32 |         self.base_joints = ["base_x", "base_y", "base_yaw"]
   33 |         
   34 |         # Indices
   35 |         self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   36 |         self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   37 |         
   38 |         self.glove_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "glove_site")
   39 |         self.ball_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "ball_site")
   40 |         
   41 |         self.max_steps = 200
   42 |         self.current_step = 0
   43 |         
   44 |     def reset(self, seed=None, options=None):
   45 |         if seed is not None:
   46 |             np.random.seed(seed)
   47 |             
   48 |         mujoco.mj_resetData(self.model, self.data)
   49 |         
   50 |         # Launch ball from origin with random fly ball trajectory
   51 |         vx = np.random.uniform(-10.0, 10.0)
   52 |         vy = np.random.uniform(15.0, 30.0)
   53 |         vz = np.random.uniform(10.0, 25.0)
   54 |         
   55 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 0.0, 1.0]
   56 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
   57 |         
   58 |         # Position fielder roughly where the ball will land
   59 |         # Time of flight approx: t = 2 * vz / 9.81
   60 |         t_flight = 2 * vz / 9.81
   61 |         land_x = vx * t_flight
   62 |         land_y = vy * t_flight
   63 |         
   64 |         # Add some random noise to fielder's starting position so it has to move
   65 |         start_x = land_x + np.random.uniform(-5.0, 5.0)
   66 |         start_y = land_y + np.random.uniform(-5.0, 5.0)
   67 |         
   68 |         base_x_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "base_x")
   69 |         base_y_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "base_y")
   70 |         
   71 |         self.data.qpos[self.model.jnt_qposadr[base_x_id]] = start_x
   72 |         self.data.qpos[self.model.jnt_qposadr[base_y_id]] = start_y
   73 |         
   74 |         mujoco.mj_forward(self.model, self.data)
   75 |         
   76 |         self.current_step = 0
   77 |         return self._get_obs(), {}
   78 |         
   79 |     def _get_obs(self):
   80 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
   81 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
   82 |         
   83 |         base_qpos = []
   84 |         base_qvel = []
   85 |         for j in self.base_joints:
   86 |             jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)
   87 |             base_qpos.append(self.data.qpos[self.model.jnt_qposadr[jid]])
   88 |             base_qvel.append(self.data.qvel[self.model.jnt_dofadr[jid]])
   89 |             
   90 |         up_qpos = []
   91 |         up_qvel = []
   92 |         for j in self.upper_joints:
   93 |             jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)
   94 |             up_qpos.append(self.data.qpos[self.model.jnt_qposadr[jid]])
   95 |             up_qvel.append(self.data.qvel[self.model.jnt_dofadr[jid]])
   96 |             
   97 |         return np.concatenate([
   98 |             ball_pos, ball_vel,
   99 |             base_qpos, base_qvel,
  100 |             up_qpos, up_qvel
  101 |         ]).astype(np.float32)
  102 | 
  103 |     def step(self, action):
  104 |         # Action mappings to actuators
  105 |         # base_x, base_y, base_yaw
  106 |         for i, j in enumerate(self.base_joints):
  107 |             act_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, j)
  108 |             self.data.ctrl[act_id] = action[i] * 5.0 # Max speed/force multiplier
  109 |             
  110 |         # Upper body
  111 |         for i, j in enumerate(self.upper_joints):
  112 |             act_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, j)
  113 |             ctrl_range = self.model.actuator_ctrlrange[act_id]
  114 |             # scale -1 to 1 into ctrl_range
  115 |             val = ctrl_range[0] + (action[i+3] + 1.0) * 0.5 * (ctrl_range[1] - ctrl_range[0])
  116 |             self.data.ctrl[act_id] = val
  117 |             
  118 |         for _ in range(self.frame_skip):
  119 |             mujoco.mj_step(self.model, self.data)
  120 |             
  121 |         self.current_step += 1
  122 |         
  123 |         obs = self._get_obs()
  124 |         
  125 |         # Calculate distance between glove and ball
  126 |         glove_pos = self.data.site_xpos[self.glove_site_id]
  127 |         ball_pos = self.data.site_xpos[self.ball_site_id]
  128 |         dist = np.linalg.norm(glove_pos - ball_pos)
  129 |         
  130 |         reward = -dist * 0.1 # Penalty for being far
  131 |         
  132 |         terminated = False
  133 |         truncated = False
  134 |         info = {"dist": dist}
  135 |         
  136 |         if dist < 0.25:
  137 |             reward += 1000.0
  138 |             terminated = True
  139 |             info["catch"] = True
  140 |             
  141 |         elif ball_pos[2] < 0.2:
  142 |             # Ball hit the ground
  143 |             reward -= 50.0
  144 |             terminated = True
  145 |             info["catch"] = False
  146 |             
  147 |         if self.current_step >= self.max_steps:
  148 |             truncated = True
  149 |             
  150 |         return obs, reward, terminated, truncated, info
  151 | 
````
