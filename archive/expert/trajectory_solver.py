"""
trajectory_solver.py — Analytical Physics Solver & Inverse Kinematics (IK) Engine

투구 3D 포구/타격점 위치와 도착 시간(t_impact)을 역산하고,
공을 배트 바렐(Sweet Spot) 중심에 내야/외야 방향으로 맞추기 위한
최적의 스윙 타이밍 및 토크 시퀀스(Inverse Kinematics)를 계산합니다.
"""

from typing import Tuple, Dict, Any
import numpy as np


class AnalyticalTrajectorySolver:
    """물리 수식 기반 포구 및 타격 타이밍 역산 솔버."""

    def __init__(self, g: float = 9.81, air_drag_coef: float = 0.0015):
        self.g = g
        self.c_d = air_drag_coef

    def solve_pitch_impact(
        self,
        init_pos: np.ndarray,
        init_vel: np.ndarray,
        target_y: float = 0.0,
    ) -> Tuple[float, np.ndarray, np.ndarray]:
        """투구 궤적 수식을 역산하여 홈플레이트(y=target_y) 도달 시간 t 및 3D 위치/속도를 추정합니다.

        Args:
            init_pos: (3,) [x0, y0, z0]
            init_vel: (3,) [vx0, vy0, vz0]
            target_y: 홈플레이트 y 위치 (기본 0.0)

        Returns:
            (t_impact, impact_pos, impact_vel)
        """
        x0, y0, z0 = init_pos
        vx0, vy0, vz0 = init_vel

        # y(t) = y0 + vy0 * t - 0.5 * c_d * vy0^2 * t -> 근사 1차 도달 시간
        # vy0 < 0 (마운드 -> 포수)
        dist_y = y0 - target_y
        speed_y = abs(vy0)

        t_impact = dist_y / max(speed_y, 1.0)

        # 공기 저항 감쇄 반영 위치
        x_impact = x0 + vx0 * t_impact * np.exp(-self.c_d * t_impact)
        y_impact = target_y
        z_impact = z0 + vz0 * t_impact - 0.5 * self.g * (t_impact ** 2)

        impact_pos = np.array([x_impact, y_impact, z_impact], dtype=np.float32)

        vx_imp = vx0 * np.exp(-self.c_d * t_impact)
        vy_imp = vy0
        vz_imp = vz0 - self.g * t_impact
        impact_vel = np.array([vx_imp, vy_imp, vz_imp], dtype=np.float32)

        return float(t_impact), impact_pos, impact_vel

    def solve_inverse_kinematics_swing(
        self,
        current_obs: np.ndarray,
        impact_pos: np.ndarray,
        time_to_impact: float,
    ) -> np.ndarray:
        """역운동학(IK) 솔버: 현재 관찰과 타격 지점을 기반으로 3D 배트 관절 토크 산출.

        Args:
            current_obs: (15,) 환경 관찰 벡터
            impact_pos: (3,) 예상 3D 타격 위치
            time_to_impact: 타격까지 남은 시간 (초)

        Returns:
            (3,) [yaw_torque, pitch_torque, roll_torque]
        """
        ball_pos = current_obs[0:3]
        bat_qpos = current_obs[6:9]

        # 스윙 타이밍 존 (타격 0.12초 전 스윙 트리거 시작)
        if time_to_impact < 0.18:
            # 공의 높이(z)와 좌우(x)에 맞춘 관절 목표 각도 산출
            target_yaw = np.radians(85.0)  # 힘차게 내두르는 스윙 궤적
            target_pitch = np.clip(np.radians((impact_pos[2] - 0.75) * 60.0), -0.5, 0.5)
            target_roll = np.clip(np.radians((impact_pos[0] - 0.0) * 40.0), -0.5, 0.5)

            # PD Control (Proportional-Derivative Controller)
            k_p = 4.0
            k_d = 0.5

            err_yaw = target_yaw - bat_qpos[0]
            err_pitch = target_pitch - bat_qpos[1]
            err_roll = target_roll - bat_qpos[2]

            yaw_torque = np.clip(k_p * err_yaw, -1.0, 1.0)
            pitch_torque = np.clip(k_p * err_pitch, -1.0, 1.0)
            roll_torque = np.clip(k_p * err_roll, -1.0, 1.0)

            return np.array([yaw_torque, pitch_torque, roll_torque], dtype=np.float32)

        # 대기 상태
        return np.array([0.0, 0.0, 0.0], dtype=np.float32)
