# baseball/cognitive_ai/envs/breaking_ball_env.py

원본: [cognitive_ai/envs/breaking_ball_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/breaking_ball_env.py)

SHA256: `b9f69eb3d23905c4cbd11588efa30cd86c8ede7a689af0d636e8d76a2e41ee7b`

전체 251행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BreakingBallEnv` | ClassDef | 6 | 251 |
| `__init__` | FunctionDef | 13 | 55 |
| `reset` | FunctionDef | 57 | 125 |
| `step` | FunctionDef | 127 | 212 |
| `_update_swing_kinematics` | FunctionDef | 214 | 225 |
| `_check_contact` | FunctionDef | 227 | 233 |
| `_get_obs` | FunctionDef | 235 | 247 |
| `close` | FunctionDef | 249 | 251 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | from gymnasium import spaces
    3 | import mujoco
    4 | import numpy as np
    5 | 
    6 | class BreakingBallEnv(gym.Env):
    7 |     """
    8 |     Phase 1-D: Breaking Ball & 3D Swing Environment
    9 |     - Pitches: Fastball (직구), Slider (슬라이더), Curveball (커브) + Inside/Outside courses
   10 |     - Observation (9-dim): [x, y, z, vx, vy, vz, t_remain, z_zone, x_zone]
   11 |     - Action (3-dim): [swing_trigger, target_z_delta, target_x_yaw]
   12 |     """
   13 |     def __init__(self, xml_path="shared_assets/h1_baseball.xml", render_mode=None):
   14 |         super().__init__()
   15 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   16 |         self.data = mujoco.MjData(self.model)
   17 |         
   18 |         # 9-dim Observation
   19 |         self.observation_space = spaces.Box(low=-100.0, high=100.0, shape=(9,), dtype=np.float32)
   20 |         
   21 |         # 3-dim Action: [trigger, target_z_delta (height), target_x_yaw (course)]
   22 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
   23 |         
   24 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   25 |         self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   26 |         self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   27 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   28 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   29 |         
   30 |         self.joint_names = [
   31 |             "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
   32 |             "left_hip_roll", "left_hip_pitch", "left_knee", "right_hip_roll", "right_hip_pitch", "right_knee"
   33 |         ]
   34 |         self.qpos_adrs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.joint_names]
   35 |         
   36 |         # Base Keyframes [torso, rs_p, rs_r, rs_y, r_elbow, l_hr, l_hp, l_k, r_hr, r_hp, r_k]
   37 |         self.base_keyframes = np.array([
   38 |             [-0.5, -1.0, 0.0, 0.5, 1.5,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stance
   39 |             [-1.0, -1.2, 0.0, 0.8, 2.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Load
   40 |             [0.0, -0.5, 0.0, 0.0, 1.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stride
   41 |             [1.5, 0.5, 0.0, -0.5, 0.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Contact
   42 |             [2.0, 1.0, 0.0, -1.0, 1.5,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8]  # Follow-through
   43 |         ])
   44 |         
   45 |         self.render_mode = render_mode
   46 |         if render_mode == "human":
   47 |             from mujoco import viewer
   48 |             self.viewer = viewer.launch_passive(self.model, self.data)
   49 |         else:
   50 |             self.viewer = None
   51 |             
   52 |         self.frame_skip = 4
   53 |         self.max_steps = 60
   54 |         self.current_step = 0
   55 |         self.pitch_type = "FASTBALL"
   56 | 
   57 |     def reset(self, seed=None, options=None):
   58 |         super().reset(seed=seed)
   59 |         mujoco.mj_resetData(self.model, self.data)
   60 |         
   61 |         self.swing_active = False
   62 |         self.swing_progress = 0.0
   63 |         self.swing_duration_frames = 24
   64 |         self.has_contacted = False
   65 |         self.trigger_ball_y = -999.0
   66 |         self.trigger_t_remain = -999.0
   67 |         self.trigger_z_zone = 0.0
   68 |         self.trigger_x_zone = 0.0
   69 |         self.current_keyframes = self.base_keyframes.copy()
   70 |         self.current_step = 0
   71 |         self.min_dist = 999.0
   72 |         
   73 |         self.model.body_mass[self.ball_body_id] = 0.145
   74 |         
   75 |         # Random pitch selection: 0: FASTBALL, 1: SLIDER, 2: CURVE
   76 |         pitch_idx = np.random.choice([0, 1, 2], p=[0.4, 0.35, 0.25])
   77 |         dist = 12.0 # 12 meters pitching distance
   78 |         
   79 |         # Target arrival coordinates at home plate (y = 0.20m)
   80 |         x_target = np.random.uniform(-0.12, 0.12) # Inside to Outside
   81 |         z_target = np.random.uniform(0.68, 0.95)  # Low to High
   82 |         
   83 |         if pitch_idx == 0:
   84 |             self.pitch_type = "FASTBALL"
   85 |             vy = np.random.uniform(-18.0, -16.5) # ~62 km/h
   86 |             z0 = 1.6
   87 |             x0 = 0.0
   88 |             t_flight = (dist - 0.20) / abs(vy)
   89 |             drop = 0.5 * 9.81 * (t_flight ** 2)
   90 |             vz = (z_target + drop - z0) / t_flight
   91 |             vx = (x_target - x0) / t_flight
   92 |             self.extra_acc = np.array([0.0, 0.0, 0.0])
   93 |         elif pitch_idx == 1:
   94 |             self.pitch_type = "SLIDER"
   95 |             vy = np.random.uniform(-15.5, -14.5) # ~54 km/h
   96 |             z0 = 1.6
   97 |             x0 = -0.10
   98 |             t_flight = (dist - 0.20) / abs(vy)
   99 |             drop = 0.5 * 9.81 * (t_flight ** 2)
  100 |             vz = (z_target + drop - z0) / t_flight
  101 |             # Lateral acceleration break
  102 |             lat_acc = np.random.uniform(2.5, 4.0)
  103 |             vx = (x_target - x0 - 0.5 * lat_acc * (t_flight ** 2)) / t_flight
  104 |             self.extra_acc = np.array([lat_acc, 0.0, 0.0])
  105 |         else:
  106 |             self.pitch_type = "CURVE"
  107 |             vy = np.random.uniform(-13.5, -12.5) # ~47 km/h
  108 |             z0 = 1.8
  109 |             x0 = 0.08
  110 |             t_flight = (dist - 0.20) / abs(vy)
  111 |             # Extra 12-6 drop acceleration
  112 |             drop_acc = 3.5
  113 |             lat_acc = -1.5
  114 |             drop = 0.5 * (9.81 + drop_acc) * (t_flight ** 2)
  115 |             vz = (z_target + drop - z0) / t_flight
  116 |             vx = (x_target - x0 - 0.5 * lat_acc * (t_flight ** 2)) / t_flight
  117 |             self.extra_acc = np.array([lat_acc, 0.0, -drop_acc])
  118 |             
  119 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [x0, dist, z0]
  120 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
  121 |         
  122 |         self._update_swing_kinematics(0.0)
  123 |         mujoco.mj_forward(self.model, self.data)
  124 |         
  125 |         return self._get_obs(), {}
  126 | 
  127 |     def step(self, action):
  128 |         swing_trigger = float(action[0])
  129 |         target_z_delta = float(action[1])
  130 |         target_x_yaw = float(action[2])
  131 |         
  132 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  133 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  134 |         t_remain = max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1]))
  135 |         
  136 |         # Trigger swing inside decision zone (t_remain <= 0.25s)
  137 |         if not self.swing_active and swing_trigger > 0.0 and t_remain <= 0.25:
  138 |             self.swing_active = True
  139 |             self.trigger_ball_y = float(ball_pos[1])
  140 |             self.trigger_t_remain = float(t_remain)
  141 |             
  142 |             # Predict intercept coordinates
  143 |             pred_z = float(ball_pos[2] + ball_vel[2] * t_remain - 0.5 * (9.81 - self.extra_acc[2]) * (t_remain ** 2))
  144 |             pred_x = float(ball_pos[0] + ball_vel[0] * t_remain + 0.5 * self.extra_acc[0] * (t_remain ** 2))
  145 |             
  146 |             self.trigger_z_zone = float((pred_z - 0.815) / 0.135)
  147 |             self.trigger_x_zone = float(pred_x / 0.15)
  148 |             
  149 |             # Kinematic adjustments:
  150 |             pitch_adj = -0.75 - target_z_delta * 0.55
  151 |             torso_adj = target_x_yaw * 0.35
  152 |             
  153 |             self.current_keyframes = self.base_keyframes.copy()
  154 |             self.current_keyframes[3, 0] += torso_adj # Contact torso yaw
  155 |             self.current_keyframes[4, 0] += torso_adj # Follow-through torso yaw
  156 |             self.current_keyframes[3, 1] += pitch_adj # Contact shoulder pitch
  157 |             self.current_keyframes[4, 1] += pitch_adj # Follow-through shoulder pitch
  158 |             
  159 |         reward = 0.0
  160 |         
  161 |         for _ in range(self.frame_skip):
  162 |             # Apply breaking ball aerodynamic Magnus acceleration
  163 |             dt = 0.005
  164 |             self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += self.extra_acc * dt
  165 |             
  166 |             if self.swing_active and self.swing_progress < 1.0:
  167 |                 self._update_swing_kinematics(self.swing_progress)
  168 |                 self.swing_progress += 1.0 / self.swing_duration_frames
  169 |                 
  170 |             mujoco.mj_step(self.model, self.data)
  171 |             
  172 |             bat_pos = self.data.geom_xpos[self.bat_geom_id]
  173 |             ball_pos_curr = self.data.geom_xpos[self.ball_geom_id]
  174 |             dist = np.linalg.norm(bat_pos - ball_pos_curr)
  175 |             self.min_dist = min(self.min_dist, dist)
  176 |             
  177 |             if not self.has_contacted and self._check_contact():
  178 |                 self.has_contacted = True
  179 |                 
  180 |         if self.viewer:
  181 |             self.viewer.sync()
  182 |             
  183 |         self.current_step += 1
  184 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  185 |         
  186 |         terminated = False
  187 |         truncated = False
  188 |         
  189 |         if self.has_contacted or ball_pos[1] < -0.3 or ball_pos[2] < 0.1 or (self.swing_active and self.swing_progress >= 1.0):
  190 |             terminated = True
  191 |             if self.has_contacted:
  192 |                 ball_vel_end = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  193 |                 exit_speed = np.linalg.norm(ball_vel_end)
  194 |                 reward += 200.0 + min(exit_speed * 10.0, 50.0)
  195 |             else:
  196 |                 reward -= 50.0 * (self.min_dist ** 2)
  197 |                 if self.swing_active:
  198 |                     # Timing reward
  199 |                     timing_err = abs(self.trigger_t_remain - 0.10)
  200 |                     reward -= min(timing_err * 300.0, 40.0)
  201 |                     # Height & Yaw alignment guidance
  202 |                     height_err = abs(target_z_delta - self.trigger_z_zone)
  203 |                     yaw_err = abs(target_x_yaw - self.trigger_x_zone)
  204 |                     reward -= min(height_err * 20.0, 20.0)
  205 |                     reward -= min(yaw_err * 20.0, 20.0)
  206 |                 else:
  207 |                     reward -= 50.0 # Staring at pitch penalty
  208 |                     
  209 |         if self.current_step >= self.max_steps:
  210 |             truncated = True
  211 |             
  212 |         return self._get_obs(), reward, terminated, truncated, {"pitch_type": self.pitch_type}
  213 | 
  214 |     def _update_swing_kinematics(self, progress):
  215 |         num_kfs = len(self.current_keyframes)
  216 |         scaled = progress * (num_kfs - 1)
  217 |         idx1 = int(np.floor(scaled))
  218 |         idx2 = min(idx1 + 1, num_kfs - 1)
  219 |         t = scaled - idx1
  220 |         angles = (1-t)*self.current_keyframes[idx1] + t*self.current_keyframes[idx2]
  221 |         for i, adr in enumerate(self.qpos_adrs):
  222 |             self.data.qpos[adr] = angles[i]
  223 |             jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, self.joint_names[i])
  224 |             vel_adr = self.model.jnt_dofadr[jnt_id]
  225 |             self.data.qvel[vel_adr] = 0.0
  226 | 
  227 |     def _check_contact(self):
  228 |         for i in range(self.data.ncon):
  229 |             contact = self.data.contact[i]
  230 |             if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \
  231 |                (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
  232 |                 return True
  233 |         return False
  234 | 
  235 |     def _get_obs(self):
  236 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  237 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
  238 |         t_remain = float(max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1])))
  239 |         
  240 |         pred_z = float(ball_pos[2] + ball_vel[2] * t_remain - 0.5 * 9.81 * (t_remain ** 2))
  241 |         pred_x = float(ball_pos[0] + ball_vel[0] * t_remain)
  242 |         
  243 |         z_zone = float((pred_z - 0.815) / 0.135)
  244 |         x_zone = float(pred_x / 0.15)
  245 |         
  246 |         features = np.array([t_remain, z_zone, x_zone], dtype=np.float32)
  247 |         return np.concatenate([ball_pos, ball_vel, features]).astype(np.float32)
  248 | 
  249 |     def close(self):
  250 |         if self.viewer:
  251 |             self.viewer.close()
````
