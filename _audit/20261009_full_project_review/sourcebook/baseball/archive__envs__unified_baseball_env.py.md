# baseball/archive/envs/unified_baseball_env.py

원본: [archive/envs/unified_baseball_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/envs/unified_baseball_env.py)

SHA256: `8839132e581e273d9acb34b23bf38bf363cdd40a0ee320445fc515c1c9c91e6a`

전체 446행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `UnifiedBaseballEnv` | ClassDef | 23 | 446 |
| `__init__` | FunctionDef | 71 | 130 |
| `set_curriculum_stage` | FunctionDef | 132 | 134 |
| `get_curriculum_stage` | FunctionDef | 136 | 137 |
| `_compute_egocentric_vision` | FunctionDef | 142 | 185 |
| `_get_obs` | FunctionDef | 187 | 196 |
| `reset` | FunctionDef | 201 | 253 |
| `_apply_head_lock` | FunctionDef | 256 | 290 |
| `step` | FunctionDef | 295 | 415 |
| `_check_contacts` | FunctionDef | 417 | 437 |
| `render` | FunctionDef | 439 | 443 |
| `get_contact_rate` | FunctionDef | 445 | 446 |

## 전체 원문

````text
    1 | """
    2 | unified_baseball_env.py — Phase 2.5: 능동 시야(Active Vision) 및 주변시 흐림 효과
    3 | 
    4 | 특징:
    5 |   1. Action Space: 9-DOF (어깨3 + 팔꿈치1 + 손목3 + 목2)
    6 |   2. Proprioception: 18D (qpos 9 + qvel 9)
    7 |   3. Vision: 중심시(±60도), 주변시(±60~100도, 노이즈 추가/속도 차단), 사각지대(±100도 밖)
    8 |   4. 커리큘럼 Head-Lock: 초기 학습 시 목 관절을 강제로 공 궤적에 맞춤
    9 | """
   10 | 
   11 | import os
   12 | import math
   13 | from pathlib import Path
   14 | from typing import Dict, Tuple, Any, Optional
   15 | import numpy as np
   16 | import gymnasium as gym
   17 | from gymnasium import spaces
   18 | import mujoco
   19 | 
   20 | from envs.game_engine import BaseballGameEngine
   21 | 
   22 | 
   23 | class UnifiedBaseballEnv(gym.Env):
   24 |     """Phase 2.5: 9-DOF 능동 시야 및 주변시가 적용된 야구 시뮬레이션."""
   25 | 
   26 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 60}
   27 | 
   28 |     CURRICULUM = {
   29 |         1: {
   30 |             "name": "Stage 2.5a: Head-Lock & Center Vision",
   31 |             "release_distance": 5.0,
   32 |             "speed_range": (25.0, 30.0),
   33 |             "target_x_range": (-0.05, 0.05),
   34 |             "target_z_range": (0.75, 0.85),
   35 |             "pitch_types": ["fastball"],
   36 |             "contact_rate_to_promote": 0.40,
   37 |             "use_distance_shaping": True,
   38 |             "randomize_context": False,
   39 |             "head_lock": True,  # 시선 강제 고정
   40 |         },
   41 |         2: {
   42 |             "name": "Stage 2.5b: Free Gaze & Risk",
   43 |             "release_distance": 12.0,
   44 |             "speed_range": (30.0, 38.0),
   45 |             "target_x_range": (-0.15, 0.15),
   46 |             "target_z_range": (0.55, 1.05),
   47 |             "pitch_types": ["fastball"],
   48 |             "contact_rate_to_promote": 0.25,
   49 |             "use_distance_shaping": True,
   50 |             "randomize_context": True,
   51 |             "head_lock": False, # 시선 자유 제어 (스스로 공 쫓기)
   52 |         },
   53 |         3: {
   54 |             "name": "Stage 2.5c: Full Multi-Agent",
   55 |             "release_distance": 18.44,
   56 |             "speed_range": (35.0, 43.0),
   57 |             "target_x_range": (-0.30, 0.30),
   58 |             "target_z_range": (0.45, 1.10),
   59 |             "pitch_types": ["fastball"],
   60 |             "contact_rate_to_promote": 0.15,
   61 |             "use_distance_shaping": False,
   62 |             "randomize_context": True,
   63 |             "head_lock": False,
   64 |         },
   65 |     }
   66 | 
   67 |     PITCH_PARAMS = {
   68 |         "fastball":  {"spin_rpm": 2200, "spin_axis": np.array([0, 1, 0]),   "speed_mod": 1.0},
   69 |     }
   70 | 
   71 |     def __init__(
   72 |         self,
   73 |         xml_path: Optional[str] = None,
   74 |         curriculum_stage: int = 1,
   75 |         frame_skip: int = 4,
   76 |         render_mode: Optional[str] = None,
   77 |         max_steps_per_pitch: int = 300,
   78 |     ):
   79 |         super().__init__()
   80 | 
   81 |         if xml_path is None:
   82 |             xml_path = str(Path(__file__).parent.parent / "assets" / "stadium_3d.xml")
   83 | 
   84 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   85 |         self.data = mujoco.MjData(self.model)
   86 |         self.frame_skip = frame_skip
   87 |         self.render_mode = render_mode
   88 |         self.max_steps = max_steps_per_pitch
   89 | 
   90 |         self.curriculum_stage = curriculum_stage
   91 |         self.stage_config = self.CURRICULUM[curriculum_stage]
   92 | 
   93 |         # ── MuJoCo ID 캐싱 ──
   94 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   95 |         self.bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "bat")
   96 |         self.cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "batter_cam")
   97 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   98 |         self.bat_barrel_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   99 |         self.bat_taper_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_taper")
  100 |         
  101 |         self.ball_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
  102 |         self.ball_qpos_adr = self.model.jnt_qposadr[self.ball_joint_id]
  103 |         self.ball_qvel_adr = self.model.jnt_dofadr[self.ball_joint_id]
  104 | 
  105 |         # ── Spaces (Dict 멀티모달, 9-DOF Action) ──
  106 |         # 팔 7개 + 목 2개 = 9개
  107 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(9,), dtype=np.float32)
  108 | 
  109 |         self.observation_space = spaces.Dict({
  110 |             # [azimuth(rad), elevation(rad), distance(m), rel_velocity(m/s)]
  111 |             "vision": spaces.Box(low=-50.0, high=50.0, shape=(4,), dtype=np.float32),
  112 |             # 9-DOF [qpos, qvel] = 18D
  113 |             "proprioception": spaces.Box(low=-200.0, high=200.0, shape=(18,), dtype=np.float32),
  114 |             # [balls(0-3), strikes(0-2), outs(0-2), r1(0-1), r2(0-1), r3(0-1)]
  115 |             "context": spaces.Box(low=0.0, high=4.0, shape=(6,), dtype=np.float32),
  116 |         })
  117 | 
  118 |         self.renderer = None
  119 |         if self.render_mode == "rgb_array":
  120 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
  121 | 
  122 |         self.game_engine = BaseballGameEngine()
  123 | 
  124 |         self.step_count = 0
  125 |         self.has_contacted = False
  126 |         self.contact_info = {}
  127 |         self.min_dist_to_ball = float("inf")
  128 | 
  129 |         self.episode_contacts = 0
  130 |         self.episode_total = 0
  131 | 
  132 |     def set_curriculum_stage(self, stage: int):
  133 |         self.curriculum_stage = min(stage, max(self.CURRICULUM.keys()))
  134 |         self.stage_config = self.CURRICULUM[self.curriculum_stage]
  135 | 
  136 |     def get_curriculum_stage(self) -> int:
  137 |         return self.curriculum_stage
  138 | 
  139 |     # ──────────────────────────────────────────────────────────
  140 |     #  중심시(Foveal) vs 주변시(Peripheral Blur) 계산 로직
  141 |     # ──────────────────────────────────────────────────────────
  142 |     def _compute_egocentric_vision(self) -> np.ndarray:
  143 |         ball_pos = self.data.xpos[self.ball_body_id]
  144 |         ball_vel = self.data.cvel[self.ball_body_id][3:6]
  145 |         
  146 |         cam_pos = self.data.cam_xpos[self.cam_id]
  147 |         cam_mat = self.data.cam_xmat[self.cam_id].reshape(3, 3)
  148 | 
  149 |         # 카메라 로컬 좌표계로 공 위치 변환 (1인칭 시점)
  150 |         rel_pos = ball_pos - cam_pos
  151 |         local_pos = cam_mat.T @ rel_pos
  152 | 
  153 |         x, y, z = local_pos
  154 |         distance = np.linalg.norm(local_pos)
  155 |         
  156 |         azimuth = math.atan2(x, -z)
  157 |         elevation = math.asin(y / max(distance, 1e-5))
  158 |         rel_vel = np.linalg.norm(ball_vel)
  159 | 
  160 |         azimuth_deg = math.degrees(abs(azimuth))
  161 | 
  162 |         if distance > 25.0:
  163 |             return np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
  164 | 
  165 |         # 1. 중심시 (정면 ±60도 이내) - 맑고 정확한 시야
  166 |         if azimuth_deg <= 60.0:
  167 |             return np.array([azimuth, elevation, distance, rel_vel], dtype=np.float32)
  168 |         
  169 |         # 2. 주변시 (±60도 ~ ±100도) - 흐림(Blur) 및 노이즈 적용
  170 |         elif 60.0 < azimuth_deg <= 100.0:
  171 |             noise_az = self.np_random.normal(0, 0.1) # 방위각 노이즈 추가 (약 5도)
  172 |             noise_el = self.np_random.normal(0, 0.1) # 앙각 노이즈 추가
  173 |             noise_dist = self.np_random.normal(0, 1.0) # 거리 노이즈 크게 추가
  174 |             
  175 |             # 주변시는 속도 파악이 어려움 (0으로 차단)
  176 |             return np.array([
  177 |                 azimuth + noise_az, 
  178 |                 elevation + noise_el, 
  179 |                 max(0.1, distance + noise_dist), 
  180 |                 0.0
  181 |             ], dtype=np.float32)
  182 |         
  183 |         # 3. 사각지대 (±100도 초과) - 완전한 시야 상실
  184 |         else:
  185 |             return np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
  186 | 
  187 |     def _get_obs(self) -> Dict[str, np.ndarray]:
  188 |         vision = self._compute_egocentric_vision()
  189 |         # 팔(7) + 목(2) = 총 9-DOF 의 qpos/qvel
  190 |         prop = np.concatenate([self.data.qpos[7:16], self.data.qvel[6:15]], dtype=np.float32)
  191 |         
  192 |         return {
  193 |             "vision": vision,
  194 |             "proprioception": prop,
  195 |             "context": self.game_engine.get_context_vector()
  196 |         }
  197 | 
  198 |     # ──────────────────────────────────────────────────────────
  199 |     #  리셋: 상황 무작위 부여
  200 |     # ──────────────────────────────────────────────────────────
  201 |     def reset(self, *, seed=None, options=None):
  202 |         super().reset(seed=seed)
  203 |         mujoco.mj_resetData(self.model, self.data)
  204 |         cfg = self.stage_config
  205 | 
  206 |         if cfg.get("randomize_context", False):
  207 |             self.game_context = np.array([
  208 |                 self.np_random.integers(0, 4),  
  209 |                 self.np_random.integers(0, 3),  
  210 |                 self.np_random.integers(0, 3),  
  211 |                 self.np_random.integers(0, 2),  
  212 |                 self.np_random.integers(0, 2),  
  213 |                 self.np_random.integers(0, 2),  
  214 |             ], dtype=np.float32)
  215 |         else:
  216 |             self.game_context = np.zeros(6, dtype=np.float32)
  217 | 
  218 |         release_y = cfg["release_distance"]
  219 |         target_x = self.np_random.uniform(*cfg["target_x_range"])
  220 |         target_z = self.np_random.uniform(*cfg["target_z_range"])
  221 | 
  222 |         self.data.qpos[self.ball_qpos_adr + 0] = self.np_random.uniform(-0.02, 0.02)
  223 |         self.data.qpos[self.ball_qpos_adr + 1] = release_y
  224 |         self.data.qpos[self.ball_qpos_adr + 2] = 1.8 + self.np_random.uniform(-0.05, 0.05)
  225 |         self.data.qpos[self.ball_qpos_adr + 3: self.ball_qpos_adr + 7] = [1, 0, 0, 0]
  226 | 
  227 |         base_speed = self.np_random.uniform(*cfg["speed_range"])
  228 |         ball_start = np.array([
  229 |             self.data.qpos[self.ball_qpos_adr],
  230 |             release_y,
  231 |             self.data.qpos[self.ball_qpos_adr + 2],
  232 |         ])
  233 |         target_pos = np.array([target_x, 0.0, target_z])
  234 |         direction = target_pos - ball_start
  235 |         direction = direction / (np.linalg.norm(direction) + 1e-8)
  236 | 
  237 |         self.data.qvel[self.ball_qvel_adr + 0] = direction[0] * base_speed
  238 |         self.data.qvel[self.ball_qvel_adr + 1] = direction[1] * base_speed
  239 |         self.data.qvel[self.ball_qvel_adr + 2] = direction[2] * base_speed + 2.0
  240 | 
  241 |         # 로봇 9-DOF 초기화
  242 |         self.data.qpos[7:16] = 0.0
  243 |         self.data.qvel[6:15] = 0.0
  244 | 
  245 |         mujoco.mj_forward(self.model, self.data)
  246 | 
  247 |         self.step_count = 0
  248 |         self.has_contacted = False
  249 |         self.contact_info = {}
  250 |         self.min_dist_to_ball = float("inf")
  251 |         self.episode_total += 1
  252 | 
  253 |         return self._get_obs(), {"stage": self.curriculum_stage}
  254 | 
  255 |         # ── Head-Lock 보정 계산 (IK 기반 자동 시선 추적) ──
  256 |     def _apply_head_lock(self):
  257 |         ball_pos = self.data.xpos[self.ball_body_id]
  258 |         neck_pos = np.array([0.6, -0.1, 1.6]) 
  259 |         
  260 |         rel_pos = ball_pos - neck_pos
  261 |         x, y, z = rel_pos
  262 |         
  263 |         target_yaw = math.atan2(-y, -x)  
  264 |         dist_xy = math.hypot(x, y)
  265 |         target_pitch = math.atan2(z, dist_xy)
  266 |         
  267 |         # head joints 
  268 |         head_yaw_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "head_yaw")
  269 |         head_pitch_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "head_pitch")
  270 |         
  271 |         head_yaw_qpos_adr = self.model.jnt_qposadr[head_yaw_id]
  272 |         head_pitch_qpos_adr = self.model.jnt_qposadr[head_pitch_id]
  273 |         head_yaw_dof_adr = self.model.jnt_dofadr[head_yaw_id]
  274 |         head_pitch_dof_adr = self.model.jnt_dofadr[head_pitch_id]
  275 |         
  276 |         current_yaw = self.data.qpos[head_yaw_qpos_adr]
  277 |         current_pitch = self.data.qpos[head_pitch_qpos_adr]
  278 |         
  279 |         kp_yaw = 20.0
  280 |         kp_pitch = 20.0
  281 |         
  282 |         yaw_torque = (target_yaw - current_yaw) * kp_yaw - self.data.qvel[head_yaw_dof_adr] * 2.0
  283 |         pitch_torque = (target_pitch - current_pitch) * kp_pitch - self.data.qvel[head_pitch_dof_adr] * 2.0
  284 |         
  285 |         # ctrl actuator index
  286 |         head_yaw_act = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_yaw")
  287 |         head_pitch_act = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_pitch")
  288 |         
  289 |         self.data.ctrl[head_yaw_act] = np.clip(yaw_torque, -20.0, 20.0)
  290 |         self.data.ctrl[head_pitch_act] = np.clip(pitch_torque, -20.0, 20.0)
  291 | 
  292 |     # ──────────────────────────────────────────────────────────
  293 |     #  물리 스텝 (9-DOF)
  294 |     # ──────────────────────────────────────────────────────────
  295 |     def step(self, action: np.ndarray):
  296 |         action = np.clip(action, -1.0, 1.0)
  297 | 
  298 |         # 1. 팔(Arm) 7-DOF 토크 인가 (목 뒤의 액추에이터는 7~13번 인덱스임)
  299 |         # Wait, stadium_3d.xml에서 motor 선언 순서:
  300 |         # shoulder(3), elbow(1), wrist(3), cf_slide(3), head(2)
  301 |         # 아차, cf_slide가 중간에 있음.
  302 |         # motor 인덱스를 명확하게 확인해야 함.
  303 |         # 0~2: shoulder, 3: elbow, 4~6: wrist
  304 |         # 7~9: cf_actuators
  305 |         # 10~11: head_yaw, head_pitch
  306 |         self.data.ctrl[0] = action[0] * 50.0  
  307 |         self.data.ctrl[1] = action[1] * 50.0  
  308 |         self.data.ctrl[2] = action[2] * 50.0  
  309 |         self.data.ctrl[3] = action[3] * 50.0  
  310 |         self.data.ctrl[4] = action[4] * 25.0  
  311 |         self.data.ctrl[5] = action[5] * 25.0  
  312 |         self.data.ctrl[6] = action[6] * 25.0  
  313 | 
  314 |         # 2. 목(Neck) 2-DOF 제어
  315 |         if self.stage_config.get("head_lock", False):
  316 |             # RL 정책의 action[7:9] 무시하고 PID 추적기 작동
  317 |             self._apply_head_lock()
  318 |         else:
  319 |             # RL 정책이 스스로 고개를 돌림
  320 |             head_yaw_act = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_yaw")
  321 |             head_pitch_act = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_pitch")
  322 |             self.data.ctrl[head_yaw_act] = action[7] * 20.0  
  323 |             self.data.ctrl[head_pitch_act] = action[8] * 20.0
  324 | 
  325 |         # Head-Lock 로직에서 motor 인덱스를 제대로 맞춰야 함:
  326 |         # _apply_head_lock에서 ctrl[10], ctrl[11]을 건드려야 함 (아래 함수 수정됨)
  327 | 
  328 |         for _ in range(self.frame_skip):
  329 |             mujoco.mj_step(self.model, self.data)
  330 |             self._check_contacts()
  331 | 
  332 |         self.step_count += 1
  333 |         obs = self._get_obs()
  334 |         
  335 |         ball_pos = self.data.xpos[self.ball_body_id]
  336 |         bat_pos = self.data.xpos[self.bat_body_id]
  337 |         bat_rot = self.data.xmat[self.bat_body_id].reshape(3, 3)
  338 |         barrel_offset = bat_rot.dot(np.array([0.0, 0.675, 0.0]))
  339 |         barrel_pos = bat_pos + barrel_offset
  340 |         dist = np.linalg.norm(ball_pos - barrel_pos)
  341 |         self.min_dist_to_ball = min(self.min_dist_to_ball, dist)
  342 | 
  343 |         reward = 0.0
  344 |         terminated = False
  345 |         info = {"has_contacted": self.has_contacted, "stage": self.curriculum_stage}
  346 | 
  347 |         event_str = ""
  348 |         runs = 0
  349 | 
  350 |         if self.has_contacted:
  351 |             reward += 5.0
  352 |             self.episode_contacts += 1
  353 | 
  354 |             ev = self.contact_info.get("exit_velocity_kmh", 0.0)
  355 |             la = self.contact_info.get("launch_angle", 0.0)
  356 |             sa = self.contact_info.get("spray_angle", 0.0)
  357 |             dist_est = (ev / 3.6) * 3.0
  358 | 
  359 |             event_str, runs = self.game_engine.process_pitch(
  360 |                 swung=True, contacted=True, in_strike_zone=True,
  361 |                 exit_velocity_kmh=ev, distance_m=dist_est
  362 |             )
  363 | 
  364 |             reward += min(ev / 30.0, 5.0)
  365 |             if -45.0 <= sa <= 45.0:
  366 |                 reward += 2.0
  367 |             
  368 |             if "Home Run" in event_str:
  369 |                 reward += 20.0
  370 |             elif "Double" in event_str:
  371 |                 reward += 10.0
  372 |             elif "Single" in event_str:
  373 |                 reward += 5.0
  374 | 
  375 |             reward += runs * 5.0
  376 | 
  377 |             info.update(self.contact_info)
  378 |             info["game_event"] = event_str
  379 |             info["runs"] = runs
  380 |             terminated = True
  381 | 
  382 |         elif ball_pos[1] < -1.0 or ball_pos[2] < 0.02:
  383 |             # 타격 실패 (Miss / Strikeout / Ball)
  384 |             # 팔 관절 속도로 스윙 여부 판단
  385 |             swung = np.max(np.abs(self.data.qvel[6:13])) > 2.0
  386 |             # ball_joint_id는 관절 ID(int)이므로, qpos 주소는 ball_qpos_adr 사용
  387 |             target_x = self.data.qpos[self.ball_qpos_adr]  # x 좌표 (홈플레이트 좌우)
  388 |             in_sz = abs(target_x) <= 0.25
  389 | 
  390 |             event_str, runs = self.game_engine.process_pitch(
  391 |                 swung=swung, contacted=False, in_strike_zone=in_sz
  392 |             )
  393 | 
  394 |             if event_str == "Swinging Strike":
  395 |                 reward -= 1.5
  396 |             elif event_str == "Called Strike":
  397 |                 reward -= 1.0
  398 |             elif event_str == "Ball":
  399 |                 reward += 0.5
  400 |             elif event_str == "Walk":
  401 |                 reward += 2.5
  402 |             elif event_str == "Strikeout":
  403 |                 reward -= 4.0
  404 | 
  405 |             info["result"] = "MISS"
  406 |             info["game_event"] = event_str
  407 |             terminated = True
  408 | 
  409 |         else:
  410 |             if self.stage_config.get("use_distance_shaping", False):
  411 |                 dist_reward = max(0.0, 1.0 - dist) * 0.3
  412 |                 reward += dist_reward
  413 | 
  414 |         truncated = self.step_count >= self.max_steps
  415 |         return obs, float(reward), terminated, truncated, info
  416 | 
  417 |     def _check_contacts(self):
  418 |         if self.has_contacted: return
  419 |         for i in range(self.data.ncon):
  420 |             con = self.data.contact[i]
  421 |             g1, g2 = con.geom1, con.geom2
  422 |             is_ball = (g1 == self.ball_geom_id or g2 == self.ball_geom_id)
  423 |             is_bat = (g1 == self.bat_barrel_id or g2 == self.bat_barrel_id or
  424 |                       g1 == self.bat_taper_id or g2 == self.bat_taper_id)
  425 | 
  426 |             if is_ball and is_bat:
  427 |                 self.has_contacted = True
  428 |                 ball_vel = self.data.cvel[self.ball_body_id][3:6].copy()
  429 |                 exit_speed = np.linalg.norm(ball_vel)
  430 |                 vx, vy, vz = ball_vel
  431 |                 horiz_speed = np.hypot(vx, vy)
  432 |                 self.contact_info = {
  433 |                     "exit_velocity_kmh": exit_speed * 3.6,
  434 |                     "launch_angle": np.degrees(np.arctan2(vz, max(horiz_speed, 1e-3))),
  435 |                     "spray_angle": np.degrees(np.arctan2(vx, max(-vy, 1e-3))),
  436 |                 }
  437 |                 break
  438 | 
  439 |     def render(self):
  440 |         if self.renderer:
  441 |             self.renderer.update_scene(self.data, camera="batter_cam")
  442 |             return self.renderer.render()
  443 |         return None
  444 | 
  445 |     def get_contact_rate(self) -> float:
  446 |         return self.episode_contacts / self.episode_total if self.episode_total > 0 else 0.0
````
