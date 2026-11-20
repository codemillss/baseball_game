# bipedal/envs/hit_and_run_env.py

원본: [envs/hit_and_run_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/envs/hit_and_run_env.py)

SHA256: `a7a604582f015b6abd993c5cfa3ac9c57389b84b25d859823a388c123907b608`

전체 454행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `HitAndRunEnv` | ClassDef | 24 | 454 |
| `__init__` | FunctionDef | 27 | 141 |
| `reset` | FunctionDef | 143 | 220 |
| `_get_obs` | FunctionDef | 222 | 256 |
| `step` | FunctionDef | 258 | 444 |
| `render` | FunctionDef | 446 | 450 |
| `close` | FunctionDef | 452 | 454 |

## 전체 원문

````text
    1 | """
    2 | HitAndRunEnv: Phase 4 Hit-and-Run Locomotion Transition for H1 Humanoid.
    3 | Features:
    4 | - Full 6-DoF Free-Floating Pelvis (pelvis_joint).
    5 | - 19-DoF Unitree H1 humanoid model with real motor torque limits.
    6 | - Stage 1: Goal-conditioned athletic bipedal swing and precision contact (100% Phase 3 kinematics).
    7 | - Stage 2: Post-impact bat release via dynamic handover to freejoint dropped_bat (bat drops and tumbles on turf).
    8 | - Stage 3: Dynamic bipedal sprint locomotion toward 1st Base (x=6.5m, y=6.5m).
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
   24 | class HitAndRunEnv(gym.Env):
   25 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}
   26 | 
   27 |     def __init__(
   28 |         self,
   29 |         xml_path=None,
   30 |         render_mode=None,
   31 |         frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz)
   32 |         pitch_speed_range=(14.0, 18.0),
   33 |         pitch_dist=7.5,
   34 |     ):
   35 |         super().__init__()
   36 | 
   37 |         if xml_path is None:
   38 |             xml_path = os.path.join(parent_dir, "models", "h1_hit_and_run.xml")
   39 | 
   40 |         self.xml_path = xml_path
   41 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   42 |         self.data = mujoco.MjData(self.model)
   43 | 
   44 |         self.render_mode = render_mode
   45 |         self.frame_skip = frame_skip
   46 |         self.dt = self.model.opt.timestep * self.frame_skip  # 0.02s
   47 |         self.pitch_speed_range = pitch_speed_range
   48 |         self.pitch_dist = pitch_dist
   49 | 
   50 |         # 1st Base target
   51 |         self.target_1b = np.array([6.5, 6.5], dtype=np.float32)
   52 | 
   53 |         # Bodies, Geoms, Sites
   54 |         self.pelvis_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
   55 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   56 |         self.held_bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "held_bat")
   57 |         self.dropped_bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "dropped_bat")
   58 |         
   59 |         self.held_bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "held_bat_barrel")
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
   72 |         drop_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "dropped_bat_joint")
   73 |         self.drop_qpos_adr = self.model.jnt_qposadr[drop_jnt_id]
   74 |         self.drop_qvel_adr = self.model.jnt_dofadr[drop_jnt_id]
   75 | 
   76 |         # Upper body swing actuators [torso, rsp, rsr, rsy, relb]
   77 |         self.swing_act_names = ["torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"]
   78 |         self.swing_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.swing_act_names]
   79 |         self.swing_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.swing_act_ids]
   80 |         self.swing_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.swing_act_ids]
   81 | 
   82 |         # Leg actuators (10 motors)
   83 |         self.leg_act_names = [
   84 |             "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
   85 |             "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
   86 |         ]
   87 |         self.leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.leg_act_names]
   88 |         self.leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.leg_act_ids]
   89 |         self.leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.leg_act_ids]
   90 | 
   91 |         # Gains
   92 |         self.swing_Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
   93 |         self.swing_Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)
   94 | 
   95 |         self.leg_Kp = np.array([350.0, 400.0, 500.0, 550.0, 250.0, 350.0, 400.0, 500.0, 550.0, 250.0], dtype=np.float32)
   96 |         self.leg_Kd = np.array([30.0,  35.0,  45.0,  50.0,  20.0,  30.0,  35.0,  45.0,  50.0,  20.0], dtype=np.float32)
   97 | 
   98 |         # Athletic batting keyframes
   99 |         self.base_keyframes = np.array([
  100 |             [-0.40, -1.00,  0.00,  0.40,  1.50],
  101 |             [-0.60, -1.15,  0.00,  0.60,  1.70],
  102 |             [-0.10, -0.70, -0.05,  0.20,  1.20],
  103 |             [ 0.50, -0.30, -0.10, -0.10,  0.70],
  104 |             [ 1.15,  0.20, -0.08, -0.40,  0.35],
  105 |             [ 1.70,  0.80,  0.00, -0.70,  1.20]
  106 |         ], dtype=np.float32)
  107 | 
  108 |         # Nominal Leg Stance
  109 |         self.base_leg_q = np.array([
  110 |             0.0, 0.12, -0.35, 0.65, -0.30,  # Left leg
  111 |             0.0,-0.12, -0.35, 0.65, -0.30   # Right leg
  112 |         ], dtype=np.float32)
  113 | 
  114 |         # Action: 6 dims
  115 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)
  116 |         self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(41,), dtype=np.float32)
  117 | 
  118 |         self.current_step = 0
  119 |         self.max_steps = 35  # 35 * 0.02s = 0.70s (pitch + swing + contact + bat drop + sprint launch)
  120 |         self.prev_action = np.zeros(6, dtype=np.float32)
  121 |         self.filtered_action = np.zeros(6, dtype=np.float32)
  122 | 
  123 |         self.swing_triggered = False
  124 |         self.locked_t_trigger = 0.0
  125 |         self.locked_swing_duration = 0.17
  126 |         self.has_contacted = False
  127 |         self.bat_released = False
  128 |         self.contact_step = -1
  129 |         self.release_step = -1
  130 |         self.contact_ball_pos = None
  131 |         self.contact_sweet_pos = None
  132 |         self.exit_velocity = 0.0
  133 |         self.exit_azimuth_deg = 0.0
  134 |         self.is_fair_hit = False
  135 |         self.has_fallen = False
  136 |         self.start_dist_1b = 9.81
  137 |         self.prev_dist_1b = 9.81
  138 | 
  139 |         self.renderer = None
  140 |         if self.render_mode in ["rgb_array", "human"]:
  141 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  142 | 
  143 |     def reset(self, seed=None, options=None):
  144 |         super().reset(seed=seed)
  145 |         mujoco.mj_resetData(self.model, self.data)
  146 | 
  147 |         self.current_step = 0
  148 |         self.prev_action = np.zeros(6, dtype=np.float32)
  149 |         self.filtered_action = np.zeros(6, dtype=np.float32)
  150 |         self.swing_triggered = False
  151 |         self.locked_t_trigger = 0.0
  152 |         self.locked_swing_duration = 0.17
  153 |         self.has_contacted = False
  154 |         self.bat_released = False
  155 |         self.contact_step = -1
  156 |         self.release_step = -1
  157 |         self.contact_ball_pos = None
  158 |         self.contact_sweet_pos = None
  159 |         self.exit_velocity = 0.0
  160 |         self.exit_azimuth_deg = 0.0
  161 |         self.is_fair_hit = False
  162 |         self.has_fallen = False
  163 | 
  164 |         # Restore held bat visibility
  165 |         self.model.geom_size[self.held_bat_geom_id] = [0.032, 0.45, 0.0]
  166 |         self.model.geom_rgba[self.held_bat_geom_id, 3] = 1.0
  167 | 
  168 |         # Reset dropped bat underground
  169 |         self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = [0.0, 0.0, -10.0]
  170 |         self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+6] = 0.0
  171 | 
  172 |         # Set 6-DoF Pelvis in batter box
  173 |         self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3] = [-0.85, 0.00, 0.88]
  174 |         self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  175 |         self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+6] = 0.0
  176 | 
  177 |         # Set nominal leg stance
  178 |         for i, adr in enumerate(self.leg_qpos_adrs):
  179 |             self.data.qpos[adr] = self.base_leg_q[i]
  180 | 
  181 |         # Set upper body initial keyframe
  182 |         for i, adr in enumerate(self.swing_qpos_adrs):
  183 |             self.data.qpos[adr] = self.base_keyframes[0, i]
  184 | 
  185 |         # Draw Goal Condition
  186 |         target_azimuth_deg = self.np_random.uniform(-35.0, 35.0)
  187 |         self.target_azimuth_rad = float(np.radians(target_azimuth_deg))
  188 |         target_launch_deg = self.np_random.uniform(12.0, 32.0)
  189 |         self.target_launch_rad = float(np.radians(target_launch_deg))
  190 |         self.target_exit_vel = float(self.np_random.uniform(10.0, 18.0))
  191 | 
  192 |         # Sample Pitched Ball
  193 |         pitch_speed = self.np_random.uniform(*self.pitch_speed_range)
  194 |         vy = -pitch_speed
  195 |         plate_y_contact = 0.22
  196 |         t_flight = (self.pitch_dist - plate_y_contact) / abs(vy)
  197 |         self.nominal_t_flight = t_flight
  198 | 
  199 |         target_x = self.np_random.uniform(0.06, 0.12)
  200 |         target_z = self.np_random.uniform(0.55, 0.62)
  201 | 
  202 |         z0 = 0.85
  203 |         drop = 0.5 * 9.81 * (t_flight ** 2)
  204 |         vz = (target_z + drop - z0) / t_flight
  205 | 
  206 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [target_x, self.pitch_dist, z0]
  207 |         self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  208 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, vy, vz]
  209 |         self.data.qvel[self.ball_qvel_adr+3:self.ball_qvel_adr+6] = [0.0, 0.0, 0.0]
  210 | 
  211 |         mujoco.mj_forward(self.model, self.data)
  212 | 
  213 |         self.nominal_t_trigger = t_flight - 0.145
  214 |         self.nominal_swing_duration = 0.17
  215 | 
  216 |         pelvis_xy = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+2]
  217 |         self.start_dist_1b = float(np.linalg.norm(self.target_1b - pelvis_xy))
  218 |         self.prev_dist_1b = self.start_dist_1b
  219 | 
  220 |         return self._get_obs(), {}
  221 | 
  222 |     def _get_obs(self):
  223 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  224 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  225 |         t_remain = max(0.0, (ball_pos[1] - 0.20) / abs(ball_vel[1])) if abs(ball_vel[1]) > 1.0 else 0.0
  226 | 
  227 |         pelvis_pos = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3]
  228 |         pelvis_vel = self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+3]
  229 |         pelvis_quat = self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7]
  230 | 
  231 |         rel_1b = self.target_1b - pelvis_pos[:2]
  232 |         dist_1b = float(np.linalg.norm(rel_1b))
  233 |         desired_yaw = np.arctan2(rel_1b[1], rel_1b[0])
  234 | 
  235 |         qw, qx, qy, qz = pelvis_quat
  236 |         current_yaw = np.arctan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy*qy + qz*qz))
  237 |         heading_err = float(desired_yaw - current_yaw)
  238 | 
  239 |         leg_qpos = np.array([self.data.qpos[adr] for adr in self.leg_qpos_adrs], dtype=np.float32)
  240 |         stage_idx = 0.0 if not self.swing_triggered else (1.0 if not self.bat_released else 2.0)
  241 | 
  242 |         obs = np.concatenate([
  243 |             ball_pos,                                    # 3
  244 |             ball_vel,                                    # 3
  245 |             np.array([t_remain], dtype=np.float32),      # 1
  246 |             pelvis_pos,                                  # 3
  247 |             pelvis_vel,                                  # 3
  248 |             pelvis_quat,                                 # 4
  249 |             rel_1b,                                      # 2
  250 |             np.array([dist_1b, heading_err], dtype=np.float32), # 2
  251 |             np.array([stage_idx, 1.0 if self.bat_released else 0.0, 1.0 if self.has_contacted else 0.0], dtype=np.float32), # 3
  252 |             leg_qpos,                                    # 10
  253 |             self.prev_action,                            # 6
  254 |             np.array([float(self.exit_velocity)], dtype=np.float32), # 1
  255 |         ])
  256 |         return obs.astype(np.float32)
  257 | 
  258 |     def step(self, action):
  259 |         action = np.clip(action, -1.0, 1.0).astype(np.float32)
  260 |         self.filtered_action = 0.6 * self.filtered_action + 0.4 * action
  261 | 
  262 |         current_time = self.current_step * self.dt
  263 | 
  264 |         dt_lead_lag = float(self.filtered_action[0]) * 0.030
  265 |         dz_bat = float(self.filtered_action[1]) * 0.08
  266 |         dalpha_plane = float(self.filtered_action[2]) * 0.15
  267 |         dpower_dur = float(self.filtered_action[3]) * 0.02
  268 |         delbow_reach = float(self.filtered_action[4]) * 0.15
  269 |         dweight_shift = float(self.filtered_action[5]) * 0.10
  270 | 
  271 |         if not self.swing_triggered:
  272 |             candidate_trigger = self.nominal_t_trigger + dt_lead_lag
  273 |             if current_time >= candidate_trigger:
  274 |                 self.swing_triggered = True
  275 |                 self.locked_t_trigger = candidate_trigger
  276 |                 self.locked_swing_duration = max(0.12, self.nominal_swing_duration + dpower_dur)
  277 | 
  278 |         # Post-contact bat release handover
  279 |         if self.swing_triggered and not self.bat_released:
  280 |             if (self.has_contacted and self.current_step >= self.contact_step + 4) or (current_time >= self.locked_t_trigger + 0.22):
  281 |                 self.bat_released = True
  282 |                 self.release_step = self.current_step
  283 | 
  284 |                 # Seamless handover to dropped_bat freejoint
  285 |                 self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = self.data.xpos[self.held_bat_body_id]
  286 |                 self.data.qpos[self.drop_qpos_adr+3:self.drop_qpos_adr+7] = self.data.xquat[self.held_bat_body_id]
  287 |                 v6 = np.zeros(6, dtype=np.float64)
  288 |                 mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_BODY, self.held_bat_body_id, v6, 0)
  289 |                 self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+3] = v6[3:6]
  290 |                 self.data.qvel[self.drop_qvel_adr+3:self.drop_qvel_adr+6] = v6[0:3]
  291 | 
  292 |                 # Hide held bat
  293 |                 self.model.geom_size[self.held_bat_geom_id] = [0.0001, 0.0001, 0.0]
  294 |                 self.model.geom_rgba[self.held_bat_geom_id, 3] = 0.0
  295 | 
  296 |         # Trajectory computation
  297 |         kfs = self.base_keyframes.copy()
  298 |         kfs[3, 1] += dz_bat * 0.6
  299 |         kfs[3, 2] += dalpha_plane * 0.6
  300 |         kfs[3, 4] += delbow_reach * 0.6
  301 |         kfs[4, 1] += dz_bat * 1.0
  302 |         kfs[4, 2] += dalpha_plane * 1.0
  303 |         kfs[4, 4] += delbow_reach * 1.0
  304 |         kfs[5, 1] += dz_bat * 0.5
  305 |         kfs[5, 2] += dalpha_plane * 0.5
  306 | 
  307 |         leg_target = self.base_leg_q.copy()
  308 |         if self.swing_triggered and not self.bat_released:
  309 |             leg_target[2] -= dweight_shift
  310 |             leg_target[7] += dweight_shift
  311 |         elif self.bat_released:
  312 |             # Sprint transition modulation: step towards 1st base
  313 |             prog_sprint = min(1.0, (self.current_step - self.release_step) / 10.0)
  314 |             steer = 0.25 * float(self.filtered_action[4])
  315 |             leg_target[0] += (0.20 + steer) * prog_sprint  # Hip yaw towards 1st base
  316 |             leg_target[5] += (0.20 + steer) * prog_sprint
  317 |             leg_target[2] -= 0.15 * prog_sprint # forward stride
  318 |             leg_target[7] += 0.10 * prog_sprint # back leg push-off
  319 | 
  320 |         for _ in range(self.frame_skip):
  321 |             if not self.bat_released:
  322 |                 if not self.swing_triggered:
  323 |                     q_target = kfs[0]
  324 |                 else:
  325 |                     elapsed = current_time - self.locked_t_trigger
  326 |                     prog = elapsed / self.locked_swing_duration
  327 |                     if prog < 0.20:
  328 |                         w = prog / 0.20
  329 |                         q_target = (1.0 - w) * kfs[0] + w * kfs[1]
  330 |                     elif prog < 0.45:
  331 |                         w = (prog - 0.20) / 0.25
  332 |                         q_target = (1.0 - w) * kfs[1] + w * kfs[2]
  333 |                     elif prog < 0.70:
  334 |                         w = (prog - 0.45) / 0.25
  335 |                         q_target = (1.0 - w) * kfs[2] + w * kfs[3]
  336 |                     elif prog < 0.90:
  337 |                         w = (prog - 0.70) / 0.20
  338 |                         q_target = (1.0 - w) * kfs[3] + w * kfs[4]
  339 |                     else:
  340 |                         w = min(1.0, (prog - 0.90) / 0.30)
  341 |                         q_target = (1.0 - w) * kfs[4] + w * kfs[5]
  342 |             else:
  343 |                 # Running posture: Torso aligns towards 1st base, right arm tucks
  344 |                 prog_sprint = min(1.0, (self.current_step - self.release_step) / 10.0)
  345 |                 q_target = np.array([
  346 |                     0.40 * prog_sprint, # Torso towards 1st base
  347 |                     0.20 * prog_sprint,
  348 |                     -0.10,
  349 |                     0.00,
  350 |                     1.20 # Elbow bent for sprint
  351 |                 ], dtype=np.float32)
  352 | 
  353 |             # Apply Upper body PD
  354 |             for i in range(5):
  355 |                 q = self.data.qpos[self.swing_qpos_adrs[i]]
  356 |                 dq = self.data.qvel[self.swing_qvel_adrs[i]]
  357 |                 tau = self.swing_Kp[i] * (q_target[i] - q) - self.swing_Kd[i] * dq
  358 |                 cr = self.model.actuator_ctrlrange[self.swing_act_ids[i]]
  359 |                 self.data.ctrl[self.swing_act_ids[i]] = np.clip(tau, cr[0], cr[1])
  360 | 
  361 |             # Apply Leg PD
  362 |             for a in range(10):
  363 |                 jid = self.model.actuator_trnid[self.leg_act_ids[a], 0]
  364 |                 q = self.data.qpos[self.model.jnt_qposadr[jid]]
  365 |                 dq = self.data.qvel[self.model.jnt_dofadr[jid]]
  366 |                 tau = self.leg_Kp[a] * (leg_target[a] - q) - self.leg_Kd[a] * dq
  367 |                 cr = self.model.actuator_ctrlrange[self.leg_act_ids[a]]
  368 |                 self.data.ctrl[self.leg_act_ids[a]] = np.clip(tau, cr[0], cr[1])
  369 | 
  370 |             mujoco.mj_step(self.model, self.data)
  371 | 
  372 |             # Contact detection between held bat and ball
  373 |             if not self.has_contacted and not self.bat_released:
  374 |                 for c_idx in range(self.data.ncon):
  375 |                     con = self.data.contact[c_idx]
  376 |                     g1, g2 = con.geom1, con.geom2
  377 |                     if (g1 == self.held_bat_geom_id and g2 == self.ball_geom_id) or (g2 == self.held_bat_geom_id and g1 == self.ball_geom_id):
  378 |                         self.has_contacted = True
  379 |                         self.contact_step = self.current_step
  380 |                         self.contact_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  381 |                         self.contact_sweet_pos = self.data.site_xpos[self.sweet_spot_id].copy()
  382 | 
  383 |         self.current_step += 1
  384 |         obs = self._get_obs()
  385 | 
  386 |         pelvis_pos = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3]
  387 |         pelvis_z = pelvis_pos[2]
  388 |         if pelvis_z < 0.65:
  389 |             self.has_fallen = True
  390 | 
  391 |         if self.has_contacted:
  392 |             ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  393 |             self.exit_velocity = float(np.linalg.norm(ball_vel))
  394 |             if ball_vel[1] > 0.10:
  395 |                 self.is_fair_hit = True
  396 |                 self.exit_azimuth_deg = float(np.degrees(np.arctan2(ball_vel[0], ball_vel[1])))
  397 | 
  398 |         curr_dist_1b = float(np.linalg.norm(self.target_1b - pelvis_pos[:2]))
  399 |         dist_traveled = float(self.start_dist_1b - curr_dist_1b)
  400 |         progress_1b = self.prev_dist_1b - curr_dist_1b
  401 |         self.prev_dist_1b = curr_dist_1b
  402 | 
  403 |         terminated = False
  404 |         truncated = False
  405 | 
  406 |         if self.has_fallen:
  407 |             terminated = True
  408 |         elif self.current_step >= self.max_steps:
  409 |             truncated = True
  410 | 
  411 |         # Rewards
  412 |         reward = 0.0
  413 |         # Dynamic balance reward
  414 |         reward += 5.0 * float(np.exp(-15.0 * ((pelvis_z - 0.88) ** 2)))
  415 | 
  416 |         if self.has_fallen:
  417 |             reward -= 40.0
  418 | 
  419 |         if self.has_contacted and self.current_step == self.contact_step + 1:
  420 |             reward += 15.0
  421 |             if self.is_fair_hit:
  422 |                 reward += 12.0
  423 | 
  424 |         if self.bat_released:
  425 |             reward += 25.0 * max(0.0, progress_1b)
  426 |             # Yaw alignment towards 1st base
  427 |             reward += 3.0 * float(np.exp(-5.0 * (obs[18] ** 2)))
  428 | 
  429 |         reward -= 0.005 * float(np.sum(action ** 2))
  430 |         self.prev_action = action.copy()
  431 | 
  432 |         info = {
  433 |             "contact": self.has_contacted,
  434 |             "fair_hit": self.is_fair_hit,
  435 |             "bat_released": self.bat_released,
  436 |             "has_fallen": self.has_fallen,
  437 |             "dist_to_1b": curr_dist_1b,
  438 |             "dist_traveled": dist_traveled,
  439 |             "pelvis_z": float(pelvis_z),
  440 |             "exit_speed_kmh": float(self.exit_velocity * 3.6),
  441 |             "azimuth_deg": float(self.exit_azimuth_deg),
  442 |         }
  443 | 
  444 |         return obs, reward, terminated, truncated, info
  445 | 
  446 |     def render(self, camera_name="run_tracking_cam"):
  447 |         if self.render_mode == "rgb_array" and self.renderer is not None:
  448 |             self.renderer.update_scene(self.data, camera=camera_name)
  449 |             return self.renderer.render()
  450 |         return None
  451 | 
  452 |     def close(self):
  453 |         if self.renderer is not None:
  454 |             self.renderer.close()
````
