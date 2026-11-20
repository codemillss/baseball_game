# baseball/cognitive_ai/envs/teeball_env.py

원본: [cognitive_ai/envs/teeball_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/teeball_env.py)

SHA256: `7a99741fdb43df9435102a22b8e8f23812ae8bd419ba2b9869e64e169a470c2f`

전체 170행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `TeeBallEnv` | ClassDef | 6 | 170 |
| `__init__` | FunctionDef | 12 | 56 |
| `reset` | FunctionDef | 58 | 81 |
| `step` | FunctionDef | 83 | 138 |
| `_update_swing_kinematics` | FunctionDef | 140 | 153 |
| `_check_contact` | FunctionDef | 155 | 161 |
| `_get_obs` | FunctionDef | 163 | 166 |
| `close` | FunctionDef | 168 | 170 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | from gymnasium import spaces
    3 | import mujoco
    4 | import numpy as np
    5 | 
    6 | class TeeBallEnv(gym.Env):
    7 |     """
    8 |     Phase 1-A: Tee-ball Environment (State-based)
    9 |     공은 특정 위치(가상의 티대 위)에 정지해 있으며, 픽셀 대신 공의 절대 좌표(X,Y,Z)를 Observation으로 받습니다.
   10 |     에이전트는 [스윙_트리거, 타격_높이_조절] 액션을 통해 공을 맞추는 법을 학습합니다.
   11 |     """
   12 |     def __init__(self, xml_path="shared_assets/h1_baseball.xml", render_mode=None):
   13 |         super().__init__()
   14 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   15 |         
   16 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   17 |         self.data = mujoco.MjData(self.model)
   18 |         
   19 |         # Observation: [ball_x, ball_y, ball_z]
   20 |         self.observation_space = spaces.Box(low=-10.0, high=10.0, shape=(3,), dtype=np.float32)
   21 |         
   22 |         # Action: [target_z_delta]
   23 |         # Controls the vertical bat height adjustment to match the ball height
   24 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
   25 |         
   26 |         self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   27 |         self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   28 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   29 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   30 |         
   31 |         # Humanoid joints to control kinematically (Upper body + Legs for wide stance)
   32 |         self.joint_names = [
   33 |             "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
   34 |             "left_hip_roll", "left_hip_pitch", "left_knee", "right_hip_roll", "right_hip_pitch", "right_knee"
   35 |         ]
   36 |         self.qpos_adrs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.joint_names]
   37 |         
   38 |         # Base Keyframes [torso, rs_p, rs_r, rs_y, r_elbow, l_hr, l_hp, l_k, r_hr, r_hp, r_k]
   39 |         self.base_keyframes = np.array([
   40 |             [-0.5, -1.0, 0.0, 0.5, 1.5,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stance
   41 |             [-1.0, -1.2, 0.0, 0.8, 2.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Load
   42 |             [0.0, -0.5, 0.0, 0.0, 1.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stride (Hip turn only)
   43 |             [1.5, 0.5, 0.0, -0.5, 0.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Contact
   44 |             [2.0, 1.0, 0.0, -1.0, 1.5,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8]  # Follow-through
   45 |         ])
   46 |         
   47 |         self.render_mode = render_mode
   48 |         if render_mode == "human":
   49 |             from mujoco import viewer
   50 |             self.viewer = viewer.launch_passive(self.model, self.data)
   51 |         else:
   52 |             self.viewer = None
   53 |             
   54 |         self.frame_skip = 2
   55 |         self.max_steps = 40
   56 |         self.current_step = 0
   57 | 
   58 |     def reset(self, seed=None, options=None):
   59 |         super().reset(seed=seed)
   60 |         mujoco.mj_resetData(self.model, self.data)
   61 |         
   62 |         self.swing_active = True
   63 |         self.swing_progress = 0.0
   64 |         self.swing_duration_frames = 25
   65 |         self.has_contacted = False
   66 |         self.current_keyframes = self.base_keyframes.copy()
   67 |         self.current_step = 0
   68 |         self.min_dist = 999.0
   69 |         
   70 |         # Place ball randomly on the tee (varying height Z between 0.65m and 0.95m)
   71 |         ball_z = np.random.uniform(0.65, 0.95)
   72 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 0.4, ball_z]
   73 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, 0.0, 0.0]
   74 |         
   75 |         # Counteract gravity for the ball (Tee-ball effect)
   76 |         self.model.body_mass[self.ball_body_id] = 1e-6 
   77 |         
   78 |         self._update_swing_kinematics(0.0)
   79 |         mujoco.mj_forward(self.model, self.data)
   80 |         
   81 |         return self._get_obs(), {}
   82 | 
   83 |     def step(self, action):
   84 |         target_z_delta = float(action[0])
   85 |         
   86 |         # Linear kinematic mapping for full strike zone reachability (0.65m ~ 0.95m)
   87 |         # action = -1.0 (low ball) -> pitch_adj = -0.25
   88 |         # action = 0.0  (mid ball) -> pitch_adj = -0.80
   89 |         # action = +1.0 (high ball) -> pitch_adj = -1.35
   90 |         pitch_adj = -0.80 - target_z_delta * 0.55
   91 |         self.current_keyframes = self.base_keyframes.copy()
   92 |         self.current_keyframes[3, 1] += pitch_adj # Contact shoulder pitch
   93 |         self.current_keyframes[4, 1] += pitch_adj # Follow-through shoulder pitch
   94 |         
   95 |         reward = 0.0
   96 |         
   97 |         for _ in range(self.frame_skip):
   98 |             if self.swing_progress < 1.0:
   99 |                 self._update_swing_kinematics(self.swing_progress)
  100 |                 self.swing_progress += 1.0 / self.swing_duration_frames
  101 |                 
  102 |             mujoco.mj_step(self.model, self.data)
  103 |             
  104 |             # Track distance between bat barrel and ball
  105 |             bat_pos = self.data.geom_xpos[self.bat_geom_id]
  106 |             ball_pos = self.data.geom_xpos[self.ball_geom_id]
  107 |             dist = np.linalg.norm(bat_pos - ball_pos)
  108 |             self.min_dist = min(self.min_dist, dist)
  109 |             
  110 |             # Keep ball stationary before hit
  111 |             if not self.has_contacted:
  112 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0, 0, 0]
  113 |             
  114 |             if not self.has_contacted and self._check_contact():
  115 |                 self.has_contacted = True
  116 |                 reward += 100.0  # Big reward for hitting the ball!
  117 |                 
  118 |         if self.viewer:
  119 |             self.viewer.sync()
  120 |             
  121 |         self.current_step += 1
  122 |         
  123 |         terminated = False
  124 |         truncated = False
  125 |         
  126 |         if self.has_contacted or self.swing_progress >= 1.0:
  127 |             terminated = True
  128 |             if self.has_contacted:
  129 |                 reward += 100.0  # Big bonus for contact
  130 |             else:
  131 |                 # Dense quadratic penalty: closer = higher reward
  132 |                 # min_dist ~ 0.05m -> -0.125, min_dist ~ 0.3m -> -4.5
  133 |                 reward -= 50.0 * (self.min_dist ** 2)
  134 |             
  135 |         if self.current_step >= self.max_steps:
  136 |             truncated = True
  137 |                 
  138 |         return self._get_obs(), reward, terminated, truncated, {}
  139 | 
  140 |     def _update_swing_kinematics(self, progress):
  141 |         num_kfs = len(self.current_keyframes)
  142 |         scaled = progress * (num_kfs - 1)
  143 |         idx1 = int(np.floor(scaled))
  144 |         idx2 = min(idx1 + 1, num_kfs - 1)
  145 |         t = scaled - idx1
  146 |         
  147 |         current_angles = (1-t)*self.current_keyframes[idx1] + t*self.current_keyframes[idx2]
  148 |         
  149 |         for i, adr in enumerate(self.qpos_adrs):
  150 |             self.data.qpos[adr] = current_angles[i]
  151 |             jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, self.joint_names[i])
  152 |             vel_adr = self.model.jnt_dofadr[jnt_id]
  153 |             self.data.qvel[vel_adr] = 0.0
  154 | 
  155 |     def _check_contact(self):
  156 |         for i in range(self.data.ncon):
  157 |             contact = self.data.contact[i]
  158 |             if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \
  159 |                (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
  160 |                 return True
  161 |         return False
  162 | 
  163 |     def _get_obs(self):
  164 |         # Observation is just the ball's absolute position [X, Y, Z]
  165 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  166 |         return ball_pos.astype(np.float32)
  167 | 
  168 |     def close(self):
  169 |         if self.viewer:
  170 |             self.viewer.close()
````
