"""
pitcher_robot.py — 투수 로봇 물리 정의

설계 철학: "실제 제작 가능한 고정 베이스 산업용 로봇팔"
  - 투수 마운드에 고정 (18.44m 위치)
  - 8 DOF 팔로 투구 동작 수행
  - 릴리즈 메커니즘으로 공을 던짐

DOF 구성 (총 8 DOF):
  어깨 3 DOF : p_shoulder_pitch (-30°~210°), p_shoulder_yaw (-45°~45°), p_shoulder_roll (-120°~120°)
  팔꿈치 2 DOF: p_elbow_flex (0°~150°), p_elbow_pronate (-90°~90°)
  손목 2 DOF : p_wrist_flex (-70°~70°), p_wrist_dev (-30°~30°)
  릴리즈 1 DOF: p_release (추상화 — 볼 속도 직접 제어)

물리 스펙 (현실 기반):
  총 중량   : 약 120 kg (베이스 80kg + 팔 40kg)
  설치 위치 : 투수 마운드 (y=18.44m, z=0.26m 고무판)
  팔 길이   : 0.85 m (상완 0.45m + 전완 0.40m)

투구 물리 계산:
  릴리즈 포인트: 지면에서 약 2.0m 높이
  최대 릴리즈 속도: √(2 × τ × ω × L) ≈ 44 m/s ≈ 160 km/h
  실제 MLB 투구 속도: 110~165 km/h

볼 물리 (규정값):
  질량     : 0.145 kg (141.75g~148.83g)
  직경     : 0.074 m (7.3cm~7.5cm)
  Magnus force 계수: C_L ≈ 0.25 (실험값)
  회전수   : 1,500~3,000 RPM (MLB 평균 약 2,200 RPM)
"""

