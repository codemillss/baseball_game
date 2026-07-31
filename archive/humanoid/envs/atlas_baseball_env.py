import os
import time
import numpy as np
import mujoco
from typing import Dict, Any, Tuple
import gymnasium as gym
from humanoid.envs.game_engine import BaseballGameEngine

class AtlasBaseballEnv(gym.Env):
    """
    보스턴 다이내믹스 아틀라스(Boston Dynamics Atlas) 30-DOF 기반 야구 타격 환경
    - 특징: 실제 3D STL 메쉬 적용, Unpinned Pelvis (두 발로 타석 접지), Ground Reaction Force(GRF) 물리 적용
    """
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    CURRICULUM = {
        1: {"name": "Stage 1 (Atlas Grounded Batter)"},
        2: {"name": "Stage 2 (Full Game Logic & Corner Pitch)"},
    }

    def __init__(self, xml_path: str = "humanoid/assets/stadium_3d_atlas.xml", render_mode: str = None):
        super().__init__()

        self.game_engine = BaseballGameEngine()
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        self.render_mode = render_mode
        if self.render_mode == "rgb_array":
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)
        else:
            self.renderer = None

        # ID Mapping
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.ball_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        
        self.bat_barrel_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.pitcher_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pitcher_placeholder")

        # Actuator mapping (30 motors)
        self.actuator_names = [
            'back_bkz_motor', 'back_bky_motor', 'back_bkx_motor',
            'l_arm_shz_motor', 'l_arm_shx_motor', 'l_arm_ely_motor', 'l_arm_elx_motor', 'l_arm_uwy_motor', 'l_arm_mwx_motor', 'l_arm_lwy_motor',
            'neck_ay_motor',
            'r_arm_shz_motor', 'r_arm_shx_motor', 'r_arm_ely_motor', 'r_arm_elx_motor', 'r_arm_uwy_motor', 'r_arm_mwx_motor', 'r_arm_lwy_motor',
            'l_leg_hpz_motor', 'l_leg_hpx_motor', 'l_leg_hpy_motor', 'l_leg_kny_motor', 'l_leg_aky_motor', 'l_leg_akx_motor',
            'r_leg_hpz_motor', 'r_leg_hpx_motor', 'r_leg_hpy_motor', 'r_leg_kny_motor', 'r_leg_aky_motor', 'r_leg_akx_motor'
        ]
        self.motor_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in self.actuator_names]

        # Action Space: 30 continuous torques/positions
        self.action_dim = len(self.motor_ids)
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(self.action_dim,), dtype=np.float32)

        # Observation Space (Vision 4D, Proprio 60D, Context 8D)
        self.observation_space = gym.spaces.Dict({
            "vision": gym.spaces.Box(low=-np.inf, high=np.inf, shape=(4,), dtype=np.float32),
            "proprio": gym.spaces.Box(low=-np.inf, high=np.inf, shape=(60,), dtype=np.float32),
            "context": gym.spaces.Box(low=-np.inf, high=np.inf, shape=(8,), dtype=np.float32)
        })

        self.curriculum_stage = 1
        self.step_count = 0
        self.max_steps = 150
        self.has_contacted = False
        self.contact_info = {}

    def set_curriculum_stage(self, stage: int):
        self.curriculum_stage = stage

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        
        self.step_count = 0
        self.has_contacted = False
        self.contact_info = {}
        
        self._throw_pitch()
        mujoco.mj_forward(self.model, self.data)
        return self._get_obs(), {"stage": self.curriculum_stage}

    def _throw_pitch(self):
        pitcher_pos = self.data.xpos[self.pitcher_id]
        if self.curriculum_stage == 1:
            target_x = np.random.uniform(-0.1, 0.1)
            target_z = np.random.uniform(0.9, 1.1)
            speed = 32.0
        else:
            target_x = np.random.uniform(-0.3, 0.3)
            target_z = np.random.uniform(0.6, 1.2)
            speed = np.random.uniform(30.0, 42.0)

        self.target_zone = np.array([target_x, target_z])
        start_pos = pitcher_pos + np.array([0, 0, 0.5])
        target_pos = np.array([target_x, 0.0, target_z])
        
        direction = target_pos - start_pos
        direction /= np.linalg.norm(direction)
        vel = direction * speed

        qpos_adr = self.model.jnt_qposadr[self.ball_joint_id]
        qvel_adr = self.model.jnt_dofadr[self.ball_joint_id]
        
        self.data.qpos[qpos_adr : qpos_adr+3] = start_pos
        self.data.qvel[qvel_adr : qvel_adr+3] = vel

    def _get_obs(self) -> Dict[str, np.ndarray]:
        # 1. Proprioception (30 qpos + 30 qvel = 60D)
        # Use actuator ctrl / joint values
        qpos_vals = self.data.qpos[7:37] if len(self.data.qpos) >= 37 else np.zeros(30)
        qvel_vals = self.data.qvel[6:36] if len(self.data.qvel) >= 36 else np.zeros(30)
        proprio = np.concatenate([qpos_vals, qvel_vals]).astype(np.float32)

        # 2. Vision (Relative ball coords from head camera)
        head_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "head")
        head_pos = self.data.xpos[head_body_id]
        head_mat = self.data.xmat[head_body_id].reshape(3, 3)
        
        ball_pos_world = self.data.xpos[self.ball_body_id]
        rel_pos = head_mat.T @ (ball_pos_world - head_pos)
        
        dist = np.linalg.norm(rel_pos)
        azimuth = np.arctan2(rel_pos[1], rel_pos[0])
        elevation = np.arctan2(rel_pos[2], np.linalg.norm(rel_pos[:2]))
        vision = np.array([azimuth, elevation, dist, 1.0], dtype=np.float32)

        # 3. Context (Game Engine 6D + Target 2D = 8D)
        game_context = self.game_engine.get_context_vector()
        context = np.concatenate([game_context, self.target_zone]).astype(np.float32)

        return {"vision": vision, "proprio": proprio, "context": context}

    def _check_contacts(self):
        if self.has_contacted: return
        for i in range(self.data.ncon):
            con = self.data.contact[i]
            g1, g2 = con.geom1, con.geom2
            is_ball = (g1 == self.ball_geom_id or g2 == self.ball_geom_id)
            is_bat = (g1 == self.bat_barrel_id or g2 == self.bat_barrel_id)
            if is_ball and is_bat:
                self.has_contacted = True
                ball_vel = self.data.cvel[self.ball_body_id][3:6].copy()
                exit_speed = np.linalg.norm(ball_vel)
                vx, vy, vz = ball_vel
                self.contact_info = {
                    "exit_velocity_kmh": exit_speed * 3.6,
                    "launch_angle": np.degrees(np.arctan2(vz, max(np.hypot(vx, vy), 1e-3))),
                }

    def step(self, action: np.ndarray) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        action = np.clip(action, -1.0, 1.0)
        self.data.ctrl[self.motor_ids] = action

        for _ in range(5):
            mujoco.mj_step(self.model, self.data)
            self._check_contacts()

        self.step_count += 1
        obs = self._get_obs()

        # Balance & Posture Reward (Pelvis height stability)
        pelvis_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
        pelvis_z = self.data.xpos[pelvis_body_id][2]
        balance_reward = max(0.0, 1.0 - abs(pelvis_z - 0.95)) * 0.5

        info = {
            "has_contacted": self.has_contacted,
            "stage": self.curriculum_stage,
            "balance_reward": balance_reward
        }
        info.update(self.contact_info)

        terminated = False
        reward = balance_reward

        if self.has_contacted:
            terminated = True
            ev_kmh = self.contact_info.get("exit_velocity_kmh", 0.0)
            dist_m = (ev_kmh / 3.6) * 3.0
            event_str, runs = self.game_engine.process_pitch(
                swung=True, contacted=True, in_strike_zone=True,
                exit_velocity_kmh=ev_kmh, distance_m=dist_m
            )
            reward += 15.0 + (ev_kmh / 10.0)
            info["game_event"] = event_str
        else:
            ball_pos = self.data.xpos[self.ball_body_id]
            if ball_pos[1] > 2.0 or pelvis_z < 0.4: # Ball passed or robot fell down
                terminated = True
                if pelvis_z < 0.4:
                    reward -= 5.0 # Fall penalty
                    info["game_event"] = "Fall Down"
                else:
                    info["game_event"] = "Ball Passed"

        truncated = self.step_count >= self.max_steps
        return obs, float(reward), terminated, truncated, info

    def render(self):
        if self.renderer:
            self.renderer.update_scene(self.data, camera="broadcaster_cam")
            return self.renderer.render()
        return None
