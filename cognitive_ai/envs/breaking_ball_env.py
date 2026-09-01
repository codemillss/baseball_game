import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np

class BreakingBallEnv(gym.Env):
    """
    Phase 1-D: Breaking Ball & 3D Swing Environment
    - Pitches: Fastball (직구), Slider (슬라이더), Curveball (커브) + Inside/Outside courses
    - Observation (9-dim): [x, y, z, vx, vy, vz, t_remain, z_zone, x_zone]
    - Action (3-dim): [swing_trigger, target_z_delta, target_x_yaw]
    """
    def __init__(self, xml_path="shared_assets/h1_baseball.xml", render_mode=None):
        super().__init__()
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        
        # 9-dim Observation
        self.observation_space = spaces.Box(low=-100.0, high=100.0, shape=(9,), dtype=np.float32)
        
        # 3-dim Action: [trigger, target_z_delta (height), target_x_yaw (course)]
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        
        self.joint_names = [
            "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
            "left_hip_roll", "left_hip_pitch", "left_knee", "right_hip_roll", "right_hip_pitch", "right_knee"
        ]
        self.qpos_adrs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.joint_names]
        
        # Base Keyframes [torso, rs_p, rs_r, rs_y, r_elbow, l_hr, l_hp, l_k, r_hr, r_hp, r_k]
        self.base_keyframes = np.array([
            [-0.5, -1.0, 0.0, 0.5, 1.5,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stance
            [-1.0, -1.2, 0.0, 0.8, 2.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Load
            [0.0, -0.5, 0.0, 0.0, 1.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stride
            [1.5, 0.5, 0.0, -0.5, 0.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Contact
            [2.0, 1.0, 0.0, -1.0, 1.5,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8]  # Follow-through
        ])
        
        self.render_mode = render_mode
        if render_mode == "human":
            from mujoco import viewer
            self.viewer = viewer.launch_passive(self.model, self.data)
        else:
            self.viewer = None
            
        self.frame_skip = 4
        self.max_steps = 60
        self.current_step = 0
        self.pitch_type = "FASTBALL"

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        
        self.swing_active = False
        self.swing_progress = 0.0
        self.swing_duration_frames = 24
        self.has_contacted = False
        self.trigger_ball_y = -999.0
        self.trigger_t_remain = -999.0
        self.trigger_z_zone = 0.0
        self.trigger_x_zone = 0.0
        self.current_keyframes = self.base_keyframes.copy()
        self.current_step = 0
        self.min_dist = 999.0
        
        self.model.body_mass[self.ball_body_id] = 0.145
        
        # Random pitch selection: 0: FASTBALL, 1: SLIDER, 2: CURVE
        pitch_idx = np.random.choice([0, 1, 2], p=[0.4, 0.35, 0.25])
        dist = 12.0 # 12 meters pitching distance
        
        # Target arrival coordinates at home plate (y = 0.20m)
        x_target = np.random.uniform(-0.12, 0.12) # Inside to Outside
        z_target = np.random.uniform(0.68, 0.95)  # Low to High
        
        if pitch_idx == 0:
            self.pitch_type = "FASTBALL"
            vy = np.random.uniform(-18.0, -16.5) # ~62 km/h
            z0 = 1.6
            x0 = 0.0
            t_flight = (dist - 0.20) / abs(vy)
            drop = 0.5 * 9.81 * (t_flight ** 2)
            vz = (z_target + drop - z0) / t_flight
            vx = (x_target - x0) / t_flight
            self.extra_acc = np.array([0.0, 0.0, 0.0])
        elif pitch_idx == 1:
            self.pitch_type = "SLIDER"
            vy = np.random.uniform(-15.5, -14.5) # ~54 km/h
            z0 = 1.6
            x0 = -0.10
            t_flight = (dist - 0.20) / abs(vy)
            drop = 0.5 * 9.81 * (t_flight ** 2)
            vz = (z_target + drop - z0) / t_flight
            # Lateral acceleration break
            lat_acc = np.random.uniform(2.5, 4.0)
            vx = (x_target - x0 - 0.5 * lat_acc * (t_flight ** 2)) / t_flight
            self.extra_acc = np.array([lat_acc, 0.0, 0.0])
        else:
            self.pitch_type = "CURVE"
            vy = np.random.uniform(-13.5, -12.5) # ~47 km/h
            z0 = 1.8
            x0 = 0.08
            t_flight = (dist - 0.20) / abs(vy)
            # Extra 12-6 drop acceleration
            drop_acc = 3.5
            lat_acc = -1.5
            drop = 0.5 * (9.81 + drop_acc) * (t_flight ** 2)
            vz = (z_target + drop - z0) / t_flight
            vx = (x_target - x0 - 0.5 * lat_acc * (t_flight ** 2)) / t_flight
            self.extra_acc = np.array([lat_acc, 0.0, -drop_acc])
            
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [x0, dist, z0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
        
        self._update_swing_kinematics(0.0)
        mujoco.mj_forward(self.model, self.data)
        
        return self._get_obs(), {}

    def step(self, action):
        swing_trigger = float(action[0])
        target_z_delta = float(action[1])
        target_x_yaw = float(action[2])
        
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        t_remain = max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1]))
        
        # Trigger swing inside decision zone (t_remain <= 0.25s)
        if not self.swing_active and swing_trigger > 0.0 and t_remain <= 0.25:
            self.swing_active = True
            self.trigger_ball_y = float(ball_pos[1])
            self.trigger_t_remain = float(t_remain)
            
            # Predict intercept coordinates
            pred_z = float(ball_pos[2] + ball_vel[2] * t_remain - 0.5 * (9.81 - self.extra_acc[2]) * (t_remain ** 2))
            pred_x = float(ball_pos[0] + ball_vel[0] * t_remain + 0.5 * self.extra_acc[0] * (t_remain ** 2))
            
            self.trigger_z_zone = float((pred_z - 0.815) / 0.135)
            self.trigger_x_zone = float(pred_x / 0.15)
            
            # Kinematic adjustments:
            pitch_adj = -0.75 - target_z_delta * 0.55
            torso_adj = target_x_yaw * 0.35
            
            self.current_keyframes = self.base_keyframes.copy()
            self.current_keyframes[3, 0] += torso_adj # Contact torso yaw
            self.current_keyframes[4, 0] += torso_adj # Follow-through torso yaw
            self.current_keyframes[3, 1] += pitch_adj # Contact shoulder pitch
            self.current_keyframes[4, 1] += pitch_adj # Follow-through shoulder pitch
            
        reward = 0.0
        
        for _ in range(self.frame_skip):
            # Apply breaking ball aerodynamic Magnus acceleration
            dt = 0.005
            self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += self.extra_acc * dt
            
            if self.swing_active and self.swing_progress < 1.0:
                self._update_swing_kinematics(self.swing_progress)
                self.swing_progress += 1.0 / self.swing_duration_frames
                
            mujoco.mj_step(self.model, self.data)
            
            bat_pos = self.data.geom_xpos[self.bat_geom_id]
            ball_pos_curr = self.data.geom_xpos[self.ball_geom_id]
            dist = np.linalg.norm(bat_pos - ball_pos_curr)
            self.min_dist = min(self.min_dist, dist)
            
            if not self.has_contacted and self._check_contact():
                self.has_contacted = True
                
        if self.viewer:
            self.viewer.sync()
            
        self.current_step += 1
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        
        terminated = False
        truncated = False
        
        if self.has_contacted or ball_pos[1] < -0.3 or ball_pos[2] < 0.1 or (self.swing_active and self.swing_progress >= 1.0):
            terminated = True
            if self.has_contacted:
                ball_vel_end = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                exit_speed = np.linalg.norm(ball_vel_end)
                reward += 200.0 + min(exit_speed * 10.0, 50.0)
            else:
                reward -= 50.0 * (self.min_dist ** 2)
                if self.swing_active:
                    # Timing reward
                    timing_err = abs(self.trigger_t_remain - 0.10)
                    reward -= min(timing_err * 300.0, 40.0)
                    # Height & Yaw alignment guidance
                    height_err = abs(target_z_delta - self.trigger_z_zone)
                    yaw_err = abs(target_x_yaw - self.trigger_x_zone)
                    reward -= min(height_err * 20.0, 20.0)
                    reward -= min(yaw_err * 20.0, 20.0)
                else:
                    reward -= 50.0 # Staring at pitch penalty
                    
        if self.current_step >= self.max_steps:
            truncated = True
            
        return self._get_obs(), reward, terminated, truncated, {"pitch_type": self.pitch_type}

    def _update_swing_kinematics(self, progress):
        num_kfs = len(self.current_keyframes)
        scaled = progress * (num_kfs - 1)
        idx1 = int(np.floor(scaled))
        idx2 = min(idx1 + 1, num_kfs - 1)
        t = scaled - idx1
        angles = (1-t)*self.current_keyframes[idx1] + t*self.current_keyframes[idx2]
        for i, adr in enumerate(self.qpos_adrs):
            self.data.qpos[adr] = angles[i]
            jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, self.joint_names[i])
            vel_adr = self.model.jnt_dofadr[jnt_id]
            self.data.qvel[vel_adr] = 0.0

    def _check_contact(self):
        for i in range(self.data.ncon):
            contact = self.data.contact[i]
            if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \
               (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
                return True
        return False

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
        t_remain = float(max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1])))
        
        pred_z = float(ball_pos[2] + ball_vel[2] * t_remain - 0.5 * 9.81 * (t_remain ** 2))
        pred_x = float(ball_pos[0] + ball_vel[0] * t_remain)
        
        z_zone = float((pred_z - 0.815) / 0.135)
        x_zone = float(pred_x / 0.15)
        
        features = np.array([t_remain, z_zone, x_zone], dtype=np.float32)
        return np.concatenate([ball_pos, ball_vel, features]).astype(np.float32)

    def close(self):
        if self.viewer:
            self.viewer.close()
