# bipedal/envs/hardened_batting_env.py

원본: [envs/hardened_batting_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/envs/hardened_batting_env.py)

SHA256: `68ad332e2cc186dd9616591ffedf2418d7f07b0e7a3b97f2f732331fc8aa3bdb`

전체 489행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `HardenedBattingEnv` | ClassDef | 28 | 489 |
| `__init__` | FunctionDef | 36 | 157 |
| `_set_athletic_leg_crouch` | FunctionDef | 159 | 168 |
| `reset` | FunctionDef | 170 | 246 |
| `_get_obs` | FunctionDef | 248 | 286 |
| `step` | FunctionDef | 288 | 479 |
| `render` | FunctionDef | 481 | 485 |
| `close` | FunctionDef | 487 | 489 |

## 전체 원문

````text
    1 | """
    2 | HardenedBattingEnv: Phase 2 Sim-to-Real Physically Hardened Batting Environment.
    3 | Features:
    4 | - Communication Latency Buffer (20ms EtherCAT delay queue).
    5 | - Strict rated motor torque saturation clipping on all H1 joints (Arm: 18-40 N*m, Torso: 200 N*m).
    6 | - Domain Randomization:
    7 |   * Bat mass variation (+/- 10%: 0.81 ~ 0.99 kg)
    8 |   * Ball restitution variation (COR damping jitter)
    9 |   * Vision observation sensor noise (Gaussian jitter on ball tracking)
   10 |   * Pitch velocity and course perturbations
   11 | - Forward fair-ball contact tracking and goal-conditioned directional control.
   12 | """
   13 | 
   14 | import os
   15 | import sys
   16 | import collections
   17 | import numpy as np
   18 | import gymnasium as gym
   19 | from gymnasium import spaces
   20 | import mujoco
   21 | 
   22 | current_dir = os.path.dirname(os.path.abspath(__file__))
   23 | parent_dir = os.path.dirname(current_dir)
   24 | if parent_dir not in sys.path:
   25 |     sys.path.insert(0, parent_dir)
   26 | 
   27 | 
   28 | class HardenedBattingEnv(gym.Env):
   29 |     """
   30 |     Phase 2 Sim-to-Real Physically Hardened Batting Environment.
   31 |     Incorporates latency buffers, strict hardware torque limits, and domain randomization.
   32 |     """
   33 | 
   34 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}
   35 | 
   36 |     def __init__(
   37 |         self,
   38 |         xml_path=None,
   39 |         render_mode=None,
   40 |         frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz control)
   41 |         pitch_speed_range=(14.0, 19.0),
   42 |         pitch_dist=7.5,
   43 |         latency_steps=1,  # 1 step delay = 20ms
   44 |         enable_domain_randomization=True,
   45 |     ):
   46 |         super().__init__()
   47 | 
   48 |         if xml_path is None:
   49 |             xml_path = os.path.join(parent_dir, "models", "h1_baseball.xml")
   50 | 
   51 |         self.xml_path = xml_path
   52 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   53 |         
   54 |         pelvis_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
   55 |         if pelvis_body_id >= 0:
   56 |             self.model.body_pos[pelvis_body_id, 0] = -0.90
   57 |             self.model.body_pos[pelvis_body_id, 1] = 0.00
   58 |             self.model.body_pos[pelvis_body_id, 2] = 0.95
   59 | 
   60 |         self.data = mujoco.MjData(self.model)
   61 | 
   62 |         self.render_mode = render_mode
   63 |         self.frame_skip = frame_skip
   64 |         self.dt = self.model.opt.timestep * self.frame_skip  # 0.02 s
   65 |         self.pitch_speed_range = pitch_speed_range
   66 |         self.pitch_dist = pitch_dist
   67 |         self.latency_steps = latency_steps
   68 |         self.enable_domain_randomization = enable_domain_randomization
   69 | 
   70 |         # Identify Geoms & Sites
   71 |         self.bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "bat")
   72 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   73 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   74 |         self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")
   75 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   76 | 
   77 |         # Freejoint for ball
   78 |         ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   79 |         self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
   80 |         self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]
   81 | 
   82 |         # Upper body swing actuators and joints
   83 |         self.swing_actuator_names = [
   84 |             "torso",
   85 |             "right_shoulder_pitch",
   86 |             "right_shoulder_roll",
   87 |             "right_shoulder_yaw",
   88 |             "right_elbow",
   89 |         ]
   90 |         self.act_ids = [
   91 |             mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
   92 |             for name in self.swing_actuator_names
   93 |         ]
   94 |         self.jnt_ids = [self.model.actuator_trnid[a, 0] for a in self.act_ids]
   95 |         self.qpos_adrs = [self.model.jnt_qposadr[j] for j in self.jnt_ids]
   96 |         self.qvel_adrs = [self.model.jnt_dofadr[j] for j in self.jnt_ids]
   97 | 
   98 |         # Athletic batting crouch leg joint addresses
   99 |         self.leg_joint_names = [
  100 |             "left_hip_pitch", "left_knee", "left_hip_roll",
  101 |             "right_hip_pitch", "right_knee", "right_hip_roll"
  102 |         ]
  103 |         self.leg_qpos_adrs = [
  104 |             self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, lj)]
  105 |             for lj in self.leg_joint_names
  106 |         ]
  107 | 
  108 |         # Canonical Kinematic Chain Swing Keyframes
  109 |         self.base_keyframes = np.array([
  110 |             [-0.40, -1.00,  0.00,  0.40,  1.50],  # 0: Stance
  111 |             [-0.60, -1.15,  0.00,  0.60,  1.70],  # 1: Load / Takeback
  112 |             [-0.10, -0.70, -0.05,  0.20,  1.20],  # 2: Stride / Uncoil start
  113 |             [ 0.50, -0.30, -0.10, -0.10,  0.70],  # 3: Slot / Acceleration
  114 |             [ 1.15,  0.20, -0.08, -0.40,  0.35],  # 4: Contact
  115 |             [ 1.70,  0.80,  0.00, -0.70,  1.20]   # 5: Follow-through
  116 |         ], dtype=np.float32)
  117 | 
  118 |         # PD Gains for Upper Body Actuators
  119 |         self.Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
  120 |         self.Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)
  121 | 
  122 |         # Action Space: 5-dim continuous
  123 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(5,), dtype=np.float32)
  124 | 
  125 |         # Observation Space: 31-dim continuous
  126 |         obs_dim = 7 + 3 + 5 + 5 + 3 + 3 + 5
  127 |         self.observation_space = spaces.Box(
  128 |             low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
  129 |         )
  130 | 
  131 |         # Base nominal bat mass
  132 |         self.nominal_bat_mass = float(self.model.body_mass[self.bat_body_id]) if self.bat_body_id >= 0 else 0.90
  133 | 
  134 |         # State Variables
  135 |         self.current_step = 0
  136 |         self.max_steps = 35
  137 |         self.action_queue = collections.deque(maxlen=self.latency_steps + 1)
  138 |         self.prev_action = np.zeros(5, dtype=np.float32)
  139 |         self.filtered_action = np.zeros(5, dtype=np.float32)
  140 |         self.swing_triggered = False
  141 |         self.locked_t_trigger = 0.0
  142 |         self.locked_swing_duration = 0.17
  143 |         self.has_contacted = False
  144 |         self.contact_reward_given = False
  145 |         self.contact_step = -1
  146 |         self.contact_ball_pos = None
  147 |         self.contact_sweet_pos = None
  148 |         self.exit_ball_vel = None
  149 |         self.min_ball_sweet_dist = 999.0
  150 |         self.exit_velocity = 0.0
  151 |         self.exit_azimuth_deg = 0.0
  152 |         self.exit_launch_deg = 0.0
  153 |         self.is_fair_hit = False
  154 | 
  155 |         self.renderer = None
  156 |         if self.render_mode in ["rgb_array", "human"]:
  157 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  158 | 
  159 |     def _set_athletic_leg_crouch(self):
  160 |         for lj, qadr in zip(self.leg_joint_names, self.leg_qpos_adrs):
  161 |             if "pitch" in lj:
  162 |                 self.data.qpos[qadr] = -0.35
  163 |             elif "knee" in lj:
  164 |                 self.data.qpos[qadr] = 0.70
  165 |             elif "left_hip_roll" in lj:
  166 |                 self.data.qpos[qadr] = 0.18
  167 |             elif "right_hip_roll" in lj:
  168 |                 self.data.qpos[qadr] = -0.18
  169 | 
  170 |     def reset(self, seed=None, options=None):
  171 |         super().reset(seed=seed)
  172 |         mujoco.mj_resetData(self.model, self.data)
  173 | 
  174 |         self.current_step = 0
  175 |         self.action_queue.clear()
  176 |         for _ in range(self.latency_steps + 1):
  177 |             self.action_queue.append(np.zeros(5, dtype=np.float32))
  178 | 
  179 |         self.prev_action = np.zeros(5, dtype=np.float32)
  180 |         self.filtered_action = np.zeros(5, dtype=np.float32)
  181 |         self.swing_triggered = False
  182 |         self.locked_t_trigger = 0.0
  183 |         self.locked_swing_duration = 0.17
  184 |         self.has_contacted = False
  185 |         self.contact_reward_given = False
  186 |         self.contact_step = -1
  187 |         self.contact_ball_pos = None
  188 |         self.contact_sweet_pos = None
  189 |         self.exit_ball_vel = None
  190 |         self.min_ball_sweet_dist = 999.0
  191 |         self.exit_velocity = 0.0
  192 |         self.exit_azimuth_deg = 0.0
  193 |         self.exit_launch_deg = 0.0
  194 |         self.is_fair_hit = False
  195 | 
  196 |         # Domain Randomization
  197 |         if self.enable_domain_randomization:
  198 |             # 1. Bat mass randomization (+/- 10%)
  199 |             mass_scale = float(self.np_random.uniform(0.90, 1.10))
  200 |             if self.bat_body_id >= 0:
  201 |                 self.model.body_mass[self.bat_body_id] = self.nominal_bat_mass * mass_scale
  202 | 
  203 |             # 2. Contact restitution jitter
  204 |             if hasattr(self.model, 'pair_solimp') and self.model.npair > 0:
  205 |                 self.model.pair_solimp[0, 0] = float(self.np_random.uniform(0.93, 0.97))
  206 | 
  207 |         self._set_athletic_leg_crouch()
  208 | 
  209 |         for i, qadr in enumerate(self.qpos_adrs):
  210 |             self.data.qpos[qadr] = self.base_keyframes[0, i]
  211 | 
  212 |         # Target Goal Vector
  213 |         target_azimuth_deg = self.np_random.uniform(-35.0, 35.0)
  214 |         self.target_azimuth_rad = float(np.radians(target_azimuth_deg))
  215 | 
  216 |         target_launch_deg = self.np_random.uniform(12.0, 32.0)
  217 |         self.target_launch_rad = float(np.radians(target_launch_deg))
  218 | 
  219 |         self.target_exit_vel = float(self.np_random.uniform(10.0, 18.0))
  220 | 
  221 |         # Sample Pitched Ball
  222 |         pitch_speed = self.np_random.uniform(*self.pitch_speed_range)
  223 |         vy = -pitch_speed
  224 |         
  225 |         plate_y_contact = 0.22
  226 |         t_flight = (self.pitch_dist - plate_y_contact) / abs(vy)
  227 |         self.nominal_t_flight = t_flight
  228 | 
  229 |         target_x = self.np_random.uniform(0.10, 0.16)
  230 |         target_z = self.np_random.uniform(0.74, 0.78)
  231 | 
  232 |         z0 = 0.85
  233 |         drop = 0.5 * 9.81 * (t_flight ** 2)
  234 |         vz = (target_z + drop - z0) / t_flight
  235 | 
  236 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [target_x, self.pitch_dist, z0]
  237 |         self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  238 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, vy, vz]
  239 |         self.data.qvel[self.ball_qvel_adr+3:self.ball_qvel_adr+6] = [0.0, 0.0, 0.0]
  240 | 
  241 |         mujoco.mj_forward(self.model, self.data)
  242 | 
  243 |         self.nominal_t_trigger = t_flight - 0.126
  244 |         self.nominal_swing_duration = 0.17
  245 | 
  246 |         return self._get_obs(), {}
  247 | 
  248 |     def _get_obs(self):
  249 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  250 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
  251 | 
  252 |         # Add Gaussian vision sensor observation noise in domain randomization
  253 |         if self.enable_domain_randomization:
  254 |             ball_pos += self.np_random.normal(0.0, 0.003, size=3)
  255 |             ball_vel += self.np_random.normal(0.0, 0.05, size=3)
  256 |         
  257 |         y_pos = ball_pos[1]
  258 |         vy = ball_vel[1]
  259 |         t_remain = max(0.0, (y_pos - 0.20) / abs(vy)) if abs(vy) > 1.0 else 0.0
  260 | 
  261 |         goals = np.array([
  262 |             self.target_azimuth_rad,
  263 |             self.target_launch_rad,
  264 |             self.target_exit_vel,
  265 |         ], dtype=np.float32)
  266 | 
  267 |         swing_qpos = np.array([self.data.qpos[adr] for adr in self.qpos_adrs], dtype=np.float32)
  268 |         swing_qvel = np.array([self.data.qvel[adr] for adr in self.qvel_adrs], dtype=np.float32)
  269 | 
  270 |         sweet_pos = self.data.site_xpos[self.sweet_spot_id]
  271 |         sweet_v = np.zeros(6, dtype=np.float64)
  272 |         mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_SITE, self.sweet_spot_id, sweet_v, 0)
  273 |         sweet_vel = sweet_v[3:6]
  274 | 
  275 |         obs = np.concatenate([
  276 |             ball_pos,                                    # 3
  277 |             ball_vel,                                    # 3
  278 |             np.array([t_remain], dtype=np.float32),      # 1
  279 |             goals,                                       # 3
  280 |             swing_qpos,                                  # 5
  281 |             swing_qvel,                                  # 5
  282 |             sweet_pos,                                   # 3
  283 |             sweet_vel,                                   # 3
  284 |             self.prev_action,                            # 5
  285 |         ])
  286 |         return obs.astype(np.float32)
  287 | 
  288 |     def step(self, action):
  289 |         action = np.clip(action, -1.0, 1.0).astype(np.float32)
  290 | 
  291 |         # 1. Latency Buffer Queue: Push current action, pop delayed action
  292 |         self.action_queue.append(action)
  293 |         delayed_action = self.action_queue.popleft()
  294 | 
  295 |         # EMA action filter for physical smoothness
  296 |         self.filtered_action = 0.6 * self.filtered_action + 0.4 * delayed_action
  297 | 
  298 |         # Decompose action
  299 |         dt_lead_lag = float(self.filtered_action[0]) * 0.030
  300 |         dz_bat = float(self.filtered_action[1]) * 0.08
  301 |         dalpha_plane = float(self.filtered_action[2]) * 0.15
  302 |         dpower_dur = float(self.filtered_action[3]) * 0.02
  303 |         delbow_reach = float(self.filtered_action[4]) * 0.15
  304 | 
  305 |         current_time = self.current_step * self.dt
  306 | 
  307 |         if not self.swing_triggered:
  308 |             candidate_trigger = self.nominal_t_trigger + dt_lead_lag
  309 |             if current_time >= candidate_trigger:
  310 |                 self.swing_triggered = True
  311 |                 self.locked_t_trigger = candidate_trigger
  312 |                 self.locked_swing_duration = max(0.12, self.nominal_swing_duration + dpower_dur)
  313 | 
  314 |         kfs = self.base_keyframes.copy()
  315 |         kfs[3, 1] += dz_bat * 0.6
  316 |         kfs[3, 2] += dalpha_plane * 0.6
  317 |         kfs[3, 4] += delbow_reach * 0.6
  318 | 
  319 |         kfs[4, 1] += dz_bat * 1.0
  320 |         kfs[4, 2] += dalpha_plane * 1.0
  321 |         kfs[4, 4] += delbow_reach * 1.0
  322 | 
  323 |         kfs[5, 1] += dz_bat * 0.5
  324 |         kfs[5, 2] += dalpha_plane * 0.5
  325 | 
  326 |         for _ in range(self.frame_skip):
  327 |             self._set_athletic_leg_crouch()
  328 | 
  329 |             if not self.swing_triggered:
  330 |                 q_target = kfs[0]
  331 |             else:
  332 |                 elapsed_swing = current_time - self.locked_t_trigger
  333 |                 prog = elapsed_swing / self.locked_swing_duration
  334 | 
  335 |                 if prog < 0.20:
  336 |                     w = prog / 0.20
  337 |                     q_target = (1.0 - w) * kfs[0] + w * kfs[1]
  338 |                 elif prog < 0.45:
  339 |                     w = (prog - 0.20) / 0.25
  340 |                     q_target = (1.0 - w) * kfs[1] + w * kfs[2]
  341 |                 elif prog < 0.70:
  342 |                     w = (prog - 0.45) / 0.25
  343 |                     q_target = (1.0 - w) * kfs[2] + w * kfs[3]
  344 |                 elif prog < 0.90:
  345 |                     w = (prog - 0.70) / 0.20
  346 |                     q_target = (1.0 - w) * kfs[3] + w * kfs[4]
  347 |                 else:
  348 |                     w = min(1.0, (prog - 0.90) / 0.30)
  349 |                     q_target = (1.0 - w) * kfs[4] + w * kfs[5]
  350 | 
  351 |             # Low-Level PD Motor Torques with Strict Saturation
  352 |             for i in range(5):
  353 |                 q = self.data.qpos[self.qpos_adrs[i]]
  354 |                 dq = self.data.qvel[self.qvel_adrs[i]]
  355 |                 tau = self.Kp[i] * (q_target[i] - q) - self.Kd[i] * dq
  356 |                 ctrlrange = self.model.actuator_ctrlrange[self.act_ids[i]]
  357 |                 self.data.ctrl[self.act_ids[i]] = np.clip(tau, ctrlrange[0], ctrlrange[1])
  358 | 
  359 |             mujoco.mj_step(self.model, self.data)
  360 | 
  361 |             # Contact detection
  362 |             for c_idx in range(self.data.ncon):
  363 |                 con = self.data.contact[c_idx]
  364 |                 g1, g2 = con.geom1, con.geom2
  365 |                 if (g1 == self.bat_geom_id and g2 == self.ball_geom_id) or \
  366 |                    (g2 == self.bat_geom_id and g1 == self.ball_geom_id):
  367 |                     if not self.has_contacted:
  368 |                         self.has_contacted = True
  369 |                         self.contact_step = self.current_step
  370 |                         self.contact_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  371 |                         self.contact_sweet_pos = self.data.site_xpos[self.sweet_spot_id].copy()
  372 | 
  373 |             ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  374 |             sweet_pos = self.data.site_xpos[self.sweet_spot_id]
  375 |             dist = float(np.linalg.norm(ball_pos - sweet_pos))
  376 |             if dist < self.min_ball_sweet_dist:
  377 |                 self.min_ball_sweet_dist = dist
  378 | 
  379 |         self.current_step += 1
  380 |         obs = self._get_obs()
  381 | 
  382 |         terminated = False
  383 |         truncated = False
  384 | 
  385 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  386 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  387 | 
  388 |         if self.has_contacted and self.current_step >= self.contact_step + 4:
  389 |             self.exit_ball_vel = ball_vel.copy()
  390 |             vx, vy, vz = self.exit_ball_vel
  391 |             speed = float(np.linalg.norm([vx, vy, vz]))
  392 |             self.exit_velocity = speed
  393 | 
  394 |             if vy > 0.10:
  395 |                 self.is_fair_hit = True
  396 |                 self.exit_azimuth_deg = float(np.degrees(np.arctan2(vx, vy)))
  397 |                 v_horiz = np.sqrt(vx**2 + vy**2)
  398 |                 self.exit_launch_deg = float(np.degrees(np.arctan2(vz, v_horiz)))
  399 |             else:
  400 |                 self.is_fair_hit = False
  401 |                 self.exit_azimuth_deg = float(np.degrees(np.arctan2(vx, max(0.1, vy))))
  402 |                 self.exit_launch_deg = -30.0
  403 | 
  404 |             terminated = True
  405 |         elif ball_pos[1] < -0.8:
  406 |             terminated = True
  407 |         elif self.current_step >= self.max_steps:
  408 |             truncated = True
  409 | 
  410 |         reward = 0.0
  411 |         r_approach = float(np.exp(-12.0 * self.min_ball_sweet_dist))
  412 |         reward += r_approach
  413 | 
  414 |         info = {
  415 |             "contact": self.has_contacted,
  416 |             "fair_hit": self.is_fair_hit,
  417 |             "min_dist_cm": float(self.min_ball_sweet_dist * 100.0),
  418 |             "exit_speed_ms": float(self.exit_velocity),
  419 |             "exit_speed_kmh": float(self.exit_velocity * 3.6),
  420 |             "azimuth_deg": float(self.exit_azimuth_deg),
  421 |             "launch_deg": float(self.exit_launch_deg),
  422 |             "target_azimuth_deg": float(np.degrees(self.target_azimuth_rad)),
  423 |             "target_launch_deg": float(np.degrees(self.target_launch_rad)),
  424 |         }
  425 | 
  426 |         if terminated and self.has_contacted and not self.contact_reward_given:
  427 |             self.contact_reward_given = True
  428 |             r_contact = 12.0
  429 | 
  430 |             sweet_offset = float(np.linalg.norm(self.contact_ball_pos - self.contact_sweet_pos))
  431 |             info["sweet_spot_offset_cm"] = float(sweet_offset * 100.0)
  432 |             r_sweet = 8.0 * float(np.exp(-25.0 * sweet_offset))
  433 | 
  434 |             r_fair = 0.0
  435 |             r_azimuth = 0.0
  436 |             r_launch = 0.0
  437 |             r_vel = 0.0
  438 | 
  439 |             if self.is_fair_hit:
  440 |                 r_fair = 10.0
  441 |                 actual_az_rad = np.radians(self.exit_azimuth_deg)
  442 |                 az_err = abs(actual_az_rad - self.target_azimuth_rad)
  443 |                 info["azimuth_error_deg"] = float(np.degrees(az_err))
  444 | 
  445 |                 sigma_az = 0.35
  446 |                 r_az_gauss = np.exp(- (az_err ** 2) / (2.0 * (sigma_az ** 2)))
  447 |                 r_az_lin = max(0.0, 1.0 - az_err / 1.0)
  448 |                 r_azimuth = 8.0 * (0.6 * r_az_gauss + 0.4 * r_az_lin)
  449 | 
  450 |                 target_deg = np.degrees(self.target_azimuth_rad)
  451 |                 actual_deg = self.exit_azimuth_deg
  452 |                 target_sector = "pull" if target_deg < -10 else ("push" if target_deg > 10 else "center")
  453 |                 actual_sector = "pull" if actual_deg < -10 else ("push" if actual_deg > 10 else "center")
  454 |                 if target_sector == actual_sector:
  455 |                     r_azimuth += 5.0
  456 |                     info["sector_matched"] = True
  457 | 
  458 |                 actual_la_rad = np.radians(self.exit_launch_deg)
  459 |                 la_err = abs(actual_la_rad - self.target_launch_rad)
  460 |                 info["launch_error_deg"] = float(np.degrees(la_err))
  461 | 
  462 |                 sigma_la = 0.25
  463 |                 r_la_gauss = np.exp(- (la_err ** 2) / (2.0 * (sigma_la ** 2)))
  464 |                 r_la_lin = max(0.0, 1.0 - la_err / 0.8)
  465 |                 r_launch = 5.0 * (0.6 * r_la_gauss + 0.4 * r_la_lin)
  466 | 
  467 |                 r_vel = 4.0 * float(np.clip(self.exit_velocity / 12.0, 0.0, 1.5))
  468 |             else:
  469 |                 r_fair = -10.0
  470 |                 info["azimuth_error_deg"] = 99.0
  471 |                 info["launch_error_deg"] = 99.0
  472 | 
  473 |             reward += r_contact + r_sweet + r_fair + r_azimuth + r_launch + r_vel
  474 | 
  475 |         reward -= 0.015 * float(np.sum(action ** 2))
  476 |         reward -= 0.030 * float(np.sum((action - self.prev_action) ** 2))
  477 |         self.prev_action = action.copy()
  478 | 
  479 |         return obs, reward, terminated, truncated, info
  480 | 
  481 |     def render(self):
  482 |         if self.render_mode == "rgb_array" and self.renderer is not None:
  483 |             self.renderer.update_scene(self.data, camera="broadcast_cam")
  484 |             return self.renderer.render()
  485 |         return None
  486 | 
  487 |     def close(self):
  488 |         if self.renderer is not None:
  489 |             self.renderer.close()
````
