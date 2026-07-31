"""
batter_robot.py — 타자 로봇 물리 정의

설계 철학: "실제 제작 가능한 고정 베이스 로봇팔"
  - 다리 없음 (타자 박스에 고정 마운트)
  - 상체(토르소 + 팔 + 목)만으로 스윙 동작 수행
  - 물리 파라미터는 실제 산업용 로봇팔 수준 기반

DOF 구성 (총 9 DOF):
  목   2 DOF : head_yaw (-90°~90°), head_pitch (-45°~45°)
  어깨 3 DOF : shoulder_yaw, shoulder_pitch, shoulder_roll
  팔꿈치 1 DOF: elbow_flex (0°~150°)
  손목 3 DOF : wrist_yaw, wrist_pitch, wrist_roll

물리 스펙 (현실 기반):
  총 중량   : 약 30 kg (팔 + 토르소)
  배트 길이 : 0.84 m (MLB 규정)
  배트 질량 : 0.94 kg (MLB 규정 목재 배트)
  최대 배트팁 속도: ~110 km/h (어깨 토크 200Nm 기준)

실제 야구 타격 참고값:
  MLB 평균 배트 스피드 : 105~115 km/h
  MLB 평균 exit velocity: 140~160 km/h (볼+배트 충돌 보존)
  스윗 스팟 범위       : 배트 끝에서 15~20cm 이내
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple
import math


@dataclass
class BatterRobotParams:
    """타자 로봇 물리 파라미터.

    모든 단위:
      길이 : 미터 (m)
      질량 : 킬로그램 (kg)
      토크 : 뉴턴·미터 (Nm)
      각도 : 도 (degree), MuJoCo XML 입력값
    """

    # ── 설치 위치 (MLB 우타자 기준) ──
    base_pos: Tuple[float, float, float] = (0.6, -0.1, 0.0)
    stance: str = "right"  # "right" or "left"

    # ── 토르소 ──
    torso_mass: float = 20.0        # kg
    torso_height: float = 1.1       # 지면에서 토르소 중심까지 (m)

    # ── 목 (Head) — 2 DOF ──
    neck_height: float = 1.6        # 토르소 기준 높이 (m)
    head_mass: float = 1.0          # kg
    head_yaw_range: Tuple[float, float] = (-90.0, 90.0)    # 좌우 회전
    head_pitch_range: Tuple[float, float] = (-45.0, 45.0)  # 상하 회전
    head_damping: float = 0.5
    head_max_torque: float = 50.0   # Nm

    # ── 어깨 (Shoulder) — 3 DOF ──
    shoulder_height: float = 1.3    # 토르소 기준 어깨 위치 (m)
    shoulder_mass: float = 3.0      # kg (어깨 관절 + 상완 합산)
    shoulder_yaw_range: Tuple[float, float] = (-90.0, 90.0)
    shoulder_pitch_range: Tuple[float, float] = (-90.0, 90.0)
    shoulder_roll_range: Tuple[float, float] = (-90.0, 90.0)
    shoulder_damping: float = 2.0
    shoulder_max_torque: float = 200.0  # Nm (↑ 이전 100→200, 실제 스윙 요구치)
    shoulder_gear: float = 2.0

    upper_arm_length: float = 0.4   # 상완 길이 (m)
    upper_arm_mass: float = 3.0     # kg

    # ── 팔꿈치 (Elbow) — 1 DOF ──
    elbow_flex_range: Tuple[float, float] = (0.0, 150.0)  # 수정: 이전 -150~0 → 0~150
    elbow_damping: float = 1.5
    elbow_max_torque: float = 150.0  # Nm
    elbow_gear: float = 2.0

    forearm_length: float = 0.4     # 전완 길이 (m)
    forearm_mass: float = 2.0       # kg

    # ── 손목 (Wrist) — 3 DOF ──
    wrist_yaw_range: Tuple[float, float] = (-90.0, 90.0)
    wrist_pitch_range: Tuple[float, float] = (-90.0, 90.0)
    wrist_roll_range: Tuple[float, float] = (-90.0, 90.0)
    wrist_damping: float = 0.5
    wrist_max_torque: float = 50.0   # Nm
    wrist_gear: float = 1.0

    # ── 배트 (Bat) ──
    # MLB 규정: 길이 최대 106.7cm, 직경 최대 7cm (배럴), 질량 제한 없음 (보통 850~950g)
    bat_knob_radius: float = 0.025   # m
    bat_handle_radius: float = 0.014 # m
    bat_handle_length: float = 0.25  # m  (핸들 구간)
    bat_taper_length: float = 0.09   # m  (테이퍼 전환 구간) ← 수정
    bat_barrel_radius: float = 0.034 # m (직경 6.8cm, 규정 이내)
    bat_barrel_length: float = 0.50  # m
    bat_total_length: float = 0.84   # m (= 0.25 + 0.09 + 0.50 = 0.84 ✅)

    bat_mass_total: float = 0.94     # kg
    bat_knob_mass: float = 0.05
    bat_handle_mass: float = 0.20    # ← 수정
    bat_taper_mass: float = 0.19     # ← 수정 (0.05+0.20+0.19+0.50=0.94)
    bat_barrel_mass: float = 0.50

    # 배트 스윗 스팟: 배트 끝에서 15~20cm 이내
    sweet_spot_from_tip: float = 0.175  # m
    sweet_spot_radius: float = 0.04     # m (허용 오차)

    # ── 파생 물리량 (계산값) ──
    @property
    def total_arm_length(self) -> float:
        """어깨→배트 끝까지 총 길이 (m)."""
        return self.upper_arm_length + self.forearm_length + self.bat_total_length

    @property
    def max_bat_tip_speed_ms(self) -> float:
        """물리적 최대 배트팁 속도 추정 (m/s).

        토크 × 각변위 = 관성 에너지 기반 근사:
          τ × θ ≈ 0.5 × I × ω²
          I = (1/3) × m_arm × L_arm² + m_bat × (L_arm + L_bat/2)²
          ω_max = sqrt(2 × τ × θ / I)
          v_tip = ω_max × (L_arm + L_bat)
        """
        L_arm = self.upper_arm_length + self.forearm_length  # 0.8m
        L_bat = self.bat_total_length
        m_arm = self.upper_arm_mass + self.elbow_damping * 0  # ≈ 5kg
        m_bat = self.bat_mass_total

        # 팔 관성 모멘트 (어깨 기준)
        I_arm = (1/3) * (self.upper_arm_mass + 2.0) * L_arm ** 2
        # 배트 관성 모멘트 (어깨 기준, 배트 중심까지)
        I_bat = m_bat * (L_arm + L_bat / 2) ** 2
        I_total = I_arm + I_bat

        # 스윙 각도 ≈ 90도(π/2 rad), 순수 어깨 토크만 사용
        theta = 3.14159 / 2
        omega = math.sqrt(max(0, 2 * self.shoulder_max_torque * theta / I_total))
        return omega * (L_arm + L_bat)

    @property
    def max_bat_tip_speed_kmh(self) -> float:
        return self.max_bat_tip_speed_ms * 3.6

    def validate(self) -> Dict[str, str]:
        """물리 파라미터 유효성 검사."""
        issues = {}

        # 배트 길이 합산 검사
        computed = self.bat_handle_length + self.bat_taper_length + self.bat_barrel_length
        if abs(computed - self.bat_total_length) > 0.01:
            issues["bat_length"] = f"합산 {computed:.3f}m ≠ 선언값 {self.bat_total_length}m"

        # 배트 질량 합산 검사
        m_sum = self.bat_knob_mass + self.bat_handle_mass + self.bat_taper_mass + self.bat_barrel_mass
        if abs(m_sum - self.bat_mass_total) > 0.01:
            issues["bat_mass"] = f"합산 {m_sum:.3f}kg ≠ 선언값 {self.bat_mass_total}kg"

        # 배트 배럴 직경 MLB 규정 (최대 7cm = 0.07m 반지름 0.035m)
        if self.bat_barrel_radius > 0.035:
            issues["bat_barrel"] = f"배럴 반지름 {self.bat_barrel_radius}m > MLB 규정 0.035m"

        # 배트 전체 길이 MLB 규정 (최대 106.7cm)
        if self.bat_total_length > 1.067:
            issues["bat_total_length"] = f"배트 길이 {self.bat_total_length}m > MLB 규정 1.067m"

        # 배트팁 속도가 실제 MLB 범위인지 (80~150 km/h)
        v = self.max_bat_tip_speed_kmh
        if not (50 < v < 200):
            issues["bat_speed"] = f"추정 팁 속도 {v:.0f}km/h — 비현실적 범위"

        return issues

    def print_summary(self):
        """물리 스펙 요약 출력."""
        issues = self.validate()
        print("=" * 55)
        print(" ⚾ Batter Robot — 물리 스펙 요약")
        print("=" * 55)
        print(f"  자유도        : 9 DOF (목2 + 어깨3 + 팔꿈치1 + 손목3)")
        print(f"  설치 위치     : {self.base_pos}")
        print(f"  어깨 최대토크 : {self.shoulder_max_torque} Nm")
        print(f"  팔꿈치 최대토크: {self.elbow_max_torque} Nm")
        print(f"  총 팔 길이    : {self.total_arm_length:.2f} m")
        print(f"  배트 길이     : {self.bat_total_length:.2f} m")
        print(f"  배트 질량     : {self.bat_mass_total:.2f} kg")
        print(f"  스윗스팟 위치 : 끝에서 {self.sweet_spot_from_tip*100:.1f}cm")
        print(f"  최대 팁 속도  : {self.max_bat_tip_speed_kmh:.0f} km/h (추정)")
        if issues:
            print(f"\n  ⚠️  검증 이슈:")
            for k, v in issues.items():
                print(f"    - {k}: {v}")
        else:
            print(f"\n  ✅ 물리 파라미터 검증 통과")
        print("=" * 55)


# 기본 파라미터 인스턴스
DEFAULT_BATTER = BatterRobotParams()


if __name__ == "__main__":
    robot = BatterRobotParams()
    robot.print_summary()
