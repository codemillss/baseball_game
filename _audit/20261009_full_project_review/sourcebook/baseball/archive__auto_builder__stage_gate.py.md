# baseball/archive/auto_builder/stage_gate.py

원본: [archive/auto_builder/stage_gate.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/auto_builder/stage_gate.py)

SHA256: `9a820e691868df4686fef597a149e82202550f71458bea236323d9cca35e2f5c`

전체 227행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `StageGate` | ClassDef | 12 | 27 |
| `__init__` | FunctionDef | 15 | 17 |
| `evaluate` | FunctionDef | 19 | 27 |
| `Phase1Gate` | ClassDef | 30 | 55 |
| `__init__` | FunctionDef | 31 | 32 |
| `evaluate` | FunctionDef | 34 | 55 |
| `Phase2Gate` | ClassDef | 58 | 78 |
| `__init__` | FunctionDef | 59 | 60 |
| `evaluate` | FunctionDef | 62 | 78 |
| `Phase3Gate` | ClassDef | 81 | 101 |
| `__init__` | FunctionDef | 82 | 83 |
| `evaluate` | FunctionDef | 85 | 101 |
| `Phase4Gate` | ClassDef | 104 | 128 |
| `__init__` | FunctionDef | 105 | 106 |
| `evaluate` | FunctionDef | 108 | 128 |
| `Phase5Gate` | ClassDef | 131 | 153 |
| `__init__` | FunctionDef | 132 | 133 |
| `evaluate` | FunctionDef | 135 | 153 |
| `Phase6Gate` | ClassDef | 156 | 182 |
| `__init__` | FunctionDef | 157 | 158 |
| `evaluate` | FunctionDef | 160 | 182 |
| `Phase7Gate` | ClassDef | 185 | 207 |
| `__init__` | FunctionDef | 186 | 187 |
| `evaluate` | FunctionDef | 189 | 207 |
| `GateKeeper` | ClassDef | 210 | 227 |
| `__init__` | FunctionDef | 213 | 222 |
| `evaluate` | FunctionDef | 224 | 227 |

## 전체 원문

