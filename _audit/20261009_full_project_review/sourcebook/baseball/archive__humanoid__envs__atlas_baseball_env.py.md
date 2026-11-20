# baseball/archive/humanoid/envs/atlas_baseball_env.py

원본: [archive/humanoid/envs/atlas_baseball_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/humanoid/envs/atlas_baseball_env.py)

SHA256: `e2fc1ecef7d4dff3e818626445f059d8305d1339af3a75a846d8f57cdcdbcfa3`

전체 205행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `AtlasBaseballEnv` | ClassDef | 9 | 205 |
| `__init__` | FunctionDef | 21 | 67 |
| `set_curriculum_stage` | FunctionDef | 69 | 70 |
| `reset` | FunctionDef | 72 | 82 |
| `_throw_pitch` | FunctionDef | 84 | 107 |
| `_get_obs` | FunctionDef | 109 | 133 |
| `_check_contacts` | FunctionDef | 135 | 150 |
| `step` | FunctionDef | 152 | 199 |
| `render` | FunctionDef | 201 | 205 |

## 전체 원문

````text
    1 | import os
    2 | import time
    3 | import numpy as np
    4 | import mujoco
    5 | from typing import Dict, Any, Tuple
    6 | import gymnasium as gym
    7 | from humanoid.envs.game_engine import BaseballGameEngine
    8 | 
    9 | class AtlasBaseballEnv(gym.Env):
   10 |     """
   11 |     보스턴 다이내믹스 아틀라스(Boston Dynamics Atlas) 30-DOF 기반 야구 타격 환경
   12 |     - 특징: 실제 3D STL 메쉬 적용, Unpinned Pelvis (두 발로 타석 접지), Ground Reaction Force(GRF) 물리 적용
   13 |     """
   14 |     metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}
   15 | 
   16 |     CURRICULUM = {
   17 |         1: {"name": "Stage 1 (Atlas Grounded Batter)"},
   18 |         2: {"name": "Stage 2 (Full Game Logic & Corner Pitch)"},
   19 |     }
   20 | 
   21 |     def __init__(self, xml_path: str = "humanoid/assets/stadium_3d_atlas.xml", render_mode: str = None):
   22 |         super().__init__()
   23 | 
   24 |         self.game_engine = BaseballGameEngine()
   25 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   26 |         self.data = mujoco.MjData(self.model)
   27 |         self.render_mode = render_mode
   28 |         if self.render_mode == "rgb_array":
   29 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
   30 |         else:
   31 |             self.renderer = None
   32 | 
   33 |         # ID Mapping
   34 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   35 |         self.ball_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   36 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   37 |         
   38 |         self.bat_barrel_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   39 |         self.pitcher_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pitcher_placeholder")
   40 | 
   41 |         # Actuator mapping (30 motors)
   42 |         self.actuator_names = [
   43 |             'back_bkz_motor', 'back_bky_motor', 'back_bkx_motor',
   44 |             'l_arm_shz_motor', 'l_arm_shx_motor', 'l_arm_ely_motor', 'l_arm_elx_motor', 'l_arm_uwy_motor', 'l_arm_mwx_motor', 'l_arm_lwy_motor',
   45 |             'neck_ay_motor',
   46 |             'r_arm_shz_motor', 'r_arm_shx_motor', 'r_arm_ely_motor', 'r_arm_elx_motor', 'r_arm_uwy_motor', 'r_arm_mwx_motor', 'r_arm_lwy_motor',
   47 |             'l_leg_hpz_motor', 'l_leg_hpx_motor', 'l_leg_hpy_motor', 'l_leg_kny_motor', 'l_leg_aky_motor', 'l_leg_akx_motor',
   48 |             'r_leg_hpz_motor', 'r_leg_hpx_motor', 'r_leg_hpy_motor', 'r_leg_kny_motor', 'r_leg_aky_motor', 'r_leg_akx_motor'
   49 |         ]
   50 |         self.motor_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in self.actuator_names]
   51 | 
   52 |         # Action Space: 30 continuous torques/positions
   53 |         self.action_dim = len(self.motor_ids)
   54 |         self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(self.action_dim,), dtype=np.float32)
   55 | 
   56 |         # Observation Space (Vision 4D, Proprio 60D, Context 8D)
   57 |         self.observation_space = gym.spaces.Dict({
   58 |             "vision": gym.spaces.Box(low=-np.inf, high=np.inf, shape=(4,), dtype=np.float32),
   59 |             "proprio": gym.spaces.Box(low=-np.inf, high=np.inf, shape=(60,), dtype=np.float32),
   60 |             "context": gym.spaces.Box(low=-np.inf, high=np.inf, shape=(8,), dtype=np.float32)
   61 |         })
   62 | 
   63 |         self.curriculum_stage = 1
   64 |         self.step_count = 0
   65 |         self.max_steps = 150
   66 |         self.has_contacted = False
   67 |         self.contact_info = {}
   68 | 
   69 |     def set_curriculum_stage(self, stage: int):
   70 |         self.curriculum_stage = stage
   71 | 
   72 |     def reset(self, seed=None, options=None):
   73 |         super().reset(seed=seed)
   74 |         mujoco.mj_resetData(self.model, self.data)
   75 |         
   76 |         self.step_count = 0
   77 |         self.has_contacted = False
   78 |         self.contact_info = {}
   79 |         
   80 |         self._throw_pitch()
   81 |         mujoco.mj_forward(self.model, self.data)
   82 |         return self._get_obs(), {"stage": self.curriculum_stage}
   83 | 
   84 |     def _throw_pitch(self):
   85 |         pitcher_pos = self.data.xpos[self.pitcher_id]
   86 |         if self.curriculum_stage == 1:
   87 |             target_x = np.random.uniform(-0.1, 0.1)
   88 |             target_z = np.random.uniform(0.9, 1.1)
   89 |             speed = 32.0
   90 |         else:
   91 |             target_x = np.random.uniform(-0.3, 0.3)
   92 |             target_z = np.random.uniform(0.6, 1.2)
   93 |             speed = np.random.uniform(30.0, 42.0)
   94 | 
   95 |         self.target_zone = np.array([target_x, target_z])
   96 |         start_pos = pitcher_pos + np.array([0, 0, 0.5])
   97 |         target_pos = np.array([target_x, 0.0, target_z])
   98 |         
   99 |         direction = target_pos - start_pos
  100 |         direction /= np.linalg.norm(direction)
  101 |         vel = direction * speed
  102 | 
  103 |         qpos_adr = self.model.jnt_qposadr[self.ball_joint_id]
  104 |         qvel_adr = self.model.jnt_dofadr[self.ball_joint_id]
  105 |         
  106 |         self.data.qpos[qpos_adr : qpos_adr+3] = start_pos
  107 |         self.data.qvel[qvel_adr : qvel_adr+3] = vel
  108 | 
  109 |     def _get_obs(self) -> Dict[str, np.ndarray]:
  110 |         # 1. Proprioception (30 qpos + 30 qvel = 60D)
  111 |         # Use actuator ctrl / joint values
  112 |         qpos_vals = self.data.qpos[7:37] if len(self.data.qpos) >= 37 else np.zeros(30)
  113 |         qvel_vals = self.data.qvel[6:36] if len(self.data.qvel) >= 36 else np.zeros(30)
  114 |         proprio = np.concatenate([qpos_vals, qvel_vals]).astype(np.float32)
  115 | 
  116 |         # 2. Vision (Relative ball coords from head camera)
  117 |         head_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "head")
  118 |         head_pos = self.data.xpos[head_body_id]
  119 |         head_mat = self.data.xmat[head_body_id].reshape(3, 3)
  120 |         
  121 |         ball_pos_world = self.data.xpos[self.ball_body_id]
  122 |         rel_pos = head_mat.T @ (ball_pos_world - head_pos)
  123 |         
  124 |         dist = np.linalg.norm(rel_pos)
  125 |         azimuth = np.arctan2(rel_pos[1], rel_pos[0])
  126 |         elevation = np.arctan2(rel_pos[2], np.linalg.norm(rel_pos[:2]))
  127 |         vision = np.array([azimuth, elevation, dist, 1.0], dtype=np.float32)
  128 | 
  129 |         # 3. Context (Game Engine 6D + Target 2D = 8D)
  130 |         game_context = self.game_engine.get_context_vector()
  131 |         context = np.concatenate([game_context, self.target_zone]).astype(np.float32)
  132 | 
  133 |         return {"vision": vision, "proprio": proprio, "context": context}
  134 | 
  135 |     def _check_contacts(self):
  136 |         if self.has_contacted: return
  137 |         for i in range(self.data.ncon):
  138 |             con = self.data.contact[i]
  139 |             g1, g2 = con.geom1, con.geom2
  140 |             is_ball = (g1 == self.ball_geom_id or g2 == self.ball_geom_id)
  141 |             is_bat = (g1 == self.bat_barrel_id or g2 == self.bat_barrel_id)
  142 |             if is_ball and is_bat:
  143 |                 self.has_contacted = True
  144 |                 ball_vel = self.data.cvel[self.ball_body_id][3:6].copy()
  145 |                 exit_speed = np.linalg.norm(ball_vel)
  146 |                 vx, vy, vz = ball_vel
  147 |                 self.contact_info = {
  148 |                     "exit_velocity_kmh": exit_speed * 3.6,
  149 |                     "launch_angle": np.degrees(np.arctan2(vz, max(np.hypot(vx, vy), 1e-3))),
  150 |                 }
  151 | 
  152 |     def step(self, action: np.ndarray) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
  153 |         action = np.clip(action, -1.0, 1.0)
  154 |         self.data.ctrl[self.motor_ids] = action
  155 | 
  156 |         for _ in range(5):
  157 |             mujoco.mj_step(self.model, self.data)
  158 |             self._check_contacts()
  159 | 
  160 |         self.step_count += 1
  161 |         obs = self._get_obs()
  162 | 
  163 |         # Balance & Posture Reward (Pelvis height stability)
  164 |         pelvis_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
  165 |         pelvis_z = self.data.xpos[pelvis_body_id][2]
  166 |         balance_reward = max(0.0, 1.0 - abs(pelvis_z - 0.95)) * 0.5
  167 | 
  168 |         info = {
  169 |             "has_contacted": self.has_contacted,
  170 |             "stage": self.curriculum_stage,
  171 |             "balance_reward": balance_reward
  172 |         }
  173 |         info.update(self.contact_info)
  174 | 
  175 |         terminated = False
  176 |         reward = balance_reward
  177 | 
  178 |         if self.has_contacted:
  179 |             terminated = True
  180 |             ev_kmh = self.contact_info.get("exit_velocity_kmh", 0.0)
  181 |             dist_m = (ev_kmh / 3.6) * 3.0
  182 |             event_str, runs = self.game_engine.process_pitch(
  183 |                 swung=True, contacted=True, in_strike_zone=True,
  184 |                 exit_velocity_kmh=ev_kmh, distance_m=dist_m
  185 |             )
  186 |             reward += 15.0 + (ev_kmh / 10.0)
  187 |             info["game_event"] = event_str
  188 |         else:
  189 |             ball_pos = self.data.xpos[self.ball_body_id]
  190 |             if ball_pos[1] > 2.0 or pelvis_z < 0.4: # Ball passed or robot fell down
  191 |                 terminated = True
  192 |                 if pelvis_z < 0.4:
  193 |                     reward -= 5.0 # Fall penalty
  194 |                     info["game_event"] = "Fall Down"
  195 |                 else:
  196 |                     info["game_event"] = "Ball Passed"
  197 | 
  198 |         truncated = self.step_count >= self.max_steps
  199 |         return obs, float(reward), terminated, truncated, info
  200 | 
  201 |     def render(self):
  202 |         if self.renderer:
  203 |             self.renderer.update_scene(self.data, camera="broadcaster_cam")
  204 |             return self.renderer.render()
  205 |         return None
````