import math
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class PitcherRobotParams:
    """투수 로봇 물리 파라미터."""

    # ── 설치 위치 (투수 마운드) ──
    base_pos: Tuple[float, float, float] = (0.0, 18.44, 0.26)  # MLB 규정 마운드 위치
    mound_height: float = 0.254  # 마운드 높이 10인치 = 0.254m (MLB 규정)

    # ── 베이스 (고정 마운트) ──
    base_mass: float = 80.0     # kg (무거운 베이스로 반동 억제)
    base_height: float = 0.25   # m

    # ── 어깨 (Shoulder) — 3 DOF ──
    shoulder_height: float = 1.2    # 베이스 기준 어깨 높이 (m)
    shoulder_mass: float = 8.0      # kg (관절 + 상완 합산)

    # pitch: 넓은 범위로 투구 백스윙~팔로우스루 전체 커버
    shoulder_pitch_range: Tuple[float, float] = (-30.0, 210.0)
    shoulder_yaw_range: Tuple[float, float] = (-45.0, 45.0)    # 좌우 타겟팅
    shoulder_roll_range: Tuple[float, float] = (-120.0, 120.0) # 스핀 준비

    shoulder_damping: float = 5.0
    shoulder_max_torque: float = 250.0  # Nm (고출력 투구)
    shoulder_gear: float = 2.5

    upper_arm_length: float = 0.45  # m
    upper_arm_mass: float = 6.0     # kg

    # ── 팔꿈치 (Elbow) — 2 DOF ──
    elbow_flex_range: Tuple[float, float] = (0.0, 150.0)        # 굴곡
    elbow_pronate_range: Tuple[float, float] = (-90.0, 90.0)    # 회내/회외 (스핀 제어)

    elbow_damping: float = 3.0
    elbow_max_torque: float = 150.0  # Nm
    elbow_gear: float = 2.0

    forearm_length: float = 0.40    # m
    forearm_mass: float = 4.0       # kg

    # ── 손목 (Wrist) — 2 DOF ──
    wrist_flex_range: Tuple[float, float] = (-70.0, 70.0)
    wrist_dev_range: Tuple[float, float] = (-30.0, 30.0)

    wrist_damping: float = 1.0
    wrist_max_torque: float = 50.0  # Nm
    wrist_gear: float = 1.0

    # ── 릴리즈 메커니즘 ──
    # 물리 시뮬레이션에서는 볼에 직접 속도를 부여하는 방식으로 추상화
    # (실제 그리퍼 메커니즘의 복잡성 회피)
    release_height: float = 2.0     # 지면에서 릴리즈 포인트 높이 (m)
    release_angle_deg: float = -5.0 # 릴리즈 각도 (하향: 음수)

    # ── 볼 물리 (MLB 규정) ──
    ball_mass: float = 0.145        # kg (5.125 oz = 145.15g)
    ball_radius: float = 0.037      # m (지름 7.4cm)
    ball_magnus_coeff: float = 0.25 # 실험 측정값

    # ── 투구 속도 범위 ──
    pitch_speed_range: Tuple[float, float] = (60.0, 160.0)  # km/h
    # 커리큘럼 단계별 속도
    curriculum_speeds: Dict[int, Tuple[float, float]] = field(default_factory=lambda: {
        1: (25.0, 30.0),   # Stage 1: 느림 (학습 초기)
        2: (30.0, 38.0),   # Stage 2: 중간
        3: (35.0, 43.0),   # Stage 3: 빠름
        4: (40.0, 50.0),   # Stage 4: 변화구 추가
        5: (45.0, 60.0),   # Stage 5: Self-Play 목표
    })

    # 구종별 스핀 파라미터 (RPM)
    pitch_types: Dict[str, Dict] = field(default_factory=lambda: {
        "fastball": {
            "spin_rpm": 2200,
            "spin_axis": (0, 1, 0),  # 역회전 (라이징)
            "speed_factor": 1.0,
            "description": "직구: 역회전, 빠름",
        },
        "curveball": {
            "spin_rpm": 2500,
            "spin_axis": (1, 0, 0),  # 탑스핀 (낙하)
            "speed_factor": 0.75,
            "description": "커브: 탑스핀, 아래로 휨",
        },
        "slider": {
            "spin_rpm": 2400,
            "spin_axis": (0.7, 0, 0.7),  # 사이드스핀
            "speed_factor": 0.85,
            "description": "슬라이더: 가로로 휨",
        },
        "changeup": {
            "spin_rpm": 1800,
            "spin_axis": (0, 1, 0),
            "speed_factor": 0.65,
            "description": "체인지업: 직구와 같은 팔 동작, 느림",
        },
    })

    # ── 파생 물리량 (계산값) ──
    @property
    def total_arm_length(self) -> float:
        """어깨→손목까지 팔 총 길이 (m)."""
        return self.upper_arm_length + self.forearm_length

    @property
    def max_release_speed_ms(self) -> float:
        """물리적 최대 릴리즈 속도 추정 (m/s).

        에너지 기반 근사:
          토크×각변위 = 0.5 × I × ω²
          I = (1/3) × m × L² (어깨 기준)
          gear ratio 적용 토크 = 토크 × gear
        """
        eff_torque = self.shoulder_max_torque * self.shoulder_gear  # 기어 적용
        I = (self.upper_arm_mass + self.forearm_mass) * self.total_arm_length ** 2 / 3
        theta = math.pi  # 180도 스윗 (백스윗 → 릴리즈)
        omega_sq = 2 * eff_torque * theta / (I + 1e-6)
        omega = math.sqrt(max(0, omega_sq))
        return omega * self.total_arm_length

    @property
    def max_release_speed_kmh(self) -> float:
        return self.max_release_speed_ms * 3.6

    @property
    def magnus_force_max_n(self) -> float:
        """최대 마그누스 힘 추정 (N).

        F_magnus = C_L * ρ * π * r² * v * (ω × v̂)
        단순화: F ≈ C_L * 0.5 * ρ * A * v²
        """
        rho = 1.225   # 공기 밀도 (kg/m³)
        A = math.pi * self.ball_radius ** 2
        v_max = self.pitch_speed_range[1] / 3.6  # m/s
        return self.ball_magnus_coeff * 0.5 * rho * A * v_max ** 2

    def validate(self) -> Dict[str, str]:
        """물리 파라미터 유효성 검사."""
        issues = {}

        # 볼 규격 검사 (MLB 기준)
        if not (0.141 <= self.ball_mass <= 0.149):
            issues["ball_mass"] = f"{self.ball_mass}kg — MLB 규정 0.141~0.149kg 범위 이탈"
        if not (0.0365 <= self.ball_radius <= 0.0375):
            issues["ball_radius"] = f"{self.ball_radius}m — MLB 규정 7.3~7.5cm 범위 이탈"

        # 최대 투구 속도 현실성 검사
        v = self.max_release_speed_kmh
        if v < 80:
            issues["speed_low"] = f"추정 최대 속도 {v:.0f}km/h — 너무 낮음 (목표 ≥120km/h)"
        elif v > 300:
            issues["speed_high"] = f"추정 최대 속도 {v:.0f}km/h — 비현실적으로 높음"

        # 릴리즈 높이 (일반적으로 1.5~2.5m)
        if not (1.2 <= self.release_height <= 2.8):
            issues["release_height"] = f"{self.release_height}m — 비현실적 릴리즈 높이"

        return issues

    def get_pitch_velocity(self, speed_kmh: float, pitch_type: str = "fastball") -> Tuple[float, float, float]:
        """투구 속도 벡터 계산 (MuJoCo freejoint 초기 속도).

        Args:
            speed_kmh: 투구 속도 (km/h)
            pitch_type: 구종

        Returns:
            (vy, vz, vx) 속도 벡터 (m/s) — MuJoCo 좌표계
        """
        speed_ms = speed_kmh / 3.6
        angle_rad = math.radians(self.release_angle_deg)

        # y축: 홈플레이트 방향 (음수)
        vy = -speed_ms * math.cos(angle_rad)
        # z축: 수직 (릴리즈 각도만큼 하향)
        vz = speed_ms * math.sin(angle_rad)
        vx = 0.0  # 직구 기준 (변화구는 별도 처리)

        return (vx, vy, vz)

    def print_summary(self):
        """물리 스펙 요약 출력."""
        issues = self.validate()
        print("=" * 55)
        print(" ⚾ Pitcher Robot — 물리 스펙 요약")
        print("=" * 55)
        print(f"  자유도        : 8 DOF (어깨3 + 팔꿈치2 + 손목2 + 릴리즈1)")
        print(f"  설치 위치     : y={self.base_pos[1]}m (투수 마운드)")
        print(f"  마운드 높이   : {self.mound_height*100:.0f}cm (MLB 규정 10인치)")
        print(f"  어깨 최대토크 : {self.shoulder_max_torque} Nm")
        print(f"  팔 길이       : {self.total_arm_length:.2f} m")
        print(f"  릴리즈 높이   : {self.release_height:.1f} m")
        print(f"  최대 투구 속도: {self.max_release_speed_kmh:.0f} km/h (추정)")
        print(f"  볼 질량       : {self.ball_mass*1000:.0f} g")
        print(f"  볼 직경       : {self.ball_radius*200:.1f} cm")
        print(f"  최대 마그누스 힘: {self.magnus_force_max_n:.2f} N")
        print(f"\n  구종 목록:")
        for name, params in self.pitch_types.items():
            print(f"    [{name:10s}] {params['description']}")
        if issues:
            print(f"\n  ⚠️  검증 이슈:")
            for k, v in issues.items():
                print(f"    - {k}: {v}")
        else:
            print(f"\n  ✅ 물리 파라미터 검증 통과")
        print("=" * 55)


# 기본 파라미터 인스턴스
DEFAULT_PITCHER = PitcherRobotParams()


if __name__ == "__main__":
    robot = PitcherRobotParams()
    robot.print_summary()
    print(f"\n  직구 100km/h 속도 벡터: {robot.get_pitch_velocity(100, 'fastball')}")
    print(f"  커브 80km/h 속도 벡터:  {robot.get_pitch_velocity(80, 'curveball')}")
