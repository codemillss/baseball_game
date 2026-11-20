# bipedal/envs/directional_batting_env.py

원본: [envs/directional_batting_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/envs/directional_batting_env.py)

SHA256: `520f0ad77c9b94655eeb59072d0b13c4bf49bec5ce98e3f0484520e3c672619d`

전체 528행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `DirectionalBattingEnv` | ClassDef | 18 | 528 |
| `__init__` | FunctionDef | 43 | 159 |
| `_set_athletic_leg_crouch` | FunctionDef | 161 | 171 |
| `reset` | FunctionDef | 173 | 245 |
| `_get_obs` | FunctionDef | 247 | 287 |
| `step` | FunctionDef | 289 | 411 |
| `_compute_reward` | FunctionDef | 413 | 517 |
| `render` | FunctionDef | 519 | 524 |
| `close` | FunctionDef | 526 | 528 |

## 전체 원문

````text
    1 | """
    2 | DirectionalBattingEnv: Phase 1 Goal-Conditioned Precision Batting Environment for H1 Humanoid.
    3 | Features:
    4 | - Full 19-DoF H1 kinematics with athletic batting stance and upper-body swing actuators.
    5 | - Realistic motor torque saturation limits (H1 actuator limits).
    6 | - Goal-conditioned directional hitting: Target Azimuth (Pull / Center / Push), Target Launch Angle, Target Exit Velocity.
    7 | - Precision sweet-spot contact detection and fair-ball exit trajectory tracking.
    8 | """
    9 | 
   10 | import os
   11 | import sys
   12 | import numpy as np
   13 | import gymnasium as gym
   14 | from gymnasium import spaces
   15 | import mujoco
   16 | 
   17 | 
   18 | class DirectionalBattingEnv(gym.Env):
   19 |     """
   20 |     Phase 1 Goal-Conditioned Directional Batting Environment.
   21 |     
   22 |     Observation (31 dims):
   23 |       [0:3]   Pitched ball pos relative to plate [x, y, z]
   24 |       [3:6]   Pitched ball velocity [vx, vy, vz]
   25 |       [6]     Time remaining to reach plate (s)
   26 |       [7:10]  Goal vector: [target_azimuth_rad, target_launch_angle_rad, target_exit_vel]
   27 |       [10:15] Robot swing joint positions [torso, r_pitch, r_roll, r_yaw, r_elbow]
   28 |       [15:20] Robot swing joint velocities
   29 |       [20:23] Bat sweet spot world pos [x, y, z]
   30 |       [23:26] Bat sweet spot linear velocity [vx, vy, vz]
   31 |       [26:31] Previous action (5 dims)
   32 |       
   33 |     Action (5 dims, range [-1, 1]):
   34 |       a[0]: Swing timing lead/lag delta: dt in [-0.030, +0.030] s (Pull vs Center vs Push control)
   35 |       a[1]: Bat elevation delta: dz in [-0.08, +0.08] m (High vs Low pitch tracking)
   36 |       a[2]: Swing plane / attack angle delta: dalpha in [-0.15, +0.15] rad (Launch angle control)
   37 |       a[3]: Torso uncoiling duration / power: dpower in [-0.02, +0.02] s (Exit velocity modulation)
   38 |       a[4]: Arm extension / reach: delb in [-0.15, +0.15] rad (Inside vs Outside sweet spot alignment)
   39 |     """
   40 | 
   41 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}
   42 | 
   43 |     def __init__(
   44 |         self,
   45 |         xml_path=None,
   46 |         render_mode=None,
   47 |         frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz control)
   48 |         pitch_speed_range=(14.0, 18.0),  # 50 ~ 65 km/h
   49 |         pitch_dist=7.5,
   50 |     ):
   51 |         super().__init__()
   52 | 
   53 |         if xml_path is None:
   54 |             curr_dir = os.path.dirname(os.path.abspath(__file__))
   55 |             xml_path = os.path.join(curr_dir, "..", "models", "h1_baseball.xml")
   56 | 
   57 |         self.xml_path = xml_path
   58 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   59 |         
   60 |         # Position H1 batter at home plate batter box
   61 |         pelvis_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
   62 |         if pelvis_body_id >= 0:
   63 |             self.model.body_pos[pelvis_body_id, 0] = -0.90
   64 |             self.model.body_pos[pelvis_body_id, 1] = 0.00
   65 |             self.model.body_pos[pelvis_body_id, 2] = 0.95
   66 | 
   67 |         self.data = mujoco.MjData(self.model)
   68 | 
   69 |         self.render_mode = render_mode
   70 |         self.frame_skip = frame_skip
   71 |         self.dt = self.model.opt.timestep * self.frame_skip  # 0.02 s
   72 |         self.pitch_speed_range = pitch_speed_range
   73 |         self.pitch_dist = pitch_dist
   74 | 
   75 |         # Identify Geoms & Sites
   76 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   77 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   78 |         self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")
   79 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   80 | 
   81 |         # Freejoint for ball
   82 |         ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   83 |         self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
   84 |         self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]
   85 | 
   86 |         # Upper body swing actuators and joints
   87 |         self.swing_actuator_names = [
   88 |             "torso",
   89 |             "right_shoulder_pitch",
   90 |             "right_shoulder_roll",
   91 |             "right_shoulder_yaw",
   92 |             "right_elbow",
   93 |         ]
   94 |         self.act_ids = [
   95 |             mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
   96 |             for name in self.swing_actuator_names
   97 |         ]
   98 |         self.jnt_ids = [self.model.actuator_trnid[a, 0] for a in self.act_ids]
   99 |         self.qpos_adrs = [self.model.jnt_qposadr[j] for j in self.jnt_ids]
  100 |         self.qvel_adrs = [self.model.jnt_dofadr[j] for j in self.jnt_ids]
  101 | 
  102 |         # Athletic batting crouch leg joint addresses
  103 |         self.leg_joint_names = [
  104 |             "left_hip_pitch", "left_knee", "left_hip_roll",
  105 |             "right_hip_pitch", "right_knee", "right_hip_roll"
  106 |         ]
  107 |         self.leg_qpos_adrs = [
  108 |             self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, lj)]
  109 |             for lj in self.leg_joint_names
  110 |         ]
  111 | 
  112 |         # Canonical Kinematic Chain Swing Keyframes
  113 |         # [torso, rsp, rsr, rsy, relb]
  114 |         self.base_keyframes = np.array([
  115 |             [-0.40, -1.00,  0.00,  0.40,  1.50],  # 0: Stance
  116 |             [-0.60, -1.15,  0.00,  0.60,  1.70],  # 1: Load / Takeback
  117 |             [-0.10, -0.70, -0.05,  0.20,  1.20],  # 2: Stride / Uncoil start
  118 |             [ 0.50, -0.30, -0.10, -0.10,  0.70],  # 3: Slot / Acceleration
  119 |             [ 1.15,  0.20, -0.08, -0.40,  0.35],  # 4: Contact
  120 |             [ 1.70,  0.80,  0.00, -0.70,  1.20]   # 5: Follow-through
  121 |         ], dtype=np.float32)
  122 | 
  123 |         # PD Gains for Upper Body Actuators
  124 |         self.Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
  125 |         self.Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)
  126 | 
  127 |         # Action Space: 5-dim continuous
  128 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(5,), dtype=np.float32)
  129 | 
  130 |         # Observation Space: 31-dim continuous
  131 |         obs_dim = 7 + 3 + 5 + 5 + 3 + 3 + 5
  132 |         self.observation_space = spaces.Box(
  133 |             low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
  134 |         )
  135 | 
  136 |         # Episode State Variables
  137 |         self.current_step = 0
  138 |         self.max_steps = 35
  139 |         self.prev_action = np.zeros(5, dtype=np.float32)
  140 |         self.filtered_action = np.zeros(5, dtype=np.float32)
  141 |         self.swing_triggered = False
  142 |         self.locked_t_trigger = 0.0
  143 |         self.locked_swing_duration = 0.17
  144 |         self.has_contacted = False
  145 |         self.contact_reward_given = False
  146 |         self.contact_step = -1
  147 |         self.contact_ball_pos = None
  148 |         self.contact_sweet_pos = None
  149 |         self.exit_ball_vel = None
  150 |         self.min_ball_sweet_dist = 999.0
  151 |         self.exit_velocity = 0.0
  152 |         self.exit_azimuth_deg = 0.0
  153 |         self.exit_launch_deg = 0.0
  154 |         self.is_fair_hit = False
  155 | 
  156 |         # Viewer / Renderer
  157 |         self.renderer = None
  158 |         if self.render_mode in ["rgb_array", "human"]:
  159 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  160 | 
  161 |     def _set_athletic_leg_crouch(self):
  162 |         """Maintains stable athletic batting stance legs."""
  163 |         for lj, qadr in zip(self.leg_joint_names, self.leg_qpos_adrs):
  164 |             if "pitch" in lj:
  165 |                 self.data.qpos[qadr] = -0.35
  166 |             elif "knee" in lj:
  167 |                 self.data.qpos[qadr] = 0.70
  168 |             elif "left_hip_roll" in lj:
  169 |                 self.data.qpos[qadr] = 0.18
  170 |             elif "right_hip_roll" in lj:
  171 |                 self.data.qpos[qadr] = -0.18
  172 | 
  173 |     def reset(self, seed=None, options=None):
  174 |         super().reset(seed=seed)
  175 |         mujoco.mj_resetData(self.model, self.data)
  176 | 
  177 |         self.current_step = 0
  178 |         self.prev_action = np.zeros(5, dtype=np.float32)
  179 |         self.filtered_action = np.zeros(5, dtype=np.float32)
  180 |         self.swing_triggered = False
  181 |         self.locked_t_trigger = 0.0
  182 |         self.locked_swing_duration = 0.17
  183 |         self.has_contacted = False
  184 |         self.contact_reward_given = False
  185 |         self.contact_step = -1
  186 |         self.contact_ball_pos = None
  187 |         self.contact_sweet_pos = None
  188 |         self.exit_ball_vel = None
  189 |         self.min_ball_sweet_dist = 999.0
  190 |         self.exit_velocity = 0.0
  191 |         self.exit_azimuth_deg = 0.0
  192 |         self.exit_launch_deg = 0.0
  193 |         self.is_fair_hit = False
  194 | 
  195 |         # Set athletic stance
  196 |         self._set_athletic_leg_crouch()
  197 | 
  198 |         # Initialize upper body joints to stance keyframe
  199 |         for i, qadr in enumerate(self.qpos_adrs):
  200 |             self.data.qpos[qadr] = self.base_keyframes[0, i]
  201 | 
  202 |         # 1. Sample Goal Condition Vector
  203 |         # Target Azimuth: Pull (-35° to -10°), Center (-10° to +10°), Push (+10° to +35°)
  204 |         target_azimuth_deg = self.np_random.uniform(-35.0, 35.0)
  205 |         self.target_azimuth_rad = float(np.radians(target_azimuth_deg))
  206 | 
  207 |         # Target Launch Angle: Line Drive to home run trajectory (12° to 32°)
  208 |         target_launch_deg = self.np_random.uniform(12.0, 32.0)
  209 |         self.target_launch_rad = float(np.radians(target_launch_deg))
  210 | 
  211 |         # Target Exit Velocity: 10 to 20 m/s (36 ~ 72 km/h)
  212 |         self.target_exit_vel = float(np.random.uniform(10.0, 18.0) if not hasattr(self, 'np_random') else self.np_random.uniform(10.0, 18.0))
  213 | 
  214 |         # 2. Sample Pitched Ball Parameters
  215 |         pitch_speed = self.np_random.uniform(*self.pitch_speed_range)
  216 |         vy = -pitch_speed
  217 |         
  218 |         # Target arrival coordinate in strike zone (over home plate at y = 0.22m)
  219 |         plate_y_contact = 0.22
  220 |         t_flight = (self.pitch_dist - plate_y_contact) / abs(vy)
  221 |         self.nominal_t_flight = t_flight
  222 | 
  223 |         # Inside / Outside pitch variation (0.10m ~ 0.16m over home plate)
  224 |         target_x = self.np_random.uniform(0.10, 0.16)
  225 |         # Pitch height variation centered on sweet spot hitting plane (0.74m ~ 0.78m)
  226 |         target_z = self.np_random.uniform(0.74, 0.78)
  227 | 
  228 |         # Calculate initial vertical velocity with gravity drop
  229 |         z0 = 0.85
  230 |         drop = 0.5 * 9.81 * (t_flight ** 2)
  231 |         vz = (target_z + drop - z0) / t_flight
  232 | 
  233 |         # Set ball position and velocity
  234 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [target_x, self.pitch_dist, z0]
  235 |         self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  236 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, vy, vz]
  237 |         self.data.qvel[self.ball_qvel_adr+3:self.ball_qvel_adr+6] = [0.0, 0.0, 0.0]
  238 | 
  239 |         mujoco.mj_forward(self.model, self.data)
  240 | 
  241 |         # Nominal swing trigger time (empirically centered for symmetric Pull/Center/Push coverage)
  242 |         self.nominal_t_trigger = t_flight - 0.126
  243 |         self.nominal_swing_duration = 0.17
  244 | 
  245 |         return self._get_obs(), {}
  246 | 
  247 |     def _get_obs(self):
  248 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  249 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  250 |         
  251 |         # Time remaining to plate
  252 |         vy = ball_vel[1]
  253 |         t_remain = max(0.0, ball_pos[1] / abs(vy)) if vy < -0.1 else 0.0
  254 | 
  255 |         # Goal vector (3 dims)
  256 |         goal = np.array([
  257 |             self.target_azimuth_rad,
  258 |             self.target_launch_rad,
  259 |             self.target_exit_vel,
  260 |         ], dtype=np.float32)
  261 | 
  262 |         # Upper body joint positions and velocities (5 + 5 = 10 dims)
  263 |         joint_pos = np.array([self.data.qpos[adr] for adr in self.qpos_adrs], dtype=np.float32)
  264 |         joint_vel = np.array([self.data.qvel[adr] for adr in self.qvel_adrs], dtype=np.float32)
  265 | 
  266 |         # Bat sweet spot state (3 + 3 = 6 dims)
  267 |         sweet_pos = self.data.site_xpos[self.sweet_spot_id].astype(np.float32)
  268 |         res = np.zeros(6, dtype=np.float64)
  269 |         mujoco.mj_objectVelocity(
  270 |             self.model, self.data, mujoco.mjtObj.mjOBJ_SITE,
  271 |             self.sweet_spot_id, res, 0
  272 |         )
  273 |         sweet_vel = res[3:6].astype(np.float32)
  274 | 
  275 |         obs = np.concatenate([
  276 |             ball_pos,           # 3
  277 |             ball_vel,           # 3
  278 |             [t_remain],         # 1
  279 |             goal,               # 3
  280 |             joint_pos,          # 5
  281 |             joint_vel,          # 5
  282 |             sweet_pos,          # 3
  283 |             sweet_vel,          # 3
  284 |             self.prev_action,   # 5
  285 |         ], dtype=np.float32)
  286 | 
  287 |         return obs
  288 | 
  289 |     def step(self, action):
  290 |         self.current_step += 1
  291 |         action = np.clip(action, -1.0, 1.0).astype(np.float32)
  292 | 
  293 |         # Exponential moving average filter for smooth continuous action modulation
  294 |         self.filtered_action = 0.6 * self.filtered_action + 0.4 * action
  295 | 
  296 |         # Unpack Action Modulations:
  297 |         # a[0]: Timing delta dt in [-0.030, +0.030] s (Pull < 0, Push > 0)
  298 |         dt_timing = float(self.filtered_action[0] * 0.030)
  299 |         # a[1]: Bat elevation delta dz in [-0.08, +0.08] m
  300 |         d_rsp = float(-self.filtered_action[1] * 0.12)
  301 |         # a[2]: Attack angle / plane tilt -> shoulder roll & elbow tilt
  302 |         d_tilt = float(self.filtered_action[2] * 0.10)
  303 |         # a[3]: Torso uncoiling speed / duration delta in [-0.02, +0.02] s
  304 |         d_duration = float(-self.filtered_action[3] * 0.02)
  305 |         # a[4]: Extension / sweet spot alignment -> elbow delta
  306 |         d_elbow = float(self.filtered_action[4] * 0.15)
  307 | 
  308 |         # Swing trigger and duration management:
  309 |         sim_time_curr = self.data.time
  310 |         if not self.swing_triggered:
  311 |             candidate_t_trigger = max(0.04, self.nominal_t_trigger + dt_timing)
  312 |             candidate_duration = max(0.12, self.nominal_swing_duration + d_duration)
  313 |             if sim_time_curr >= candidate_t_trigger:
  314 |                 self.swing_triggered = True
  315 |                 self.locked_t_trigger = candidate_t_trigger
  316 |                 self.locked_swing_duration = candidate_duration
  317 |             t_trigger = candidate_t_trigger
  318 |             swing_duration = candidate_duration
  319 |         else:
  320 |             t_trigger = self.locked_t_trigger
  321 |             swing_duration = self.locked_swing_duration
  322 | 
  323 |         # Modulate Keyframes for entire hitting phase (Keyframes 3, 4, 5)
  324 |         mod_keyframes = self.base_keyframes.copy()
  325 |         mod_keyframes[3, 1] += d_rsp * 0.6
  326 |         mod_keyframes[4, 1] += d_rsp
  327 |         mod_keyframes[5, 1] += d_rsp
  328 | 
  329 |         mod_keyframes[3, 2] += d_tilt * 0.6
  330 |         mod_keyframes[4, 2] += d_tilt
  331 |         mod_keyframes[5, 2] += d_tilt
  332 | 
  333 |         mod_keyframes[3, 4] += d_elbow * 0.6
  334 |         mod_keyframes[4, 4] += d_elbow
  335 |         mod_keyframes[5, 4] += d_elbow
  336 | 
  337 |         # Execute physics simulation over frame_skip sub-steps
  338 |         for _ in range(self.frame_skip):
  339 |             sim_time = self.data.time
  340 | 
  341 |             # Compute target upper-body joints
  342 |             if sim_time < t_trigger:
  343 |                 target_q = mod_keyframes[0]
  344 |             else:
  345 |                 progress = np.clip((sim_time - t_trigger) / swing_duration, 0.0, 1.0)
  346 |                 idx_f = progress * (len(mod_keyframes) - 1)
  347 |                 idx0 = int(np.floor(idx_f))
  348 |                 idx1 = min(idx0 + 1, len(mod_keyframes) - 1)
  349 |                 alpha = idx_f - idx0
  350 |                 target_q = (1.0 - alpha) * mod_keyframes[idx0] + alpha * mod_keyframes[idx1]
  351 | 
  352 |             # Apply PD torques to upper body actuators with torque saturation clipping
  353 |             for i, aid in enumerate(self.act_ids):
  354 |                 q = self.data.qpos[self.qpos_adrs[i]]
  355 |                 dq = self.data.qvel[self.qvel_adrs[i]]
  356 |                 tau = self.Kp[i] * (target_q[i] - q) - self.Kd[i] * dq
  357 |                 ctrl_min = self.model.actuator_ctrlrange[aid, 0]
  358 |                 ctrl_max = self.model.actuator_ctrlrange[aid, 1]
  359 |                 self.data.ctrl[aid] = np.clip(tau, ctrl_min, ctrl_max)
  360 | 
  361 |             # Step MuJoCo physics
  362 |             mujoco.mj_step(self.model, self.data)
  363 | 
  364 |             # Track minimum distance between ball and sweet spot
  365 |             ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  366 |             sweet_pos = self.data.site_xpos[self.sweet_spot_id]
  367 |             dist_curr = float(np.linalg.norm(ball_pos - sweet_pos))
  368 |             if dist_curr < self.min_ball_sweet_dist:
  369 |                 self.min_ball_sweet_dist = dist_curr
  370 | 
  371 |             # Detect Bat-Ball Collision
  372 |             if self.data.ncon > 0:
  373 |                 for c in range(self.data.ncon):
  374 |                     con = self.data.contact[c]
  375 |                     if (con.geom1 == self.bat_geom_id and con.geom2 == self.ball_geom_id) or \
  376 |                        (con.geom1 == self.ball_geom_id and con.geom2 == self.bat_geom_id):
  377 |                         if not self.has_contacted:
  378 |                             self.has_contacted = True
  379 |                             self.contact_step = self.current_step
  380 |                             self.contact_ball_pos = ball_pos.copy()
  381 |                             self.contact_sweet_pos = sweet_pos.copy()
  382 |                         break
  383 | 
  384 |             # If contact has occurred, track post-contact ball velocity
  385 |             if self.has_contacted:
  386 |                 curr_ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  387 |                 if curr_ball_vel[1] > 0:
  388 |                     self.is_fair_hit = True
  389 |                     if self.exit_ball_vel is None or np.linalg.norm(curr_ball_vel) > np.linalg.norm(self.exit_ball_vel):
  390 |                         self.exit_ball_vel = curr_ball_vel.copy()
  391 |                 elif self.exit_ball_vel is None:
  392 |                     self.exit_ball_vel = curr_ball_vel.copy()
  393 | 
  394 |         # Check termination condition:
  395 |         ball_y = self.data.qpos[self.ball_qpos_adr+1]
  396 |         terminated = False
  397 |         if self.has_contacted:
  398 |             if (self.current_step - self.contact_step) >= 6 or ball_y > 4.0:
  399 |                 terminated = True
  400 |         elif ball_y < -0.7:
  401 |             terminated = True
  402 |         elif self.current_step >= self.max_steps:
  403 |             terminated = True
  404 | 
  405 |         truncated = (self.current_step >= self.max_steps) and not terminated
  406 | 
  407 |         # Reward Computation
  408 |         reward, info = self._compute_reward(action)
  409 | 
  410 |         self.prev_action = action.copy()
  411 |         return self._get_obs(), reward, terminated, truncated, info
  412 | 
  413 |     def _compute_reward(self, action):
  414 |         reward = 0.0
  415 |         info = {
  416 |             "contact": self.has_contacted,
  417 |             "fair_hit": self.is_fair_hit,
  418 |             "min_sweet_dist_cm": self.min_ball_sweet_dist * 100.0,
  419 |             "exit_speed_ms": 0.0,
  420 |             "exit_azimuth_deg": 0.0,
  421 |             "exit_launch_deg": 0.0,
  422 |             "sweet_spot_offset_cm": 99.0,
  423 |             "azimuth_error_deg": 99.0,
  424 |             "launch_error_deg": 99.0,
  425 |         }
  426 | 
  427 |         # 1. Dense Approach Shaping Reward (continuous guidance towards ball)
  428 |         r_approach = float(np.exp(-8.0 * self.min_ball_sweet_dist))
  429 |         reward += r_approach
  430 | 
  431 |         # 2. Bat-Ball Contact & Precision Trajectory Evaluation (awarded once upon confirmed contact)
  432 |         if self.has_contacted and not self.contact_reward_given and self.exit_ball_vel is not None:
  433 |             self.contact_reward_given = True
  434 |             
  435 |             # Base Contact Bonus
  436 |             r_contact = 6.0
  437 | 
  438 |             # Sweet Spot Precision Contact
  439 |             sweet_offset = float(np.linalg.norm(self.contact_sweet_pos - self.contact_ball_pos))
  440 |             info["sweet_spot_offset_cm"] = sweet_offset * 100.0
  441 |             r_sweet = 5.0 * float(np.exp(-20.0 * sweet_offset))
  442 | 
  443 |             vx, vy, vz = self.exit_ball_vel
  444 |             exit_speed = float(np.linalg.norm(self.exit_ball_vel))
  445 |             info["exit_speed_ms"] = exit_speed
  446 |             self.exit_velocity = exit_speed
  447 | 
  448 |             if self.is_fair_hit and vy > 0.05:
  449 |                 # Solid Fair Ball Forward Rebound Bonus
  450 |                 r_forward = 10.0
  451 | 
  452 |                 # Spray Azimuth: negative = Left field (Pull), positive = Right field (Push)
  453 |                 azimuth_rad = float(np.arctan2(vx, vy))
  454 |                 azimuth_deg = float(np.degrees(azimuth_rad))
  455 |                 info["exit_azimuth_deg"] = azimuth_deg
  456 |                 self.exit_azimuth_deg = azimuth_deg
  457 | 
  458 |                 # Launch Angle: relative to horizontal
  459 |                 ground_speed = float(np.hypot(vx, vy))
  460 |                 launch_rad = float(np.arctan2(vz, max(0.1, ground_speed)))
  461 |                 launch_deg = float(np.degrees(launch_rad))
  462 |                 info["exit_launch_deg"] = launch_deg
  463 |                 self.exit_launch_deg = launch_deg
  464 | 
  465 |                 # Directional Hitting Goal-Conditioning Reward
  466 |                 azimuth_err_rad = abs(azimuth_rad - self.target_azimuth_rad)
  467 |                 info["azimuth_error_deg"] = float(np.degrees(azimuth_err_rad))
  468 |                 # Gaussian + linear gradient support
  469 |                 r_azimuth = 10.0 * float(np.exp(-0.5 * (azimuth_err_rad / 0.35) ** 2)) + \
  470 |                             5.0 * float(max(0.0, 1.0 - azimuth_err_rad / 1.0))
  471 | 
  472 |                 # Sector Matching Milestone Bonus
  473 |                 target_deg = float(np.degrees(self.target_azimuth_rad))
  474 |                 r_sector = 0.0
  475 |                 if target_deg < -10.0 and azimuth_deg < -10.0:
  476 |                     r_sector = 5.0
  477 |                 elif target_deg > 10.0 and azimuth_deg > 10.0:
  478 |                     r_sector = 5.0
  479 |                 elif abs(target_deg) <= 10.0 and abs(azimuth_deg) <= 10.0:
  480 |                     r_sector = 5.0
  481 | 
  482 |                 # Launch Angle Goal-Conditioning Reward
  483 |                 launch_err_rad = abs(launch_rad - self.target_launch_rad)
  484 |                 info["launch_error_deg"] = float(np.degrees(launch_err_rad))
  485 |                 # Gaussian + linear gradient support
  486 |                 r_launch = 8.0 * float(np.exp(-0.5 * (launch_err_rad / 0.25) ** 2)) + \
  487 |                            4.0 * float(max(0.0, 1.0 - launch_err_rad / 0.6))
  488 | 
  489 |                 # Exit Velocity Modulation Reward
  490 |                 r_vel = 5.0 * float(np.clip(exit_speed / max(1.0, self.target_exit_vel), 0.0, 1.5))
  491 | 
  492 |                 reward += (r_contact + r_sweet + r_forward + r_azimuth + r_sector + r_launch + r_vel)
  493 |             else:
  494 |                 # Foul tip or backward deflection penalty
  495 |                 reward += (r_contact + r_sweet - 3.0)
  496 |                 info["exit_azimuth_deg"] = -90.0
  497 |                 info["exit_launch_deg"] = -30.0
  498 | 
  499 |         # Maintain info metrics for active contact
  500 |         if self.has_contacted and self.exit_ball_vel is not None:
  501 |             info["contact"] = True
  502 |             info["fair_hit"] = self.is_fair_hit
  503 |             info["exit_speed_ms"] = self.exit_velocity
  504 |             info["exit_azimuth_deg"] = self.exit_azimuth_deg
  505 |             info["exit_launch_deg"] = self.exit_launch_deg
  506 |             if self.is_fair_hit:
  507 |                 info["azimuth_error_deg"] = abs(self.exit_azimuth_deg - np.degrees(self.target_azimuth_rad))
  508 |                 info["launch_error_deg"] = abs(self.exit_launch_deg - np.degrees(self.target_launch_rad))
  509 |             if self.contact_sweet_pos is not None and self.contact_ball_pos is not None:
  510 |                 info["sweet_spot_offset_cm"] = float(np.linalg.norm(self.contact_sweet_pos - self.contact_ball_pos)) * 100.0
  511 | 
  512 |         # 3. Regularization & Action Smoothness Penalty
  513 |         action_penalty = 0.01 * float(np.sum(action ** 2))
  514 |         action_rate_penalty = 0.02 * float(np.sum((action - self.prev_action) ** 2))
  515 |         reward -= (action_penalty + action_rate_penalty)
  516 | 
  517 |         return reward, info
  518 | 
  519 |     def render(self):
  520 |         if self.render_mode == "rgb_array":
  521 |             self.renderer.update_scene(self.data, camera="broadcast_cam")
  522 |             return self.renderer.render()
  523 |         elif self.render_mode == "human":
  524 |             pass
  525 | 
  526 |     def close(self):
  527 |         if self.renderer is not None:
  528 |             self.renderer.close()
````
