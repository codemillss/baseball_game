# bipedal/envs/battery_pitch_catch_env.py

원본: [envs/battery_pitch_catch_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/envs/battery_pitch_catch_env.py)

SHA256: `c344cc7e47595da6c1fe979c229d895c4d986dae99a6234e389e5113f29372e9`

전체 385행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BatteryPitchCatchEnv` | ClassDef | 7 | 385 |
| `__init__` | FunctionDef | 10 | 114 |
| `reset` | FunctionDef | 116 | 173 |
| `_get_obs` | FunctionDef | 175 | 215 |
| `step` | FunctionDef | 217 | 374 |
| `render` | FunctionDef | 376 | 381 |
| `close` | FunctionDef | 383 | 385 |

## 전체 원문

````text
    1 | import os
    2 | import gymnasium as gym
    3 | from gymnasium import spaces
    4 | import numpy as np
    5 | import mujoco
    6 | 
    7 | class BatteryPitchCatchEnv(gym.Env):
    8 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}
    9 | 
   10 |     def __init__(self, render_mode=None):
   11 |         super().__init__()
   12 |         self.render_mode = render_mode
   13 | 
   14 |         model_path = os.path.abspath("models/h1_battery_pitch_catch.xml")
   15 |         if not os.path.exists(model_path):
   16 |             raise FileNotFoundError(f"Model file not found: {model_path}")
   17 | 
   18 |         self.model = mujoco.MjModel.from_xml_path(model_path)
   19 |         self.data = mujoco.MjData(self.model)
   20 | 
   21 |         self.frame_skip = 10
   22 |         self.dt = self.model.opt.timestep * self.frame_skip
   23 | 
   24 |         self.pitch_types = [0, 1, 2]
   25 |         self.pitch_type = 0
   26 |         self.pitch_name = "Fastball"
   27 |         self.pitch_speed = 24.0
   28 |         self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
   29 |         self.actual_release_step = 2
   30 | 
   31 |         self.rho = 1.205
   32 |         self.r_ball = 0.037
   33 |         self.m_ball = 0.145
   34 |         self.A_ball = np.pi * (self.r_ball ** 2)
   35 |         self.Cd = 0.32
   36 |         self.Cl = 0.24
   37 | 
   38 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   39 |         self.ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   40 |         self.ball_qpos_adr = self.model.jnt_qposadr[self.ball_jnt_id]
   41 |         self.ball_qvel_adr = self.model.jnt_dofadr[self.ball_jnt_id]
   42 | 
   43 |         self.p_hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")
   44 |         self.c_mitt_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "c_mitt_site")
   45 |         self.strike_zone_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "strike_zone")
   46 | 
   47 |         self.c_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "c_pelvis_joint")
   48 |         self.c_pelvis_qpos_adr = self.model.jnt_qposadr[self.c_pelvis_jnt_id]
   49 |         self.c_pelvis_qvel_adr = self.model.jnt_dofadr[self.c_pelvis_jnt_id]
   50 | 
   51 |         self.p_act_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
   52 |         self.p_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.p_act_names]
   53 |         self.p_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
   54 | 
   55 |         self.c_leg_act_names = [
   56 |             "c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle",
   57 |             "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle",
   58 |         ]
   59 |         self.c_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.c_leg_act_names]
   60 |         self.c_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.c_leg_act_ids]
   61 |         self.c_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.c_leg_act_ids]
   62 | 
   63 |         self.c_upper_act_names = [
   64 |             "c_torso",
   65 |             "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow",
   66 |             "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"
   67 |         ]
   68 |         self.c_upper_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.c_upper_act_names]
   69 |         self.c_upper_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.c_upper_act_ids]
   70 |         self.c_upper_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.c_upper_act_ids]
   71 | 
   72 |         self.c_leg_Kp = np.array([450.0, 450.0, 650.0, 750.0, 350.0, 450.0, 450.0, 650.0, 750.0, 350.0], dtype=np.float32)
   73 |         self.c_leg_Kd = np.array([35.0,  40.0,  55.0,  65.0,  28.0,  35.0,  40.0,  55.0,  65.0,  28.0], dtype=np.float32)
   74 | 
   75 |         self.c_upper_Kp = np.array([350.0, 150.0, 150.0, 100.0, 80.0, 150.0, 150.0, 100.0, 80.0], dtype=np.float32)
   76 |         self.c_upper_Kd = np.array([30.0,  15.0,  15.0,  10.0,  8.0,  15.0,  15.0,  10.0,  8.0], dtype=np.float32)
   77 | 
   78 |         self.q_squat_legs = np.array([
   79 |             0.00,  0.18, -1.15, 1.88, -0.75,
   80 |             0.00, -0.18, -1.15, 1.88, -0.75
   81 |         ], dtype=np.float32)
   82 | 
   83 |         self.q_squat_upper = np.array([
   84 |             0.00,
   85 |            -0.50, -0.30, -0.30, 0.20,
   86 |            -0.60, -0.20,  0.00, 1.50
   87 |         ], dtype=np.float32)
   88 | 
   89 |         self.p_keyframes = np.array([
   90 |             [ 0.20, -0.20, -0.40,  0.30,  1.00],
   91 |             [-0.50, -1.40, -0.20, -0.20,  0.20],
   92 |             [-0.90, -1.80, -0.60, -0.50,  0.70],
   93 |         ], dtype=np.float32)
   94 | 
   95 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(5,), dtype=np.float32)
   96 |         self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(42,), dtype=np.float32)
   97 | 
   98 |         self.current_step = 0
   99 |         self.max_steps = 45
  100 |         self.is_released = False
  101 |         self.ball_caught = False
  102 |         self.catch_step = -1
  103 |         self.target_pitch_x = 0.0
  104 |         self.target_pitch_z = 0.85
  105 |         self.catcher_fallen = False
  106 |         self.plate_cross_z = 0.0
  107 |         self.plate_cross_x = 0.0
  108 |         self.plate_crossed = False
  109 |         self.is_strike = False
  110 |         self.framing_error = 0.0
  111 | 
  112 |         self.renderer = None
  113 |         if self.render_mode in ["rgb_array", "human"]:
  114 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  115 | 
  116 |     def reset(self, seed=None, options=None):
  117 |         super().reset(seed=seed)
  118 |         mujoco.mj_resetData(self.model, self.data)
  119 | 
  120 |         self.current_step = 0
  121 |         self.is_released = False
  122 |         self.ball_caught = False
  123 |         self.catch_step = -1
  124 |         self.catcher_fallen = False
  125 |         self.plate_crossed = False
  126 |         self.is_strike = False
  127 |         self.framing_error = 0.0
  128 | 
  129 |         for i, adr in enumerate(self.p_qpos_adrs):
  130 |             self.data.qpos[adr] = self.p_keyframes[0, i]
  131 | 
  132 |         self.data.qpos[self.c_pelvis_qpos_adr:self.c_pelvis_qpos_adr+3] = [0.0, -0.95, 0.55]
  133 |         self.data.qpos[self.c_pelvis_qpos_adr+3:self.c_pelvis_qpos_adr+7] = [0.7071068, 0.0, 0.0, 0.7071068]
  134 |         self.data.qvel[self.c_pelvis_qvel_adr:self.c_pelvis_qvel_adr+6] = 0.0
  135 | 
  136 |         for i, adr in enumerate(self.c_leg_qpos_adrs):
  137 |             self.data.qpos[adr] = self.q_squat_legs[i]
  138 | 
  139 |         for i, adr in enumerate(self.c_upper_qpos_adrs):
  140 |             self.data.qpos[adr] = self.q_squat_upper[i]
  141 | 
  142 |         self.pitch_type = int(self.np_random.choice(self.pitch_types))
  143 | 
  144 |         if self.pitch_type == 0:
  145 |             self.pitch_name = "Fastball"
  146 |             self.pitch_speed = float(self.np_random.uniform(23.6, 24.6))
  147 |             self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
  148 |             self.target_pitch_x = float(self.np_random.uniform(-0.12, 0.12))
  149 |             self.target_pitch_z = float(self.np_random.uniform(0.82, 0.94))
  150 |             self.actual_release_step = 2
  151 |         elif self.pitch_type == 1:
  152 |             self.pitch_name = "Slider"
  153 |             self.pitch_speed = float(self.np_random.uniform(21.2, 22.2))
  154 |             self.pitch_spin = np.array([-30.0, 0.0, 150.0], dtype=np.float32)
  155 |             self.target_pitch_x = float(self.np_random.uniform(0.02, 0.15))
  156 |             self.target_pitch_z = float(self.np_random.uniform(0.72, 0.85))
  157 |             self.actual_release_step = 1
  158 |         else:
  159 |             self.pitch_name = "Curveball"
  160 |             self.pitch_speed = float(self.np_random.uniform(19.8, 20.8))
  161 |             self.pitch_spin = np.array([170.0, 0.0, -20.0], dtype=np.float32)
  162 |             self.target_pitch_x = float(self.np_random.uniform(-0.08, 0.08))
  163 |             self.target_pitch_z = float(self.np_random.uniform(0.68, 0.78))
  164 |             self.actual_release_step = 0
  165 | 
  166 |         mujoco.mj_forward(self.model, self.data)
  167 |         hand_pos = self.data.site_xpos[self.p_hand_site_id].copy()
  168 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
  169 |         self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  170 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+6] = 0.0
  171 |         mujoco.mj_forward(self.model, self.data)
  172 | 
  173 |         return self._get_obs(), {}
  174 | 
  175 |     def _get_obs(self):
  176 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  177 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
  178 | 
  179 |         if self.is_released and abs(ball_vel[1]) > 1.0 and ball_pos[1] > -0.90:
  180 |             t_remain = float((ball_pos[1] - (-0.90)) / abs(ball_vel[1]))
  181 |         elif not self.is_released:
  182 |             t_remain = float(10.0 / self.pitch_speed)
  183 |         else:
  184 |             t_remain = 0.0
  185 | 
  186 |         c_pos = self.data.qpos[self.c_pelvis_qpos_adr:self.c_pelvis_qpos_adr+3].copy()
  187 |         c_quat = self.data.qpos[self.c_pelvis_qpos_adr+3:self.c_pelvis_qpos_adr+7].copy()
  188 |         c_vel = self.data.qvel[self.c_pelvis_qvel_adr:self.c_pelvis_qvel_adr+3].copy()
  189 |         c_angvel = self.data.qvel[self.c_pelvis_qvel_adr+3:self.c_pelvis_qvel_adr+6].copy()
  190 | 
  191 |         mitt_pos = self.data.site_xpos[self.c_mitt_site_id].copy()
  192 |         mitt_vel = np.zeros(3, dtype=np.float32)
  193 | 
  194 |         target_pos = np.array([self.target_pitch_x, 0.0, self.target_pitch_z], dtype=np.float32)
  195 | 
  196 |         leg_q = [self.data.qpos[adr] for adr in self.c_leg_qpos_adrs]
  197 |         torso_q = [self.data.qpos[self.c_upper_qpos_adrs[0]]]
  198 |         arm_q = [self.data.qpos[self.c_upper_qpos_adrs[1]], self.data.qpos[self.c_upper_qpos_adrs[4]]]
  199 |         c_joint_q = np.array(leg_q + torso_q + arm_q, dtype=np.float32)
  200 | 
  201 |         obs = np.concatenate([
  202 |             ball_pos,
  203 |             ball_vel,
  204 |             np.array([t_remain], dtype=np.float32),
  205 |             c_pos,
  206 |             c_quat,
  207 |             c_vel,
  208 |             c_angvel,
  209 |             mitt_pos,
  210 |             mitt_vel,
  211 |             target_pos,
  212 |             c_joint_q
  213 |         ]).astype(np.float32)
  214 | 
  215 |         return obs
  216 | 
  217 |     def step(self, action):
  218 |         self.current_step += 1
  219 |         current_time = (self.current_step - 1) * self.dt
  220 | 
  221 |         dx_mitt = float(action[0]) * 0.18
  222 |         dz_mitt = float(action[1]) * 0.18
  223 |         dy_mitt = float(action[2]) * 0.08
  224 |         d_squat_z = float(action[3]) * 0.03
  225 |         d_tilt = float(action[4]) * 0.05
  226 | 
  227 |         if self.current_step < 2:
  228 |             p_pose = self.p_keyframes[0]
  229 |         elif self.current_step < 4:
  230 |             p_pose = self.p_keyframes[1]
  231 |         else:
  232 |             p_pose = self.p_keyframes[2]
  233 | 
  234 |         q_arm_tgt = self.q_squat_upper.copy()
  235 |         # Analytical Jacobian mapping covering the entire strike zone volume:
  236 |         # Torso yaw and shoulder roll control lateral reach (dx)
  237 |         # Shoulder pitch and elbow control vertical reach (dz)
  238 |         q_arm_tgt[0] += -1.8 * dx_mitt
  239 |         q_arm_tgt[1] += -2.5 * dz_mitt + 0.3 * dy_mitt
  240 |         q_arm_tgt[2] += -1.5 * dx_mitt
  241 |         q_arm_tgt[4] += -2.0 * dz_mitt - 0.5 * dy_mitt
  242 | 
  243 |         q_leg_tgt = self.q_squat_legs.copy()
  244 |         q_leg_tgt[2] += -0.3 * d_squat_z
  245 |         q_leg_tgt[3] += 0.6 * d_squat_z
  246 |         q_leg_tgt[7] += -0.3 * d_squat_z
  247 |         q_leg_tgt[8] += 0.6 * d_squat_z
  248 | 
  249 |         for s_idx in range(self.frame_skip):
  250 |             sim_time = current_time + s_idx * self.model.opt.timestep
  251 | 
  252 |             if not self.is_released and self.current_step >= self.actual_release_step:
  253 |                 self.is_released = True
  254 |                 hp_now = self.data.site_xpos[self.p_hand_site_id].copy()
  255 |                 tgt_pt = np.array([self.target_pitch_x, 0.0, self.target_pitch_z], dtype=np.float32)
  256 |                 tf = (hp_now[1] - tgt_pt[1]) / self.pitch_speed
  257 |                 vx_rel = (tgt_pt[0] - hp_now[0]) / tf
  258 |                 vz_rel = (tgt_pt[2] + 0.5 * 9.81 * (tf**2) - hp_now[2]) / tf
  259 | 
  260 |                 for _ in range(3):
  261 |                     p_s = hp_now.copy()
  262 |                     v_s = np.array([vx_rel, -self.pitch_speed, vz_rel], dtype=np.float32)
  263 |                     while p_s[1] > tgt_pt[1]:
  264 |                         vm = np.linalg.norm(v_s)
  265 |                         fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_s
  266 |                         fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_s)
  267 |                         acc = (fd + fm) / self.m_ball + np.array([0, 0, -9.81], dtype=np.float32)
  268 |                         v_s += acc * 0.002
  269 |                         p_s += v_s * 0.002
  270 |                     err_x = tgt_pt[0] - p_s[0]
  271 |                     err_z = tgt_pt[2] - p_s[2]
  272 |                     vx_rel += err_x / tf
  273 |                     vz_rel += err_z / tf
  274 | 
  275 |                 self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hp_now
  276 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx_rel, -self.pitch_speed, vz_rel]
  277 | 
  278 |             if self.is_released and not self.ball_caught:
  279 |                 v_ball = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  280 |                 vm = np.linalg.norm(v_ball)
  281 |                 if vm > 1.0:
  282 |                     fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_ball
  283 |                     fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_ball)
  284 |                     self.data.qfrc_applied[self.ball_qvel_adr:self.ball_qvel_adr+3] = fd + fm
  285 | 
  286 |             # Plate Crossing Check
  287 |             ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  288 |             if not self.plate_crossed and ball_pos[1] <= 0.0:
  289 |                 self.plate_crossed = True
  290 |                 self.plate_cross_x = ball_pos[0]
  291 |                 self.plate_cross_z = ball_pos[2]
  292 |                 if abs(self.plate_cross_x) <= 0.22 and (0.65 <= self.plate_cross_z <= 1.05):
  293 |                     self.is_strike = True
  294 | 
  295 |             # Catch Detection at Catcher Mitt Plane (y <= -0.75m)
  296 |             mitt_pos = self.data.site_xpos[self.c_mitt_site_id]
  297 |             if not self.ball_caught and ball_pos[1] <= (mitt_pos[1] + 0.12):
  298 |                 d_planar = float(np.sqrt((ball_pos[0] - mitt_pos[0])**2 + (ball_pos[2] - mitt_pos[2])**2))
  299 |                 if d_planar <= 0.18:
  300 |                     self.ball_caught = True
  301 |                     self.catch_step = self.current_step
  302 |                     self.framing_error = d_planar
  303 | 
  304 |             if self.ball_caught:
  305 |                 self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = mitt_pos + np.array([0.0, 0.02, 0.0])
  306 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = 0.0
  307 | 
  308 |             # Pitcher control
  309 |             for i, a_id in enumerate(self.p_act_ids):
  310 |                 adr = self.p_qpos_adrs[i]
  311 |                 q_cur = self.data.qpos[adr]
  312 |                 q_dot = self.data.qvel[self.model.jnt_dofadr[self.model.actuator_trnid[a_id, 0]]]
  313 |                 tau = 350.0 * (p_pose[i] - q_cur) - 25.0 * q_dot
  314 |                 self.data.ctrl[a_id] = np.clip(tau, -60.0, 60.0)
  315 | 
  316 |             # Catcher upper body
  317 |             for i, a_id in enumerate(self.c_upper_act_ids):
  318 |                 adr = self.c_upper_qpos_adrs[i]
  319 |                 q_cur = self.data.qpos[adr]
  320 |                 q_dot = self.data.qvel[self.c_upper_qvel_adrs[i]]
  321 |                 tau = self.c_upper_Kp[i] * (q_arm_tgt[i] - q_cur) - self.c_upper_Kd[i] * q_dot
  322 |                 self.data.ctrl[a_id] = np.clip(tau, -40.0, 40.0)
  323 | 
  324 |             # Catcher legs
  325 |             for i, a_id in enumerate(self.c_leg_act_ids):
  326 |                 adr = self.c_leg_qpos_adrs[i]
  327 |                 q_cur = self.data.qpos[adr]
  328 |                 q_dot = self.data.qvel[self.c_leg_qvel_adrs[i]]
  329 |                 tau = self.c_leg_Kp[i] * (q_leg_tgt[i] - q_cur) - self.c_leg_Kd[i] * q_dot
  330 |                 self.data.ctrl[a_id] = np.clip(tau, -200.0, 200.0)
  331 | 
  332 |             mujoco.mj_step(self.model, self.data)
  333 | 
  334 |         # Catcher fall check: only true fall if pelvis drops below ground or flips
  335 |         c_z = self.data.qpos[self.c_pelvis_qpos_adr + 2]
  336 |         if c_z < 0.20 or c_z > 0.95:
  337 |             self.catcher_fallen = True
  338 | 
  339 |         # Reward
  340 |         reward = 0.0
  341 |         mitt_pos = self.data.site_xpos[self.c_mitt_site_id]
  342 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  343 |         d_planar = float(np.sqrt((ball_pos[0] - mitt_pos[0])**2 + (ball_pos[2] - mitt_pos[2])**2))
  344 |         reward += 2.0 * np.exp(-10.0 * (d_planar ** 2))
  345 | 
  346 |         if self.ball_caught:
  347 |             reward += 15.0
  348 | 
  349 |         if self.plate_crossed and self.is_strike:
  350 |             reward += 5.0
  351 | 
  352 |         if not self.catcher_fallen:
  353 |             reward += 0.5
  354 |         else:
  355 |             reward -= 15.0
  356 | 
  357 |         terminated = False
  358 |         ball_y = self.data.qpos[self.ball_qpos_adr + 1]
  359 |         if self.catcher_fallen or self.ball_caught or ball_y < -1.10 or self.current_step >= self.max_steps:
  360 |             terminated = True
  361 | 
  362 |         info = {
  363 |             "pitch_type": self.pitch_name,
  364 |             "pitch_speed_kmh": self.pitch_speed * 3.6,
  365 |             "ball_caught": self.ball_caught,
  366 |             "is_strike": self.is_strike,
  367 |             "framing_error_cm": self.framing_error * 100.0 if self.ball_caught else d_planar * 100.0,
  368 |             "catcher_fallen": self.catcher_fallen,
  369 |             "plate_cross_x": self.plate_cross_x,
  370 |             "plate_cross_z": self.plate_cross_z,
  371 |             "catcher_pelvis_z": c_z
  372 |         }
  373 | 
  374 |         return self._get_obs(), reward, terminated, False, info
  375 | 
  376 |     def render(self):
  377 |         if self.renderer is None:
  378 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  379 |         cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "battery_broadcast_cam")
  380 |         self.renderer.update_scene(self.data, camera=cam_id)
  381 |         return self.renderer.render()
  382 | 
  383 |     def close(self):
  384 |         if self.renderer is not None:
  385 |             self.renderer.close()
````
