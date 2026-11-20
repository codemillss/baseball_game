# baseball/cognitive_ai/envs/soft_toss_env.py

원본: [cognitive_ai/envs/soft_toss_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/soft_toss_env.py)

SHA256: `60156a964455ca199b64c80ba0fe894e7e9720a7924c4f626b663683e8cfd2f3`

전체 195행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `SoftTossEnv` | ClassDef | 6 | 195 |
| `__init__` | FunctionDef | 15 | 58 |
| `reset` | FunctionDef | 60 | 88 |
| `step` | FunctionDef | 90 | 155 |
| `_update_swing_kinematics` | FunctionDef | 157 | 170 |
| `_check_contact` | FunctionDef | 172 | 178 |
| `_get_obs` | FunctionDef | 180 | 191 |
| `close` | FunctionDef | 193 | 195 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | from gymnasium import spaces
    3 | import mujoco
    4 | import numpy as np
    5 | 
    6 | class SoftTossEnv(gym.Env):
    7 |     """
    8 |     Phase 1-B: Soft-Toss Batting Environment (25~30 km/h)
    9 |     - 6m 전방에서 포물선을 그리며 시속 ~28km/h로 날아오는 소프트토스 배팅볼
   10 |     - Observation (6차원): [ball_x, ball_y, ball_z, ball_vx, ball_vy, ball_vz]
   11 |     - Action (2차원): [swing_trigger, target_z_delta]
   12 |       * swing_trigger > 0.0: 스윙 시작 트리거 (타이밍 판단)
   13 |       * target_z_delta [-1, 1]: 타격 높이 조절 (0.65m ~ 0.95m 대응)
   14 |     """
   15 |     def __init__(self, xml_path="shared_assets/h1_baseball.xml", render_mode=None):
   16 |         super().__init__()
   17 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   18 |         self.data = mujoco.MjData(self.model)
   19 |         
   20 |         # Observation (8차원):
   21 |         # [ball_x, ball_y, ball_z, ball_vx, ball_vy, ball_vz, time_to_plate, predicted_z_at_plate]
   22 |         self.observation_space = spaces.Box(low=-50.0, high=50.0, shape=(8,), dtype=np.float32)
   23 |         
   24 |         # Action: [swing_trigger, target_z_delta]
   25 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
   26 |         
   27 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   28 |         self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   29 |         self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   30 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   31 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   32 |         
   33 |         # Humanoid joints to control
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
   57 |         self.max_steps = 45
   58 |         self.current_step = 0
   59 | 
   60 |     def reset(self, seed=None, options=None):
   61 |         super().reset(seed=seed)
   62 |         mujoco.mj_resetData(self.model, self.data)
   63 |         
   64 |         self.swing_active = False
   65 |         self.swing_progress = 0.0
   66 |         self.swing_duration_frames = 24
   67 |         self.has_contacted = False
   68 |         self.trigger_ball_y = -999.0
   69 |         self.current_keyframes = self.base_keyframes.copy()
   70 |         self.current_step = 0
   71 |         self.min_dist = 999.0
   72 |         
   73 |         # Standard baseball mass
   74 |         self.model.body_mass[self.ball_body_id] = 0.145
   75 |         
   76 |         # Soft-toss launch from 4.0m away (28.8 km/h)
   77 |         vy = np.random.uniform(-8.2, -7.8)
   78 |         # Vertical velocity tuned so ball strictly arrives in strike zone (0.68m ~ 0.95m) at home plate
   79 |         vz = np.random.uniform(1.55, 2.05)
   80 |         vx = np.random.uniform(-0.04, 0.04)
   81 |         
   82 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 4.0, 1.0]
   83 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
   84 |         
   85 |         self._update_swing_kinematics(0.0)
   86 |         mujoco.mj_forward(self.model, self.data)
   87 |         
   88 |         return self._get_obs(), {}
   89 | 
   90 |     def step(self, action):
   91 |         swing_trigger = float(action[0])
   92 |         target_z_delta = float(action[1])
   93 |         
   94 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
   95 |         
   96 |         # Start swing if triggered and not active
   97 |         if not self.swing_active and swing_trigger > 0.0:
   98 |             self.swing_active = True
   99 |             self.trigger_ball_y = float(ball_pos[1])
  100 |             pitch_adj = -0.80 - target_z_delta * 0.55
  101 |             self.current_keyframes = self.base_keyframes.copy()
  102 |             self.current_keyframes[3, 1] += pitch_adj # Contact shoulder pitch
  103 |             self.current_keyframes[4, 1] += pitch_adj # Follow-through shoulder pitch
  104 |             
  105 |         reward = 0.0
  106 |         
  107 |         for _ in range(self.frame_skip):
  108 |             if self.swing_active and self.swing_progress < 1.0:
  109 |                 self._update_swing_kinematics(self.swing_progress)
  110 |                 self.swing_progress += 1.0 / self.swing_duration_frames
  111 |                 
  112 |             mujoco.mj_step(self.model, self.data)
  113 |             
  114 |             # Track closest distance
  115 |             bat_pos = self.data.geom_xpos[self.bat_geom_id]
  116 |             ball_pos = self.data.geom_xpos[self.ball_geom_id]
  117 |             dist = np.linalg.norm(bat_pos - ball_pos)
  118 |             self.min_dist = min(self.min_dist, dist)
  119 |             
  120 |             if not self.has_contacted and self._check_contact():
  121 |                 self.has_contacted = True
  122 |                 reward += 100.0  # Big bonus for contact!
  123 |                 
  124 |         if self.viewer:
  125 |             self.viewer.sync()
  126 |             
  127 |         self.current_step += 1
  128 |         
  129 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  130 |         
  131 |         terminated = False
  132 |         truncated = False
  133 |         
  134 |         # End episode when ball passes home plate (y < -0.3) or hits ground or swing finishes
  135 |         if self.has_contacted or ball_pos[1] < -0.3 or ball_pos[2] < 0.1 or (self.swing_active and self.swing_progress >= 1.0):
  136 |             terminated = True
  137 |             if self.has_contacted:
  138 |                 # Big bonus for contact + exit speed
  139 |                 ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  140 |                 exit_speed = np.linalg.norm(ball_vel)
  141 |                 reward += 150.0 + min(exit_speed * 10.0, 50.0)
  142 |             else:
  143 |                 # Dense quadratic distance penalty
  144 |                 reward -= 50.0 * (self.min_dist ** 2)
  145 |                 if self.swing_active:
  146 |                     # Timing guidance: optimal trigger is when ball is at Y ~ 1.20m
  147 |                     timing_err = abs(self.trigger_ball_y - 1.20)
  148 |                     reward -= min(timing_err * 30.0, 30.0)
  149 |                 else:
  150 |                     reward -= 30.0 # Heavy penalty for frozen/no-swing
  151 |                     
  152 |         if self.current_step >= self.max_steps:
  153 |             truncated = True
  154 |             
  155 |         return self._get_obs(), reward, terminated, truncated, {}
  156 | 
  157 |     def _update_swing_kinematics(self, progress):
  158 |         num_kfs = len(self.current_keyframes)
  159 |         scaled = progress * (num_kfs - 1)
  160 |         idx1 = int(np.floor(scaled))
  161 |         idx2 = min(idx1 + 1, num_kfs - 1)
  162 |         t = scaled - idx1
  163 |         
  164 |         current_angles = (1-t)*self.current_keyframes[idx1] + t*self.current_keyframes[idx2]
  165 |         
  166 |         for i, adr in enumerate(self.qpos_adrs):
  167 |             self.data.qpos[adr] = current_angles[i]
  168 |             jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, self.joint_names[i])
  169 |             vel_adr = self.model.jnt_dofadr[jnt_id]
  170 |             self.data.qvel[vel_adr] = 0.0
  171 | 
  172 |     def _check_contact(self):
  173 |         for i in range(self.data.ncon):
  174 |             contact = self.data.contact[i]
  175 |             if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \
  176 |                (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
  177 |                 return True
  178 |         return False
  179 | 
  180 |     def _get_obs(self):
  181 |         # 8-dim State: [X, Y, Z, Vx, Vy, Vz, time_to_plate, predicted_z_at_plate]
  182 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  183 |         ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
  184 |         
  185 |         # Calculate time remaining to home plate (Y = 0.20m)
  186 |         t_remain = float(max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1])))
  187 |         # Calculate expected ball Z height when crossing home plate under gravity
  188 |         pred_z = float(ball_pos[2] + ball_vel[2] * t_remain - 0.5 * 9.81 * (t_remain ** 2))
  189 |         
  190 |         features = np.array([t_remain, pred_z], dtype=np.float32)
  191 |         return np.concatenate([ball_pos, ball_vel, features]).astype(np.float32)
  192 | 
  193 |     def close(self):
  194 |         if self.viewer:
  195 |             self.viewer.close()
````
