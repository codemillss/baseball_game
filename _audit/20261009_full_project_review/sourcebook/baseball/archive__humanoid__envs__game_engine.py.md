# baseball/archive/humanoid/envs/game_engine.py

원본: [archive/humanoid/envs/game_engine.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/humanoid/envs/game_engine.py)

SHA256: `adb53cec803cf1c66f50b7eb8c5ce849019c6d0f76bccbdb741e41ee98b86c03`

전체 165행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BaseballGameEngine` | ClassDef | 4 | 165 |
| `__init__` | FunctionDef | 5 | 7 |
| `reset_game` | FunctionDef | 9 | 19 |
| `reset_at_bat` | FunctionDef | 21 | 23 |
| `get_context_vector` | FunctionDef | 25 | 37 |
| `process_pitch` | FunctionDef | 39 | 94 |
| `_resolve_hit` | FunctionDef | 96 | 120 |
| `_advance_runners` | FunctionDef | 122 | 143 |
| `_add_out` | FunctionDef | 145 | 147 |
| `_check_inning_state` | FunctionDef | 149 | 165 |

## 전체 원문

````text
    1 | import numpy as np
    2 | from typing import Dict, Any, Tuple
    3 | 
    4 | class BaseballGameEngine:
    5 |     def __init__(self, max_innings: int = 9):
    6 |         self.max_innings = max_innings
    7 |         self.reset_game()
    8 | 
    9 |     def reset_game(self):
   10 |         self.inning = 1
   11 |         self.is_top = True # True: 어웨이팀 공격, False: 홈팀 공격
   12 |         self.score_away = 0
   13 |         self.score_home = 0
   14 |         self.outs = 0
   15 |         self.strikes = 0
   16 |         self.balls = 0
   17 |         # 주자 상태: [1루, 2루, 3루]
   18 |         self.runners = [0, 0, 0]
   19 |         self.game_over = False
   20 | 
   21 |     def reset_at_bat(self):
   22 |         self.strikes = 0
   23 |         self.balls = 0
   24 | 
   25 |     def get_context_vector(self) -> np.ndarray:
   26 |         """
   27 |         강화학습 에이전트의 뇌(Context)에 들어갈 상태 벡터 (6D)
   28 |         [balls, strikes, outs, r1, r2, r3]
   29 |         """
   30 |         return np.array([
   31 |             self.balls / 3.0,
   32 |             self.strikes / 2.0,
   33 |             self.outs / 2.0,
   34 |             float(self.runners[0]),
   35 |             float(self.runners[1]),
   36 |             float(self.runners[2])
   37 |         ], dtype=np.float32)
   38 | 
   39 |     def process_pitch(self, 
   40 |                       swung: bool, 
   41 |                       contacted: bool, 
   42 |                       in_strike_zone: bool, 
   43 |                       exit_velocity_kmh: float = 0.0, 
   44 |                       distance_m: float = 0.0) -> Tuple[str, int]:
   45 |         """
   46 |         투구 결과를 처리하고 (이벤트 문자열, 발생한 득점) 반환
   47 |         """
   48 |         if self.game_over:
   49 |             return "Game Over", 0
   50 | 
   51 |         event = ""
   52 |         runs_scored = 0
   53 | 
   54 |         if contacted:
   55 |             # 타격 발생! 비거리와 속도로 휴리스틱 판정
   56 |             if distance_m < 2.0:
   57 |                 event = "Foul"
   58 |                 if self.strikes < 2:
   59 |                     self.strikes += 1
   60 |             else:
   61 |                 event, runs_scored = self._resolve_hit(exit_velocity_kmh, distance_m)
   62 |         else:
   63 |             if swung:
   64 |                 event = "Swinging Strike"
   65 |                 self.strikes += 1
   66 |             else:
   67 |                 if in_strike_zone:
   68 |                     event = "Called Strike"
   69 |                     self.strikes += 1
   70 |                 else:
   71 |                     event = "Ball"
   72 |                     self.balls += 1
   73 | 
   74 |         # 볼넷 처리
   75 |         if self.balls >= 4:
   76 |             event = "Walk"
   77 |             runs_scored = self._advance_runners(1, force=True)
   78 |             self.reset_at_bat()
   79 | 
   80 |         # 삼진 처리
   81 |         if self.strikes >= 3:
   82 |             event = "Strikeout"
   83 |             self._add_out()
   84 | 
   85 |         # 이닝/게임 종료 체크 로직
   86 |         self._check_inning_state()
   87 |         
   88 |         # 득점 적용
   89 |         if self.is_top:
   90 |             self.score_away += runs_scored
   91 |         else:
   92 |             self.score_home += runs_scored
   93 | 
   94 |         return event, runs_scored
   95 | 
   96 |     def _resolve_hit(self, ev: float, dist: float) -> Tuple[str, int]:
   97 |         """비거리와 타구 속도로 안타/아웃 판정 및 주자 진루 처리"""
   98 |         # 단순 휴리스틱: 100km/h 이상 & 30m 이상이면 안타, 100m 이상이면 홈런
   99 |         if ev < 80.0 or dist < 20.0:
  100 |             self._add_out()
  101 |             return "Ground Out / Pop Out", 0
  102 |         
  103 |         runs = 0
  104 |         if dist >= 100.0:
  105 |             # 홈런
  106 |             runs = self._advance_runners(4) + 1 # 타자 본인 포함
  107 |             self.reset_at_bat()
  108 |             return "Home Run", runs
  109 |         elif dist >= 60.0:
  110 |             # 2루타
  111 |             runs = self._advance_runners(2)
  112 |             self.runners[1] = 1 # 타자는 2루로
  113 |             self.reset_at_bat()
  114 |             return "Double", runs
  115 |         else:
  116 |             # 단타
  117 |             runs = self._advance_runners(1)
  118 |             self.runners[0] = 1 # 타자는 1루로
  119 |             self.reset_at_bat()
  120 |             return "Single", runs
  121 | 
  122 |     def _advance_runners(self, bases: int, force: bool = False) -> int:
  123 |         runs = 0
  124 |         if force: # 볼넷 밀어내기
  125 |             if self.runners[0] == 1:
  126 |                 if self.runners[1] == 1:
  127 |                     if self.runners[2] == 1:
  128 |                         runs += 1
  129 |                     self.runners[2] = 1
  130 |                 self.runners[1] = 1
  131 |             self.runners[0] = 1
  132 |         else:
  133 |             # 일반 타격 시 진루
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
  160 |                 # 정규 이닝 종료 확인
  161 |                 if self.inning > self.max_innings:
  162 |                     self.game_over = True
  163 |                 # 9회말에 홈팀이 이기고 있으면 바로 종료
  164 |                 elif self.inning == self.max_innings and not self.is_top and self.score_home > self.score_away:
  165 |                     self.game_over = True
````
