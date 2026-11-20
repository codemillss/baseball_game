# baseball/archive/training/reward_audit.py

원본: [archive/training/reward_audit.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/reward_audit.py)

SHA256: `5fc9fa3806adbd88f89d3048120baceec7f89ed0fecfcc16f7809cb6ec51307e`

전체 96행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `RewardAuditSystem` | ClassDef | 14 | 96 |
| `__init__` | FunctionDef | 17 | 26 |
| `record_hit` | FunctionDef | 28 | 37 |
| `audit` | FunctionDef | 39 | 80 |
| `get_summary` | FunctionDef | 82 | 96 |

## 전체 원문

````text
    1 | """
    2 | reward_audit.py — 보상 악용(Reward Hacking) 자동 감시 및 분석
    3 | 
    4 | Exit Velocity, Spray Angle 등의 분포를 추적하여,
    5 | 정상적인 야구 타격이 아닌 편법(예: 배트 밀어넣기, 연속 파울)으로
    6 | 보상을 수확하는 징후를 감지합니다.
    7 | """
    8 | 
    9 | import numpy as np
   10 | from collections import deque
   11 | from typing import Dict, List, Optional
   12 | 
   13 | 
   14 | class RewardAuditSystem:
   15 |     """보상 악용 및 이상 타격 패턴 자동 감시 시스템."""
   16 | 
   17 |     def __init__(self, window_size: int = 100):
   18 |         self.window_size = window_size
   19 |         
   20 |         # 타격 성공 시의 메트릭만 추적
   21 |         self.exit_velocities = deque(maxlen=window_size)
   22 |         self.launch_angles = deque(maxlen=window_size)
   23 |         self.spray_angles = deque(maxlen=window_size)
   24 |         self.rewards = deque(maxlen=window_size)
   25 |         
   26 |         self.alerts: List[Dict] = []
   27 | 
   28 |     def record_hit(self, info: Dict, reward: float):
   29 |         """타격이 발생한 에피소드의 데이터를 기록합니다."""
   30 |         if "exit_velocity_kmh" in info:
   31 |             self.exit_velocities.append(info["exit_velocity_kmh"])
   32 |         if "launch_angle" in info:
   33 |             self.launch_angles.append(info["launch_angle"])
   34 |         if "spray_angle" in info:
   35 |             self.spray_angles.append(info["spray_angle"])
   36 |             
   37 |         self.rewards.append(reward)
   38 | 
   39 |     def audit(self) -> List[str]:
   40 |         """현재 타격 분포를 분석하여 이상 징후를 보고합니다."""
   41 |         alerts = []
   42 |         n_hits = len(self.exit_velocities)
   43 |         
   44 |         if n_hits < 20:
   45 |             return alerts  # 분석하기에 데이터 부족
   46 | 
   47 |         # 1. "배트 밀어넣기" (Bunting/Pushing) 감지
   48 |         # 보상은 받는데 타구 속도가 비정상적으로 낮은 경우
   49 |         avg_exit_velo = np.mean(list(self.exit_velocities))
   50 |         if avg_exit_velo < 40.0:
   51 |             alerts.append(
   52 |                 f"🚨 [보상 악용 의심] 타구 속도 비정상 낮음 (평균 {avg_exit_velo:.1f}km/h). "
   53 |                 "배트를 휘두르지 않고 공 궤적에 밀어넣는 편법 가능성 높음."
   54 |             )
   55 | 
   56 |         # 2. "연속 파울" (Foul Spamming) 감지
   57 |         # 파울 페널티가 너무 작을 때, 파울만 쳐서 에피소드를 끝내려는 징후
   58 |         foul_count = sum(1 for sa in self.spray_angles if abs(sa) > 45.0)
   59 |         foul_rate = foul_count / n_hits
   60 |         if foul_rate > 0.8:
   61 |             alerts.append(
   62 |                 f"⚠️ [보상 악용 의심] 파울 비율 극단적 높음 ({foul_rate:.1%}). "
   63 |                 "파울 페널티(현재 -0.5)를 강화하거나 페어존 보너스를 높여야 함."
   64 |             )
   65 | 
   66 |         # 3. 타구 다양성 상실 (Mode Collapse)
   67 |         # 모든 타구가 동일한 각도/속도로 날아가는 경우 (표준편차 극소)
   68 |         if len(self.launch_angles) > 50:
   69 |             la_std = np.std(list(self.launch_angles))
   70 |             sa_std = np.std(list(self.spray_angles))
   71 |             if la_std < 2.0 and sa_std < 2.0:
   72 |                 alerts.append(
   73 |                     f"⚠️ [다양성 상실] 타구 각도 분포가 극도로 편중됨 (LA Std={la_std:.1f}, SA Std={sa_std:.1f})."
   74 |                 )
   75 |                 
   76 |         # 알림 저장
   77 |         for alert in alerts:
   78 |             self.alerts.append({"message": alert})
   79 | 
   80 |         return alerts
   81 | 
   82 |     def get_summary(self) -> str:
   83 |         """현재 감사 요약을 문자열로 반환합니다."""
   84 |         n_hits = len(self.exit_velocities)
   85 |         if n_hits == 0:
   86 |             return "No hits recorded."
   87 |             
   88 |         avg_ev = np.mean(list(self.exit_velocities))
   89 |         max_ev = np.max(list(self.exit_velocities))
   90 |         foul_count = sum(1 for sa in self.spray_angles if abs(sa) > 45.0)
   91 |         
   92 |         return (
   93 |             f"[Audit] Hits: {n_hits} | "
   94 |             f"Avg EV: {avg_ev:.1f} km/h (Max: {max_ev:.1f}) | "
   95 |             f"Foul Rate: {foul_count/n_hits:.1%}"
   96 |         )
````
