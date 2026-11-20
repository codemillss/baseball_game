# baseball/archive/legacy_scripts/simulator/game_engine.py

원본: [archive/legacy_scripts/simulator/game_engine.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_scripts/simulator/game_engine.py)

SHA256: `2038bbcc52425b8a1402788bd8ae4c64b79dc2b560ad6be64e22acbe73621325`

전체 138행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `Baseball9InningGameEngine` | ClassDef | 11 | 134 |
| `__init__` | FunctionDef | 14 | 26 |
| `play_full_game` | FunctionDef | 28 | 41 |
| `_play_half_inning` | FunctionDef | 43 | 107 |
| `_print_box_score` | FunctionDef | 109 | 124 |
| `_get_game_summary` | FunctionDef | 126 | 134 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | import numpy as np
    4 | import torch
    5 | import mujoco
    6 | 
    7 | sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    8 | from envs.mujoco_baseball_env import MuJoCoBaseballEnv
    9 | from expert.trajectory_solver import AnalyticalTrajectorySolver
   10 | 
   11 | class Baseball9InningGameEngine:
   12 |     """9이닝 완전 자동 야구 경기 엔진 및 박스스코어 생성기."""
   13 | 
   14 |     def __init__(self):
   15 |         self.env = MuJoCoBaseballEnv()
   16 |         self.solver = AnalyticalTrajectorySolver()
   17 | 
   18 |         # Box Score Stats
   19 |         self.away_scores = [0] * 9
   20 |         self.home_scores = [0] * 9
   21 |         self.away_hits = 0
   22 |         self.home_hits = 0
   23 |         self.away_hrs = 0
   24 |         self.home_hrs = 0
   25 |         self.away_errors = 0
   26 |         self.home_errors = 0
   27 | 
   28 |     def play_full_game(self) -> dict:
   29 |         """9이닝 경기 전체를 자동 시뮬레이션합니다."""
   30 |         print("==================================================")
   31 |         print(" 🏟️ 9이닝 완전 자동 프로야구 경기 시뮬레이션 시작")
   32 |         print("==================================================")
   33 | 
   34 |         for inning in range(9):
   35 |             # 초 (Top Inning - Away Team Batting)
   36 |             self._play_half_inning(inning, is_home=False)
   37 |             # 말 (Bottom Inning - Home Team Batting)
   38 |             self._play_half_inning(inning, is_home=True)
   39 | 
   40 |         self._print_box_score()
   41 |         return self._get_game_summary()
   42 | 
   43 |     def _play_half_inning(self, inning_idx: int, is_home: bool):
   44 |         outs = 0
   45 |         balls = 0
   46 |         strikes = 0
   47 |         bases = [False, False, False] # 1st, 2nd, 3rd Base
   48 | 
   49 |         half_str = "말 (Home)" if is_home else "초 (Away)"
   50 |         print(f"\n📢 [{inning_idx+1}회{half_str}] 이닝 시작...")
   51 | 
   52 |         while outs < 3:
   53 |             obs, info = self.env.reset()
   54 |             ball_pos = obs[0:3]
   55 |             ball_vel = obs[3:6]
   56 |             t_impact, impact_pos, _ = self.solver.solve_pitch_impact(ball_pos, ball_vel)
   57 | 
   58 |             done = False
   59 |             ep_steps = 0
   60 |             has_hit = False
   61 | 
   62 |             while not done:
   63 |                 time_remaining = t_impact - (ep_steps * 0.002 * self.env.frame_skip)
   64 |                 action = self.solver.solve_inverse_kinematics_swing(obs, impact_pos, time_remaining)
   65 | 
   66 |                 obs, reward, terminated, truncated, step_info = self.env.step(action)
   67 |                 done = terminated or truncated
   68 |                 ep_steps += 1
   69 | 
   70 |                 if step_info.get('has_contacted', False) and not has_hit:
   71 |                     has_hit = True
   72 |                     exit_velo = step_info.get('exit_velocity_kmh', 0.0)
   73 |                     launch_ang = step_info.get('launch_angle', 0.0)
   74 | 
   75 |                     # Determine Play Outcome
   76 |                     if exit_velo >= 140.0 and 20.0 <= launch_ang <= 40.0:
   77 |                         print(f"   🚀 HOME RUN!! (Exit Velo: {exit_velo:.1f} km/h, Launch Angle: {launch_ang:.1f}°)")
   78 |                         runs = 1 + sum(bases)
   79 |                         if is_home:
   80 |                             self.home_scores[inning_idx] += runs
   81 |                             self.home_hits += 1
   82 |                             self.home_hrs += 1
   83 |                         else:
   84 |                             self.away_scores[inning_idx] += runs
   85 |                             self.away_hits += 1
   86 |                             self.away_hrs += 1
   87 |                         bases = [False, False, False]
   88 |                     elif exit_velo >= 115.0:
   89 |                         print(f"   ⚡ 안타 (Hit)! (Exit Velo: {exit_velo:.1f} km/h)")
   90 |                         if is_home:
   91 |                             self.home_hits += 1
   92 |                         else:
   93 |                             self.away_hits += 1
   94 |                         # Base running logic
   95 |                         if bases[2]:
   96 |                             if is_home: self.home_scores[inning_idx] += 1
   97 |                             else: self.away_scores[inning_idx] += 1
   98 |                         bases = [True, bases[0], bases[1]]
   99 |                     else:
  100 |                         print(f"   🟤 아웃 (Out - Grounder/Fly)")
  101 |                         outs += 1
  102 | 
  103 |             if not has_hit:
  104 |                 print("   ⚾ 삼진/아웃 (Strikeout/Out)")
  105 |                 outs += 1
  106 | 
  107 |         print(f" 🔚 [{inning_idx+1}회{half_str}] 이닝 종료 (3아웃)")
  108 | 
  109 |     def _print_box_score(self):
  110 |         away_total_r = sum(self.away_scores)
  111 |         home_total_r = sum(self.home_scores)
  112 | 
  113 |         print("\n=========================================================================")
  114 |         print(" 📊 9이닝 최종 경기 박스스코어 (BOX SCORE)")
  115 |         print("=========================================================================")
  116 |         print("TEAM   | 1  2  3  4  5  6  7  8  9 |  R   H   E  HR")
  117 |         print("-------+---------------------------+----------------")
  118 |         away_str = " ".join([f"{s:2d}" for s in self.away_scores])
  119 |         home_str = " ".join([f"{s:2d}" for s in self.home_scores])
  120 |         print(f"AWAY   | {away_str} | {away_total_r:2d}  {self.away_hits:2d}  {self.away_errors:2d}  {self.away_hrs:2d}")
  121 |         print(f"HOME   | {home_str} | {home_total_r:2d}  {self.home_hits:2d}  {self.home_errors:2d}  {self.home_hrs:2d}")
  122 |         print("=========================================================================")
  123 |         winner = "HOME TEAM WIN! 🎉" if home_total_r >= away_total_r else "AWAY TEAM WIN! 🎉"
  124 |         print(f" 🏆 승리 팀: {winner}\n")
  125 | 
  126 |     def _get_game_summary(self) -> dict:
  127 |         return {
  128 |             "away_runs": sum(self.away_scores),
  129 |             "home_runs": sum(self.home_scores),
  130 |             "away_hits": self.away_hits,
  131 |             "home_hits": self.home_hits,
  132 |             "away_hrs": self.away_hrs,
  133 |             "home_hrs": self.home_hrs,
  134 |         }
  135 | 
  136 | if __name__ == "__main__":
  137 |     engine = Baseball9InningGameEngine()
  138 |     engine.play_full_game()
````
