# baseball/archive/training/curriculum_manager.py

원본: [archive/training/curriculum_manager.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/curriculum_manager.py)

SHA256: `af0b8d346486af066ac28f71fac04147482de7a47690681cd0b5c2a413765005`

전체 150행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `CurriculumManager` | ClassDef | 12 | 150 |
| `__init__` | FunctionDef | 31 | 48 |
| `record_episode` | FunctionDef | 50 | 57 |
| `get_contact_rate` | FunctionDef | 59 | 63 |
| `should_promote` | FunctionDef | 65 | 80 |
| `promote` | FunctionDef | 82 | 102 |
| `should_demote` | FunctionDef | 104 | 118 |
| `demote` | FunctionDef | 120 | 128 |
| `check_and_update` | FunctionDef | 130 | 140 |
| `get_status_str` | FunctionDef | 142 | 150 |

## 전체 원문

````text
    1 | """
    2 | curriculum_manager.py — 커리큘럼 학습 자동 관리자
    3 | 
    4 | Contact Rate를 실시간 모니터링하여 커리큘럼 Stage를 자동 승격하고,
    5 | 학습이 불안정할 경우 이전 Stage로 롤백합니다.
    6 | """
    7 | 
    8 | from typing import Optional, List, Dict
    9 | from collections import deque
   10 | 
   11 | 
   12 | class CurriculumManager:
   13 |     """커리큘럼 학습 자동 관리자.
   14 | 
   15 |     Args:
   16 |         initial_stage: 시작 커리큘럼 단계 (1~5)
   17 |         window_size: 승격 판단에 사용할 최근 에피소드 수
   18 |         promotion_patience: 승격 조건을 연속 N회 충족해야 승격
   19 |         max_stage: 최대 커리큘럼 단계
   20 |     """
   21 | 
   22 |     # 각 Stage별 승격 기준 Contact Rate
   23 |     PROMOTION_THRESHOLDS = {
   24 |         1: 0.40,  # Stage 1 → 2: Contact Rate > 40%
   25 |         2: 0.25,  # Stage 2 → 3: > 25%
   26 |         3: 0.15,  # Stage 3 → 4: > 15%
   27 |         4: 0.10,  # Stage 4 → 5: > 10%
   28 |         5: None,  # 최종 단계
   29 |     }
   30 | 
   31 |     def __init__(
   32 |         self,
   33 |         initial_stage: int = 1,
   34 |         window_size: int = 50,
   35 |         promotion_patience: int = 3,
   36 |         max_stage: int = 5,
   37 |     ):
   38 |         self.current_stage = initial_stage
   39 |         self.window_size = window_size
   40 |         self.promotion_patience = promotion_patience
   41 |         self.max_stage = max_stage
   42 | 
   43 |         # 최근 에피소드 결과 슬라이딩 윈도우
   44 |         self.contact_history: deque = deque(maxlen=window_size)
   45 |         self.consecutive_promotable = 0
   46 | 
   47 |         # 로그
   48 |         self.stage_history: List[Dict] = []
   49 | 
   50 |     def record_episode(self, contacted: bool, info: Optional[Dict] = None):
   51 |         """에피소드 결과를 기록합니다.
   52 | 
   53 |         Args:
   54 |             contacted: 이번 에피소드에서 배트-공 충돌이 발생했는지
   55 |             info: 추가 에피소드 정보 (exit_velo, result 등)
   56 |         """
   57 |         self.contact_history.append(1.0 if contacted else 0.0)
   58 | 
   59 |     def get_contact_rate(self) -> float:
   60 |         """최근 윈도우의 Contact Rate를 반환합니다."""
   61 |         if len(self.contact_history) == 0:
   62 |             return 0.0
   63 |         return sum(self.contact_history) / len(self.contact_history)
   64 | 
   65 |     def should_promote(self) -> bool:
   66 |         """현재 Stage에서 다음 Stage로 승격해야 하는지 판단합니다."""
   67 |         threshold = self.PROMOTION_THRESHOLDS.get(self.current_stage)
   68 |         if threshold is None:
   69 |             return False  # 최종 단계
   70 | 
   71 |         if len(self.contact_history) < self.window_size // 2:
   72 |             return False  # 데이터 부족
   73 | 
   74 |         rate = self.get_contact_rate()
   75 |         if rate >= threshold:
   76 |             self.consecutive_promotable += 1
   77 |         else:
   78 |             self.consecutive_promotable = 0
   79 | 
   80 |         return self.consecutive_promotable >= self.promotion_patience
   81 | 
   82 |     def promote(self) -> int:
   83 |         """다음 Stage로 승격합니다.
   84 | 
   85 |         Returns:
   86 |             새로운 Stage 번호
   87 |         """
   88 |         old_stage = self.current_stage
   89 |         # clear() 전에 rate를 먼저 기록해야 올바른 값이 저장됨
   90 |         rate_at_promotion = self.get_contact_rate()
   91 |         self.current_stage = min(self.current_stage + 1, self.max_stage)
   92 |         self.consecutive_promotable = 0
   93 |         self.contact_history.clear()
   94 | 
   95 |         self.stage_history.append({
   96 |             "from_stage": old_stage,
   97 |             "to_stage": self.current_stage,
   98 |             "contact_rate_at_promotion": rate_at_promotion,
   99 |         })
  100 | 
  101 |         print(f"  🎓 커리큘럼 승격: Stage {old_stage} → Stage {self.current_stage}")
  102 |         return self.current_stage
  103 | 
  104 |     def should_demote(self) -> bool:
  105 |         """학습이 붕괴되어 이전 Stage로 롤백해야 하는지 판단합니다."""
  106 |         if self.current_stage <= 1:
  107 |             return False
  108 | 
  109 |         if len(self.contact_history) < self.window_size:
  110 |             return False
  111 | 
  112 |         rate = self.get_contact_rate()
  113 |         # 현재 Stage의 이전 Stage 기준보다도 못하면 롤백
  114 |         prev_threshold = self.PROMOTION_THRESHOLDS.get(self.current_stage - 1, 0.0)
  115 |         if prev_threshold and rate < prev_threshold * 0.3:
  116 |             return True
  117 | 
  118 |         return False
  119 | 
  120 |     def demote(self) -> int:
  121 |         """이전 Stage로 롤백합니다."""
  122 |         old_stage = self.current_stage
  123 |         self.current_stage = max(1, self.current_stage - 1)
  124 |         self.consecutive_promotable = 0
  125 |         self.contact_history.clear()
  126 | 
  127 |         print(f"  ⚠️ 커리큘럼 롤백: Stage {old_stage} → Stage {self.current_stage}")
  128 |         return self.current_stage
  129 | 
  130 |     def check_and_update(self) -> int:
  131 |         """승격/롤백 여부를 확인하고 필요 시 업데이트합니다.
  132 | 
  133 |         Returns:
  134 |             현재(업데이트 후) Stage 번호
  135 |         """
  136 |         if self.should_promote():
  137 |             return self.promote()
  138 |         elif self.should_demote():
  139 |             return self.demote()
  140 |         return self.current_stage
  141 | 
  142 |     def get_status_str(self) -> str:
  143 |         """현재 커리큘럼 상태 문자열을 반환합니다."""
  144 |         rate = self.get_contact_rate()
  145 |         threshold = self.PROMOTION_THRESHOLDS.get(self.current_stage, "N/A")
  146 |         return (
  147 |             f"Stage {self.current_stage}/5 | "
  148 |             f"Contact Rate: {rate:.1%} | "
  149 |             f"Promotion Target: {threshold}"
  150 |         )
````
