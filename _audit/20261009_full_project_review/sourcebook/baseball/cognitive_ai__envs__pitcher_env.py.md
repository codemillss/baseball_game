# baseball/cognitive_ai/envs/pitcher_env.py

원본: [cognitive_ai/envs/pitcher_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/pitcher_env.py)

SHA256: `1d5253ba7806cc404bc995a146ed62c193751d354239cd2e2311f44d62e77ccb`

전체 254행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `PitcherEnv` | ClassDef | 6 | 254 |
| `__init__` | FunctionDef | 19 | 86 |
| `set_kf` | FunctionDef | 58 | 61 |
| `reset` | FunctionDef | 88 | 112 |
| `step` | FunctionDef | 114 | 221 |
| `_set_arm_pose` | FunctionDef | 223 | 225 |
| `_update_arm_kinematics` | FunctionDef | 228 | 236 |
| `_get_obs` | FunctionDef | 238 | 250 |
| `close` | FunctionDef | 252 | 254 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | from gymnasium import spaces
    3 | import mujoco
    4 | import numpy as np
    5 | 
    6 | class PitcherEnv(gym.Env):
    7 |     """
    8 |     Phase 2: Embodied Humanoid Pitcher Environment (Unitree H1)
    9 |     - Robot stands on the mound at y = 10.0m (or configurable distance).
   10 |     - Objective: Pitch the ball into the designated Strike Zone at Home Plate (y = 0.20m).
   11 |     - Action Space (4-dim):
   12 |         [0]: release_timing (0.3 ~ 0.8 progress of throwing motion)
   13 |         [1]: target_z_aim (-1.0 ~ 1.0 vertical angle adjustment)
   14 |         [2]: target_x_aim (-1.0 ~ 1.0 horizontal course adjustment)
   15 |         [3]: arm_velocity_scale (0.8 ~ 1.6 throw power multiplier)
   16 |     - Observation Space (13-dim):
   17 |         [target_x, target_z, is_released, ball_x, ball_y, ball_z, ball_vx, ball_vy, ball_vz, hand_x, hand_y, hand_z, progress]
   18 |     """
   19 |     def __init__(self, xml_path="shared_assets/h1_pitcher.xml", mound_distance=10.0, render_mode=None):
   20 |         super().__init__()
   21 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   22 |         self.data = mujoco.MjData(self.model)
   23 |         self.mound_distance = mound_distance
   24 |         
   25 |         # 18-dim observation (13 + 1 (progress) + 1 (target_pitch) + 3 (one-hot pitch type) - actually 18D)
   26 |         # target_x, target_z, is_released, throw_progress, ball_xyz, ball_vxyz, hand_xyz, pitch_one_hot (3D)
   27 |         # Total = 2 + 2 + 3 + 3 + 3 + 3 = 16D. Let's recount: 
   28 |         # target_x(1), target_z(1), is_rel(1), prog(1), ball_pos(3), ball_vel(3), hand_pos(3), onehot(3)
   29 |         # 1 + 1 + 1 + 1 + 3 + 3 + 3 + 3 = 16D
   30 |         self.observation_space = spaces.Box(low=-100.0, high=100.0, shape=(16,), dtype=np.float32)
   31 |         
   32 |         # 4-dim action: [release_timing, z_aim, x_aim, velocity_scale]
   33 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
   34 |         
   35 |         self.hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "pitcher_hand_site")
   36 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   37 |         self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   38 |         self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   39 |         
   40 |         self.joint_names = [
   41 |             "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
   42 |             "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
   43 |             "torso",
   44 |             "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
   45 |             "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"
   46 |         ]
   47 |         
   48 |         self.valid_indices = []
   49 |         self.qpos_adrs = []
   50 |         for i, n in enumerate(self.joint_names):
   51 |             jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
   52 |             if jid != -1:
   53 |                 self.valid_indices.append(i)
   54 |                 self.qpos_adrs.append(self.model.jnt_qposadr[jid])
   55 |         self.qvel_adrs = [self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.joint_names]
   56 |         
   57 |         self.base_keyframes = np.zeros((6, 19))
   58 |         def set_kf(idx, **kwargs):
   59 |             for k, v in kwargs.items():
   60 |                 j_idx = self.joint_names.index(k)
   61 |                 self.base_keyframes[idx, j_idx] = v
   62 |         set_kf(0, torso=-1.57, left_elbow=1.5, right_elbow=1.5)
   63 |         set_kf(1, torso=-1.57, left_hip_pitch=-1.5, left_knee=1.8, left_elbow=1.5, right_elbow=1.5)
   64 |         set_kf(2, torso=-1.57, left_hip_pitch=-0.5, left_knee=0.2, left_shoulder_pitch=-0.5, left_elbow=0.5, right_shoulder_pitch=-1.0, right_shoulder_roll=-1.0, right_elbow=0.5)
   65 |         set_kf(3, torso=-0.5, left_hip_pitch=0.0, left_knee=0.2, left_shoulder_pitch=-1.5, left_elbow=0.2, right_shoulder_pitch=-2.0, right_shoulder_roll=-1.5, right_shoulder_yaw=1.0, right_elbow=1.5)
   66 |         set_kf(4, torso=0.5, left_hip_pitch=0.0, left_knee=0.1, left_shoulder_pitch=1.0, left_elbow=0.5, right_shoulder_pitch=1.5, right_shoulder_roll=-0.2, right_shoulder_yaw=0.0, right_elbow=0.1, right_hip_pitch=0.5)
   67 |         set_kf(5, torso=1.2, left_hip_pitch=0.0, left_knee=0.3, left_shoulder_pitch=1.5, left_elbow=1.0, right_shoulder_pitch=2.2, right_shoulder_roll=-1.0, right_shoulder_yaw=-0.5, right_elbow=0.5, right_hip_pitch=1.0, right_knee=1.0)
   68 |         
   69 |         self.render_mode = render_mode
   70 |         self.viewer = None
   71 |         self.frame_skip = 2
   72 |         self.max_steps = 70
   73 |         self.current_step = 0
   74 |         
   75 |         self.target_x = 0.0
   76 |         self.target_z = 0.815
   77 |         
   78 |         self.is_released = False
   79 |         self.release_step = None
   80 |         self.release_speed_kmh = 0.0
   81 |         self.min_dist_to_target = 999.0
   82 |         self.reached_plate = False
   83 |         
   84 |         # Pitch type state
   85 |         self.target_pitch_type = 0
   86 |         self.extra_acc = np.array([0.0, 0.0, 0.0])
   87 | 
   88 |     def reset(self, seed=None, options=None):
   89 |         super().reset(seed=seed)
   90 |         mujoco.mj_resetData(self.model, self.data)
   91 |         
   92 |         self.is_released = False
   93 |         self.release_step = None
   94 |         self.release_speed_kmh = 0.0
   95 |         self.min_dist_to_target = 999.0
   96 |         self.reached_plate = False
   97 |         self.current_step = 0
   98 |         self.throw_progress = 0.0
   99 |         self.extra_acc = np.array([0.0, 0.0, 0.0])
  100 |         
  101 |         self.target_x = float(np.random.uniform(-0.12, 0.12))
  102 |         self.target_z = float(np.random.uniform(0.70, 0.93))
  103 |         
  104 |         # Randomly select target pitch type (0: Fastball, 1: Slider, 2: Curveball)
  105 |         self.target_pitch_type = np.random.choice([0, 1, 2])
  106 |         
  107 |         self.data.eq_active[0] = True
  108 |         
  109 |         self._set_arm_pose(self.base_keyframes[0])
  110 |         mujoco.mj_forward(self.model, self.data)
  111 |         
  112 |         return self._get_obs(), {}
  113 | 
  114 |     def step(self, action):
  115 |         release_progress_target = 0.60 + 0.15 * float(np.clip(action[0], -1.0, 1.0))
  116 |         z_aim_delta = float(action[1]) * 0.4
  117 |         x_aim_delta = float(action[2]) * 0.3
  118 |         
  119 |         # Velocity scale for 150km/h (+). [-1, 1] -> [0.8, 2.5]. 2.5 * 18 = 45m/s (162km/h)
  120 |         vel_scale = 0.8 + 1.7 * (float(action[3]) + 1.0) / 2.0
  121 |         total_motion_frames = int(np.clip(16 / vel_scale, 8, 24))
  122 |         
  123 |         kfs = self.base_keyframes.copy()
  124 |         kfs[2:, 0] += x_aim_delta
  125 |         kfs[2:, 1] += z_aim_delta
  126 |         kfs[2:, 2] -= x_aim_delta * 0.5
  127 |         
  128 |         reward = 0.0
  129 |         terminated = False
  130 |         truncated = False
  131 |         dt = self.model.opt.timestep
  132 |         
  133 |         for _ in range(self.frame_skip):
  134 |             if self.throw_progress < 1.0:
  135 |                 self.throw_progress += 1.0 / total_motion_frames
  136 |                 self._update_arm_kinematics(self.throw_progress, kfs)
  137 |                 
  138 |                 if not self.is_released and self.throw_progress >= release_progress_target:
  139 |                     self.is_released = True
  140 |                     self.data.eq_active[0] = False
  141 |                     self.release_step = self.current_step
  142 |                     
  143 |                     # Direct momentum injection
  144 |                     base_vy = -18.0 * vel_scale
  145 |                     base_vz = 2.2 + z_aim_delta * 4.0
  146 |                     base_vx = -x_aim_delta * 3.5
  147 |                     
  148 |                     # Add spin physics based on pitch type
  149 |                     if self.target_pitch_type == 0:
  150 |                         # Fastball: slight upward magnus (hopping effect)
  151 |                         self.extra_acc = np.array([0.0, 0.0, 3.0])
  152 |                         # Extra velocity for fastball
  153 |                         base_vy *= 1.1 
  154 |                     elif self.target_pitch_type == 1:
  155 |                         # Slider: breaks horizontally
  156 |                         self.extra_acc = np.array([4.5, 0.0, 0.0])
  157 |                         # Slightly slower
  158 |                         base_vy *= 0.90
  159 |                     else:
  160 |                         # Curveball: sharp drop
  161 |                         self.extra_acc = np.array([-1.5, 0.0, -4.5])
  162 |                         # Much slower
  163 |                         base_vy *= 0.80
  164 | 
  165 |                     self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [base_vx, base_vy, base_vz]
  166 |                     
  167 |                     bvel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  168 |                     self.release_speed_kmh = float(np.linalg.norm(bvel) * 3.6)
  169 |             
  170 |             # Apply magnus force to the ball if released
  171 |             if self.is_released:
  172 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += self.extra_acc * dt
  173 |                 
  174 |             mujoco.mj_step(self.model, self.data)
  175 |             
  176 |             ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  177 |             
  178 |             if ball_pos[1] <= 0.20 and not self.reached_plate:
  179 |                 self.reached_plate = True
  180 |                 dist = np.sqrt((ball_pos[0] - self.target_x)**2 + (ball_pos[2] - self.target_z)**2)
  181 |                 self.min_dist_to_target = float(dist)
  182 |                 
  183 |         self.current_step += 1
  184 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  185 |         
  186 |         info = {}
  187 |         if self.reached_plate or ball_pos[2] <= 0.05 or ball_pos[1] < -0.5:
  188 |             terminated = True
  189 |             
  190 |             if self.reached_plate:
  191 |                 dist = self.min_dist_to_target
  192 |                 if dist <= 0.20:
  193 |                     # Strike Zone! Huge reward!
  194 |                     reward += 1000.0 + (0.20 - dist) * 1000.0 + self.release_speed_kmh * 3.0
  195 |                     info['outcome'] = 'STRIKE'
  196 |                 else:
  197 |                     # Missing the zone should be punished severely so it learns control
  198 |                     reward -= dist * 300.0
  199 |                     info['outcome'] = 'BALL'
  200 |             else:
  201 |                 reward -= 100.0 * max(0.1, ball_pos[1] - 0.20)
  202 |                 info['outcome'] = 'WILD PITCH'
  203 |                 
  204 |         if self.current_step >= self.max_steps:
  205 |             truncated = True
  206 |             if not self.is_released:
  207 |                 reward -= 100.0
  208 |                 info['outcome'] = 'NO PITCH'
  209 | 
  210 |         info.update({
  211 |             "is_success": self.reached_plate and getattr(self, 'min_dist_to_target', 999) <= 0.2,
  212 |             "dist": getattr(self, 'min_dist_to_target', 999),
  213 |             "speed": self.release_speed_kmh,
  214 |             "is_released": self.is_released,
  215 |             "reached_plate": self.reached_plate,
  216 |             "min_dist": self.min_dist_to_target,
  217 |             "release_speed_kmh": self.release_speed_kmh,
  218 |             "pitch_type": self.target_pitch_type
  219 |         })
  220 |         
  221 |         return self._get_obs(), float(reward), terminated, truncated, info
  222 | 
  223 |     def _set_arm_pose(self, angles):
  224 |         for valid_i, adr in zip(self.valid_indices, self.qpos_adrs):
  225 |             self.data.qpos[adr] = angles[valid_i]
  226 |             
  227 | 
  228 |     def _update_arm_kinematics(self, progress, kfs):
  229 |         num_kfs = len(kfs)
  230 |         scaled = np.clip(progress, 0.0, 1.0) * (num_kfs - 1)
  231 |         idx1 = int(np.floor(scaled))
  232 |         idx2 = min(idx1 + 1, num_kfs - 1)
  233 |         t = scaled - idx1
  234 |         angles = (1-t)*kfs[idx1] + t*kfs[idx2]
  235 |         for valid_i, adr in zip(self.valid_indices, self.qpos_adrs):
  236 |             self.data.qpos[adr] = angles[valid_i]
  237 | 
  238 |     def _get_obs(self):
  239 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  240 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
  241 |         hand_pos = self.data.site_xpos[self.hand_site_id].copy()
  242 |         
  243 |         target = np.array([self.target_x, self.target_z], dtype=np.float32)
  244 |         rel_state = np.array([1.0 if self.is_released else 0.0, self.throw_progress], dtype=np.float32)
  245 |         
  246 |         # One-hot encoding of pitch type
  247 |         pitch_type_onehot = np.zeros(3, dtype=np.float32)
  248 |         pitch_type_onehot[self.target_pitch_type] = 1.0
  249 |         
  250 |         return np.concatenate([target, rel_state[:1], ball_pos, ball_vel, hand_pos, rel_state[1:], pitch_type_onehot]).astype(np.float32)
  251 | 
  252 |     def close(self):
  253 |         if self.viewer:
  254 |             self.viewer.close()
````
