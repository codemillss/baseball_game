# baseball/cognitive_ai/envs/baseball_rules.py

원본: [cognitive_ai/envs/baseball_rules.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/baseball_rules.py)

SHA256: `153121bdec350562f28f889e9ca0e405467d38996f96453754764b371903eb16`

전체 59행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BaseballUmpire` | ClassDef | 3 | 59 |
| `__init__` | FunctionDef | 4 | 11 |
| `is_in_strike_zone` | FunctionDef | 13 | 18 |
| `check_pitch_outcome` | FunctionDef | 20 | 28 |
| `check_hit_outcome` | FunctionDef | 30 | 59 |

## 전체 원문

````text
    1 | import numpy as np
    2 | 
    3 | class BaseballUmpire:
    4 |     def __init__(self):
    5 |         # Strike Zone limits based on h1_baseball_match.xml
    6 |         self.sz_x_min = -0.215
    7 |         self.sz_x_max = 0.215
    8 |         self.sz_y_min = -0.215
    9 |         self.sz_y_max = 0.215
   10 |         self.sz_z_min = 0.5
   11 |         self.sz_z_max = 1.1
   12 | 
   13 |     def is_in_strike_zone(self, ball_pos):
   14 |         """ Check if a single point is inside the strike zone box """
   15 |         x, y, z = ball_pos
   16 |         return (self.sz_x_min <= x <= self.sz_x_max and 
   17 |                 self.sz_y_min <= y <= self.sz_y_max and 
   18 |                 self.sz_z_min <= z <= self.sz_z_max)
   19 | 
   20 |     def check_pitch_outcome(self, ball_trajectory):
   21 |         """
   22 |         Given a list of ball positions (x, y, z) over time,
   23 |         determine if it passed through the strike zone.
   24 |         """
   25 |         for pos in ball_trajectory:
   26 |             if self.is_in_strike_zone(pos):
   27 |                 return "STRIKE"
   28 |         return "BALL"
   29 | 
   30 |     def check_hit_outcome(self, land_pos):
   31 |         """
   32 |         Given the (x, y, z) position where the ball landed,
   33 |         determine FOUL, FAIR, or HOME RUN.
   34 |         Assuming foul lines are at y = |x|.
   35 |         """
   36 |         x, y, z = land_pos
   37 |         
   38 |         # If it lands behind home plate
   39 |         if y < 0:
   40 |             return "FOUL"
   41 |             
   42 |         # Distance from home
   43 |         dist = np.sqrt(x**2 + y**2)
   44 |         
   45 |         # Check Foul lines (y = |x|)
   46 |         # The angle from home plate. center field is x=0, y>0 (angle 90).
   47 |         # 1st base is x>0, y=x (angle 45).
   48 |         # 3rd base is x<0, y=-x (angle 135).
   49 |         # FAIR territory is between 45 and 135 degrees.
   50 |         # This is exactly y >= |x|.
   51 |         
   52 |         is_fair = y >= abs(x)
   53 |         
   54 |         if is_fair:
   55 |             if dist > 120.0: # 120 meters for a home run
   56 |                 return "HOME RUN"
   57 |             return "FAIR"
   58 |         else:
   59 |             return "FOUL"
````
