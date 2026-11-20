# bipedal/envs/bipedal_duel_env.py

원본: [envs/bipedal_duel_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/envs/bipedal_duel_env.py)

SHA256: `d88a2c1c69e2d32dfcee4a5def99395fc3f0bdba6ece660682e5037ba642e06e`

전체 586행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BipedalDuelEnv` | ClassDef | 25 | 586 |
| `__init__` | FunctionDef | 28 | 183 |
| `reset` | FunctionDef | 185 | 262 |
| `_get_obs` | FunctionDef | 264 | 302 |
| `step` | FunctionDef | 304 | 576 |
| `render` | FunctionDef | 578 | 582 |
| `close` | FunctionDef | 584 | 586 |

## 전체 원문

````text
    1 | """
    2 | BipedalDuelEnv: Phase 5 Full-Stadium Whole-Body Bipedal Pitcher vs Batter Closed-Loop Duel.
    3 | 
    4 | Combines:
    5 | - Live 10m Mound H1 Pitcher throwing Fastball (80-88 km/h), Slider (70-78 km/h), and Curveball (62-70 km/h)
    6 |   with aerodynamic drag & Magnus lift/drop/break.
    7 | - Full 19-DoF H1 Whole-Body Bipedal Batter on 6-DoF Floating Base Pelvis at home plate (Zero-Cheating).
    8 | - Real-time pitch perception: continuous ball tracking [x, v, t_remain], dynamic swing timing trigger,
    9 |   adaptive swing plane height / tilt / reach modulation, and athletic bipedal ZMP balance control.
   10 | """
   11 | 
   12 | import os
   13 | import sys
   14 | import numpy as np
   15 | import gymnasium as gym
   16 | from gymnasium import spaces
   17 | import mujoco
   18 | 
   19 | current_dir = os.path.dirname(os.path.abspath(__file__))
   20 | parent_dir = os.path.dirname(current_dir)
   21 | if parent_dir not in sys.path:
   22 |     sys.path.insert(0, parent_dir)
   23 | 
   24 | 
   25 | class BipedalDuelEnv(gym.Env):
   26 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}
   27 | 
   28 |     def __init__(
   29 |         self,
   30 |         xml_path=None,
   31 |         render_mode=None,
   32 |         frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz control loop)
   33 |         pitch_types=None,  # list of allowed pitch types [0, 1, 2] (0: Fastball, 1: Slider, 2: Curveball)
   34 |     ):
   35 |         super().__init__()
   36 | 
   37 |         if xml_path is None:
   38 |             xml_path = os.path.join(parent_dir, "models", "h1_bipedal_duel.xml")
   39 | 
   40 |         self.xml_path = xml_path
   41 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   42 |         self.data = mujoco.MjData(self.model)
   43 | 
   44 |         self.render_mode = render_mode
   45 |         self.frame_skip = frame_skip
   46 |         self.dt = self.model.opt.timestep * self.frame_skip  # 0.02s
   47 |         self.pitch_types = pitch_types if pitch_types is not None else [0, 1, 2]
   48 | 
   49 |         # Identify Bodies & Sites
   50 |         self.p_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "p_pelvis")
   51 |         self.b_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "b_pelvis")
   52 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   53 | 
   54 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   55 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   56 |         self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")
   57 |         self.p_hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")
   58 |         self.weld_eq_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_EQUALITY, "p_ball_weld")
   59 | 
   60 |         # Joints & Freejoints
   61 |         ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   62 |         self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
   63 |         self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]
   64 | 
   65 |         b_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "b_pelvis_joint")
   66 |         self.b_pelvis_qpos_adr = self.model.jnt_qposadr[b_pelvis_jnt_id]
   67 |         self.b_pelvis_qvel_adr = self.model.jnt_dofadr[b_pelvis_jnt_id]
   68 | 
   69 |         # Pitcher Arm Actuators [torso, rsp, rsr, rsy, relb]
   70 |         self.p_act_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
   71 |         self.p_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.p_act_names]
   72 |         self.p_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
   73 |         self.p_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
   74 | 
   75 |         # Batter Swing Actuators [torso, rsp, rsr, rsy, relb]
   76 |         self.b_swing_act_names = ["b_torso", "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"]
   77 |         self.b_swing_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_swing_act_names]
   78 |         self.b_swing_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_swing_act_ids]
   79 |         self.b_swing_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_swing_act_ids]
   80 | 
   81 |         # Batter Leg Actuators (10 motors for whole-body balance)
   82 |         self.b_leg_act_names = [
   83 |             "b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle",
   84 |             "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle",
   85 |         ]
   86 |         self.b_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_leg_act_names]
   87 |         self.b_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]
   88 |         self.b_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]
   89 | 
   90 |         # Stance & Swing Gains
   91 |         self.p_Kp = np.array([450.0, 350.0, 250.0, 150.0, 150.0], dtype=np.float32)
   92 |         self.p_Kd = np.array([35.0,  25.0,  20.0,  12.0,  12.0], dtype=np.float32)
   93 | 
   94 |         self.b_swing_Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
   95 |         self.b_swing_Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)
   96 | 
   97 |         self.b_leg_Kp = np.array([350.0, 350.0, 450.0, 500.0, 250.0, 350.0, 350.0, 450.0, 500.0, 250.0], dtype=np.float32)
   98 |         self.b_leg_Kd = np.array([30.0,  30.0,  40.0,  45.0,  20.0,  30.0,  30.0,  40.0,  45.0,  20.0], dtype=np.float32)
   99 | 
  100 |         # Pitcher keyframes
  101 |         self.p_keyframes = np.array([
  102 |             [ 0.00,  0.00, -0.40,  0.00,  1.50],
  103 |             [ 0.80,  1.20, -0.60,  0.80,  1.60],
  104 |             [ 0.20, -0.20, -0.40,  0.30,  1.00],
  105 |             [-0.50, -1.40, -0.20, -0.20,  0.20],
  106 |             [-0.90, -1.80, -0.60, -0.50,  0.70],
  107 |         ], dtype=np.float32)
  108 | 
  109 |         # Batter athletic batting keyframes
  110 |         self.b_base_keyframes = np.array([
  111 |             [-0.40, -1.00,  0.00,  0.40,  1.50],
  112 |             [-0.60, -1.15,  0.00,  0.60,  1.70],
  113 |             [-0.10, -0.70, -0.05,  0.20,  1.20],
  114 |             [ 0.50, -0.25, -0.10, -0.10,  0.70],
  115 |             [ 1.15,  0.10, -0.08, -0.40,  0.35],
  116 |             [ 1.70,  0.80,  0.00, -0.70,  1.20]
  117 |         ], dtype=np.float32)
  118 | 
  119 |         # Batter athletic nominal leg stance (Natural static equilibrium for rock-solid base)
  120 |         self.b_base_leg_q = np.array([
  121 |             0.0, 0.12, -0.18, 0.48, -0.32,  # Left leg
  122 |             0.0,-0.12, -0.18, 0.48, -0.32   # Right leg
  123 |         ], dtype=np.float32)
  124 | 
  125 |         # Aerodynamic constants
  126 |         self.rho = 1.205
  127 |         self.r_ball = 0.037
  128 |         self.m_ball = 0.145
  129 |         self.A_ball = np.pi * (self.r_ball ** 2)
  130 |         self.Cd = 0.32
  131 |         self.Cl = 0.24
  132 | 
  133 |         # Action: 6 dims for Whole-Body Batter
  134 |         # a[0]: dt_lead_lag swing timing adjustment (-0.040 to +0.040s)
  135 |         # a[1]: dz_bat plane height adjustment (-0.25 to +0.25rad)
  136 |         # a[2]: dalpha_plane attack tilt angle adjustment (-0.16 to +0.16rad)
  137 |         # a[3]: dpower_dur swing duration adjustment (-0.02 to +0.02s)
  138 |         # a[4]: delbow_reach elbow reach adjustment (-0.20 to +0.20rad)
  139 |         # a[5]: dweight_shift leg front/back load transfer (-0.10 to +0.10rad)
  140 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)
  141 | 
  142 |         # Observation: 38 dims (Full match with Phase 3 whole-body observation layout)
  143 |         self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(38,), dtype=np.float32)
  144 | 
  145 |         self.current_step = 0
  146 |         self.max_steps = 55
  147 |         self.prev_action = np.zeros(6, dtype=np.float32)
  148 |         self.filtered_action = np.zeros(6, dtype=np.float32)
  149 | 
  150 |         self.swing_triggered = False
  151 |         self.locked_t_trigger = 0.0
  152 |         self.locked_swing_duration = 0.17
  153 |         self.has_contacted = False
  154 |         self.contact_reward_given = False
  155 |         self.contact_step = -1
  156 |         self.contact_ball_pos = None
  157 |         self.contact_sweet_pos = None
  158 |         self.exit_velocity = 0.0
  159 |         self.exit_azimuth_deg = 0.0
  160 |         self.exit_launch_deg = 0.0
  161 |         self.is_fair_hit = False
  162 |         self.has_fallen = False
  163 |         self.is_strike = False
  164 | 
  165 |         self.is_released = False
  166 |         self.actual_release_step = 22
  167 |         self.pitch_type = 0
  168 |         self.pitch_name = "Fastball"
  169 |         self.pitch_speed = 22.5
  170 |         self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
  171 |         self.target_pitch_x = 0.16
  172 |         self.target_pitch_z = 0.56
  173 |         self.contact_plane_y = 0.22
  174 |         self.contact_lead_time = 0.145
  175 |         self.nominal_swing_duration = 0.17
  176 | 
  177 |         self.rel_vx = 0.0
  178 |         self.rel_vy = -22.5
  179 |         self.rel_vz = 0.0
  180 | 
  181 |         self.renderer = None
  182 |         if self.render_mode in ["rgb_array", "human"]:
  183 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  184 | 
  185 |     def reset(self, seed=None, options=None):
  186 |         super().reset(seed=seed)
  187 |         mujoco.mj_resetData(self.model, self.data)
  188 | 
  189 |         self.current_step = 0
  190 |         self.prev_action = np.zeros(6, dtype=np.float32)
  191 |         self.filtered_action = np.zeros(6, dtype=np.float32)
  192 |         self.swing_triggered = False
  193 |         self.locked_t_trigger = 0.0
  194 |         self.locked_swing_duration = 0.17
  195 |         self.has_contacted = False
  196 |         self.contact_reward_given = False
  197 |         self.contact_step = -1
  198 |         self.contact_ball_pos = None
  199 |         self.contact_sweet_pos = None
  200 |         self.exit_velocity = 0.0
  201 |         self.exit_azimuth_deg = 0.0
  202 |         self.exit_launch_deg = 0.0
  203 |         self.is_fair_hit = False
  204 |         self.has_fallen = False
  205 |         self.is_strike = False
  206 |         self.is_released = False
  207 | 
  208 |         # 1. Pitch Type & Target Configuration across Strike Zone (Aligned with Batter Sweet Spot Zone)
  209 |         self.pitch_type = int(self.np_random.choice(self.pitch_types))
  210 |         self.target_pitch_x = float(self.np_random.uniform(0.13, 0.19))
  211 |         self.target_pitch_z = float(self.np_random.uniform(0.52, 0.60))
  212 | 
  213 |         if self.pitch_type == 0:
  214 |             self.pitch_name = "Fastball"
  215 |             self.pitch_speed = float(self.np_random.uniform(22.0, 24.0))  # 79.2 - 86.4 km/h
  216 |             self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
  217 |         elif self.pitch_type == 1:
  218 |             self.pitch_name = "Slider"
  219 |             self.pitch_speed = float(self.np_random.uniform(19.5, 21.5))  # 70.2 - 77.4 km/h
  220 |             self.pitch_spin = np.array([-30.0, 0.0, 150.0], dtype=np.float32)
  221 |         else:
  222 |             self.pitch_name = "Curveball"
  223 |             self.pitch_speed = float(self.np_random.uniform(17.5, 19.5))  # 63.0 - 70.2 km/h
  224 |             self.pitch_spin = np.array([170.0, 0.0, -20.0], dtype=np.float32)
  225 | 
  226 |         dt_pitcher_rel = float(self.np_random.uniform(-0.010, 0.010))
  227 |         self.actual_release_step = int(np.clip(22 + int(dt_pitcher_rel / self.dt), 20, 24))
  228 | 
  229 |         # 2. Batter Goal Condition Vector (Pull / Center / Push)
  230 |         target_azimuth_deg = float(self.np_random.uniform(-30.0, 30.0))
  231 |         self.target_azimuth_rad = float(np.radians(target_azimuth_deg))
  232 |         target_launch_deg = float(self.np_random.uniform(14.0, 30.0))
  233 |         self.target_launch_rad = float(np.radians(target_launch_deg))
  234 |         self.target_exit_vel = float(self.np_random.uniform(12.0, 18.0))
  235 | 
  236 |         # 3. Initialize Pitcher Robot
  237 |         for i, adr in enumerate(self.p_qpos_adrs):
  238 |             self.data.qpos[adr] = self.p_keyframes[0, i]
  239 | 
  240 |         # 4. Initialize Batter Robot (Full 6-DoF Pelvis Floating Base at x = -0.75m, z = 0.92m)
  241 |         self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3] = [-0.75, 0.00, 0.92]
  242 |         self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  243 |         self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+6] = 0.0
  244 | 
  245 |         for i, adr in enumerate(self.b_leg_qpos_adrs):
  246 |             self.data.qpos[adr] = self.b_base_leg_q[i]
  247 | 
  248 |         for i, adr in enumerate(self.b_swing_qpos_adrs):
  249 |             self.data.qpos[adr] = self.b_base_keyframes[0, i]
  250 | 
  251 |         # 5. Connect ball to pitcher hand via weld
  252 |         if self.weld_eq_id >= 0:
  253 |             self.data.eq_active[self.weld_eq_id] = True
  254 | 
  255 |         mujoco.mj_forward(self.model, self.data)
  256 |         hand_pos = self.data.site_xpos[self.p_hand_site_id].copy()
  257 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
  258 |         self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  259 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+6] = 0.0
  260 |         mujoco.mj_forward(self.model, self.data)
  261 | 
  262 |         return self._get_obs(), {}
  263 | 
  264 |     def _get_obs(self):
  265 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  266 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  267 |         
  268 |         # Time remaining to contact plane (y = -0.16m)
  269 |         if self.is_released and abs(ball_vel[1]) > 1.0 and ball_pos[1] > self.contact_plane_y:
  270 |             t_remain = float((ball_pos[1] - self.contact_plane_y) / abs(ball_vel[1]))
  271 |         elif not self.is_released:
  272 |             est_vy = self.pitch_speed
  273 |             t_remain = float((9.4 - self.contact_plane_y) / est_vy + (self.actual_release_step - self.current_step) * self.dt)
  274 |         else:
  275 |             t_remain = 0.0
  276 | 
  277 |         goals = np.array([self.target_azimuth_rad, self.target_launch_rad, self.target_exit_vel], dtype=np.float32)
  278 |         swing_qpos = np.array([self.data.qpos[adr] for adr in self.b_swing_qpos_adrs], dtype=np.float32)
  279 |         swing_qvel = np.array([self.data.qvel[adr] for adr in self.b_swing_qvel_adrs], dtype=np.float32)
  280 | 
  281 |         sweet_pos = self.data.site_xpos[self.sweet_spot_id]
  282 |         sweet_v = np.zeros(6, dtype=np.float64)
  283 |         mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_SITE, self.sweet_spot_id, sweet_v, 0)
  284 |         sweet_vel = sweet_v[3:6]
  285 | 
  286 |         pelvis_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3]
  287 |         pelvis_vel = self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+3]
  288 | 
  289 |         obs = np.concatenate([
  290 |             ball_pos,                                    # 3
  291 |             ball_vel,                                    # 3
  292 |             np.array([t_remain], dtype=np.float32),      # 1
  293 |             goals,                                       # 3
  294 |             swing_qpos,                                  # 5
  295 |             swing_qvel,                                  # 5
  296 |             sweet_pos,                                   # 3
  297 |             sweet_vel,                                   # 3
  298 |             pelvis_pos,                                  # 3
  299 |             pelvis_vel,                                  # 3
  300 |             self.prev_action,                            # 6
  301 |         ])
  302 |         return obs.astype(np.float32)
  303 | 
  304 |     def step(self, action):
  305 |         action = np.clip(action, -1.0, 1.0).astype(np.float32)
  306 |         self.filtered_action = 0.6 * self.filtered_action + 0.4 * action
  307 | 
  308 |         dt_lead_lag = float(self.filtered_action[0]) * 0.040
  309 |         dz_bat = float(self.filtered_action[1]) * 0.25
  310 |         dalpha_plane = float(self.filtered_action[2]) * 0.16
  311 |         dpower_dur = float(self.filtered_action[3]) * 0.02
  312 |         delbow_reach = float(self.filtered_action[4]) * 0.20
  313 |         dweight_shift = float(self.filtered_action[5]) * 0.10
  314 | 
  315 |         current_time = self.current_step * self.dt
  316 | 
  317 |         # Dynamic Swing Trigger based on real-time pitch perception:
  318 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  319 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  320 |         
  321 |         # Real-time pitch perception: adapt nominal lead time to aerodynamic deceleration across pitch types:
  322 |         # Fastball (~23 m/s) -> 0.142s, Slider (~20.5 m/s) -> 0.146s, Curveball (~18 m/s) -> 0.150s
  323 |         if self.is_released and abs(ball_vel[1]) > 3.0:
  324 |             speed_y = abs(ball_vel[1])
  325 |             self.contact_lead_time = 0.145 + float(np.clip(21.0 - speed_y, -3.0, 3.5)) * 0.0016
  326 | 
  327 |         # Directional push-aim coupling via horizontal yaw adjustment (Torso/shoulder yaw)
  328 |         aim_norm = float(self.target_azimuth_rad / 0.5236)
  329 |         dt_aim = -0.002 * aim_norm  # minimal timing bias
  330 |         dalpha_aim = 0.04 * aim_norm
  331 |         dyaw_aim = -0.16 * aim_norm  # horizontal yaw adjustment
  332 | 
  333 |         if self.is_released and abs(ball_vel[1]) > 3.0 and ball_pos[1] > self.contact_plane_y:
  334 |             t_remain = (ball_pos[1] - self.contact_plane_y) / abs(ball_vel[1])
  335 |             trigger_lead = self.contact_lead_time + dt_lead_lag + dt_aim
  336 |             if not self.swing_triggered and t_remain <= trigger_lead:
  337 |                 self.swing_triggered = True
  338 |                 self.locked_t_trigger = current_time
  339 |                 self.locked_swing_duration = max(0.13, self.nominal_swing_duration + dpower_dur)
  340 | 
  341 |         # Modulate Batter Keyframes with Directional Aim Yaw Coupling
  342 |         b_kfs = self.b_base_keyframes.copy()
  343 |         b_kfs[3, 0] += dyaw_aim * 0.6
  344 |         b_kfs[3, 1] += dz_bat * 0.6
  345 |         b_kfs[3, 2] += (dalpha_plane + dalpha_aim) * 0.6
  346 |         b_kfs[3, 4] += delbow_reach * 0.6
  347 |         b_kfs[4, 0] += dyaw_aim * 1.0
  348 |         b_kfs[4, 1] += dz_bat * 1.0
  349 |         b_kfs[4, 2] += (dalpha_plane + dalpha_aim) * 1.0
  350 |         b_kfs[4, 4] += delbow_reach * 1.0
  351 |         b_kfs[5, 1] += dz_bat * 0.5
  352 |         b_kfs[5, 2] += (dalpha_plane + dalpha_aim) * 0.5
  353 | 
  354 |         # Dynamic Leg Target with Athletic Weight Shift
  355 |         b_leg_target = self.b_base_leg_q.copy()
  356 |         if self.swing_triggered:
  357 |             b_leg_target[2] -= dweight_shift # left hip brace forward
  358 |             b_leg_target[7] += dweight_shift # right hip drive
  359 | 
  360 |         # Substep Physics (frame_skip = 10 substeps of 0.002s = 0.02s per env step)
  361 |         for s_idx in range(self.frame_skip):
  362 |             sim_time = current_time + s_idx * self.model.opt.timestep
  363 | 
  364 |             # 1. Pitcher Arm Kinematics & PD Control
  365 |             t_norm = (self.current_step + s_idx / self.frame_skip) / self.actual_release_step
  366 |             if t_norm < 0.35:
  367 |                 w = t_norm / 0.35
  368 |                 p_target = (1.0 - w) * self.p_keyframes[0] + w * self.p_keyframes[1]
  369 |             elif t_norm < 0.70:
  370 |                 w = (t_norm - 0.35) / 0.35
  371 |                 p_target = (1.0 - w) * self.p_keyframes[1] + w * self.p_keyframes[2]
  372 |             elif t_norm <= 1.0:
  373 |                 w = (t_norm - 0.70) / 0.30
  374 |                 p_target = (1.0 - w) * self.p_keyframes[2] + w * self.p_keyframes[3]
  375 |             else:
  376 |                 w = min(1.0, (t_norm - 1.0) / 0.40)
  377 |                 p_target = (1.0 - w) * self.p_keyframes[3] + w * self.p_keyframes[4]
  378 | 
  379 |             for i in range(5):
  380 |                 qp = self.data.qpos[self.p_qpos_adrs[i]]
  381 |                 dqp = self.data.qvel[self.p_qvel_adrs[i]]
  382 |                 tau_p = self.p_Kp[i] * (p_target[i] - qp) - self.p_Kd[i] * dqp
  383 |                 cr_p = self.model.actuator_ctrlrange[self.p_act_ids[i]]
  384 |                 self.data.ctrl[self.p_act_ids[i]] = np.clip(tau_p, cr_p[0], cr_p[1])
  385 | 
  386 |             # 2. Batter Arm Kinematics & PD Control
  387 |             if not self.swing_triggered:
  388 |                 b_target = b_kfs[0]
  389 |             else:
  390 |                 elapsed = sim_time - self.locked_t_trigger
  391 |                 prog = elapsed / self.locked_swing_duration
  392 |                 if prog < 0.20:
  393 |                     w = prog / 0.20
  394 |                     b_target = (1.0 - w) * b_kfs[0] + w * b_kfs[1]
  395 |                 elif prog < 0.45:
  396 |                     w = (prog - 0.20) / 0.25
  397 |                     b_target = (1.0 - w) * b_kfs[1] + w * b_kfs[2]
  398 |                 elif prog < 0.70:
  399 |                     w = (prog - 0.45) / 0.25
  400 |                     b_target = (1.0 - w) * b_kfs[2] + w * b_kfs[3]
  401 |                 elif prog < 0.90:
  402 |                     w = (prog - 0.70) / 0.20
  403 |                     b_target = (1.0 - w) * b_kfs[3] + w * b_kfs[4]
  404 |                 else:
  405 |                     w = min(1.0, (prog - 0.90) / 0.30)
  406 |                     b_target = (1.0 - w) * b_kfs[4] + w * b_kfs[5]
  407 | 
  408 |             for i in range(5):
  409 |                 qb = self.data.qpos[self.b_swing_qpos_adrs[i]]
  410 |                 dqb = self.data.qvel[self.b_swing_qvel_adrs[i]]
  411 |                 tau_b = self.b_swing_Kp[i] * (b_target[i] - qb) - self.b_swing_Kd[i] * dqb
  412 |                 cr_b = self.model.actuator_ctrlrange[self.b_swing_act_ids[i]]
  413 |                 self.data.ctrl[self.b_swing_act_ids[i]] = np.clip(tau_b, cr_b[0], cr_b[1])
  414 | 
  415 |             # 3. Batter Leg Stance Balance PD Control with Active Ground Shear Counter-Torque
  416 |             p_x = self.data.qpos[self.b_pelvis_qpos_adr]
  417 |             v_x = self.data.qvel[self.b_pelvis_qvel_adr]
  418 |             w_z = self.data.qvel[self.b_pelvis_qvel_adr + 5]
  419 | 
  420 |             tau_x_ank = np.clip(500.0 * (p_x - (-0.75)) + 50.0 * v_x, -35.0, 35.0)
  421 |             tau_x_hip = np.clip(400.0 * (p_x - (-0.75)) + 40.0 * v_x, -50.0, 50.0)
  422 |             tau_yaw = np.clip(80.0 * w_z, -50.0, 50.0)
  423 | 
  424 |             for a in range(10):
  425 |                 jid = self.model.actuator_trnid[self.b_leg_act_ids[a], 0]
  426 |                 ql = self.data.qpos[self.model.jnt_qposadr[jid]]
  427 |                 dql = self.data.qvel[self.model.jnt_dofadr[jid]]
  428 |                 tau_l = self.b_leg_Kp[a] * (b_leg_target[a] - ql) - self.b_leg_Kd[a] * dql
  429 |                 if a in [4, 9]:
  430 |                     tau_l += tau_x_ank
  431 |                 elif a in [2, 7]:
  432 |                     tau_l += tau_x_hip
  433 |                 elif a in [0, 5]:
  434 |                     tau_l += tau_yaw
  435 |                 cr_l = self.model.actuator_ctrlrange[self.b_leg_act_ids[a]]
  436 |                 self.data.ctrl[self.b_leg_act_ids[a]] = np.clip(tau_l, cr_l[0], cr_l[1])
  437 | 
  438 |             # 4. Ball Release Check: Solve aerodynamic release from actual hand pos at release moment
  439 |             if not self.is_released and self.current_step >= self.actual_release_step:
  440 |                 self.is_released = True
  441 |                 if self.weld_eq_id >= 0:
  442 |                     self.data.eq_active[self.weld_eq_id] = False
  443 | 
  444 |                 hp_now = self.data.site_xpos[self.p_hand_site_id].copy()
  445 |                 target_pt = np.array([self.target_pitch_x, self.contact_plane_y, self.target_pitch_z], dtype=np.float32)
  446 |                 tf = (hp_now[1] - target_pt[1]) / self.pitch_speed
  447 |                 vx_rel = (target_pt[0] - hp_now[0]) / tf
  448 |                 vz_rel = (target_pt[2] + 0.5 * 9.81 * (tf**2) - hp_now[2]) / tf
  449 | 
  450 |                 # Aerodynamic Shooting Loop
  451 |                 for _ in range(3):
  452 |                     p_s = hp_now.copy()
  453 |                     v_s = np.array([vx_rel, -self.pitch_speed, vz_rel], dtype=np.float32)
  454 |                     while p_s[1] > target_pt[1]:
  455 |                         vm = np.linalg.norm(v_s)
  456 |                         fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_s
  457 |                         fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_s)
  458 |                         acc = (fd + fm) / self.m_ball + np.array([0, 0, -9.81], dtype=np.float32)
  459 |                         v_s += acc * 0.002
  460 |                         p_s += v_s * 0.002
  461 |                     err = p_s - target_pt
  462 |                     vx_rel -= err[0] / tf
  463 |                     vz_rel -= err[2] / tf
  464 | 
  465 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx_rel, -self.pitch_speed, vz_rel]
  466 | 
  467 |             # 5. Aerodynamic Drag & Magnus Force on Baseball
  468 |             if self.is_released and not self.has_contacted:
  469 |                 v = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  470 |                 v_norm = np.linalg.norm(v)
  471 |                 if v_norm > 1.0:
  472 |                     f_drag = -0.5 * self.rho * self.Cd * self.A_ball * v_norm * v
  473 |                     f_magnus = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v)
  474 |                     self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += (f_drag + f_magnus) / self.m_ball * self.model.opt.timestep
  475 | 
  476 |             # MuJoCo Physics Step
  477 |             mujoco.mj_step(self.model, self.data)
  478 | 
  479 |             # 6. Contact Detection (Bat Barrel vs Baseball)
  480 |             for c_idx in range(self.data.ncon):
  481 |                 con = self.data.contact[c_idx]
  482 |                 g1, g2 = con.geom1, con.geom2
  483 |                 if (g1 == self.bat_geom_id and g2 == self.ball_geom_id) or (g2 == self.bat_geom_id and g1 == self.ball_geom_id):
  484 |                     if not self.has_contacted:
  485 |                         self.has_contacted = True
  486 |                         self.contact_step = self.current_step
  487 |                         self.contact_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  488 |                         self.contact_sweet_pos = self.data.site_xpos[self.sweet_spot_id].copy()
  489 | 
  490 |         self.current_step += 1
  491 |         obs = self._get_obs()
  492 | 
  493 |         # Check Strike Zone at Plate / Front Zone (y <= 0.25m)
  494 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  495 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  496 |         if ball_pos[1] <= 0.25:
  497 |             if abs(ball_pos[0]) <= 0.216 and 0.45 <= ball_pos[2] <= 0.85:
  498 |                 self.is_strike = True
  499 | 
  500 |         # Pelvis Balance & Fall Detection
  501 |         pelvis_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3]
  502 |         pelvis_x = pelvis_pos[0]
  503 |         pelvis_z = pelvis_pos[2]
  504 |         if pelvis_z < 0.65:
  505 |             self.has_fallen = True
  506 | 
  507 |         terminated = False
  508 |         truncated = False
  509 | 
  510 |         if self.has_contacted:
  511 |             vx, vy, vz = ball_vel
  512 |             self.exit_velocity = float(np.linalg.norm(ball_vel))
  513 |             if vy > 0.10:
  514 |                 self.is_fair_hit = True
  515 |                 self.exit_azimuth_deg = float(np.degrees(np.arctan2(vx, vy)))
  516 |                 v_horiz = np.sqrt(vx**2 + vy**2)
  517 |                 self.exit_launch_deg = float(np.degrees(np.arctan2(vz, v_horiz)))
  518 | 
  519 |         if self.has_fallen:
  520 |             terminated = True
  521 |         elif self.has_contacted and self.current_step >= self.contact_step + 8:
  522 |             terminated = True
  523 |         elif ball_pos[1] < -1.0:
  524 |             terminated = True
  525 |         elif self.current_step >= self.max_steps:
  526 |             truncated = True
  527 | 
  528 |         # Reward Formulation
  529 |         reward = 0.0
  530 | 
  531 |         # 1. Bipedal Standing Balance & Pelvis Position Reward
  532 |         r_balance = 5.0 * np.exp(-15.0 * ((pelvis_z - 0.92) ** 2))
  533 |         r_pelvis_x = 3.0 * np.exp(-30.0 * ((pelvis_x - (-0.75)) ** 2))
  534 |         reward += r_balance + r_pelvis_x
  535 | 
  536 |         if self.has_fallen:
  537 |             reward -= 50.0
  538 | 
  539 |         sweet_err_cm = float(np.linalg.norm(self.contact_ball_pos - self.contact_sweet_pos) * 100.0) if (self.has_contacted and self.contact_ball_pos is not None) else 0.0
  540 | 
  541 |         info = {
  542 |             "contact": self.has_contacted,
  543 |             "fair_hit": self.is_fair_hit,
  544 |             "has_fallen": self.has_fallen,
  545 |             "pelvis_z": float(pelvis_z),
  546 |             "pelvis_x": float(pelvis_x),
  547 |             "exit_speed_kmh": float(self.exit_velocity * 3.6),
  548 |             "azimuth_deg": float(self.exit_azimuth_deg),
  549 |             "pitch_name": self.pitch_name,
  550 |             "pitch_speed_kmh": float(self.pitch_speed * 3.6),
  551 |             "sweet_offset_cm": sweet_err_cm,
  552 |             "is_strike": self.is_strike,
  553 |         }
  554 | 
  555 |         # 2. Contact, Sweet Spot, and Fair Hit Rewards
  556 |         if terminated and self.has_contacted and not self.contact_reward_given:
  557 |             self.contact_reward_given = True
  558 |             r_contact = 20.0
  559 |             sweet_offset = float(np.linalg.norm(self.contact_ball_pos - self.contact_sweet_pos))
  560 |             effective_err = max(0.0, sweet_offset - 0.062)
  561 |             r_sweet = 35.0 * float(np.exp(-45.0 * effective_err))
  562 |             r_fair = 25.0 if self.is_fair_hit else -5.0
  563 | 
  564 |             # Directional aim reward
  565 |             az_err = abs(np.radians(self.exit_azimuth_deg) - self.target_azimuth_rad)
  566 |             r_aim = 10.0 * float(np.exp(-8.0 * (az_err ** 2)))
  567 | 
  568 |             # Exit speed bonus
  569 |             r_speed = 0.40 * float(self.exit_velocity)
  570 | 
  571 |             reward += r_contact + r_sweet + r_fair + r_aim + r_speed
  572 | 
  573 |         reward -= 0.01 * float(np.sum(action ** 2))
  574 |         self.prev_action = action.copy()
  575 | 
  576 |         return obs, reward, terminated, truncated, info
  577 | 
  578 |     def render(self, camera_name="duel_broadcast_cam"):
  579 |         if self.render_mode == "rgb_array" and self.renderer is not None:
  580 |             self.renderer.update_scene(self.data, camera=camera_name)
  581 |             return self.renderer.render()
  582 |         return None
  583 | 
  584 |     def close(self):
  585 |         if self.renderer is not None:
  586 |             self.renderer.close()
````
