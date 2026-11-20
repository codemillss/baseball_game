# baseball/archive/humanoid/envs/humanoid_baseball_env.py

원본: [archive/humanoid/envs/humanoid_baseball_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/humanoid/envs/humanoid_baseball_env.py)

SHA256: `6333f1a512df42ccbb6fec645d1df0864acf98cca555b3ceea54ef2b5f3d50c5`

전체 340행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `HumanoidBaseballEnv` | ClassDef | 9 | 340 |
| `__init__` | FunctionDef | 23 | 90 |
| `set_curriculum_stage` | FunctionDef | 92 | 93 |
| `reset` | FunctionDef | 95 | 111 |
| `_throw_pitch` | FunctionDef | 113 | 141 |
| `_get_obs` | FunctionDef | 143 | 180 |
| `_check_contacts` | FunctionDef | 182 | 201 |
| `_get_reference_motion` | FunctionDef | 203 | 235 |
| `step` | FunctionDef | 237 | 340 |

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
    9 | class HumanoidBaseballEnv(gym.Env):
   10 |     """
   11 |     야구 타격(배팅)을 위한 MuJoCo 기반 강화학습 환경 (휴머노이드 21-DOF 버전)
   12 |     - 특징: Standard Humanoid를 타자로 사용하여 전신 제어 학습
   13 |     - 목표: 투수가 던진 공을 방망이로 정확히 맞추기 (Contact)
   14 |     """
   15 |     metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}
   16 | 
   17 |     CURRICULUM = {
   18 |         1: {"name": "Stage 1 (Stage 2.5a: Head-Lock & Center Vision)"},
   19 |         2: {"name": "Stage 2 (Vision Only, No Head-Lock)"},
   20 |         3: {"name": "Stage 3 (Full Multimodal & Edge Vision)"}
   21 |     }
   22 |     
   23 |     def __init__(self, xml_path: str = "humanoid/assets/stadium_3d_humanoid.xml", render_mode: str = None):
   24 |         super().__init__()
   25 |         
   26 |         self.game_engine = BaseballGameEngine()
   27 |         
   28 |         # 1. 모델 로드
   29 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   30 |         self.data = mujoco.MjData(self.model)
   31 |         self.render_mode = render_mode
   32 | 
   33 |         # 2. 객체 ID 매핑
   34 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   35 |         self.ball_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   36 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   37 |         
   38 |         self.bat_barrel_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   39 |         self.bat_taper_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_taper")
   40 |         
   41 |         self.pitcher_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pitcher_placeholder")
   42 | 
   43 |         # 3. 휴머노이드 모터 및 관절 매핑 (21-DOF)
   44 |         self.actuator_names = [
   45 |             "abdomen_z", "abdomen_y", "abdomen_x",
   46 |             "hip_x_right", "hip_z_right", "hip_y_right", "knee_right", "ankle_y_right", "ankle_x_right",
   47 |             "hip_x_left", "hip_z_left", "hip_y_left", "knee_left", "ankle_y_left", "ankle_x_left",
   48 |             "shoulder1_right", "shoulder2_right", "elbow_right",
   49 |             "shoulder1_left", "shoulder2_left", "elbow_left"
   50 |         ]
   51 |         
   52 |         self.motor_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in self.actuator_names]
   53 |         self.joint_names = self.actuator_names # In this model, motor names match joint names exactly
   54 |         self.joint_qpos_idxs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)] for j in self.joint_names]
   55 |         self.joint_qvel_idxs = [self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)] for j in self.joint_names]
   56 | 
   57 |         # 4. 카메라 매핑
   58 |         self.batter_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "batter_cam")
   59 |         self.pitcher_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "pitcher_cam")
   60 |         self.catcher_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "catcher_cam")
   61 |         self.broadcaster_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "broadcaster_cam")
   62 |         
   63 |         self.camera_ids = [self.batter_cam_id, self.pitcher_cam_id, self.catcher_cam_id, self.broadcaster_cam_id]
   64 | 
   65 |         # 5. 공간 정의
   66 |         self.action_dim = len(self.motor_ids)  # 21
   67 |         self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(self.action_dim,), dtype=np.float32)
   68 | 
   69 |         # 상태 공간: [관절각(21), 관절속도(21), 공의상대좌표(3), 공의상대속도(3), 컨텍스트(2)] = 21+21+3+3+2 = 50
   70 |         self.proprio_dim = self.action_dim * 2
   71 |         self.vision_dim = 4 # (azimuth, elevation, distance, is_visible)
   72 |         self.context_dim = 2 # (strike_zone_x, strike_zone_z)
   73 |         self.observation_space = gym.spaces.Dict({
   74 |             "vision": gym.spaces.Box(low=-10.0, high=10.0, shape=(self.vision_dim,), dtype=np.float32),
   75 |             "proprio": gym.spaces.Box(low=-50.0, high=50.0, shape=(self.proprio_dim,), dtype=np.float32),
   76 |             "context": gym.spaces.Box(low=-5.0, high=5.0, shape=(self.context_dim,), dtype=np.float32)
   77 |         })
   78 | 
   79 |         # 6. 환경 상태 변수
   80 |         self.max_steps = 150
   81 |         self.step_count = 0
   82 |         self.has_contacted = False
   83 |         self.contact_info = {}
   84 |         
   85 |         self.curriculum_stage = 1
   86 |         
   87 |         # Renderer
   88 |         self.renderer = None
   89 |         if self.render_mode == "rgb_array":
   90 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
   91 | 
   92 |     def set_curriculum_stage(self, stage: int):
   93 |         self.curriculum_stage = stage
   94 | 
   95 |     def reset(self, seed: int = None, options: dict = None) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
   96 |         super().reset(seed=seed)
   97 |         mujoco.mj_resetData(self.model, self.data)
   98 |         
   99 |         # 1. 공 발사 (투구) 설정
  100 |         self._throw_pitch()
  101 |         
  102 |         # 2. 로봇 자세 초기화
  103 |         self.data.ctrl[self.motor_ids] = 0.0
  104 |         
  105 |         self.step_count = 0
  106 |         self.has_contacted = False
  107 |         self.contact_info = {}
  108 | 
  109 |         mujoco.mj_forward(self.model, self.data)
  110 |         
  111 |         return self._get_obs(), {"stage": self.curriculum_stage}
  112 | 
  113 |     def _throw_pitch(self):
  114 |         pitcher_pos = self.data.xpos[self.pitcher_id]
  115 |         
  116 |         # 커리큘럼에 따른 투구 다양성 (Stage 1: 직구 중앙, Stage 2: 코너 워크)
  117 |         if self.curriculum_stage == 1:
  118 |             target_x = np.random.uniform(-0.1, 0.1)
  119 |             target_z = np.random.uniform(0.9, 1.1)
  120 |             speed = 30.0
  121 |         else:
  122 |             target_x = np.random.uniform(-0.3, 0.3)
  123 |             target_z = np.random.uniform(0.5, 1.3)
  124 |             speed = np.random.uniform(30.0, 40.0)
  125 |             
  126 |         self.target_zone = np.array([target_x, target_z])
  127 |         
  128 |         start_pos = pitcher_pos + np.array([0, 0, 0.5]) # 투수 손 위치
  129 |         target_pos = np.array([target_x, 0.0, target_z]) # 홈플레이트 통과 위치
  130 |         
  131 |         direction = target_pos - start_pos
  132 |         distance = np.linalg.norm(direction)
  133 |         direction /= distance
  134 |         
  135 |         vel = direction * speed
  136 |         
  137 |         qpos_adr = self.model.jnt_qposadr[self.ball_joint_id]
  138 |         qvel_adr = self.model.jnt_dofadr[self.ball_joint_id]
  139 |         
  140 |         self.data.qpos[qpos_adr : qpos_adr+3] = start_pos
  141 |         self.data.qvel[qvel_adr : qvel_adr+3] = vel
  142 | 
  143 |     def _get_obs(self) -> Dict[str, np.ndarray]:
  144 |         # 1. Proprioception (21 DOF)
  145 |         qpos = np.array([self.data.qpos[idx] for idx in self.joint_qpos_idxs])
  146 |         qvel = np.array([self.data.qvel[idx] for idx in self.joint_qvel_idxs])
  147 |         proprio = np.concatenate([qpos, qvel]).astype(np.float32)
  148 | 
  149 |         # 2. Vision (Relative ball coords from batter's head)
  150 |         head_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "head")
  151 |         head_pos = self.data.xpos[head_body_id]
  152 |         head_mat = self.data.xmat[head_body_id].reshape(3, 3)
  153 |         
  154 |         ball_pos_world = self.data.xpos[self.ball_body_id]
  155 |         rel_pos = head_mat.T @ (ball_pos_world - head_pos)
  156 |         
  157 |         dist = np.linalg.norm(rel_pos)
  158 |         azimuth = np.arctan2(rel_pos[1], rel_pos[0])
  159 |         elevation = np.arctan2(rel_pos[2], np.linalg.norm(rel_pos[:2]))
  160 |         
  161 |         # 커리큘럼 시야 처리
  162 |         if self.curriculum_stage >= 2:
  163 |             visible = 1.0 if abs(azimuth) < np.radians(60) else 0.0
  164 |             if abs(azimuth) >= np.radians(60) and abs(azimuth) < np.radians(100):
  165 |                 azimuth += np.random.normal(0, 0.1)
  166 |                 dist += np.random.normal(0, 0.5)
  167 |         else:
  168 |             visible = 1.0
  169 | 
  170 |         vision = np.array([azimuth, elevation, dist, visible], dtype=np.float32)
  171 | 
  172 |         # 3. Context (Game Engine 6D + Target Zone 2D = 8D)
  173 |         game_context = self.game_engine.get_context_vector()
  174 |         context = np.concatenate([game_context, self.target_zone]).astype(np.float32)
  175 | 
  176 |         return {
  177 |             "vision": vision,
  178 |             "proprio": proprio,
  179 |             "context": context
  180 |         }
  181 | 
  182 |     def _check_contacts(self):
  183 |         if self.has_contacted: return
  184 |         for i in range(self.data.ncon):
  185 |             con = self.data.contact[i]
  186 |             g1, g2 = con.geom1, con.geom2
  187 |             is_ball = (g1 == self.ball_geom_id or g2 == self.ball_geom_id)
  188 |             is_bat = (g1 == self.bat_barrel_id or g2 == self.bat_barrel_id or
  189 |                       g1 == self.bat_taper_id or g2 == self.bat_taper_id)
  190 | 
  191 |             if is_ball and is_bat:
  192 |                 self.has_contacted = True
  193 |                 ball_vel = self.data.cvel[self.ball_body_id][3:6].copy()
  194 |                 exit_speed = np.linalg.norm(ball_vel)
  195 |                 vx, vy, vz = ball_vel
  196 |                 horiz_speed = np.hypot(vx, vy)
  197 |                 self.contact_info = {
  198 |                     "exit_velocity_kmh": exit_speed * 3.6,
  199 |                     "launch_angle": np.degrees(np.arctan2(vz, max(horiz_speed, 1e-3))),
  200 |                     "spray_angle": np.degrees(np.arctan2(vx, max(-vy, 1e-3))),
  201 |                 }
  202 | 
  203 |     def _get_reference_motion(self, time_fraction: float) -> np.ndarray:
  204 |         """
  205 |         간략화된 모방 학습 레퍼런스(Reference) 생성 (총 21 DOF)
  206 |         0.0 (Stance) -> 0.5 (Impact) -> 1.0 (Follow-through)
  207 |         """
  208 |         # 기본 자세 0으로 초기화
  209 |         ref = np.zeros(self.action_dim, dtype=np.float32)
  210 |         
  211 |         # 주요 관절 인덱스 (humanoid.xml 기준 순서)
  212 |         idx_abd_z = 0 # abdomen_z (허리 비틀기)
  213 |         idx_sho_r = 15 # shoulder1_right
  214 |         idx_elb_r = 17 # elbow_right
  215 |         idx_sho_l = 18 # shoulder1_left
  216 |         idx_elb_l = 20 # elbow_left
  217 | 
  218 |         if time_fraction < 0.5:
  219 |             # Stance -> Impact
  220 |             alpha = time_fraction / 0.5
  221 |             ref[idx_abd_z] = np.interp(alpha, [0, 1], [-0.5, 0.8])
  222 |             ref[idx_sho_r] = np.interp(alpha, [0, 1], [-0.5, 0.2])
  223 |             ref[idx_elb_r] = np.interp(alpha, [0, 1], [-1.5, -0.2])
  224 |             ref[idx_sho_l] = np.interp(alpha, [0, 1], [-0.2, 0.5])
  225 |             ref[idx_elb_l] = np.interp(alpha, [0, 1], [-1.0, -0.5])
  226 |         else:
  227 |             # Impact -> Follow-through
  228 |             alpha = (time_fraction - 0.5) / 0.5
  229 |             ref[idx_abd_z] = np.interp(alpha, [0, 1], [0.8, 1.2])
  230 |             ref[idx_sho_r] = np.interp(alpha, [0, 1], [0.2, 1.0])
  231 |             ref[idx_elb_r] = np.interp(alpha, [0, 1], [-0.2, -1.0])
  232 |             ref[idx_sho_l] = np.interp(alpha, [0, 1], [0.5, 1.0])
  233 |             ref[idx_elb_l] = np.interp(alpha, [0, 1], [-0.5, -1.5])
  234 | 
  235 |         return ref
  236 | 
  237 |     def step(self, action: np.ndarray) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
  238 |         action = np.clip(action, -1.0, 1.0)
  239 |         self.data.ctrl[self.motor_ids] = action
  240 | 
  241 |         for _ in range(5):
  242 |             mujoco.mj_step(self.model, self.data)
  243 |             self._check_contacts()
  244 | 
  245 |         self.step_count += 1
  246 |         obs = self._get_obs()
  247 |         
  248 |         # 모방 학습 리워드 계산 (Imitation Reward)
  249 |         time_fraction = min(1.0, self.step_count / 100.0) # 예상 투구 도달 프레임을 100으로 가정
  250 |         qpos_ref = self._get_reference_motion(time_fraction)
  251 |         
  252 |         qpos_actual = np.array([self.data.qpos[idx] for idx in self.joint_qpos_idxs])
  253 |         
  254 |         # 관절 각도 L2 오차 페널티 (값이 작을수록 폼이 예쁨)
  255 |         pose_error = np.mean(np.square(qpos_actual - qpos_ref))
  256 |         imitation_reward = max(0.0, 1.0 - pose_error) * 0.5 # 최대 0.5점 부여
  257 |         
  258 |         info = {
  259 |             "has_contacted": self.has_contacted, 
  260 |             "stage": self.curriculum_stage,
  261 |             "imitation_reward": imitation_reward,
  262 |             "pose_error": pose_error
  263 |         }
  264 |         info.update(self.contact_info)
  265 | 
  266 |         terminated = False
  267 |         reward = imitation_reward # 베이스 리워드는 모방 리워드로 시작
  268 | 
  269 |         # 게임 엔진 이벤트 처리를 위한 변수
  270 |         event_str = ""
  271 |         runs = 0
  272 | 
  273 |         if self.has_contacted:
  274 |             terminated = True
  275 |             
  276 |             ev_kmh = self.contact_info.get("exit_velocity_kmh", 0.0)
  277 |             # 비거리 추정 (초속 * 체공시간 3초 가정)
  278 |             dist_m = (ev_kmh / 3.6) * 3.0
  279 |             
  280 |             event_str, runs = self.game_engine.process_pitch(
  281 |                 swung=True, contacted=True, in_strike_zone=True,
  282 |                 exit_velocity_kmh=ev_kmh, distance_m=dist_m
  283 |             )
  284 |             
  285 |             # 태스크 보상
  286 |             if "Home Run" in event_str:
  287 |                 reward += 20.0
  288 |             elif "Double" in event_str:
  289 |                 reward += 10.0
  290 |             elif "Single" in event_str:
  291 |                 reward += 5.0
  292 |             else: # 아웃
  293 |                 reward -= 1.0
  294 |                 
  295 |             reward += runs * 5.0 # 타점 보상
  296 | 
  297 |         else:
  298 |             bat_pos = self.data.xpos[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "bat")]
  299 |             ball_pos = self.data.xpos[self.ball_body_id]
  300 |             
  301 |             # 볼이 배터를 지나쳤으면 종료
  302 |             if ball_pos[1] > 2.0:
  303 |                 terminated = True
  304 |                 
  305 |                 # 스윙 여부 판정 (관절 속도 최대값)
  306 |                 qvels = np.array([self.data.qvel[idx] for idx in self.joint_qvel_idxs])
  307 |                 swung = np.max(np.abs(qvels)) > 3.0
  308 |                 
  309 |                 # 스트라이크 존 판정
  310 |                 tx, tz = self.target_zone
  311 |                 in_sz = (abs(tx) <= 0.25) and (0.6 <= tz <= 1.2)
  312 |                 
  313 |                 event_str, runs = self.game_engine.process_pitch(
  314 |                     swung=swung, contacted=False, in_strike_zone=in_sz
  315 |                 )
  316 |                 
  317 |                 if event_str == "Swinging Strike":
  318 |                     reward -= 1.0
  319 |                 elif event_str == "Called Strike":
  320 |                     reward -= 0.5
  321 |                 elif event_str == "Ball":
  322 |                     reward += 0.5
  323 |                 elif event_str == "Walk":
  324 |                     reward += 2.0
  325 |                 elif event_str == "Strikeout":
  326 |                     reward -= 3.0
  327 |                     
  328 |                 reward += runs * 5.0
  329 | 
  330 |                 # Distance penalty
  331 |                 dist = np.linalg.norm(bat_pos - ball_pos)
  332 |                 dist_reward = max(0.0, 1.0 - dist) * 0.3
  333 |                 reward += dist_reward
  334 | 
  335 |         info["game_event"] = event_str
  336 |         info["runs_scored"] = runs
  337 |         info["game_over"] = self.game_engine.game_over
  338 | 
  339 |         truncated = self.step_count >= self.max_steps
  340 |         return obs, float(reward), terminated, truncated, info
````