````text
    1 | """
    2 | stage_gate.py — 학습 단계별 통과 기준(Stage Gate) 정의
    3 | 
    4 | 각 Phase 별 성공 기준(Success Criteria)을 정의합니다.
    5 | AutoGameBuilder가 현재 모델 성능(Metrics)을 평가하여
    6 | 다음 단계로 넘어갈지, 혹은 파라미터를 조정할지 결정하는 기준이 됩니다.
    7 | """
    8 | 
    9 | from typing import Dict, Any, Tuple
   10 | 
   11 | 
   12 | class StageGate:
   13 |     """단일 Stage의 통과/정체 상태를 평가하는 클래스."""
   14 | 
   15 |     def __init__(self, name: str, phase_id: int):
   16 |         self.name = name
   17 |         self.phase_id = phase_id
   18 | 
   19 |     def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
   20 |         """
   21 |         메트릭을 평가하여 상태를 반환합니다.
   22 |         Returns:
   23 |             passed (bool): 통과 여부 (다음 단계로 진행)
   24 |             stuck (bool): 정체 여부 (파라미터 조정 필요)
   25 |             reason (str): 판단 이유
   26 |         """
   27 |         raise NotImplementedError
   28 | 
   29 | 
   30 | class Phase1Gate(StageGate):
   31 |     def __init__(self):
   32 |         super().__init__("Phase 1: Motor Primitives", 1)
   33 | 
   34 |     def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
   35 |         """
   36 |         성공 기준:
   37 |           [투수] 투구 동작 완료율 > 80% (release 됨)
   38 |           [타자] 스윙 완료율 > 80% (bat tip speed > 60km/h)
   39 |         """
   40 |         pitch_completion = metrics.get('pitch_completion_rate', 0.0)
   41 |         swing_completion = metrics.get('swing_completion_rate', 0.0)
   42 |         bat_speed = metrics.get('avg_bat_speed_kmh', 0.0)
   43 | 
   44 |         passed = pitch_completion > 0.8 and swing_completion > 0.8 and bat_speed > 60.0
   45 |         
   46 |         # 1000 에피소드 이상 진행되었는데도 통과하지 못한 경우
   47 |         episodes = metrics.get('episodes', 0)
   48 |         stuck = not passed and episodes > 1000
   49 | 
   50 |         if passed:
   51 |             return True, False, "투수/타자 기본 모션 완료"
   52 |         elif stuck:
   53 |             return False, True, f"모션 학습 정체 (Pitch:{pitch_completion:.1f}, Swing:{swing_completion:.1f}, Spd:{bat_speed:.1f})"
   54 |         else:
   55 |             return False, False, "모션 학습 진행 중"
   56 | 
   57 | 
   58 | class Phase2Gate(StageGate):
   59 |     def __init__(self):
   60 |         super().__init__("Phase 2: Ball Tracking", 2)
   61 | 
   62 |     def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
   63 |         """
   64 |         성공 기준:
   65 |           시야 유지율 > 90% (공이 박스 통과할 때까지)
   66 |         """
   67 |         tracking_rate = metrics.get('visual_tracking_rate', 0.0)
   68 |         
   69 |         passed = tracking_rate > 0.90
   70 |         episodes = metrics.get('episodes_in_phase', 0)
   71 |         stuck = not passed and episodes > 2000
   72 | 
   73 |         if passed:
   74 |             return True, False, "시선 추적 안정화"
   75 |         elif stuck:
   76 |             return False, True, f"시선 추적 정체 (Tracking:{tracking_rate:.1%})"
   77 |         else:
   78 |             return False, False, "시선 추적 학습 중"
   79 | 
   80 | 
   81 | class Phase3Gate(StageGate):
   82 |     def __init__(self):
   83 |         super().__init__("Phase 3: First Contact", 3)
   84 | 
   85 |     def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
   86 |         """
   87 |         성공 기준:
   88 |           Contact Rate > 20%
   89 |         """
   90 |         contact_rate = metrics.get('contact_rate', 0.0)
   91 |         
   92 |         passed = contact_rate > 0.20
   93 |         episodes = metrics.get('episodes_in_phase', 0)
   94 |         stuck = contact_rate < 0.05 and episodes > 3000
   95 | 
   96 |         if passed:
   97 |             return True, False, "초기 컨택 확보"
   98 |         elif stuck:
   99 |             return False, True, f"컨택 실패 정체 (Contact:{contact_rate:.1%})"
  100 |         else:
  101 |             return False, False, "컨택 학습 중"
  102 | 
  103 | 
  104 | class Phase4Gate(StageGate):
  105 |     def __init__(self):
  106 |         super().__init__("Phase 4: Quality Contact", 4)
  107 | 
  108 |     def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
  109 |         """
  110 |         성공 기준:
  111 |           Contact Rate > 50%
  112 |           Avg Exit Velocity > 80 km/h
  113 |           Sweet Spot Rate > 30%
  114 |         """
  115 |         contact_rate = metrics.get('contact_rate', 0.0)
  116 |         ev = metrics.get('avg_exit_velocity_kmh', 0.0)
  117 |         ss_rate = metrics.get('sweet_spot_rate', 0.0)
  118 |         
  119 |         passed = contact_rate > 0.50 and ev > 80.0 and ss_rate > 0.30
  120 |         episodes = metrics.get('episodes_in_phase', 0)
  121 |         stuck = (contact_rate < 0.20 or ev < 40.0) and episodes > 5000
  122 | 
  123 |         if passed:
  124 |             return True, False, "양질의 타구 확보"
  125 |         elif stuck:
  126 |             return False, True, f"타구 품질 정체 (CR:{contact_rate:.1%}, EV:{ev:.1f}, SS:{ss_rate:.1%})"
  127 |         else:
  128 |             return False, False, "타격 품질 개선 중"
  129 | 
  130 | 
  131 | class Phase5Gate(StageGate):
  132 |     def __init__(self):
  133 |         super().__init__("Phase 5: Self-Play Exploration", 5)
  134 | 
  135 |     def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
  136 |         """
  137 |         성공 기준:
  138 |           [투수] 스트라이크존 투구 비율 > 40% (제구력 확보)
  139 |           [타자] Contact Rate > 30% (다양한 공에 대한 대처)
  140 |         """
  141 |         strike_rate = metrics.get('pitcher_strike_rate', 0.0)
  142 |         contact_rate = metrics.get('contact_rate', 0.0)
  143 |         
  144 |         passed = strike_rate > 0.40 and contact_rate > 0.30
  145 |         episodes = metrics.get('episodes_in_phase', 0)
  146 |         stuck = (strike_rate < 0.10 or contact_rate < 0.10) and episodes > 5000
  147 | 
  148 |         if passed:
  149 |             return True, False, "기본 제구력 및 타격 대처 확보 (경쟁 준비 완료)"
  150 |         elif stuck:
  151 |             return False, True, f"Self-Play 탐색 정체 (Strike:{strike_rate:.1%}, Contact:{contact_rate:.1%})"
  152 |         else:
  153 |             return False, False, "Self-Play 탐색 학습 중"
  154 | 
  155 | 
  156 | class Phase6Gate(StageGate):
  157 |     def __init__(self):
  158 |         super().__init__("Phase 6: Competitive Self-Play", 6)
  159 | 
  160 |     def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
  161 |         """
  162 |         성공 기준:
  163 |           양측의 승률(Reward 우위)이 균형을 이루며(40~60%),
  164 |           고도화된 지표(Exit Velocity > 100km/h, Pitching Speed > 100km/h) 달성
  165 |         """
  166 |         batter_win_rate = metrics.get('batter_win_rate', 0.5)
  167 |         ev = metrics.get('avg_exit_velocity_kmh', 0.0)
  168 |         pitch_speed = metrics.get('avg_pitch_speed_kmh', 0.0)
  169 |         
  170 |         balance_ok = 0.40 <= batter_win_rate <= 0.60
  171 |         quality_ok = ev > 100.0 and pitch_speed > 100.0
  172 |         
  173 |         passed = balance_ok and quality_ok
  174 |         episodes = metrics.get('episodes_in_phase', 0)
  175 |         stuck = not passed and episodes > 10000
  176 | 
  177 |         if passed:
  178 |             return True, False, "고품질 경쟁적 Self-Play 달성 (인간 수준 근접)"
  179 |         elif stuck:
  180 |             return False, True, f"경쟁 고도화 정체 (WinRate:{batter_win_rate:.1%}, EV:{ev:.0f}, Pitch:{pitch_speed:.0f})"
  181 |         else:
  182 |             return False, False, "경쟁적 Self-Play 진행 중"
  183 | 
  184 | 
  185 | class Phase7Gate(StageGate):
  186 |     def __init__(self):
  187 |         super().__init__("Phase 7: World Model Mastery", 7)
  188 | 
  189 |     def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
  190 |         """
  191 |         성공 기준:
  192 |           World Model의 예측력(Prediction)과 상상 보상(Imagination Reward)이 최고 수준 도달
  193 |         """
  194 |         wm_loss_p = metrics.get('pitcher_wm_loss', 999.0)
  195 |         wm_loss_b = metrics.get('batter_wm_loss', 999.0)
  196 |         imag_rew_b = metrics.get('batter_imag_rew', 0.0)
  197 |         
  198 |         passed = wm_loss_p < 2.0 and wm_loss_b < 2.0 and imag_rew_b > 5.0
  199 |         episodes = metrics.get('episodes_in_phase', 0)
  200 |         stuck = not passed and episodes > 20000
  201 | 
  202 |         if passed:
  203 |             return True, False, "World Model 마스터리 달성 (최상위 성능)"
  204 |         elif stuck:
  205 |             return False, True, f"World Model 수렴 정체 (Loss P:{wm_loss_p:.1f} B:{wm_loss_b:.1f})"
  206 |         else:
  207 |             return False, False, "World Model 최적화 중"
  208 | 
  209 | 
  210 | class GateKeeper:
  211 |     """현재 Phase에 맞는 Gate를 관리합니다."""
  212 |     
  213 |     def __init__(self):
  214 |         self.gates = {
  215 |             1: Phase1Gate(),
  216 |             2: Phase2Gate(),
  217 |             3: Phase3Gate(),
  218 |             4: Phase4Gate(),
  219 |             5: Phase5Gate(),
  220 |             6: Phase6Gate(),
  221 |             7: Phase7Gate(),
  222 |         }
  223 |         
  224 |     def evaluate(self, phase_id: int, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
  225 |         if phase_id not in self.gates:
  226 |             return False, False, f"Phase {phase_id}에 대한 Gate가 없습니다."
  227 |         return self.gates[phase_id].evaluate(metrics)
````
