# bipedal/envs/bipedal_sprint_env.py

원본: [envs/bipedal_sprint_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/envs/bipedal_sprint_env.py)

SHA256: `ed74b14e74e161be6a96bee7398bf38a38b5972a674b45fe49bf3b28b395418c`

전체 552행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BipedalSprintEnv` | ClassDef | 24 | 552 |
| `__init__` | FunctionDef | 27 | 154 |
| `reset` | FunctionDef | 156 | 224 |
| `_get_obs` | FunctionDef | 226 | 260 |
| `step` | FunctionDef | 262 | 542 |
| `render` | FunctionDef | 544 | 548 |
| `close` | FunctionDef | 550 | 552 |

## 전체 원문

````text
    1 | """
    2 | BipedalSprintEnv: Phase 6 Continuous Multi-Step Bipedal Base Running to 1st Base.
    3 | Integrates:
    4 | - 19-DoF Unitree H1 Humanoid with full 6-DoF Free-Floating Base Pelvis.
    5 | - Stage 1: Whole-body bipedal athletic swing and contact (0.0s to 0.52s).
    6 | - Stage 2: Dynamic prop handover of dropped_bat to field turf at release (t = 0.52s).
    7 | - Stage 3: Continuous multi-step bipedal sprint locomotion toward 1st Base (6.5m, 6.5m) (0.52s to 2.50s).
    8 | - Full 50 Hz control loop (frame_skip=10 @ 0.002s timestep).
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
   24 | class BipedalSprintEnv(gym.Env):
   25 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}
   26 | 
   27 |     def __init__(
   28 |         self,
   29 |         xml_path=None,
   30 |         render_mode=None,
   31 |         frame_skip=10,
   32 |         pitch_speed_range=(16.0, 20.0),
   33 |         pitch_dist=7.5,
   34 |     ):
   35 |         super().__init__()
   36 | 
   37 |         if xml_path is None:
   38 |             xml_path = os.path.join(parent_dir, "models", "h1_bipedal_sprint.xml")
   39 | 
   40 |         self.xml_path = xml_path
   41 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   42 |         self.data = mujoco.MjData(self.model)
   43 | 
   44 |         self.render_mode = render_mode
   45 |         self.frame_skip = frame_skip
   46 |         self.dt = self.model.opt.timestep * self.frame_skip  # 0.02s per step
   47 |         self.pitch_speed_range = pitch_speed_range
   48 |         self.pitch_dist = pitch_dist
   49 | 
   50 |         # 1st Base location and unit vector from home plate (-0.75, 0.0)
   51 |         self.target_1b = np.array([6.5, 6.5], dtype=np.float32)
   52 |         self.start_p0 = np.array([-0.75, 0.0], dtype=np.float32)
   53 |         vec_1b = self.target_1b - self.start_p0
   54 |         self.nominal_dist_1b = float(np.linalg.norm(vec_1b))
   55 |         self.u_1b = (vec_1b / self.nominal_dist_1b).astype(np.float32)
   56 |         self.yaw_1b = float(np.arctan2(self.u_1b[1], self.u_1b[0]))  # ~0.731 rad (41.9 deg)
   57 | 
   58 |         # Body and site IDs
   59 |         self.pelvis_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
   60 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   61 |         self.held_bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "held_bat")
   62 |         self.dropped_bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "dropped_bat")
   63 | 
   64 |         self.held_bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "held_bat_barrel")
   65 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   66 |         self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")
   67 | 
   68 |         # Freejoints
   69 |         ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   70 |         self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
   71 |         self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]
   72 | 
   73 |         pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "pelvis_joint")
   74 |         self.pelvis_qpos_adr = self.model.jnt_qposadr[pelvis_jnt_id]
   75 |         self.pelvis_qvel_adr = self.model.jnt_dofadr[pelvis_jnt_id]
   76 | 
   77 |         drop_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "dropped_bat_joint")
   78 |         self.drop_qpos_adr = self.model.jnt_qposadr[drop_jnt_id]
   79 |         self.drop_qvel_adr = self.model.jnt_dofadr[drop_jnt_id]
   80 | 
   81 |         # Actuators
   82 |         self.swing_act_names = ["torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"]
   83 |         self.swing_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.swing_act_names]
   84 |         self.swing_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.swing_act_ids]
   85 |         self.swing_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.swing_act_ids]
   86 | 
   87 |         self.leg_act_names = [
   88 |             "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
   89 |             "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
   90 |         ]
   91 |         self.leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.leg_act_names]
   92 |         self.leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.leg_act_ids]
   93 |         self.leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.leg_act_ids]
   94 | 
   95 |         # Gains
   96 |         self.swing_Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
   97 |         self.swing_Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)
   98 | 
   99 |         self.leg_Kp = np.array([450.0, 450.0, 650.0, 750.0, 350.0, 450.0, 450.0, 650.0, 750.0, 350.0], dtype=np.float32)
  100 |         self.leg_Kd = np.array([35.0,  40.0,  55.0,  65.0,  28.0,  35.0,  40.0,  55.0,  65.0,  28.0], dtype=np.float32)
  101 | 
  102 |         # Athletic batting keyframes
  103 |         self.base_keyframes = np.array([
  104 |             [-0.40, -1.00,  0.00,  0.40,  1.50],
  105 |             [-0.60, -1.15,  0.00,  0.60,  1.70],
  106 |             [-0.10, -0.70, -0.05,  0.20,  1.20],
  107 |             [ 0.50, -0.30, -0.10, -0.10,  0.70],
  108 |             [ 1.15,  0.20, -0.08, -0.40,  0.35],
  109 |             [ 1.70,  0.80,  0.00, -0.70,  1.20]
  110 |         ], dtype=np.float32)
  111 | 
  112 |         # Nominal athletic leg stance (Natural static equilibrium)
  113 |         self.base_leg_q = np.array([
  114 |             0.0,  0.10, -0.18, 0.48, -0.32,  # Left leg
  115 |             0.0, -0.10, -0.18, 0.48, -0.32   # Right leg
  116 |         ], dtype=np.float32)
  117 | 
  118 |         # Action Space (6 dims):
  119 |         # a[0]: dt_trigger timing lead/lag (-0.03 to +0.03s)
  120 |         # a[1]: dz_bat plane height (-0.20 to +0.20rad)
  121 |         # a[2]: dalpha_plane attack tilt (-0.20 to +0.20rad)
  122 |         # a[3]: stride_freq modulation (1.4 to 2.2 Hz)
  123 |         # a[4]: sprint_push_gain (0.8 to 1.4)
  124 |         # a[5]: sprint_steer_yaw (-0.25 to +0.25rad)
  125 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)
  126 | 
  127 |         # Observation Space (44 dims):
  128 |         # ball_pos (3), ball_vel (3), t_remain (1), pelvis_pos (3), pelvis_vel (3),
  129 |         # pelvis_quat (4), pelvis_angvel (3), rel_1b (2), dist_1b (1), heading_err (1),
  130 |         # leg_qpos (10), leg_qvel (10)
  131 |         self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(44,), dtype=np.float32)
  132 | 
  133 |         self.current_step = 0
  134 |         self.max_steps = 85  # 85 * 0.02s = 1.70s (batting 0.52s + sprint 1.18s)
  135 |         self.filtered_action = np.zeros(6, dtype=np.float32)
  136 | 
  137 |         self.swing_triggered = False
  138 |         self.locked_t_trigger = 0.0
  139 |         self.locked_swing_duration = 0.17
  140 |         self.has_contacted = False
  141 |         self.bat_released = False
  142 |         self.contact_step = -1
  143 |         self.release_step = -1
  144 |         self.exit_velocity = 0.0
  145 |         self.exit_azimuth_deg = 0.0
  146 |         self.is_fair_hit = False
  147 |         self.has_fallen = False
  148 |         self.sweet_spot_offset = 0.0
  149 |         self.prev_dist_1b = self.nominal_dist_1b
  150 |         self.max_sprint_dist = 0.0
  151 | 
  152 |         self.renderer = None
  153 |         if self.render_mode in ["rgb_array", "human"]:
  154 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  155 | 
  156 |     def reset(self, seed=None, options=None):
  157 |         super().reset(seed=seed)
  158 |         mujoco.mj_resetData(self.model, self.data)
  159 | 
  160 |         self.current_step = 0
  161 |         self.filtered_action = np.zeros(6, dtype=np.float32)
  162 |         self.swing_triggered = False
  163 |         self.locked_t_trigger = 0.0
  164 |         self.locked_swing_duration = 0.17
  165 |         self.has_contacted = False
  166 |         self.bat_released = False
  167 |         self.contact_step = -1
  168 |         self.release_step = -1
  169 |         self.exit_velocity = 0.0
  170 |         self.exit_azimuth_deg = 0.0
  171 |         self.is_fair_hit = False
  172 |         self.has_fallen = False
  173 |         self.sweet_spot_offset = 0.0
  174 | 
  175 |         # Restore held bat visibility
  176 |         self.model.geom_size[self.held_bat_geom_id] = [0.032, 0.45, 0.0]
  177 |         self.model.geom_rgba[self.held_bat_geom_id, 3] = 1.0
  178 | 
  179 |         # Reset dropped bat in sky before release
  180 |         self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = [0.0, 0.0, 50.0]
  181 |         self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+6] = 0.0
  182 | 
  183 |         # Set 6-DoF Pelvis in batter box at natural equilibrium
  184 |         self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3] = [-0.75, 0.00, 0.92]
  185 |         self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  186 |         self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+6] = 0.0
  187 | 
  188 |         # Set nominal leg stance
  189 |         for i, adr in enumerate(self.leg_qpos_adrs):
  190 |             self.data.qpos[adr] = self.base_leg_q[i]
  191 | 
  192 |         # Set upper body initial keyframe
  193 |         for i, adr in enumerate(self.swing_qpos_adrs):
  194 |             self.data.qpos[adr] = self.base_keyframes[0, i]
  195 | 
  196 |         # Pitch generation
  197 |         pitch_speed = float(self.np_random.uniform(*self.pitch_speed_range))
  198 |         vy = -pitch_speed
  199 |         contact_y = 0.22
  200 |         t_flight = (self.pitch_dist - contact_y) / abs(vy)
  201 |         self.nominal_t_flight = t_flight
  202 | 
  203 |         target_x = float(self.np_random.uniform(0.12, 0.18))
  204 |         target_z = float(self.np_random.uniform(0.54, 0.60))
  205 | 
  206 |         z0 = 0.85
  207 |         drop = 0.5 * 9.81 * (t_flight ** 2)
  208 |         vz = (target_z + drop - z0) / t_flight
  209 | 
  210 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [target_x, self.pitch_dist, z0]
  211 |         self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  212 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, vy, vz]
  213 |         self.data.qvel[self.ball_qvel_adr+3:self.ball_qvel_adr+6] = 0.0
  214 | 
  215 |         mujoco.mj_forward(self.model, self.data)
  216 | 
  217 |         self.nominal_t_trigger = t_flight - 0.145
  218 |         self.nominal_swing_duration = 0.17
  219 | 
  220 |         pelvis_xy = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+2]
  221 |         self.prev_dist_1b = float(np.linalg.norm(self.target_1b - pelvis_xy))
  222 |         self.max_sprint_dist = 0.0
  223 | 
  224 |         return self._get_obs(), {}
  225 | 
  226 |     def _get_obs(self):
  227 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  228 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  229 |         t_remain = max(0.0, (ball_pos[1] - 0.22) / abs(ball_vel[1])) if abs(ball_vel[1]) > 1.0 else 0.0
  230 | 
  231 |         pelvis_pos = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3]
  232 |         pelvis_vel = self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+3]
  233 |         pelvis_quat = self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7]
  234 |         pelvis_angvel = self.data.qvel[self.pelvis_qvel_adr+3:self.pelvis_qvel_adr+6]
  235 | 
  236 |         rel_1b = self.target_1b - pelvis_pos[:2]
  237 |         dist_1b = float(np.linalg.norm(rel_1b))
  238 |         desired_yaw = np.arctan2(rel_1b[1], rel_1b[0])
  239 | 
  240 |         qw, qx, qy, qz = pelvis_quat
  241 |         current_yaw = np.arctan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy*qy + qz*qz))
  242 |         heading_err = float(desired_yaw - current_yaw)
  243 | 
  244 |         leg_qpos = np.array([self.data.qpos[adr] for adr in self.leg_qpos_adrs], dtype=np.float32)
  245 |         leg_qvel = np.array([self.data.qvel[adr] for adr in self.leg_qvel_adrs], dtype=np.float32)
  246 | 
  247 |         obs = np.concatenate([
  248 |             ball_pos,                                           # 3
  249 |             ball_vel,                                           # 3
  250 |             np.array([t_remain], dtype=np.float32),             # 1
  251 |             pelvis_pos,                                         # 3
  252 |             pelvis_vel,                                         # 3
  253 |             pelvis_quat,                                        # 4
  254 |             pelvis_angvel,                                      # 3
  255 |             rel_1b,                                             # 2
  256 |             np.array([dist_1b, heading_err], dtype=np.float32), # 2
  257 |             leg_qpos,                                           # 10
  258 |             leg_qvel                                            # 10
  259 |         ]).astype(np.float32)
  260 |         return obs
  261 | 
  262 |     def step(self, action):
  263 |         self.current_step += 1
  264 |         current_time = self.current_step * self.dt
  265 | 
  266 |         action = np.clip(action, self.action_space.low, self.action_space.high)
  267 |         self.filtered_action = 0.6 * self.filtered_action + 0.4 * action
  268 | 
  269 |         dt_trigger = 0.030 * float(self.filtered_action[0])
  270 |         dz_bat = 0.20 * float(self.filtered_action[1])
  271 |         dalpha_plane = 0.20 * float(self.filtered_action[2])
  272 |         freq_sprint = 1.8 + 0.3 * float(self.filtered_action[3]) # 1.5 to 2.1 Hz
  273 |         push_gain = 1.0 + 0.3 * float(self.filtered_action[4])   # 0.7 to 1.3
  274 |         steer_yaw = 0.20 * float(self.filtered_action[5])
  275 | 
  276 |         # Stage 1: Dynamic Swing Trigger (around t = 0.30s to 0.45s)
  277 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  278 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  279 | 
  280 |         if not self.swing_triggered and abs(ball_vel[1]) > 2.0 and ball_pos[1] > 0.22:
  281 |             t_rem = (ball_pos[1] - 0.22) / abs(ball_vel[1])
  282 |             lead_needed = 0.145 + dt_trigger
  283 |             if t_rem <= lead_needed:
  284 |                 self.swing_triggered = True
  285 |                 self.locked_t_trigger = current_time
  286 | 
  287 |         # Stage 2: Post-impact Bat Release at t = 0.52s
  288 |         if not self.bat_released and current_time >= 0.52:
  289 |             self.bat_released = True
  290 |             self.release_step = self.current_step
  291 | 
  292 |             # Transfer 6D pose and velocity to dropped_bat freejoint
  293 |             bat_xpos = self.data.xpos[self.held_bat_body_id].copy()
  294 |             bat_xmat = self.data.xmat[self.held_bat_body_id].copy()
  295 |             bat_quat = np.zeros(4)
  296 |             mujoco.mju_mat2Quat(bat_quat, bat_xmat)
  297 | 
  298 |             self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = bat_xpos
  299 |             self.data.qpos[self.drop_qpos_adr+3:self.drop_qpos_adr+7] = bat_quat
  300 | 
  301 |             v6 = np.zeros(6)
  302 |             mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_BODY, self.held_bat_body_id, v6, 0)
  303 |             self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+3] = v6[3:6]
  304 |             self.data.qvel[self.drop_qvel_adr+3:self.drop_qvel_adr+6] = v6[0:3]
  305 | 
  306 |             # Hide held bat geom
  307 |             self.model.geom_size[self.held_bat_geom_id] = [0.0001, 0.0001, 0.0]
  308 |             self.model.geom_rgba[self.held_bat_geom_id, 3] = 0.0
  309 | 
  310 |         # Upper body swing keyframe setup
  311 |         kfs = self.base_keyframes.copy()
  312 |         kfs[3, 1] += dz_bat * 0.6
  313 |         kfs[3, 2] += dalpha_plane * 0.6
  314 |         kfs[4, 1] += dz_bat * 1.0
  315 |         kfs[4, 2] += dalpha_plane * 1.0
  316 |         kfs[5, 1] += dz_bat * 0.5
  317 | 
  318 |         # Substep Physics Loop (10 substeps of 0.002s = 0.02s per env step)
  319 |         for s_idx in range(self.frame_skip):
  320 |             sim_time = current_time + s_idx * self.model.opt.timestep
  321 | 
  322 |             # 1. Upper Body PD
  323 |             if not self.bat_released:
  324 |                 if not self.swing_triggered:
  325 |                     q_arm = kfs[0]
  326 |                 else:
  327 |                     elapsed = sim_time - self.locked_t_trigger
  328 |                     prog = elapsed / self.locked_swing_duration
  329 |                     if prog < 0.20:
  330 |                         w = prog / 0.20
  331 |                         q_arm = (1.0 - w) * kfs[0] + w * kfs[1]
  332 |                     elif prog < 0.45:
  333 |                         w = (prog - 0.20) / 0.25
  334 |                         q_arm = (1.0 - w) * kfs[1] + w * kfs[2]
  335 |                     elif prog < 0.70:
  336 |                         w = (prog - 0.45) / 0.25
  337 |                         q_arm = (1.0 - w) * kfs[2] + w * kfs[3]
  338 |                     elif prog < 0.90:
  339 |                         w = (prog - 0.70) / 0.20
  340 |                         q_arm = (1.0 - w) * kfs[3] + w * kfs[4]
  341 |                     else:
  342 |                         w = min(1.0, (prog - 0.90) / 0.30)
  343 |                         q_arm = (1.0 - w) * kfs[4] + w * kfs[5]
  344 |             else:
  345 |                 # Running posture: Torso aligns towards 1st base, arms in running pump
  346 |                 t_run = sim_time - 0.52
  347 |                 turn_p = min(1.0, t_run / 0.4)
  348 |                 target_yaw = (self.yaw_1b + steer_yaw) * turn_p
  349 |                 arm_phi = 2.0 * np.pi * freq_sprint * t_run
  350 |                 q_arm = np.array([
  351 |                     target_yaw,                  # Torso yaw
  352 |                     0.20 + 0.35 * np.sin(arm_phi),# Right shoulder pitch (running swing)
  353 |                     -0.10,
  354 |                     0.00,
  355 |                     1.20                         # Right elbow bent
  356 |                 ], dtype=np.float32)
  357 | 
  358 |             for i in range(5):
  359 |                 q = self.data.qpos[self.swing_qpos_adrs[i]]
  360 |                 dq = self.data.qvel[self.swing_qvel_adrs[i]]
  361 |                 tau_a = self.swing_Kp[i] * (q_arm[i] - q) - self.swing_Kd[i] * dq
  362 |                 cr = self.model.actuator_ctrlrange[self.swing_act_ids[i]]
  363 |                 self.data.ctrl[self.swing_act_ids[i]] = np.clip(tau_a, cr[0], cr[1])
  364 | 
  365 |             # 2. Leg PD & Ground Reaction Propulsion
  366 |             p_x = self.data.qpos[self.pelvis_qpos_adr]
  367 |             v_x = self.data.qvel[self.pelvis_qvel_adr]
  368 |             w_z = self.data.qvel[self.pelvis_qvel_adr + 5]
  369 | 
  370 |             if not self.bat_released:
  371 |                 # Stage 1: Batting Stance Ground Shear Balance (rock-solid hold at x = -0.75m)
  372 |                 tau_x_ank = np.clip(500.0 * (p_x - (-0.75)) + 50.0 * v_x, -35.0, 35.0)
  373 |                 tau_x_hip = np.clip(400.0 * (p_x - (-0.75)) + 40.0 * v_x, -50.0, 50.0)
  374 |                 tau_yaw = np.clip(80.0 * w_z, -50.0, 50.0)
  375 | 
  376 |                 leg_tgt = self.base_leg_q.copy()
  377 |                 for a in range(10):
  378 |                     jid = self.model.actuator_trnid[self.leg_act_ids[a], 0]
  379 |                     ql = self.data.qpos[self.model.jnt_qposadr[jid]]
  380 |                     dql = self.data.qvel[self.model.jnt_dofadr[jid]]
  381 |                     tau_l = self.leg_Kp[a] * (leg_tgt[a] - ql) - self.leg_Kd[a] * dql
  382 |                     if a in [4, 9]: tau_l += tau_x_ank
  383 |                     elif a in [2, 7]: tau_l += tau_x_hip
  384 |                     elif a in [0, 5]: tau_l += tau_yaw
  385 |                     cr_l = self.model.actuator_ctrlrange[self.leg_act_ids[a]]
  386 |                     self.data.ctrl[self.leg_act_ids[a]] = np.clip(tau_l, cr_l[0], cr_l[1])
  387 |             else:
  388 |                 # Stage 3: Continuous Multi-Step Sprint Locomotion
  389 |                 t_run = sim_time - 0.52
  390 |                 turn_p = min(1.0, t_run / 0.35)
  391 |                 target_yaw = (self.yaw_1b + steer_yaw) * turn_p
  392 | 
  393 |                 # Advance forward smoothly along baseline
  394 |                 v_fwd = min(0.85 * push_gain, 0.60 * t_run)
  395 |                 s_dist = 0.5 * v_fwd * t_run
  396 |                 x_ref = self.start_p0[0] + self.u_1b[0] * s_dist
  397 |                 vx_ref = v_fwd * self.u_1b[0]
  398 | 
  399 |                 # Ground shear drive
  400 |                 tau_x_ank = np.clip(450.0 * (x_ref - p_x) + 45.0 * (vx_ref - v_x), -30.0, 30.0)
  401 |                 tau_x_hip = np.clip(380.0 * (x_ref - p_x) + 38.0 * (vx_ref - v_x), -45.0, 45.0)
  402 | 
  403 |                 # Active yaw steering towards 1st base
  404 |                 qw, qx, qy, qz = self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7]
  405 |                 pelvis_yaw = np.arctan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy*qy + qz*qz))
  406 |                 yaw_err = target_yaw - pelvis_yaw
  407 |                 tau_yaw = np.clip(-120.0 * yaw_err - 20.0 * w_z, -40.0, 40.0)
  408 | 
  409 |                 # Periodic cyclic stride
  410 |                 phase = (t_run * freq_sprint) % 1.0
  411 |                 sw = np.sin(2.0 * np.pi * phase)
  412 |                 cw = np.cos(2.0 * np.pi * phase)
  413 | 
  414 |                 # Torso heading to 1B
  415 |                 leg_tgt = self.base_leg_q.copy()
  416 |                 leg_tgt[0] = target_yaw
  417 |                 leg_tgt[5] = target_yaw
  418 | 
  419 |                 # Lateral roll balance
  420 |                 leg_tgt[1] += 0.03 * cw
  421 |                 leg_tgt[6] += 0.03 * cw
  422 | 
  423 |                 # Hip stride
  424 |                 amp = 0.15 * min(1.0, t_run / 0.30)
  425 |                 leg_tgt[2] -= amp * sw
  426 |                 leg_tgt[7] += amp * sw
  427 | 
  428 |                 # Knee ground clearance
  429 |                 k_amp = 0.20 * min(1.0, t_run / 0.30)
  430 |                 leg_tgt[3] += k_amp * max(0.0, sw)
  431 |                 leg_tgt[8] += k_amp * max(0.0, -sw)
  432 | 
  433 |                 # Height & attitude stabilization
  434 |                 p_z = self.data.qpos[self.pelvis_qpos_adr + 2]
  435 |                 v_z = self.data.qvel[self.pelvis_qvel_adr + 2]
  436 |                 tau_z = np.clip(600.0 * (0.92 - p_z) - 50.0 * v_z, -30.0, 90.0)
  437 | 
  438 |                 pitch_tilt = 2.0 * (qx * qz + qw * qy)
  439 |                 wy = self.data.qvel[self.pelvis_qvel_adr + 4]
  440 |                 tau_pitch = np.clip(-200.0 * pitch_tilt - 20.0 * wy, -30.0, 30.0)
  441 | 
  442 |                 for a in range(10):
  443 |                     jid = self.model.actuator_trnid[self.leg_act_ids[a], 0]
  444 |                     ql = self.data.qpos[self.model.jnt_qposadr[jid]]
  445 |                     dql = self.data.qvel[self.model.jnt_dofadr[jid]]
  446 |                     tau_l = self.leg_Kp[a] * (leg_tgt[a] - ql) - self.leg_Kd[a] * dql
  447 |                     if a in [4, 9]: tau_l += tau_x_ank + 0.5 * tau_pitch
  448 |                     elif a in [2, 7]: tau_l += tau_x_hip + 0.5 * tau_pitch
  449 |                     elif a in [0, 5]: tau_l += tau_yaw
  450 |                     elif a in [3, 8]: tau_l += 0.5 * tau_z
  451 |                     cr_l = self.model.actuator_ctrlrange[self.leg_act_ids[a]]
  452 |                     self.data.ctrl[self.leg_act_ids[a]] = np.clip(tau_l, cr_l[0], cr_l[1])
  453 | 
  454 |             mujoco.mj_step(self.model, self.data)
  455 | 
  456 |             # Contact detection between held bat and ball
  457 |             if not self.has_contacted and not self.bat_released:
  458 |                 for c_idx in range(self.data.ncon):
  459 |                     con = self.data.contact[c_idx]
  460 |                     g1, g2 = con.geom1, con.geom2
  461 |                     if (g1 == self.held_bat_geom_id and g2 == self.ball_geom_id) or (g2 == self.held_bat_geom_id and g1 == self.ball_geom_id):
  462 |                         self.has_contacted = True
  463 |                         self.contact_step = self.current_step
  464 |                         ball_p = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  465 |                         sweet_p = self.data.site_xpos[self.sweet_spot_id]
  466 |                         self.sweet_spot_offset = float(np.linalg.norm(ball_p - sweet_p))
  467 | 
  468 |                         ball_v = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  469 |                         self.exit_velocity = float(np.linalg.norm(ball_v))
  470 |                         self.exit_azimuth_deg = float(np.degrees(np.arctan2(ball_v[0], -ball_v[1])))
  471 |                         if ball_v[1] < 0.0 and abs(self.exit_azimuth_deg) <= 45.0:
  472 |                             self.is_fair_hit = True
  473 | 
  474 |         # State assessment
  475 |         pelvis_pos = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3]
  476 |         pelvis_quat = self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7]
  477 |         pelvis_vel = self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+3]
  478 | 
  479 |         qw, qx, qy, qz = pelvis_quat
  480 |         upright_z = 1.0 - 2.0 * (qx*qx + qy*qy)
  481 | 
  482 |         dist_1b = float(np.linalg.norm(self.target_1b - pelvis_pos[:2]))
  483 |         dist_traveled = float(np.linalg.norm(pelvis_pos[:2] - self.start_p0))
  484 |         self.max_sprint_dist = max(self.max_sprint_dist, dist_traveled)
  485 | 
  486 |         # Fall detection: threshold 0.55m
  487 |         if pelvis_pos[2] < 0.55 or upright_z < 0.55:
  488 |             self.has_fallen = True
  489 | 
  490 |         # Reward formulation
  491 |         reward = 0.0
  492 | 
  493 |         # 1. Contact & Fair Hit Rewards
  494 |         if self.has_contacted and self.current_step == self.contact_step:
  495 |             reward += 10.0
  496 |             sweet_rew = 5.0 * np.exp(-max(0.0, self.sweet_spot_offset - 0.06) / 0.04)
  497 |             reward += sweet_rew
  498 |             if self.is_fair_hit:
  499 |                 reward += 15.0 + 0.5 * (self.exit_velocity * 3.6)
  500 | 
  501 |         # 2. Bat Release Bonus
  502 |         if self.bat_released and self.current_step == self.release_step:
  503 |             reward += 8.0
  504 | 
  505 |         # 3. Sprint Progression Reward
  506 |         if self.bat_released:
  507 |             progress_1b = self.prev_dist_1b - dist_1b
  508 |             reward += 20.0 * max(0.0, progress_1b)
  509 | 
  510 |             # Velocity along 1B baseline
  511 |             v_along_1b = float(np.dot(pelvis_vel[:2], self.u_1b))
  512 |             reward += 2.0 * max(0.0, v_along_1b)
  513 | 
  514 |         # 4. Upright Balance Reward
  515 |         balance_rew = 2.0 * np.exp(-((pelvis_pos[2] - 0.95)**2) / 0.04) * max(0.0, upright_z)
  516 |         reward += balance_rew
  517 | 
  518 |         # Termination
  519 |         terminated = False
  520 |         if self.has_fallen:
  521 |             terminated = True
  522 |             reward -= 50.0
  523 |         elif dist_1b < 0.50:  # Reached 1st base!
  524 |             terminated = True
  525 |             reward += 100.0
  526 | 
  527 |         truncated = self.current_step >= self.max_steps
  528 |         self.prev_dist_1b = dist_1b
  529 | 
  530 |         info = {
  531 |             "contact": self.has_contacted,
  532 |             "fair_hit": self.is_fair_hit,
  533 |             "bat_released": self.bat_released,
  534 |             "has_fallen": self.has_fallen,
  535 |             "pelvis_z": float(pelvis_pos[2]),
  536 |             "dist_to_1b": dist_1b,
  537 |             "dist_traveled": dist_traveled,
  538 |             "exit_speed_kmh": self.exit_velocity * 3.6,
  539 |             "sweet_spot_offset": self.sweet_spot_offset,
  540 |         }
  541 | 
  542 |         return self._get_obs(), float(reward), terminated, truncated, info
  543 | 
  544 |     def render(self, camera_name="run_tracking_cam"):
  545 |         if self.render_mode not in ["rgb_array", "human"]:
  546 |             return None
  547 |         self.renderer.update_scene(self.data, camera=camera_name)
  548 |         return self.renderer.render()
  549 | 
  550 |     def close(self):
  551 |         if self.renderer is not None:
  552 |             self.renderer.close()
````
