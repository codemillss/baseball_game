import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np

class PitcherEnv(gym.Env):
    """
    Phase 2: Embodied Humanoid Pitcher Environment (Unitree H1)
    - Robot stands on the mound at y = 10.0m (or configurable distance).
    - Objective: Pitch the ball into the designated Strike Zone at Home Plate (y = 0.20m).
    - Action Space (4-dim):
        [0]: release_timing (0.3 ~ 0.8 progress of throwing motion)
        [1]: target_z_aim (-1.0 ~ 1.0 vertical angle adjustment)
        [2]: target_x_aim (-1.0 ~ 1.0 horizontal course adjustment)
        [3]: arm_velocity_scale (0.8 ~ 1.6 throw power multiplier)
    - Observation Space (13-dim):
        [target_x, target_z, is_released, ball_x, ball_y, ball_z, ball_vx, ball_vy, ball_vz, hand_x, hand_y, hand_z, progress]
    """
    def __init__(self, xml_path="shared_assets/h1_pitcher.xml", mound_distance=10.0, render_mode=None):
        super().__init__()
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        self.mound_distance = mound_distance
        
        # 18-dim observation (13 + 1 (progress) + 1 (target_pitch) + 3 (one-hot pitch type) - actually 18D)
        # target_x, target_z, is_released, throw_progress, ball_xyz, ball_vxyz, hand_xyz, pitch_one_hot (3D)
        # Total = 2 + 2 + 3 + 3 + 3 + 3 = 16D. Let's recount: 
        # target_x(1), target_z(1), is_rel(1), prog(1), ball_pos(3), ball_vel(3), hand_pos(3), onehot(3)
        # 1 + 1 + 1 + 1 + 3 + 3 + 3 + 3 = 16D
        self.observation_space = spaces.Box(low=-100.0, high=100.0, shape=(16,), dtype=np.float32)
        
        # 4-dim action: [release_timing, z_aim, x_aim, velocity_scale]
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
        
        self.hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "pitcher_hand_site")
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        
        self.joint_names = [
            "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
            "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
            "torso",
            "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
            "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"
        ]
        
        self.valid_indices = []
        self.qpos_adrs = []
        for i, n in enumerate(self.joint_names):
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
            if jid != -1:
                self.valid_indices.append(i)
                self.qpos_adrs.append(self.model.jnt_qposadr[jid])
        self.qvel_adrs = [self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.joint_names]
        
        self.base_keyframes = np.zeros((6, 19))
        def set_kf(idx, **kwargs):
            for k, v in kwargs.items():
                j_idx = self.joint_names.index(k)
                self.base_keyframes[idx, j_idx] = v
        set_kf(0, torso=-1.57, left_elbow=1.5, right_elbow=1.5)
        set_kf(1, torso=-1.57, left_hip_pitch=-1.5, left_knee=1.8, left_elbow=1.5, right_elbow=1.5)
        set_kf(2, torso=-1.57, left_hip_pitch=-0.5, left_knee=0.2, left_shoulder_pitch=-0.5, left_elbow=0.5, right_shoulder_pitch=-1.0, right_shoulder_roll=-1.0, right_elbow=0.5)
        set_kf(3, torso=-0.5, left_hip_pitch=0.0, left_knee=0.2, left_shoulder_pitch=-1.5, left_elbow=0.2, right_shoulder_pitch=-2.0, right_shoulder_roll=-1.5, right_shoulder_yaw=1.0, right_elbow=1.5)
        set_kf(4, torso=0.5, left_hip_pitch=0.0, left_knee=0.1, left_shoulder_pitch=1.0, left_elbow=0.5, right_shoulder_pitch=1.5, right_shoulder_roll=-0.2, right_shoulder_yaw=0.0, right_elbow=0.1, right_hip_pitch=0.5)
        set_kf(5, torso=1.2, left_hip_pitch=0.0, left_knee=0.3, left_shoulder_pitch=1.5, left_elbow=1.0, right_shoulder_pitch=2.2, right_shoulder_roll=-1.0, right_shoulder_yaw=-0.5, right_elbow=0.5, right_hip_pitch=1.0, right_knee=1.0)
        
        self.render_mode = render_mode
        self.viewer = None
        self.frame_skip = 2
        self.max_steps = 70
        self.current_step = 0
        
        self.target_x = 0.0
        self.target_z = 0.815
        
        self.is_released = False
        self.release_step = None
        self.release_speed_kmh = 0.0
        self.min_dist_to_target = 999.0
        self.reached_plate = False
        
        # Pitch type state
        self.target_pitch_type = 0
        self.extra_acc = np.array([0.0, 0.0, 0.0])

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        
        self.is_released = False
        self.release_step = None
        self.release_speed_kmh = 0.0
        self.min_dist_to_target = 999.0
        self.reached_plate = False
        self.current_step = 0
        self.throw_progress = 0.0
        self.extra_acc = np.array([0.0, 0.0, 0.0])
        
        self.target_x = float(np.random.uniform(-0.12, 0.12))
        self.target_z = float(np.random.uniform(0.70, 0.93))
        
        # Randomly select target pitch type (0: Fastball, 1: Slider, 2: Curveball)
        self.target_pitch_type = np.random.choice([0, 1, 2])
        
        self.data.eq_active[0] = True
        
        self._set_arm_pose(self.base_keyframes[0])
        mujoco.mj_forward(self.model, self.data)
        
        return self._get_obs(), {}

    def step(self, action):
        release_progress_target = 0.60 + 0.15 * float(np.clip(action[0], -1.0, 1.0))
        z_aim_delta = float(action[1]) * 0.4
        x_aim_delta = float(action[2]) * 0.3
        
        # Velocity scale for 150km/h (+). [-1, 1] -> [0.8, 2.5]. 2.5 * 18 = 45m/s (162km/h)
        vel_scale = 0.8 + 1.7 * (float(action[3]) + 1.0) / 2.0
        total_motion_frames = int(np.clip(16 / vel_scale, 8, 24))
        
        kfs = self.base_keyframes.copy()
        kfs[2:, 0] += x_aim_delta
        kfs[2:, 1] += z_aim_delta
        kfs[2:, 2] -= x_aim_delta * 0.5
        
        reward = 0.0
        terminated = False
        truncated = False
        dt = self.model.opt.timestep
        
        for _ in range(self.frame_skip):
            if self.throw_progress < 1.0:
                self.throw_progress += 1.0 / total_motion_frames
                self._update_arm_kinematics(self.throw_progress, kfs)
                
                if not self.is_released and self.throw_progress >= release_progress_target:
                    self.is_released = True
                    self.data.eq_active[0] = False
                    self.release_step = self.current_step
                    
                    # Direct momentum injection
                    base_vy = -18.0 * vel_scale
                    base_vz = 2.2 + z_aim_delta * 4.0
                    base_vx = -x_aim_delta * 3.5
                    
                    # Add spin physics based on pitch type
                    if self.target_pitch_type == 0:
                        # Fastball: slight upward magnus (hopping effect)
                        self.extra_acc = np.array([0.0, 0.0, 3.0])
                        # Extra velocity for fastball
                        base_vy *= 1.1 
                    elif self.target_pitch_type == 1:
                        # Slider: breaks horizontally
                        self.extra_acc = np.array([4.5, 0.0, 0.0])
                        # Slightly slower
                        base_vy *= 0.90
                    else:
                        # Curveball: sharp drop
                        self.extra_acc = np.array([-1.5, 0.0, -4.5])
                        # Much slower
                        base_vy *= 0.80

                    self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [base_vx, base_vy, base_vz]
                    
                    bvel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                    self.release_speed_kmh = float(np.linalg.norm(bvel) * 3.6)
            
            # Apply magnus force to the ball if released
            if self.is_released:
                self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += self.extra_acc * dt
                
            mujoco.mj_step(self.model, self.data)
            
            ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
            
            if ball_pos[1] <= 0.20 and not self.reached_plate:
                self.reached_plate = True
                dist = np.sqrt((ball_pos[0] - self.target_x)**2 + (ball_pos[2] - self.target_z)**2)
                self.min_dist_to_target = float(dist)
                
        self.current_step += 1
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        
        if self.reached_plate or ball_pos[2] <= 0.05 or ball_pos[1] < -0.5:
            terminated = True
            
            if self.reached_plate:
                dist = self.min_dist_to_target
                if dist <= 0.20:
                    # Strike! Emphasize velocity reward to force 150km/h
                    reward += 300.0 + (0.20 - dist) * 400.0 + self.release_speed_kmh * 2.5
                else:
                    reward += max(0.0, 100.0 - dist * 150.0)
            else:
                reward -= 50.0 * max(0.1, ball_pos[1] - 0.20)
                
        if self.current_step >= self.max_steps:
            truncated = True
            if not self.is_released:
                reward -= 100.0
                
        return self._get_obs(), reward, terminated, truncated, {
            "is_released": self.is_released,
            "reached_plate": self.reached_plate,
            "min_dist": self.min_dist_to_target,
            "release_speed_kmh": self.release_speed_kmh,
            "pitch_type": self.target_pitch_type
        }

    def _set_arm_pose(self, angles):
        for valid_i, adr in zip(self.valid_indices, self.qpos_adrs):
            self.data.qpos[adr] = angles[valid_i]
            

    def _update_arm_kinematics(self, progress, kfs):
        num_kfs = len(kfs)
        scaled = np.clip(progress, 0.0, 1.0) * (num_kfs - 1)
        idx1 = int(np.floor(scaled))
        idx2 = min(idx1 + 1, num_kfs - 1)
        t = scaled - idx1
        angles = (1-t)*kfs[idx1] + t*kfs[idx2]
        for valid_i, adr in zip(self.valid_indices, self.qpos_adrs):
            self.data.qpos[adr] = angles[valid_i]

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
        hand_pos = self.data.site_xpos[self.hand_site_id].copy()
        
        target = np.array([self.target_x, self.target_z], dtype=np.float32)
        rel_state = np.array([1.0 if self.is_released else 0.0, self.throw_progress], dtype=np.float32)
        
        # One-hot encoding of pitch type
        pitch_type_onehot = np.zeros(3, dtype=np.float32)
        pitch_type_onehot[self.target_pitch_type] = 1.0
        
        return np.concatenate([target, rel_state[:1], ball_pos, ball_vel, hand_pos, rel_state[1:], pitch_type_onehot]).astype(np.float32)

    def close(self):
        if self.viewer:
            self.viewer.close()
