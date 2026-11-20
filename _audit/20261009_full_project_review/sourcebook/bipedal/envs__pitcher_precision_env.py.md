# bipedal/envs/pitcher_precision_env.py

원본: [envs/pitcher_precision_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/envs/pitcher_precision_env.py)

SHA256: `2fe66de47732cab340600f55e6360057c63e4bc721263bd7217920d63cf02085`

전체 421행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `PitcherPrecisionEnv` | ClassDef | 24 | 421 |
| `__init__` | FunctionDef | 47 | 147 |
| `_set_pitcher_stance` | FunctionDef | 149 | 161 |
| `reset` | FunctionDef | 163 | 226 |
| `_get_obs` | FunctionDef | 228 | 250 |
| `step` | FunctionDef | 252 | 411 |
| `render` | FunctionDef | 413 | 417 |
| `close` | FunctionDef | 419 | 421 |

## 전체 원문

````text
    1 | """
    2 | PitcherPrecisionEnv: Goal-Conditioned Humanoid Pitcher Precision Environment for Unitree H1.
    3 | Features:
    4 | - Full 19-DoF H1 pitching kinematics with athletic mound stance.
    5 | - True PD motor torque control with rated actuator saturation clipping.
    6 | - Goal-conditioned 9-grid strike zone target tracking (High/Mid/Low x Inside/Center/Outside).
    7 | - 3 distinct pitch repertoires: 4-seam Fastball, Slider, Curveball with aerodynamic drag and Magnus force.
    8 | - Continuous action space modulating release timing, 3D aiming angles, and pitch speed.
    9 | """
   10 | 
   11 | import os
   12 | import sys
   13 | import numpy as np
   14 | import gymnasium as gym
   15 | from gymnasium import spaces
   16 | import mujoco
   17 | 
   18 | current_dir = os.path.dirname(os.path.abspath(__file__))
   19 | parent_dir = os.path.dirname(current_dir)
   20 | if parent_dir not in sys.path:
   21 |     sys.path.insert(0, parent_dir)
   22 | 
   23 | 
   24 | class PitcherPrecisionEnv(gym.Env):
   25 |     """
   26 |     Goal-Conditioned Humanoid Pitcher Precision Environment.
   27 | 
   28 |     Observation Space (23 dims):
   29 |       [0:2]   Target strike zone coordinate over home plate [target_x, target_z] (m)
   30 |       [2:5]   Target pitch type one-hot: [Fastball, Slider, Curveball]
   31 |       [5:8]   Current ball position [x, y, z] (m)
   32 |       [8:11]  Current ball velocity [vx, vy, vz] (m/s)
   33 |       [11:14] Pitcher hand site position [x, y, z] (m)
   34 |       [14:17] Pitcher hand site velocity [vx, vy, vz] (m/s)
   35 |       [17:22] Pitching arm joint positions [torso, rsp, rsr, rsy, relb] (rad)
   36 |       [22]    Throw progress (0.0 to 1.0)
   37 | 
   38 |     Action Space (4 dims, continuous in [-1, 1]):
   39 |       a[0]: Release timing offset: dt in [-0.030, +0.030] s
   40 |       a[1]: Horizontal aim course: dx in [-0.15, +0.15] m
   41 |       a[2]: Vertical elevation aim: dz in [-0.12, +0.12] m
   42 |       a[3]: Arm acceleration / velocity scaling: dv in [-0.15, +0.15]
   43 |     """
   44 | 
   45 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}
   46 | 
   47 |     def __init__(
   48 |         self,
   49 |         xml_path=None,
   50 |         render_mode=None,
   51 |         frame_skip=5,  # 5 * 0.002s = 0.010s per step (100 Hz control)
   52 |         mound_y=10.0,
   53 |     ):
   54 |         super().__init__()
   55 | 
   56 |         if xml_path is None:
   57 |             xml_path = os.path.join(parent_dir, "models", "h1_pitcher.xml")
   58 | 
   59 |         self.xml_path = xml_path
   60 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   61 |         self.data = mujoco.MjData(self.model)
   62 | 
   63 |         self.render_mode = render_mode
   64 |         self.frame_skip = frame_skip
   65 |         self.dt = self.model.opt.timestep * self.frame_skip
   66 |         self.mound_y = mound_y
   67 | 
   68 |         # Geoms & Sites
   69 |         self.hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "pitcher_hand_site")
   70 |         self.target_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "pitch_target_point")
   71 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   72 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   73 |         self.weld_eq_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_EQUALITY, "ball_weld")
   74 | 
   75 |         # Freejoint for ball
   76 |         ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   77 |         self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
   78 |         self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]
   79 | 
   80 |         # Pitching joints and actuators: [torso, rsp, rsr, rsy, relb]
   81 |         self.pitch_actuator_names = [
   82 |             "torso",
   83 |             "right_shoulder_pitch",
   84 |             "right_shoulder_roll",
   85 |             "right_shoulder_yaw",
   86 |             "right_elbow",
   87 |         ]
   88 |         self.act_ids = [
   89 |             mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
   90 |             for name in self.pitch_actuator_names
   91 |         ]
   92 |         self.jnt_ids = [self.model.actuator_trnid[a, 0] for a in self.act_ids]
   93 |         self.qpos_adrs = [self.model.jnt_qposadr[j] for j in self.jnt_ids]
   94 |         self.qvel_adrs = [self.model.jnt_dofadr[j] for j in self.jnt_ids]
   95 | 
   96 |         # Leg joints for stance
   97 |         self.leg_joint_names = [
   98 |             "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
   99 |             "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
  100 |         ]
  101 |         self.leg_qpos_adrs = [
  102 |             self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)]
  103 |             for n in self.leg_joint_names
  104 |         ]
  105 | 
  106 |         # Canonical Pitching Keyframes
  107 |         # [torso, rsp, rsr, rsy, relb]
  108 |         self.base_keyframes = np.array([
  109 |             [ 0.00,  0.00, -0.40,  0.00,  1.50],  # 0: Set (glove at chest)
  110 |             [ 0.80,  1.20, -0.60,  0.80,  1.60],  # 1: Cocking (back & up)
  111 |             [ 0.20, -0.20, -0.40,  0.30,  1.00],  # 2: Acceleration
  112 |             [-0.50, -1.40, -0.20, -0.20,  0.20],  # 3: Release
  113 |             [-0.90, -1.80, -0.60, -0.50,  0.70],  # 4: Follow-through
  114 |         ], dtype=np.float32)
  115 | 
  116 |         # PD Controller gains for Pitching Arm
  117 |         self.Kp = np.array([450.0, 350.0, 250.0, 150.0, 150.0], dtype=np.float32)
  118 |         self.Kd = np.array([35.0,  25.0,  20.0,  12.0,  12.0], dtype=np.float32)
  119 | 
  120 |         # Aerodynamic Constants
  121 |         self.rho = 1.205  # kg/m^3 (air density)
  122 |         self.r_ball = 0.037  # m (radius)
  123 |         self.m_ball = 0.145  # kg (mass)
  124 |         self.A_ball = np.pi * (self.r_ball ** 2)
  125 |         self.Cd = 0.32  # drag coefficient
  126 |         self.Cl = 0.24  # lift coefficient
  127 | 
  128 |         # Spaces
  129 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
  130 |         self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(23,), dtype=np.float32)
  131 | 
  132 |         # State Variables
  133 |         self.current_step = 0
  134 |         self.max_steps = 100
  135 |         self.is_released = False
  136 |         self.release_step = -1
  137 |         self.release_speed_ms = 0.0
  138 |         self.release_speed_kmh = 0.0
  139 |         self.reached_plate = False
  140 |         self.plate_crossing_pos = None
  141 |         self.plate_crossing_vel = None
  142 |         self.min_dist_to_target = 999.0
  143 |         self.prev_action = np.zeros(4, dtype=np.float32)
  144 | 
  145 |         self.renderer = None
  146 |         if self.render_mode in ["rgb_array", "human"]:
  147 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  148 | 
  149 |     def _set_pitcher_stance(self):
  150 |         """Sets a firm athletic pitcher mound stance."""
  151 |         for n, adr in zip(self.leg_joint_names, self.leg_qpos_adrs):
  152 |             if "left_hip_pitch" in n:
  153 |                 self.data.qpos[adr] = -0.30
  154 |             elif "left_knee" in n:
  155 |                 self.data.qpos[adr] = 0.50
  156 |             elif "right_hip_pitch" in n:
  157 |                 self.data.qpos[adr] = 0.10
  158 |             elif "right_knee" in n:
  159 |                 self.data.qpos[adr] = 0.20
  160 |             elif "yaw" in n or "roll" in n or "ankle" in n:
  161 |                 self.data.qpos[adr] = 0.0
  162 | 
  163 |     def reset(self, seed=None, options=None):
  164 |         super().reset(seed=seed)
  165 |         mujoco.mj_resetData(self.model, self.data)
  166 | 
  167 |         self.current_step = 0
  168 |         self.is_released = False
  169 |         self.release_step = -1
  170 |         self.release_speed_ms = 0.0
  171 |         self.release_speed_kmh = 0.0
  172 |         self.reached_plate = False
  173 |         self.plate_crossing_pos = None
  174 |         self.plate_crossing_vel = None
  175 |         self.min_dist_to_target = 999.0
  176 |         self.prev_action = np.zeros(4, dtype=np.float32)
  177 | 
  178 |         # 1. Sample 9-Grid Strike Zone Target
  179 |         # Grid X: [-0.15, +0.15], Grid Z: [0.68, 0.92]
  180 |         self.target_x = float(self.np_random.uniform(-0.15, 0.15))
  181 |         self.target_z = float(self.np_random.uniform(0.68, 0.92))
  182 | 
  183 |         # Update visual target marker
  184 |         if self.target_site_id >= 0:
  185 |             self.model.site_pos[self.target_site_id] = [self.target_x, 0.0, self.target_z]
  186 | 
  187 |         # 2. Sample Pitch Type
  188 |         # 0: Fastball, 1: Slider, 2: Curveball
  189 |         self.pitch_type = int(self.np_random.integers(0, 3))
  190 |         self.pitch_one_hot = np.zeros(3, dtype=np.float32)
  191 |         self.pitch_one_hot[self.pitch_type] = 1.0
  192 | 
  193 |         # Base nominal velocity and spin according to pitch type
  194 |         if self.pitch_type == 0:
  195 |             # 4-Seam Fastball: 75 ~ 88 km/h (21 ~ 24.5 m/s), backspin
  196 |             self.nominal_speed = float(self.np_random.uniform(21.0, 24.0))
  197 |             self.nominal_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
  198 |         elif self.pitch_type == 1:
  199 |             # Slider: 68 ~ 78 km/h (19 ~ 21.6 m/s), lateral break
  200 |             self.nominal_speed = float(self.np_random.uniform(19.0, 21.5))
  201 |             self.nominal_spin = np.array([-30.0, 0.0, 150.0], dtype=np.float32)
  202 |         else:
  203 |             # Curveball: 60 ~ 70 km/h (16.7 ~ 19.5 m/s), 12-to-6 drop
  204 |             self.nominal_speed = float(self.np_random.uniform(17.0, 19.5))
  205 |             self.nominal_spin = np.array([170.0, 0.0, -20.0], dtype=np.float32)
  206 | 
  207 |         # Setup stance and arm initial keyframe
  208 |         self._set_pitcher_stance()
  209 |         for i, adr in enumerate(self.qpos_adrs):
  210 |             self.data.qpos[adr] = self.base_keyframes[0, i]
  211 | 
  212 |         # Activate weld constraint to pitcher hand
  213 |         if self.weld_eq_id >= 0:
  214 |             self.data.eq_active[self.weld_eq_id] = True
  215 | 
  216 |         mujoco.mj_forward(self.model, self.data)
  217 | 
  218 |         # Sync ball initial position to hand site
  219 |         hand_pos = self.data.site_xpos[self.hand_site_id]
  220 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
  221 |         self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  222 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+6] = 0.0
  223 | 
  224 |         mujoco.mj_forward(self.model, self.data)
  225 | 
  226 |         return self._get_obs(), {}
  227 | 
  228 |     def _get_obs(self):
  229 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  230 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  231 |         hand_pos = self.data.site_xpos[self.hand_site_id]
  232 | 
  233 |         hand_v = np.zeros(6, dtype=np.float64)
  234 |         mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_SITE, self.hand_site_id, hand_v, 0)
  235 |         hand_vel = hand_v[3:6]
  236 | 
  237 |         arm_qpos = np.array([self.data.qpos[adr] for adr in self.qpos_adrs], dtype=np.float32)
  238 |         progress = float(self.current_step / self.max_steps)
  239 | 
  240 |         obs = np.concatenate([
  241 |             np.array([self.target_x, self.target_z], dtype=np.float32),  # 2
  242 |             self.pitch_one_hot,                                          # 3
  243 |             ball_pos,                                                    # 3
  244 |             ball_vel,                                                    # 3
  245 |             hand_pos,                                                    # 3
  246 |             hand_vel,                                                    # 3
  247 |             arm_qpos,                                                    # 5
  248 |             np.array([progress], dtype=np.float32),                       # 1
  249 |         ])
  250 |         return obs.astype(np.float32)
  251 | 
  252 |     def step(self, action):
  253 |         action = np.clip(action, -1.0, 1.0).astype(np.float32)
  254 | 
  255 |         # Action modulations:
  256 |         # a[0]: release timing offset [-0.030, +0.030] s
  257 |         # a[1]: horizontal aim course [-0.15, +0.15] m
  258 |         # a[2]: vertical elevation aim [-0.12, +0.12] m
  259 |         # a[3]: speed scale [-0.15, +0.15]
  260 |         dt_rel = float(action[0]) * 0.030
  261 |         dx_aim = float(action[1]) * 0.15
  262 |         dz_aim = float(action[2]) * 0.12
  263 |         dv_scale = float(action[3]) * 0.15
  264 | 
  265 |         nominal_release_step = 22
  266 |         actual_release_step = int(np.clip(nominal_release_step + int(dt_rel / self.dt), 18, 26))
  267 | 
  268 |         # Modulate Keyframes for aiming
  269 |         kfs = self.base_keyframes.copy()
  270 |         kfs[2, 0] += dx_aim * 0.5
  271 |         kfs[3, 0] += dx_aim * 1.0
  272 |         kfs[3, 1] += dz_aim * 1.2
  273 |         kfs[3, 2] += dx_aim * 0.3
  274 | 
  275 |         substep_dt = self.model.opt.timestep  # 0.002s
  276 | 
  277 |         for _ in range(self.frame_skip):
  278 |             # 1. Interpolate keyframes for arm motion
  279 |             t_norm = self.current_step / actual_release_step
  280 |             if t_norm < 0.35:
  281 |                 w = t_norm / 0.35
  282 |                 q_target = (1 - w) * kfs[0] + w * kfs[1]
  283 |             elif t_norm < 0.70:
  284 |                 w = (t_norm - 0.35) / 0.35
  285 |                 q_target = (1 - w) * kfs[1] + w * kfs[2]
  286 |             elif t_norm <= 1.0:
  287 |                 w = (t_norm - 0.70) / 0.30
  288 |                 q_target = (1 - w) * kfs[2] + w * kfs[3]
  289 |             else:
  290 |                 w = min(1.0, (t_norm - 1.0) / 0.40)
  291 |                 q_target = (1 - w) * kfs[3] + w * kfs[4]
  292 | 
  293 |             # 2. Low-Level PD Motor Torque with Saturation
  294 |             for i in range(5):
  295 |                 q = self.data.qpos[self.qpos_adrs[i]]
  296 |                 dq = self.data.qvel[self.qvel_adrs[i]]
  297 |                 tau = self.Kp[i] * (q_target[i] - q) - self.Kd[i] * dq
  298 |                 ctrlrange = self.model.actuator_ctrlrange[self.act_ids[i]]
  299 |                 self.data.ctrl[self.act_ids[i]] = np.clip(tau, ctrlrange[0], ctrlrange[1])
  300 | 
  301 |             # 3. Release Ball at Release Step
  302 |             if not self.is_released and self.current_step >= actual_release_step:
  303 |                 self.is_released = True
  304 |                 self.release_step = self.current_step
  305 |                 if self.weld_eq_id >= 0:
  306 |                     self.data.eq_active[self.weld_eq_id] = False
  307 | 
  308 |                 # Desired target coordinates at home plate (y = 0.0m)
  309 |                 tx = self.target_x + dx_aim
  310 |                 tz = self.target_z + dz_aim
  311 |                 speed = self.nominal_speed * (1.0 + dv_scale)
  312 | 
  313 |                 curr_hand_pos = self.data.site_xpos[self.hand_site_id]
  314 |                 x0, y0, z0 = curr_hand_pos[0], curr_hand_pos[1], curr_hand_pos[2]
  315 |                 dy = y0 - 0.0
  316 |                 t_f = dy / speed
  317 |                 vy = -speed
  318 |                 vx = (tx - x0) / t_f
  319 | 
  320 |                 # Gravity drop compensation
  321 |                 drop = 0.5 * 9.81 * (t_f ** 2)
  322 |                 vz = (tz + drop - z0) / t_f
  323 | 
  324 |                 # Calibrated baseline and aerodynamic spin compensation
  325 |                 vx -= 0.14
  326 |                 if self.pitch_type == 0:  # Fastball backspin lifts the ball
  327 |                     vz += 0.13
  328 |                 elif self.pitch_type == 1:  # Slider breaks right (+X)
  329 |                     vx -= 0.12
  330 |                 elif self.pitch_type == 2:  # Curveball drops down (-Z)
  331 |                     vz += 0.05
  332 | 
  333 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
  334 |                 self.release_speed_ms = float(np.linalg.norm([vx, vy, vz]))
  335 |                 self.release_speed_kmh = float(self.release_speed_ms * 3.6)
  336 | 
  337 |             # 4. Aerodynamic Drag and Magnus Forces in Flight
  338 |             if self.is_released:
  339 |                 v = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  340 |                 v_norm = np.linalg.norm(v)
  341 |                 if v_norm > 1.0:
  342 |                     f_drag = -0.5 * self.rho * self.Cd * self.A_ball * v_norm * v
  343 |                     f_magnus = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.nominal_spin, v)
  344 |                     a_aero = (f_drag + f_magnus) / self.m_ball
  345 |                     self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += a_aero * substep_dt
  346 | 
  347 |             mujoco.mj_step(self.model, self.data)
  348 | 
  349 |             # Check Home Plate crossing
  350 |             ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  351 |             if ball_pos[1] <= 0.0 and not self.reached_plate and self.is_released:
  352 |                 self.reached_plate = True
  353 |                 self.plate_crossing_pos = ball_pos.copy()
  354 |                 self.plate_crossing_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
  355 |                 dist = np.sqrt((ball_pos[0] - self.target_x)**2 + (ball_pos[2] - self.target_z)**2)
  356 |                 self.min_dist_to_target = float(dist)
  357 | 
  358 |         self.current_step += 1
  359 |         obs = self._get_obs()
  360 | 
  361 |         terminated = False
  362 |         truncated = False
  363 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  364 | 
  365 |         if self.reached_plate:
  366 |             terminated = True
  367 |         elif ball_pos[2] <= 0.04 and self.is_released:  # Dirt pitch
  368 |             terminated = True
  369 |         elif self.current_step >= self.max_steps:
  370 |             truncated = True
  371 | 
  372 |         # Reward Calculation
  373 |         reward = 0.0
  374 |         info = {
  375 |             "target_x": self.target_x,
  376 |             "target_z": self.target_z,
  377 |             "pitch_type": self.pitch_type,
  378 |             "is_released": self.is_released,
  379 |             "release_speed_kmh": self.release_speed_kmh,
  380 |             "reached_plate": self.reached_plate,
  381 |             "min_dist_to_target": self.min_dist_to_target,
  382 |             "is_strike": False,
  383 |         }
  384 | 
  385 |         if terminated and self.reached_plate:
  386 |             dist = self.min_dist_to_target
  387 |             # Dense Gaussian target reward (sigma = 7 cm)
  388 |             r_target = 18.0 * np.exp(- (dist ** 2) / (2.0 * (0.07 ** 2)))
  389 |             # Linear guide gradient
  390 |             r_linear = np.clip(1.0 - dist / 0.25, -1.0, 1.0) * 10.0
  391 | 
  392 |             # Strike zone check: official MLB width 17 in (+/- 0.216m), height [0.65, 0.95]
  393 |             is_strike = (abs(self.plate_crossing_pos[0]) <= 0.216) and (0.65 <= self.plate_crossing_pos[2] <= 0.95)
  394 |             r_strike = 15.0 if is_strike else -6.0
  395 |             info["is_strike"] = is_strike
  396 | 
  397 |             # Velocity bonus
  398 |             r_vel = 4.0 * np.clip(self.release_speed_kmh / 80.0, 0.5, 1.2)
  399 | 
  400 |             reward += r_target + r_linear + r_strike + r_vel
  401 |             info["dist_error_cm"] = float(dist * 100.0)
  402 |         elif terminated and not self.reached_plate:
  403 |             reward -= 20.0
  404 |             info["dist_error_cm"] = 99.0
  405 | 
  406 |         # Action regularizations
  407 |         reward -= 0.01 * float(np.sum(action ** 2))
  408 |         reward -= 0.02 * float(np.sum((action - self.prev_action) ** 2))
  409 |         self.prev_action = action.copy()
  410 | 
  411 |         return obs, reward, terminated, truncated, info
  412 | 
  413 |     def render(self):
  414 |         if self.render_mode == "rgb_array" and self.renderer is not None:
  415 |             self.renderer.update_scene(self.data, camera="catcher_cam")
  416 |             return self.renderer.render()
  417 |         return None
  418 | 
  419 |     def close(self):
  420 |         if self.renderer is not None:
  421 |             self.renderer.close()
````
