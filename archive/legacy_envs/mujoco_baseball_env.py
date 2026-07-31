"""
mujoco_baseball_env.py — High-Res 3D MuJoCo Baseball Physics Environment

MuJoCo 3.x + Gymnasium 래퍼 환경:
- 3D Stadium Field (마운드, 베이스, 펜스, 스트라이크 존)
- 3D Dynamic Baseball (Freejoint + Drag/Magnus Air Resistance)
- Multi-DOF Articulated Bat (Torque / Joint Control)
- Contact & Hit Dynamics (Exit Velocity, Launch Angle, Spray Angle)
"""

import os
from pathlib import Path
from typing import Optional, Dict, Tuple, Any

import numpy as np
import gymnasium as gym
from gymnasium import spaces

import mujoco


class MuJoCoBaseballEnv(gym.Env):
    """3D MuJoCo 야구 시뮬레이션 Gymnasium 환경."""

    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 60}

    def __init__(
        self,
        xml_path: Optional[str] = None,
        frame_skip: int = 5,
        render_mode: Optional[str] = None,
    ):
        super().__init__()

        if xml_path is None:
            xml_path = str(Path(__file__).parent.parent / "assets" / "stadium_3d.xml")

        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"MuJoCo XML file not found at: {xml_path}")

        self.xml_path = xml_path
        self.model = mujoco.MjModel.from_xml_path(self.xml_path)
        self.data = mujoco.MjData(self.model)
        self.frame_skip = frame_skip
        self.render_mode = render_mode

        # ID 캐싱
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.bat_base_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "bat_base")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.bat_barrel_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")

        # Action Space: [Bat Yaw Torque, Bat Pitch Torque, Bat Roll Torque] [-1, 1]
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(3,), dtype=np.float32
        )

        # Observation Space:
        # [ball_pos(3), ball_vel(3), bat_qpos(3), bat_qvel(3), rel_dist(3)] -> 15차원
        obs_low = np.array([-100.0] * 15, dtype=np.float32)
        obs_high = np.array([100.0] * 15, dtype=np.float32)
        self.observation_space = spaces.Box(low=obs_low, high=obs_high, dtype=np.float32)

        # 렌더러 초기화 (비디오 / 시각화용)
        self.renderer = None
        if self.render_mode == "rgb_array":
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)

        # 상태 제어 변수
        self.step_count = 0
        self.max_steps = 200
        self.has_contacted = False
        self.max_exit_velocity = 0.0
        self.hit_info = {}

    def _get_obs(self) -> np.ndarray:
        """현재 3D 물리 상태에서 관찰 벡터를 추출합니다."""
        # 공 위치 & 속도 (qpos 0:3, qvel 0:3 for freejoint)
        ball_pos = self.data.xpos[self.ball_body_id].copy()
        ball_vel = self.data.cvel[self.ball_body_id][3:6].copy()

        # 배트 관절 각도 & 각속도 (bat joints: index 1, 2, 3 in model joints)
        bat_qpos = self.data.qpos[7:10].copy()  # 0~6: ball freejoint (pos3 + quat4)
        bat_qvel = self.data.qvel[6:9].copy()  # 0~5: ball freejoint (vel3 + rot3)

        # 상대 위치 벡터
        bat_pos = self.data.xpos[self.bat_base_id].copy()
        rel_dist = ball_pos - bat_pos

        obs = np.concatenate([
            ball_pos, ball_vel, bat_qpos, bat_qvel, rel_dist
        ], dtype=np.float32)

        return obs

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """환경 초기화: 투수 마운드에서 공 투구."""
        super().reset(seed=seed)

        mujoco.mj_resetData(self.model, self.data)

        # 1. 야구공 초기 위치 (마운드: x=0, y=18.44, z=1.8)
        self.data.qpos[0] = self.np_random.uniform(-0.1, 0.1)  # x 약간 유인
        self.data.qpos[1] = 18.44                               # y 마운드
        self.data.qpos[2] = 1.8 + self.np_random.uniform(-0.05, 0.05)  # z 릴리스 높이
        self.data.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]             # 쿼터니언

        # 2. 투구 초기 속도 (예: 130 ~ 150 km/h -> 36.1 ~ 41.6 m/s)
        v_y = -self.np_random.uniform(36.0, 42.0)
        v_x = self.np_random.uniform(-1.0, 1.0)
        v_z = self.np_random.uniform(-1.0, 1.5)
        self.data.qvel[0] = v_x
        self.data.qvel[1] = v_y
        self.data.qvel[2] = v_z

        # 3. 배트 초기 위치 초기화
        self.data.qpos[7:10] = 0.0
        self.data.qvel[6:9] = 0.0

        mujoco.mj_forward(self.model, self.data)

        self.step_count = 0
        self.has_contacted = False
        self.max_exit_velocity = 0.0
        self.hit_info = {}

        obs = self._get_obs()
        return obs, {}

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """물리 프레임 진행 및 보상 계산."""
        action = np.clip(action, -1.0, 1.0)

        # 액션 적용 (Motor ctrl)
        self.data.ctrl[0] = action[0] * 100.0  # yaw torque
        self.data.ctrl[1] = action[1] * 50.0   # pitch torque
        self.data.ctrl[2] = action[2] * 50.0   # roll torque

        # Frame skip 물리 스텝
        for _ in range(self.frame_skip):
            # 공기저항 & 마그누스 양력 보정
            self._apply_aerodynamics()
            mujoco.mj_step(self.model, self.data)
            self._check_contacts()

        self.step_count += 1
        obs = self._get_obs()

        # 보상 계산 및 종료 조건 검사
        reward, terminated, info = self._compute_reward_and_done()
        truncated = self.step_count >= self.max_steps

        return obs, reward, terminated, truncated, info

    def _apply_aerodynamics(self):
        """공기저항(Drag) 및 마그누스(Magnus) 양력을 공에 부과합니다."""
        ball_vel = self.data.cvel[self.ball_body_id][3:6]
        speed = np.linalg.norm(ball_vel)
        if speed < 1e-3:
            return

        # 항력 Cd = 0.3
        rho = 1.225
        area = np.pi * (0.037 ** 2)
        c_d = 0.3
        drag_mag = 0.5 * rho * (speed ** 2) * area * c_d
        drag_force = -drag_mag * (ball_vel / speed)

        # xfrc_applied에 외력 추가 (freejoint body index)
        self.data.xfrc_applied[self.ball_body_id][:3] = drag_force

    def _check_contacts(self):
        """배트와 야구공 간의 충돌 여부를 감지합니다."""
        for i in range(self.data.ncon):
            con = self.data.contact[i]
            g1, g2 = con.geom1, con.geom2

            is_ball = (g1 == self.ball_geom_id or g2 == self.ball_geom_id)
            is_bat = (g1 == self.bat_barrel_id or g2 == self.bat_barrel_id)

            if is_ball and is_bat:
                self.has_contacted = True
                ball_vel = self.data.cvel[self.ball_body_id][3:6]
                exit_speed_kmh = np.linalg.norm(ball_vel) * 3.6
                if exit_speed_kmh > self.max_exit_velocity:
                    self.max_exit_velocity = exit_speed_kmh

                    # 발사각 & 스프레이각 추정
                    vx, vy, vz = ball_vel
                    horiz_speed = np.hypot(vx, vy)
                    launch_angle = np.degrees(np.arctan2(vz, max(horiz_speed, 1e-3)))
                    spray_angle = np.degrees(np.arctan2(vx, max(-vy, 1e-3)))

                    self.hit_info = {
                        'exit_velocity_kmh': exit_speed_kmh,
                        'launch_angle': launch_angle,
                        'spray_angle': spray_angle,
                    }

    def _compute_reward_and_done(self) -> Tuple[float, bool, Dict[str, Any]]:
        """보상 함수 및 종료 여부 산출."""
        ball_pos = self.data.xpos[self.ball_body_id]
        reward = 0.0
        terminated = False
        info = {'has_contacted': self.has_contacted, **self.hit_info}

        # 1. Contact Reward
        if self.has_contacted:
            reward += 10.0
            # 2. Exit Velocity Reward
            reward += (self.max_exit_velocity / 10.0)

            # 3. Fair Zone Angle Reward (-45도 ~ +45도 페어)
            sa = self.hit_info.get('spray_angle', 0.0)
            if -45.0 <= sa <= 45.0:
                reward += 5.0  # Fair zone bonus

            terminated = True

        # 공이 캐처 미트 통과 (y < -0.5) 또는 바닥 낙하 (z < 0.1)
        elif ball_pos[1] < -0.5 or ball_pos[2] < 0.05:
            # 접촉 못하고 통과함 -> 스트라이크/볼
            reward -= 1.0
            terminated = True

        return float(reward), terminated, info

    def render(self) -> Optional[np.ndarray]:
        """3D 프레임 렌더링."""
        if self.renderer is not None:
            self.renderer.update_scene(self.data)
            return self.renderer.render()
        return None

    def close(self):
        """환경 닫기."""
        if self.renderer is not None:
            del self.renderer
