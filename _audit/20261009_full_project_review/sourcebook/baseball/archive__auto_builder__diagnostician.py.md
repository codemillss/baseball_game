# baseball/archive/auto_builder/diagnostician.py

원본: [archive/auto_builder/diagnostician.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/auto_builder/diagnostician.py)

SHA256: `2fd9546543b487b1608ec8976a4ded2fdebc49799129c834404920a4651370d5`

전체 77행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `Diagnostician` | ClassDef | 11 | 77 |
| `__init__` | FunctionDef | 12 | 13 |
| `diagnose` | FunctionDef | 15 | 32 |
| `_diagnose_phase_1` | FunctionDef | 34 | 41 |
| `_diagnose_phase_2` | FunctionDef | 43 | 48 |
| `_diagnose_phase_3` | FunctionDef | 50 | 64 |
| `_diagnose_phase_4` | FunctionDef | 66 | 77 |

## 전체 원문

````text
    1 | """
    2 | diagnostician.py — 정체 구간 원인 분석 및 파라미터 조정(Plan Adjuster)
    3 | 
    4 | 학습이 정체(Stuck)되었을 때, 메트릭을 분석하여 환경 또는 학습 파라미터를 
    5 | 어떻게 조정할지(Action Plan)를 결정합니다.
    6 | """
    7 | 
    8 | from typing import Dict, Any, List
    9 | 
   10 | 
   11 | class Diagnostician:
   12 |     def __init__(self):
   13 |         pass
   14 | 
   15 |     def diagnose(self, phase_id: int, metrics: Dict[str, Any]) -> Dict[str, Any]:
   16 |         """
   17 |         메트릭을 분석하여 조정 계획(Action Plan)을 반환합니다.
   18 |         
   19 |         Returns:
   20 |             Dict: 조정할 파라미터 딕셔너리
   21 |                 예) {'env.pitch_speed': 30.0, 'reward.contact_bonus': 5.0}
   22 |         """
   23 |         if phase_id == 1:
   24 |             return self._diagnose_phase_1(metrics)
   25 |         elif phase_id == 2:
   26 |             return self._diagnose_phase_2(metrics)
   27 |         elif phase_id == 3:
   28 |             return self._diagnose_phase_3(metrics)
   29 |         elif phase_id == 4:
   30 |             return self._diagnose_phase_4(metrics)
   31 |         else:
   32 |             return {}
   33 | 
   34 |     def _diagnose_phase_1(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
   35 |         """Phase 1 (모션) 진단"""
   36 |         plan = {}
   37 |         # 타자 스윙이 안 되면 토크 상한을 더 풀어주거나 보상 셰이핑 조정
   38 |         if metrics.get('swing_completion_rate', 0.0) < 0.5:
   39 |             plan['action_penalty_weight'] = 0.5  # 액션 페널티 감소 (움직임 장려)
   40 |             plan['swing_bonus'] = 2.0            # 스윙 보너스 증가
   41 |         return plan
   42 | 
   43 |     def _diagnose_phase_2(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
   44 |         """Phase 2 (시선 추적) 진단"""
   45 |         plan = {}
   46 |         if metrics.get('visual_tracking_rate', 0.0) < 0.5:
   47 |             plan['pitch_speed_max'] = 40.0       # 공 속도를 늦춰서 보기 쉽게 만듦
   48 |         return plan
   49 | 
   50 |     def _diagnose_phase_3(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
   51 |         """Phase 3 (첫 컨택) 진단"""
   52 |         plan = {}
   53 |         contact_rate = metrics.get('contact_rate', 0.0)
   54 |         swing_rate = metrics.get('swing_completion_rate', 0.0)
   55 |         
   56 |         if swing_rate < 0.5:
   57 |             # 아예 스윙을 안해서 못 치는 경우
   58 |             plan['swing_bonus'] = 3.0
   59 |         elif contact_rate < 0.05:
   60 |             # 스윙은 하는데 안 맞는 경우 -> 거리를 좁히거나 (release_distance 감소) 공을 더 크게 만듦
   61 |             plan['release_distance'] = max(2.0, metrics.get('current_release_distance', 18.44) * 0.8)
   62 |             plan['pitch_speed_max'] = 35.0
   63 |             
   64 |         return plan
   65 | 
   66 |     def _diagnose_phase_4(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
   67 |         """Phase 4 (양질의 컨택) 진단"""
   68 |         plan = {}
   69 |         ev = metrics.get('avg_exit_velocity_kmh', 0.0)
   70 |         ss = metrics.get('sweet_spot_rate', 0.0)
   71 |         
   72 |         if ev < 50.0:
   73 |             # 빗맞음 -> 스윗 스팟 보상 강화
   74 |             plan['sweet_spot_bonus_weight'] = 2.0
   75 |             plan['power_bonus_weight'] = 1.5
   76 |             
   77 |         return plan
````
