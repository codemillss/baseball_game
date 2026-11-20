# bipedal/envs/athletic_duel_env.py

원본: [envs/athletic_duel_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/envs/athletic_duel_env.py)

SHA256: `9926d5d37152a657ad948263661c4dc7ea7542121e513624bf7f7791cf85dd92`

전체 737행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `AthleticDuelEnv` | ClassDef | 19 | 737 |
| `__init__` | FunctionDef | 22 | 192 |
| `reset` | FunctionDef | 194 | 272 |
| `_get_obs` | FunctionDef | 274 | 314 |
| `step` | FunctionDef | 316 | 724 |
| `render` | FunctionDef | 726 | 733 |
| `close` | FunctionDef | 735 | 737 |

## 전체 원문

````text
    1 | """
    2 | AthleticDuelEnv: Unified Whole-Body Stadium Duel with Deep-Knee Athletic Batter Stance,
    3 | 10m Pitcher Mound, 6-DoF Deep-Squat Catcher, and Standardized Strike Zone.
    4 | """
    5 | 
    6 | import os
    7 | import sys
    8 | import numpy as np
    9 | import gymnasium as gym
   10 | from gymnasium import spaces
   11 | import mujoco
   12 | 
   13 | current_dir = os.path.dirname(os.path.abspath(__file__))
   14 | parent_dir = os.path.dirname(current_dir)
   15 | if parent_dir not in sys.path:
   16 |     sys.path.insert(0, parent_dir)
   17 | 
   18 | 
   19 | class AthleticDuelEnv(gym.Env):
   20 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}
   21 | 
   22 |     def __init__(
   23 |         self,
   24 |         xml_path=None,
   25 |         render_mode=None,
   26 |         frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz)
   27 |         pitch_types=None,  # 0: Fastball, 1: Slider, 2: Curveball
   28 |     ):
   29 |         super().__init__()
   30 | 
   31 |         if xml_path is None:
   32 |             xml_path = os.path.join(parent_dir, "models", "h1_athletic_duel.xml")
   33 | 
   34 |         self.xml_path = xml_path
   35 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   36 |         self.data = mujoco.MjData(self.model)
   37 | 
   38 |         self.render_mode = render_mode
   39 |         self.frame_skip = frame_skip
   40 |         self.dt = self.model.opt.timestep * self.frame_skip
   41 |         self.pitch_types = pitch_types if pitch_types is not None else [0, 1, 2]
   42 | 
   43 |         # Bodies & Sites
   44 |         self.p_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "p_pelvis")
   45 |         self.c_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "c_pelvis")
   46 |         self.b_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "b_pelvis")
   47 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   48 | 
   49 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   50 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   51 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   52 |         self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")
   53 |         self.c_mitt_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "c_mitt_site")
   54 |         self.p_hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")
   55 |         self.b_left_ankle_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "b_left_ankle_link")
   56 |         self.b_right_ankle_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "b_right_ankle_link")
   57 |         self.b_left_ankle_dof = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "b_left_ankle")]
   58 |         self.b_l_hand_grip_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "b_l_hand_grip")
   59 |         self.bat_grip_left_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_grip_left")
   60 | 
   61 |         # Freejoints
   62 |         ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   63 |         self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
   64 |         self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]
   65 | 
   66 |         c_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "c_pelvis_joint")
   67 |         self.c_pelvis_qpos_adr = self.model.jnt_qposadr[c_pelvis_jnt_id]
   68 |         self.c_pelvis_qvel_adr = self.model.jnt_dofadr[c_pelvis_jnt_id]
   69 | 
   70 |         b_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "b_pelvis_joint")
   71 |         self.b_pelvis_qpos_adr = self.model.jnt_qposadr[b_pelvis_jnt_id]
   72 |         self.b_pelvis_qvel_adr = self.model.jnt_dofadr[b_pelvis_jnt_id]
   73 | 
   74 |         # Pitcher Actuators
   75 |         self.p_act_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
   76 |         self.p_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.p_act_names]
   77 |         self.p_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
   78 |         self.p_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
   79 | 
   80 |         # Catcher Upper & Legs
   81 |         self.c_upper_names = ["c_torso", "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow", "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"]
   82 |         self.c_upper_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.c_upper_names]
   83 |         self.c_upper_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.c_upper_act_ids]
   84 |         self.c_upper_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.c_upper_act_ids]
   85 | 
   86 |         self.c_leg_names = ["c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle", "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle"]
   87 |         self.c_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.c_leg_names]
   88 |         self.c_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.c_leg_act_ids]
   89 |         self.c_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.c_leg_act_ids]
   90 | 
   91 |         # Batter Upper (Two-Handed Coordination: 9 DoF)
   92 |         self.b_upper_names = ["b_torso", "b_left_shoulder_pitch", "b_left_shoulder_roll", "b_left_shoulder_yaw", "b_left_elbow", "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"]
   93 |         self.b_upper_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_upper_names]
   94 |         self.b_upper_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_upper_act_ids]
   95 |         self.b_upper_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_upper_act_ids]
   96 | 
   97 |         # Batter Legs (10 DoF Whole-Body ZMP Balance & Planted Lead Foot)
   98 |         self.b_leg_names = ["b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle", "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle"]
   99 |         self.b_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_leg_names]
  100 |         self.b_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]
  101 |         self.b_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]
  102 | 
  103 |         # PD Gains
  104 |         self.p_Kp = 350.0
  105 |         self.p_Kd = 25.0
  106 |         self.c_leg_Kp = np.array([400, 400, 700, 1000, 250, 400, 400, 700, 1000, 250], dtype=np.float32)
  107 |         self.c_leg_Kd = np.array([30, 30, 50, 70, 20, 30, 30, 50, 70, 20], dtype=np.float32)
  108 |         self.c_upper_Kp = 80.0
  109 |         self.c_upper_Kd = 8.0
  110 | 
  111 |         self.b_leg_Kp = np.array([450, 450, 650, 720, 280, 450, 450, 650, 720, 280], dtype=np.float32)
  112 |         self.b_leg_Kd = np.array([38, 38, 48, 58, 22, 38, 38, 48, 58, 22], dtype=np.float32)
  113 |         self.b_upper_Kp = np.array([850, 260, 205, 152, 185, 260, 205, 152, 185], dtype=np.float32)
  114 |         self.b_upper_Kd = np.array([55, 21, 16, 12, 14, 21, 16, 12, 14], dtype=np.float32)
  115 | 
  116 |         # Catcher Rock-Solid Low Squat Targets (CoM aligned directly over midfoot)
  117 |         self.c_pelvis_z_target = 0.765
  118 |         self.c_pelvis_y_target = -0.85
  119 |         self.c_pelvis_x_target = 0.0
  120 |         self.q_squat_legs = np.array([0.04, 0.16, -0.58, 1.45, -0.87, -0.04, -0.16, -0.58, 1.45, -0.87], dtype=np.float32)
  121 |         self.q_squat_upper = np.array([0.0, -0.40, -0.30, -0.30, 0.20, -0.50, -0.20, 0.0, 1.50], dtype=np.float32)
  122 | 
  123 |         # Batter Deep-Knee Low Athletic Stance (Pelvis Z = 0.855m, knee = 72.2 deg)
  124 |         self.b_pelvis_z_target = 0.855
  125 |         self.b_pelvis_x_target = -1.10
  126 |         self.b_pelvis_y_target = 0.00
  127 |         th_k = 1.26
  128 |         th_h = -0.63
  129 |         th_a = -0.63
  130 |         self.b_base_legs = np.array([0.0, 0.16, th_h, th_k, th_a, 0.0, -0.16, th_h, th_k, th_a], dtype=np.float32)
  131 | 
  132 |         # Fully Coordinated 9-DoF Whole-Body Kinetic Swing Sequence (Tight two-handed grip & Torso Uncoil)
  133 |         # [torso, left_pitch, left_roll, left_yaw, left_elbow, right_pitch, right_roll, right_yaw, right_elbow]
  134 |         self.b_swing_keyframes = np.array([
  135 |             [-0.35, -1.238, -0.127, -0.707, 0.824, -0.288, 0.048, -0.075, -0.224],  # 0: Ready Cocked Bat (-20.1 deg)
  136 |             [-0.45, -1.267, -0.144, -0.748, 0.849, -0.255, -0.076, -0.014, -0.251], # 1: Deep Coil / Stride Load (-25.8 deg)
  137 |             [ 0.05, -1.058, -0.340, -1.300, 1.466, 0.023, 0.340, -0.120, 0.100],   # 2: Slot / Kinetic Whip (+2.9 deg)
  138 |             [ 0.35, -1.026, -0.340, -1.300, 1.323, 0.124, 0.340, -0.120, -0.003],  # 3: Impact on Plate (+20.1 deg, z ~ 0.83m)
  139 |             [ 0.70, -0.956, -0.340, -1.300, 1.154, 0.270, 0.340, -0.090, -0.121],  # 4: Full Extension through ball (+40.1 deg)
  140 |             [ 1.25, -0.812, -0.340, -1.300, 0.328, 0.853, -0.101, 0.195, -0.826],  # 5: High Follow-through wrap (+71.6 deg)
  141 |         ], dtype=np.float32)
  142 | 
  143 |         self.p_keyframes = np.array([
  144 |             [ 0.20, -0.20, -0.40,  0.30,  1.00],
  145 |             [-0.50, -1.40, -0.20, -0.20,  0.20],
  146 |             [-0.90, -1.80, -0.60, -0.50,  0.70],
  147 |         ], dtype=np.float32)
  148 | 
  149 |         # Aerodynamics constants
  150 |         self.rho = 1.205
  151 |         self.r_ball = 0.037
  152 |         self.m_ball = 0.145
  153 |         self.A_ball = np.pi * (self.r_ball ** 2)
  154 |         self.Cd = 0.32
  155 |         self.Cl = 0.24
  156 | 
  157 |         # Action: 6 dims for Whole-Body Batter
  158 |         # a[0]: dt_lead swing timing adjustment (-0.030 to +0.030s)
  159 |         # a[1]: dz_bat plane height adjustment (-0.15 to +0.15rad)
  160 |         # a[2]: dalpha_tilt attack tilt angle adjustment (-0.10 to +0.10rad)
  161 |         # a[3]: dpower_dur swing duration adjustment (-0.020 to +0.020s)
  162 |         # a[4]: dknee_crouch knee flexion depth adjustment (-0.06 to +0.06rad)
  163 |         # a[5]: dweight_shift ankle ZMP balance adjustment (-0.06 to +0.06rad)
  164 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)
  165 |         self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(51,), dtype=np.float32)
  166 | 
  167 |         # Episode state variables
  168 |         self.current_step = 0
  169 |         self.max_steps = 55
  170 |         self.is_released = False
  171 |         self.plate_crossed = False
  172 |         self.plate_cross_x = 0.0
  173 |         self.plate_cross_z = 0.0
  174 |         self.is_strike = False
  175 |         self.is_hit = False
  176 |         self.is_fair = False
  177 |         self.contact_step = -1
  178 |         self.sweet_spot_error = 0.0
  179 |         self.exit_velocity = 0.0
  180 |         self.exit_heading = 0.0
  181 |         self.catcher_caught = False
  182 |         self.catcher_fallen = False
  183 |         self.batter_fallen = False
  184 |         self.framing_error = 0.0
  185 | 
  186 |         self.swing_triggered = False
  187 |         self.locked_t_trigger = 0.0
  188 |         self.locked_swing_duration = 0.200
  189 | 
  190 |         self.renderer = None
  191 |         if self.render_mode in ["rgb_array", "human"]:
  192 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  193 | 
  194 |     def reset(self, seed=None, options=None):
  195 |         super().reset(seed=seed)
  196 |         mujoco.mj_resetData(self.model, self.data)
  197 | 
  198 |         self.current_step = 0
  199 |         self.is_released = False
  200 |         self.plate_crossed = False
  201 |         self.plate_cross_x = 0.0
  202 |         self.plate_cross_z = 0.0
  203 |         self.is_strike = False
  204 |         self.is_hit = False
  205 |         self.is_fair = False
  206 |         self.contact_step = -1
  207 |         self.sweet_spot_error = 0.0
  208 |         self.exit_velocity = 0.0
  209 |         self.exit_heading = 0.0
  210 |         self.catcher_caught = False
  211 |         self.catcher_fallen = False
  212 |         self.batter_fallen = False
  213 |         self.framing_error = 0.0
  214 | 
  215 |         self.swing_triggered = False
  216 |         self.locked_t_trigger = 0.0
  217 |         self.locked_swing_duration = 0.200
  218 | 
  219 |         # Pitch selection
  220 |         p_choice = int(self.np_random.choice(self.pitch_types))
  221 |         if p_choice == 0:
  222 |             self.pitch_name = "Fastball"
  223 |             self.pitch_speed = float(self.np_random.uniform(23.6, 24.7))  # 85-89 km/h
  224 |             self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
  225 |             self.target_pitch_x = float(self.np_random.uniform(-0.12, 0.12))
  226 |             self.target_pitch_z = float(self.np_random.uniform(0.82, 0.94))
  227 |         elif p_choice == 1:
  228 |             self.pitch_name = "Slider"
  229 |             self.pitch_speed = float(self.np_random.uniform(21.1, 22.2))  # 76-80 km/h
  230 |             self.pitch_spin = np.array([40.0, 0.0, 150.0], dtype=np.float32)
  231 |             self.target_pitch_x = float(self.np_random.uniform(0.02, 0.15))
  232 |             self.target_pitch_z = float(self.np_random.uniform(0.72, 0.85))
  233 |         else:
  234 |             self.pitch_name = "Curveball"
  235 |             self.pitch_speed = float(self.np_random.uniform(19.7, 20.8))  # 71-75 km/h
  236 |             self.pitch_spin = np.array([170.0, 0.0, -30.0], dtype=np.float32)
  237 |             self.target_pitch_x = float(self.np_random.uniform(-0.08, 0.08))
  238 |             self.target_pitch_z = float(self.np_random.uniform(0.72, 0.82))
  239 | 
  240 |         # Setup Pitcher
  241 |         for i, adr in enumerate(self.p_qpos_adrs):
  242 |             self.data.qpos[adr] = self.p_keyframes[0, i]
  243 | 
  244 |         # Setup Catcher Deep Squat behind Home Plate (CoM aligned over midfoot)
  245 |         self.data.qpos[self.c_pelvis_qpos_adr:self.c_pelvis_qpos_adr+3] = [self.c_pelvis_x_target, self.c_pelvis_y_target, self.c_pelvis_z_target]
  246 |         self.data.qpos[self.c_pelvis_qpos_adr+3:self.c_pelvis_qpos_adr+7] = [0.7071068, 0.0, 0.0, 0.7071068]
  247 |         self.data.qvel[self.c_pelvis_qvel_adr:self.c_pelvis_qvel_adr+6] = 0.0
  248 |         for i, adr in enumerate(self.c_leg_qpos_adrs):
  249 |             self.data.qpos[adr] = self.q_squat_legs[i]
  250 |         for i, adr in enumerate(self.c_upper_qpos_adrs):
  251 |             self.data.qpos[adr] = self.q_squat_upper[i]
  252 | 
  253 |         # Setup Batter Deep-Knee Low Athletic Stance in Batter's Box (x = -1.10, z = 0.915)
  254 |         self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3] = [self.b_pelvis_x_target, 0.00, self.b_pelvis_z_target]
  255 |         self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  256 |         self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+6] = 0.0
  257 |         for i, adr in enumerate(self.b_leg_qpos_adrs):
  258 |             self.data.qpos[adr] = self.b_base_legs[i]
  259 | 
  260 |         for i, adr in enumerate(self.b_upper_qpos_adrs):
  261 |             self.data.qpos[adr] = self.b_swing_keyframes[0, i]
  262 | 
  263 |         # Place ball in pitcher's hand
  264 |         mujoco.mj_forward(self.model, self.data)
  265 |         hand_pos = self.data.site_xpos[self.p_hand_site_id].copy()
  266 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
  267 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+6] = 0.0
  268 |         mujoco.mj_forward(self.model, self.data)
  269 | 
  270 |         self.flight_time_nominal = float(10.0 / self.pitch_speed)
  271 | 
  272 |         return self._get_obs(), {}
  273 | 
  274 |     def _get_obs(self):
  275 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  276 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
  277 | 
  278 |         if self.is_released and abs(ball_vel[1]) > 1.0 and ball_pos[1] > 0.0:
  279 |             t_remain = float(ball_pos[1] / abs(ball_vel[1]))
  280 |         elif not self.is_released:
  281 |             t_remain = float(self.flight_time_nominal)
  282 |         else:
  283 |             t_remain = 0.0
  284 | 
  285 |         b_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3].copy()
  286 |         b_quat = self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7].copy()
  287 |         b_vel = self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+3].copy()
  288 |         b_angvel = self.data.qvel[self.b_pelvis_qvel_adr+3:self.b_pelvis_qvel_adr+6].copy()
  289 | 
  290 |         sweet_pos = self.data.site_xpos[self.sweet_spot_id].copy()
  291 |         sweet_vel = np.zeros(3, dtype=np.float32)
  292 | 
  293 |         target_pos = np.array([self.target_pitch_x, 0.0, self.target_pitch_z], dtype=np.float32)
  294 | 
  295 |         leg_q = [self.data.qpos[adr] for adr in self.b_leg_qpos_adrs]
  296 |         upper_q = [self.data.qpos[adr] for adr in self.b_upper_qpos_adrs]
  297 |         joint_q = np.array(leg_q + upper_q, dtype=np.float32)
  298 | 
  299 |         obs = np.concatenate([
  300 |             ball_pos,
  301 |             ball_vel,
  302 |             self.pitch_spin * 0.01,
  303 |             np.array([t_remain], dtype=np.float32),
  304 |             b_pos,
  305 |             b_quat,
  306 |             b_vel,
  307 |             b_angvel,
  308 |             sweet_pos,
  309 |             sweet_vel,
  310 |             target_pos,
  311 |             joint_q
  312 |         ]).astype(np.float32)
  313 | 
  314 |         return obs
  315 | 
  316 |     def step(self, action):
  317 |         self.current_step += 1
  318 |         current_time = (self.current_step - 1) * self.dt
  319 | 
  320 |         # Unpack action modulations
  321 |         dt_lead = float(action[0]) * 0.030
  322 |         dz_plane = float(action[1]) * 0.15
  323 |         dalpha_tilt = float(action[2]) * 0.10
  324 |         dpower_dur = float(action[3]) * 0.020
  325 |         dknee_crouch = float(action[4]) * 0.06
  326 |         dweight_shift = float(action[5]) * 0.06
  327 | 
  328 |         # 1. Pitcher kinematics
  329 |         if self.current_step < 2:
  330 |             p_pose = self.p_keyframes[0]
  331 |         elif self.current_step < 4:
  332 |             p_pose = self.p_keyframes[1]
  333 |         else:
  334 |             p_pose = self.p_keyframes[2]
  335 | 
  336 |         # 2. Catcher target framing (moves mitt toward predicted pitch arrival at y = -0.65)
  337 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  338 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  339 |         mitt_pos = self.data.site_xpos[self.c_mitt_site_id]
  340 | 
  341 |         if self.is_released and not self.is_hit and abs(ball_vel[1]) > 1.0 and ball_vel[1] < -0.5:
  342 |             dt_arr = max(0.0, (-0.65 - ball_pos[1]) / ball_vel[1])
  343 |             pred_x = ball_pos[0] + ball_vel[0] * dt_arr
  344 |             pred_z = ball_pos[2] + ball_vel[2] * dt_arr - 0.5 * 9.81 * (dt_arr**2)
  345 |         else:
  346 |             pred_x = self.target_pitch_x
  347 |             pred_z = self.target_pitch_z
  348 | 
  349 |         ex_mitt = float(np.clip((pred_x - mitt_pos[0]) * 1.5, -0.20, 0.20))
  350 |         ez_mitt = float(np.clip((pred_z - mitt_pos[2]) * 1.5, -0.20, 0.20))
  351 | 
  352 |         c_arm_tgt = self.q_squat_upper.copy()
  353 |         c_arm_tgt[0] += -1.8 * ex_mitt
  354 |         c_arm_tgt[1] += -2.5 * ez_mitt
  355 |         c_arm_tgt[2] += -1.5 * ex_mitt
  356 |         c_arm_tgt[4] += -2.0 * ez_mitt
  357 | 
  358 |         c_leg_tgt = self.q_squat_legs.copy()
  359 | 
  360 |         # 3. Dynamic In-Flight Perception & Swing Trigger
  361 |         if self.is_released and abs(ball_vel[1]) > 3.0 and ball_pos[1] > 0.0:
  362 |             speed_y = abs(ball_vel[1])
  363 |             # Calibrated speed-adaptive lead time for 9-DoF connected swing:
  364 |             base_lead = 0.255 + (21.6 - speed_y) * 0.006
  365 |             trigger_lead = base_lead + dt_lead
  366 |             t_rem = ball_pos[1] / speed_y
  367 |             if not self.swing_triggered and t_rem <= trigger_lead:
  368 |                 self.swing_triggered = True
  369 |                 self.locked_t_trigger = current_time
  370 |                 self.locked_swing_duration = max(0.18, 0.220 + dpower_dur)
  371 | 
  372 |         # 4. Batter Stance Legs (with dynamic crouch modulation)
  373 |         b_leg_cmd = self.b_base_legs.copy()
  374 |         b_leg_cmd[3] += dknee_crouch  # Left knee
  375 |         b_leg_cmd[8] += dknee_crouch  # Right knee
  376 |         b_leg_cmd[2] += -0.5 * dknee_crouch
  377 |         b_leg_cmd[7] += -0.5 * dknee_crouch
  378 | 
  379 |         # Sub-step simulation loop
  380 |         for s_idx in range(self.frame_skip):
  381 |             sim_time = current_time + s_idx * self.model.opt.timestep
  382 | 
  383 |             # Pitch release at step 2
  384 |             if not self.is_released and self.current_step >= 2:
  385 |                 self.is_released = True
  386 |                 hp_now = self.data.site_xpos[self.p_hand_site_id].copy()
  387 |                 tgt_pt = np.array([self.target_pitch_x, 0.0, self.target_pitch_z], dtype=np.float32)
  388 |                 tf = (hp_now[1] - tgt_pt[1]) / self.pitch_speed
  389 |                 vx_rel = (tgt_pt[0] - hp_now[0]) / tf
  390 |                 vz_rel = (tgt_pt[2] + 0.5 * 9.81 * (tf**2) - hp_now[2]) / tf
  391 | 
  392 |                 for _ in range(3):
  393 |                     p_s = hp_now.copy()
  394 |                     v_s = np.array([vx_rel, -self.pitch_speed, vz_rel], dtype=np.float32)
  395 |                     while p_s[1] > tgt_pt[1]:
  396 |                         vm = np.linalg.norm(v_s)
  397 |                         fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_s
  398 |                         fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_s)
  399 |                         acc = (fd + fm) / self.m_ball + np.array([0, 0, -9.81], dtype=np.float32)
  400 |                         v_s += acc * 0.002
  401 |                         p_s += v_s * 0.002
  402 |                     vx_rel += (tgt_pt[0] - p_s[0]) / tf
  403 |                     vz_rel += (tgt_pt[2] - p_s[2]) / tf
  404 | 
  405 |                 self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hp_now
  406 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx_rel, -self.pitch_speed, vz_rel]
  407 | 
  408 |             # Direct Aerodynamics Integration on Ball
  409 |             if self.is_released and not self.is_hit and not self.catcher_caught:
  410 |                 v_ball = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  411 |                 vm = np.linalg.norm(v_ball)
  412 |                 if vm > 1.0:
  413 |                     fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_ball
  414 |                     fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_ball)
  415 |                     self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += (fd + fm) / self.m_ball * self.model.opt.timestep
  416 | 
  417 |             # Batter Arm Kinematic Progression (Fully Coordinated 9-DoF Upper Body)
  418 |             if not self.swing_triggered:
  419 |                 b_upper_cmd = list(self.b_swing_keyframes[0])
  420 |             else:
  421 |                 t_sw = sim_time - self.locked_t_trigger
  422 |                 prog = t_sw / self.locked_swing_duration
  423 |                 if prog < 0.20:
  424 |                     w = prog / 0.20
  425 |                     b_upper_cmd = [(1-w)*self.b_swing_keyframes[0][j] + w*self.b_swing_keyframes[1][j] for j in range(9)]
  426 |                 elif prog < 0.45:
  427 |                     w = (prog - 0.20) / 0.25
  428 |                     b_upper_cmd = [(1-w)*self.b_swing_keyframes[1][j] + w*self.b_swing_keyframes[2][j] for j in range(9)]
  429 |                 elif prog < 0.70:
  430 |                     w = (prog - 0.45) / 0.25
  431 |                     b_upper_cmd = [(1-w)*self.b_swing_keyframes[2][j] + w*self.b_swing_keyframes[3][j] for j in range(9)]
  432 |                 elif prog < 0.90:
  433 |                     w = (prog - 0.70) / 0.20
  434 |                     b_upper_cmd = [(1-w)*self.b_swing_keyframes[3][j] + w*self.b_swing_keyframes[4][j] for j in range(9)]
  435 |                 else:
  436 |                     w = min(1.0, (prog - 0.90) / 0.30)
  437 |                     b_upper_cmd = [(1-w)*self.b_swing_keyframes[4][j] + w*self.b_swing_keyframes[5][j] for j in range(9)]
  438 | 
  439 |                 # In-flight perceptual tracking across plate
  440 |                 b_p = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  441 |                 b_v = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  442 |                 if self.is_released and abs(b_v[1]) > 1.0:
  443 |                     t_to_plate = max(0.0, b_p[1] / abs(b_v[1]))
  444 |                     pred_plate_x = b_p[0] + b_v[0] * t_to_plate
  445 |                     pred_plate_z = b_p[2] + b_v[2] * t_to_plate - 0.5 * 9.81 * (t_to_plate ** 2)
  446 |                     # Blend toward target prior when ball is far away (t_to_plate > 0.35s)
  447 |                     blend = min(1.0, (0.35 - t_to_plate) / 0.25) if t_to_plate < 0.35 else 0.0
  448 |                     pred_plate_z = (1.0 - blend) * self.target_pitch_z + blend * pred_plate_z
  449 |                     pred_plate_x = (1.0 - blend) * self.target_pitch_x + blend * pred_plate_x
  450 |                 else:
  451 |                     pred_plate_x = self.target_pitch_x
  452 |                     pred_plate_z = self.target_pitch_z
  453 | 
  454 |                 dz = (pred_plate_z - 0.83) * 1.20 + dz_plane
  455 |                 dx = (pred_plate_x - (-0.05)) * 0.85
  456 |                 b_upper_cmd[1] -= dz  # left shoulder pitch (lower = raise bat plane)
  457 |                 b_upper_cmd[5] -= dz  # right shoulder pitch
  458 |                 b_upper_cmd[0] += dx  # torso uncoil reaches outside/inside
  459 |                 b_upper_cmd[2] += dalpha_tilt
  460 |                 b_upper_cmd[6] += dalpha_tilt
  461 | 
  462 |             # Dynamic Hip Uncoil & Authentic Weight Transfer during swing ("허리를쓰고, 무게중심 이동")
  463 |             b_leg_curr = b_leg_cmd.copy()
  464 |             shift = 0.0
  465 |             if self.swing_triggered:
  466 |                 prog = (sim_time - self.locked_t_trigger) / self.locked_swing_duration
  467 |                 shift = np.clip(prog, 0.0, 1.0)
  468 |                 # Hip yaw actively rotates open ("허리를쓰고")
  469 |                 b_leg_curr[0] += shift * 0.30  # left hip yaw
  470 |                 b_leg_curr[5] += shift * 0.30  # right hip yaw
  471 |                 # Authentic weight transfer from back to front hip
  472 |                 b_leg_curr[7] += shift * 0.20  # right hip pitch extends forward
  473 |                 b_leg_curr[2] -= shift * 0.15  # left hip pitch flexes to brace
  474 |                 # Rear leg pivots on ball of foot ("squash the bug")
  475 |                 b_leg_curr[8] -= shift * 0.15  # right knee drives forward
  476 |                 b_leg_curr[9] += shift * 0.30  # right ankle pivots onto ball of foot
  477 |                 # Lead leg firm plant
  478 |                 b_leg_curr[3] -= shift * 0.06  # left knee locks firmly into turf
  479 |                 b_leg_curr[4] -= shift * 0.04  # left ankle downward plant
  480 | 
  481 |             # Plate Crossing Check (y = 0.0)
  482 |             curr_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  483 |             if not self.plate_crossed and curr_ball_pos[1] <= 0.0:
  484 |                 self.plate_crossed = True
  485 |                 self.plate_cross_x = curr_ball_pos[0]
  486 |                 self.plate_cross_z = curr_ball_pos[2]
  487 |                 if abs(self.plate_cross_x) <= 0.22 and (0.65 <= self.plate_cross_z <= 1.05):
  488 |                     self.is_strike = True
  489 | 
  490 |             # Pre-contact trajectory logging when ball is in front of plate
  491 |             if not self.plate_crossed and curr_ball_pos[1] <= 0.40 and abs(self.data.qvel[self.ball_qvel_adr+1]) > 1.0:
  492 |                 t_cross = curr_ball_pos[1] / abs(self.data.qvel[self.ball_qvel_adr+1])
  493 |                 self.proj_plate_x = float(curr_ball_pos[0] + self.data.qvel[self.ball_qvel_adr] * t_cross)
  494 |                 self.proj_plate_z = float(curr_ball_pos[2] + self.data.qvel[self.ball_qvel_adr+2] * t_cross - 0.5 * 9.81 * (t_cross**2))
  495 | 
  496 |             # Bat-Ball Physical Contact Detection
  497 |             if not self.is_hit and curr_ball_pos[1] <= 0.40:
  498 |                 sweet_pos = self.data.site_xpos[self.sweet_spot_id]
  499 |                 d_contact = float(np.linalg.norm(curr_ball_pos - sweet_pos))
  500 | 
  501 |                 has_collision = False
  502 |                 for c_idx in range(self.data.ncon):
  503 |                     con = self.data.contact[c_idx]
  504 |                     g1, g2 = con.geom1, con.geom2
  505 |                     if (g1 == self.bat_geom_id and g2 == self.ball_geom_id) or \
  506 |                        (g2 == self.bat_geom_id and g1 == self.ball_geom_id):
  507 |                         has_collision = True
  508 |                         break
  509 | 
  510 |                 if has_collision or (d_contact <= 0.18 and abs(curr_ball_pos[1] - sweet_pos[1]) <= 0.09):
  511 |                     self.is_hit = True
  512 |                     self.contact_step = self.current_step
  513 |                     self.sweet_spot_error = d_contact
  514 |                     if not self.plate_crossed:
  515 |                         self.plate_crossed = True
  516 |                         self.plate_cross_x = getattr(self, "proj_plate_x", curr_ball_pos[0])
  517 |                         self.plate_cross_z = getattr(self, "proj_plate_z", curr_ball_pos[2])
  518 |                         if abs(self.plate_cross_x) <= 0.22 and (0.65 <= self.plate_cross_z <= 1.05):
  519 |                             self.is_strike = True
  520 | 
  521 |                     # Elastic impact restitution (COR = 0.55)
  522 |                     v_in = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  523 |                     v_rebound = 0.55 * abs(v_in[1]) + 15.0
  524 |                     vx_out = float(self.np_random.uniform(3.0, 9.0))   # Fair spray angle into field
  525 |                     vz_out = float(self.np_random.uniform(2.0, 5.0))   # Line drive / fly ball
  526 |                     self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx_out, v_rebound, vz_out]
  527 | 
  528 |                     self.exit_velocity = float(np.linalg.norm([vx_out, v_rebound, vz_out])) * 3.6
  529 |                     self.exit_heading = float(np.degrees(np.arctan2(vx_out, v_rebound)))
  530 |                     if 0.0 <= self.exit_heading <= 90.0:
  531 |                         self.is_fair = True
  532 | 
  533 |             # Catcher Catch Detection (if ball not hit and crosses mitt plane)
  534 |             if not self.is_hit and not self.catcher_caught and curr_ball_pos[1] <= (mitt_pos[1] + 0.12):
  535 |                 d_planar = float(np.sqrt((curr_ball_pos[0] - mitt_pos[0])**2 + (curr_ball_pos[2] - mitt_pos[2])**2))
  536 |                 if d_planar <= 0.18:
  537 |                     self.catcher_caught = True
  538 |                     self.framing_error = d_planar
  539 | 
  540 |             if self.catcher_caught:
  541 |                 self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = mitt_pos + np.array([0.0, 0.02, 0.0])
  542 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = 0.0
  543 | 
  544 |             # Actuator Controls:
  545 |             # 1. Pitcher
  546 |             for i, a_id in enumerate(self.p_act_ids):
  547 |                 adr = self.p_qpos_adrs[i]
  548 |                 q_cur = self.data.qpos[adr]
  549 |                 q_dot = self.data.qvel[self.model.jnt_dofadr[self.model.actuator_trnid[a_id, 0]]]
  550 |                 tau = self.p_Kp * (p_pose[i] - q_cur) - self.p_Kd * q_dot
  551 |                 self.data.ctrl[a_id] = np.clip(tau, -60.0, 60.0)
  552 | 
  553 |             # 2. Catcher Upper
  554 |             for i, a_id in enumerate(self.c_upper_act_ids):
  555 |                 adr = self.c_upper_qpos_adrs[i]
  556 |                 q_cur = self.data.qpos[adr]
  557 |                 q_dot = self.data.qvel[self.c_upper_qvel_adrs[i]]
  558 |                 tau = self.c_upper_Kp * (c_arm_tgt[i] - q_cur) - self.c_upper_Kd * q_dot
  559 |                 self.data.ctrl[a_id] = np.clip(tau, -40.0, 40.0)
  560 | 
  561 |             # 3. Catcher Legs: Rock-Solid Active Restorative Balance Controller (No sag, no wobble)
  562 |             cp_x = self.data.qpos[self.c_pelvis_qpos_adr]
  563 |             cp_y = self.data.qpos[self.c_pelvis_qpos_adr + 1]
  564 |             cp_z = self.data.qpos[self.c_pelvis_qpos_adr + 2]
  565 |             cv_x = self.data.qvel[self.c_pelvis_qvel_adr]
  566 |             cv_y = self.data.qvel[self.c_pelvis_qvel_adr + 1]
  567 |             cv_z = self.data.qvel[self.c_pelvis_qvel_adr + 2]
  568 |             cw_z = self.data.qvel[self.c_pelvis_qvel_adr + 5]
  569 | 
  570 |             c_tau_pitch = np.clip(2200.0 * (self.c_pelvis_y_target - cp_y) - 200.0 * cv_y, -200.0, 200.0)
  571 |             c_tau_sag_ank = -np.clip(650.0 * (self.c_pelvis_y_target - cp_y) - 60.0 * cv_y, -60.0, 60.0)
  572 |             c_tau_height_knee = -np.clip(2800.0 * (self.c_pelvis_z_target - cp_z) - 220.0 * cv_z, -250.0, 250.0)
  573 |             c_tau_lat_roll = np.clip(800.0 * (self.c_pelvis_x_target - cp_x) - 80.0 * cv_x, -80.0, 80.0)
  574 |             c_tau_yaw = np.clip(-120.0 * cw_z, -60.0, 60.0)
  575 | 
  576 |             for i, a_id in enumerate(self.c_leg_act_ids):
  577 |                 adr = self.c_leg_qpos_adrs[i]
  578 |                 q_cur = self.data.qpos[adr]
  579 |                 q_dot = self.data.qvel[self.c_leg_qvel_adrs[i]]
  580 |                 tau = self.c_leg_Kp[i] * (c_leg_tgt[i] - q_cur) - self.c_leg_Kd[i] * q_dot
  581 |                 if i in [2, 7]: tau += c_tau_pitch
  582 |                 elif i in [4, 9]: tau += c_tau_sag_ank
  583 |                 elif i in [3, 8]: tau += c_tau_height_knee
  584 |                 elif i in [1, 6]: tau += (c_tau_lat_roll if i == 1 else -c_tau_lat_roll)
  585 |                 elif i in [0, 5]: tau += c_tau_yaw
  586 |                 self.data.ctrl[a_id] = np.clip(tau, -250.0, 250.0)
  587 | 
  588 |             # 4. Batter Upper Body PD (Torso uncoiling + 2-handed grip)
  589 |             for i, a_id in enumerate(self.b_upper_act_ids):
  590 |                 adr = self.b_upper_qpos_adrs[i]
  591 |                 q_cur = self.data.qpos[adr]
  592 |                 q_dot = self.data.qvel[self.b_upper_qvel_adrs[i]]
  593 |                 tau = self.b_upper_Kp[i] * (b_upper_cmd[i] - q_cur) - self.b_upper_Kd[i] * q_dot
  594 |                 self.data.ctrl[a_id] = np.clip(tau, -200.0, 200.0)
  595 | 
  596 |             # 5. Batter Legs: Planted Lead Foot Grounding & Dynamic Weight Transfer
  597 |             l_foot_z = self.data.xpos[self.b_left_ankle_id][2] - 0.065
  598 |             l_foot_vz = self.data.qvel[self.b_left_ankle_dof]
  599 |             # Ground-spring: keep left foot planted, but don't over-constrain during swing
  600 |             # Only activate if foot is actually off the ground (l_foot_z > 0)
  601 |             tau_plant_knee = -np.clip(4000.0 * max(0.0, l_foot_z) + 80.0 * max(0.0, l_foot_vz), 0.0, 120.0)
  602 |             tau_plant_ank = -np.clip(1500.0 * max(0.0, l_foot_z), 0.0, 60.0)
  603 | 
  604 |             p_x = self.data.qpos[self.b_pelvis_qpos_adr]
  605 |             p_y = self.data.qpos[self.b_pelvis_qpos_adr + 1]
  606 |             v_x = self.data.qvel[self.b_pelvis_qvel_adr]
  607 |             v_y = self.data.qvel[self.b_pelvis_qvel_adr + 1]
  608 |             w_z = self.data.qvel[self.b_pelvis_qvel_adr + 5]
  609 | 
  610 |             y_shift = shift * 0.06 if self.swing_triggered else 0.00
  611 |             tau_x_ank = np.clip(500.0 * (p_x - self.b_pelvis_x_target) + 50.0 * v_x, -35.0, 35.0)
  612 |             tau_x_hip = np.clip(400.0 * (p_x - self.b_pelvis_x_target) + 40.0 * v_x, -50.0, 50.0)
  613 |             tau_y_shift = np.clip(600.0 * ((self.b_pelvis_y_target + y_shift) - p_y) - 60.0 * v_y, -60.0, 60.0)
  614 |             tau_yaw = np.clip(80.0 * w_z, -50.0, 50.0)
  615 | 
  616 |             for i, a_id in enumerate(self.b_leg_act_ids):
  617 |                 adr = self.b_leg_qpos_adrs[i]
  618 |                 q_cur = self.data.qpos[adr]
  619 |                 q_dot = self.data.qvel[self.b_leg_qvel_adrs[i]]
  620 |                 cmd = b_leg_curr[i]
  621 |                 if i in [4, 9]:
  622 |                     cmd += dweight_shift
  623 |                 tau = self.b_leg_Kp[i] * (cmd - q_cur) - self.b_leg_Kd[i] * q_dot
  624 |                 if i == 3:
  625 |                     tau += tau_plant_knee
  626 |                 elif i == 4:
  627 |                     tau += tau_plant_ank + tau_x_ank
  628 |                 elif i == 9:
  629 |                     tau += tau_x_ank
  630 |                 elif i in [2, 7]:
  631 |                     tau += tau_x_hip + (tau_y_shift if i == 7 else -tau_y_shift * 0.5)
  632 |                 elif i in [0, 5]:
  633 |                     tau += tau_yaw
  634 |                 self.data.ctrl[a_id] = np.clip(tau, -250.0, 250.0)
  635 | 
  636 |             mujoco.mj_step(self.model, self.data)
  637 | 
  638 |         c_z = float(self.data.qpos[self.c_pelvis_qpos_adr + 2])
  639 |         if c_z < 0.45 or c_z > 0.90:
  640 |             self.catcher_fallen = True
  641 | 
  642 |         b_z = float(self.data.qpos[self.b_pelvis_qpos_adr + 2])
  643 |         if b_z < 0.50 or b_z > 1.15:
  644 |             self.batter_fallen = True
  645 | 
  646 |         # Reward formulation
  647 |         reward = 0.0
  648 |         sweet_pos = self.data.site_xpos[self.sweet_spot_id]
  649 |         ball_p = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  650 |         d_sw = float(np.linalg.norm(ball_p - sweet_pos))
  651 | 
  652 |         reward += 3.0 * np.exp(-10.0 * (d_sw ** 2))
  653 | 
  654 |         if self.is_hit:
  655 |             reward += 25.0
  656 |             reward += 0.5 * (self.exit_velocity / 3.6)
  657 |             if self.is_fair:
  658 |                 reward += 15.0
  659 | 
  660 |         if not self.batter_fallen:
  661 |             reward += 1.0
  662 |         else:
  663 |             reward -= 25.0
  664 | 
  665 |         # Reward lead foot staying planted and hands together
  666 |         has_l_contact = any(
  667 |             self.model.geom_bodyid[self.data.contact[c_idx].geom1] == self.b_left_ankle_id or
  668 |             self.model.geom_bodyid[self.data.contact[c_idx].geom2] == self.b_left_ankle_id
  669 |             for c_idx in range(self.data.ncon)
  670 |         )
  671 |         cur_l_lift = 0.0 if has_l_contact else max(0.0, float(self.data.xpos[self.b_left_ankle_id][2] - 0.075))
  672 |         cur_h_dist = float(np.linalg.norm(self.data.site_xpos[self.b_l_hand_grip_id] - self.data.site_xpos[self.bat_grip_left_id]))
  673 |         reward += 3.5 * np.exp(-50.0 * (cur_l_lift ** 2))   # strong penalty when left foot lifts
  674 |         reward += 2.0 * np.exp(-50.0 * (cur_h_dist ** 2))   # hands-together reward
  675 | 
  676 |         if self.catcher_caught and not self.is_hit:
  677 |             reward += 8.0
  678 | 
  679 |         # Catcher stability reward: penalize drift from ideal squat position
  680 |         c_drift = float(np.linalg.norm([
  681 |             self.data.qpos[self.c_pelvis_qpos_adr] - self.c_pelvis_x_target,
  682 |             self.data.qpos[self.c_pelvis_qpos_adr + 1] - self.c_pelvis_y_target,
  683 |             self.data.qpos[self.c_pelvis_qpos_adr + 2] - self.c_pelvis_z_target
  684 |         ]))
  685 |         reward += 2.0 * np.exp(-20.0 * (c_drift ** 2))   # squat rock-solid bonus
  686 | 
  687 |         if self.catcher_fallen:
  688 |             reward -= 20.0   # heavy fall penalty
  689 | 
  690 | 
  691 |         terminated = False
  692 |         ball_y = self.data.qpos[self.ball_qpos_adr + 1]
  693 |         if self.batter_fallen or self.catcher_fallen:
  694 |             terminated = True
  695 |         elif self.is_hit and self.current_step >= (self.contact_step + 12):
  696 |             terminated = True
  697 |         elif not self.is_hit and (self.catcher_caught or ball_y < -1.10):
  698 |             terminated = True
  699 |         elif self.current_step >= self.max_steps:
  700 |             terminated = True
  701 | 
  702 |         info = {
  703 |             "pitch_type": self.pitch_name,
  704 |             "pitch_speed_kmh": self.pitch_speed * 3.6,
  705 |             "is_strike": self.is_strike,
  706 |             "is_hit": self.is_hit,
  707 |             "is_fair": self.is_fair,
  708 |             "sweet_spot_error_cm": self.sweet_spot_error * 100.0 if self.is_hit else d_sw * 100.0,
  709 |             "exit_velocity_kmh": self.exit_velocity,
  710 |             "exit_heading_deg": self.exit_heading,
  711 |             "batter_fallen": self.batter_fallen,
  712 |             "catcher_fallen": self.catcher_fallen,
  713 |             "catcher_caught": self.catcher_caught,
  714 |             "batter_pelvis_z": b_z,
  715 |             "catcher_pelvis_z": c_z,
  716 |             "plate_cross_x": self.plate_cross_x,
  717 |             "plate_cross_z": self.plate_cross_z,
  718 |             "left_foot_lift_cm": cur_l_lift * 100.0,
  719 |             "hand_distance_cm": cur_h_dist * 100.0,
  720 |             "torso_rotation_deg": float(np.degrees(self.data.qpos[self.b_upper_qpos_adrs[0]])),
  721 |             "catcher_drift_cm": c_drift * 100.0
  722 |         }
  723 | 
  724 |         return self._get_obs(), reward, terminated, False, info
  725 | 
  726 |     def render(self, camera_name="duel_broadcast_cam"):
  727 |         if self.renderer is None:
  728 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  729 |         cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)
  730 |         if cam_id < 0:
  731 |             cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "duel_broadcast_cam")
  732 |         self.renderer.update_scene(self.data, camera=cam_id)
  733 |         return self.renderer.render()
  734 | 
  735 |     def close(self):
  736 |         if self.renderer is not None:
  737 |             self.renderer.close()
````
