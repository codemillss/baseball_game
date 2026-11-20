# baseball/archive/robots/batter_robot.py

원본: [archive/robots/batter_robot.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/robots/batter_robot.py)

SHA256: `b863844a8d038e3e8b8def13648a99bd406a1ef125aeebf89506296c92a29a74`

전체 204행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BatterRobotParams` | ClassDef | 33 | 195 |
| `total_arm_length` | FunctionDef | 111 | 113 |
| `max_bat_tip_speed_ms` | FunctionDef | 116 | 139 |
| `max_bat_tip_speed_kmh` | FunctionDef | 142 | 143 |
| `validate` | FunctionDef | 145 | 172 |
| `print_summary` | FunctionDef | 174 | 195 |

## 전체 원문

````text
    1 | """
    2 | batter_robot.py — 타자 로봇 물리 정의
    3 | 
    4 | 설계 철학: "실제 제작 가능한 고정 베이스 로봇팔"
    5 |   - 다리 없음 (타자 박스에 고정 마운트)
    6 |   - 상체(토르소 + 팔 + 목)만으로 스윙 동작 수행
    7 |   - 물리 파라미터는 실제 산업용 로봇팔 수준 기반
    8 | 
    9 | DOF 구성 (총 9 DOF):
   10 |   목   2 DOF : head_yaw (-90°~90°), head_pitch (-45°~45°)
   11 |   어깨 3 DOF : shoulder_yaw, shoulder_pitch, shoulder_roll
   12 |   팔꿈치 1 DOF: elbow_flex (0°~150°)
   13 |   손목 3 DOF : wrist_yaw, wrist_pitch, wrist_roll
   14 | 
   15 | 물리 스펙 (현실 기반):
   16 |   총 중량   : 약 30 kg (팔 + 토르소)
   17 |   배트 길이 : 0.84 m (MLB 규정)
   18 |   배트 질량 : 0.94 kg (MLB 규정 목재 배트)
   19 |   최대 배트팁 속도: ~110 km/h (어깨 토크 200Nm 기준)
   20 | 
   21 | 실제 야구 타격 참고값:
   22 |   MLB 평균 배트 스피드 : 105~115 km/h
   23 |   MLB 평균 exit velocity: 140~160 km/h (볼+배트 충돌 보존)
   24 |   스윗 스팟 범위       : 배트 끝에서 15~20cm 이내
   25 | """
   26 | 
   27 | from dataclasses import dataclass, field
   28 | from typing import Dict, Tuple
   29 | import math
   30 | 
   31 | 
   32 | @dataclass
   33 | class BatterRobotParams:
   34 |     """타자 로봇 물리 파라미터.
   35 | 
   36 |     모든 단위:
   37 |       길이 : 미터 (m)
   38 |       질량 : 킬로그램 (kg)
   39 |       토크 : 뉴턴·미터 (Nm)
   40 |       각도 : 도 (degree), MuJoCo XML 입력값
   41 |     """
   42 | 
   43 |     # ── 설치 위치 (MLB 우타자 기준) ──
   44 |     base_pos: Tuple[float, float, float] = (0.6, -0.1, 0.0)
   45 |     stance: str = "right"  # "right" or "left"
   46 | 
   47 |     # ── 토르소 ──
   48 |     torso_mass: float = 20.0        # kg
   49 |     torso_height: float = 1.1       # 지면에서 토르소 중심까지 (m)
   50 | 
   51 |     # ── 목 (Head) — 2 DOF ──
   52 |     neck_height: float = 1.6        # 토르소 기준 높이 (m)
   53 |     head_mass: float = 1.0          # kg
   54 |     head_yaw_range: Tuple[float, float] = (-90.0, 90.0)    # 좌우 회전
   55 |     head_pitch_range: Tuple[float, float] = (-45.0, 45.0)  # 상하 회전
   56 |     head_damping: float = 0.5
   57 |     head_max_torque: float = 50.0   # Nm
   58 | 
   59 |     # ── 어깨 (Shoulder) — 3 DOF ──
   60 |     shoulder_height: float = 1.3    # 토르소 기준 어깨 위치 (m)
   61 |     shoulder_mass: float = 3.0      # kg (어깨 관절 + 상완 합산)
   62 |     shoulder_yaw_range: Tuple[float, float] = (-90.0, 90.0)
   63 |     shoulder_pitch_range: Tuple[float, float] = (-90.0, 90.0)
   64 |     shoulder_roll_range: Tuple[float, float] = (-90.0, 90.0)
   65 |     shoulder_damping: float = 2.0
   66 |     shoulder_max_torque: float = 200.0  # Nm (↑ 이전 100→200, 실제 스윙 요구치)
   67 |     shoulder_gear: float = 2.0
   68 | 
   69 |     upper_arm_length: float = 0.4   # 상완 길이 (m)
   70 |     upper_arm_mass: float = 3.0     # kg
   71 | 
   72 |     # ── 팔꿈치 (Elbow) — 1 DOF ──
   73 |     elbow_flex_range: Tuple[float, float] = (0.0, 150.0)  # 수정: 이전 -150~0 → 0~150
   74 |     elbow_damping: float = 1.5
   75 |     elbow_max_torque: float = 150.0  # Nm
   76 |     elbow_gear: float = 2.0
   77 | 
   78 |     forearm_length: float = 0.4     # 전완 길이 (m)
   79 |     forearm_mass: float = 2.0       # kg
   80 | 
   81 |     # ── 손목 (Wrist) — 3 DOF ──
   82 |     wrist_yaw_range: Tuple[float, float] = (-90.0, 90.0)
   83 |     wrist_pitch_range: Tuple[float, float] = (-90.0, 90.0)
   84 |     wrist_roll_range: Tuple[float, float] = (-90.0, 90.0)
   85 |     wrist_damping: float = 0.5
   86 |     wrist_max_torque: float = 50.0   # Nm
   87 |     wrist_gear: float = 1.0
   88 | 
   89 |     # ── 배트 (Bat) ──
   90 |     # MLB 규정: 길이 최대 106.7cm, 직경 최대 7cm (배럴), 질량 제한 없음 (보통 850~950g)
   91 |     bat_knob_radius: float = 0.025   # m
   92 |     bat_handle_radius: float = 0.014 # m
   93 |     bat_handle_length: float = 0.25  # m  (핸들 구간)
   94 |     bat_taper_length: float = 0.09   # m  (테이퍼 전환 구간) ← 수정
   95 |     bat_barrel_radius: float = 0.034 # m (직경 6.8cm, 규정 이내)
   96 |     bat_barrel_length: float = 0.50  # m
   97 |     bat_total_length: float = 0.84   # m (= 0.25 + 0.09 + 0.50 = 0.84 ✅)
   98 | 
   99 |     bat_mass_total: float = 0.94     # kg
  100 |     bat_knob_mass: float = 0.05
  101 |     bat_handle_mass: float = 0.20    # ← 수정
  102 |     bat_taper_mass: float = 0.19     # ← 수정 (0.05+0.20+0.19+0.50=0.94)
  103 |     bat_barrel_mass: float = 0.50
  104 | 
  105 |     # 배트 스윗 스팟: 배트 끝에서 15~20cm 이내
  106 |     sweet_spot_from_tip: float = 0.175  # m
  107 |     sweet_spot_radius: float = 0.04     # m (허용 오차)
  108 | 
  109 |     # ── 파생 물리량 (계산값) ──
  110 |     @property
  111 |     def total_arm_length(self) -> float:
  112 |         """어깨→배트 끝까지 총 길이 (m)."""
  113 |         return self.upper_arm_length + self.forearm_length + self.bat_total_length
  114 | 
  115 |     @property
  116 |     def max_bat_tip_speed_ms(self) -> float:
  117 |         """물리적 최대 배트팁 속도 추정 (m/s).
  118 | 
  119 |         토크 × 각변위 = 관성 에너지 기반 근사:
  120 |           τ × θ ≈ 0.5 × I × ω²
  121 |           I = (1/3) × m_arm × L_arm² + m_bat × (L_arm + L_bat/2)²
  122 |           ω_max = sqrt(2 × τ × θ / I)
  123 |           v_tip = ω_max × (L_arm + L_bat)
  124 |         """
  125 |         L_arm = self.upper_arm_length + self.forearm_length  # 0.8m
  126 |         L_bat = self.bat_total_length
  127 |         m_arm = self.upper_arm_mass + self.elbow_damping * 0  # ≈ 5kg
  128 |         m_bat = self.bat_mass_total
  129 | 
  130 |         # 팔 관성 모멘트 (어깨 기준)
  131 |         I_arm = (1/3) * (self.upper_arm_mass + 2.0) * L_arm ** 2
  132 |         # 배트 관성 모멘트 (어깨 기준, 배트 중심까지)
  133 |         I_bat = m_bat * (L_arm + L_bat / 2) ** 2
  134 |         I_total = I_arm + I_bat
  135 | 
  136 |         # 스윙 각도 ≈ 90도(π/2 rad), 순수 어깨 토크만 사용
  137 |         theta = 3.14159 / 2
  138 |         omega = math.sqrt(max(0, 2 * self.shoulder_max_torque * theta / I_total))
  139 |         return omega * (L_arm + L_bat)
  140 | 
  141 |     @property
  142 |     def max_bat_tip_speed_kmh(self) -> float:
  143 |         return self.max_bat_tip_speed_ms * 3.6
  144 | 
  145 |     def validate(self) -> Dict[str, str]:
  146 |         """물리 파라미터 유효성 검사."""
  147 |         issues = {}
  148 | 
  149 |         # 배트 길이 합산 검사
  150 |         computed = self.bat_handle_length + self.bat_taper_length + self.bat_barrel_length
  151 |         if abs(computed - self.bat_total_length) > 0.01:
  152 |             issues["bat_length"] = f"합산 {computed:.3f}m ≠ 선언값 {self.bat_total_length}m"
  153 | 
  154 |         # 배트 질량 합산 검사
  155 |         m_sum = self.bat_knob_mass + self.bat_handle_mass + self.bat_taper_mass + self.bat_barrel_mass
  156 |         if abs(m_sum - self.bat_mass_total) > 0.01:
  157 |             issues["bat_mass"] = f"합산 {m_sum:.3f}kg ≠ 선언값 {self.bat_mass_total}kg"
  158 | 
  159 |         # 배트 배럴 직경 MLB 규정 (최대 7cm = 0.07m 반지름 0.035m)
  160 |         if self.bat_barrel_radius > 0.035:
  161 |             issues["bat_barrel"] = f"배럴 반지름 {self.bat_barrel_radius}m > MLB 규정 0.035m"
  162 | 
  163 |         # 배트 전체 길이 MLB 규정 (최대 106.7cm)
  164 |         if self.bat_total_length > 1.067:
  165 |             issues["bat_total_length"] = f"배트 길이 {self.bat_total_length}m > MLB 규정 1.067m"
  166 | 
  167 |         # 배트팁 속도가 실제 MLB 범위인지 (80~150 km/h)
  168 |         v = self.max_bat_tip_speed_kmh
  169 |         if not (50 < v < 200):
  170 |             issues["bat_speed"] = f"추정 팁 속도 {v:.0f}km/h — 비현실적 범위"
  171 | 
  172 |         return issues
  173 | 
  174 |     def print_summary(self):
  175 |         """물리 스펙 요약 출력."""
  176 |         issues = self.validate()
  177 |         print("=" * 55)
  178 |         print(" ⚾ Batter Robot — 물리 스펙 요약")
  179 |         print("=" * 55)
  180 |         print(f"  자유도        : 9 DOF (목2 + 어깨3 + 팔꿈치1 + 손목3)")
  181 |         print(f"  설치 위치     : {self.base_pos}")
  182 |         print(f"  어깨 최대토크 : {self.shoulder_max_torque} Nm")
  183 |         print(f"  팔꿈치 최대토크: {self.elbow_max_torque} Nm")
  184 |         print(f"  총 팔 길이    : {self.total_arm_length:.2f} m")
  185 |         print(f"  배트 길이     : {self.bat_total_length:.2f} m")
  186 |         print(f"  배트 질량     : {self.bat_mass_total:.2f} kg")
  187 |         print(f"  스윗스팟 위치 : 끝에서 {self.sweet_spot_from_tip*100:.1f}cm")
  188 |         print(f"  최대 팁 속도  : {self.max_bat_tip_speed_kmh:.0f} km/h (추정)")
  189 |         if issues:
  190 |             print(f"\n  ⚠️  검증 이슈:")
  191 |             for k, v in issues.items():
  192 |                 print(f"    - {k}: {v}")
  193 |         else:
  194 |             print(f"\n  ✅ 물리 파라미터 검증 통과")
  195 |         print("=" * 55)
  196 | 
  197 | 
  198 | # 기본 파라미터 인스턴스
  199 | DEFAULT_BATTER = BatterRobotParams()
  200 | 
  201 | 
  202 | if __name__ == "__main__":
  203 |     robot = BatterRobotParams()
  204 |     robot.print_summary()
````
