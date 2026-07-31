"""
multi_agent_env.py — 완전한 분산형 1인칭 Multi-Agent 야구 환경

특징:
  1. 철저한 정보 격리: 타자는 batter_cam만, 투수는 pitcher_cam만 봄 (에고센트릭 시야)
  2. Action Space: Dict({pitcher: 8-DOF, batter: 9-DOF})
  3. Observation Space: Dict({pitcher: vision+prop, batter: vision+prop})
  4. 투구 릴리즈: 투수가 action[7] > 0.5를 입력하면 손에서 공이 홈플레이트를 향해 발사됨
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
import mujoco
from pathlib import Path
from typing import Dict, Any, Tuple

from envs.game_engine import BaseballGameEngine
from dataclasses import dataclass

@dataclass
class EnvConfig:
    mode: str = "full" # "full", "pitcher_only", "batter_only", "fielder_only"
    is_tee_ball: bool = False
    pitch_speed_y: float = -33.3  # m/s (approx 120km/h)
    strike_zone_scale: float = 1.0
    bat_speed_reward: bool = True

class MultiAgentBaseballEnv(gym.Env):
    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 60}

    def __init__(self, xml_path: str = None, frame_skip: int = 4, render_mode: str = "rgb_array", config: EnvConfig = None):
        super().__init__()
        self.config = config if config is not None else EnvConfig()
        if xml_path is None:
            xml_path = str(Path(__file__).parent.parent / "assets" / "stadium_3d.xml")

        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        self.frame_skip = frame_skip
        self.render_mode = render_mode
        self.game_engine = BaseballGameEngine()

        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.ball_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_qpos_adr = self.model.jnt_qposadr[self.ball_joint_id]
        self.ball_qvel_adr = self.model.jnt_dofadr[self.ball_joint_id]
        
        self.pitcher_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "pitcher_cam")
        self.batter_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "batter_cam")
        self.fielder_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "fielder_cam")
        self.release_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_release_site")
        
        self.bat_barrel_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.cf_glove_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "cf_glove")

        # action_spaces
        self.action_space = spaces.Dict({
            "pitcher": spaces.Box(low=-1.0, high=1.0, shape=(8,), dtype=np.float32),
            "batter": spaces.Box(low=-1.0, high=1.0, shape=(9,), dtype=np.float32),
            "fielder": spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32),
        })

        # observation_spaces
        # vision is 64x64 RGB
        # pitcher prop: 7 joints (qpos+qvel = 14) + release state (1) = 15D
        # batter prop: 9 joints (qpos+qvel = 18) = 18D
        # fielder prop: 3 joints (qpos+qvel = 6) = 6D
        self.observation_space = spaces.Dict({
            "pitcher": spaces.Dict({
                "vision": spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
                "proprioception": spaces.Box(low=-100.0, high=100.0, shape=(15,), dtype=np.float32),
            }),
            "batter": spaces.Dict({
                "vision": spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
                "proprioception": spaces.Box(low=-100.0, high=100.0, shape=(18,), dtype=np.float32),
            }),
            "fielder": spaces.Dict({
                "vision": spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
                "proprioception": spaces.Box(low=-100.0, high=100.0, shape=(6,), dtype=np.float32),
            })
        })

        self.renderer_pitcher = None
        self.renderer_batter = None
        self.renderer_fielder = None
        if self.render_mode == "rgb_array":
            self.renderer_pitcher = mujoco.Renderer(self.model, height=64, width=64)
            self.renderer_batter = mujoco.Renderer(self.model, height=64, width=64)
            self.renderer_fielder = mujoco.Renderer(self.model, height=64, width=64)

        self.step_count = 0
        self.max_steps = 150 if self.config.is_tee_ball else 300
        self.is_released = False
        self.has_contacted = False
        self.contact_info = {}

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        
        self.step_count = 0
        self.max_steps = 150 if self.config.is_tee_ball else 300
        self.is_released = False
        self.has_contacted = False
        self.is_caught = False
        self.contact_info = {}
        
        mujoco.mj_forward(self.model, self.data)
        
        # Move ball to pitcher's hand initially or Tee
        if self.config.is_tee_ball:
            self._sync_ball_to_tee()
        else:
            self._sync_ball_to_hand()
            
        mujoco.mj_forward(self.model, self.data)

        return self._get_obs(), {}

    def _sync_ball_to_hand(self):
        """볼을 투수의 손(p_release_site)에 고정"""
        hand_pos = self.data.site_xpos[self.release_site_id]
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, 0.0, 0.0]
        
    def _sync_ball_to_tee(self):
        """볼을 타자 앞 허공(Tee)에 고정"""
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 0.0, 1.0] # 1m height at home plate
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, 0.0, 0.0]
        self.is_released = True # Already "released" so it can be hit

    def _get_obs(self):
        obs = {"pitcher": {}, "batter": {}, "fielder": {}}
        
        if self.renderer_pitcher and self.renderer_batter and self.renderer_fielder:
            self.renderer_pitcher.update_scene(self.data, camera="pitcher_cam")
            obs["pitcher"]["vision"] = self.renderer_pitcher.render().copy()
            
            self.renderer_batter.update_scene(self.data, camera="batter_cam")
            obs["batter"]["vision"] = self.renderer_batter.render().copy()
            
            self.renderer_fielder.update_scene(self.data, camera="fielder_cam")
            obs["fielder"]["vision"] = self.renderer_fielder.render().copy()
        else:
            obs["pitcher"]["vision"] = np.zeros((64, 64, 3), dtype=np.uint8)
            obs["batter"]["vision"] = np.zeros((64, 64, 3), dtype=np.uint8)
            obs["fielder"]["vision"] = np.zeros((64, 64, 3), dtype=np.uint8)
            
        p_joints = ["p_shoulder_pitch", "p_shoulder_yaw", "p_shoulder_roll", 
                    "p_elbow_flex", "p_elbow_pronate", "p_wrist_flex", "p_wrist_dev"]
        p_qpos = [self.data.qpos[self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in p_joints]
        p_qvel = [self.data.qvel[self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in p_joints]
        obs["pitcher"]["proprioception"] = np.concatenate([p_qpos, p_qvel, [float(self.is_released)]], dtype=np.float32)

        b_joints = ["head_yaw", "head_pitch", "shoulder_yaw", "shoulder_pitch", "shoulder_roll", 
                    "elbow_flex", "wrist_yaw", "wrist_pitch", "wrist_roll"]
        b_qpos = [self.data.qpos[self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in b_joints]
        b_qvel = [self.data.qvel[self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in b_joints]
        obs["batter"]["proprioception"] = np.concatenate([b_qpos, b_qvel], dtype=np.float32)

        f_joints = ["cf_slide_x", "cf_slide_y", "cf_arm_pitch"]
        f_qpos = [self.data.qpos[self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in f_joints]
        f_qvel = [self.data.qvel[self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in f_joints]
        obs["fielder"]["proprioception"] = np.concatenate([f_qpos, f_qvel], dtype=np.float32)

        return obs

    def step(self, actions: Dict[str, np.ndarray]):
        p_act = np.clip(actions["pitcher"], -1.0, 1.0)
        b_act = np.clip(actions["batter"], -1.0, 1.0)
        f_act = np.clip(actions["fielder"], -1.0, 1.0)
        
        # Override actions based on drill mode
        if self.config.mode == "batter_only":
            p_act = np.zeros(8, dtype=np.float32)
            p_act[7] = 1.0 # auto throw
            f_act = np.zeros(3, dtype=np.float32)
        elif self.config.mode == "pitcher_only":
            b_act = np.zeros(9, dtype=np.float32)
            f_act = np.zeros(3, dtype=np.float32)
        elif self.config.mode == "fielder_only":
            p_act = np.zeros(8, dtype=np.float32)
            p_act[7] = 1.0
            b_act = np.zeros(9, dtype=np.float32)

        # Apply Batter controls
        b_acts = ["head_yaw", "head_pitch", "shoulder_yaw", "shoulder_pitch", "shoulder_roll", 
                  "elbow_flex", "wrist_yaw", "wrist_pitch", "wrist_roll"]
        for i, act_name in enumerate(b_acts):
            act_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, act_name)
            cr_max = self.model.actuator_ctrlrange[act_id][1]
            self.data.ctrl[act_id] = b_act[i] * cr_max

        # Apply Pitcher controls
        p_acts = ["p_shoulder_pitch", "p_shoulder_yaw", "p_shoulder_roll", 
                  "p_elbow_flex", "p_elbow_pronate", "p_wrist_flex", "p_wrist_dev"]
        for i, act_name in enumerate(p_acts):
            act_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, act_name)
            cr_max = self.model.actuator_ctrlrange[act_id][1]
            self.data.ctrl[act_id] = p_act[i] * cr_max

        # Apply Fielder controls
        f_acts = ["cf_slide_x", "cf_slide_y", "cf_arm_pitch"]
        for i, act_name in enumerate(f_acts):
            act_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, act_name)
            cr_max = self.model.actuator_ctrlrange[act_id][1]
            self.data.ctrl[act_id] = f_act[i] * cr_max

        p_release_intent = p_act[7]
        
        for _ in range(self.frame_skip):
            mujoco.mj_step(self.model, self.data)
            self._check_contacts()
            
            if self.config.is_tee_ball and not self.has_contacted:
                self._sync_ball_to_tee()
            elif not self.is_released:
                if p_release_intent > 0.5:
                    self.is_released = True
                    
                    if self.config.mode == "batter_only":
                        # Batting Machine mode: Spawn at Y=15.0 (near mound) and throw towards home plate (Y=0)
                        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 15.0, 1.5]
                        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, self.config.pitch_speed_y, 1.5]
                    elif self.config.mode == "fielder_only":
                        # Fielder training: Auto hit a pop fly
                        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 0.0, 1.0]
                        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [np.random.uniform(-10, 10), 20.0, 30.0]
                        self.has_contacted = True # Trigger play
                    else:
                        # Full / Pitcher mode: Standard release from hand
                        self.data.qvel[self.ball_qvel_adr+1] = self.config.pitch_speed_y
                else:
                    self._sync_ball_to_hand()

        self.step_count += 1
        obs = self._get_obs()
        
        rewards = {"pitcher": 0.0, "batter": 0.0, "fielder": 0.0}
        terminated = {"pitcher": False, "batter": False, "fielder": False, "__all__": False}
        truncated = {"pitcher": False, "batter": False, "fielder": False, "__all__": False}
        info = {"pitcher": {}, "batter": {}, "fielder": {}}

        ball_pos = self.data.xpos[self.ball_body_id]
        bat_pos = self.data.geom_xpos[self.bat_barrel_id]
        
        # Continuous Stance & Swing shaping rewards for Batter
        if not self.has_contacted and self.config.mode != "pitcher_only":
            if self.config.is_tee_ball:
                # Tee-Ball: Encourage bat to hit the ball continuously
                dist = np.linalg.norm(bat_pos - ball_pos)
                rewards["batter"] += 0.05 * np.exp(-dist)
            else:
                if ball_pos[1] > 2.0:
                    # Ball is far (coming from pitcher at +18): Encourage ready stance
                    stance_rew = 0.01 * max(0, bat_pos[2] - 0.8) + 0.01 * max(0, bat_pos[1])
                    rewards["batter"] += stance_rew
                elif ball_pos[1] >= -1.0 and ball_pos[1] <= 2.0:
                    # Ball is close: Encourage bat barrel to be near the ball
                    dist = np.linalg.norm(bat_pos - ball_pos)
                    swing_rew = 0.02 * np.exp(-dist)
                    rewards["batter"] += swing_rew
                
            # Energy Penalty (Prevent jittery/alien movements, heavily reduced so batter is not afraid to move)
            action_penalty = 0.0005 * np.sum(np.square(b_act))
            rewards["batter"] -= action_penalty
        
        if self.is_caught:
            # 뜬공 아웃 (Catch)
            rewards["fielder"] += 10.0
            rewards["batter"] -= 10.0
            rewards["pitcher"] += 5.0 # Pitcher is happy about the out
            terminated = {k: True for k in terminated}
            info["fielder"]["caught"] = True
            
        elif self.has_contacted and ball_pos[2] < 0.2:
            # 땅볼 혹은 안타 (일단 충돌 후 바닥에 닿으면 종료로 간주)
            rewards["batter"] += 10.0
            rewards["pitcher"] -= 10.0
            rewards["fielder"] -= 5.0 # Fielder missed it
            terminated = {k: True for k in terminated}
            info["batter"]["contact"] = True
            
        elif ball_pos[1] < -1.0 or ball_pos[2] < 0.0:
            if self.config.is_tee_ball:
                # In Tee-ball, if the ball drops to the ground without contact, the batter failed.
                rewards["batter"] -= 5.0
                terminated = {k: True for k in terminated}
            else:
                bat_speed = np.max(np.abs(b_act[2:7])) # 팔 관절 움직임으로 판단
                swung = bat_speed > 0.5
                target_x = self.data.qpos[self.ball_qpos_adr]
                
                # Strike zone based on config
                in_sz = abs(target_x) <= (0.25 * self.config.strike_zone_scale)
                
                if in_sz and swung:
                    rewards["pitcher"] += 5.0
                    rewards["batter"] -= 5.0
                elif in_sz and not swung:
                    rewards["pitcher"] += 3.0
                    rewards["batter"] -= 1.0
                else:
                    rewards["batter"] += 2.0
                    rewards["pitcher"] -= 2.0
                    
                # Punish batter for doing absolutely nothing if not in tee ball
                if not swung and self.config.mode != "pitcher_only":
                    rewards["batter"] -= 2.0
                
                terminated = {k: True for k in terminated}
            
        # Reward shaping for bat speed on contact
        if self.has_contacted and self.config.bat_speed_reward:
            bat_speed = np.max(np.abs(b_act[2:7]))
            rewards["batter"] += bat_speed * 5.0 # Encourages hard swings

        if self.step_count >= self.max_steps:
            truncated = {k: True for k in truncated}
            
        return obs, rewards, terminated, truncated, info

    def _check_contacts(self):
        for i in range(self.data.ncon):
            con = self.data.contact[i]
            g1, g2 = con.geom1, con.geom2
            
            # 1. Bat - Ball Contact
            if not self.has_contacted:
                if (g1 == self.ball_geom_id and g2 == self.bat_barrel_id) or (g2 == self.ball_geom_id and g1 == self.bat_barrel_id):
                    self.has_contacted = True
            
            # 2. Glove - Ball Contact (Flyout Catch)
            if not self.is_caught and self.has_contacted: # Only can catch if hit
                if (g1 == self.ball_geom_id and g2 == self.cf_glove_id) or (g2 == self.ball_geom_id and g1 == self.cf_glove_id):
                    self.is_caught = True
