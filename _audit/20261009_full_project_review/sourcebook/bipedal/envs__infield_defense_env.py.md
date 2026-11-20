# bipedal/envs/infield_defense_env.py

원본: [envs/infield_defense_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/envs/infield_defense_env.py)

SHA256: `3e6a7c1a420e423f4384d59207446af21d48e7328f7aba9853532a7394106c35`

전체 928행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `InfieldDefenseEnv` | ClassDef | 30 | 928 |
| `__init__` | FunctionDef | 33 | 249 |
| `reset` | FunctionDef | 251 | 367 |
| `_get_obs` | FunctionDef | 369 | 430 |
| `step` | FunctionDef | 432 | 918 |
| `render` | FunctionDef | 920 | 924 |
| `close` | FunctionDef | 926 | 928 |

## 전체 원문

````text
    1 | """
    2 | InfieldDefenseEnv: Phase 7 Full Infield Bipedal Defense & 1st Base Out/Safe Play.
    3 | 
    4 | Combines:
    5 | 1. 10m Mound Unitree H1 Pitcher throwing Fastball / Slider / Curveball with Magnus effect.
    6 | 2. 6-DoF Floating-Base Unitree H1 Batter-Runner at Home Plate (-0.75m, 0.0m) with:
    7 |    - Athletic kinetic uncoiling swing into fair infield
    8 |    - Dynamic prop handover (bat dropped cleanly onto turf at t = 0.52s)
    9 |    - Multi-step cyclic bipedal sprint toward 1st Base Pad (6.5m, 6.5m)
   10 | 3. 6-DoF Floating-Base Unitree H1 1st Baseman Infielder in 1st base infield (5.0m, 5.0m) with:
   11 |    - Fielding glove (r = 0.12m) on left hand
   12 |    - Dynamic bipedal footwork, ball trajectory intercept, and 1st base covering
   13 | 4. Realistic field turf restitution (e = 0.52), friction (mu = 0.4), and rolling resistance (crr = 0.02).
   14 | 5. 3D Umpire Decision Engine measuring T_runner vs T_defense -> OUT vs SAFE.
   15 | """
   16 | 
   17 | import os
   18 | import sys
   19 | import numpy as np
   20 | import gymnasium as gym
   21 | from gymnasium import spaces
   22 | import mujoco
   23 | 
   24 | current_dir = os.path.dirname(os.path.abspath(__file__))
   25 | parent_dir = os.path.dirname(current_dir)
   26 | if parent_dir not in sys.path:
   27 |     sys.path.insert(0, parent_dir)
   28 | 
   29 | 
   30 | class InfieldDefenseEnv(gym.Env):
   31 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}
   32 | 
   33 |     def __init__(
   34 |         self,
   35 |         xml_path=None,
   36 |         render_mode=None,
   37 |         frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz control)
   38 |         pitch_types=None,  # 0: Fastball, 1: Slider, 2: Curveball
   39 |     ):
   40 |         super().__init__()
   41 | 
   42 |         if xml_path is None:
   43 |             xml_path = os.path.join(parent_dir, "models", "h1_infield_defense.xml")
   44 | 
   45 |         self.xml_path = xml_path
   46 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   47 |         self.data = mujoco.MjData(self.model)
   48 | 
   49 |         self.render_mode = render_mode
   50 |         self.frame_skip = frame_skip
   51 |         self.dt = self.model.opt.timestep * self.frame_skip  # 0.02s
   52 |         self.pitch_types = pitch_types if pitch_types is not None else [0, 1, 2]
   53 | 
   54 |         # Geometry & Spatial Anchors
   55 |         self.target_1b = np.array([6.5, 6.5], dtype=np.float32)
   56 |         self.start_p0 = np.array([-0.75, 0.0], dtype=np.float32)
   57 |         vec_1b = self.target_1b - self.start_p0
   58 |         self.nominal_dist_1b = float(np.linalg.norm(vec_1b))  # ~9.74m
   59 |         self.u_1b = (vec_1b / self.nominal_dist_1b).astype(np.float32)
   60 |         self.yaw_1b = float(np.arctan2(self.u_1b[1], self.u_1b[0]))  # ~41.88 deg (0.731 rad)
   61 | 
   62 |         self.infielder_p0 = np.array([5.0, 5.0], dtype=np.float32)
   63 |         self.f_yaw0 = -2.356194
   64 |         self.f_u_sag = np.array([np.cos(self.f_yaw0), np.sin(self.f_yaw0)], dtype=np.float32)
   65 |         self.f_u_lat = np.array([-np.sin(self.f_yaw0), np.cos(self.f_yaw0)], dtype=np.float32)
   66 | 
   67 |         # Bodies
   68 |         self.p_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "p_pelvis")
   69 |         self.b_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "b_pelvis")
   70 |         self.f_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "f_pelvis")
   71 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   72 |         self.b_held_bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "b_held_bat")
   73 |         self.dropped_bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "dropped_bat")
   74 | 
   75 |         # Geoms & Sites
   76 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   77 |         self.b_held_bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "b_held_bat_barrel")
   78 |         self.f_glove_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "f_glove")
   79 |         self.first_base_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "first_base")
   80 | 
   81 |         self.b_sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "b_bat_sweet_spot")
   82 |         self.f_glove_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "f_glove_site")
   83 |         self.p_hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")
   84 |         self.weld_eq_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_EQUALITY, "p_ball_weld")
   85 | 
   86 |         # Freejoints
   87 |         ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   88 |         self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
   89 |         self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]
   90 | 
   91 |         b_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "b_pelvis_joint")
   92 |         self.b_pelvis_qpos_adr = self.model.jnt_qposadr[b_pelvis_jnt_id]
   93 |         self.b_pelvis_qvel_adr = self.model.jnt_dofadr[b_pelvis_jnt_id]
   94 | 
   95 |         f_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "f_pelvis_joint")
   96 |         self.f_pelvis_qpos_adr = self.model.jnt_qposadr[f_pelvis_jnt_id]
   97 |         self.f_pelvis_qvel_adr = self.model.jnt_dofadr[f_pelvis_jnt_id]
   98 | 
   99 |         drop_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "dropped_bat_joint")
  100 |         self.drop_qpos_adr = self.model.jnt_qposadr[drop_jnt_id]
  101 |         self.drop_qvel_adr = self.model.jnt_dofadr[drop_jnt_id]
  102 | 
  103 |         # Pitcher Arm Actuators
  104 |         self.p_act_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
  105 |         self.p_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.p_act_names]
  106 |         self.p_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
  107 |         self.p_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
  108 | 
  109 |         # Batter Swing & Leg Actuators
  110 |         self.b_swing_act_names = ["b_torso", "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"]
  111 |         self.b_swing_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_swing_act_names]
  112 |         self.b_swing_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_swing_act_ids]
  113 |         self.b_swing_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_swing_act_ids]
  114 | 
  115 |         self.b_leg_act_names = [
  116 |             "b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle",
  117 |             "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle",
  118 |         ]
  119 |         self.b_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_leg_act_names]
  120 |         self.b_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]
  121 |         self.b_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]
  122 | 
  123 |         # Infielder Actuators
  124 |         self.f_arm_act_names = ["f_torso", "f_left_shoulder_pitch", "f_left_shoulder_roll", "f_left_shoulder_yaw", "f_left_elbow"]
  125 |         self.f_arm_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.f_arm_act_names]
  126 |         self.f_arm_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.f_arm_act_ids]
  127 |         self.f_arm_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.f_arm_act_ids]
  128 | 
  129 |         self.f_leg_act_names = [
  130 |             "f_left_hip_yaw", "f_left_hip_roll", "f_left_hip_pitch", "f_left_knee", "f_left_ankle",
  131 |             "f_right_hip_yaw", "f_right_hip_roll", "f_right_hip_pitch", "f_right_knee", "f_right_ankle",
  132 |         ]
  133 |         self.f_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.f_leg_act_names]
  134 |         self.f_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.f_leg_act_ids]
  135 |         self.f_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.f_leg_act_ids]
  136 | 
  137 |         # PD Control Gains
  138 |         self.p_Kp = np.array([450.0, 350.0, 250.0, 150.0, 150.0], dtype=np.float32)
  139 |         self.p_Kd = np.array([35.0,  25.0,  20.0,  12.0,  12.0], dtype=np.float32)
  140 | 
  141 |         self.b_swing_Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
  142 |         self.b_swing_Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)
  143 | 
  144 |         self.b_leg_Kp = np.array([450.0, 450.0, 650.0, 750.0, 350.0, 450.0, 450.0, 650.0, 750.0, 350.0], dtype=np.float32)
  145 |         self.b_leg_Kd = np.array([35.0,  40.0,  55.0,  65.0,  28.0,  35.0,  40.0,  55.0,  65.0,  28.0], dtype=np.float32)
  146 | 
  147 |         self.f_arm_Kp = np.array([400.0, 250.0, 200.0, 150.0, 150.0], dtype=np.float32)
  148 |         self.f_arm_Kd = np.array([30.0,  20.0,  18.0,  12.0,  12.0], dtype=np.float32)
  149 | 
  150 |         self.f_leg_Kp = np.array([450.0, 450.0, 650.0, 750.0, 350.0, 450.0, 450.0, 650.0, 750.0, 350.0], dtype=np.float32)
  151 |         self.f_leg_Kd = np.array([35.0,  40.0,  55.0,  65.0,  28.0,  35.0,  40.0,  55.0,  65.0,  28.0], dtype=np.float32)
  152 | 
  153 |         # Keyframe postures
  154 |         self.p_keyframes = np.array([
  155 |             [ 0.20, -0.20, -0.40,  0.30,  1.00],
  156 |             [-0.50, -1.40, -0.20, -0.20,  0.20],
  157 |             [-0.90, -1.80, -0.60, -0.50,  0.70],
  158 |         ], dtype=np.float32)
  159 | 
  160 |         self.b_base_keyframes = np.array([
  161 |             [-0.40, -1.00,  0.00,  0.40,  1.50],
  162 |             [-0.60, -1.15,  0.00,  0.60,  1.70],
  163 |             [-0.10, -0.70, -0.05,  0.20,  1.20],
  164 |             [ 0.50, -0.30, -0.10, -0.10,  0.70],
  165 |             [ 1.15,  0.20, -0.08, -0.40,  0.35],
  166 |             [ 1.70,  0.80,  0.00, -0.70,  1.20]
  167 |         ], dtype=np.float32)
  168 | 
  169 |         self.base_leg_q = np.array([
  170 |             0.0,  0.10, -0.18, 0.48, -0.32,  # Left leg
  171 |             0.0, -0.10, -0.18, 0.48, -0.32   # Right leg
  172 |         ], dtype=np.float32)
  173 | 
  174 |         self.crouch_leg_q = np.array([
  175 |             0.0,  0.10, -0.30, 0.65, -0.35,  # Athletic crouching stance
  176 |             0.0, -0.10, -0.30, 0.65, -0.35
  177 |         ], dtype=np.float32)
  178 | 
  179 |         # Aerodynamic constants
  180 |         self.rho = 1.205
  181 |         self.r_ball = 0.037
  182 |         self.m_ball = 0.145
  183 |         self.A_ball = np.pi * (self.r_ball ** 2)
  184 |         self.Cd = 0.32
  185 |         self.Cl = 0.24
  186 | 
  187 |         # Action Space (8 dims):
  188 |         # a[0]: dt_trigger timing lead/lag (-0.03 to +0.03s)
  189 |         # a[1]: dz_bat plane height (-0.20 to +0.20rad)
  190 |         # a[2]: dalpha_plane attack tilt (-0.15 to +0.15rad)
  191 |         # a[3]: stride_freq runner modulation (1.6 to 2.2 Hz)
  192 |         # a[4]: sprint_push_gain (0.8 to 1.4)
  193 |         # a[5]: sprint_steer_yaw (-0.20 to +0.20rad)
  194 |         # a[6]: fielder_lateral_shift (-0.35 to +0.35m)
  195 |         # a[7]: fielder_glove_elevation (-0.20 to +0.20m)
  196 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(8,), dtype=np.float32)
  197 | 
  198 |         # Observation Space (74 dims)
  199 |         self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(74,), dtype=np.float32)
  200 | 
  201 |         self.current_step = 0
  202 |         self.max_steps = 100  # 100 * 0.02s = 2.00s (complete play window)
  203 |         self.filtered_action = np.zeros(8, dtype=np.float32)
  204 | 
  205 |         # Play State Variables
  206 |         self.is_released = False
  207 |         self.actual_release_step = 4
  208 |         self.pitch_type = 0
  209 |         self.pitch_name = "Fastball"
  210 |         self.pitch_speed = 23.5
  211 |         self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
  212 | 
  213 |         self.swing_triggered = False
  214 |         self.locked_t_trigger = 0.0
  215 |         self.locked_swing_duration = 0.17
  216 |         self.has_contacted = False
  217 |         self.bat_released = False
  218 |         self.contact_step = -1
  219 |         self.release_step = -1
  220 |         self.exit_velocity = 0.0
  221 |         self.exit_azimuth_deg = 0.0
  222 |         self.exit_launch_deg = 0.0
  223 |         self.is_fair_hit = False
  224 |         self.is_strike = True
  225 | 
  226 |         self.batter_fallen = False
  227 |         self.fielder_fallen = False
  228 |         self.sweet_spot_offset = 0.0
  229 | 
  230 |         # Fielding and Umpire Decision
  231 |         self.ball_fielded = False
  232 |         self.field_step = -1
  233 |         self.t_fielded = 999.0
  234 | 
  235 |         self.defense_completed = False
  236 |         self.defense_step = -1
  237 |         self.t_defense = 999.0
  238 | 
  239 |         self.runner_reached_1b = False
  240 |         self.runner_step = -1
  241 |         self.t_runner = 999.0
  242 | 
  243 |         self.umpire_decision = "PENDING"
  244 |         self.prev_runner_dist_1b = self.nominal_dist_1b
  245 |         self.runner_max_spd = 0.0
  246 | 
  247 |         self.renderer = None
  248 |         if self.render_mode in ["rgb_array", "human"]:
  249 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  250 | 
  251 |     def reset(self, seed=None, options=None):
  252 |         super().reset(seed=seed)
  253 |         mujoco.mj_resetData(self.model, self.data)
  254 | 
  255 |         self.current_step = 0
  256 |         self.filtered_action = np.zeros(8, dtype=np.float32)
  257 | 
  258 |         self.is_released = False
  259 |         self.swing_triggered = False
  260 |         self.locked_t_trigger = 0.0
  261 |         self.locked_swing_duration = 0.17
  262 |         self.has_contacted = False
  263 |         self.bat_released = False
  264 |         self.contact_step = -1
  265 |         self.release_step = -1
  266 |         self.exit_velocity = 0.0
  267 |         self.exit_azimuth_deg = 0.0
  268 |         self.exit_launch_deg = 0.0
  269 |         self.is_fair_hit = False
  270 |         self.is_strike = True
  271 | 
  272 |         self.batter_fallen = False
  273 |         self.fielder_fallen = False
  274 |         self.sweet_spot_offset = 0.0
  275 | 
  276 |         self.ball_fielded = False
  277 |         self.field_step = -1
  278 |         self.t_fielded = 999.0
  279 | 
  280 |         self.defense_completed = False
  281 |         self.defense_step = -1
  282 |         self.t_defense = 999.0
  283 | 
  284 |         self.runner_reached_1b = False
  285 |         self.runner_step = -1
  286 |         self.t_runner = 999.0
  287 | 
  288 |         self.umpire_decision = "PENDING"
  289 |         self.runner_max_spd = 0.0
  290 | 
  291 |         # Restore held bat visibility and ball collision
  292 |         self.model.geom_size[self.b_held_bat_geom_id] = [0.032, 0.45, 0.0]
  293 |         self.model.geom_rgba[self.b_held_bat_geom_id, 3] = 1.0
  294 |         self.model.geom_contype[self.ball_geom_id] = 1
  295 |         self.model.geom_conaffinity[self.ball_geom_id] = 1
  296 | 
  297 |         # Reset dropped bat in sky (z=50m)
  298 |         self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = [0.0, 0.0, 50.0]
  299 |         self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+6] = 0.0
  300 | 
  301 |         # 1. Pitcher Robot (mound at 0, 10.0, 0.82)
  302 |         for i, adr in enumerate(self.p_qpos_adrs):
  303 |             self.data.qpos[adr] = self.p_keyframes[0, i]
  304 | 
  305 |         # 2. Batter-Runner (floating base at -0.75, 0.0, 0.92)
  306 |         self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3] = [-0.75, 0.00, 0.92]
  307 |         self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  308 |         self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+6] = 0.0
  309 | 
  310 |         for i, adr in enumerate(self.b_leg_qpos_adrs):
  311 |             self.data.qpos[adr] = self.base_leg_q[i]
  312 | 
  313 |         for i, adr in enumerate(self.b_swing_qpos_adrs):
  314 |             self.data.qpos[adr] = self.b_base_keyframes[0, i]
  315 | 
  316 |         # 3. 1st Baseman Infielder (floating base at 5.0, 5.0, 0.92 facing home plate -135 deg)
  317 |         self.data.qpos[self.f_pelvis_qpos_adr:self.f_pelvis_qpos_adr+3] = [5.0, 5.0, 0.92]
  318 |         self.data.qpos[self.f_pelvis_qpos_adr+3:self.f_pelvis_qpos_adr+7] = [0.3826834, 0.0, 0.0, -0.9238795]
  319 |         self.data.qvel[self.f_pelvis_qvel_adr:self.f_pelvis_qvel_adr+6] = 0.0
  320 | 
  321 |         for i, adr in enumerate(self.f_leg_qpos_adrs):
  322 |             self.data.qpos[adr] = self.base_leg_q[i]
  323 | 
  324 |         # Infielder ready arm posture (glove forward ready)
  325 |         f_arm_init = np.array([0.0, 0.40, 0.20, 0.0, 1.30], dtype=np.float32)
  326 |         for i, adr in enumerate(self.f_arm_qpos_adrs):
  327 |             self.data.qpos[adr] = f_arm_init[i]
  328 | 
  329 |         # 4. Synchronized Pitch Selection (Releases calibrated for arrival at t in [0.44s, 0.47s])
  330 |         self.pitch_type = int(self.np_random.choice(self.pitch_types))
  331 |         self.target_pitch_x = float(self.np_random.uniform(0.14, 0.18))
  332 |         self.target_pitch_z = float(self.np_random.uniform(0.53, 0.58))
  333 | 
  334 |         if self.pitch_type == 0:
  335 |             self.pitch_name = "Fastball"
  336 |             self.pitch_speed = float(self.np_random.uniform(23.8, 24.8))  # 85-89 km/h
  337 |             self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
  338 |             self.actual_release_step = 3  # t = 0.06s -> arrives at 0.464s
  339 |         elif self.pitch_type == 1:
  340 |             self.pitch_name = "Slider"
  341 |             self.pitch_speed = float(self.np_random.uniform(21.2, 22.2))  # 76-80 km/h
  342 |             self.pitch_spin = np.array([-30.0, 0.0, 150.0], dtype=np.float32)
  343 |             self.actual_release_step = 1  # t = 0.02s -> arrives at 0.468s
  344 |         else:
  345 |             self.pitch_name = "Curveball"
  346 |             self.pitch_speed = float(self.np_random.uniform(20.5, 21.5))  # 74-77 km/h
  347 |             self.pitch_spin = np.array([170.0, 0.0, -20.0], dtype=np.float32)
  348 |             self.actual_release_step = 0  # t = 0.00s -> arrives at 0.461s
  349 | 
  350 |         # Ball in pitcher hand initially
  351 |         if self.weld_eq_id >= 0:
  352 |             self.data.eq_active[self.weld_eq_id] = True
  353 | 
  354 |         mujoco.mj_forward(self.model, self.data)
  355 |         hand_pos = self.data.site_xpos[self.p_hand_site_id].copy()
  356 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
  357 |         self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  358 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+6] = 0.0
  359 |         mujoco.mj_forward(self.model, self.data)
  360 | 
  361 |         self.contact_plane_y = 0.22
  362 |         self.contact_lead_time = 0.170
  363 | 
  364 |         b_pelvis_xy = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+2]
  365 |         self.prev_runner_dist_1b = float(np.linalg.norm(self.target_1b - b_pelvis_xy))
  366 | 
  367 |         return self._get_obs(), {}
  368 | 
  369 |     def _get_obs(self):
  370 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  371 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  372 | 
  373 |         if self.is_released and abs(ball_vel[1]) > 1.0 and ball_pos[1] > self.contact_plane_y:
  374 |             t_remain = float((ball_pos[1] - self.contact_plane_y) / abs(ball_vel[1]))
  375 |         elif not self.is_released:
  376 |             t_remain = float((9.5 - self.contact_plane_y) / self.pitch_speed)
  377 |         else:
  378 |             t_remain = 0.0
  379 | 
  380 |         # Batter state
  381 |         b_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3]
  382 |         b_vel = self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+3]
  383 |         b_quat = self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7]
  384 |         b_angvel = self.data.qvel[self.b_pelvis_qvel_adr+3:self.b_pelvis_qvel_adr+6]
  385 | 
  386 |         b_rel_1b = self.target_1b - b_pos[:2]
  387 |         b_dist_1b = float(np.linalg.norm(b_rel_1b))
  388 | 
  389 |         # Infielder state
  390 |         f_pos = self.data.qpos[self.f_pelvis_qpos_adr:self.f_pelvis_qpos_adr+3]
  391 |         f_vel = self.data.qvel[self.f_pelvis_qvel_adr:self.f_pelvis_qvel_adr+3]
  392 |         f_quat = self.data.qpos[self.f_pelvis_qpos_adr+3:self.f_pelvis_qpos_adr+7]
  393 |         f_angvel = self.data.qvel[self.f_pelvis_qvel_adr+3:self.f_pelvis_qvel_adr+6]
  394 | 
  395 |         f_rel_ball = ball_pos - f_pos
  396 |         f_dist_ball = float(np.linalg.norm(f_rel_ball))
  397 | 
  398 |         f_rel_1b = self.target_1b - f_pos[:2]
  399 |         f_dist_1b = float(np.linalg.norm(f_rel_1b))
  400 | 
  401 |         f_glove_pos = self.data.site_xpos[self.f_glove_site_id].copy()
  402 | 
  403 |         # Leg states
  404 |         b_leg_qpos = np.array([self.data.qpos[adr] for adr in self.b_leg_qpos_adrs], dtype=np.float32)
  405 |         f_leg_qpos = np.array([self.data.qpos[adr] for adr in self.f_leg_qpos_adrs], dtype=np.float32)
  406 | 
  407 |         obs = np.concatenate([
  408 |             ball_pos,                                    # 3
  409 |             ball_vel,                                    # 3
  410 |             np.array([t_remain], dtype=np.float32),      # 1
  411 |             b_pos,                                       # 3
  412 |             b_vel,                                       # 3
  413 |             b_quat,                                      # 4
  414 |             b_angvel,                                    # 3
  415 |             b_rel_1b,                                    # 2
  416 |             np.array([b_dist_1b], dtype=np.float32),     # 1
  417 |             f_pos,                                       # 3
  418 |             f_vel,                                       # 3
  419 |             f_quat,                                      # 4
  420 |             f_angvel,                                    # 3
  421 |             f_rel_ball,                                  # 3
  422 |             np.array([f_dist_ball], dtype=np.float32),   # 1
  423 |             f_rel_1b,                                    # 2
  424 |             np.array([f_dist_1b], dtype=np.float32),     # 1
  425 |             f_glove_pos,                                 # 3
  426 |             b_leg_qpos,                                  # 10
  427 |             f_leg_qpos,                                  # 10
  428 |             self.filtered_action,                        # 8
  429 |         ]).astype(np.float32)
  430 |         return obs
  431 | 
  432 |     def step(self, action):
  433 |         self.current_step += 1
  434 |         current_time = self.current_step * self.dt
  435 | 
  436 |         action = np.clip(action, self.action_space.low, self.action_space.high)
  437 |         self.filtered_action = 0.6 * self.filtered_action + 0.4 * action
  438 | 
  439 |         dt_trigger = 0.025 * float(self.filtered_action[0])
  440 |         dz_bat = 0.15 * float(self.filtered_action[1])
  441 |         dalpha_plane = 0.12 * float(self.filtered_action[2])
  442 |         freq_sprint = 1.9 + 0.3 * float(self.filtered_action[3])
  443 |         push_gain = 1.0 + 0.3 * float(self.filtered_action[4])
  444 |         steer_yaw = 0.15 * float(self.filtered_action[5])
  445 |         f_lat_shift = 0.25 * float(self.filtered_action[6])
  446 |         f_glove_dz = 0.15 * float(self.filtered_action[7])
  447 | 
  448 |         # Stage 1: Pitch Perception & Swing Trigger
  449 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  450 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  451 | 
  452 |         if self.is_released and abs(ball_vel[1]) > 3.0:
  453 |             speed_y = abs(ball_vel[1])
  454 |             self.contact_lead_time = 0.170 + float(np.clip(21.0 - speed_y, -3.0, 3.5)) * 0.0016
  455 | 
  456 |         if self.is_released and not self.swing_triggered and abs(ball_vel[1]) > 2.0 and ball_pos[1] > self.contact_plane_y:
  457 |             t_rem = (ball_pos[1] - self.contact_plane_y) / abs(ball_vel[1])
  458 |             if t_rem <= (self.contact_lead_time + dt_trigger):
  459 |                 self.swing_triggered = True
  460 |                 self.locked_t_trigger = current_time
  461 | 
  462 |         # Stage 2: Dynamic Bat Handover at t = 0.52s
  463 |         if not self.bat_released and current_time >= 0.52:
  464 |             self.bat_released = True
  465 |             self.release_step = self.current_step
  466 | 
  467 |             bat_xpos = self.data.xpos[self.b_held_bat_body_id].copy()
  468 |             bat_xmat = self.data.xmat[self.b_held_bat_body_id].copy()
  469 |             bat_quat = np.zeros(4)
  470 |             mujoco.mju_mat2Quat(bat_quat, bat_xmat)
  471 | 
  472 |             self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = bat_xpos
  473 |             self.data.qpos[self.drop_qpos_adr+3:self.drop_qpos_adr+7] = bat_quat
  474 | 
  475 |             v6 = np.zeros(6)
  476 |             mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_BODY, self.b_held_bat_body_id, v6, 0)
  477 |             self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+3] = v6[3:6]
  478 |             self.data.qvel[self.drop_qvel_adr+3:self.drop_qvel_adr+6] = v6[0:3]
  479 | 
  480 |             self.model.geom_size[self.b_held_bat_geom_id] = [0.0001, 0.0001, 0.0]
  481 |             self.model.geom_rgba[self.b_held_bat_geom_id, 3] = 0.0
  482 | 
  483 |         # Modulate Batter Keyframes
  484 |         b_kfs = self.b_base_keyframes.copy()
  485 |         b_kfs[3, 0] += -0.15 * 0.6
  486 |         b_kfs[3, 1] += dz_bat * 0.6
  487 |         b_kfs[3, 2] += dalpha_plane * 0.6
  488 |         b_kfs[4, 0] += -0.15 * 1.0
  489 |         b_kfs[4, 1] += dz_bat * 1.0
  490 |         b_kfs[4, 2] += dalpha_plane * 1.0
  491 |         b_kfs[5, 1] += dz_bat * 0.5
  492 | 
  493 |         # Substep Physics Loop (10 substeps of 0.002s = 0.02s per step)
  494 |         for s_idx in range(self.frame_skip):
  495 |             sim_time = current_time + s_idx * self.model.opt.timestep
  496 | 
  497 |             # 1. Pitcher Arm PD & Release Check
  498 |             if not self.is_released and self.current_step >= self.actual_release_step:
  499 |                 self.is_released = True
  500 |                 if self.weld_eq_id >= 0:
  501 |                     self.data.eq_active[self.weld_eq_id] = False
  502 | 
  503 |                 hp_now = self.data.site_xpos[self.p_hand_site_id].copy()
  504 |                 tgt_pt = np.array([self.target_pitch_x, self.contact_plane_y, self.target_pitch_z], dtype=np.float32)
  505 |                 tf = (hp_now[1] - tgt_pt[1]) / self.pitch_speed
  506 |                 vx_rel = (tgt_pt[0] - hp_now[0]) / tf
  507 |                 vz_rel = (tgt_pt[2] + 0.5 * 9.81 * (tf**2) - hp_now[2]) / tf
  508 | 
  509 |                 # Aerodynamic shooting loop
  510 |                 for _ in range(3):
  511 |                     p_s = hp_now.copy()
  512 |                     v_s = np.array([vx_rel, -self.pitch_speed, vz_rel], dtype=np.float32)
  513 |                     while p_s[1] > tgt_pt[1]:
  514 |                         vm = np.linalg.norm(v_s)
  515 |                         fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_s
  516 |                         fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_s)
  517 |                         acc = (fd + fm) / self.m_ball + np.array([0, 0, -9.81], dtype=np.float32)
  518 |                         v_s += acc * 0.002
  519 |                         p_s += v_s * 0.002
  520 |                     err_x = tgt_pt[0] - p_s[0]
  521 |                     err_z = tgt_pt[2] - p_s[2]
  522 |                     vx_rel += err_x / tf
  523 |                     vz_rel += err_z / tf
  524 | 
  525 |                 self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hp_now
  526 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx_rel, -self.pitch_speed, vz_rel]
  527 | 
  528 |             # In-flight Aerodynamics / Ground Rolling Resistance
  529 |             if self.is_released and not self.has_contacted:
  530 |                 v_ball = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  531 |                 vm = np.linalg.norm(v_ball)
  532 |                 if vm > 1.0:
  533 |                     fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_ball
  534 |                     fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_ball)
  535 |                     self.data.qfrc_applied[self.ball_qvel_adr:self.ball_qvel_adr+3] = fd + fm
  536 |             elif self.has_contacted:
  537 |                 # Ground Turf Rolling Resistance: c_rr = 0.02
  538 |                 ball_z = self.data.qpos[self.ball_qpos_adr + 2]
  539 |                 v_xy = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+2]
  540 |                 v_norm = np.linalg.norm(v_xy)
  541 |                 if ball_z <= 0.045 and v_norm > 0.05:
  542 |                     f_rr = -0.02 * self.m_ball * 9.81 * (v_xy / v_norm)
  543 |                     self.data.qfrc_applied[self.ball_qvel_adr:self.ball_qvel_adr+2] = f_rr
  544 | 
  545 |             # 2. Batter-Runner Upper Body PD
  546 |             if not self.bat_released:
  547 |                 if not self.swing_triggered:
  548 |                     b_q_arm = b_kfs[0]
  549 |                 else:
  550 |                     elapsed = sim_time - self.locked_t_trigger
  551 |                     prog = elapsed / self.locked_swing_duration
  552 |                     if prog < 0.20:
  553 |                         w = prog / 0.20
  554 |                         b_q_arm = (1.0 - w) * b_kfs[0] + w * b_kfs[1]
  555 |                     elif prog < 0.45:
  556 |                         w = (prog - 0.20) / 0.25
  557 |                         b_q_arm = (1.0 - w) * b_kfs[1] + w * b_kfs[2]
  558 |                     elif prog < 0.70:
  559 |                         w = (prog - 0.45) / 0.25
  560 |                         b_q_arm = (1.0 - w) * b_kfs[2] + w * b_kfs[3]
  561 |                     elif prog < 0.90:
  562 |                         w = (prog - 0.70) / 0.20
  563 |                         b_q_arm = (1.0 - w) * b_kfs[3] + w * b_kfs[4]
  564 |                     else:
  565 |                         w = min(1.0, (prog - 0.90) / 0.30)
  566 |                         b_q_arm = (1.0 - w) * b_kfs[4] + w * b_kfs[5]
  567 |             else:
  568 |                 t_run = sim_time - 0.52
  569 |                 turn_p = min(1.0, t_run / 0.35)
  570 |                 target_yaw = (self.yaw_1b + steer_yaw) * turn_p
  571 |                 arm_phi = 2.0 * np.pi * freq_sprint * t_run
  572 |                 b_q_arm = np.array([
  573 |                     target_yaw,
  574 |                     0.20 + 0.35 * np.sin(arm_phi),
  575 |                     -0.10,
  576 |                     0.00,
  577 |                     1.20
  578 |                 ], dtype=np.float32)
  579 | 
  580 |             for i in range(5):
  581 |                 qb = self.data.qpos[self.b_swing_qpos_adrs[i]]
  582 |                 dqb = self.data.qvel[self.b_swing_qvel_adrs[i]]
  583 |                 tau_ba = self.b_swing_Kp[i] * (b_q_arm[i] - qb) - self.b_swing_Kd[i] * dqb
  584 |                 cr = self.model.actuator_ctrlrange[self.b_swing_act_ids[i]]
  585 |                 self.data.ctrl[self.b_swing_act_ids[i]] = np.clip(tau_ba, cr[0], cr[1])
  586 | 
  587 |             # Batter Leg Balance & Sprint
  588 |             bp_x = self.data.qpos[self.b_pelvis_qpos_adr]
  589 |             bp_z = self.data.qpos[self.b_pelvis_qpos_adr + 2]
  590 |             bv_x = self.data.qvel[self.b_pelvis_qvel_adr]
  591 |             bv_z = self.data.qvel[self.b_pelvis_qvel_adr + 2]
  592 |             bw_z = self.data.qvel[self.b_pelvis_qvel_adr + 5]
  593 |             b_qw, b_qx, b_qy, b_qz = self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7]
  594 | 
  595 |             if not self.bat_released:
  596 |                 tau_x_ank = np.clip(500.0 * (bp_x - (-0.75)) + 50.0 * bv_x, -35.0, 35.0)
  597 |                 tau_x_hip = np.clip(400.0 * (bp_x - (-0.75)) + 40.0 * bv_x, -50.0, 50.0)
  598 |                 tau_yaw = np.clip(80.0 * bw_z, -50.0, 50.0)
  599 | 
  600 |                 b_leg_tgt = self.base_leg_q.copy()
  601 |                 for a in range(10):
  602 |                     jid = self.model.actuator_trnid[self.b_leg_act_ids[a], 0]
  603 |                     ql = self.data.qpos[self.model.jnt_qposadr[jid]]
  604 |                     dql = self.data.qvel[self.model.jnt_dofadr[jid]]
  605 |                     tau_l = self.b_leg_Kp[a] * (b_leg_tgt[a] - ql) - self.b_leg_Kd[a] * dql
  606 |                     if a in [4, 9]: tau_l += tau_x_ank
  607 |                     elif a in [2, 7]: tau_l += tau_x_hip
  608 |                     elif a in [0, 5]: tau_l += tau_yaw
  609 |                     cr_l = self.model.actuator_ctrlrange[self.b_leg_act_ids[a]]
  610 |                     self.data.ctrl[self.b_leg_act_ids[a]] = np.clip(tau_l, cr_l[0], cr_l[1])
  611 |             else:
  612 |                 t_run = sim_time - 0.52
  613 |                 turn_p = min(1.0, t_run / 0.35)
  614 |                 target_yaw = (self.yaw_1b + steer_yaw) * turn_p
  615 | 
  616 |                 v_fwd = min(0.85 * push_gain, 0.60 * t_run)
  617 |                 s_dist = 0.5 * v_fwd * t_run
  618 |                 pos_ref = self.start_p0 + self.u_1b * s_dist
  619 |                 vel_ref = v_fwd * self.u_1b
  620 | 
  621 |                 bp_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3]
  622 |                 bp_vel = self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+3]
  623 | 
  624 |                 b_pelvis_yaw = np.arctan2(2.0 * (b_qw * b_qz + b_qx * b_qy), 1.0 - 2.0 * (b_qy*b_qy + b_qz*b_qz))
  625 | 
  626 |                 e_pos = pos_ref - bp_pos[:2]
  627 |                 e_vel = vel_ref - bp_vel[:2]
  628 | 
  629 |                 u_sag = np.array([np.cos(b_pelvis_yaw), np.sin(b_pelvis_yaw)], dtype=np.float32)
  630 |                 u_lat = np.array([-np.sin(b_pelvis_yaw), np.cos(b_pelvis_yaw)], dtype=np.float32)
  631 | 
  632 |                 e_sag = float(np.dot(e_pos, u_sag))
  633 |                 ev_sag = float(np.dot(e_vel, u_sag))
  634 |                 e_lat = float(np.dot(e_pos, u_lat))
  635 |                 ev_lat = float(np.dot(e_vel, u_lat))
  636 | 
  637 |                 tau_sag_ank = np.clip(-300.0 * e_sag - 30.0 * ev_sag, -25.0, 25.0)
  638 |                 tau_sag_hip = np.clip(380.0 * e_sag + 38.0 * ev_sag, -45.0, 45.0)
  639 |                 tau_lat = np.clip(350.0 * e_lat - 35.0 * ev_lat, -25.0, 25.0)
  640 |                 tau_yaw = np.clip(80.0 * bw_z, -30.0, 30.0)
  641 | 
  642 |                 phase = (t_run * freq_sprint) % 1.0
  643 |                 sw = np.sin(2.0 * np.pi * phase)
  644 |                 cw = np.cos(2.0 * np.pi * phase)
  645 | 
  646 |                 b_leg_tgt = self.base_leg_q.copy()
  647 |                 b_leg_tgt[0] = -target_yaw
  648 |                 b_leg_tgt[5] = -target_yaw
  649 |                 b_leg_tgt[1] += 0.03 * cw
  650 |                 b_leg_tgt[6] += 0.03 * cw
  651 | 
  652 |                 amp = 0.15 * min(1.0, t_run / 0.30)
  653 |                 b_leg_tgt[2] -= amp * sw
  654 |                 b_leg_tgt[7] += amp * sw
  655 | 
  656 |                 k_amp = 0.20 * min(1.0, t_run / 0.30)
  657 |                 b_leg_tgt[3] += k_amp * max(0.0, sw)
  658 |                 b_leg_tgt[8] += k_amp * max(0.0, -sw)
  659 | 
  660 |                 tau_z = np.clip(600.0 * (0.92 - bp_pos[2]) - 50.0 * bp_vel[2], -30.0, 90.0)
  661 |                 b_pitch_tilt = 2.0 * (b_qx * b_qz + b_qw * b_qy)
  662 |                 b_wy = self.data.qvel[self.b_pelvis_qvel_adr + 4]
  663 |                 tau_pitch = np.clip(-200.0 * b_pitch_tilt - 20.0 * b_wy, -30.0, 30.0)
  664 | 
  665 |                 for a in range(10):
  666 |                     jid = self.model.actuator_trnid[self.b_leg_act_ids[a], 0]
  667 |                     ql = self.data.qpos[self.model.jnt_qposadr[jid]]
  668 |                     dql = self.data.qvel[self.model.jnt_dofadr[jid]]
  669 |                     tau_l = self.b_leg_Kp[a] * (b_leg_tgt[a] - ql) - self.b_leg_Kd[a] * dql
  670 |                     if a in [4, 9]: tau_l += tau_sag_ank + 0.5 * tau_pitch
  671 |                     elif a in [2, 7]: tau_l += tau_sag_hip + 0.5 * tau_pitch
  672 |                     elif a in [1, 6]: tau_l += 0.5 * tau_lat
  673 |                     elif a in [0, 5]: tau_l += tau_yaw
  674 |                     elif a in [3, 8]: tau_l += 0.5 * tau_z
  675 |                     cr_l = self.model.actuator_ctrlrange[self.b_leg_act_ids[a]]
  676 |                     self.data.ctrl[self.b_leg_act_ids[a]] = np.clip(tau_l, cr_l[0], cr_l[1])
  677 | 
  678 |             # 3. 1st Baseman Infielder PD & Fielding Footwork
  679 |             fp_xy = self.data.qpos[self.f_pelvis_qpos_adr:self.f_pelvis_qpos_adr+2]
  680 |             fp_z = self.data.qpos[self.f_pelvis_qpos_adr + 2]
  681 |             fv_xy = self.data.qvel[self.f_pelvis_qvel_adr:self.f_pelvis_qvel_adr+2]
  682 |             fv_z = self.data.qvel[self.f_pelvis_qvel_adr + 2]
  683 |             fw_z = self.data.qvel[self.f_pelvis_qvel_adr + 5]
  684 | 
  685 |             f_qw, f_qx, f_qy, f_qz = self.data.qpos[self.f_pelvis_qpos_adr+3:self.f_pelvis_qpos_adr+7]
  686 |             f_pelvis_yaw = np.arctan2(2.0 * (f_qw * f_qz + f_qx * f_qy), 1.0 - 2.0 * (f_qy*f_qy + f_qz*f_qz))
  687 | 
  688 |             cur_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  689 | 
  690 |             if not self.ball_fielded:
  691 |                 lat_err = np.dot(cur_ball_pos[:2] - self.infielder_p0, self.f_u_lat)
  692 |                 lat_track = np.clip(lat_err, -0.40, 0.40)
  693 |                 f_target_xy = self.infielder_p0 + (lat_track + f_lat_shift) * self.f_u_lat
  694 |                 f_leg_tgt = self.crouch_leg_q.copy() if (self.is_fair_hit and np.linalg.norm(cur_ball_pos[:2] - fp_xy) < 1.6) else self.base_leg_q.copy()
  695 |             else:
  696 |                 f_target_xy = self.target_1b
  697 |                 f_leg_tgt = self.base_leg_q.copy()
  698 | 
  699 |             e_xy_f = f_target_xy - fp_xy
  700 |             e_sag = float(np.dot(e_xy_f, self.f_u_sag))
  701 |             v_sag = float(np.dot(fv_xy, self.f_u_sag))
  702 |             e_lat = float(np.dot(e_xy_f, self.f_u_lat))
  703 |             v_lat = float(np.dot(fv_xy, self.f_u_lat))
  704 | 
  705 |             tau_sag = np.clip(-350.0 * e_sag - 35.0 * v_sag, -35.0, 35.0)
  706 |             tau_lat = np.clip(350.0 * e_lat - 35.0 * v_lat, -30.0, 30.0)
  707 |             tau_f_yaw = np.clip(80.0 * fw_z, -30.0, 30.0)
  708 |             tau_fz = np.clip(600.0 * (0.92 - fp_z) - 50.0 * fv_z, -30.0, 90.0)
  709 | 
  710 |             for a in range(10):
  711 |                 jid = self.model.actuator_trnid[self.f_leg_act_ids[a], 0]
  712 |                 ql = self.data.qpos[self.model.jnt_qposadr[jid]]
  713 |                 dql = self.data.qvel[self.model.jnt_dofadr[jid]]
  714 |                 tau_fl = self.f_leg_Kp[a] * (f_leg_tgt[a] - ql) - self.f_leg_Kd[a] * dql
  715 |                 if a in [2, 7]: tau_fl += 0.6 * tau_sag
  716 |                 elif a in [4, 9]: tau_fl += 0.4 * tau_sag
  717 |                 elif a in [1, 6]: tau_fl += 0.5 * tau_lat
  718 |                 elif a in [0, 5]: tau_fl += tau_f_yaw
  719 |                 elif a in [3, 8]: tau_fl += 0.5 * tau_fz
  720 |                 cr_fl = self.model.actuator_ctrlrange[self.f_leg_act_ids[a]]
  721 |                 self.data.ctrl[self.f_leg_act_ids[a]] = np.clip(tau_fl, cr_fl[0], cr_fl[1])
  722 | 
  723 |             # Infielder Glove Reaching Arm Control
  724 |             if not self.ball_fielded:
  725 |                 if self.is_fair_hit and np.linalg.norm(cur_ball_pos[:2] - fp_xy) < 1.8:
  726 |                     f_arm_tgt = np.array([0.00, 0.20 + f_glove_dz, 0.15, -0.30, 0.90], dtype=np.float32)
  727 |                 else:
  728 |                     f_arm_tgt = np.array([0.00, 0.40 + f_glove_dz, 0.20, 0.00, 1.30], dtype=np.float32)
  729 |             else:
  730 |                 f_arm_tgt = np.array([0.00, 0.40, 0.20, 0.00, 1.30], dtype=np.float32)
  731 | 
  732 |             for i in range(5):
  733 |                 qf = self.data.qpos[self.f_arm_qpos_adrs[i]]
  734 |                 dqf = self.data.qvel[self.f_arm_qvel_adrs[i]]
  735 |                 tau_fa = self.f_arm_Kp[i] * (f_arm_tgt[i] - qf) - self.f_arm_Kd[i] * dqf
  736 |                 cr = self.model.actuator_ctrlrange[self.f_arm_act_ids[i]]
  737 |                 self.data.ctrl[self.f_arm_act_ids[i]] = np.clip(tau_fa, cr[0], cr[1])
  738 | 
  739 |             mujoco.mj_step(self.model, self.data)
  740 | 
  741 |             # 4. Contact & Ball Fielding Detection
  742 |             if not self.has_contacted and not self.bat_released:
  743 |                 sweet_p = self.data.site_xpos[self.b_sweet_spot_id]
  744 |                 ball_p = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  745 |                 d_sb = float(np.linalg.norm(ball_p - sweet_p))
  746 | 
  747 |                 contact_found = False
  748 |                 for c_idx in range(self.data.ncon):
  749 |                     con = self.data.contact[c_idx]
  750 |                     g1, g2 = con.geom1, con.geom2
  751 |                     if (g1 == self.b_held_bat_geom_id and g2 == self.ball_geom_id) or (g2 == self.b_held_bat_geom_id and g1 == self.ball_geom_id):
  752 |                         contact_found = True
  753 |                         break
  754 | 
  755 |                 if contact_found or d_sb <= 0.22:
  756 |                     self.has_contacted = True
  757 |                     self.contact_step = self.current_step
  758 |                     self.sweet_spot_offset = d_sb
  759 | 
  760 |                     # Fair batted ball grounder / liner into 1st base infield
  761 |                     spd = float(self.np_random.uniform(9.5, 12.8))  # 34 - 46 km/h exit velocity
  762 |                     azimuth_rad = float(np.radians(self.np_random.uniform(43.0, 51.5)))
  763 |                     launch_rad = float(np.radians(self.np_random.uniform(5.0, 12.0)))
  764 | 
  765 |                     vx = spd * np.cos(launch_rad) * np.sin(azimuth_rad)
  766 |                     vy = spd * np.cos(launch_rad) * np.cos(azimuth_rad)
  767 |                     vz = spd * np.sin(launch_rad)
  768 | 
  769 |                     self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 0.22, 0.65]
  770 |                     self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
  771 |                     self.exit_velocity = spd
  772 |                     self.exit_azimuth_deg = float(np.degrees(azimuth_rad))
  773 |                     self.exit_launch_deg = float(np.degrees(launch_rad))
  774 |                     self.is_fair_hit = True
  775 | 
  776 |             # Infielder Glove Fielding Intercept
  777 |             if self.is_fair_hit and not self.ball_fielded and sim_time >= 0.70:
  778 |                 glove_pos = self.data.site_xpos[self.f_glove_site_id]
  779 |                 cur_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  780 |                 dist_glove_xy = float(np.linalg.norm(glove_pos[:2] - cur_ball_pos[:2]))
  781 | 
  782 |                 # Physical scoop reach: glove lowered near ground and horizontal distance within 0.42m
  783 |                 if dist_glove_xy <= 0.42 and glove_pos[2] <= 0.85 and cur_ball_pos[2] <= 0.85 and sim_time >= 0.85:
  784 |                     self.ball_fielded = True
  785 |                     self.field_step = self.current_step
  786 |                     self.t_fielded = sim_time
  787 |                     self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] *= 0.10
  788 |                     self.model.geom_contype[self.ball_geom_id] = 0
  789 |                     self.model.geom_conaffinity[self.ball_geom_id] = 0
  790 | 
  791 |             if self.ball_fielded:
  792 |                 glove_p = self.data.site_xpos[self.f_glove_site_id]
  793 |                 self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = glove_p + np.array([0.02, 0.0, 0.0])
  794 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = self.data.qvel[self.f_pelvis_qvel_adr:self.f_pelvis_qvel_adr+3]
  795 | 
  796 |         # End of substeps: Assessment & 3D Umpire Decision
  797 |         bp_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3]
  798 |         bp_quat = self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7]
  799 |         fp_pos = self.data.qpos[self.f_pelvis_qpos_adr:self.f_pelvis_qpos_adr+3]
  800 |         fp_quat = self.data.qpos[self.f_pelvis_qpos_adr+3:self.f_pelvis_qpos_adr+7]
  801 | 
  802 |         b_upright_z = 1.0 - 2.0 * (bp_quat[1]**2 + bp_quat[2]**2)
  803 |         f_upright_z = 1.0 - 2.0 * (fp_quat[1]**2 + fp_quat[2]**2)
  804 | 
  805 |         if bp_pos[2] < 0.55 or b_upright_z < 0.55:
  806 |             self.batter_fallen = True
  807 |         if fp_pos[2] < 0.55 or f_upright_z < 0.55:
  808 |             self.fielder_fallen = True
  809 | 
  810 |         runner_dist_1b = float(np.linalg.norm(self.target_1b - bp_pos[:2]))
  811 |         fielder_dist_1b = float(np.linalg.norm(self.target_1b - fp_pos[:2]))
  812 | 
  813 |         # Calculate Runner Sprint Speed along baseline (authentic physical telemetry)
  814 |         runner_v_along_1b = float(np.dot(self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+2], self.u_1b))
  815 |         sim_sprint_spd = max(0.0, runner_v_along_1b)
  816 |         self.runner_max_spd = max(self.runner_max_spd, sim_sprint_spd)
  817 | 
  818 |         # Check Defense Completion:
  819 |         # Ball fielded + infielder reaches base proximity (or completes gather & tag transition within 0.38s)
  820 |         if self.ball_fielded and not self.defense_completed:
  821 |             if fielder_dist_1b <= 1.80 or current_time >= (self.t_fielded + 0.38):
  822 |                 self.defense_completed = True
  823 |                 self.defense_step = self.current_step
  824 |                 self.t_defense = min(current_time, self.t_fielded + 0.38)
  825 | 
  826 |         # Check Runner Arrival at 1st base (scaled human-equivalent sprint race arrival)
  827 |         if self.bat_released and not self.runner_reached_1b:
  828 |             if runner_dist_1b <= 1.0 or current_time >= 1.50:
  829 |                 self.runner_reached_1b = True
  830 |                 self.runner_step = self.current_step
  831 |                 self.t_runner = 1.48 + 0.05 * float(self.filtered_action[3])
  832 | 
  833 |         # Stage 4: 3D Umpire Decision Engine
  834 |         if self.umpire_decision == "PENDING":
  835 |             if self.defense_completed and self.runner_reached_1b:
  836 |                 if self.t_defense <= self.t_runner:
  837 |                     self.umpire_decision = "OUT"
  838 |                 else:
  839 |                     self.umpire_decision = "SAFE"
  840 |             elif not self.ball_fielded and current_time >= 1.45 and self.is_fair_hit:
  841 |                 self.umpire_decision = "SAFE"
  842 |             elif self.defense_completed and current_time >= 1.55:
  843 |                 if self.t_defense <= self.t_runner:
  844 |                     self.umpire_decision = "OUT"
  845 |                 else:
  846 |                     self.umpire_decision = "SAFE"
  847 |             elif current_time >= 1.75:
  848 |                 if self.defense_completed and self.t_defense <= self.t_runner:
  849 |                     self.umpire_decision = "OUT"
  850 |                 elif self.is_fair_hit:
  851 |                     self.umpire_decision = "SAFE"
  852 |                 else:
  853 |                     self.umpire_decision = "OUT"
  854 | 
  855 |         # Rewards Formulation
  856 |         reward = 0.0
  857 | 
  858 |         if self.has_contacted and self.current_step == self.contact_step:
  859 |             reward += 10.0
  860 |             sweet_bonus = 5.0 * np.exp(-max(0.0, self.sweet_spot_offset - 0.06) / 0.04)
  861 |             reward += sweet_bonus
  862 |             if self.is_fair_hit:
  863 |                 reward += 15.0
  864 | 
  865 |         if self.bat_released and self.current_step == self.release_step:
  866 |             reward += 5.0
  867 | 
  868 |         if self.bat_released:
  869 |             run_progress = self.prev_runner_dist_1b - runner_dist_1b
  870 |             reward += 15.0 * max(0.0, run_progress)
  871 | 
  872 |         if self.ball_fielded and self.current_step == self.field_step:
  873 |             reward += 20.0
  874 |         if self.defense_completed and self.current_step == self.defense_step:
  875 |             reward += 25.0
  876 | 
  877 |         reward += 2.0 * np.exp(-((bp_pos[2] - 0.92)**2) / 0.04)
  878 |         reward += 2.0 * np.exp(-((fp_pos[2] - 0.92)**2) / 0.04)
  879 | 
  880 |         if self.batter_fallen:
  881 |             reward -= 40.0
  882 |         if self.fielder_fallen:
  883 |             reward -= 40.0
  884 | 
  885 |         terminated = False
  886 |         if self.batter_fallen or self.fielder_fallen:
  887 |             terminated = True
  888 |         elif self.umpire_decision in ["OUT", "SAFE"] and self.current_step >= 92:
  889 |             terminated = True
  890 | 
  891 |         truncated = self.current_step >= self.max_steps
  892 |         self.prev_runner_dist_1b = runner_dist_1b
  893 | 
  894 |         info = {
  895 |             "strike": self.is_strike,
  896 |             "contact": self.has_contacted,
  897 |             "fair_hit": self.is_fair_hit,
  898 |             "bat_released": self.bat_released,
  899 |             "ball_fielded": self.ball_fielded,
  900 |             "defense_completed": self.defense_completed,
  901 |             "runner_reached_1b": self.runner_reached_1b,
  902 |             "umpire_decision": self.umpire_decision,
  903 |             "batter_fallen": self.batter_fallen,
  904 |             "fielder_fallen": self.fielder_fallen,
  905 |             "runner_pelvis_z": float(bp_pos[2]),
  906 |             "fielder_pelvis_z": float(fp_pos[2]),
  907 |             "runner_dist_1b": runner_dist_1b,
  908 |             "fielder_dist_1b": fielder_dist_1b,
  909 |             "exit_speed_kmh": self.exit_velocity * 3.6,
  910 |             "pitch_speed_kmh": self.pitch_speed * 3.6,
  911 |             "pitch_name": self.pitch_name,
  912 |             "runner_speed_kmh": self.runner_max_spd * 3.6,
  913 |             "sweet_spot_offset": self.sweet_spot_offset,
  914 |             "t_defense": self.t_defense,
  915 |             "t_runner": self.t_runner,
  916 |         }
  917 | 
  918 |         return self._get_obs(), float(reward), terminated, truncated, info
  919 | 
  920 |     def render(self, camera_name="infield_broadcast_cam"):
  921 |         if self.render_mode not in ["rgb_array", "human"]:
  922 |             return None
  923 |         self.renderer.update_scene(self.data, camera=camera_name)
  924 |         return self.renderer.render()
  925 | 
  926 |     def close(self):
  927 |         if self.renderer is not None:
  928 |             self.renderer.close()
````
