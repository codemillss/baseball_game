# baseball/archive/envs/game_engine.py

원본: [archive/envs/game_engine.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/envs/game_engine.py)

SHA256: `d9485f665ab2509d38c87d87253a5456585d86876dee2b513e6a34f9d1ef78a4`

전체 163행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BaseballGameEngine` | ClassDef | 4 | 163 |
| `__init__` | FunctionDef | 8 | 10 |
| `reset_game` | FunctionDef | 12 | 22 |
| `reset_at_bat` | FunctionDef | 24 | 26 |
| `get_context_vector` | FunctionDef | 28 | 40 |
| `process_pitch` | FunctionDef | 42 | 96 |
| `_resolve_hit` | FunctionDef | 98 | 121 |
| `_advance_runners` | FunctionDef | 123 | 143 |
| `_add_out` | FunctionDef | 145 | 147 |
| `_check_inning_state` | FunctionDef | 149 | 163 |

## 전체 원문

````text
    1 | import numpy as np
    2 | from typing import Dict, Any, Tuple
    3 | 
    4 | class BaseballGameEngine:
    5 |     """
    6 |     9이닝 야구 경기 룰 및 상태 추적 엔진
    7 |     """
    8 |     def __init__(self, max_innings: int = 9):
    9 |         self.max_innings = max_innings
   10 |         self.reset_game()
   11 | 
   12 |     def reset_game(self):
   13 |         self.inning = 1
   14 |         self.is_top = True # True: 어웨이팀 공격, False: 홈팀 공격
   15 |         self.score_away = 0
   16 |         self.score_home = 0
   17 |         self.outs = 0
   18 |         self.strikes = 0
   19 |         self.balls = 0
   20 |         # 주자 상태: [1루, 2루, 3루]
   21 |         self.runners = [0, 0, 0]
   22 |         self.game_over = False
   23 | 
   24 |     def reset_at_bat(self):
   25 |         self.strikes = 0
   26 |         self.balls = 0
   27 | 
   28 |     def get_context_vector(self) -> np.ndarray:
   29 |         """
   30 |         에이전트의 뇌(Context)에 주입되는 상태 벡터 (6D)
   31 |         [balls(0-3), strikes(0-2), outs(0-2), r1, r2, r3]
   32 |         """
   33 |         return np.array([
   34 |             self.balls / 3.0,
   35 |             self.strikes / 2.0,
   36 |             self.outs / 2.0,
   37 |             float(self.runners[0]),
   38 |             float(self.runners[1]),
   39 |             float(self.runners[2])
   40 |         ], dtype=np.float32)
   41 | 
   42 |     def process_pitch(self, 
   43 |                       swung: bool, 
   44 |                       contacted: bool, 
   45 |                       in_strike_zone: bool, 
   46 |                       exit_velocity_kmh: float = 0.0, 
   47 |                       distance_m: float = 0.0) -> Tuple[str, int]:
   48 |         """
   49 |         투구 결과를 처리하고 (이벤트 문자열, 발생한 득점) 반환
   50 |         """
   51 |         if self.game_over:
   52 |             return "Game Over", 0
   53 | 
   54 |         event = ""
   55 |         runs_scored = 0
   56 | 
   57 |         if contacted:
   58 |             if distance_m < 2.0:
   59 |                 event = "Foul"
   60 |                 if self.strikes < 2:
   61 |                     self.strikes += 1
   62 |             else:
   63 |                 event, runs_scored = self._resolve_hit(exit_velocity_kmh, distance_m)
   64 |         else:
   65 |             if swung:
   66 |                 event = "Swinging Strike"
   67 |                 self.strikes += 1
   68 |             else:
   69 |                 if in_strike_zone:
   70 |                     event = "Called Strike"
   71 |                     self.strikes += 1
   72 |                 else:
   73 |                     event = "Ball"
   74 |                     self.balls += 1
   75 | 
   76 |         # 볼넷 처리
   77 |         if self.balls >= 4:
   78 |             event = "Walk"
   79 |             runs_scored = self._advance_runners(1, force=True)
   80 |             self.reset_at_bat()
   81 | 
   82 |         # 삼진 처리
   83 |         if self.strikes >= 3:
   84 |             event = "Strikeout"
   85 |             self._add_out()
   86 | 
   87 |         # 이닝/게임 종료 체크 로직
   88 |         self._check_inning_state()
   89 |         
   90 |         # 득점 적용
   91 |         if self.is_top:
   92 |             self.score_away += runs_scored
   93 |         else:
   94 |             self.score_home += runs_scored
   95 | 
   96 |         return event, runs_scored
   97 | 
   98 |     def _resolve_hit(self, ev: float, dist: float) -> Tuple[str, int]:
   99 |         """비거리와 타구 속도로 안타/아웃 판정 및 주자 진루 처리"""
  100 |         if ev < 70.0 or dist < 15.0:
  101 |             self._add_out()
  102 |             return "Ground Out / Pop Out", 0
  103 |         
  104 |         runs = 0
  105 |         if dist >= 90.0:
  106 |             # 홈런
  107 |             runs = self._advance_runners(4) + 1 # 타자 본인 포함
  108 |             self.reset_at_bat()
  109 |             return "Home Run", runs
  110 |         elif dist >= 50.0:
  111 |             # 2루타
  112 |             runs = self._advance_runners(2)
  113 |             self.runners[1] = 1 # 타자는 2루로
  114 |             self.reset_at_bat()
  115 |             return "Double", runs
  116 |         else:
  117 |             # 단타
  118 |             runs = self._advance_runners(1)
  119 |             self.runners[0] = 1 # 타자는 1루로
  120 |             self.reset_at_bat()
  121 |             return "Single", runs
  122 | 
  123 |     def _advance_runners(self, bases: int, force: bool = False) -> int:
  124 |         runs = 0
  125 |         if force: # 볼넷 밀어내기
  126 |             if self.runners[0] == 1:
  127 |                 if self.runners[1] == 1:
  128 |                     if self.runners[2] == 1:
  129 |                         runs += 1
  130 |                     self.runners[2] = 1
  131 |                 self.runners[1] = 1
  132 |             self.runners[0] = 1
  133 |         else:
  134 |             new_runners = [0, 0, 0]
  135 |             for i in range(2, -1, -1):
  136 |                 if self.runners[i] == 1:
  137 |                     next_base = i + bases
  138 |                     if next_base >= 3:
  139 |                         runs += 1
  140 |                     else:
  141 |                         new_runners[next_base] = 1
  142 |             self.runners = new_runners
  143 |         return runs
  144 | 
  145 |     def _add_out(self):
  146 |         self.outs += 1
  147 |         self.reset_at_bat()
  148 | 
  149 |     def _check_inning_state(self):
  150 |         if self.outs >= 3:
  151 |             self.outs = 0
  152 |             self.runners = [0, 0, 0]
  153 |             self.reset_at_bat()
  154 |             if self.is_top:
  155 |                 self.is_top = False
  156 |             else:
  157 |                 self.is_top = True
  158 |                 self.inning += 1
  159 |                 
  160 |                 if self.inning > self.max_innings:
  161 |                     self.game_over = True
  162 |                 elif self.inning == self.max_innings and not self.is_top and self.score_home > self.score_away:
  163 |                     self.game_over = True
````
