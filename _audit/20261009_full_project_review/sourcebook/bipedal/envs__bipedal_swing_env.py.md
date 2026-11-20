# bipedal/envs/bipedal_swing_env.py

원본: [envs/bipedal_swing_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/envs/bipedal_swing_env.py)

SHA256: `3ed0a1e4e13cd7f7fa73290e737ed78d5b969409a4cd93f33b56addb9cbc50c7`

전체 401행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BipedalSwingEnv` | ClassDef | 24 | 401 |
| `__init__` | FunctionDef | 33 | 138 |
| `reset` | FunctionDef | 140 | 205 |
| `_get_obs` | FunctionDef | 207 | 237 |
| `step` | FunctionDef | 239 | 391 |
| `render` | FunctionDef | 393 | 397 |
| `close` | FunctionDef | 399 | 401 |

## 전체 원문

````text
    1 | """
    2 | BipedalSwingEnv: Phase 3 Whole-Body Kinetic Chain Batting for H1 Humanoid.
    3 | Features:
    4 | - Full 6-DoF Free-Floating Pelvis (pelvis_joint).
    5 | - Ground Reaction Forces (GRF) and bipedal balance during high-speed athletic swing.
    6 | - Active leg PD balance controller with dynamic weight-shift transfer.
    7 | - Goal-conditioned directional hitting (Pull / Center / Push).
    8 | - Fall detection and dynamic ZMP balance reward formulation.
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
   24 | class BipedalSwingEnv(gym.Env):
   25 |     """
   26 |     Phase 3 Whole-Body Kinetic Chain Batting Environment.
   27 |     Robot has a 6-DoF free-floating pelvis and must maintain balance on two feet
   28 |     while swinging at an incoming pitched ball.
   29 |     """
   30 | 
   31 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}
   32 | 
   33 |     def __init__(
   34 |         self,
   35 |         xml_path=None,
   36 |         render_mode=None,
   37 |         frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz)
   38 |         pitch_speed_range=(14.0, 18.0),
   39 |         pitch_dist=7.5,
   40 |     ):
   41 |         super().__init__()
   42 | 
   43 |         if xml_path is None:
   44 |             xml_path = os.path.join(parent_dir, "models", "h1_bipedal_baseball.xml")
   45 | 
   46 |         self.xml_path = xml_path
   47 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   48 |         self.data = mujoco.MjData(self.model)
   49 | 
   50 |         self.render_mode = render_mode
   51 |         self.frame_skip = frame_skip
   52 |         self.dt = self.model.opt.timestep * self.frame_skip  # 0.02s
   53 |         self.pitch_speed_range = pitch_speed_range
   54 |         self.pitch_dist = pitch_dist
   55 | 
   56 |         # Identify Bodies & Sites
   57 |         self.pelvis_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
   58 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   59 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   60 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   61 |         self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")
   62 | 
   63 |         # Freejoints
   64 |         ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   65 |         self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
   66 |         self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]
   67 | 
   68 |         pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "pelvis_joint")
   69 |         self.pelvis_qpos_adr = self.model.jnt_qposadr[pelvis_jnt_id]
   70 |         self.pelvis_qvel_adr = self.model.jnt_dofadr[pelvis_jnt_id]
   71 | 
   72 |         # Upper body swing actuators [torso, rsp, rsr, rsy, relb]
   73 |         self.swing_act_names = ["torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"]
   74 |         self.swing_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.swing_act_names]
   75 |         self.swing_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.swing_act_ids]
   76 |         self.swing_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.swing_act_ids]
   77 | 
   78 |         # Leg actuators (10 motors)
   79 |         self.leg_act_names = [
   80 |             "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
   81 |             "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
   82 |         ]
   83 |         self.leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.leg_act_names]
   84 |         self.leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.leg_act_ids]
   85 |         self.leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.leg_act_ids]
   86 | 
   87 |         # Gains
   88 |         self.swing_Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
   89 |         self.swing_Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)
   90 | 
   91 |         self.leg_Kp = np.array([350.0, 350.0, 450.0, 500.0, 250.0, 350.0, 350.0, 450.0, 500.0, 250.0], dtype=np.float32)
   92 |         self.leg_Kd = np.array([30.0,  30.0,  40.0,  45.0,  20.0,  30.0,  30.0,  40.0,  45.0,  20.0], dtype=np.float32)
   93 | 
   94 |         # Athletic batting keyframes
   95 |         self.base_keyframes = np.array([
   96 |             [-0.40, -1.00,  0.00,  0.40,  1.50],
   97 |             [-0.60, -1.15,  0.00,  0.60,  1.70],
   98 |             [-0.10, -0.70, -0.05,  0.20,  1.20],
   99 |             [ 0.50, -0.30, -0.10, -0.10,  0.70],
  100 |             [ 1.15,  0.20, -0.08, -0.40,  0.35],
  101 |             [ 1.70,  0.80,  0.00, -0.70,  1.20]
  102 |         ], dtype=np.float32)
  103 | 
  104 |         # Nominal Leg Stance
  105 |         self.base_leg_q = np.array([
  106 |             0.0, 0.12, -0.35, 0.65, -0.30,  # Left leg
  107 |             0.0,-0.12, -0.35, 0.65, -0.30   # Right leg
  108 |         ], dtype=np.float32)
  109 | 
  110 |         # Action: 6 dims
  111 |         # a[0:5]: swing modulations (lead/lag, dz, attack angle, power, reach)
  112 |         # a[5]: leg weight-shift modulation (front-to-back load transfer)
  113 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)
  114 | 
  115 |         # Obs: 36 dims (ball state 7, goals 3, upper joints 10, sweet 6, pelvis state 6, prev_action 4)
  116 |         self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(38,), dtype=np.float32)
  117 | 
  118 |         self.current_step = 0
  119 |         self.max_steps = 35
  120 |         self.prev_action = np.zeros(6, dtype=np.float32)
  121 |         self.filtered_action = np.zeros(6, dtype=np.float32)
  122 |         self.swing_triggered = False
  123 |         self.locked_t_trigger = 0.0
  124 |         self.locked_swing_duration = 0.17
  125 |         self.has_contacted = False
  126 |         self.contact_reward_given = False
  127 |         self.contact_step = -1
  128 |         self.contact_ball_pos = None
  129 |         self.contact_sweet_pos = None
  130 |         self.exit_velocity = 0.0
  131 |         self.exit_azimuth_deg = 0.0
  132 |         self.exit_launch_deg = 0.0
  133 |         self.is_fair_hit = False
  134 |         self.has_fallen = False
  135 | 
  136 |         self.renderer = None
  137 |         if self.render_mode in ["rgb_array", "human"]:
  138 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  139 | 
  140 |     def reset(self, seed=None, options=None):
  141 |         super().reset(seed=seed)
  142 |         mujoco.mj_resetData(self.model, self.data)
  143 | 
  144 |         self.current_step = 0
  145 |         self.prev_action = np.zeros(6, dtype=np.float32)
  146 |         self.filtered_action = np.zeros(6, dtype=np.float32)
  147 |         self.swing_triggered = False
  148 |         self.locked_t_trigger = 0.0
  149 |         self.locked_swing_duration = 0.17
  150 |         self.has_contacted = False
  151 |         self.contact_reward_given = False
  152 |         self.contact_step = -1
  153 |         self.contact_ball_pos = None
  154 |         self.contact_sweet_pos = None
  155 |         self.exit_velocity = 0.0
  156 |         self.exit_azimuth_deg = 0.0
  157 |         self.exit_launch_deg = 0.0
  158 |         self.is_fair_hit = False
  159 |         self.has_fallen = False
  160 | 
  161 |         # Set 6-DoF Pelvis floating base in batter's box
  162 |         self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3] = [-0.85, 0.00, 0.88]
  163 |         self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  164 |         self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+6] = 0.0
  165 | 
  166 |         # Set leg stance
  167 |         for i, adr in enumerate(self.leg_qpos_adrs):
  168 |             self.data.qpos[adr] = self.base_leg_q[i]
  169 | 
  170 |         # Set upper body initial keyframe
  171 |         for i, adr in enumerate(self.swing_qpos_adrs):
  172 |             self.data.qpos[adr] = self.base_keyframes[0, i]
  173 | 
  174 |         # Sample Goal Condition Vector
  175 |         target_azimuth_deg = self.np_random.uniform(-35.0, 35.0)
  176 |         self.target_azimuth_rad = float(np.radians(target_azimuth_deg))
  177 |         target_launch_deg = self.np_random.uniform(12.0, 32.0)
  178 |         self.target_launch_rad = float(np.radians(target_launch_deg))
  179 |         self.target_exit_vel = float(self.np_random.uniform(10.0, 18.0))
  180 | 
  181 |         # Sample Pitched Ball
  182 |         pitch_speed = self.np_random.uniform(*self.pitch_speed_range)
  183 |         vy = -pitch_speed
  184 |         plate_y_contact = 0.22
  185 |         t_flight = (self.pitch_dist - plate_y_contact) / abs(vy)
  186 |         self.nominal_t_flight = t_flight
  187 | 
  188 |         target_x = self.np_random.uniform(0.06, 0.12)
  189 |         target_z = self.np_random.uniform(0.55, 0.62)
  190 | 
  191 |         z0 = 0.85
  192 |         drop = 0.5 * 9.81 * (t_flight ** 2)
  193 |         vz = (target_z + drop - z0) / t_flight
  194 | 
  195 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [target_x, self.pitch_dist, z0]
  196 |         self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  197 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, vy, vz]
  198 |         self.data.qvel[self.ball_qvel_adr+3:self.ball_qvel_adr+6] = [0.0, 0.0, 0.0]
  199 | 
  200 |         mujoco.mj_forward(self.model, self.data)
  201 | 
  202 |         self.nominal_t_trigger = t_flight - 0.145
  203 |         self.nominal_swing_duration = 0.17
  204 | 
  205 |         return self._get_obs(), {}
  206 | 
  207 |     def _get_obs(self):
  208 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  209 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  210 |         t_remain = max(0.0, (ball_pos[1] - 0.20) / abs(ball_vel[1])) if abs(ball_vel[1]) > 1.0 else 0.0
  211 | 
  212 |         goals = np.array([self.target_azimuth_rad, self.target_launch_rad, self.target_exit_vel], dtype=np.float32)
  213 |         swing_qpos = np.array([self.data.qpos[adr] for adr in self.swing_qpos_adrs], dtype=np.float32)
  214 |         swing_qvel = np.array([self.data.qvel[adr] for adr in self.swing_qvel_adrs], dtype=np.float32)
  215 | 
  216 |         sweet_pos = self.data.site_xpos[self.sweet_spot_id]
  217 |         sweet_v = np.zeros(6, dtype=np.float64)
  218 |         mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_SITE, self.sweet_spot_id, sweet_v, 0)
  219 |         sweet_vel = sweet_v[3:6]
  220 | 
  221 |         pelvis_pos = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3]
  222 |         pelvis_vel = self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+3]
  223 | 
  224 |         obs = np.concatenate([
  225 |             ball_pos,                                    # 3
  226 |             ball_vel,                                    # 3
  227 |             np.array([t_remain], dtype=np.float32),      # 1
  228 |             goals,                                       # 3
  229 |             swing_qpos,                                  # 5
  230 |             swing_qvel,                                  # 5
  231 |             sweet_pos,                                   # 3
  232 |             sweet_vel,                                   # 3
  233 |             pelvis_pos,                                  # 3
  234 |             pelvis_vel,                                  # 3
  235 |             np.array([self.prev_action[0], self.prev_action[1], self.prev_action[2], self.prev_action[3], self.prev_action[4], self.prev_action[5]], dtype=np.float32), # 6
  236 |         ])
  237 |         return obs.astype(np.float32)
  238 | 
  239 |     def step(self, action):
  240 |         action = np.clip(action, -1.0, 1.0).astype(np.float32)
  241 |         self.filtered_action = 0.6 * self.filtered_action + 0.4 * action
  242 | 
  243 |         dt_lead_lag = float(self.filtered_action[0]) * 0.030
  244 |         dz_bat = float(self.filtered_action[1]) * 0.08
  245 |         dalpha_plane = float(self.filtered_action[2]) * 0.15
  246 |         dpower_dur = float(self.filtered_action[3]) * 0.02
  247 |         delbow_reach = float(self.filtered_action[4]) * 0.15
  248 |         dweight_shift = float(self.filtered_action[5]) * 0.10
  249 | 
  250 |         current_time = self.current_step * self.dt
  251 | 
  252 |         if not self.swing_triggered:
  253 |             candidate_trigger = self.nominal_t_trigger + dt_lead_lag
  254 |             if current_time >= candidate_trigger:
  255 |                 self.swing_triggered = True
  256 |                 self.locked_t_trigger = candidate_trigger
  257 |                 self.locked_swing_duration = max(0.12, self.nominal_swing_duration + dpower_dur)
  258 | 
  259 |         # Keyframe modulation
  260 |         kfs = self.base_keyframes.copy()
  261 |         kfs[3, 1] += dz_bat * 0.6
  262 |         kfs[3, 2] += dalpha_plane * 0.6
  263 |         kfs[3, 4] += delbow_reach * 0.6
  264 |         kfs[4, 1] += dz_bat * 1.0
  265 |         kfs[4, 2] += dalpha_plane * 1.0
  266 |         kfs[4, 4] += delbow_reach * 1.0
  267 |         kfs[5, 1] += dz_bat * 0.5
  268 |         kfs[5, 2] += dalpha_plane * 0.5
  269 | 
  270 |         # Dynamic leg target with weight shift
  271 |         leg_target = self.base_leg_q.copy()
  272 |         if self.swing_triggered:
  273 |             # Shift weight to front (left) leg during swing
  274 |             leg_target[2] -= dweight_shift # left hip pitch forward
  275 |             leg_target[7] += dweight_shift # right hip uncoil
  276 | 
  277 |         for _ in range(self.frame_skip):
  278 |             if not self.swing_triggered:
  279 |                 q_target = kfs[0]
  280 |             else:
  281 |                 elapsed = current_time - self.locked_t_trigger
  282 |                 prog = elapsed / self.locked_swing_duration
  283 |                 if prog < 0.20:
  284 |                     w = prog / 0.20
  285 |                     q_target = (1.0 - w) * kfs[0] + w * kfs[1]
  286 |                 elif prog < 0.45:
  287 |                     w = (prog - 0.20) / 0.25
  288 |                     q_target = (1.0 - w) * kfs[1] + w * kfs[2]
  289 |                 elif prog < 0.70:
  290 |                     w = (prog - 0.45) / 0.25
  291 |                     q_target = (1.0 - w) * kfs[2] + w * kfs[3]
  292 |                 elif prog < 0.90:
  293 |                     w = (prog - 0.70) / 0.20
  294 |                     q_target = (1.0 - w) * kfs[3] + w * kfs[4]
  295 |                 else:
  296 |                     w = min(1.0, (prog - 0.90) / 0.30)
  297 |                     q_target = (1.0 - w) * kfs[4] + w * kfs[5]
  298 | 
  299 |             # Upper body PD control
  300 |             for i in range(5):
  301 |                 q = self.data.qpos[self.swing_qpos_adrs[i]]
  302 |                 dq = self.data.qvel[self.swing_qvel_adrs[i]]
  303 |                 tau = self.swing_Kp[i] * (q_target[i] - q) - self.swing_Kd[i] * dq
  304 |                 cr = self.model.actuator_ctrlrange[self.swing_act_ids[i]]
  305 |                 self.data.ctrl[self.swing_act_ids[i]] = np.clip(tau, cr[0], cr[1])
  306 | 
  307 |             # Leg stance balance PD control
  308 |             for a in range(10):
  309 |                 jid = self.model.actuator_trnid[self.leg_act_ids[a], 0]
  310 |                 q = self.data.qpos[self.model.jnt_qposadr[jid]]
  311 |                 dq = self.data.qvel[self.model.jnt_dofadr[jid]]
  312 |                 tau = self.leg_Kp[a] * (leg_target[a] - q) - self.leg_Kd[a] * dq
  313 |                 cr = self.model.actuator_ctrlrange[self.leg_act_ids[a]]
  314 |                 self.data.ctrl[self.leg_act_ids[a]] = np.clip(tau, cr[0], cr[1])
  315 | 
  316 |             mujoco.mj_step(self.model, self.data)
  317 | 
  318 |             # Contact detection
  319 |             for c_idx in range(self.data.ncon):
  320 |                 con = self.data.contact[c_idx]
  321 |                 g1, g2 = con.geom1, con.geom2
  322 |                 if (g1 == self.bat_geom_id and g2 == self.ball_geom_id) or (g2 == self.bat_geom_id and g1 == self.ball_geom_id):
  323 |                     if not self.has_contacted:
  324 |                         self.has_contacted = True
  325 |                         self.contact_step = self.current_step
  326 |                         self.contact_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  327 |                         self.contact_sweet_pos = self.data.site_xpos[self.sweet_spot_id].copy()
  328 | 
  329 |         self.current_step += 1
  330 |         obs = self._get_obs()
  331 | 
  332 |         pelvis_pos = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3]
  333 |         pelvis_z = pelvis_pos[2]
  334 |         if pelvis_z < 0.65:
  335 |             self.has_fallen = True
  336 | 
  337 |         terminated = False
  338 |         truncated = False
  339 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  340 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  341 | 
  342 |         if self.has_contacted:
  343 |             vx, vy, vz = ball_vel
  344 |             self.exit_velocity = float(np.linalg.norm(ball_vel))
  345 |             if vy > 0.10:
  346 |                 self.is_fair_hit = True
  347 |                 self.exit_azimuth_deg = float(np.degrees(np.arctan2(vx, vy)))
  348 |                 v_horiz = np.sqrt(vx**2 + vy**2)
  349 |                 self.exit_launch_deg = float(np.degrees(np.arctan2(vz, v_horiz)))
  350 | 
  351 |         if self.has_fallen:
  352 |             terminated = True
  353 |         elif self.has_contacted and self.current_step >= self.contact_step + 8:
  354 |             terminated = True
  355 |         elif ball_pos[1] < -0.8:
  356 |             terminated = True
  357 |         elif self.current_step >= self.max_steps:
  358 |             truncated = True
  359 | 
  360 |         # Reward formulation
  361 |         reward = 0.0
  362 | 
  363 |         # 1. Bipedal Standing Balance Reward
  364 |         r_balance = 5.0 * np.exp(-15.0 * ((pelvis_z - 0.85) ** 2))
  365 |         reward += r_balance
  366 | 
  367 |         if self.has_fallen:
  368 |             reward -= 40.0
  369 | 
  370 |         info = {
  371 |             "contact": self.has_contacted,
  372 |             "fair_hit": self.is_fair_hit,
  373 |             "has_fallen": self.has_fallen,
  374 |             "pelvis_z": float(pelvis_z),
  375 |             "exit_speed_kmh": float(self.exit_velocity * 3.6),
  376 |             "azimuth_deg": float(self.exit_azimuth_deg),
  377 |         }
  378 | 
  379 |         if terminated and self.has_contacted and not self.contact_reward_given:
  380 |             self.contact_reward_given = True
  381 |             r_contact = 12.0
  382 |             sweet_offset = float(np.linalg.norm(self.contact_ball_pos - self.contact_sweet_pos))
  383 |             r_sweet = 8.0 * float(np.exp(-25.0 * sweet_offset))
  384 |             r_fair = 10.0 if self.is_fair_hit else -5.0
  385 | 
  386 |             reward += r_contact + r_sweet + r_fair
  387 | 
  388 |         reward -= 0.01 * float(np.sum(action ** 2))
  389 |         self.prev_action = action.copy()
  390 | 
  391 |         return obs, reward, terminated, truncated, info
  392 | 
  393 |     def render(self):
  394 |         if self.render_mode == "rgb_array" and self.renderer is not None:
  395 |             self.renderer.update_scene(self.data, camera="broadcast_cam")
  396 |             return self.renderer.render()
  397 |         return None
  398 | 
  399 |     def close(self):
  400 |         if self.renderer is not None:
  401 |             self.renderer.close()
````
