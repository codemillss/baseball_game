# baseball/cognitive_ai/envs/pitching_machine_env.py

원본: [cognitive_ai/envs/pitching_machine_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/pitching_machine_env.py)

SHA256: `0c4f95738ed23598060cadb9d46f82b81710aa5005974ddbcb533afbbf89169c`

전체 224행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `PitchingMachineEnv` | ClassDef | 6 | 224 |
| `__init__` | FunctionDef | 16 | 58 |
| `set_speed` | FunctionDef | 60 | 61 |
| `reset` | FunctionDef | 63 | 117 |
| `step` | FunctionDef | 119 | 186 |
| `_update_swing_kinematics` | FunctionDef | 188 | 199 |
| `_check_contact` | FunctionDef | 201 | 207 |
| `_get_obs` | FunctionDef | 209 | 220 |
| `close` | FunctionDef | 222 | 224 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | from gymnasium import spaces
    3 | import mujoco
    4 | import numpy as np
    5 | 
    6 | class PitchingMachineEnv(gym.Env):
    7 |     """
    8 |     Phase 1-C: Multi-Speed Pitching Machine Environment (30 ~ 80 km/h)
    9 |     - Supports dynamic speed stages:
   10 |       * Stage 1: ~30 km/h (vy = -8.0 m/s, dist = 4.0m)
   11 |       * Stage 2: 50~55 km/h (vy = -14.5 m/s, dist = 10.0m)
   12 |       * Stage 3: 75~80 km/h (vy = -21.5 m/s, dist = 15.0m)
   13 |     - Observation (8-dim): [x, y, z, vx, vy, vz, t_remain, pred_z_at_plate]
   14 |     - Action (2-dim): [swing_trigger, target_z_delta]
   15 |     """
   16 |     def __init__(self, xml_path="shared_assets/h1_baseball.xml", target_speed_kmh=50, render_mode=None):
   17 |         super().__init__()
   18 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   19 |         self.data = mujoco.MjData(self.model)
   20 |         self.target_speed_kmh = target_speed_kmh
   21 |         
   22 |         # 8-dim Observation
   23 |         self.observation_space = spaces.Box(low=-100.0, high=100.0, shape=(8,), dtype=np.float32)
   24 |         
   25 |         # 2-dim Action [trigger, target_z_delta]
   26 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
   27 |         
   28 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   29 |         self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   30 |         self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   31 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   32 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   33 |         
   34 |         self.joint_names = [
   35 |             "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
   36 |             "left_hip_roll", "left_hip_pitch", "left_knee", "right_hip_roll", "right_hip_pitch", "right_knee"
   37 |         ]
   38 |         self.qpos_adrs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.joint_names]
   39 |         
   40 |         # Base Keyframes [torso, rs_p, rs_r, rs_y, r_elbow, l_hr, l_hp, l_k, r_hr, r_hp, r_k]
   41 |         self.base_keyframes = np.array([
   42 |             [-0.5, -1.0, 0.0, 0.5, 1.5,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stance
   43 |             [-1.0, -1.2, 0.0, 0.8, 2.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Load
   44 |             [0.0, -0.5, 0.0, 0.0, 1.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stride
   45 |             [1.5, 0.5, 0.0, -0.5, 0.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Contact
   46 |             [2.0, 1.0, 0.0, -1.0, 1.5,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8]  # Follow-through
   47 |         ])
   48 |         
   49 |         self.render_mode = render_mode
   50 |         if render_mode == "human":
   51 |             from mujoco import viewer
   52 |             self.viewer = viewer.launch_passive(self.model, self.data)
   53 |         else:
   54 |             self.viewer = None
   55 |             
   56 |         self.frame_skip = 4
   57 |         self.max_steps = 55
   58 |         self.current_step = 0
   59 | 
   60 |     def set_speed(self, speed_kmh: int):
   61 |         self.target_speed_kmh = speed_kmh
   62 | 
   63 |     def reset(self, seed=None, options=None):
   64 |         super().reset(seed=seed)
   65 |         mujoco.mj_resetData(self.model, self.data)
   66 |         
   67 |         self.swing_active = False
   68 |         self.swing_progress = 0.0
   69 |         self.swing_duration_frames = 24
   70 |         self.has_contacted = False
   71 |         self.trigger_ball_y = -999.0
   72 |         self.trigger_t_remain = -999.0
   73 |         self.trigger_z_zone = 0.0
   74 |         self.current_keyframes = self.base_keyframes.copy()
   75 |         self.current_step = 0
   76 |         self.min_dist = 999.0
   77 |         
   78 |         self.model.body_mass[self.ball_body_id] = 0.145
   79 |         
   80 |         # Configure pitch parameters according to target_speed_kmh
   81 |         if self.target_speed_kmh <= 35:
   82 |             # 30 km/h: 4m distance, vy = -8.0 m/s
   83 |             dist = 4.0
   84 |             z0 = 1.0
   85 |             vy = np.random.uniform(-8.3, -7.7)
   86 |             t_flight = (dist - 0.20) / abs(vy)
   87 |             drop = 0.5 * 9.81 * (t_flight ** 2)
   88 |             z_target = np.random.uniform(0.68, 0.95)
   89 |             vz = (z_target + drop - z0) / t_flight
   90 |         elif self.target_speed_kmh <= 60:
   91 |             # 50~55 km/h: 10m distance, vy = -14.5 m/s (~52 km/h)
   92 |             dist = 10.0
   93 |             z0 = 1.6
   94 |             vy = np.random.uniform(-15.0, -14.0)
   95 |             t_flight = (dist - 0.20) / abs(vy)
   96 |             drop = 0.5 * 9.81 * (t_flight ** 2)
   97 |             z_target = np.random.uniform(0.68, 0.95)
   98 |             vz = (z_target + drop - z0) / t_flight
   99 |         else:
  100 |             # 75~80 km/h: 15m distance, vy = -21.5 m/s (~77.4 km/h)
  101 |             dist = 15.0
  102 |             z0 = 1.8
  103 |             vy = np.random.uniform(-22.2, -21.0)
  104 |             t_flight = (dist - 0.20) / abs(vy)
  105 |             drop = 0.5 * 9.81 * (t_flight ** 2)
  106 |             z_target = np.random.uniform(0.68, 0.95)
  107 |             vz = (z_target + drop - z0) / t_flight
  108 |             
  109 |         vx = np.random.uniform(-0.03, 0.03)
  110 |         
  111 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, dist, z0]
  112 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
  113 |         
  114 |         self._update_swing_kinematics(0.0)
  115 |         mujoco.mj_forward(self.model, self.data)
  116 |         
  117 |         return self._get_obs(), {}
  118 | 
  119 |     def step(self, action):
  120 |         swing_trigger = float(action[0])
  121 |         target_z_delta = float(action[1])
  122 |         
  123 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  124 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  125 |         t_remain = max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1]))
  126 |         
  127 |         # Trigger swing only when ball enters decision zone (t_remain <= 0.25s)
  128 |         if not self.swing_active and swing_trigger > 0.0 and t_remain <= 0.25:
  129 |             self.swing_active = True
  130 |             self.trigger_ball_y = float(ball_pos[1])
  131 |             self.trigger_t_remain = float(t_remain)
  132 |             pred_z = float(ball_pos[2] + ball_vel[2] * t_remain - 0.5 * 9.81 * (t_remain ** 2))
  133 |             self.trigger_z_zone = float((pred_z - 0.815) / 0.135)
  134 |             pitch_adj = -0.80 - target_z_delta * 0.55
  135 |             self.current_keyframes = self.base_keyframes.copy()
  136 |             self.current_keyframes[3, 1] += pitch_adj
  137 |             self.current_keyframes[4, 1] += pitch_adj
  138 |             
  139 |         reward = 0.0
  140 |         
  141 |         for _ in range(self.frame_skip):
  142 |             if self.swing_active and self.swing_progress < 1.0:
  143 |                 self._update_swing_kinematics(self.swing_progress)
  144 |                 self.swing_progress += 1.0 / self.swing_duration_frames
  145 |                 
  146 |             mujoco.mj_step(self.model, self.data)
  147 |             
  148 |             bat_pos = self.data.geom_xpos[self.bat_geom_id]
  149 |             ball_pos_curr = self.data.geom_xpos[self.ball_geom_id]
  150 |             dist = np.linalg.norm(bat_pos - ball_pos_curr)
  151 |             self.min_dist = min(self.min_dist, dist)
  152 |             
  153 |             if not self.has_contacted and self._check_contact():
  154 |                 self.has_contacted = True
  155 |                 
  156 |         if self.viewer:
  157 |             self.viewer.sync()
  158 |             
  159 |         self.current_step += 1
  160 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  161 |         
  162 |         terminated = False
  163 |         truncated = False
  164 |         
  165 |         if self.has_contacted or ball_pos[1] < -0.3 or ball_pos[2] < 0.1 or (self.swing_active and self.swing_progress >= 1.0):
  166 |             terminated = True
  167 |             if self.has_contacted:
  168 |                 ball_vel_end = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  169 |                 exit_speed = np.linalg.norm(ball_vel_end)
  170 |                 reward += 200.0 + min(exit_speed * 10.0, 50.0)
  171 |             else:
  172 |                 reward -= 50.0 * (self.min_dist ** 2)
  173 |                 if self.swing_active:
  174 |                     # Ideal trigger is strictly t_remain in [0.11s, 0.13s]
  175 |                     timing_err = abs(self.trigger_t_remain - 0.12)
  176 |                     reward -= min(timing_err * 400.0, 50.0)
  177 |                     # Height guidance: align target_z_delta with z_zone
  178 |                     height_err = abs(target_z_delta - self.trigger_z_zone)
  179 |                     reward -= min(height_err * 25.0, 25.0)
  180 |                 else:
  181 |                     reward -= 60.0 # Heavy penalty for looking at strike without swinging
  182 |                     
  183 |         if self.current_step >= self.max_steps:
  184 |             truncated = True
  185 |             
  186 |         return self._get_obs(), reward, terminated, truncated, {}
  187 | 
  188 |     def _update_swing_kinematics(self, progress):
  189 |         num_kfs = len(self.current_keyframes)
  190 |         scaled = progress * (num_kfs - 1)
  191 |         idx1 = int(np.floor(scaled))
  192 |         idx2 = min(idx1 + 1, num_kfs - 1)
  193 |         t = scaled - idx1
  194 |         angles = (1-t)*self.current_keyframes[idx1] + t*self.current_keyframes[idx2]
  195 |         for i, adr in enumerate(self.qpos_adrs):
  196 |             self.data.qpos[adr] = angles[i]
  197 |             jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, self.joint_names[i])
  198 |             vel_adr = self.model.jnt_dofadr[jnt_id]
  199 |             self.data.qvel[vel_adr] = 0.0
  200 | 
  201 |     def _check_contact(self):
  202 |         for i in range(self.data.ncon):
  203 |             contact = self.data.contact[i]
  204 |             if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \
  205 |                (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
  206 |                 return True
  207 |         return False
  208 | 
  209 |     def _get_obs(self):
  210 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  211 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
  212 |         t_remain = float(max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1])))
  213 |         pred_z = float(ball_pos[2] + ball_vel[2] * t_remain - 0.5 * 9.81 * (t_remain ** 2))
  214 |         
  215 |         # Normalized strike zone height coordinate in [-1.0, 1.0]
  216 |         # (0.68m -> -1.0, 0.815m -> 0.0, 0.95m -> +1.0)
  217 |         z_zone = float((pred_z - 0.815) / 0.135)
  218 |         
  219 |         features = np.array([t_remain, z_zone], dtype=np.float32)
  220 |         return np.concatenate([ball_pos, ball_vel, features]).astype(np.float32)
  221 | 
  222 |     def close(self):
  223 |         if self.viewer:
  224 |             self.viewer.close()
````
