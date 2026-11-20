# baseball/cognitive_ai/evaluation/simulate_9_innings.py

원본: [cognitive_ai/evaluation/simulate_9_innings.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/simulate_9_innings.py)

SHA256: `8b58c45e5b55667061151a4b88113963c32b8222941d9ae572b6e796aae6ed94`

전체 37행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `simulate_game` | FunctionDef | 8 | 34 |

## 전체 원문

````text
    1 | import sys
    2 | import os
    3 | sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    4 | import time
    5 | from cognitive_ai.envs.baseball_game_state import BaseballGameState
    6 | import random
    7 | 
    8 | def simulate_game():
    9 |     game = BaseballGameState()
   10 |     print("=======================================================")
   11 |     print("🏟️  FULL 9-INNING BASEBALL SIMULATION START")
   12 |     print("=======================================================")
   13 |     
   14 |     while game.inning <= 9:
   15 |         # Simulate AI Umpire outcomes for speed
   16 |         # In the full system, this is fed by the MuJoCo + PPO environment
   17 |         r = random.random()
   18 |         if r < 0.1: outcome = "HOME RUN"
   19 |         elif r < 0.3: outcome = "FAIR"
   20 |         elif r < 0.4: outcome = "FOUL"
   21 |         elif r < 0.7: outcome = "STRIKE"
   22 |         else: outcome = "BALL"
   23 |         
   24 |         if outcome in ["STRIKE", "BALL"]:
   25 |             game.handle_pitch(outcome)
   26 |         else:
   27 |             game.handle_hit(outcome)
   28 |             
   29 |         print(f"Outcome: {outcome.ljust(10)} | {game.get_scoreboard()}")
   30 |         time.sleep(0.01) # fast simulation
   31 |         
   32 |     print("=======================================================")
   33 |     print(f"🏆 FINAL SCORE: AWAY {game.score_away} - {game.score_home} HOME")
   34 |     print("=======================================================")
   35 | 
   36 | if __name__ == "__main__":
   37 |     simulate_game()
````
