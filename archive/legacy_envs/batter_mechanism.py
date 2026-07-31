"""
batter_mechanism.py — End-to-End 타자 물리 엔진

배트 스윙 역학(관절 토크 → FK), Sweet Spot 충돌 판정,
Exit Velocity / Launch Angle 계산을 수행합니다.

핵심 물리:
    Exit Velocity: v_exit = q × (e × v_ball + (1+e) × v_bat)
    Sweet Spot:    배트 끝에서 ~17cm 지점, COR 보정
    Launch Angle:  배트 경사각 + 공 입사각 기반
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple


# ──────────────────────────────────────────────────────────────
#  배트 물리 모델
# ──────────────────────────────────────────────────────────────

@dataclass
class BatModel:
    """배트의 물리 상수를 관리하는 데이터 클래스.

    MLB 표준 목재 배트 기준값을 사용합니다.
    """

    mass: float = 0.94               # 배트 질량 (kg), ~33oz
    length: float = 0.84             # 배트 길이 (m), ~33인치
    barrel_radius: float = 0.033     # 배럴 반지름 (m), ~2.6인치
    handle_radius: float = 0.012     # 손잡이 반지름 (m)

    # 관성 모멘트 (회전축: 손잡이 끝단)
    moment_of_inertia: float = 0.22  # kg·m²

    # Sweet Spot 위치 (손잡이 끝단 기준)
    sweet_spot_distance: float = 0.67  # 배트 끝에서 ~17cm = 손잡이에서 ~67cm

    # 반발 계수 (Coefficient of Restitution)
    cor_sweet_spot: float = 0.50     # Sweet Spot에서의 COR
    cor_tip: float = 0.35           # 배트 끝단
    cor_handle: float = 0.30        # 손잡이 쪽

    # 타자 위치 (홈플레이트 옆)
    batter_position: np.ndarray = field(
        default_factory=lambda: np.array([0.2, 0.3, 0.0])
        # x=0.2m (홈플레이트 우측), y=0.3m (약간 뒤), z=0.0m
    )


@dataclass
class SwingConfig:
    """스윙 설정 범위를 정의하는 데이터 클래스.

    신경망 액션의 [-1, 1] 범위를 실제 스윙 파라미터로 매핑합니다.
    """

    # 스윙 트리거 임계값 (타이밍)
    # action[0] > 0 이면 스윙 결정
    swing_threshold: float = 0.0

    # Yaw 토크 범위 (수평 회전, N·m)
    yaw_torque_min: float = -80.0
    yaw_torque_max: float = 80.0

    # Pitch 토크 범위 (수직 경사, N·m)
    pitch_torque_min: float = -40.0
    pitch_torque_max: float = 40.0

    # 높이 타겟 범위 (m)
    height_target_min: float = 0.3
    height_target_max: float = 1.3

    # 스윙 시간 범위 (릴리스부터 스윙까지)
    swing_duration: float = 0.15     # 스윙 동작 소요 시간 (초)

    # 배트 각속도 범위
    max_angular_velocity: float = 35.0  # rad/s (~2000 deg/s)


# ──────────────────────────────────────────────────────────────
#  스윙 운동학 (Forward Kinematics)
# ──────────────────────────────────────────────────────────────

class SwingKinematics:
    """배트 스윙의 운동학을 계산합니다.

    Yaw(수평)/Pitch(수직) 2자유도 회전 모델을 사용하여
    배트 끝단의 3D 위치와 속도를 계산합니다.
    """

    def __init__(
        self,
        bat: Optional[BatModel] = None,
        config: Optional[SwingConfig] = None,
    ):
        self.bat = bat or BatModel()
        self.config = config or SwingConfig()

    def compute_bat_state(
        self,
        yaw_angle: float,
        pitch_angle: float,
        yaw_angular_vel: float,
        pitch_angular_vel: float,
        batter_pos: Optional[np.ndarray] = None,
    ) -> dict:
        """현재 관절 각도/각속도로 배트의 3D 상태를 계산합니다.

        2자유도 FK: 어깨(yaw) → 손목(pitch) → 배트 끝단

        Args:
            yaw_angle: 수평 회전 각도 (rad), 0=투수 방향
            pitch_angle: 수직 경사 각도 (rad), 0=수평
            yaw_angular_vel: Yaw 각속도 (rad/s)
            pitch_angular_vel: Pitch 각속도 (rad/s)
            batter_pos: 타자 기준 위치 (None이면 기본값)

        Returns:
            dict:
                'tip_position': 배트 끝단 3D 위치
                'sweet_spot_position': Sweet Spot 3D 위치
                'tip_velocity': 배트 끝단 3D 속도
                'sweet_spot_velocity': Sweet Spot 3D 속도
                'bat_direction': 배트 방향 단위벡터
                'bat_normal': 배트 면 법선벡터
        """
        pos = batter_pos if batter_pos is not None else self.bat.batter_position.copy()
        L = self.bat.length
        L_ss = self.bat.sweet_spot_distance

        # 배트 방향 벡터 (yaw, pitch 회전 적용)
        bat_dir = np.array([
            -np.cos(pitch_angle) * np.sin(yaw_angle),  # x: 좌우
            -np.cos(pitch_angle) * np.cos(yaw_angle),  # y: 전후 (투수 방향)
            np.sin(pitch_angle),                        # z: 상하
        ])

        # 배트 끝단 위치
        tip_pos = pos + L * bat_dir
        sweet_spot_pos = pos + L_ss * bat_dir

        # 배트 끝단 속도 (각속도 × 팔 길이)
        # v = ω × r (벡터 외적)
        omega_vec = np.array([
            pitch_angular_vel * np.cos(yaw_angle),
            -pitch_angular_vel * np.sin(yaw_angle),
            yaw_angular_vel,
        ])

        r_tip = tip_pos - pos
        r_ss = sweet_spot_pos - pos

        tip_vel = np.cross(omega_vec, r_tip)
        sweet_spot_vel = np.cross(omega_vec, r_ss)

        # 배트 면 법선벡터 (배트 방향에 수직, z축 방향 성분)
        bat_normal = np.cross(bat_dir, np.array([0.0, 0.0, 1.0]))
        norm = np.linalg.norm(bat_normal)
        if norm > 1e-10:
            bat_normal = bat_normal / norm
        else:
            bat_normal = np.array([1.0, 0.0, 0.0])

        return {
            'tip_position': tip_pos,
            'sweet_spot_position': sweet_spot_pos,
            'tip_velocity': tip_vel,
            'sweet_spot_velocity': sweet_spot_vel,
            'bat_direction': bat_dir,
            'bat_normal': bat_normal,
        }

    def simulate_swing(
        self,
        yaw_torque: float,
        pitch_torque: float,
        height_target: float,
        dt: float = 0.001,
        duration: Optional[float] = None,
    ) -> dict:
        """토크 입력으로 전체 스윙 동작을 시뮬레이션합니다.

        Args:
            yaw_torque: 수평 토크 (N·m)
            pitch_torque: 수직 토크 (N·m)
            height_target: 목표 높이 (m)
            dt: 시뮬레이션 시간 간격 (초)
            duration: 스윙 지속 시간 (초)

        Returns:
            dict:
                'states': 시간별 배트 상태 리스트
                'times': 시간 배열
                'max_bat_speed': 최대 배트 속도 (m/s)
        """
        if duration is None:
            duration = self.config.swing_duration

        # 초기 상태 (코킹 위치: 투수 반대편에서 시작)
        yaw_angle = np.pi * 0.4      # 약간 뒤로 당긴 상태
        pitch_angle = 0.0             # 수평
        yaw_omega = 0.0
        pitch_omega = 0.0

        # 높이 보정: pitch_angle 초기값을 height_target에 맞게 조정
        bat_center_z = self.bat.batter_position[2] + \
            self.bat.sweet_spot_distance * np.sin(pitch_angle)
        height_error = height_target - bat_center_z
        pitch_angle = np.arcsin(np.clip(
            height_error / (self.bat.sweet_spot_distance + 1e-10), -0.9, 0.9
        ))

        states = []
        times = []
        max_bat_speed = 0.0

        n_steps = int(duration / dt)
        t = 0.0

        for _ in range(n_steps):
            # 각가속도 = 토크 / 관성모멘트
            yaw_alpha = yaw_torque / self.bat.moment_of_inertia
            pitch_alpha = pitch_torque / self.bat.moment_of_inertia

            # 오일러 적분
            yaw_omega += yaw_alpha * dt
            pitch_omega += pitch_alpha * dt

            # 각속도 제한
            max_w = self.config.max_angular_velocity
            yaw_omega = np.clip(yaw_omega, -max_w, max_w)
            pitch_omega = np.clip(pitch_omega, -max_w * 0.5, max_w * 0.5)

            yaw_angle += yaw_omega * dt
            pitch_angle += pitch_omega * dt
            pitch_angle = np.clip(pitch_angle, -np.pi / 4, np.pi / 4)

            state = self.compute_bat_state(
                yaw_angle, pitch_angle, yaw_omega, pitch_omega
            )
            state['yaw_angle'] = yaw_angle
            state['pitch_angle'] = pitch_angle
            state['yaw_omega'] = yaw_omega
            state['pitch_omega'] = pitch_omega
            state['time'] = t

            bat_speed = np.linalg.norm(state['sweet_spot_velocity'])
            max_bat_speed = max(max_bat_speed, bat_speed)

            states.append(state)
            times.append(t)
            t += dt

        return {
            'states': states,
            'times': np.array(times),
            'max_bat_speed': max_bat_speed,
        }


# ──────────────────────────────────────────────────────────────
#  충돌 엔진
# ──────────────────────────────────────────────────────────────

class CollisionEngine:
    """배트-공 충돌 판정 및 타구 물리를 계산합니다.

    충돌 모델:
        v_exit = q × (e × v_ball + (1+e) × v_bat_contact)
        q: Sweet Spot 보정 계수 (0.6 ~ 1.0)
        e: 반발 계수 COR (0.30 ~ 0.50)
    """

    def __init__(self, bat: Optional[BatModel] = None):
        self.bat = bat or BatModel()

    def check_collision(
        self,
        ball_pos: np.ndarray,
        bat_tip: np.ndarray,
        bat_base: np.ndarray,
        collision_radius: float = 0.06,
    ) -> Tuple[bool, float, np.ndarray]:
        """배트-공 충돌 여부를 판정합니다.

        배트를 선분(base → tip)으로 모델링하고, 공 중심과의 최소 거리를 계산합니다.

        Args:
            ball_pos: 공의 3D 위치
            bat_tip: 배트 끝단 3D 위치
            bat_base: 배트 손잡이 끝단 3D 위치 (타자 위치)
            collision_radius: 충돌 판정 반경 (m), 배트 반경 + 공 반경

        Returns:
            (is_hit, contact_distance, contact_point)
            is_hit: 충돌 여부
            contact_distance: 손잡이 기준 접촉 거리 (m)
            contact_point: 충돌 지점 3D 위치
        """
        bat_vec = bat_tip - bat_base
        bat_len = np.linalg.norm(bat_vec)
        if bat_len < 1e-10:
            return False, 0.0, bat_base.copy()

        bat_dir = bat_vec / bat_len

        # 공 중심에서 배트 선분까지의 최소 거리점 계산
        ball_to_base = ball_pos - bat_base
        t = np.dot(ball_to_base, bat_dir) / bat_len
        t = np.clip(t, 0.0, 1.0)  # 선분 범위 내로 제한

        closest_point = bat_base + t * bat_vec
        distance = np.linalg.norm(ball_pos - closest_point)
        contact_distance = t * bat_len

        is_hit = distance < collision_radius

        return is_hit, contact_distance, closest_point

    def sweet_spot_factor(self, contact_distance: float) -> float:
        """접촉 지점의 Sweet Spot 보정 계수를 계산합니다.

        Sweet Spot(~67cm) 지점에서 1.0, 거리가 멀어질수록 감소.
        가우시안 분포 모델 사용.

        Args:
            contact_distance: 손잡이 기준 접촉 거리 (m)

        Returns:
            Sweet Spot 보정 계수 (0.5 ~ 1.0)
        """
        ss = self.bat.sweet_spot_distance
        sigma = 0.08  # 가우시안 폭 (m)

        deviation = abs(contact_distance - ss)
        factor = np.exp(-(deviation ** 2) / (2 * sigma ** 2))

        # 최소 0.5로 제한 (완전 빗맞은 타격에도 일부 에너지 전달)
        return float(max(factor, 0.5))

    def compute_cor(self, contact_distance: float) -> float:
        """접촉 지점의 반발 계수(COR)를 계산합니다.

        Sweet Spot에서 최대, 끝단/손잡이에서 감소.

        Args:
            contact_distance: 손잡이 기준 접촉 거리 (m)

        Returns:
            COR 값
        """
        ss = self.bat.sweet_spot_distance
        q = self.sweet_spot_factor(contact_distance)

        # COR = 기본값 × Sweet Spot 보정
        cor = self.bat.cor_handle + \
            (self.bat.cor_sweet_spot - self.bat.cor_handle) * q

        return float(cor)

    def compute_exit_velocity(
        self,
        ball_velocity: np.ndarray,
        bat_velocity: np.ndarray,
        bat_normal: np.ndarray,
        contact_distance: float,
    ) -> Tuple[np.ndarray, float]:
        """타구의 Exit Velocity 벡터를 계산합니다.

        충돌 모델: v_exit = q × (e × v_ball_n + (1+e) × v_bat_n) + v_ball_t
        (법선 성분만 반발, 접선 성분 보존)

        Args:
            ball_velocity: 공의 속도 벡터 (m/s)
            bat_velocity: 배트 접촉점 속도 벡터 (m/s)
            bat_normal: 배트 면 법선벡터 (정규화)
            contact_distance: 손잡이 기준 접촉 거리 (m)

        Returns:
            (exit_velocity_vector, exit_speed)
        """
        e = self.compute_cor(contact_distance)
        q = self.sweet_spot_factor(contact_distance)

        # 법선 방향 상대 속도
        v_rel = ball_velocity - bat_velocity
        v_n = np.dot(v_rel, bat_normal) * bat_normal
        v_t = v_rel - v_n

        # 반발 후 법선 속도
        v_n_exit = -e * v_n

        # 타구 속도 = 배트 속도 + 반발된 상대 속도
        exit_vel = bat_velocity + v_n_exit + v_t

        # Sweet Spot 보정 적용
        exit_vel = exit_vel * q + exit_vel * (1.0 - q) * 0.7

        exit_speed = float(np.linalg.norm(exit_vel))

        return exit_vel, exit_speed

    def compute_launch_angle(
        self,
        exit_velocity: np.ndarray,
    ) -> float:
        """타구의 Launch Angle을 계산합니다.

        수평면(xy 평면)과 타구 속도 벡터 사이의 각도.
        양수: 뜬 공, 음수: 땅볼

        Args:
            exit_velocity: 타구 속도 벡터 (m/s)

        Returns:
            Launch Angle (degrees)
        """
        horizontal_speed = np.sqrt(exit_velocity[0] ** 2 + exit_velocity[1] ** 2)
        if horizontal_speed < 1e-6:
            return 0.0
        return float(np.degrees(np.arctan2(exit_velocity[2], horizontal_speed)))

    def compute_spray_angle(
        self,
        exit_velocity: np.ndarray,
    ) -> float:
        """타구의 Spray Angle을 계산합니다.

        중앙(투수 방향)을 0°로, 좌측(+), 우측(-)

        Args:
            exit_velocity: 타구 속도 벡터 (m/s)

        Returns:
            Spray Angle (degrees)
        """
        if abs(exit_velocity[1]) < 1e-6:
            return 0.0
        return float(np.degrees(np.arctan2(exit_velocity[0], -exit_velocity[1])))


# ──────────────────────────────────────────────────────────────
#  타자 메커니즘 (E2E Action → 스윙 → 충돌)
# ──────────────────────────────────────────────────────────────

class BatterMechanism:
    """End-to-End 타자 물리 메커니즘.

    신경망의 연속 액션 벡터를 스윙 토크로 변환하고,
    공 궤적과의 충돌을 판정합니다.

    Action Vector:
        [0] t_trigger:    스윙 결정 (> 0이면 스윙)
        [1] yaw_torque:   수평 토크 (normalized)
        [2] pitch_torque:  수직 토크 (normalized)
        [3] z_height:     목표 높이 (normalized)
    """

    def __init__(
        self,
        bat: Optional[BatModel] = None,
        config: Optional[SwingConfig] = None,
    ):
        self.bat = bat or BatModel()
        self.config = config or SwingConfig()
        self.kinematics = SwingKinematics(self.bat, self.config)
        self.collision = CollisionEngine(self.bat)

    def _normalize_to_range(
        self, value: float, low: float, high: float
    ) -> float:
        """[-1, 1] 범위를 [low, high] 범위로 매핑합니다."""
        return low + (value + 1.0) * 0.5 * (high - low)

    def decode_action(self, action: np.ndarray) -> dict:
        """신경망 액션 벡터를 스윙 파라미터로 변환합니다.

        Args:
            action: 4차원 연속 액션 벡터, 각 성분 ∈ [-1, 1]

        Returns:
            dict:
                'should_swing': 스윙 여부
                'yaw_torque': 수평 토크 (N·m)
                'pitch_torque': 수직 토크 (N·m)
                'height_target': 목표 높이 (m)
        """
        cfg = self.config
        action = np.clip(action, -1.0, 1.0)

        return {
            'should_swing': action[0] > cfg.swing_threshold,
            'yaw_torque': self._normalize_to_range(
                action[1], cfg.yaw_torque_min, cfg.yaw_torque_max
            ),
            'pitch_torque': self._normalize_to_range(
                action[2], cfg.pitch_torque_min, cfg.pitch_torque_max
            ),
            'height_target': self._normalize_to_range(
                action[3], cfg.height_target_min, cfg.height_target_max
            ),
        }

    def swing_and_check(
        self,
        action: np.ndarray,
        ball_trajectory_positions: np.ndarray,
        ball_trajectory_velocities: np.ndarray,
        ball_trajectory_times: np.ndarray,
        swing_start_time: float,
    ) -> dict:
        """스윙을 실행하고 공 궤적과의 충돌을 판정합니다.

        Args:
            action: 4차원 연속 액션 벡터
            ball_trajectory_positions: 공 궤적 위치 (N, 3)
            ball_trajectory_velocities: 공 궤적 속도 (N, 3)
            ball_trajectory_times: 공 궤적 시간 (N,)
            swing_start_time: 스윙 시작 시간 (공 릴리스 기준)

        Returns:
            dict:
                'result': 'swing_miss' | 'hit' | 'no_swing'
                'swing_params': 스윙 파라미터 (decode_action 결과)
                'contact_info': 충돌 정보 (hit인 경우)
                    - 'exit_velocity': (3,) m/s
                    - 'exit_speed': float m/s
                    - 'exit_speed_kmh': float km/h
                    - 'launch_angle': float deg
                    - 'spray_angle': float deg
                    - 'contact_distance': float m
                    - 'sweet_spot_factor': float
                    - 'contact_time': float s
                    - 'contact_position': (3,) m
        """
        params = self.decode_action(action)

        if not params['should_swing']:
            return {
                'result': 'no_swing',
                'swing_params': params,
                'contact_info': None,
            }

        # 스윙 시뮬레이션
        swing_result = self.kinematics.simulate_swing(
            yaw_torque=params['yaw_torque'],
            pitch_torque=params['pitch_torque'],
            height_target=params['height_target'],
        )

        # 스윙 동작의 각 시간 프레임에서 공과의 충돌 체크
        swing_states = swing_result['states']
        dt = self.kinematics.config.swing_duration / len(swing_states)

        for i, swing_state in enumerate(swing_states):
            swing_time = swing_start_time + i * dt

            # 공 궤적에서 해당 시간의 공 위치/속도 보간
            if swing_time < ball_trajectory_times[0] or \
               swing_time > ball_trajectory_times[-1]:
                continue

            # 선형 보간으로 공 위치 찾기
            idx = np.searchsorted(ball_trajectory_times, swing_time) - 1
            idx = np.clip(idx, 0, len(ball_trajectory_times) - 2)

            t_frac = (swing_time - ball_trajectory_times[idx]) / \
                     (ball_trajectory_times[idx + 1] - ball_trajectory_times[idx] + 1e-10)

            ball_pos = (1 - t_frac) * ball_trajectory_positions[idx] + \
                       t_frac * ball_trajectory_positions[idx + 1]
            ball_vel = (1 - t_frac) * ball_trajectory_velocities[idx] + \
                       t_frac * ball_trajectory_velocities[idx + 1]

            # 충돌 판정
            bat_tip = swing_state['tip_position']
            bat_base = self.bat.batter_position.copy()

            is_hit, contact_dist, contact_point = self.collision.check_collision(
                ball_pos, bat_tip, bat_base
            )

            if is_hit:
                # 타구 물리 계산
                exit_vel, exit_speed = self.collision.compute_exit_velocity(
                    ball_vel,
                    swing_state['sweet_spot_velocity'],
                    swing_state['bat_normal'],
                    contact_dist,
                )
                launch_angle = self.collision.compute_launch_angle(exit_vel)
                spray_angle = self.collision.compute_spray_angle(exit_vel)
                ss_factor = self.collision.sweet_spot_factor(contact_dist)

                return {
                    'result': 'hit',
                    'swing_params': params,
                    'contact_info': {
                        'exit_velocity': exit_vel,
                        'exit_speed': exit_speed,
                        'exit_speed_kmh': exit_speed * 3.6,
                        'launch_angle': launch_angle,
                        'spray_angle': spray_angle,
                        'contact_distance': contact_dist,
                        'sweet_spot_factor': ss_factor,
                        'contact_time': swing_time,
                        'contact_position': contact_point,
                    },
                }

        # 스윙했으나 헛스윙
        return {
            'result': 'swing_miss',
            'swing_params': params,
            'contact_info': None,
        }

    def classify_hit(self, contact_info: dict) -> str:
        """타구 결과를 분류합니다.

        Exit Velocity와 Launch Angle을 기반으로 타구 유형을 결정합니다.

        Args:
            contact_info: swing_and_check에서 반환된 충돌 정보

        Returns:
            'home_run' | 'extra_base' | 'single' | 'foul' | 'out'
        """
        if contact_info is None:
            return 'out'

        exit_speed = contact_info['exit_speed_kmh']
        launch_angle = contact_info['launch_angle']
        spray_angle = abs(contact_info['spray_angle'])

        # 파울 판정 (spray angle > 45°)
        if spray_angle > 45.0:
            return 'foul'

        # 홈런 (Exit Velocity > 155 km/h & Launch Angle 25~35°)
        if exit_speed > 155.0 and 20.0 <= launch_angle <= 40.0:
            return 'home_run'

        # 장타 (Exit Velocity > 140 km/h & Launch Angle 10~30°)
        if exit_speed > 140.0 and 10.0 <= launch_angle <= 35.0:
            return 'extra_base'

        # 안타 (Exit Velocity > 120 km/h & Launch Angle 5~25°)
        if exit_speed > 120.0 and 5.0 <= launch_angle <= 30.0:
            return 'single'

        # 땅볼 / 플라이아웃
        return 'out'
