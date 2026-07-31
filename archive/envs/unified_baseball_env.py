"""
unified_baseball_env.py — Phase 2.5: 능동 시야(Active Vision) 및 주변시 흐림 효과

특징:
  1. Action Space: 9-DOF (어깨3 + 팔꿈치1 + 손목3 + 목2)
  2. Proprioception: 18D (qpos 9 + qvel 9)
  3. Vision: 중심시(±60도), 주변시(±60~100도, 노이즈 추가/속도 차단), 사각지대(±100도 밖)
  4. 커리큘럼 Head-Lock: 초기 학습 시 목 관절을 강제로 공 궤적에 맞춤
"""

import os
import math
from pathlib import Path
from typing import Dict, Tuple, Any, Optional
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import mujoco

from envs.game_engine import BaseballGameEngine


class UnifiedBaseballEnv(gym.Env):
    """Phase 2.5: 9-DOF 능동 시야 및 주변시가 적용된 야구 시뮬레이션."""

    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 60}

    CURRICULUM = {
        1: {
            "name": "Stage 2.5a: Head-Lock & Center Vision",
            "release_distance": 5.0,
            "speed_range": (25.0, 30.0),
            "target_x_range": (-0.05, 0.05),
            "target_z_range": (0.75, 0.85),
            "pitch_types": ["fastball"],
            "contact_rate_to_promote": 0.40,
            "use_distance_shaping": True,
            "randomize_context": False,
            "head_lock": True,  # 시선 강제 고정
        },
        2: {
            "name": "Stage 2.5b: Free Gaze & Risk",
            "release_distance": 12.0,
            "speed_range": (30.0, 38.0),
            "target_x_range": (-0.15, 0.15),
            "target_z_range": (0.55, 1.05),
            "pitch_types": ["fastball"],
            "contact_rate_to_promote": 0.25,
            "use_distance_shaping": True,
            "randomize_context": True,
            "head_lock": False, # 시선 자유 제어 (스스로 공 쫓기)
        },
        3: {
            "name": "Stage 2.5c: Full Multi-Agent",
            "release_distance": 18.44,
            "speed_range": (35.0, 43.0),
            "target_x_range": (-0.30, 0.30),
            "target_z_range": (0.45, 1.10),
            "pitch_types": ["fastball"],
            "contact_rate_to_promote": 0.15,
            "use_distance_shaping": False,
            "randomize_context": True,
            "head_lock": False,
        },
    }

    PITCH_PARAMS = {
        "fastball":  {"spin_rpm": 2200, "spin_axis": np.array([0, 1, 0]),   "speed_mod": 1.0},
    }

    def __init__(
        self,
        xml_path: Optional[str] = None,
        curriculum_stage: int = 1,
        frame_skip: int = 4,
        render_mode: Optional[str] = None,
        max_steps_per_pitch: int = 300,
    ):
        super().__init__()

        if xml_path is None:
            xml_path = str(Path(__file__).parent.parent / "assets" / "stadium_3d.xml")

        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        self.frame_skip = frame_skip
        self.render_mode = render_mode
        self.max_steps = max_steps_per_pitch

        self.curriculum_stage = curriculum_stage
        self.stage_config = self.CURRICULUM[curriculum_stage]

        # ── MuJoCo ID 캐싱 ──
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "bat")
        self.cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "batter_cam")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.bat_barrel_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.bat_taper_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_taper")
        
        self.ball_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_qpos_adr = self.model.jnt_qposadr[self.ball_joint_id]
        self.ball_qvel_adr = self.model.jnt_dofadr[self.ball_joint_id]

        # ── Spaces (Dict 멀티모달, 9-DOF Action) ──
        # 팔 7개 + 목 2개 = 9개
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(9,), dtype=np.float32)

        self.observation_space = spaces.Dict({
            # [azimuth(rad), elevation(rad), distance(m), rel_velocity(m/s)]
            "vision": spaces.Box(low=-50.0, high=50.0, shape=(4,), dtype=np.float32),
            # 9-DOF [qpos, qvel] = 18D
            "proprioception": spaces.Box(low=-200.0, high=200.0, shape=(18,), dtype=np.float32),
            # [balls(0-3), strikes(0-2), outs(0-2), r1(0-1), r2(0-1), r3(0-1)]
            "context": spaces.Box(low=0.0, high=4.0, shape=(6,), dtype=np.float32),
        })

        self.renderer = None
        if self.render_mode == "rgb_array":
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)

        self.game_engine = BaseballGameEngine()

        self.step_count = 0
        self.has_contacted = False
        self.contact_info = {}
        self.min_dist_to_ball = float("inf")

        self.episode_contacts = 0
        self.episode_total = 0

    def set_curriculum_stage(self, stage: int):
        self.curriculum_stage = min(stage, max(self.CURRICULUM.keys()))
        self.stage_config = self.CURRICULUM[self.curriculum_stage]

    def get_curriculum_stage(self) -> int:
        return self.curriculum_stage

    # ──────────────────────────────────────────────────────────
    #  중심시(Foveal) vs 주변시(Peripheral Blur) 계산 로직
    # ──────────────────────────────────────────────────────────
    def _compute_egocentric_vision(self) -> np.ndarray:
        ball_pos = self.data.xpos[self.ball_body_id]
        ball_vel = self.data.cvel[self.ball_body_id][3:6]
        
        cam_pos = self.data.cam_xpos[self.cam_id]
        cam_mat = self.data.cam_xmat[self.cam_id].reshape(3, 3)

        # 카메라 로컬 좌표계로 공 위치 변환 (1인칭 시점)
        rel_pos = ball_pos - cam_pos
        local_pos = cam_mat.T @ rel_pos

        x, y, z = local_pos
        distance = np.linalg.norm(local_pos)
        
        azimuth = math.atan2(x, -z)
        elevation = math.asin(y / max(distance, 1e-5))
        rel_vel = np.linalg.norm(ball_vel)

        azimuth_deg = math.degrees(abs(azimuth))

        if distance > 25.0:
            return np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)

        # 1. 중심시 (정면 ±60도 이내) - 맑고 정확한 시야
        if azimuth_deg <= 60.0:
            return np.array([azimuth, elevation, distance, rel_vel], dtype=np.float32)
        
        # 2. 주변시 (±60도 ~ ±100도) - 흐림(Blur) 및 노이즈 적용
        elif 60.0 < azimuth_deg <= 100.0:
            noise_az = self.np_random.normal(0, 0.1) # 방위각 노이즈 추가 (약 5도)
            noise_el = self.np_random.normal(0, 0.1) # 앙각 노이즈 추가
            noise_dist = self.np_random.normal(0, 1.0) # 거리 노이즈 크게 추가
            
            # 주변시는 속도 파악이 어려움 (0으로 차단)
            return np.array([
                azimuth + noise_az, 
                elevation + noise_el, 
                max(0.1, distance + noise_dist), 
                0.0
            ], dtype=np.float32)
        
        # 3. 사각지대 (±100도 초과) - 완전한 시야 상실
        else:
            return np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)

    def _get_obs(self) -> Dict[str, np.ndarray]:
        vision = self._compute_egocentric_vision()
        # 팔(7) + 목(2) = 총 9-DOF 의 qpos/qvel
        prop = np.concatenate([self.data.qpos[7:16], self.data.qvel[6:15]], dtype=np.float32)
        
        return {
            "vision": vision,
            "proprioception": prop,
            "context": self.game_engine.get_context_vector()
        }

    # ──────────────────────────────────────────────────────────
    #  리셋: 상황 무작위 부여
    # ──────────────────────────────────────────────────────────
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        cfg = self.stage_config

        if cfg.get("randomize_context", False):
            self.game_context = np.array([
                self.np_random.integers(0, 4),  
                self.np_random.integers(0, 3),  
                self.np_random.integers(0, 3),  
                self.np_random.integers(0, 2),  
                self.np_random.integers(0, 2),  
                self.np_random.integers(0, 2),  
            ], dtype=np.float32)
        else:
            self.game_context = np.zeros(6, dtype=np.float32)

        release_y = cfg["release_distance"]
        target_x = self.np_random.uniform(*cfg["target_x_range"])
        target_z = self.np_random.uniform(*cfg["target_z_range"])

        self.data.qpos[self.ball_qpos_adr + 0] = self.np_random.uniform(-0.02, 0.02)
        self.data.qpos[self.ball_qpos_adr + 1] = release_y
        self.data.qpos[self.ball_qpos_adr + 2] = 1.8 + self.np_random.uniform(-0.05, 0.05)
        self.data.qpos[self.ball_qpos_adr + 3: self.ball_qpos_adr + 7] = [1, 0, 0, 0]

        base_speed = self.np_random.uniform(*cfg["speed_range"])
        ball_start = np.array([
            self.data.qpos[self.ball_qpos_adr],
            release_y,
            self.data.qpos[self.ball_qpos_adr + 2],
        ])
        target_pos = np.array([target_x, 0.0, target_z])
        direction = target_pos - ball_start
        direction = direction / (np.linalg.norm(direction) + 1e-8)

        self.data.qvel[self.ball_qvel_adr + 0] = direction[0] * base_speed
        self.data.qvel[self.ball_qvel_adr + 1] = direction[1] * base_speed
        self.data.qvel[self.ball_qvel_adr + 2] = direction[2] * base_speed + 2.0

        # 로봇 9-DOF 초기화
        self.data.qpos[7:16] = 0.0
        self.data.qvel[6:15] = 0.0

        mujoco.mj_forward(self.model, self.data)

        self.step_count = 0
        self.has_contacted = False
        self.contact_info = {}
        self.min_dist_to_ball = float("inf")
        self.episode_total += 1

        return self._get_obs(), {"stage": self.curriculum_stage}

        # ── Head-Lock 보정 계산 (IK 기반 자동 시선 추적) ──
    def _apply_head_lock(self):
        ball_pos = self.data.xpos[self.ball_body_id]
        neck_pos = np.array([0.6, -0.1, 1.6]) 
        
        rel_pos = ball_pos - neck_pos
        x, y, z = rel_pos
        
        target_yaw = math.atan2(-y, -x)  
        dist_xy = math.hypot(x, y)
        target_pitch = math.atan2(z, dist_xy)
        
        # head joints 
        head_yaw_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "head_yaw")
        head_pitch_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "head_pitch")
        
        head_yaw_qpos_adr = self.model.jnt_qposadr[head_yaw_id]
        head_pitch_qpos_adr = self.model.jnt_qposadr[head_pitch_id]
        head_yaw_dof_adr = self.model.jnt_dofadr[head_yaw_id]
        head_pitch_dof_adr = self.model.jnt_dofadr[head_pitch_id]
        
        current_yaw = self.data.qpos[head_yaw_qpos_adr]
        current_pitch = self.data.qpos[head_pitch_qpos_adr]
        
        kp_yaw = 20.0
        kp_pitch = 20.0
        
        yaw_torque = (target_yaw - current_yaw) * kp_yaw - self.data.qvel[head_yaw_dof_adr] * 2.0
        pitch_torque = (target_pitch - current_pitch) * kp_pitch - self.data.qvel[head_pitch_dof_adr] * 2.0
        
        # ctrl actuator index
        head_yaw_act = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_yaw")
        head_pitch_act = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_pitch")
        
        self.data.ctrl[head_yaw_act] = np.clip(yaw_torque, -20.0, 20.0)
        self.data.ctrl[head_pitch_act] = np.clip(pitch_torque, -20.0, 20.0)

    # ──────────────────────────────────────────────────────────
    #  물리 스텝 (9-DOF)
    # ──────────────────────────────────────────────────────────
    def step(self, action: np.ndarray):
        action = np.clip(action, -1.0, 1.0)

        # 1. 팔(Arm) 7-DOF 토크 인가 (목 뒤의 액추에이터는 7~13번 인덱스임)
        # Wait, stadium_3d.xml에서 motor 선언 순서:
        # shoulder(3), elbow(1), wrist(3), cf_slide(3), head(2)
        # 아차, cf_slide가 중간에 있음.
        # motor 인덱스를 명확하게 확인해야 함.
        # 0~2: shoulder, 3: elbow, 4~6: wrist
        # 7~9: cf_actuators
        # 10~11: head_yaw, head_pitch
        self.data.ctrl[0] = action[0] * 50.0  
        self.data.ctrl[1] = action[1] * 50.0  
        self.data.ctrl[2] = action[2] * 50.0  
        self.data.ctrl[3] = action[3] * 50.0  
        self.data.ctrl[4] = action[4] * 25.0  
        self.data.ctrl[5] = action[5] * 25.0  
        self.data.ctrl[6] = action[6] * 25.0  

        # 2. 목(Neck) 2-DOF 제어
        if self.stage_config.get("head_lock", False):
            # RL 정책의 action[7:9] 무시하고 PID 추적기 작동
            self._apply_head_lock()
        else:
            # RL 정책이 스스로 고개를 돌림
            head_yaw_act = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_yaw")
            head_pitch_act = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_pitch")
            self.data.ctrl[head_yaw_act] = action[7] * 20.0  
            self.data.ctrl[head_pitch_act] = action[8] * 20.0

        # Head-Lock 로직에서 motor 인덱스를 제대로 맞춰야 함:
        # _apply_head_lock에서 ctrl[10], ctrl[11]을 건드려야 함 (아래 함수 수정됨)

        for _ in range(self.frame_skip):
            mujoco.mj_step(self.model, self.data)
            self._check_contacts()

        self.step_count += 1
        obs = self._get_obs()
        
        ball_pos = self.data.xpos[self.ball_body_id]
        bat_pos = self.data.xpos[self.bat_body_id]
        bat_rot = self.data.xmat[self.bat_body_id].reshape(3, 3)
        barrel_offset = bat_rot.dot(np.array([0.0, 0.675, 0.0]))
        barrel_pos = bat_pos + barrel_offset
        dist = np.linalg.norm(ball_pos - barrel_pos)
        self.min_dist_to_ball = min(self.min_dist_to_ball, dist)

        reward = 0.0
        terminated = False
        info = {"has_contacted": self.has_contacted, "stage": self.curriculum_stage}

        event_str = ""
        runs = 0

        if self.has_contacted:
            reward += 5.0
            self.episode_contacts += 1

            ev = self.contact_info.get("exit_velocity_kmh", 0.0)
            la = self.contact_info.get("launch_angle", 0.0)
            sa = self.contact_info.get("spray_angle", 0.0)
            dist_est = (ev / 3.6) * 3.0

            event_str, runs = self.game_engine.process_pitch(
                swung=True, contacted=True, in_strike_zone=True,
                exit_velocity_kmh=ev, distance_m=dist_est
            )

            reward += min(ev / 30.0, 5.0)
            if -45.0 <= sa <= 45.0:
                reward += 2.0
            
            if "Home Run" in event_str:
                reward += 20.0
            elif "Double" in event_str:
                reward += 10.0
            elif "Single" in event_str:
                reward += 5.0

            reward += runs * 5.0

            info.update(self.contact_info)
            info["game_event"] = event_str
            info["runs"] = runs
            terminated = True

        elif ball_pos[1] < -1.0 or ball_pos[2] < 0.02:
            # 타격 실패 (Miss / Strikeout / Ball)
            # 팔 관절 속도로 스윙 여부 판단
            swung = np.max(np.abs(self.data.qvel[6:13])) > 2.0
            # ball_joint_id는 관절 ID(int)이므로, qpos 주소는 ball_qpos_adr 사용
            target_x = self.data.qpos[self.ball_qpos_adr]  # x 좌표 (홈플레이트 좌우)
            in_sz = abs(target_x) <= 0.25

            event_str, runs = self.game_engine.process_pitch(
                swung=swung, contacted=False, in_strike_zone=in_sz
            )

            if event_str == "Swinging Strike":
                reward -= 1.5
            elif event_str == "Called Strike":
                reward -= 1.0
            elif event_str == "Ball":
                reward += 0.5
            elif event_str == "Walk":
                reward += 2.5
            elif event_str == "Strikeout":
                reward -= 4.0

            info["result"] = "MISS"
            info["game_event"] = event_str
            terminated = True

        else:
            if self.stage_config.get("use_distance_shaping", False):
                dist_reward = max(0.0, 1.0 - dist) * 0.3
                reward += dist_reward

        truncated = self.step_count >= self.max_steps
        return obs, float(reward), terminated, truncated, info

    def _check_contacts(self):
        if self.has_contacted: return
        for i in range(self.data.ncon):
            con = self.data.contact[i]
            g1, g2 = con.geom1, con.geom2
            is_ball = (g1 == self.ball_geom_id or g2 == self.ball_geom_id)
            is_bat = (g1 == self.bat_barrel_id or g2 == self.bat_barrel_id or
                      g1 == self.bat_taper_id or g2 == self.bat_taper_id)

            if is_ball and is_bat:
                self.has_contacted = True
                ball_vel = self.data.cvel[self.ball_body_id][3:6].copy()
                exit_speed = np.linalg.norm(ball_vel)
                vx, vy, vz = ball_vel
                horiz_speed = np.hypot(vx, vy)
                self.contact_info = {
                    "exit_velocity_kmh": exit_speed * 3.6,
                    "launch_angle": np.degrees(np.arctan2(vz, max(horiz_speed, 1e-3))),
                    "spray_angle": np.degrees(np.arctan2(vx, max(-vy, 1e-3))),
                }
                break

    def render(self):
        if self.renderer:
            self.renderer.update_scene(self.data, camera="batter_cam")
            return self.renderer.render()
        return None

    def get_contact_rate(self) -> float:
        return self.episode_contacts / self.episode_total if self.episode_total > 0 else 0.0
