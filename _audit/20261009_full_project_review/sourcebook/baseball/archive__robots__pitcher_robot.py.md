# baseball/archive/robots/pitcher_robot.py

원본: [archive/robots/pitcher_robot.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/robots/pitcher_robot.py)

SHA256: `f9dd34e53402e4ca07fe3a0169113a9eb21db49314dca8f705420b12fd783437`

전체 252행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `PitcherRobotParams` | ClassDef | 38 | 241 |
| `total_arm_length` | FunctionDef | 136 | 138 |
| `max_release_speed_ms` | FunctionDef | 141 | 154 |
| `max_release_speed_kmh` | FunctionDef | 157 | 158 |
| `magnus_force_max_n` | FunctionDef | 161 | 170 |
| `validate` | FunctionDef | 172 | 193 |
| `get_pitch_velocity` | FunctionDef | 195 | 214 |
| `print_summary` | FunctionDef | 216 | 241 |

## 전체 원문

````text
    1 | """
    2 | pitcher_robot.py — 투수 로봇 물리 정의
    3 | 
    4 | 설계 철학: "실제 제작 가능한 고정 베이스 산업용 로봇팔"
    5 |   - 투수 마운드에 고정 (18.44m 위치)
    6 |   - 8 DOF 팔로 투구 동작 수행
    7 |   - 릴리즈 메커니즘으로 공을 던짐
    8 | 
    9 | DOF 구성 (총 8 DOF):
   10 |   어깨 3 DOF : p_shoulder_pitch (-30°~210°), p_shoulder_yaw (-45°~45°), p_shoulder_roll (-120°~120°)
   11 |   팔꿈치 2 DOF: p_elbow_flex (0°~150°), p_elbow_pronate (-90°~90°)
   12 |   손목 2 DOF : p_wrist_flex (-70°~70°), p_wrist_dev (-30°~30°)
   13 |   릴리즈 1 DOF: p_release (추상화 — 볼 속도 직접 제어)
   14 | 
   15 | 물리 스펙 (현실 기반):
   16 |   총 중량   : 약 120 kg (베이스 80kg + 팔 40kg)
   17 |   설치 위치 : 투수 마운드 (y=18.44m, z=0.26m 고무판)
   18 |   팔 길이   : 0.85 m (상완 0.45m + 전완 0.40m)
   19 | 
   20 | 투구 물리 계산:
   21 |   릴리즈 포인트: 지면에서 약 2.0m 높이
   22 |   최대 릴리즈 속도: √(2 × τ × ω × L) ≈ 44 m/s ≈ 160 km/h
   23 |   실제 MLB 투구 속도: 110~165 km/h
   24 | 
   25 | 볼 물리 (규정값):
   26 |   질량     : 0.145 kg (141.75g~148.83g)
   27 |   직경     : 0.074 m (7.3cm~7.5cm)
   28 |   Magnus force 계수: C_L ≈ 0.25 (실험값)
   29 |   회전수   : 1,500~3,000 RPM (MLB 평균 약 2,200 RPM)
   30 | """
   31 | 
   32 | import math
   33 | from dataclasses import dataclass, field
   34 | from typing import Dict, Tuple
   35 | 
   36 | 
   37 | @dataclass
   38 | class PitcherRobotParams:
   39 |     """투수 로봇 물리 파라미터."""
   40 | 
   41 |     # ── 설치 위치 (투수 마운드) ──
   42 |     base_pos: Tuple[float, float, float] = (0.0, 18.44, 0.26)  # MLB 규정 마운드 위치
   43 |     mound_height: float = 0.254  # 마운드 높이 10인치 = 0.254m (MLB 규정)
   44 | 
   45 |     # ── 베이스 (고정 마운트) ──
   46 |     base_mass: float = 80.0     # kg (무거운 베이스로 반동 억제)
   47 |     base_height: float = 0.25   # m
   48 | 
   49 |     # ── 어깨 (Shoulder) — 3 DOF ──
   50 |     shoulder_height: float = 1.2    # 베이스 기준 어깨 높이 (m)
   51 |     shoulder_mass: float = 8.0      # kg (관절 + 상완 합산)
   52 | 
   53 |     # pitch: 넓은 범위로 투구 백스윙~팔로우스루 전체 커버
   54 |     shoulder_pitch_range: Tuple[float, float] = (-30.0, 210.0)
   55 |     shoulder_yaw_range: Tuple[float, float] = (-45.0, 45.0)    # 좌우 타겟팅
   56 |     shoulder_roll_range: Tuple[float, float] = (-120.0, 120.0) # 스핀 준비
   57 | 
   58 |     shoulder_damping: float = 5.0
   59 |     shoulder_max_torque: float = 250.0  # Nm (고출력 투구)
   60 |     shoulder_gear: float = 2.5
   61 | 
   62 |     upper_arm_length: float = 0.45  # m
   63 |     upper_arm_mass: float = 6.0     # kg
   64 | 
   65 |     # ── 팔꿈치 (Elbow) — 2 DOF ──
   66 |     elbow_flex_range: Tuple[float, float] = (0.0, 150.0)        # 굴곡
   67 |     elbow_pronate_range: Tuple[float, float] = (-90.0, 90.0)    # 회내/회외 (스핀 제어)
   68 | 
   69 |     elbow_damping: float = 3.0
   70 |     elbow_max_torque: float = 150.0  # Nm
   71 |     elbow_gear: float = 2.0
   72 | 
   73 |     forearm_length: float = 0.40    # m
   74 |     forearm_mass: float = 4.0       # kg
   75 | 
   76 |     # ── 손목 (Wrist) — 2 DOF ──
   77 |     wrist_flex_range: Tuple[float, float] = (-70.0, 70.0)
   78 |     wrist_dev_range: Tuple[float, float] = (-30.0, 30.0)
   79 | 
   80 |     wrist_damping: float = 1.0
   81 |     wrist_max_torque: float = 50.0  # Nm
   82 |     wrist_gear: float = 1.0
   83 | 
   84 |     # ── 릴리즈 메커니즘 ──
   85 |     # 물리 시뮬레이션에서는 볼에 직접 속도를 부여하는 방식으로 추상화
   86 |     # (실제 그리퍼 메커니즘의 복잡성 회피)
   87 |     release_height: float = 2.0     # 지면에서 릴리즈 포인트 높이 (m)
   88 |     release_angle_deg: float = -5.0 # 릴리즈 각도 (하향: 음수)
   89 | 
   90 |     # ── 볼 물리 (MLB 규정) ──
   91 |     ball_mass: float = 0.145        # kg (5.125 oz = 145.15g)
   92 |     ball_radius: float = 0.037      # m (지름 7.4cm)
   93 |     ball_magnus_coeff: float = 0.25 # 실험 측정값
   94 | 
   95 |     # ── 투구 속도 범위 ──
   96 |     pitch_speed_range: Tuple[float, float] = (60.0, 160.0)  # km/h
   97 |     # 커리큘럼 단계별 속도
   98 |     curriculum_speeds: Dict[int, Tuple[float, float]] = field(default_factory=lambda: {
   99 |         1: (25.0, 30.0),   # Stage 1: 느림 (학습 초기)
  100 |         2: (30.0, 38.0),   # Stage 2: 중간
  101 |         3: (35.0, 43.0),   # Stage 3: 빠름
  102 |         4: (40.0, 50.0),   # Stage 4: 변화구 추가
  103 |         5: (45.0, 60.0),   # Stage 5: Self-Play 목표
  104 |     })
  105 | 
  106 |     # 구종별 스핀 파라미터 (RPM)
  107 |     pitch_types: Dict[str, Dict] = field(default_factory=lambda: {
  108 |         "fastball": {
  109 |             "spin_rpm": 2200,
  110 |             "spin_axis": (0, 1, 0),  # 역회전 (라이징)
  111 |             "speed_factor": 1.0,
  112 |             "description": "직구: 역회전, 빠름",
  113 |         },
  114 |         "curveball": {
  115 |             "spin_rpm": 2500,
  116 |             "spin_axis": (1, 0, 0),  # 탑스핀 (낙하)
  117 |             "speed_factor": 0.75,
  118 |             "description": "커브: 탑스핀, 아래로 휨",
  119 |         },
  120 |         "slider": {
  121 |             "spin_rpm": 2400,
  122 |             "spin_axis": (0.7, 0, 0.7),  # 사이드스핀
  123 |             "speed_factor": 0.85,
  124 |             "description": "슬라이더: 가로로 휨",
  125 |         },
  126 |         "changeup": {
  127 |             "spin_rpm": 1800,
  128 |             "spin_axis": (0, 1, 0),
  129 |             "speed_factor": 0.65,
  130 |             "description": "체인지업: 직구와 같은 팔 동작, 느림",
  131 |         },
  132 |     })
  133 | 
  134 |     # ── 파생 물리량 (계산값) ──
  135 |     @property
  136 |     def total_arm_length(self) -> float:
  137 |         """어깨→손목까지 팔 총 길이 (m)."""
  138 |         return self.upper_arm_length + self.forearm_length
  139 | 
  140 |     @property
  141 |     def max_release_speed_ms(self) -> float:
  142 |         """물리적 최대 릴리즈 속도 추정 (m/s).
  143 | 
  144 |         에너지 기반 근사:
  145 |           토크×각변위 = 0.5 × I × ω²
  146 |           I = (1/3) × m × L² (어깨 기준)
  147 |           gear ratio 적용 토크 = 토크 × gear
  148 |         """
  149 |         eff_torque = self.shoulder_max_torque * self.shoulder_gear  # 기어 적용
  150 |         I = (self.upper_arm_mass + self.forearm_mass) * self.total_arm_length ** 2 / 3
  151 |         theta = math.pi  # 180도 스윗 (백스윗 → 릴리즈)
  152 |         omega_sq = 2 * eff_torque * theta / (I + 1e-6)
  153 |         omega = math.sqrt(max(0, omega_sq))
  154 |         return omega * self.total_arm_length
  155 | 
  156 |     @property
  157 |     def max_release_speed_kmh(self) -> float:
  158 |         return self.max_release_speed_ms * 3.6
  159 | 
  160 |     @property
  161 |     def magnus_force_max_n(self) -> float:
  162 |         """최대 마그누스 힘 추정 (N).
  163 | 
  164 |         F_magnus = C_L * ρ * π * r² * v * (ω × v̂)
  165 |         단순화: F ≈ C_L * 0.5 * ρ * A * v²
  166 |         """
  167 |         rho = 1.225   # 공기 밀도 (kg/m³)
  168 |         A = math.pi * self.ball_radius ** 2
  169 |         v_max = self.pitch_speed_range[1] / 3.6  # m/s
  170 |         return self.ball_magnus_coeff * 0.5 * rho * A * v_max ** 2
  171 | 
  172 |     def validate(self) -> Dict[str, str]:
  173 |         """물리 파라미터 유효성 검사."""
  174 |         issues = {}
  175 | 
  176 |         # 볼 규격 검사 (MLB 기준)
  177 |         if not (0.141 <= self.ball_mass <= 0.149):
  178 |             issues["ball_mass"] = f"{self.ball_mass}kg — MLB 규정 0.141~0.149kg 범위 이탈"
  179 |         if not (0.0365 <= self.ball_radius <= 0.0375):
  180 |             issues["ball_radius"] = f"{self.ball_radius}m — MLB 규정 7.3~7.5cm 범위 이탈"
  181 | 
  182 |         # 최대 투구 속도 현실성 검사
  183 |         v = self.max_release_speed_kmh
  184 |         if v < 80:
  185 |             issues["speed_low"] = f"추정 최대 속도 {v:.0f}km/h — 너무 낮음 (목표 ≥120km/h)"
  186 |         elif v > 300:
  187 |             issues["speed_high"] = f"추정 최대 속도 {v:.0f}km/h — 비현실적으로 높음"
  188 | 
  189 |         # 릴리즈 높이 (일반적으로 1.5~2.5m)
  190 |         if not (1.2 <= self.release_height <= 2.8):
  191 |             issues["release_height"] = f"{self.release_height}m — 비현실적 릴리즈 높이"
  192 | 
  193 |         return issues
  194 | 
  195 |     def get_pitch_velocity(self, speed_kmh: float, pitch_type: str = "fastball") -> Tuple[float, float, float]:
  196 |         """투구 속도 벡터 계산 (MuJoCo freejoint 초기 속도).
  197 | 
  198 |         Args:
  199 |             speed_kmh: 투구 속도 (km/h)
  200 |             pitch_type: 구종
  201 | 
  202 |         Returns:
  203 |             (vy, vz, vx) 속도 벡터 (m/s) — MuJoCo 좌표계
  204 |         """
  205 |         speed_ms = speed_kmh / 3.6
  206 |         angle_rad = math.radians(self.release_angle_deg)
  207 | 
  208 |         # y축: 홈플레이트 방향 (음수)
  209 |         vy = -speed_ms * math.cos(angle_rad)
  210 |         # z축: 수직 (릴리즈 각도만큼 하향)
  211 |         vz = speed_ms * math.sin(angle_rad)
  212 |         vx = 0.0  # 직구 기준 (변화구는 별도 처리)
  213 | 
  214 |         return (vx, vy, vz)
  215 | 
  216 |     def print_summary(self):
  217 |         """물리 스펙 요약 출력."""
  218 |         issues = self.validate()
  219 |         print("=" * 55)
  220 |         print(" ⚾ Pitcher Robot — 물리 스펙 요약")
  221 |         print("=" * 55)
  222 |         print(f"  자유도        : 8 DOF (어깨3 + 팔꿈치2 + 손목2 + 릴리즈1)")
  223 |         print(f"  설치 위치     : y={self.base_pos[1]}m (투수 마운드)")
  224 |         print(f"  마운드 높이   : {self.mound_height*100:.0f}cm (MLB 규정 10인치)")
  225 |         print(f"  어깨 최대토크 : {self.shoulder_max_torque} Nm")
  226 |         print(f"  팔 길이       : {self.total_arm_length:.2f} m")
  227 |         print(f"  릴리즈 높이   : {self.release_height:.1f} m")
  228 |         print(f"  최대 투구 속도: {self.max_release_speed_kmh:.0f} km/h (추정)")
  229 |         print(f"  볼 질량       : {self.ball_mass*1000:.0f} g")
  230 |         print(f"  볼 직경       : {self.ball_radius*200:.1f} cm")
  231 |         print(f"  최대 마그누스 힘: {self.magnus_force_max_n:.2f} N")
  232 |         print(f"\n  구종 목록:")
  233 |         for name, params in self.pitch_types.items():
  234 |             print(f"    [{name:10s}] {params['description']}")
  235 |         if issues:
  236 |             print(f"\n  ⚠️  검증 이슈:")
  237 |             for k, v in issues.items():
  238 |                 print(f"    - {k}: {v}")
  239 |         else:
  240 |             print(f"\n  ✅ 물리 파라미터 검증 통과")
  241 |         print("=" * 55)
  242 | 
  243 | 
  244 | # 기본 파라미터 인스턴스
  245 | DEFAULT_PITCHER = PitcherRobotParams()
  246 | 
  247 | 
  248 | if __name__ == "__main__":
  249 |     robot = PitcherRobotParams()
  250 |     robot.print_summary()
  251 |     print(f"\n  직구 100km/h 속도 벡터: {robot.get_pitch_velocity(100, 'fastball')}")
  252 |     print(f"  커브 80km/h 속도 벡터:  {robot.get_pitch_velocity(80, 'curveball')}")
````
