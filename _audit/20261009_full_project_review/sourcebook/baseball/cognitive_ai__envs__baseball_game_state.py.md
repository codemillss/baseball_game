# baseball/cognitive_ai/envs/baseball_game_state.py

원본: [cognitive_ai/envs/baseball_game_state.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/baseball_game_state.py)

SHA256: `878bfc289a518a6041ea93cecc10bebacb47d5b33aa674494b20712c20e33f49`

전체 72행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BaseballGameState` | ClassDef | 1 | 72 |
| `__init__` | FunctionDef | 2 | 10 |
| `handle_pitch` | FunctionDef | 12 | 25 |
| `handle_hit` | FunctionDef | 27 | 41 |
| `advance_runners` | FunctionDef | 43 | 50 |
| `reset_count` | FunctionDef | 52 | 54 |
| `add_runs` | FunctionDef | 56 | 58 |
| `change_inning` | FunctionDef | 60 | 68 |
| `get_scoreboard` | FunctionDef | 70 | 72 |

## 전체 원문

````text
    1 | class BaseballGameState:
    2 |     def __init__(self):
    3 |         self.inning = 1
    4 |         self.is_top = True
    5 |         self.outs = 0
    6 |         self.strikes = 0
    7 |         self.balls = 0
    8 |         self.score_away = 0
    9 |         self.score_home = 0
   10 |         self.bases = [False, False, False] # 1st, 2nd, 3rd
   11 | 
   12 |     def handle_pitch(self, outcome):
   13 |         if outcome == "STRIKE":
   14 |             self.strikes += 1
   15 |             if self.strikes == 3:
   16 |                 self.outs += 1
   17 |                 self.reset_count()
   18 |         elif outcome == "BALL":
   19 |             self.balls += 1
   20 |             if self.balls == 4:
   21 |                 self.advance_runners()
   22 |                 self.reset_count()
   23 |         
   24 |         if self.outs >= 3:
   25 |             self.change_inning()
   26 |             
   27 |     def handle_hit(self, outcome):
   28 |         self.reset_count()
   29 |         if outcome == "FOUL":
   30 |             if self.strikes < 2:
   31 |                 self.strikes += 1
   32 |         elif outcome == "HOME RUN":
   33 |             runs = sum(self.bases) + 1
   34 |             self.add_runs(runs)
   35 |             self.bases = [False, False, False]
   36 |         elif outcome == "FAIR":
   37 |             # For simplicity, assume a single for now
   38 |             if self.bases[2]: self.add_runs(1)
   39 |             self.bases[2] = self.bases[1]
   40 |             self.bases[1] = self.bases[0]
   41 |             self.bases[0] = True
   42 |             
   43 |     def advance_runners(self):
   44 |         if self.bases[0]:
   45 |             if self.bases[1]:
   46 |                 if self.bases[2]:
   47 |                     self.add_runs(1)
   48 |                 self.bases[2] = True
   49 |             self.bases[1] = True
   50 |         self.bases[0] = True
   51 | 
   52 |     def reset_count(self):
   53 |         self.strikes = 0
   54 |         self.balls = 0
   55 |         
   56 |     def add_runs(self, runs):
   57 |         if self.is_top: self.score_away += runs
   58 |         else: self.score_home += runs
   59 |         
   60 |     def change_inning(self):
   61 |         self.outs = 0
   62 |         self.reset_count()
   63 |         self.bases = [False, False, False]
   64 |         if self.is_top:
   65 |             self.is_top = False
   66 |         else:
   67 |             self.is_top = True
   68 |             self.inning += 1
   69 | 
   70 |     def get_scoreboard(self):
   71 |         half = "Top" if self.is_top else "Bot"
   72 |         return f"{half} {self.inning} | AWAY {self.score_away} - {self.score_home} HOME | O:{self.outs} S:{self.strikes} B:{self.balls} | Bases: {int(self.bases[0])}{int(self.bases[1])}{int(self.bases[2])}"
````
