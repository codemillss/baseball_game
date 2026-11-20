# baseball/archive/expert/trajectory_solver.py

원본: [archive/expert/trajectory_solver.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/expert/trajectory_solver.py)

SHA256: `92bd94de02b919d315d386ae23b811deee9df0df7ed0711125a0aadb18634af8`

전체 101행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `AnalyticalTrajectorySolver` | ClassDef | 13 | 101 |
| `__init__` | FunctionDef | 16 | 18 |
| `solve_pitch_impact` | FunctionDef | 20 | 58 |
| `solve_inverse_kinematics_swing` | FunctionDef | 60 | 101 |

## 전체 원문

````text
    1 | """
    2 | trajectory_solver.py — Analytical Physics Solver & Inverse Kinematics (IK) Engine
    3 | 
    4 | 투구 3D 포구/타격점 위치와 도착 시간(t_impact)을 역산하고,
    5 | 공을 배트 바렐(Sweet Spot) 중심에 내야/외야 방향으로 맞추기 위한
    6 | 최적의 스윙 타이밍 및 토크 시퀀스(Inverse Kinematics)를 계산합니다.
    7 | """
    8 | 
    9 | from typing import Tuple, Dict, Any
   10 | import numpy as np
   11 | 
   12 | 
   13 | class AnalyticalTrajectorySolver:
   14 |     """물리 수식 기반 포구 및 타격 타이밍 역산 솔버."""
   15 | 
   16 |     def __init__(self, g: float = 9.81, air_drag_coef: float = 0.0015):
   17 |         self.g = g
   18 |         self.c_d = air_drag_coef
   19 | 
   20 |     def solve_pitch_impact(
   21 |         self,
   22 |         init_pos: np.ndarray,
   23 |         init_vel: np.ndarray,
   24 |         target_y: float = 0.0,
   25 |     ) -> Tuple[float, np.ndarray, np.ndarray]:
   26 |         """투구 궤적 수식을 역산하여 홈플레이트(y=target_y) 도달 시간 t 및 3D 위치/속도를 추정합니다.
   27 | 
   28 |         Args:
   29 |             init_pos: (3,) [x0, y0, z0]
   30 |             init_vel: (3,) [vx0, vy0, vz0]
   31 |             target_y: 홈플레이트 y 위치 (기본 0.0)
   32 | 
   33 |         Returns:
   34 |             (t_impact, impact_pos, impact_vel)
   35 |         """
   36 |         x0, y0, z0 = init_pos
   37 |         vx0, vy0, vz0 = init_vel
   38 | 
   39 |         # y(t) = y0 + vy0 * t - 0.5 * c_d * vy0^2 * t -> 근사 1차 도달 시간
   40 |         # vy0 < 0 (마운드 -> 포수)
   41 |         dist_y = y0 - target_y
   42 |         speed_y = abs(vy0)
   43 | 
   44 |         t_impact = dist_y / max(speed_y, 1.0)
   45 | 
   46 |         # 공기 저항 감쇄 반영 위치
   47 |         x_impact = x0 + vx0 * t_impact * np.exp(-self.c_d * t_impact)
   48 |         y_impact = target_y
   49 |         z_impact = z0 + vz0 * t_impact - 0.5 * self.g * (t_impact ** 2)
   50 | 
   51 |         impact_pos = np.array([x_impact, y_impact, z_impact], dtype=np.float32)
   52 | 
   53 |         vx_imp = vx0 * np.exp(-self.c_d * t_impact)
   54 |         vy_imp = vy0
   55 |         vz_imp = vz0 - self.g * t_impact
   56 |         impact_vel = np.array([vx_imp, vy_imp, vz_imp], dtype=np.float32)
   57 | 
   58 |         return float(t_impact), impact_pos, impact_vel
   59 | 
   60 |     def solve_inverse_kinematics_swing(
   61 |         self,
   62 |         current_obs: np.ndarray,
   63 |         impact_pos: np.ndarray,
   64 |         time_to_impact: float,
   65 |     ) -> np.ndarray:
   66 |         """역운동학(IK) 솔버: 현재 관찰과 타격 지점을 기반으로 3D 배트 관절 토크 산출.
   67 | 
   68 |         Args:
   69 |             current_obs: (15,) 환경 관찰 벡터
   70 |             impact_pos: (3,) 예상 3D 타격 위치
   71 |             time_to_impact: 타격까지 남은 시간 (초)
   72 | 
   73 |         Returns:
   74 |             (3,) [yaw_torque, pitch_torque, roll_torque]
   75 |         """
   76 |         ball_pos = current_obs[0:3]
   77 |         bat_qpos = current_obs[6:9]
   78 | 
   79 |         # 스윙 타이밍 존 (타격 0.12초 전 스윙 트리거 시작)
   80 |         if time_to_impact < 0.18:
   81 |             # 공의 높이(z)와 좌우(x)에 맞춘 관절 목표 각도 산출
   82 |             target_yaw = np.radians(85.0)  # 힘차게 내두르는 스윙 궤적
   83 |             target_pitch = np.clip(np.radians((impact_pos[2] - 0.75) * 60.0), -0.5, 0.5)
   84 |             target_roll = np.clip(np.radians((impact_pos[0] - 0.0) * 40.0), -0.5, 0.5)
   85 | 
   86 |             # PD Control (Proportional-Derivative Controller)
   87 |             k_p = 4.0
   88 |             k_d = 0.5
   89 | 
   90 |             err_yaw = target_yaw - bat_qpos[0]
   91 |             err_pitch = target_pitch - bat_qpos[1]
   92 |             err_roll = target_roll - bat_qpos[2]
   93 | 
   94 |             yaw_torque = np.clip(k_p * err_yaw, -1.0, 1.0)
   95 |             pitch_torque = np.clip(k_p * err_pitch, -1.0, 1.0)
   96 |             roll_torque = np.clip(k_p * err_roll, -1.0, 1.0)
   97 | 
   98 |             return np.array([yaw_torque, pitch_torque, roll_torque], dtype=np.float32)
   99 | 
  100 |         # 대기 상태
  101 |         return np.array([0.0, 0.0, 0.0], dtype=np.float32)
````
