import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np

class PitchingMachineEnv(gym.Env):
    """
    Phase 1-C: Multi-Speed Pitching Machine Environment (30 ~ 80 km/h)
    - Supports dynamic speed stages:
      * Stage 1: ~30 km/h (vy = -8.0 m/s, dist = 4.0m)
      * Stage 2: 50~55 km/h (vy = -14.5 m/s, dist = 10.0m)
      * Stage 3: 75~80 km/h (vy = -21.5 m/s, dist = 15.0m)
    - Observation (8-dim): [x, y, z, vx, vy, vz, t_remain, pred_z_at_plate]
    - Action (2-dim): [swing_trigger, target_z_delta]
    """
    def __init__(self, xml_path="shared_assets/h1_baseball.xml", target_speed_kmh=50, render_mode=None):
        super().__init__()
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        self.target_speed_kmh = target_speed_kmh
        
        # 8-dim Observation
        self.observation_space = spaces.Box(low=-100.0, high=100.0, shape=(8,), dtype=np.float32)
        
        # 2-dim Action [trigger, target_z_delta]
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
        
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
        self.max_steps = 55
        self.current_step = 0

    def set_speed(self, speed_kmh: int):
        self.target_speed_kmh = speed_kmh

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
        self.current_keyframes = self.base_keyframes.copy()
        self.current_step = 0
        self.min_dist = 999.0
        
        self.model.body_mass[self.ball_body_id] = 0.145
        
        # Configure pitch parameters according to target_speed_kmh
        if self.target_speed_kmh <= 35:
            # 30 km/h: 4m distance, vy = -8.0 m/s
            dist = 4.0
            z0 = 1.0
            vy = np.random.uniform(-8.3, -7.7)
            t_flight = (dist - 0.20) / abs(vy)
            drop = 0.5 * 9.81 * (t_flight ** 2)
            z_target = np.random.uniform(0.68, 0.95)
            vz = (z_target + drop - z0) / t_flight
        elif self.target_speed_kmh <= 60:
            # 50~55 km/h: 10m distance, vy = -14.5 m/s (~52 km/h)
            dist = 10.0
            z0 = 1.6
            vy = np.random.uniform(-15.0, -14.0)
            t_flight = (dist - 0.20) / abs(vy)
            drop = 0.5 * 9.81 * (t_flight ** 2)
            z_target = np.random.uniform(0.68, 0.95)
            vz = (z_target + drop - z0) / t_flight
        else:
            # 75~80 km/h: 15m distance, vy = -21.5 m/s (~77.4 km/h)
            dist = 15.0
            z0 = 1.8
            vy = np.random.uniform(-22.2, -21.0)
            t_flight = (dist - 0.20) / abs(vy)
            drop = 0.5 * 9.81 * (t_flight ** 2)
            z_target = np.random.uniform(0.68, 0.95)
            vz = (z_target + drop - z0) / t_flight
            
        vx = np.random.uniform(-0.03, 0.03)
        
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, dist, z0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
        
        self._update_swing_kinematics(0.0)
        mujoco.mj_forward(self.model, self.data)
        
        return self._get_obs(), {}

    def step(self, action):
        swing_trigger = float(action[0])
        target_z_delta = float(action[1])
        
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        t_remain = max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1]))
        
        # Trigger swing only when ball enters decision zone (t_remain <= 0.25s)
        if not self.swing_active and swing_trigger > 0.0 and t_remain <= 0.25:
            self.swing_active = True
            self.trigger_ball_y = float(ball_pos[1])
            self.trigger_t_remain = float(t_remain)
            pred_z = float(ball_pos[2] + ball_vel[2] * t_remain - 0.5 * 9.81 * (t_remain ** 2))
            self.trigger_z_zone = float((pred_z - 0.815) / 0.135)
            pitch_adj = -0.80 - target_z_delta * 0.55
            self.current_keyframes = self.base_keyframes.copy()
            self.current_keyframes[3, 1] += pitch_adj
            self.current_keyframes[4, 1] += pitch_adj
            
        reward = 0.0
        
        for _ in range(self.frame_skip):
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
                    # Ideal trigger is strictly t_remain in [0.11s, 0.13s]
                    timing_err = abs(self.trigger_t_remain - 0.12)
                    reward -= min(timing_err * 400.0, 50.0)
                    # Height guidance: align target_z_delta with z_zone
                    height_err = abs(target_z_delta - self.trigger_z_zone)
                    reward -= min(height_err * 25.0, 25.0)
                else:
                    reward -= 60.0 # Heavy penalty for looking at strike without swinging
                    
        if self.current_step >= self.max_steps:
            truncated = True
            
        return self._get_obs(), reward, terminated, truncated, {}

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
        
        # Normalized strike zone height coordinate in [-1.0, 1.0]
        # (0.68m -> -1.0, 0.815m -> 0.0, 0.95m -> +1.0)
        z_zone = float((pred_z - 0.815) / 0.135)
        
        features = np.array([t_remain, z_zone], dtype=np.float32)
        return np.concatenate([ball_pos, ball_vel, features]).astype(np.float32)

    def close(self):
        if self.viewer:
            self.viewer.close()
