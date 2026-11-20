# baseball/archive/legacy_envs/batter_mechanism.py

원본: [archive/legacy_envs/batter_mechanism.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_envs/batter_mechanism.py)

SHA256: `af8044ed1fdbd417747f6d60f76eb2303c018bcdd663e88cfae3a762e9d64529`

전체 656행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BatModel` | ClassDef | 23 | 49 |
| `SwingConfig` | ClassDef | 53 | 79 |
| `SwingKinematics` | ClassDef | 86 | 260 |
| `__init__` | FunctionDef | 93 | 99 |
| `compute_bat_state` | FunctionDef | 101 | 173 |
| `simulate_swing` | FunctionDef | 175 | 260 |
| `CollisionEngine` | ClassDef | 267 | 441 |
| `__init__` | FunctionDef | 276 | 277 |
| `check_collision` | FunctionDef | 279 | 320 |
| `sweet_spot_factor` | FunctionDef | 322 | 341 |
| `compute_cor` | FunctionDef | 343 | 361 |
| `compute_exit_velocity` | FunctionDef | 363 | 403 |
| `compute_launch_angle` | FunctionDef | 405 | 423 |
| `compute_spray_angle` | FunctionDef | 425 | 441 |
| `BatterMechanism` | ClassDef | 448 | 656 |
| `__init__` | FunctionDef | 461 | 469 |
| `_normalize_to_range` | FunctionDef | 471 | 475 |
| `decode_action` | FunctionDef | 477 | 504 |
| `swing_and_check` | FunctionDef | 506 | 619 |
| `classify_hit` | FunctionDef | 621 | 656 |

## 전체 원문

````text
    1 | """
    2 | batter_mechanism.py — End-to-End 타자 물리 엔진
    3 | 
    4 | 배트 스윙 역학(관절 토크 → FK), Sweet Spot 충돌 판정,
    5 | Exit Velocity / Launch Angle 계산을 수행합니다.
    6 | 
    7 | 핵심 물리:
    8 |     Exit Velocity: v_exit = q × (e × v_ball + (1+e) × v_bat)
    9 |     Sweet Spot:    배트 끝에서 ~17cm 지점, COR 보정
   10 |     Launch Angle:  배트 경사각 + 공 입사각 기반
   11 | """
   12 | 
   13 | import numpy as np
   14 | from dataclasses import dataclass, field
   15 | from typing import Optional, Tuple
   16 | 
   17 | 
   18 | # ──────────────────────────────────────────────────────────────
   19 | #  배트 물리 모델
   20 | # ──────────────────────────────────────────────────────────────
   21 | 
   22 | @dataclass
   23 | class BatModel:
   24 |     """배트의 물리 상수를 관리하는 데이터 클래스.
   25 | 
   26 |     MLB 표준 목재 배트 기준값을 사용합니다.
   27 |     """
   28 | 
   29 |     mass: float = 0.94               # 배트 질량 (kg), ~33oz
   30 |     length: float = 0.84             # 배트 길이 (m), ~33인치
   31 |     barrel_radius: float = 0.033     # 배럴 반지름 (m), ~2.6인치
   32 |     handle_radius: float = 0.012     # 손잡이 반지름 (m)
   33 | 
   34 |     # 관성 모멘트 (회전축: 손잡이 끝단)
   35 |     moment_of_inertia: float = 0.22  # kg·m²
   36 | 
   37 |     # Sweet Spot 위치 (손잡이 끝단 기준)
   38 |     sweet_spot_distance: float = 0.67  # 배트 끝에서 ~17cm = 손잡이에서 ~67cm
   39 | 
   40 |     # 반발 계수 (Coefficient of Restitution)
   41 |     cor_sweet_spot: float = 0.50     # Sweet Spot에서의 COR
   42 |     cor_tip: float = 0.35           # 배트 끝단
   43 |     cor_handle: float = 0.30        # 손잡이 쪽
   44 | 
   45 |     # 타자 위치 (홈플레이트 옆)
   46 |     batter_position: np.ndarray = field(
   47 |         default_factory=lambda: np.array([0.2, 0.3, 0.0])
   48 |         # x=0.2m (홈플레이트 우측), y=0.3m (약간 뒤), z=0.0m
   49 |     )
   50 | 
   51 | 
   52 | @dataclass
   53 | class SwingConfig:
   54 |     """스윙 설정 범위를 정의하는 데이터 클래스.
   55 | 
   56 |     신경망 액션의 [-1, 1] 범위를 실제 스윙 파라미터로 매핑합니다.
   57 |     """
   58 | 
   59 |     # 스윙 트리거 임계값 (타이밍)
   60 |     # action[0] > 0 이면 스윙 결정
   61 |     swing_threshold: float = 0.0
   62 | 
   63 |     # Yaw 토크 범위 (수평 회전, N·m)
   64 |     yaw_torque_min: float = -80.0
   65 |     yaw_torque_max: float = 80.0
   66 | 
   67 |     # Pitch 토크 범위 (수직 경사, N·m)
   68 |     pitch_torque_min: float = -40.0
   69 |     pitch_torque_max: float = 40.0
   70 | 
   71 |     # 높이 타겟 범위 (m)
   72 |     height_target_min: float = 0.3
   73 |     height_target_max: float = 1.3
   74 | 
   75 |     # 스윙 시간 범위 (릴리스부터 스윙까지)
   76 |     swing_duration: float = 0.15     # 스윙 동작 소요 시간 (초)
   77 | 
   78 |     # 배트 각속도 범위
   79 |     max_angular_velocity: float = 35.0  # rad/s (~2000 deg/s)
   80 | 
   81 | 
   82 | # ──────────────────────────────────────────────────────────────
   83 | #  스윙 운동학 (Forward Kinematics)
   84 | # ──────────────────────────────────────────────────────────────
   85 | 
   86 | class SwingKinematics:
   87 |     """배트 스윙의 운동학을 계산합니다.
   88 | 
   89 |     Yaw(수평)/Pitch(수직) 2자유도 회전 모델을 사용하여
   90 |     배트 끝단의 3D 위치와 속도를 계산합니다.
   91 |     """
   92 | 
   93 |     def __init__(
   94 |         self,
   95 |         bat: Optional[BatModel] = None,
   96 |         config: Optional[SwingConfig] = None,
   97 |     ):
   98 |         self.bat = bat or BatModel()
   99 |         self.config = config or SwingConfig()
  100 | 
  101 |     def compute_bat_state(
  102 |         self,
  103 |         yaw_angle: float,
  104 |         pitch_angle: float,
  105 |         yaw_angular_vel: float,
  106 |         pitch_angular_vel: float,
  107 |         batter_pos: Optional[np.ndarray] = None,
  108 |     ) -> dict:
  109 |         """현재 관절 각도/각속도로 배트의 3D 상태를 계산합니다.
  110 | 
  111 |         2자유도 FK: 어깨(yaw) → 손목(pitch) → 배트 끝단
  112 | 
  113 |         Args:
  114 |             yaw_angle: 수평 회전 각도 (rad), 0=투수 방향
  115 |             pitch_angle: 수직 경사 각도 (rad), 0=수평
  116 |             yaw_angular_vel: Yaw 각속도 (rad/s)
  117 |             pitch_angular_vel: Pitch 각속도 (rad/s)
  118 |             batter_pos: 타자 기준 위치 (None이면 기본값)
  119 | 
  120 |         Returns:
  121 |             dict:
  122 |                 'tip_position': 배트 끝단 3D 위치
  123 |                 'sweet_spot_position': Sweet Spot 3D 위치
  124 |                 'tip_velocity': 배트 끝단 3D 속도
  125 |                 'sweet_spot_velocity': Sweet Spot 3D 속도
  126 |                 'bat_direction': 배트 방향 단위벡터
  127 |                 'bat_normal': 배트 면 법선벡터
  128 |         """
  129 |         pos = batter_pos if batter_pos is not None else self.bat.batter_position.copy()
  130 |         L = self.bat.length
  131 |         L_ss = self.bat.sweet_spot_distance
  132 | 
  133 |         # 배트 방향 벡터 (yaw, pitch 회전 적용)
  134 |         bat_dir = np.array([
  135 |             -np.cos(pitch_angle) * np.sin(yaw_angle),  # x: 좌우
  136 |             -np.cos(pitch_angle) * np.cos(yaw_angle),  # y: 전후 (투수 방향)
  137 |             np.sin(pitch_angle),                        # z: 상하
  138 |         ])
  139 | 
  140 |         # 배트 끝단 위치
  141 |         tip_pos = pos + L * bat_dir
  142 |         sweet_spot_pos = pos + L_ss * bat_dir
  143 | 
  144 |         # 배트 끝단 속도 (각속도 × 팔 길이)
  145 |         # v = ω × r (벡터 외적)
  146 |         omega_vec = np.array([
  147 |             pitch_angular_vel * np.cos(yaw_angle),
  148 |             -pitch_angular_vel * np.sin(yaw_angle),
  149 |             yaw_angular_vel,
  150 |         ])
  151 | 
  152 |         r_tip = tip_pos - pos
  153 |         r_ss = sweet_spot_pos - pos
  154 | 
  155 |         tip_vel = np.cross(omega_vec, r_tip)
  156 |         sweet_spot_vel = np.cross(omega_vec, r_ss)
  157 | 
  158 |         # 배트 면 법선벡터 (배트 방향에 수직, z축 방향 성분)
  159 |         bat_normal = np.cross(bat_dir, np.array([0.0, 0.0, 1.0]))
  160 |         norm = np.linalg.norm(bat_normal)
  161 |         if norm > 1e-10:
  162 |             bat_normal = bat_normal / norm
  163 |         else:
  164 |             bat_normal = np.array([1.0, 0.0, 0.0])
  165 | 
  166 |         return {
  167 |             'tip_position': tip_pos,
  168 |             'sweet_spot_position': sweet_spot_pos,
  169 |             'tip_velocity': tip_vel,
  170 |             'sweet_spot_velocity': sweet_spot_vel,
  171 |             'bat_direction': bat_dir,
  172 |             'bat_normal': bat_normal,
  173 |         }
  174 | 
  175 |     def simulate_swing(
  176 |         self,
  177 |         yaw_torque: float,
  178 |         pitch_torque: float,
  179 |         height_target: float,
  180 |         dt: float = 0.001,
  181 |         duration: Optional[float] = None,
  182 |     ) -> dict:
  183 |         """토크 입력으로 전체 스윙 동작을 시뮬레이션합니다.
  184 | 
  185 |         Args:
  186 |             yaw_torque: 수평 토크 (N·m)
  187 |             pitch_torque: 수직 토크 (N·m)
  188 |             height_target: 목표 높이 (m)
  189 |             dt: 시뮬레이션 시간 간격 (초)
  190 |             duration: 스윙 지속 시간 (초)
  191 | 
  192 |         Returns:
  193 |             dict:
  194 |                 'states': 시간별 배트 상태 리스트
  195 |                 'times': 시간 배열
  196 |                 'max_bat_speed': 최대 배트 속도 (m/s)
  197 |         """
  198 |         if duration is None:
  199 |             duration = self.config.swing_duration
  200 | 
  201 |         # 초기 상태 (코킹 위치: 투수 반대편에서 시작)
  202 |         yaw_angle = np.pi * 0.4      # 약간 뒤로 당긴 상태
  203 |         pitch_angle = 0.0             # 수평
  204 |         yaw_omega = 0.0
  205 |         pitch_omega = 0.0
  206 | 
  207 |         # 높이 보정: pitch_angle 초기값을 height_target에 맞게 조정
  208 |         bat_center_z = self.bat.batter_position[2] + \
  209 |             self.bat.sweet_spot_distance * np.sin(pitch_angle)
  210 |         height_error = height_target - bat_center_z
  211 |         pitch_angle = np.arcsin(np.clip(
  212 |             height_error / (self.bat.sweet_spot_distance + 1e-10), -0.9, 0.9
  213 |         ))
  214 | 
  215 |         states = []
  216 |         times = []
  217 |         max_bat_speed = 0.0
  218 | 
  219 |         n_steps = int(duration / dt)
  220 |         t = 0.0
  221 | 
  222 |         for _ in range(n_steps):
  223 |             # 각가속도 = 토크 / 관성모멘트
  224 |             yaw_alpha = yaw_torque / self.bat.moment_of_inertia
  225 |             pitch_alpha = pitch_torque / self.bat.moment_of_inertia
  226 | 
  227 |             # 오일러 적분
  228 |             yaw_omega += yaw_alpha * dt
  229 |             pitch_omega += pitch_alpha * dt
  230 | 
  231 |             # 각속도 제한
  232 |             max_w = self.config.max_angular_velocity
  233 |             yaw_omega = np.clip(yaw_omega, -max_w, max_w)
  234 |             pitch_omega = np.clip(pitch_omega, -max_w * 0.5, max_w * 0.5)
  235 | 
  236 |             yaw_angle += yaw_omega * dt
  237 |             pitch_angle += pitch_omega * dt
  238 |             pitch_angle = np.clip(pitch_angle, -np.pi / 4, np.pi / 4)
  239 | 
  240 |             state = self.compute_bat_state(
  241 |                 yaw_angle, pitch_angle, yaw_omega, pitch_omega
  242 |             )
  243 |             state['yaw_angle'] = yaw_angle
  244 |             state['pitch_angle'] = pitch_angle
  245 |             state['yaw_omega'] = yaw_omega
  246 |             state['pitch_omega'] = pitch_omega
  247 |             state['time'] = t
  248 | 
  249 |             bat_speed = np.linalg.norm(state['sweet_spot_velocity'])
  250 |             max_bat_speed = max(max_bat_speed, bat_speed)
  251 | 
  252 |             states.append(state)
  253 |             times.append(t)
  254 |             t += dt
  255 | 
  256 |         return {
  257 |             'states': states,
  258 |             'times': np.array(times),
  259 |             'max_bat_speed': max_bat_speed,
  260 |         }
  261 | 
  262 | 
  263 | # ──────────────────────────────────────────────────────────────
  264 | #  충돌 엔진
  265 | # ──────────────────────────────────────────────────────────────
  266 | 
  267 | class CollisionEngine:
  268 |     """배트-공 충돌 판정 및 타구 물리를 계산합니다.
  269 | 
  270 |     충돌 모델:
  271 |         v_exit = q × (e × v_ball + (1+e) × v_bat_contact)
  272 |         q: Sweet Spot 보정 계수 (0.6 ~ 1.0)
  273 |         e: 반발 계수 COR (0.30 ~ 0.50)
  274 |     """
  275 | 
  276 |     def __init__(self, bat: Optional[BatModel] = None):
  277 |         self.bat = bat or BatModel()
  278 | 
  279 |     def check_collision(
  280 |         self,
  281 |         ball_pos: np.ndarray,
  282 |         bat_tip: np.ndarray,
  283 |         bat_base: np.ndarray,
  284 |         collision_radius: float = 0.06,
  285 |     ) -> Tuple[bool, float, np.ndarray]:
  286 |         """배트-공 충돌 여부를 판정합니다.
  287 | 
  288 |         배트를 선분(base → tip)으로 모델링하고, 공 중심과의 최소 거리를 계산합니다.
  289 | 
  290 |         Args:
  291 |             ball_pos: 공의 3D 위치
  292 |             bat_tip: 배트 끝단 3D 위치
  293 |             bat_base: 배트 손잡이 끝단 3D 위치 (타자 위치)
  294 |             collision_radius: 충돌 판정 반경 (m), 배트 반경 + 공 반경
  295 | 
  296 |         Returns:
  297 |             (is_hit, contact_distance, contact_point)
  298 |             is_hit: 충돌 여부
  299 |             contact_distance: 손잡이 기준 접촉 거리 (m)
  300 |             contact_point: 충돌 지점 3D 위치
  301 |         """
  302 |         bat_vec = bat_tip - bat_base
  303 |         bat_len = np.linalg.norm(bat_vec)
  304 |         if bat_len < 1e-10:
  305 |             return False, 0.0, bat_base.copy()
  306 | 
  307 |         bat_dir = bat_vec / bat_len
  308 | 
  309 |         # 공 중심에서 배트 선분까지의 최소 거리점 계산
  310 |         ball_to_base = ball_pos - bat_base
  311 |         t = np.dot(ball_to_base, bat_dir) / bat_len
  312 |         t = np.clip(t, 0.0, 1.0)  # 선분 범위 내로 제한
  313 | 
  314 |         closest_point = bat_base + t * bat_vec
  315 |         distance = np.linalg.norm(ball_pos - closest_point)
  316 |         contact_distance = t * bat_len
  317 | 
  318 |         is_hit = distance < collision_radius
  319 | 
  320 |         return is_hit, contact_distance, closest_point
  321 | 
  322 |     def sweet_spot_factor(self, contact_distance: float) -> float:
  323 |         """접촉 지점의 Sweet Spot 보정 계수를 계산합니다.
  324 | 
  325 |         Sweet Spot(~67cm) 지점에서 1.0, 거리가 멀어질수록 감소.
  326 |         가우시안 분포 모델 사용.
  327 | 
  328 |         Args:
  329 |             contact_distance: 손잡이 기준 접촉 거리 (m)
  330 | 
  331 |         Returns:
  332 |             Sweet Spot 보정 계수 (0.5 ~ 1.0)
  333 |         """
  334 |         ss = self.bat.sweet_spot_distance
  335 |         sigma = 0.08  # 가우시안 폭 (m)
  336 | 
  337 |         deviation = abs(contact_distance - ss)
  338 |         factor = np.exp(-(deviation ** 2) / (2 * sigma ** 2))
  339 | 
  340 |         # 최소 0.5로 제한 (완전 빗맞은 타격에도 일부 에너지 전달)
  341 |         return float(max(factor, 0.5))
  342 | 
  343 |     def compute_cor(self, contact_distance: float) -> float:
  344 |         """접촉 지점의 반발 계수(COR)를 계산합니다.
  345 | 
  346 |         Sweet Spot에서 최대, 끝단/손잡이에서 감소.
  347 | 
  348 |         Args:
  349 |             contact_distance: 손잡이 기준 접촉 거리 (m)
  350 | 
  351 |         Returns:
  352 |             COR 값
  353 |         """
  354 |         ss = self.bat.sweet_spot_distance
  355 |         q = self.sweet_spot_factor(contact_distance)
  356 | 
  357 |         # COR = 기본값 × Sweet Spot 보정
  358 |         cor = self.bat.cor_handle + \
  359 |             (self.bat.cor_sweet_spot - self.bat.cor_handle) * q
  360 | 
  361 |         return float(cor)
  362 | 
  363 |     def compute_exit_velocity(
  364 |         self,
  365 |         ball_velocity: np.ndarray,
  366 |         bat_velocity: np.ndarray,
  367 |         bat_normal: np.ndarray,
  368 |         contact_distance: float,
  369 |     ) -> Tuple[np.ndarray, float]:
  370 |         """타구의 Exit Velocity 벡터를 계산합니다.
  371 | 
  372 |         충돌 모델: v_exit = q × (e × v_ball_n + (1+e) × v_bat_n) + v_ball_t
  373 |         (법선 성분만 반발, 접선 성분 보존)
  374 | 
  375 |         Args:
  376 |             ball_velocity: 공의 속도 벡터 (m/s)
  377 |             bat_velocity: 배트 접촉점 속도 벡터 (m/s)
  378 |             bat_normal: 배트 면 법선벡터 (정규화)
  379 |             contact_distance: 손잡이 기준 접촉 거리 (m)
  380 | 
  381 |         Returns:
  382 |             (exit_velocity_vector, exit_speed)
  383 |         """
  384 |         e = self.compute_cor(contact_distance)
  385 |         q = self.sweet_spot_factor(contact_distance)
  386 | 
  387 |         # 법선 방향 상대 속도
  388 |         v_rel = ball_velocity - bat_velocity
  389 |         v_n = np.dot(v_rel, bat_normal) * bat_normal
  390 |         v_t = v_rel - v_n
  391 | 
  392 |         # 반발 후 법선 속도
  393 |         v_n_exit = -e * v_n
  394 | 
  395 |         # 타구 속도 = 배트 속도 + 반발된 상대 속도
  396 |         exit_vel = bat_velocity + v_n_exit + v_t
  397 | 
  398 |         # Sweet Spot 보정 적용
  399 |         exit_vel = exit_vel * q + exit_vel * (1.0 - q) * 0.7
  400 | 
  401 |         exit_speed = float(np.linalg.norm(exit_vel))
  402 | 
  403 |         return exit_vel, exit_speed
  404 | 
  405 |     def compute_launch_angle(
  406 |         self,
  407 |         exit_velocity: np.ndarray,
  408 |     ) -> float:
  409 |         """타구의 Launch Angle을 계산합니다.
  410 | 
  411 |         수평면(xy 평면)과 타구 속도 벡터 사이의 각도.
  412 |         양수: 뜬 공, 음수: 땅볼
  413 | 
  414 |         Args:
  415 |             exit_velocity: 타구 속도 벡터 (m/s)
  416 | 
  417 |         Returns:
  418 |             Launch Angle (degrees)
  419 |         """
  420 |         horizontal_speed = np.sqrt(exit_velocity[0] ** 2 + exit_velocity[1] ** 2)
  421 |         if horizontal_speed < 1e-6:
  422 |             return 0.0
  423 |         return float(np.degrees(np.arctan2(exit_velocity[2], horizontal_speed)))
  424 | 
  425 |     def compute_spray_angle(
  426 |         self,
  427 |         exit_velocity: np.ndarray,
  428 |     ) -> float:
  429 |         """타구의 Spray Angle을 계산합니다.
  430 | 
  431 |         중앙(투수 방향)을 0°로, 좌측(+), 우측(-)
  432 | 
  433 |         Args:
  434 |             exit_velocity: 타구 속도 벡터 (m/s)
  435 | 
  436 |         Returns:
  437 |             Spray Angle (degrees)
  438 |         """
  439 |         if abs(exit_velocity[1]) < 1e-6:
  440 |             return 0.0
  441 |         return float(np.degrees(np.arctan2(exit_velocity[0], -exit_velocity[1])))
  442 | 
  443 | 
  444 | # ──────────────────────────────────────────────────────────────
  445 | #  타자 메커니즘 (E2E Action → 스윙 → 충돌)
  446 | # ──────────────────────────────────────────────────────────────
  447 | 
  448 | class BatterMechanism:
  449 |     """End-to-End 타자 물리 메커니즘.
  450 | 
  451 |     신경망의 연속 액션 벡터를 스윙 토크로 변환하고,
  452 |     공 궤적과의 충돌을 판정합니다.
  453 | 
  454 |     Action Vector:
  455 |         [0] t_trigger:    스윙 결정 (> 0이면 스윙)
  456 |         [1] yaw_torque:   수평 토크 (normalized)
  457 |         [2] pitch_torque:  수직 토크 (normalized)
  458 |         [3] z_height:     목표 높이 (normalized)
  459 |     """
  460 | 
  461 |     def __init__(
  462 |         self,
  463 |         bat: Optional[BatModel] = None,
  464 |         config: Optional[SwingConfig] = None,
  465 |     ):
  466 |         self.bat = bat or BatModel()
  467 |         self.config = config or SwingConfig()
  468 |         self.kinematics = SwingKinematics(self.bat, self.config)
  469 |         self.collision = CollisionEngine(self.bat)
  470 | 
  471 |     def _normalize_to_range(
  472 |         self, value: float, low: float, high: float
  473 |     ) -> float:
  474 |         """[-1, 1] 범위를 [low, high] 범위로 매핑합니다."""
  475 |         return low + (value + 1.0) * 0.5 * (high - low)
  476 | 
  477 |     def decode_action(self, action: np.ndarray) -> dict:
  478 |         """신경망 액션 벡터를 스윙 파라미터로 변환합니다.
  479 | 
  480 |         Args:
  481 |             action: 4차원 연속 액션 벡터, 각 성분 ∈ [-1, 1]
  482 | 
  483 |         Returns:
  484 |             dict:
  485 |                 'should_swing': 스윙 여부
  486 |                 'yaw_torque': 수평 토크 (N·m)
  487 |                 'pitch_torque': 수직 토크 (N·m)
  488 |                 'height_target': 목표 높이 (m)
  489 |         """
  490 |         cfg = self.config
  491 |         action = np.clip(action, -1.0, 1.0)
  492 | 
  493 |         return {
  494 |             'should_swing': action[0] > cfg.swing_threshold,
  495 |             'yaw_torque': self._normalize_to_range(
  496 |                 action[1], cfg.yaw_torque_min, cfg.yaw_torque_max
  497 |             ),
  498 |             'pitch_torque': self._normalize_to_range(
  499 |                 action[2], cfg.pitch_torque_min, cfg.pitch_torque_max
  500 |             ),
  501 |             'height_target': self._normalize_to_range(
  502 |                 action[3], cfg.height_target_min, cfg.height_target_max
  503 |             ),
  504 |         }
  505 | 
  506 |     def swing_and_check(
  507 |         self,
  508 |         action: np.ndarray,
  509 |         ball_trajectory_positions: np.ndarray,
  510 |         ball_trajectory_velocities: np.ndarray,
  511 |         ball_trajectory_times: np.ndarray,
  512 |         swing_start_time: float,
  513 |     ) -> dict:
  514 |         """스윙을 실행하고 공 궤적과의 충돌을 판정합니다.
  515 | 
  516 |         Args:
  517 |             action: 4차원 연속 액션 벡터
  518 |             ball_trajectory_positions: 공 궤적 위치 (N, 3)
  519 |             ball_trajectory_velocities: 공 궤적 속도 (N, 3)
  520 |             ball_trajectory_times: 공 궤적 시간 (N,)
  521 |             swing_start_time: 스윙 시작 시간 (공 릴리스 기준)
  522 | 
  523 |         Returns:
  524 |             dict:
  525 |                 'result': 'swing_miss' | 'hit' | 'no_swing'
  526 |                 'swing_params': 스윙 파라미터 (decode_action 결과)
  527 |                 'contact_info': 충돌 정보 (hit인 경우)
  528 |                     - 'exit_velocity': (3,) m/s
  529 |                     - 'exit_speed': float m/s
  530 |                     - 'exit_speed_kmh': float km/h
  531 |                     - 'launch_angle': float deg
  532 |                     - 'spray_angle': float deg
  533 |                     - 'contact_distance': float m
  534 |                     - 'sweet_spot_factor': float
  535 |                     - 'contact_time': float s
  536 |                     - 'contact_position': (3,) m
  537 |         """
  538 |         params = self.decode_action(action)
  539 | 
  540 |         if not params['should_swing']:
  541 |             return {
  542 |                 'result': 'no_swing',
  543 |                 'swing_params': params,
  544 |                 'contact_info': None,
  545 |             }
  546 | 
  547 |         # 스윙 시뮬레이션
  548 |         swing_result = self.kinematics.simulate_swing(
  549 |             yaw_torque=params['yaw_torque'],
  550 |             pitch_torque=params['pitch_torque'],
  551 |             height_target=params['height_target'],
  552 |         )
  553 | 
  554 |         # 스윙 동작의 각 시간 프레임에서 공과의 충돌 체크
  555 |         swing_states = swing_result['states']
  556 |         dt = self.kinematics.config.swing_duration / len(swing_states)
  557 | 
  558 |         for i, swing_state in enumerate(swing_states):
  559 |             swing_time = swing_start_time + i * dt
  560 | 
  561 |             # 공 궤적에서 해당 시간의 공 위치/속도 보간
  562 |             if swing_time < ball_trajectory_times[0] or \
  563 |                swing_time > ball_trajectory_times[-1]:
  564 |                 continue
  565 | 
  566 |             # 선형 보간으로 공 위치 찾기
  567 |             idx = np.searchsorted(ball_trajectory_times, swing_time) - 1
  568 |             idx = np.clip(idx, 0, len(ball_trajectory_times) - 2)
  569 | 
  570 |             t_frac = (swing_time - ball_trajectory_times[idx]) / \
  571 |                      (ball_trajectory_times[idx + 1] - ball_trajectory_times[idx] + 1e-10)
  572 | 
  573 |             ball_pos = (1 - t_frac) * ball_trajectory_positions[idx] + \
  574 |                        t_frac * ball_trajectory_positions[idx + 1]
  575 |             ball_vel = (1 - t_frac) * ball_trajectory_velocities[idx] + \
  576 |                        t_frac * ball_trajectory_velocities[idx + 1]
  577 | 
  578 |             # 충돌 판정
  579 |             bat_tip = swing_state['tip_position']
  580 |             bat_base = self.bat.batter_position.copy()
  581 | 
  582 |             is_hit, contact_dist, contact_point = self.collision.check_collision(
  583 |                 ball_pos, bat_tip, bat_base
  584 |             )
  585 | 
  586 |             if is_hit:
  587 |                 # 타구 물리 계산
  588 |                 exit_vel, exit_speed = self.collision.compute_exit_velocity(
  589 |                     ball_vel,
  590 |                     swing_state['sweet_spot_velocity'],
  591 |                     swing_state['bat_normal'],
  592 |                     contact_dist,
  593 |                 )
  594 |                 launch_angle = self.collision.compute_launch_angle(exit_vel)
  595 |                 spray_angle = self.collision.compute_spray_angle(exit_vel)
  596 |                 ss_factor = self.collision.sweet_spot_factor(contact_dist)
  597 | 
  598 |                 return {
  599 |                     'result': 'hit',
  600 |                     'swing_params': params,
  601 |                     'contact_info': {
  602 |                         'exit_velocity': exit_vel,
  603 |                         'exit_speed': exit_speed,
  604 |                         'exit_speed_kmh': exit_speed * 3.6,
  605 |                         'launch_angle': launch_angle,
  606 |                         'spray_angle': spray_angle,
  607 |                         'contact_distance': contact_dist,
  608 |                         'sweet_spot_factor': ss_factor,
  609 |                         'contact_time': swing_time,
  610 |                         'contact_position': contact_point,
  611 |                     },
  612 |                 }
  613 | 
  614 |         # 스윙했으나 헛스윙
  615 |         return {
  616 |             'result': 'swing_miss',
  617 |             'swing_params': params,
  618 |             'contact_info': None,
  619 |         }
  620 | 
  621 |     def classify_hit(self, contact_info: dict) -> str:
  622 |         """타구 결과를 분류합니다.
  623 | 
  624 |         Exit Velocity와 Launch Angle을 기반으로 타구 유형을 결정합니다.
  625 | 
  626 |         Args:
  627 |             contact_info: swing_and_check에서 반환된 충돌 정보
  628 | 
  629 |         Returns:
  630 |             'home_run' | 'extra_base' | 'single' | 'foul' | 'out'
  631 |         """
  632 |         if contact_info is None:
  633 |             return 'out'
  634 | 
  635 |         exit_speed = contact_info['exit_speed_kmh']
  636 |         launch_angle = contact_info['launch_angle']
  637 |         spray_angle = abs(contact_info['spray_angle'])
  638 | 
  639 |         # 파울 판정 (spray angle > 45°)
  640 |         if spray_angle > 45.0:
  641 |             return 'foul'
  642 | 
  643 |         # 홈런 (Exit Velocity > 155 km/h & Launch Angle 25~35°)
  644 |         if exit_speed > 155.0 and 20.0 <= launch_angle <= 40.0:
  645 |             return 'home_run'
  646 | 
  647 |         # 장타 (Exit Velocity > 140 km/h & Launch Angle 10~30°)
  648 |         if exit_speed > 140.0 and 10.0 <= launch_angle <= 35.0:
  649 |             return 'extra_base'
  650 | 
  651 |         # 안타 (Exit Velocity > 120 km/h & Launch Angle 5~25°)
  652 |         if exit_speed > 120.0 and 5.0 <= launch_angle <= 30.0:
  653 |             return 'single'
  654 | 
  655 |         # 땅볼 / 플라이아웃
  656 |         return 'out'
````
