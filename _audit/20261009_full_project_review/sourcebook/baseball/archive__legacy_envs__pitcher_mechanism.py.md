# baseball/archive/legacy_envs/pitcher_mechanism.py

원본: [archive/legacy_envs/pitcher_mechanism.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_envs/pitcher_mechanism.py)

SHA256: `cba6a6ffa6bf7575d5a2a3929a61b3d09ea479a944edfec12a389aa6f43f242d`

전체 606행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BallPhysics` | ClassDef | 23 | 40 |
| `__post_init__` | FunctionDef | 38 | 40 |
| `PitchConfig` | ClassDef | 44 | 77 |
| `AerodynamicsModel` | ClassDef | 84 | 146 |
| `__init__` | FunctionDef | 90 | 91 |
| `drag_coefficient` | FunctionDef | 93 | 122 |
| `lift_coefficient` | FunctionDef | 124 | 146 |
| `TrajectorySimulator` | ClassDef | 153 | 327 |
| `__init__` | FunctionDef | 159 | 167 |
| `compute_forces` | FunctionDef | 169 | 211 |
| `_derivatives` | FunctionDef | 213 | 233 |
| `simulate` | FunctionDef | 235 | 327 |
| `PitcherMechanism` | ClassDef | 334 | 520 |
| `__init__` | FunctionDef | 348 | 356 |
| `_normalize_to_range` | FunctionDef | 358 | 362 |
| `decode_action` | FunctionDef | 364 | 426 |
| `pitch` | FunctionDef | 428 | 479 |
| `simulate_pitch` | FunctionDef | 481 | 520 |
| `StrikeZone` | ClassDef | 527 | 606 |
| `__init__` | FunctionDef | 535 | 553 |
| `is_strike` | FunctionDef | 555 | 568 |
| `distance_to_zone` | FunctionDef | 570 | 584 |
| `zone_location` | FunctionDef | 586 | 606 |

## 전체 원문

````text
    1 | """
    2 | pitcher_mechanism.py — End-to-End 투수 물리 엔진
    3 | 
    4 | 공의 비행 역학(Magnus Effect, Drag, Gravity)을 수치적분(RK4)으로 시뮬레이션합니다.
    5 | 신경망의 연속 액션 벡터를 물리 초기조건으로 변환하여 궤적을 계산합니다.
    6 | 
    7 | 핵심 물리 방정식:
    8 |     F_gravity = (0, 0, -m*g)
    9 |     F_drag    = -½ ρ A C_d |v| v
   10 |     F_magnus  = ½ ρ A C_L (r/|v|) (ω × v)
   11 | """
   12 | 
   13 | import numpy as np
   14 | from dataclasses import dataclass, field
   15 | from typing import Optional
   16 | 
   17 | 
   18 | # ──────────────────────────────────────────────────────────────
   19 | #  물리 상수 및 야구공 파라미터
   20 | # ──────────────────────────────────────────────────────────────
   21 | 
   22 | @dataclass
   23 | class BallPhysics:
   24 |     """야구공의 물리 상수를 관리하는 데이터 클래스.
   25 | 
   26 |     MLB 공인구 기준값을 기본으로 사용합니다.
   27 |     """
   28 | 
   29 |     mass: float = 0.145          # 공 질량 (kg), MLB 규격: 141.7~148.8g
   30 |     radius: float = 0.0366       # 공 반지름 (m), 둘레 약 23cm
   31 |     air_density: float = 1.225   # 공기 밀도 (kg/m³), 해수면 표준 대기
   32 |     gravity: float = 9.81        # 중력 가속도 (m/s²)
   33 | 
   34 |     # 유도되는 물리량 (post_init에서 계산)
   35 |     cross_section_area: float = field(init=False)
   36 |     circumference: float = field(init=False)
   37 | 
   38 |     def __post_init__(self):
   39 |         self.cross_section_area = np.pi * self.radius ** 2
   40 |         self.circumference = 2.0 * np.pi * self.radius
   41 | 
   42 | 
   43 | @dataclass
   44 | class PitchConfig:
   45 |     """투구 설정 범위를 정의하는 데이터 클래스.
   46 | 
   47 |     신경망 액션의 [-1, 1] 범위를 실제 물리값으로 매핑할 때 사용됩니다.
   48 |     """
   49 | 
   50 |     # 릴리스 속도 (m/s): MLB 범위 약 30~47 m/s (108~169 km/h)
   51 |     v_release_min: float = 28.0
   52 |     v_release_max: float = 47.0
   53 | 
   54 |     # 목표 위치 오프셋 (m): 스트라이크존 기준 좌우/상하
   55 |     target_x_min: float = -0.35   # 좌측 한계
   56 |     target_x_max: float = 0.35    # 우측 한계
   57 |     target_z_min: float = 0.45    # 하단 (무릎 높이)
   58 |     target_z_max: float = 1.05    # 상단 (가슴 높이)
   59 | 
   60 |     # 스핀 (RPM): MLB 범위 약 1000~3200 RPM
   61 |     spin_rate_min: float = 800.0
   62 |     spin_rate_max: float = 3200.0
   63 | 
   64 |     # 스핀 축 각도 (rad): 0 ~ 2π (시계방향 기준)
   65 |     spin_axis_min: float = 0.0
   66 |     spin_axis_max: float = 2.0 * np.pi
   67 | 
   68 |     # 릴리스 위치 (투수 마운드 → 홈플레이트 방향)
   69 |     release_position: np.ndarray = field(
   70 |         default_factory=lambda: np.array([0.0, 18.44, 1.85])
   71 |         # x=0 (중앙), y=18.44m (마운드 거리), z=1.85m (릴리스 높이)
   72 |     )
   73 | 
   74 |     # 홈플레이트 위치
   75 |     plate_position: np.ndarray = field(
   76 |         default_factory=lambda: np.array([0.0, 0.0, 0.0])
   77 |     )
   78 | 
   79 | 
   80 | # ──────────────────────────────────────────────────────────────
   81 | #  공기역학 계수 모델
   82 | # ──────────────────────────────────────────────────────────────
   83 | 
   84 | class AerodynamicsModel:
   85 |     """공기역학 계수(Cd, Cl)를 계산하는 모델.
   86 | 
   87 |     Reynolds 수와 스핀 파라미터에 기반하여 가변 계수를 제공합니다.
   88 |     """
   89 | 
   90 |     def __init__(self, ball: BallPhysics):
   91 |         self.ball = ball
   92 | 
   93 |     def drag_coefficient(self, v_mag: float) -> float:
   94 |         """Reynolds 수 기반 항력 계수 C_d를 계산합니다.
   95 | 
   96 |         MLB 야구공의 실험적 데이터에 기반한 모델:
   97 |         - 저속(< 25 m/s): C_d ≈ 0.50 (층류 경계층)
   98 |         - 중속(25~35 m/s): C_d ≈ 0.35~0.45 (전이 영역)
   99 |         - 고속(> 35 m/s): C_d ≈ 0.30~0.35 (난류 경계층, 드래그 크라이시스)
  100 | 
  101 |         Args:
  102 |             v_mag: 공의 속력 (m/s)
  103 | 
  104 |         Returns:
  105 |             항력 계수 C_d
  106 |         """
  107 |         if v_mag < 1e-6:
  108 |             return 0.47
  109 | 
  110 |         # 실험적 피팅 (Alan Nathan의 연구 기반)
  111 |         # 속도가 증가하면 drag crisis로 인해 Cd가 감소
  112 |         v_ref = 35.0  # 참조 속도
  113 |         cd_low = 0.50
  114 |         cd_high = 0.30
  115 |         transition_width = 8.0
  116 | 
  117 |         # Sigmoid 전이 모델
  118 |         x = (v_mag - v_ref) / transition_width
  119 |         sigmoid = 1.0 / (1.0 + np.exp(-x))
  120 |         cd = cd_low + (cd_high - cd_low) * sigmoid
  121 | 
  122 |         return float(cd)
  123 | 
  124 |     def lift_coefficient(self, v_mag: float, spin_rate_rpm: float) -> float:
  125 |         """스핀 파라미터 기반 양력(마그누스) 계수 C_L을 계산합니다.
  126 | 
  127 |         스핀 파라미터 S = rω/v 에 비례하며, 실험적 상한이 존재합니다.
  128 | 
  129 |         Args:
  130 |             v_mag: 공의 속력 (m/s)
  131 |             spin_rate_rpm: 스핀 속도 (RPM)
  132 | 
  133 |         Returns:
  134 |             양력 계수 C_L
  135 |         """
  136 |         if v_mag < 1e-6:
  137 |             return 0.0
  138 | 
  139 |         omega = spin_rate_rpm * 2.0 * np.pi / 60.0  # RPM → rad/s
  140 |         spin_param = self.ball.radius * omega / v_mag
  141 | 
  142 |         # 실험적 피팅: C_L = min(a * S, C_L_max)
  143 |         # Adair(2002) 모델 기반
  144 |         cl = min(1.5 * spin_param, 0.40)
  145 | 
  146 |         return float(cl)
  147 | 
  148 | 
  149 | # ──────────────────────────────────────────────────────────────
  150 | #  궤적 시뮬레이션 엔진
  151 | # ──────────────────────────────────────────────────────────────
  152 | 
  153 | class TrajectorySimulator:
  154 |     """RK4 수치적분 기반 공 궤적 시뮬레이터.
  155 | 
  156 |     중력, 항력, 마그누스 힘을 동시에 적용하여 3D 궤적을 계산합니다.
  157 |     """
  158 | 
  159 |     def __init__(self, ball: Optional[BallPhysics] = None, dt: float = 0.001):
  160 |         """
  161 |         Args:
  162 |             ball: 야구공 물리 파라미터 (None이면 기본값 사용)
  163 |             dt: 시뮬레이션 시간 간격 (초). 고속 충돌을 위해 1ms 권장.
  164 |         """
  165 |         self.ball = ball or BallPhysics()
  166 |         self.aero = AerodynamicsModel(self.ball)
  167 |         self.dt = dt
  168 | 
  169 |     def compute_forces(
  170 |         self,
  171 |         position: np.ndarray,
  172 |         velocity: np.ndarray,
  173 |         spin_vector: np.ndarray,
  174 |         spin_rate_rpm: float,
  175 |     ) -> np.ndarray:
  176 |         """현재 상태에서 공에 작용하는 총 힘 벡터를 계산합니다.
  177 | 
  178 |         Args:
  179 |             position: 공의 3D 위치 [x, y, z] (m)
  180 |             velocity: 공의 3D 속도 [vx, vy, vz] (m/s)
  181 |             spin_vector: 정규화된 스핀 축 벡터 [sx, sy, sz]
  182 |             spin_rate_rpm: 스핀 속도 (RPM)
  183 | 
  184 |         Returns:
  185 |             총 힘 벡터 [Fx, Fy, Fz] (N)
  186 |         """
  187 |         v_mag = np.linalg.norm(velocity)
  188 |         m = self.ball.mass
  189 |         rho = self.ball.air_density
  190 |         A = self.ball.cross_section_area
  191 |         r = self.ball.radius
  192 | 
  193 |         # 1. 중력
  194 |         f_gravity = np.array([0.0, 0.0, -m * self.ball.gravity])
  195 | 
  196 |         if v_mag < 1e-6:
  197 |             return f_gravity
  198 | 
  199 |         # 2. 항력 (속도 반대 방향)
  200 |         cd = self.aero.drag_coefficient(v_mag)
  201 |         f_drag = -0.5 * rho * A * cd * v_mag * velocity
  202 | 
  203 |         # 3. 마그누스 힘 (ω × v 방향)
  204 |         cl = self.aero.lift_coefficient(v_mag, spin_rate_rpm)
  205 |         omega_vec = spin_vector * (spin_rate_rpm * 2.0 * np.pi / 60.0)
  206 |         magnus_dir = np.cross(omega_vec, velocity)
  207 |         magnus_mag = 0.5 * rho * A * cl * v_mag
  208 |         f_magnus = magnus_mag * magnus_dir / (np.linalg.norm(magnus_dir) + 1e-10) \
  209 |             if np.linalg.norm(magnus_dir) > 1e-10 else np.zeros(3)
  210 | 
  211 |         return f_gravity + f_drag + f_magnus
  212 | 
  213 |     def _derivatives(
  214 |         self,
  215 |         state: np.ndarray,
  216 |         spin_vector: np.ndarray,
  217 |         spin_rate_rpm: float,
  218 |     ) -> np.ndarray:
  219 |         """상태 벡터의 시간 미분을 계산합니다 (ODE 우변).
  220 | 
  221 |         Args:
  222 |             state: [x, y, z, vx, vy, vz]
  223 |             spin_vector: 정규화된 스핀 축 벡터
  224 |             spin_rate_rpm: 스핀 속도 (RPM)
  225 | 
  226 |         Returns:
  227 |             [vx, vy, vz, ax, ay, az]
  228 |         """
  229 |         pos = state[:3]
  230 |         vel = state[3:]
  231 |         forces = self.compute_forces(pos, vel, spin_vector, spin_rate_rpm)
  232 |         accel = forces / self.ball.mass
  233 |         return np.concatenate([vel, accel])
  234 | 
  235 |     def simulate(
  236 |         self,
  237 |         initial_position: np.ndarray,
  238 |         initial_velocity: np.ndarray,
  239 |         spin_vector: np.ndarray,
  240 |         spin_rate_rpm: float,
  241 |         max_time: float = 1.0,
  242 |         y_stop: float = 0.0,
  243 |     ) -> dict:
  244 |         """RK4 수치적분으로 공의 궤적을 시뮬레이션합니다.
  245 | 
  246 |         Args:
  247 |             initial_position: 릴리스 위치 [x, y, z] (m)
  248 |             initial_velocity: 릴리스 속도 [vx, vy, vz] (m/s)
  249 |             spin_vector: 정규화된 스핀 축 벡터 [sx, sy, sz]
  250 |             spin_rate_rpm: 스핀 속도 (RPM)
  251 |             max_time: 최대 시뮬레이션 시간 (초)
  252 |             y_stop: y좌표가 이 값 이하이면 시뮬레이션 종료 (홈플레이트 도달)
  253 | 
  254 |         Returns:
  255 |             dict with keys:
  256 |                 'positions': (N, 3) 위치 배열
  257 |                 'velocities': (N, 3) 속도 배열
  258 |                 'times': (N,) 시간 배열
  259 |                 'forces_history': (N, 3) 각 시점 총 힘
  260 |                 'final_position': (3,) 최종 위치
  261 |                 'final_velocity': (3,) 최종 속도
  262 |                 'flight_time': float 비행 시간
  263 |                 'plate_crossing': (3,) y=0 통과 위치 (보간)
  264 |         """
  265 |         state = np.concatenate([initial_position, initial_velocity])
  266 |         dt = self.dt
  267 | 
  268 |         positions = [initial_position.copy()]
  269 |         velocities = [initial_velocity.copy()]
  270 |         forces_history = [self.compute_forces(
  271 |             initial_position, initial_velocity, spin_vector, spin_rate_rpm
  272 |         )]
  273 |         times = [0.0]
  274 | 
  275 |         t = 0.0
  276 |         n_steps = int(max_time / dt)
  277 | 
  278 |         for _ in range(n_steps):
  279 |             # RK4 적분
  280 |             k1 = self._derivatives(state, spin_vector, spin_rate_rpm)
  281 |             k2 = self._derivatives(state + 0.5 * dt * k1, spin_vector, spin_rate_rpm)
  282 |             k3 = self._derivatives(state + 0.5 * dt * k2, spin_vector, spin_rate_rpm)
  283 |             k4 = self._derivatives(state + dt * k3, spin_vector, spin_rate_rpm)
  284 | 
  285 |             state = state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
  286 |             t += dt
  287 | 
  288 |             pos = state[:3].copy()
  289 |             vel = state[3:].copy()
  290 | 
  291 |             positions.append(pos)
  292 |             velocities.append(vel)
  293 |             forces_history.append(
  294 |                 self.compute_forces(pos, vel, spin_vector, spin_rate_rpm)
  295 |             )
  296 |             times.append(t)
  297 | 
  298 |             # 홈플레이트 도달 판정 (y ≤ y_stop)
  299 |             if pos[1] <= y_stop:
  300 |                 break
  301 | 
  302 |             # 지면 충돌 방지 (z < -1.0)
  303 |             if pos[2] < -1.0:
  304 |                 break
  305 | 
  306 |         positions = np.array(positions)
  307 |         velocities = np.array(velocities)
  308 |         forces_history = np.array(forces_history)
  309 |         times = np.array(times)
  310 | 
  311 |         # y=0 통과 지점 선형 보간
  312 |         plate_crossing = positions[-1][:3].copy()
  313 |         if len(positions) >= 2 and positions[-2][1] > y_stop >= positions[-1][1]:
  314 |             y1, y2 = positions[-2][1], positions[-1][1]
  315 |             alpha = (y_stop - y1) / (y2 - y1 + 1e-10)
  316 |             plate_crossing = positions[-2] + alpha * (positions[-1] - positions[-2])
  317 | 
  318 |         return {
  319 |             'positions': positions,
  320 |             'velocities': velocities,
  321 |             'times': times,
  322 |             'forces_history': forces_history,
  323 |             'final_position': positions[-1].copy(),
  324 |             'final_velocity': velocities[-1].copy(),
  325 |             'flight_time': times[-1],
  326 |             'plate_crossing': plate_crossing,
  327 |         }
  328 | 
  329 | 
  330 | # ──────────────────────────────────────────────────────────────
  331 | #  투수 메커니즘 (E2E Action → 물리 시뮬레이션)
  332 | # ──────────────────────────────────────────────────────────────
  333 | 
  334 | class PitcherMechanism:
  335 |     """End-to-End 투수 물리 메커니즘.
  336 | 
  337 |     신경망의 연속 액션 벡터 [-1, 1]^5를 실제 물리 파라미터로 변환하고,
  338 |     궤적 시뮬레이션을 수행합니다.
  339 | 
  340 |     Action Vector:
  341 |         [0] v_release:   릴리스 속도 (normalized)
  342 |         [1] theta_x:     목표 x 오프셋 (normalized)
  343 |         [2] theta_z:     목표 z 오프셋 (normalized)
  344 |         [3] spin_rate:   스핀 속도 (normalized)
  345 |         [4] spin_axis:   스핀 축 각도 (normalized)
  346 |     """
  347 | 
  348 |     def __init__(
  349 |         self,
  350 |         ball: Optional[BallPhysics] = None,
  351 |         config: Optional[PitchConfig] = None,
  352 |         dt: float = 0.001,
  353 |     ):
  354 |         self.ball = ball or BallPhysics()
  355 |         self.config = config or PitchConfig()
  356 |         self.simulator = TrajectorySimulator(self.ball, dt)
  357 | 
  358 |     def _normalize_to_range(
  359 |         self, value: float, low: float, high: float
  360 |     ) -> float:
  361 |         """[-1, 1] 범위를 [low, high] 범위로 매핑합니다."""
  362 |         return low + (value + 1.0) * 0.5 * (high - low)
  363 | 
  364 |     def decode_action(self, action: np.ndarray) -> dict:
  365 |         """신경망 액션 벡터를 물리 파라미터로 변환합니다.
  366 | 
  367 |         Args:
  368 |             action: 5차원 연속 액션 벡터, 각 성분 ∈ [-1, 1]
  369 | 
  370 |         Returns:
  371 |             dict with physical parameters:
  372 |                 'v_release': 릴리스 속도 (m/s)
  373 |                 'target_x': 목표 x 오프셋 (m)
  374 |                 'target_z': 목표 z 오프셋 (m)
  375 |                 'spin_rate_rpm': 스핀 속도 (RPM)
  376 |                 'spin_axis_angle': 스핀 축 각도 (rad)
  377 |                 'spin_vector': 3D 스핀 축 벡터 (정규화)
  378 |                 'initial_velocity': 3D 초기 속도 벡터 (m/s)
  379 |         """
  380 |         cfg = self.config
  381 |         action = np.clip(action, -1.0, 1.0)
  382 | 
  383 |         v_release = self._normalize_to_range(
  384 |             action[0], cfg.v_release_min, cfg.v_release_max
  385 |         )
  386 |         target_x = self._normalize_to_range(
  387 |             action[1], cfg.target_x_min, cfg.target_x_max
  388 |         )
  389 |         target_z = self._normalize_to_range(
  390 |             action[2], cfg.target_z_min, cfg.target_z_max
  391 |         )
  392 |         spin_rate_rpm = self._normalize_to_range(
  393 |             action[3], cfg.spin_rate_min, cfg.spin_rate_max
  394 |         )
  395 |         spin_axis_angle = self._normalize_to_range(
  396 |             action[4], cfg.spin_axis_min, cfg.spin_axis_max
  397 |         )
  398 | 
  399 |         # 스핀 축 벡터 계산 (구면좌표계에서 단위 벡터)
  400 |         # spin_axis_angle은 y-z 평면에서의 회전각
  401 |         spin_vector = np.array([
  402 |             np.sin(spin_axis_angle),    # x 성분 (좌우 스핀)
  403 |             0.0,                        # y 성분 (전후 — 투구 방향이므로 0)
  404 |             np.cos(spin_axis_angle),    # z 성분 (상하 스핀)
  405 |         ])
  406 |         spin_vector = spin_vector / (np.linalg.norm(spin_vector) + 1e-10)
  407 | 
  408 |         # 초기 속도 벡터 계산
  409 |         # 릴리스 → 타겟 방향으로 속도 벡터 생성
  410 |         release_pos = cfg.release_position.copy()
  411 |         target_pos = np.array([target_x, 0.0, target_z])  # 홈플레이트 기준
  412 | 
  413 |         direction = target_pos - release_pos
  414 |         direction = direction / (np.linalg.norm(direction) + 1e-10)
  415 |         initial_velocity = direction * v_release
  416 | 
  417 |         return {
  418 |             'v_release': v_release,
  419 |             'target_x': target_x,
  420 |             'target_z': target_z,
  421 |             'spin_rate_rpm': spin_rate_rpm,
  422 |             'spin_axis_angle': spin_axis_angle,
  423 |             'spin_vector': spin_vector,
  424 |             'initial_velocity': initial_velocity,
  425 |             'release_position': release_pos,
  426 |         }
  427 | 
  428 |     def pitch(self, action: np.ndarray) -> dict:
  429 |         """E2E 투구를 실행합니다: 액션 → 물리 파라미터 → 궤적 시뮬레이션.
  430 | 
  431 |         Args:
  432 |             action: 5차원 연속 액션 벡터, 각 성분 ∈ [-1, 1]
  433 | 
  434 |         Returns:
  435 |             dict with:
  436 |                 'params': 물리 파라미터 (decode_action의 결과)
  437 |                 'trajectory': 궤적 시뮬레이션 결과 (simulate의 결과)
  438 |                 'plate_x': 홈플레이트 통과 x 좌표 (m)
  439 |                 'plate_z': 홈플레이트 통과 z 좌표 (m)
  440 |                 'arrival_speed': 도착 속도 (m/s)
  441 |                 'arrival_speed_kmh': 도착 속도 (km/h)
  442 |                 'movement_x': 수평 무브먼트 (m) — 직구 대비 변화량
  443 |                 'movement_z': 수직 무브먼트 (m) — 직구 대비 변화량
  444 |         """
  445 |         params = self.decode_action(action)
  446 | 
  447 |         trajectory = self.simulator.simulate(
  448 |             initial_position=params['release_position'],
  449 |             initial_velocity=params['initial_velocity'],
  450 |             spin_vector=params['spin_vector'],
  451 |             spin_rate_rpm=params['spin_rate_rpm'],
  452 |             max_time=1.0,
  453 |             y_stop=0.0,
  454 |         )
  455 | 
  456 |         plate = trajectory['plate_crossing']
  457 |         final_vel = trajectory['final_velocity']
  458 | 
  459 |         # 무브먼트 계산 (스핀 없는 직구 대비)
  460 |         no_spin_traj = self.simulator.simulate(
  461 |             initial_position=params['release_position'],
  462 |             initial_velocity=params['initial_velocity'],
  463 |             spin_vector=np.array([0.0, 0.0, 0.0]),
  464 |             spin_rate_rpm=0.0,
  465 |             max_time=1.0,
  466 |             y_stop=0.0,
  467 |         )
  468 |         no_spin_plate = no_spin_traj['plate_crossing']
  469 | 
  470 |         return {
  471 |             'params': params,
  472 |             'trajectory': trajectory,
  473 |             'plate_x': float(plate[0]),
  474 |             'plate_z': float(plate[2]),
  475 |             'arrival_speed': float(np.linalg.norm(final_vel)),
  476 |             'arrival_speed_kmh': float(np.linalg.norm(final_vel) * 3.6),
  477 |             'movement_x': float(plate[0] - no_spin_plate[0]),
  478 |             'movement_z': float(plate[2] - no_spin_plate[2]),
  479 |         }
  480 | 
  481 |     def simulate_pitch(
  482 |         self,
  483 |         v_release: float,
  484 |         target_x: float,
  485 |         target_z: float,
  486 |         spin_rate_rpm: float,
  487 |         spin_vector: np.ndarray,
  488 |     ) -> np.ndarray:
  489 |         """직접 물리 파라미터를 지정하여 궤적을 시뮬레이션합니다.
  490 | 
  491 |         검증/테스트 용도로 사용됩니다.
  492 | 
  493 |         Args:
  494 |             v_release: 릴리스 속도 (m/s)
  495 |             target_x: 목표 x 위치 (m)
  496 |             target_z: 목표 z 위치 (m)
  497 |             spin_rate_rpm: 스핀 속도 (RPM)
  498 |             spin_vector: 3D 스핀 축 벡터
  499 | 
  500 |         Returns:
  501 |             (N, 3) 위치 배열
  502 |         """
  503 |         release_pos = self.config.release_position.copy()
  504 |         target_pos = np.array([target_x, 0.0, target_z])
  505 | 
  506 |         direction = target_pos - release_pos
  507 |         direction = direction / (np.linalg.norm(direction) + 1e-10)
  508 |         initial_velocity = direction * v_release
  509 | 
  510 |         spin_vector = spin_vector / (np.linalg.norm(spin_vector) + 1e-10)
  511 | 
  512 |         result = self.simulator.simulate(
  513 |             initial_position=release_pos,
  514 |             initial_velocity=initial_velocity,
  515 |             spin_vector=spin_vector,
  516 |             spin_rate_rpm=spin_rate_rpm,
  517 |             max_time=1.0,
  518 |             y_stop=0.0,
  519 |         )
  520 |         return result['positions']
  521 | 
  522 | 
  523 | # ──────────────────────────────────────────────────────────────
  524 | #  스트라이크존 판정
  525 | # ──────────────────────────────────────────────────────────────
  526 | 
  527 | class StrikeZone:
  528 |     """스트라이크존 판정 엔진.
  529 | 
  530 |     MLB 규정 기반:
  531 |     - 좌우: 홈플레이트 폭 (17인치 = 0.4318m), ±반지름 보정
  532 |     - 상하: 타자 무릎~가슴 (약 0.45m~1.05m)
  533 |     """
  534 | 
  535 |     def __init__(
  536 |         self,
  537 |         x_min: float = -0.2159,
  538 |         x_max: float = 0.2159,
  539 |         z_min: float = 0.45,
  540 |         z_max: float = 1.05,
  541 |         ball_radius: float = 0.0366,
  542 |     ):
  543 |         # 공의 반지름 보정 (공의 가장자리가 존에 걸치면 스트라이크)
  544 |         self.x_min = x_min - ball_radius
  545 |         self.x_max = x_max + ball_radius
  546 |         self.z_min = z_min - ball_radius
  547 |         self.z_max = z_max + ball_radius
  548 | 
  549 |         # 보정 전 원본 (시각화용)
  550 |         self.raw_x_min = x_min
  551 |         self.raw_x_max = x_max
  552 |         self.raw_z_min = z_min
  553 |         self.raw_z_max = z_max
  554 | 
  555 |     def is_strike(self, plate_x: float, plate_z: float) -> bool:
  556 |         """홈플레이트 통과 위치가 스트라이크존 내인지 판정합니다.
  557 | 
  558 |         Args:
  559 |             plate_x: 홈플레이트 통과 x 좌표 (m)
  560 |             plate_z: 홈플레이트 통과 z 좌표 (m)
  561 | 
  562 |         Returns:
  563 |             True if strike
  564 |         """
  565 |         return (
  566 |             self.x_min <= plate_x <= self.x_max
  567 |             and self.z_min <= plate_z <= self.z_max
  568 |         )
  569 | 
  570 |     def distance_to_zone(self, plate_x: float, plate_z: float) -> float:
  571 |         """스트라이크존까지의 거리를 계산합니다 (존 밖일 때).
  572 | 
  573 |         존 내부에 있으면 0.0을 반환합니다.
  574 | 
  575 |         Args:
  576 |             plate_x: 홈플레이트 통과 x 좌표 (m)
  577 |             plate_z: 홈플레이트 통과 z 좌표 (m)
  578 | 
  579 |         Returns:
  580 |             존까지의 유클리드 거리 (m)
  581 |         """
  582 |         dx = max(self.x_min - plate_x, 0.0, plate_x - self.x_max)
  583 |         dz = max(self.z_min - plate_z, 0.0, plate_z - self.z_max)
  584 |         return np.sqrt(dx ** 2 + dz ** 2)
  585 | 
  586 |     def zone_location(self, plate_x: float, plate_z: float) -> tuple:
  587 |         """9분할 존(3×3) 기준으로 어느 위치에 해당하는지 반환합니다.
  588 | 
  589 |         Args:
  590 |             plate_x: 홈플레이트 통과 x 좌표 (m)
  591 |             plate_z: 홈플레이트 통과 z 좌표 (m)
  592 | 
  593 |         Returns:
  594 |             (col, row) 튜플, 0-indexed. col: 0=좌, 1=중, 2=우, row: 0=하, 1=중, 2=상
  595 |             스트라이크존 밖이면 (-1, -1)
  596 |         """
  597 |         if not self.is_strike(plate_x, plate_z):
  598 |             return (-1, -1)
  599 | 
  600 |         x_range = self.x_max - self.x_min
  601 |         z_range = self.z_max - self.z_min
  602 | 
  603 |         col = min(int((plate_x - self.x_min) / (x_range / 3.0)), 2)
  604 |         row = min(int((plate_z - self.z_min) / (z_range / 3.0)), 2)
  605 | 
  606 |         return (col, row)
````
