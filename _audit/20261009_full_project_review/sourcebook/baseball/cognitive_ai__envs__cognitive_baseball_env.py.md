# baseball/cognitive_ai/envs/cognitive_baseball_env.py

원본: [cognitive_ai/envs/cognitive_baseball_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/cognitive_baseball_env.py)

SHA256: `4df442f4c5fb1faa735894b1f1d85275470c9729739f1e1eabed3df72329be7c`

전체 166행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `CognitiveBaseballEnv` | ClassDef | 7 | 166 |
| `__init__` | FunctionDef | 11 | 58 |
| `reset` | FunctionDef | 60 | 84 |
| `step` | FunctionDef | 86 | 130 |
| `_apply_aerodynamics` | FunctionDef | 132 | 139 |
| `_update_swing_kinematics` | FunctionDef | 141 | 154 |
| `_check_contact` | FunctionDef | 156 | 162 |
| `_get_obs` | FunctionDef | 164 | 166 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | from gymnasium import spaces
    3 | import mujoco
    4 | import numpy as np
    5 | import cv2
    6 | 
    7 | class CognitiveBaseballEnv(gym.Env):
    8 |     """
    9 |     Macro-Action Based Cognitive Baseball Environment (Humanoid Version).
   10 |     """
   11 |     def __init__(self, xml_path="shared_assets/h1_baseball.xml", render_mode=None):
   12 |         super().__init__()
   13 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   14 |         self.data = mujoco.MjData(self.model)
   15 |         
   16 |         self.renderer = mujoco.Renderer(self.model, height=64, width=64)
   17 |         
   18 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
   19 |         self.observation_space = spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8)
   20 |         
   21 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   22 |         self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   23 |         self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
   24 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   25 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   26 |         
   27 |         # Humanoid joints to control kinematically (Upper body + Legs for wide stance)
   28 |         self.joint_names = [
   29 |             "root_y", "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
   30 |             "left_hip_roll", "left_hip_pitch", "left_knee", "right_hip_roll", "right_hip_pitch", "right_knee"
   31 |         ]
   32 |         self.qpos_adrs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.joint_names]
   33 |         
   34 |         # Humanoid Keyframes [root_y, torso, rs_p, rs_r, rs_y, r_elbow, l_hr, l_hp, l_k, r_hr, r_hp, r_k]
   35 |         # Legs are kept at a constant wide stance: roll(0.3, -0.3), pitch(-0.4, -0.4), knee(0.8, 0.8)
   36 |         self.base_keyframes = np.array([
   37 |             [0.0, -0.5, -1.0, 0.0, 0.5, 1.5,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stance
   38 |             [0.0, -1.0, -1.2, 0.0, 0.8, 2.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Load
   39 |             [0.0, 0.0, -0.5, 0.0, 0.0, 1.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stride (Hip turn only)
   40 |             [0.0, 1.5, 0.5, 0.0, -0.5, 0.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Contact
   41 |             [0.0, 2.0, 1.0, 0.0, -1.0, 1.5,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8]  # Follow-through
   42 |         ])
   43 |         
   44 |         self.render_mode = render_mode
   45 |         if render_mode == "human":
   46 |             from mujoco import viewer
   47 |             self.viewer = viewer.launch_passive(self.model, self.data)
   48 |         else:
   49 |             self.viewer = None
   50 |             
   51 |         self.frame_skip = 4
   52 |         
   53 |         # Aerodynamics
   54 |         self.mass = 0.145
   55 |         self.area = 0.00426
   56 |         self.rho = 1.225
   57 |         self.Cd = 0.3
   58 |         self.Cl = 0.15
   59 | 
   60 |     def reset(self, seed=None, options=None):
   61 |         super().reset(seed=seed)
   62 |         mujoco.mj_resetData(self.model, self.data)
   63 |         
   64 |         self.swing_active = False
   65 |         self.swing_progress = 0.0
   66 |         self.swing_duration_frames = 20
   67 |         self.has_contacted = False
   68 |         self.current_keyframes = self.base_keyframes.copy()
   69 |         
   70 |         # Force initial stance
   71 |         self._update_swing_kinematics(0.0)
   72 |         
   73 |         pitch_type = np.random.choice(["fastball", "curveball"])
   74 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [np.random.uniform(-0.1, 0.1), 15.0, 1.6]
   75 |         
   76 |         if pitch_type == "fastball":
   77 |             self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [np.random.uniform(-1, 1), -40.0, -1.0]
   78 |             self.ball_spin = np.array([0.0, 0.0, 0.0])
   79 |         else:
   80 |             self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [np.random.uniform(-1, 1), -30.0, 1.0]
   81 |             self.ball_spin = np.array([-50.0, 0.0, 30.0])
   82 |             
   83 |         mujoco.mj_forward(self.model, self.data)
   84 |         return self._get_obs(), {}
   85 | 
   86 |     def step(self, action):
   87 |         swing_trigger = action[0]
   88 |         target_z_delta = action[1]
   89 |         swing_speed = action[2]
   90 |         
   91 |         if not self.swing_active and swing_trigger > 0.0:
   92 |             self.swing_active = True
   93 |             self.swing_duration_frames = int(np.interp(swing_speed, [-1, 1], [30, 10]))
   94 |             
   95 |             # Adjust spine pitch or arm to hit higher/lower
   96 |             # Since we didn't expose spine_pitch, let's adjust r_shoulder_y (up/down)
   97 |             pitch_adj = -target_z_delta * 0.5 
   98 |             self.current_keyframes = self.base_keyframes.copy()
   99 |             self.current_keyframes[3, 3] += pitch_adj # shoulder_y at contact
  100 |             
  101 |         reward = 0.0
  102 |         
  103 |         for _ in range(self.frame_skip):
  104 |             self._apply_aerodynamics()
  105 |             
  106 |             if self.swing_active and self.swing_progress < 1.0:
  107 |                 self._update_swing_kinematics(self.swing_progress)
  108 |                 self.swing_progress += 1.0 / self.swing_duration_frames
  109 |                 
  110 |             mujoco.mj_step(self.model, self.data)
  111 |             
  112 |             if not self.has_contacted:
  113 |                 if self._check_contact():
  114 |                     self.has_contacted = True
  115 |                     reward += 10.0
  116 |                     
  117 |         if self.viewer:
  118 |             self.viewer.sync()
  119 |             
  120 |         ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
  121 |         terminated = False
  122 |         if ball_pos[1] < -2.0 or ball_pos[2] < 0.1:
  123 |             terminated = True
  124 |             if not self.has_contacted:
  125 |                 if abs(ball_pos[0]) < 0.3 and 0.5 < ball_pos[2] < 1.2:
  126 |                     reward -= 1.0
  127 |                 else:
  128 |                     reward += 0.5
  129 |                     
  130 |         return self._get_obs(), reward, terminated, False, {}
  131 | 
  132 |     def _apply_aerodynamics(self):
  133 |         vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  134 |         speed = np.linalg.norm(vel)
  135 |         if speed < 0.1: return
  136 |         f_drag = -0.5 * self.rho * self.area * self.Cd * speed * vel
  137 |         v_hat = vel / speed
  138 |         f_magnus = 0.5 * self.rho * self.area * self.Cl * speed * np.cross(self.ball_spin, v_hat)
  139 |         self.data.xfrc_applied[self.ball_body_id][:3] = f_drag + f_magnus
  140 | 
  141 |     def _update_swing_kinematics(self, progress):
  142 |         num_kfs = len(self.current_keyframes)
  143 |         scaled = progress * (num_kfs - 1)
  144 |         idx1 = int(np.floor(scaled))
  145 |         idx2 = min(idx1 + 1, num_kfs - 1)
  146 |         t = scaled - idx1
  147 |         
  148 |         current_angles = (1-t)*self.current_keyframes[idx1] + t*self.current_keyframes[idx2]
  149 |         
  150 |         for i, adr in enumerate(self.qpos_adrs):
  151 |             self.data.qpos[adr] = current_angles[i]
  152 |             jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, self.joint_names[i])
  153 |             vel_adr = self.model.jnt_dofadr[jnt_id]
  154 |             self.data.qvel[vel_adr] = 0.0
  155 | 
  156 |     def _check_contact(self):
  157 |         for i in range(self.data.ncon):
  158 |             contact = self.data.contact[i]
  159 |             if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \
  160 |                (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
  161 |                 return True
  162 |         return False
  163 | 
  164 |     def _get_obs(self):
  165 |         self.renderer.update_scene(self.data, camera="batter_cam")
  166 |         return self.renderer.render()
````
