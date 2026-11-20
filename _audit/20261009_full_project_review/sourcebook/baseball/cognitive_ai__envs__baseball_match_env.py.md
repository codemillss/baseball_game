# baseball/cognitive_ai/envs/baseball_match_env.py

원본: [cognitive_ai/envs/baseball_match_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/baseball_match_env.py)

SHA256: `4ef6cf357806a284e6940fa2fef64c8b643bab287fcb0c0fe75202ed458ff275`

전체 408행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BaseballMatchEnv` | ClassDef | 7 | 408 |
| `__init__` | FunctionDef | 15 | 106 |
| `set_pkf` | FunctionDef | 70 | 73 |
| `set_bkf` | FunctionDef | 83 | 86 |
| `reset` | FunctionDef | 108 | 151 |
| `_apply_aerodynamics` | FunctionDef | 154 | 172 |
| `step` | FunctionDef | 174 | 300 |
| `_evaluate_outcome` | FunctionDef | 302 | 332 |
| `_check_contact` | FunctionDef | 334 | 340 |
| `_set_pitcher_pose` | FunctionDef | 342 | 345 |
| `_set_batter_pose` | FunctionDef | 347 | 350 |
| `_update_pitcher_kinematics` | FunctionDef | 352 | 361 |
| `_update_batter_kinematics` | FunctionDef | 363 | 372 |
| `get_observations` | FunctionDef | 374 | 408 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | from gymnasium import spaces
    3 | import mujoco
    4 | import numpy as np
    5 | import os
    6 | 
    7 | class BaseballMatchEnv(gym.Env):
    8 |     """
    9 |     Phase 3: Live Pitcher vs Batter Full Match Environment
   10 |     - Two Unitree H1 humanoid robots concurrently active on the field:
   11 |         1. Pitcher Robot (on mound at y = 10.0m)
   12 |         2. Batter Robot (at plate at x = -0.85m, y = 0.0m)
   13 |     - Full match simulation with pitch delivery, swing tracking, contact physics, and hit outcome evaluation.
   14 |     """
   15 |     def __init__(self, xml_path="shared_assets/h1_baseball_match.xml", render_mode=None, is_eval_mode=False):
   16 |         super().__init__()
   17 |         self.is_eval_mode = is_eval_mode
   18 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   19 |         self.data = mujoco.MjData(self.model)
   20 |         
   21 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   22 |         self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   23 |         self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   24 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   25 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   26 |         
   27 |         # Pitcher joints
   28 |         self.p_joint_names = [
   29 |             "p_left_hip_yaw", "p_left_hip_roll", "p_left_hip_pitch", "p_left_knee", "p_left_ankle",
   30 |             "p_right_hip_yaw", "p_right_hip_roll", "p_right_hip_pitch", "p_right_knee", "p_right_ankle",
   31 |             "p_torso",
   32 |             "p_left_shoulder_pitch", "p_left_shoulder_roll", "p_left_shoulder_yaw", "p_left_elbow",
   33 |             "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"
   34 |         ]
   35 |         
   36 |         
   37 |         self.p_valid_indices = []
   38 |         self.p_qpos_adrs = []
   39 |         self.p_qvel_adrs = []
   40 |         for i, n in enumerate(self.p_joint_names):
   41 |             jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
   42 |             if jid != -1:
   43 |                 self.p_valid_indices.append(i)
   44 |                 self.p_qpos_adrs.append(self.model.jnt_qposadr[jid])
   45 |                 self.p_qvel_adrs.append(self.model.jnt_dofadr[jid])
   46 |         
   47 |         # Batter joints
   48 |         self.b_joint_names = [
   49 |             "b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle",
   50 |             "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle",
   51 |             "b_torso",
   52 |             "b_left_shoulder_pitch", "b_left_shoulder_roll", "b_left_shoulder_yaw", "b_left_elbow",
   53 |             "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"
   54 |         ]
   55 |         
   56 |         
   57 |         self.b_valid_indices = []
   58 |         self.b_qpos_adrs = []
   59 |         self.b_qvel_adrs = []
   60 |         for i, n in enumerate(self.b_joint_names):
   61 |             jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
   62 |             if jid != -1:
   63 |                 self.b_valid_indices.append(i)
   64 |                 self.b_qpos_adrs.append(self.model.jnt_qposadr[jid])
   65 |                 self.b_qvel_adrs.append(self.model.jnt_dofadr[jid])
   66 | 
   67 |         
   68 |         # Pitcher Base Keyframes
   69 |         self.p_base_keyframes = np.zeros((6, 19))
   70 |         def set_pkf(idx, **kwargs):
   71 |             for k, v in kwargs.items():
   72 |                 j_idx = self.p_joint_names.index("p_" + k)
   73 |                 self.p_base_keyframes[idx, j_idx] = v
   74 |         set_pkf(0, torso=-1.57, left_elbow=1.5, right_elbow=1.5)
   75 |         set_pkf(1, torso=-1.57, left_hip_pitch=-1.5, left_knee=1.8, left_elbow=1.5, right_elbow=1.5)
   76 |         set_pkf(2, torso=-1.57, left_hip_pitch=-0.5, left_knee=0.2, left_shoulder_pitch=-0.5, left_elbow=0.5, right_shoulder_pitch=-1.0, right_shoulder_roll=-1.0, right_elbow=0.5)
   77 |         set_pkf(3, torso=-0.5, left_hip_pitch=0.0, left_knee=0.2, left_shoulder_pitch=-1.5, left_elbow=0.2, right_shoulder_pitch=-2.0, right_shoulder_roll=-1.5, right_shoulder_yaw=1.0, right_elbow=1.5)
   78 |         set_pkf(4, torso=0.5, left_hip_pitch=0.0, left_knee=0.1, left_shoulder_pitch=1.0, left_elbow=0.5, right_shoulder_pitch=1.5, right_shoulder_roll=-0.2, right_shoulder_yaw=0.0, right_elbow=0.1, right_hip_pitch=0.5)
   79 |         set_pkf(5, torso=1.2, left_hip_pitch=0.0, left_knee=0.3, left_shoulder_pitch=1.5, left_elbow=1.0, right_shoulder_pitch=2.2, right_shoulder_roll=-1.0, right_shoulder_yaw=-0.5, right_elbow=0.5, right_hip_pitch=1.0, right_knee=1.0)
   80 |         
   81 |         # Batter Base Keyframes
   82 |         self.b_base_keyframes = np.zeros((6, 19))
   83 |         def set_bkf(idx, **kwargs):
   84 |             for k, v in kwargs.items():
   85 |                 j_idx = self.b_joint_names.index("b_" + k)
   86 |                 self.b_base_keyframes[idx, j_idx] = v
   87 |         # Stance (Load) - weight on back leg (right knee slightly bent)
   88 |         set_bkf(0, torso=0.5, right_knee=0.3, left_shoulder_pitch=0.2, left_elbow=2.0, right_shoulder_pitch=-0.2, right_elbow=1.8)
   89 |         # Leg Kick / Tap
   90 |         set_bkf(1, torso=0.8, left_hip_pitch=-0.5, left_knee=0.5, right_knee=0.4, left_shoulder_pitch=0.2, left_elbow=2.0, right_shoulder_pitch=-0.2, right_elbow=1.8)
   91 |         # Stride
   92 |         set_bkf(2, torso=0.8, left_hip_pitch=-0.2, left_knee=0.2, right_knee=0.4, left_shoulder_pitch=0.3, left_elbow=1.8, right_shoulder_pitch=-0.3, right_elbow=1.6)
   93 |         # Hip Turn (Torso rotates to -0.5, bat lag - shoulders stay back slightly)
   94 |         set_bkf(3, torso=-0.2, left_hip_pitch=0.0, left_knee=0.1, right_knee=0.2, left_shoulder_pitch=0.5, left_shoulder_roll=-1.0, left_elbow=1.2, right_shoulder_pitch=-0.5, right_elbow=1.0)
   95 |         # Contact
   96 |         set_bkf(4, torso=-1.0, left_hip_pitch=0.0, left_knee=0.0, right_knee=0.1, left_shoulder_pitch=1.5, left_shoulder_roll=-1.5, left_elbow=0.2, right_shoulder_pitch=-1.0, right_elbow=0.2)
   97 |         # Follow Through
   98 |         set_bkf(5, torso=-1.5, left_hip_pitch=0.0, left_knee=0.0, right_knee=0.0, left_shoulder_pitch=2.0, left_shoulder_roll=-0.5, left_elbow=1.5, right_shoulder_pitch=-0.5, right_elbow=1.5)
   99 |         
  100 |         self.frame_skip = 2
  101 |         self.max_steps = 70
  102 |         self.current_step = 0
  103 |         self.render_mode = render_mode
  104 |         self.viewer = None
  105 |         
  106 |         self.reset()
  107 | 
  108 |     def reset(self, seed=None, options=None):
  109 |         super().reset(seed=seed)
  110 |         mujoco.mj_resetData(self.model, self.data)
  111 |         
  112 |         self.current_step = 0
  113 |         self.p_throw_progress = 0.0
  114 |         self.b_swing_progress = 0.0
  115 |         self.b_swing_active = False
  116 |         self.b_swing_duration = 24
  117 |         self.is_released = False
  118 |         self.has_contacted = False
  119 |         self.contact_step = None
  120 |         self.exit_velocity_kmh = 0.0
  121 |         self.batted_distance = 0.0
  122 |         self.pitch_speed_kmh = 0.0
  123 |         self.outcome = "IN_PLAY"
  124 |         
  125 |         # Random target for pitcher in strike zone
  126 |         self.target_x = float(np.random.uniform(-0.12, 0.12))
  127 |         self.target_z = float(np.random.uniform(0.70, 0.93))
  128 |         self.pitch_speed_kmh = 0.0
  129 |         self.outcome = "IN_PLAY"
  130 |         self.target_pitch_type = np.random.choice([0, 1, 2])
  131 |         self.extra_acc = np.array([0.0, 0.0, 0.0])
  132 |         
  133 |         # Wind Physics: random wind between -3.0 and 3.0 m/s in X and Y
  134 |         self.wind_vector = np.array([
  135 |             np.random.uniform(-4.0, 4.0),
  136 |             np.random.uniform(-4.0, 4.0),
  137 |             0.0
  138 |         ])
  139 |         
  140 |         self.data.eq_active[0] = True # Pitcher holds ball
  141 |         
  142 |         self.b_current_keyframes = self.b_base_keyframes.copy()
  143 |         self.p_current_keyframes = self.p_base_keyframes.copy()
  144 |         
  145 |         # Initialize stances
  146 |         self._set_pitcher_pose(self.p_base_keyframes[0])
  147 |         self._set_batter_pose(self.b_base_keyframes[0])
  148 |         self._set_batter_pose(self.b_base_keyframes[0])
  149 |         mujoco.mj_forward(self.model, self.data)
  150 |         
  151 |         return self.get_observations()
  152 | 
  153 | 
  154 |     def _apply_aerodynamics(self):
  155 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  156 |         speed = np.linalg.norm(ball_vel)
  157 |         if speed < 1.0: return
  158 |         
  159 |         c_d = 0.005 
  160 |         F_drag = -c_d * speed * ball_vel
  161 |         
  162 |         F_magnus = np.zeros(3)
  163 |         if hasattr(self, 'target_pitch_type'):
  164 |             c_l = 0.005 * speed
  165 |             if self.target_pitch_type == 0:
  166 |                 F_magnus = np.array([0.0, 0.0, c_l])
  167 |             elif self.target_pitch_type == 1:
  168 |                 F_magnus = np.array([-c_l, 0.0, -c_l*0.5])
  169 |             elif self.target_pitch_type == 2:
  170 |                 F_magnus = np.array([0.0, 0.0, -c_l*1.5])
  171 |                 
  172 |         self.data.xfrc_applied[self.ball_body_id][:3] = F_drag + F_magnus
  173 | 
  174 |     def step(self, pitcher_action, batter_action):
  175 | 
  176 |         """
  177 |         Step both Pitcher AI and Batter AI in the match.
  178 |         pitcher_action: [release_timing, z_aim, x_aim, vel_scale]
  179 |         batter_action: [swing_trigger, z_delta, x_yaw]
  180 |         """
  181 |         # Pitcher Parameter Modulation
  182 |         p_rel_target = 0.60 + 0.15 * float(np.clip(pitcher_action[0], -1.0, 1.0))
  183 |         p_z_aim = float(pitcher_action[1]) * 0.4
  184 |         p_x_aim = float(pitcher_action[2]) * 0.3
  185 |         p_vel_scale = 0.8 + 1.7 * (float(pitcher_action[3]) + 1.0) / 2.0
  186 |         p_total_frames = int(np.clip(16 / p_vel_scale, 8, 24))
  187 |         
  188 |         self.p_current_keyframes = self.p_base_keyframes.copy()
  189 |         self.p_current_keyframes[2:, 10] += p_x_aim
  190 |         self.p_current_keyframes[2:, 15] += p_z_aim
  191 |         self.p_current_keyframes[2:, 16] -= p_x_aim * 0.5
  192 |         
  193 |         # Batter Parameter Modulation
  194 |         b_trigger = float(batter_action[0])
  195 |         b_z_delta = float(batter_action[1])
  196 |         b_x_yaw = float(batter_action[2])
  197 |         
  198 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  199 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  200 |         t_remain = max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1]))
  201 |         
  202 |         # Trigger swing when ball is within strike interception window (t_remain <= 0.070s)
  203 |         if not self.b_swing_active and (b_trigger > 0.0) and t_remain <= 0.080 and self.is_released:
  204 |             self.b_swing_active = True
  205 |             b_pitch_adj = -0.75 - b_z_delta * 0.55
  206 |             b_torso_adj = b_x_yaw * 0.35
  207 |             self.b_current_keyframes = self.b_base_keyframes.copy()
  208 |             self.b_current_keyframes[3, 10] += b_torso_adj
  209 |             self.b_current_keyframes[4, 10] += b_torso_adj
  210 |             self.b_current_keyframes[3, 15] += b_pitch_adj; self.b_current_keyframes[3, 11] -= b_pitch_adj
  211 |             self.b_current_keyframes[4, 15] += b_pitch_adj; self.b_current_keyframes[4, 11] -= b_pitch_adj
  212 |             
  213 |         dt = self.model.opt.timestep
  214 |             
  215 |         for _ in range(self.frame_skip):
  216 |             # 1. Pitcher execution
  217 |             if self.p_throw_progress < 1.0:
  218 |                 self.p_throw_progress += 1.0 / p_total_frames
  219 |                 self._update_pitcher_kinematics(self.p_throw_progress)
  220 |                 
  221 |                 if not self.is_released and self.p_throw_progress >= p_rel_target:
  222 |                     self.is_released = True
  223 |                     self.data.eq_active[0] = False
  224 |                     base_vy = -18.0 * p_vel_scale
  225 |                     base_vz = 2.2 + p_z_aim * 4.0
  226 |                     base_vx = -p_x_aim * 3.5
  227 |                     
  228 |                     if self.target_pitch_type == 0:
  229 |                         self.extra_acc = np.array([0.0, 0.0, 3.0])
  230 |                         base_vy *= 1.1 
  231 |                     elif self.target_pitch_type == 1:
  232 |                         self.extra_acc = np.array([4.5, 0.0, 0.0])
  233 |                         base_vy *= 0.90
  234 |                     else:
  235 |                         self.extra_acc = np.array([-1.5, 0.0, -4.5])
  236 |                         base_vy *= 0.80
  237 |                         
  238 |                     self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [base_vx, base_vy, base_vz]
  239 |                     bvel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  240 |                     self.pitch_speed_kmh = float(np.linalg.norm(bvel) * 3.6)
  241 |                     
  242 |             if self.is_released:
  243 |                 # Apply Magnus effect
  244 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += self.extra_acc * dt
  245 |                 
  246 |                 # Apply aerodynamic drag and wind
  247 |                 bvel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  248 |                 v_rel = bvel - self.wind_vector
  249 |                 speed_rel = np.linalg.norm(v_rel)
  250 |                 
  251 |                 # Drag coefficient for baseball k = 0.0054
  252 |                 drag_acc = -0.0054 * speed_rel * v_rel
  253 |                 self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += drag_acc * dt
  254 |                     
  255 |             # 2. Batter execution
  256 |             if self.b_swing_active and self.b_swing_progress < 1.0:
  257 |                 self._update_batter_kinematics(self.b_swing_progress)
  258 |                 self.b_swing_progress += 1.0 / self.b_swing_duration
  259 |                 
  260 |             # Apply physics
  261 |             if not getattr(self, 'has_hit', False):
  262 |                 self._apply_aerodynamics()
  263 |                 
  264 |             mujoco.mj_step(self.model, self.data)
  265 | 
  266 |             
  267 |             # Check Bat-Ball contact
  268 |             if not self.has_contacted and self._check_contact():
  269 |                 self.has_contacted = True
  270 |                 self.contact_step = self.current_step
  271 |                 bvel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  272 |                 self.exit_velocity_kmh = float(np.linalg.norm(bvel) * 3.6)
  273 |                 
  274 |         self.current_step += 1
  275 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  276 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  277 |         
  278 |         done = False
  279 |         post_contact_limit = 350 if self.is_eval_mode else 20
  280 |         max_limit = 450 if self.is_eval_mode else self.max_steps
  281 |         
  282 |         # Check termination
  283 |         if self.current_step >= max_limit or ball_pos[1] < -0.5:
  284 |             done = True
  285 |         elif ball_pos[2] <= 0.05:
  286 |             done = True
  287 |         elif self.has_contacted and self.current_step > self.contact_step + post_contact_limit:
  288 |             done = True
  289 |             
  290 |         if done:
  291 |             self._evaluate_outcome(ball_pos, ball_vel)
  292 |             
  293 |         return self.get_observations(), done, {
  294 |             "outcome": self.outcome,
  295 |             "has_contacted": self.has_contacted,
  296 |             "pitch_speed_kmh": self.pitch_speed_kmh,
  297 |             "exit_velocity_kmh": self.exit_velocity_kmh,
  298 |             "batted_distance": self.batted_distance,
  299 |             "is_in_strike_zone": getattr(self, "is_in_strike_zone", True)
  300 |         }
  301 | 
  302 |     def _evaluate_outcome(self, ball_pos, ball_vel):
  303 |         if self.has_contacted:
  304 |             # Ball was hit
  305 |             dist = np.sqrt(ball_pos[0]**2 + (ball_pos[1])**2)
  306 |             self.batted_distance = float(dist)
  307 |             
  308 |             is_foul = ball_pos[1] < np.abs(ball_pos[0])
  309 |             
  310 |             if is_foul:
  311 |                 self.outcome = "⚪ FOUL BALL"
  312 |             else:
  313 |                 if dist >= 60.0 and ball_pos[2] > 2.5:
  314 |                     self.outcome = "🔥 OUT OF THE PARK HOME RUN!"
  315 |                 elif dist >= 58.0 and ball_pos[2] <= 2.5:
  316 |                     self.outcome = "💥 WALL-BALL DOUBLE!"
  317 |                 elif dist >= 15.0 and self.exit_velocity_kmh > 40.0:
  318 |                     self.outcome = "💥 BASE HIT!"
  319 |                 else:
  320 |                     self.outcome = "⚡ GROUND OUT / FLY OUT"
  321 |         else:
  322 |             # No contact
  323 |             dist_to_zone = np.sqrt((ball_pos[0] - self.target_x)**2 + (ball_pos[2] - self.target_z)**2)
  324 |             self.is_in_strike_zone = dist_to_zone <= 0.22
  325 |             
  326 |             if self.b_swing_active:
  327 |                 self.outcome = "❌ STRIKE OUT (Swinging)"
  328 |             else:
  329 |                 if self.is_in_strike_zone:
  330 |                     self.outcome = "🎯 CALLED STRIKE"
  331 |                 else:
  332 |                     self.outcome = "⚠️ BALL (Walk)"
  333 | 
  334 |     def _check_contact(self):
  335 |         for i in range(self.data.ncon):
  336 |             contact = self.data.contact[i]
  337 |             if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \
  338 |                (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
  339 |                 return True
  340 |         return False
  341 | 
  342 |     def _set_pitcher_pose(self, angles):
  343 |         for valid_i, qpos_adr, qvel_adr in zip(self.p_valid_indices, self.p_qpos_adrs, self.p_qvel_adrs):
  344 |             self.data.qpos[qpos_adr] = angles[valid_i]
  345 |             self.data.qvel[qvel_adr] = 0.0
  346 |             
  347 |     def _set_batter_pose(self, angles):
  348 |         for valid_i, qpos_adr, qvel_adr in zip(self.b_valid_indices, self.b_qpos_adrs, self.b_qvel_adrs):
  349 |             self.data.qpos[qpos_adr] = angles[valid_i]
  350 |             self.data.qvel[qvel_adr] = 0.0
  351 | 
  352 |     def _update_pitcher_kinematics(self, progress):
  353 |         num_kfs = len(self.p_current_keyframes)
  354 |         scaled = np.clip(progress, 0.0, 1.0) * (num_kfs - 1)
  355 |         idx1 = int(np.floor(scaled))
  356 |         idx2 = min(idx1 + 1, num_kfs - 1)
  357 |         t = scaled - idx1
  358 |         angles = (1-t)*self.p_current_keyframes[idx1] + t*self.p_current_keyframes[idx2]
  359 |         for valid_i, qpos_adr, qvel_adr in zip(self.p_valid_indices, self.p_qpos_adrs, self.p_qvel_adrs):
  360 |             self.data.qpos[qpos_adr] = angles[valid_i]
  361 |             self.data.qvel[qvel_adr] = 0.0
  362 | 
  363 |     def _update_batter_kinematics(self, progress):
  364 |         num_kfs = len(self.b_current_keyframes)
  365 |         scaled = np.clip(progress, 0.0, 1.0) * (num_kfs - 1)
  366 |         idx1 = int(np.floor(scaled))
  367 |         idx2 = min(idx1 + 1, num_kfs - 1)
  368 |         t = scaled - idx1
  369 |         angles = (1-t)*self.b_current_keyframes[idx1] + t*self.b_current_keyframes[idx2]
  370 |         for valid_i, qpos_adr, qvel_adr in zip(self.b_valid_indices, self.b_qpos_adrs, self.b_qvel_adrs):
  371 |             self.data.qpos[qpos_adr] = angles[valid_i]
  372 |             self.data.qvel[qvel_adr] = 0.0
  373 | 
  374 |     def get_observations(self):
  375 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  376 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
  377 |         
  378 |         # Pitcher Obs (16-dim)
  379 |         p_target = np.array([self.target_x, self.target_z], dtype=np.float32)
  380 |         p_rel_state = np.array([1.0 if self.is_released else 0.0, self.p_throw_progress], dtype=np.float32)
  381 |         hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "pitcher_hand_site")
  382 |         hand_pos = self.data.site_xpos[hand_site_id].copy()
  383 |         
  384 |         pitch_type_onehot = np.zeros(3, dtype=np.float32)
  385 |         if hasattr(self, "target_pitch_type"):
  386 |             pitch_type_onehot[self.target_pitch_type] = 1.0
  387 |             
  388 |         pitcher_obs = np.concatenate([
  389 |             p_target, 
  390 |             p_rel_state, 
  391 |             ball_pos, 
  392 |             ball_vel, 
  393 |             hand_pos, 
  394 |             pitch_type_onehot
  395 |         ]).astype(np.float32)
  396 |         
  397 |         # Batter Obs (12-dim)
  398 |         t_remain = float(max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1])))
  399 |         pred_z = float(ball_pos[2] + ball_vel[2] * t_remain - 0.5 * 9.81 * (t_remain ** 2))
  400 |         pred_x = float(ball_pos[0] + ball_vel[0] * t_remain)
  401 |         z_zone = float((pred_z - 0.815) / 0.135)
  402 |         x_zone = float(pred_x / 0.15)
  403 |         features = np.array([t_remain, z_zone, x_zone], dtype=np.float32)
  404 |         
  405 |         # Let's also give batter the pitch type so it can anticipate breaking balls better!
  406 |         batter_obs = np.concatenate([ball_pos, ball_vel, features, pitch_type_onehot]).astype(np.float32)
  407 |         
  408 |         return {"pitcher": pitcher_obs, "batter": batter_obs}
````
