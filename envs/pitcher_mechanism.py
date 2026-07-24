"""
pitcher_mechanism.py — End-to-End 투수 물리 엔진

공의 비행 역학(Magnus Effect, Drag, Gravity)을 수치적분(RK4)으로 시뮬레이션합니다.
신경망의 연속 액션 벡터를 물리 초기조건으로 변환하여 궤적을 계산합니다.

핵심 물리 방정식:
    F_gravity = (0, 0, -m*g)
    F_drag    = -½ ρ A C_d |v| v
    F_magnus  = ½ ρ A C_L (r/|v|) (ω × v)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────
#  물리 상수 및 야구공 파라미터
# ──────────────────────────────────────────────────────────────

@dataclass
class BallPhysics:
    """야구공의 물리 상수를 관리하는 데이터 클래스.

    MLB 공인구 기준값을 기본으로 사용합니다.
    """

    mass: float = 0.145          # 공 질량 (kg), MLB 규격: 141.7~148.8g
    radius: float = 0.0366       # 공 반지름 (m), 둘레 약 23cm
    air_density: float = 1.225   # 공기 밀도 (kg/m³), 해수면 표준 대기
    gravity: float = 9.81        # 중력 가속도 (m/s²)

    # 유도되는 물리량 (post_init에서 계산)
    cross_section_area: float = field(init=False)
    circumference: float = field(init=False)

    def __post_init__(self):
        self.cross_section_area = np.pi * self.radius ** 2
        self.circumference = 2.0 * np.pi * self.radius


@dataclass
class PitchConfig:
    """투구 설정 범위를 정의하는 데이터 클래스.

    신경망 액션의 [-1, 1] 범위를 실제 물리값으로 매핑할 때 사용됩니다.
    """

    # 릴리스 속도 (m/s): MLB 범위 약 30~47 m/s (108~169 km/h)
    v_release_min: float = 28.0
    v_release_max: float = 47.0

    # 목표 위치 오프셋 (m): 스트라이크존 기준 좌우/상하
    target_x_min: float = -0.35   # 좌측 한계
    target_x_max: float = 0.35    # 우측 한계
    target_z_min: float = 0.45    # 하단 (무릎 높이)
    target_z_max: float = 1.05    # 상단 (가슴 높이)

    # 스핀 (RPM): MLB 범위 약 1000~3200 RPM
    spin_rate_min: float = 800.0
    spin_rate_max: float = 3200.0

    # 스핀 축 각도 (rad): 0 ~ 2π (시계방향 기준)
    spin_axis_min: float = 0.0
    spin_axis_max: float = 2.0 * np.pi

    # 릴리스 위치 (투수 마운드 → 홈플레이트 방향)
    release_position: np.ndarray = field(
        default_factory=lambda: np.array([0.0, 18.44, 1.85])
        # x=0 (중앙), y=18.44m (마운드 거리), z=1.85m (릴리스 높이)
    )

    # 홈플레이트 위치
    plate_position: np.ndarray = field(
        default_factory=lambda: np.array([0.0, 0.0, 0.0])
    )


# ──────────────────────────────────────────────────────────────
#  공기역학 계수 모델
# ──────────────────────────────────────────────────────────────

class AerodynamicsModel:
    """공기역학 계수(Cd, Cl)를 계산하는 모델.

    Reynolds 수와 스핀 파라미터에 기반하여 가변 계수를 제공합니다.
    """

    def __init__(self, ball: BallPhysics):
        self.ball = ball

    def drag_coefficient(self, v_mag: float) -> float:
        """Reynolds 수 기반 항력 계수 C_d를 계산합니다.

        MLB 야구공의 실험적 데이터에 기반한 모델:
        - 저속(< 25 m/s): C_d ≈ 0.50 (층류 경계층)
        - 중속(25~35 m/s): C_d ≈ 0.35~0.45 (전이 영역)
        - 고속(> 35 m/s): C_d ≈ 0.30~0.35 (난류 경계층, 드래그 크라이시스)

        Args:
            v_mag: 공의 속력 (m/s)

        Returns:
            항력 계수 C_d
        """
        if v_mag < 1e-6:
            return 0.47

        # 실험적 피팅 (Alan Nathan의 연구 기반)
        # 속도가 증가하면 drag crisis로 인해 Cd가 감소
        v_ref = 35.0  # 참조 속도
        cd_low = 0.50
        cd_high = 0.30
        transition_width = 8.0

        # Sigmoid 전이 모델
        x = (v_mag - v_ref) / transition_width
        sigmoid = 1.0 / (1.0 + np.exp(-x))
        cd = cd_low + (cd_high - cd_low) * sigmoid

        return float(cd)

    def lift_coefficient(self, v_mag: float, spin_rate_rpm: float) -> float:
        """스핀 파라미터 기반 양력(마그누스) 계수 C_L을 계산합니다.

        스핀 파라미터 S = rω/v 에 비례하며, 실험적 상한이 존재합니다.

        Args:
            v_mag: 공의 속력 (m/s)
            spin_rate_rpm: 스핀 속도 (RPM)

        Returns:
            양력 계수 C_L
        """
        if v_mag < 1e-6:
            return 0.0

        omega = spin_rate_rpm * 2.0 * np.pi / 60.0  # RPM → rad/s
        spin_param = self.ball.radius * omega / v_mag

        # 실험적 피팅: C_L = min(a * S, C_L_max)
        # Adair(2002) 모델 기반
        cl = min(1.5 * spin_param, 0.40)

        return float(cl)


# ──────────────────────────────────────────────────────────────
#  궤적 시뮬레이션 엔진
# ──────────────────────────────────────────────────────────────

class TrajectorySimulator:
    """RK4 수치적분 기반 공 궤적 시뮬레이터.

    중력, 항력, 마그누스 힘을 동시에 적용하여 3D 궤적을 계산합니다.
    """

    def __init__(self, ball: Optional[BallPhysics] = None, dt: float = 0.001):
        """
        Args:
            ball: 야구공 물리 파라미터 (None이면 기본값 사용)
            dt: 시뮬레이션 시간 간격 (초). 고속 충돌을 위해 1ms 권장.
        """
        self.ball = ball or BallPhysics()
        self.aero = AerodynamicsModel(self.ball)
        self.dt = dt

    def compute_forces(
        self,
        position: np.ndarray,
        velocity: np.ndarray,
        spin_vector: np.ndarray,
        spin_rate_rpm: float,
    ) -> np.ndarray:
        """현재 상태에서 공에 작용하는 총 힘 벡터를 계산합니다.

        Args:
            position: 공의 3D 위치 [x, y, z] (m)
            velocity: 공의 3D 속도 [vx, vy, vz] (m/s)
            spin_vector: 정규화된 스핀 축 벡터 [sx, sy, sz]
            spin_rate_rpm: 스핀 속도 (RPM)

        Returns:
            총 힘 벡터 [Fx, Fy, Fz] (N)
        """
        v_mag = np.linalg.norm(velocity)
        m = self.ball.mass
        rho = self.ball.air_density
        A = self.ball.cross_section_area
        r = self.ball.radius

        # 1. 중력
        f_gravity = np.array([0.0, 0.0, -m * self.ball.gravity])

        if v_mag < 1e-6:
            return f_gravity

        # 2. 항력 (속도 반대 방향)
        cd = self.aero.drag_coefficient(v_mag)
        f_drag = -0.5 * rho * A * cd * v_mag * velocity

        # 3. 마그누스 힘 (ω × v 방향)
        cl = self.aero.lift_coefficient(v_mag, spin_rate_rpm)
        omega_vec = spin_vector * (spin_rate_rpm * 2.0 * np.pi / 60.0)
        magnus_dir = np.cross(omega_vec, velocity)
        magnus_mag = 0.5 * rho * A * cl * v_mag
        f_magnus = magnus_mag * magnus_dir / (np.linalg.norm(magnus_dir) + 1e-10) \
            if np.linalg.norm(magnus_dir) > 1e-10 else np.zeros(3)

        return f_gravity + f_drag + f_magnus

    def _derivatives(
        self,
        state: np.ndarray,
        spin_vector: np.ndarray,
        spin_rate_rpm: float,
    ) -> np.ndarray:
        """상태 벡터의 시간 미분을 계산합니다 (ODE 우변).

        Args:
            state: [x, y, z, vx, vy, vz]
            spin_vector: 정규화된 스핀 축 벡터
            spin_rate_rpm: 스핀 속도 (RPM)

        Returns:
            [vx, vy, vz, ax, ay, az]
        """
        pos = state[:3]
        vel = state[3:]
        forces = self.compute_forces(pos, vel, spin_vector, spin_rate_rpm)
        accel = forces / self.ball.mass
        return np.concatenate([vel, accel])

    def simulate(
        self,
        initial_position: np.ndarray,
        initial_velocity: np.ndarray,
        spin_vector: np.ndarray,
        spin_rate_rpm: float,
        max_time: float = 1.0,
        y_stop: float = 0.0,
    ) -> dict:
        """RK4 수치적분으로 공의 궤적을 시뮬레이션합니다.

        Args:
            initial_position: 릴리스 위치 [x, y, z] (m)
            initial_velocity: 릴리스 속도 [vx, vy, vz] (m/s)
            spin_vector: 정규화된 스핀 축 벡터 [sx, sy, sz]
            spin_rate_rpm: 스핀 속도 (RPM)
            max_time: 최대 시뮬레이션 시간 (초)
            y_stop: y좌표가 이 값 이하이면 시뮬레이션 종료 (홈플레이트 도달)

        Returns:
            dict with keys:
                'positions': (N, 3) 위치 배열
                'velocities': (N, 3) 속도 배열
                'times': (N,) 시간 배열
                'forces_history': (N, 3) 각 시점 총 힘
                'final_position': (3,) 최종 위치
                'final_velocity': (3,) 최종 속도
                'flight_time': float 비행 시간
                'plate_crossing': (3,) y=0 통과 위치 (보간)
        """
        state = np.concatenate([initial_position, initial_velocity])
        dt = self.dt

        positions = [initial_position.copy()]
        velocities = [initial_velocity.copy()]
        forces_history = [self.compute_forces(
            initial_position, initial_velocity, spin_vector, spin_rate_rpm
        )]
        times = [0.0]

        t = 0.0
        n_steps = int(max_time / dt)

        for _ in range(n_steps):
            # RK4 적분
            k1 = self._derivatives(state, spin_vector, spin_rate_rpm)
            k2 = self._derivatives(state + 0.5 * dt * k1, spin_vector, spin_rate_rpm)
            k3 = self._derivatives(state + 0.5 * dt * k2, spin_vector, spin_rate_rpm)
            k4 = self._derivatives(state + dt * k3, spin_vector, spin_rate_rpm)

            state = state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
            t += dt

            pos = state[:3].copy()
            vel = state[3:].copy()

            positions.append(pos)
            velocities.append(vel)
            forces_history.append(
                self.compute_forces(pos, vel, spin_vector, spin_rate_rpm)
            )
            times.append(t)

            # 홈플레이트 도달 판정 (y ≤ y_stop)
            if pos[1] <= y_stop:
                break

            # 지면 충돌 방지 (z < -1.0)
            if pos[2] < -1.0:
                break

        positions = np.array(positions)
        velocities = np.array(velocities)
        forces_history = np.array(forces_history)
        times = np.array(times)

        # y=0 통과 지점 선형 보간
        plate_crossing = positions[-1][:3].copy()
        if len(positions) >= 2 and positions[-2][1] > y_stop >= positions[-1][1]:
            y1, y2 = positions[-2][1], positions[-1][1]
            alpha = (y_stop - y1) / (y2 - y1 + 1e-10)
            plate_crossing = positions[-2] + alpha * (positions[-1] - positions[-2])

        return {
            'positions': positions,
            'velocities': velocities,
            'times': times,
            'forces_history': forces_history,
            'final_position': positions[-1].copy(),
            'final_velocity': velocities[-1].copy(),
            'flight_time': times[-1],
            'plate_crossing': plate_crossing,
        }


# ──────────────────────────────────────────────────────────────
#  투수 메커니즘 (E2E Action → 물리 시뮬레이션)
# ──────────────────────────────────────────────────────────────

class PitcherMechanism:
    """End-to-End 투수 물리 메커니즘.

    신경망의 연속 액션 벡터 [-1, 1]^5를 실제 물리 파라미터로 변환하고,
    궤적 시뮬레이션을 수행합니다.

    Action Vector:
        [0] v_release:   릴리스 속도 (normalized)
        [1] theta_x:     목표 x 오프셋 (normalized)
        [2] theta_z:     목표 z 오프셋 (normalized)
        [3] spin_rate:   스핀 속도 (normalized)
        [4] spin_axis:   스핀 축 각도 (normalized)
    """

    def __init__(
        self,
        ball: Optional[BallPhysics] = None,
        config: Optional[PitchConfig] = None,
        dt: float = 0.001,
    ):
        self.ball = ball or BallPhysics()
        self.config = config or PitchConfig()
        self.simulator = TrajectorySimulator(self.ball, dt)

    def _normalize_to_range(
        self, value: float, low: float, high: float
    ) -> float:
        """[-1, 1] 범위를 [low, high] 범위로 매핑합니다."""
        return low + (value + 1.0) * 0.5 * (high - low)

    def decode_action(self, action: np.ndarray) -> dict:
        """신경망 액션 벡터를 물리 파라미터로 변환합니다.

        Args:
            action: 5차원 연속 액션 벡터, 각 성분 ∈ [-1, 1]

        Returns:
            dict with physical parameters:
                'v_release': 릴리스 속도 (m/s)
                'target_x': 목표 x 오프셋 (m)
                'target_z': 목표 z 오프셋 (m)
                'spin_rate_rpm': 스핀 속도 (RPM)
                'spin_axis_angle': 스핀 축 각도 (rad)
                'spin_vector': 3D 스핀 축 벡터 (정규화)
                'initial_velocity': 3D 초기 속도 벡터 (m/s)
        """
        cfg = self.config
        action = np.clip(action, -1.0, 1.0)

        v_release = self._normalize_to_range(
            action[0], cfg.v_release_min, cfg.v_release_max
        )
        target_x = self._normalize_to_range(
            action[1], cfg.target_x_min, cfg.target_x_max
        )
        target_z = self._normalize_to_range(
            action[2], cfg.target_z_min, cfg.target_z_max
        )
        spin_rate_rpm = self._normalize_to_range(
            action[3], cfg.spin_rate_min, cfg.spin_rate_max
        )
        spin_axis_angle = self._normalize_to_range(
            action[4], cfg.spin_axis_min, cfg.spin_axis_max
        )

        # 스핀 축 벡터 계산 (구면좌표계에서 단위 벡터)
        # spin_axis_angle은 y-z 평면에서의 회전각
        spin_vector = np.array([
            np.sin(spin_axis_angle),    # x 성분 (좌우 스핀)
            0.0,                        # y 성분 (전후 — 투구 방향이므로 0)
            np.cos(spin_axis_angle),    # z 성분 (상하 스핀)
        ])
        spin_vector = spin_vector / (np.linalg.norm(spin_vector) + 1e-10)

        # 초기 속도 벡터 계산
        # 릴리스 → 타겟 방향으로 속도 벡터 생성
        release_pos = cfg.release_position.copy()
        target_pos = np.array([target_x, 0.0, target_z])  # 홈플레이트 기준

        direction = target_pos - release_pos
        direction = direction / (np.linalg.norm(direction) + 1e-10)
        initial_velocity = direction * v_release

        return {
            'v_release': v_release,
            'target_x': target_x,
            'target_z': target_z,
            'spin_rate_rpm': spin_rate_rpm,
            'spin_axis_angle': spin_axis_angle,
            'spin_vector': spin_vector,
            'initial_velocity': initial_velocity,
            'release_position': release_pos,
        }

    def pitch(self, action: np.ndarray) -> dict:
        """E2E 투구를 실행합니다: 액션 → 물리 파라미터 → 궤적 시뮬레이션.

        Args:
            action: 5차원 연속 액션 벡터, 각 성분 ∈ [-1, 1]

        Returns:
            dict with:
                'params': 물리 파라미터 (decode_action의 결과)
                'trajectory': 궤적 시뮬레이션 결과 (simulate의 결과)
                'plate_x': 홈플레이트 통과 x 좌표 (m)
                'plate_z': 홈플레이트 통과 z 좌표 (m)
                'arrival_speed': 도착 속도 (m/s)
                'arrival_speed_kmh': 도착 속도 (km/h)
                'movement_x': 수평 무브먼트 (m) — 직구 대비 변화량
                'movement_z': 수직 무브먼트 (m) — 직구 대비 변화량
        """
        params = self.decode_action(action)

        trajectory = self.simulator.simulate(
            initial_position=params['release_position'],
            initial_velocity=params['initial_velocity'],
            spin_vector=params['spin_vector'],
            spin_rate_rpm=params['spin_rate_rpm'],
            max_time=1.0,
            y_stop=0.0,
        )

        plate = trajectory['plate_crossing']
        final_vel = trajectory['final_velocity']

        # 무브먼트 계산 (스핀 없는 직구 대비)
        no_spin_traj = self.simulator.simulate(
            initial_position=params['release_position'],
            initial_velocity=params['initial_velocity'],
            spin_vector=np.array([0.0, 0.0, 0.0]),
            spin_rate_rpm=0.0,
            max_time=1.0,
            y_stop=0.0,
        )
        no_spin_plate = no_spin_traj['plate_crossing']

        return {
            'params': params,
            'trajectory': trajectory,
            'plate_x': float(plate[0]),
            'plate_z': float(plate[2]),
            'arrival_speed': float(np.linalg.norm(final_vel)),
            'arrival_speed_kmh': float(np.linalg.norm(final_vel) * 3.6),
            'movement_x': float(plate[0] - no_spin_plate[0]),
            'movement_z': float(plate[2] - no_spin_plate[2]),
        }

    def simulate_pitch(
        self,
        v_release: float,
        target_x: float,
        target_z: float,
        spin_rate_rpm: float,
        spin_vector: np.ndarray,
    ) -> np.ndarray:
        """직접 물리 파라미터를 지정하여 궤적을 시뮬레이션합니다.

        검증/테스트 용도로 사용됩니다.

        Args:
            v_release: 릴리스 속도 (m/s)
            target_x: 목표 x 위치 (m)
            target_z: 목표 z 위치 (m)
            spin_rate_rpm: 스핀 속도 (RPM)
            spin_vector: 3D 스핀 축 벡터

        Returns:
            (N, 3) 위치 배열
        """
        release_pos = self.config.release_position.copy()
        target_pos = np.array([target_x, 0.0, target_z])

        direction = target_pos - release_pos
        direction = direction / (np.linalg.norm(direction) + 1e-10)
        initial_velocity = direction * v_release

        spin_vector = spin_vector / (np.linalg.norm(spin_vector) + 1e-10)

        result = self.simulator.simulate(
            initial_position=release_pos,
            initial_velocity=initial_velocity,
            spin_vector=spin_vector,
            spin_rate_rpm=spin_rate_rpm,
            max_time=1.0,
            y_stop=0.0,
        )
        return result['positions']


# ──────────────────────────────────────────────────────────────
#  스트라이크존 판정
# ──────────────────────────────────────────────────────────────

class StrikeZone:
    """스트라이크존 판정 엔진.

    MLB 규정 기반:
    - 좌우: 홈플레이트 폭 (17인치 = 0.4318m), ±반지름 보정
    - 상하: 타자 무릎~가슴 (약 0.45m~1.05m)
    """

    def __init__(
        self,
        x_min: float = -0.2159,
        x_max: float = 0.2159,
        z_min: float = 0.45,
        z_max: float = 1.05,
        ball_radius: float = 0.0366,
    ):
        # 공의 반지름 보정 (공의 가장자리가 존에 걸치면 스트라이크)
        self.x_min = x_min - ball_radius
        self.x_max = x_max + ball_radius
        self.z_min = z_min - ball_radius
        self.z_max = z_max + ball_radius

        # 보정 전 원본 (시각화용)
        self.raw_x_min = x_min
        self.raw_x_max = x_max
        self.raw_z_min = z_min
        self.raw_z_max = z_max

    def is_strike(self, plate_x: float, plate_z: float) -> bool:
        """홈플레이트 통과 위치가 스트라이크존 내인지 판정합니다.

        Args:
            plate_x: 홈플레이트 통과 x 좌표 (m)
            plate_z: 홈플레이트 통과 z 좌표 (m)

        Returns:
            True if strike
        """
        return (
            self.x_min <= plate_x <= self.x_max
            and self.z_min <= plate_z <= self.z_max
        )

    def distance_to_zone(self, plate_x: float, plate_z: float) -> float:
        """스트라이크존까지의 거리를 계산합니다 (존 밖일 때).

        존 내부에 있으면 0.0을 반환합니다.

        Args:
            plate_x: 홈플레이트 통과 x 좌표 (m)
            plate_z: 홈플레이트 통과 z 좌표 (m)

        Returns:
            존까지의 유클리드 거리 (m)
        """
        dx = max(self.x_min - plate_x, 0.0, plate_x - self.x_max)
        dz = max(self.z_min - plate_z, 0.0, plate_z - self.z_max)
        return np.sqrt(dx ** 2 + dz ** 2)

    def zone_location(self, plate_x: float, plate_z: float) -> tuple:
        """9분할 존(3×3) 기준으로 어느 위치에 해당하는지 반환합니다.

        Args:
            plate_x: 홈플레이트 통과 x 좌표 (m)
            plate_z: 홈플레이트 통과 z 좌표 (m)

        Returns:
            (col, row) 튜플, 0-indexed. col: 0=좌, 1=중, 2=우, row: 0=하, 1=중, 2=상
            스트라이크존 밖이면 (-1, -1)
        """
        if not self.is_strike(plate_x, plate_z):
            return (-1, -1)

        x_range = self.x_max - self.x_min
        z_range = self.z_max - self.z_min

        col = min(int((plate_x - self.x_min) / (x_range / 3.0)), 2)
        row = min(int((plate_z - self.z_min) / (z_range / 3.0)), 2)

        return (col, row)
