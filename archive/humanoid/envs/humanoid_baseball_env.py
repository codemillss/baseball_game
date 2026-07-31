import os
import time
import numpy as np
import mujoco
from typing import Dict, Any, Tuple
import gymnasium as gym
from humanoid.envs.game_engine import BaseballGameEngine

class HumanoidBaseballEnv(gym.Env):
    """
    야구 타격(배팅)을 위한 MuJoCo 기반 강화학습 환경 (휴머노이드 21-DOF 버전)
    - 특징: Standard Humanoid를 타자로 사용하여 전신 제어 학습
    - 목표: 투수가 던진 공을 방망이로 정확히 맞추기 (Contact)
    """
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    CURRICULUM = {
        1: {"name": "Stage 1 (Stage 2.5a: Head-Lock & Center Vision)"},
        2: {"name": "Stage 2 (Vision Only, No Head-Lock)"},
        3: {"name": "Stage 3 (Full Multimodal & Edge Vision)"}
    }
    
    def __init__(self, xml_path: str = "humanoid/assets/stadium_3d_humanoid.xml", render_mode: str = None):
        super().__init__()
        
        self.game_engine = BaseballGameEngine()
        
        # 1. 모델 로드
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        self.render_mode = render_mode

        # 2. 객체 ID 매핑
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.ball_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        
        self.bat_barrel_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.bat_taper_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_taper")
        
        self.pitcher_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pitcher_placeholder")

        # 3. 휴머노이드 모터 및 관절 매핑 (21-DOF)
        self.actuator_names = [
            "abdomen_z", "abdomen_y", "abdomen_x",
            "hip_x_right", "hip_z_right", "hip_y_right", "knee_right", "ankle_y_right", "ankle_x_right",
            "hip_x_left", "hip_z_left", "hip_y_left", "knee_left", "ankle_y_left", "ankle_x_left",
            "shoulder1_right", "shoulder2_right", "elbow_right",
            "shoulder1_left", "shoulder2_left", "elbow_left"
        ]
        
        self.motor_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in self.actuator_names]
        self.joint_names = self.actuator_names # In this model, motor names match joint names exactly
        self.joint_qpos_idxs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)] for j in self.joint_names]
        self.joint_qvel_idxs = [self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)] for j in self.joint_names]

        # 4. 카메라 매핑
        self.batter_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "batter_cam")
        self.pitcher_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "pitcher_cam")
        self.catcher_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "catcher_cam")
        self.broadcaster_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "broadcaster_cam")
        
        self.camera_ids = [self.batter_cam_id, self.pitcher_cam_id, self.catcher_cam_id, self.broadcaster_cam_id]

        # 5. 공간 정의
        self.action_dim = len(self.motor_ids)  # 21
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(self.action_dim,), dtype=np.float32)

        # 상태 공간: [관절각(21), 관절속도(21), 공의상대좌표(3), 공의상대속도(3), 컨텍스트(2)] = 21+21+3+3+2 = 50
        self.proprio_dim = self.action_dim * 2
        self.vision_dim = 4 # (azimuth, elevation, distance, is_visible)
        self.context_dim = 2 # (strike_zone_x, strike_zone_z)
        self.observation_space = gym.spaces.Dict({
            "vision": gym.spaces.Box(low=-10.0, high=10.0, shape=(self.vision_dim,), dtype=np.float32),
            "proprio": gym.spaces.Box(low=-50.0, high=50.0, shape=(self.proprio_dim,), dtype=np.float32),
            "context": gym.spaces.Box(low=-5.0, high=5.0, shape=(self.context_dim,), dtype=np.float32)
        })

        # 6. 환경 상태 변수
        self.max_steps = 150
        self.step_count = 0
        self.has_contacted = False
        self.contact_info = {}
        
        self.curriculum_stage = 1
        
        # Renderer
        self.renderer = None
        if self.render_mode == "rgb_array":
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)

    def set_curriculum_stage(self, stage: int):
        self.curriculum_stage = stage

    def reset(self, seed: int = None, options: dict = None) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        
        # 1. 공 발사 (투구) 설정
        self._throw_pitch()
        
        # 2. 로봇 자세 초기화
        self.data.ctrl[self.motor_ids] = 0.0
        
        self.step_count = 0
        self.has_contacted = False
        self.contact_info = {}

        mujoco.mj_forward(self.model, self.data)
        
        return self._get_obs(), {"stage": self.curriculum_stage}

    def _throw_pitch(self):
        pitcher_pos = self.data.xpos[self.pitcher_id]
        
        # 커리큘럼에 따른 투구 다양성 (Stage 1: 직구 중앙, Stage 2: 코너 워크)
        if self.curriculum_stage == 1:
            target_x = np.random.uniform(-0.1, 0.1)
            target_z = np.random.uniform(0.9, 1.1)
            speed = 30.0
        else:
            target_x = np.random.uniform(-0.3, 0.3)
            target_z = np.random.uniform(0.5, 1.3)
            speed = np.random.uniform(30.0, 40.0)
            
        self.target_zone = np.array([target_x, target_z])
        
        start_pos = pitcher_pos + np.array([0, 0, 0.5]) # 투수 손 위치
        target_pos = np.array([target_x, 0.0, target_z]) # 홈플레이트 통과 위치
        
        direction = target_pos - start_pos
        distance = np.linalg.norm(direction)
        direction /= distance
        
        vel = direction * speed
        
        qpos_adr = self.model.jnt_qposadr[self.ball_joint_id]
        qvel_adr = self.model.jnt_dofadr[self.ball_joint_id]
        
        self.data.qpos[qpos_adr : qpos_adr+3] = start_pos
        self.data.qvel[qvel_adr : qvel_adr+3] = vel

    def _get_obs(self) -> Dict[str, np.ndarray]:
        # 1. Proprioception (21 DOF)
        qpos = np.array([self.data.qpos[idx] for idx in self.joint_qpos_idxs])
        qvel = np.array([self.data.qvel[idx] for idx in self.joint_qvel_idxs])
        proprio = np.concatenate([qpos, qvel]).astype(np.float32)

        # 2. Vision (Relative ball coords from batter's head)
        head_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "head")
        head_pos = self.data.xpos[head_body_id]
        head_mat = self.data.xmat[head_body_id].reshape(3, 3)
        
        ball_pos_world = self.data.xpos[self.ball_body_id]
        rel_pos = head_mat.T @ (ball_pos_world - head_pos)
        
        dist = np.linalg.norm(rel_pos)
        azimuth = np.arctan2(rel_pos[1], rel_pos[0])
        elevation = np.arctan2(rel_pos[2], np.linalg.norm(rel_pos[:2]))
        
        # 커리큘럼 시야 처리
        if self.curriculum_stage >= 2:
            visible = 1.0 if abs(azimuth) < np.radians(60) else 0.0
            if abs(azimuth) >= np.radians(60) and abs(azimuth) < np.radians(100):
                azimuth += np.random.normal(0, 0.1)
                dist += np.random.normal(0, 0.5)
        else:
            visible = 1.0

        vision = np.array([azimuth, elevation, dist, visible], dtype=np.float32)

        # 3. Context (Game Engine 6D + Target Zone 2D = 8D)
        game_context = self.game_engine.get_context_vector()
        context = np.concatenate([game_context, self.target_zone]).astype(np.float32)

        return {
            "vision": vision,
            "proprio": proprio,
            "context": context
        }

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

    def _get_reference_motion(self, time_fraction: float) -> np.ndarray:
        """
        간략화된 모방 학습 레퍼런스(Reference) 생성 (총 21 DOF)
        0.0 (Stance) -> 0.5 (Impact) -> 1.0 (Follow-through)
        """
        # 기본 자세 0으로 초기화
        ref = np.zeros(self.action_dim, dtype=np.float32)
        
        # 주요 관절 인덱스 (humanoid.xml 기준 순서)
        idx_abd_z = 0 # abdomen_z (허리 비틀기)
        idx_sho_r = 15 # shoulder1_right
        idx_elb_r = 17 # elbow_right
        idx_sho_l = 18 # shoulder1_left
        idx_elb_l = 20 # elbow_left

        if time_fraction < 0.5:
            # Stance -> Impact
            alpha = time_fraction / 0.5
            ref[idx_abd_z] = np.interp(alpha, [0, 1], [-0.5, 0.8])
            ref[idx_sho_r] = np.interp(alpha, [0, 1], [-0.5, 0.2])
            ref[idx_elb_r] = np.interp(alpha, [0, 1], [-1.5, -0.2])
            ref[idx_sho_l] = np.interp(alpha, [0, 1], [-0.2, 0.5])
            ref[idx_elb_l] = np.interp(alpha, [0, 1], [-1.0, -0.5])
        else:
            # Impact -> Follow-through
            alpha = (time_fraction - 0.5) / 0.5
            ref[idx_abd_z] = np.interp(alpha, [0, 1], [0.8, 1.2])
            ref[idx_sho_r] = np.interp(alpha, [0, 1], [0.2, 1.0])
            ref[idx_elb_r] = np.interp(alpha, [0, 1], [-0.2, -1.0])
            ref[idx_sho_l] = np.interp(alpha, [0, 1], [0.5, 1.0])
            ref[idx_elb_l] = np.interp(alpha, [0, 1], [-0.5, -1.5])

        return ref

    def step(self, action: np.ndarray) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        action = np.clip(action, -1.0, 1.0)
        self.data.ctrl[self.motor_ids] = action

        for _ in range(5):
            mujoco.mj_step(self.model, self.data)
            self._check_contacts()

        self.step_count += 1
        obs = self._get_obs()
        
        # 모방 학습 리워드 계산 (Imitation Reward)
        time_fraction = min(1.0, self.step_count / 100.0) # 예상 투구 도달 프레임을 100으로 가정
        qpos_ref = self._get_reference_motion(time_fraction)
        
        qpos_actual = np.array([self.data.qpos[idx] for idx in self.joint_qpos_idxs])
        
        # 관절 각도 L2 오차 페널티 (값이 작을수록 폼이 예쁨)
        pose_error = np.mean(np.square(qpos_actual - qpos_ref))
        imitation_reward = max(0.0, 1.0 - pose_error) * 0.5 # 최대 0.5점 부여
        
        info = {
            "has_contacted": self.has_contacted, 
            "stage": self.curriculum_stage,
            "imitation_reward": imitation_reward,
            "pose_error": pose_error
        }
        info.update(self.contact_info)

        terminated = False
        reward = imitation_reward # 베이스 리워드는 모방 리워드로 시작

        # 게임 엔진 이벤트 처리를 위한 변수
        event_str = ""
        runs = 0

        if self.has_contacted:
            terminated = True
            
            ev_kmh = self.contact_info.get("exit_velocity_kmh", 0.0)
            # 비거리 추정 (초속 * 체공시간 3초 가정)
            dist_m = (ev_kmh / 3.6) * 3.0
            
            event_str, runs = self.game_engine.process_pitch(
                swung=True, contacted=True, in_strike_zone=True,
                exit_velocity_kmh=ev_kmh, distance_m=dist_m
            )
            
            # 태스크 보상
            if "Home Run" in event_str:
                reward += 20.0
            elif "Double" in event_str:
                reward += 10.0
            elif "Single" in event_str:
                reward += 5.0
            else: # 아웃
                reward -= 1.0
                
            reward += runs * 5.0 # 타점 보상

        else:
            bat_pos = self.data.xpos[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "bat")]
            ball_pos = self.data.xpos[self.ball_body_id]
            
            # 볼이 배터를 지나쳤으면 종료
            if ball_pos[1] > 2.0:
                terminated = True
                
                # 스윙 여부 판정 (관절 속도 최대값)
                qvels = np.array([self.data.qvel[idx] for idx in self.joint_qvel_idxs])
                swung = np.max(np.abs(qvels)) > 3.0
                
                # 스트라이크 존 판정
                tx, tz = self.target_zone
                in_sz = (abs(tx) <= 0.25) and (0.6 <= tz <= 1.2)
                
                event_str, runs = self.game_engine.process_pitch(
                    swung=swung, contacted=False, in_strike_zone=in_sz
                )
                
                if event_str == "Swinging Strike":
                    reward -= 1.0
                elif event_str == "Called Strike":
                    reward -= 0.5
                elif event_str == "Ball":
                    reward += 0.5
                elif event_str == "Walk":
                    reward += 2.0
                elif event_str == "Strikeout":
                    reward -= 3.0
                    
                reward += runs * 5.0

                # Distance penalty
                dist = np.linalg.norm(bat_pos - ball_pos)
                dist_reward = max(0.0, 1.0 - dist) * 0.3
                reward += dist_reward

        info["game_event"] = event_str
        info["runs_scored"] = runs
        info["game_over"] = self.game_engine.game_over

        truncated = self.step_count >= self.max_steps
        return obs, float(reward), terminated, truncated, info
