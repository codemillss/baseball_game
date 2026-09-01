import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np
import os

class BaseballMatchEnv(gym.Env):
    """
    Phase 3: Live Pitcher vs Batter Full Match Environment
    - Two Unitree H1 humanoid robots concurrently active on the field:
        1. Pitcher Robot (on mound at y = 10.0m)
        2. Batter Robot (at plate at x = -0.85m, y = 0.0m)
    - Full match simulation with pitch delivery, swing tracking, contact physics, and hit outcome evaluation.
    """
    def __init__(self, xml_path="shared_assets/h1_baseball_match.xml", render_mode=None, is_eval_mode=False):
        super().__init__()
        self.is_eval_mode = is_eval_mode
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        
        # Pitcher joints
        self.p_joint_names = [
            "p_left_hip_yaw", "p_left_hip_roll", "p_left_hip_pitch", "p_left_knee", "p_left_ankle",
            "p_right_hip_yaw", "p_right_hip_roll", "p_right_hip_pitch", "p_right_knee", "p_right_ankle",
            "p_torso",
            "p_left_shoulder_pitch", "p_left_shoulder_roll", "p_left_shoulder_yaw", "p_left_elbow",
            "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"
        ]
        
        
        self.p_valid_indices = []
        self.p_qpos_adrs = []
        self.p_qvel_adrs = []
        for i, n in enumerate(self.p_joint_names):
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
            if jid != -1:
                self.p_valid_indices.append(i)
                self.p_qpos_adrs.append(self.model.jnt_qposadr[jid])
                self.p_qvel_adrs.append(self.model.jnt_dofadr[jid])
        
        # Batter joints
        self.b_joint_names = [
            "b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle",
            "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle",
            "b_torso",
            "b_left_shoulder_pitch", "b_left_shoulder_roll", "b_left_shoulder_yaw", "b_left_elbow",
            "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"
        ]
        
        
        self.b_valid_indices = []
        self.b_qpos_adrs = []
        self.b_qvel_adrs = []
        for i, n in enumerate(self.b_joint_names):
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)
            if jid != -1:
                self.b_valid_indices.append(i)
                self.b_qpos_adrs.append(self.model.jnt_qposadr[jid])
                self.b_qvel_adrs.append(self.model.jnt_dofadr[jid])

        
        # Pitcher Base Keyframes
        self.p_base_keyframes = np.zeros((6, 19))
        def set_pkf(idx, **kwargs):
            for k, v in kwargs.items():
                j_idx = self.p_joint_names.index("p_" + k)
                self.p_base_keyframes[idx, j_idx] = v
        set_pkf(0, torso=-1.57, left_elbow=1.5, right_elbow=1.5)
        set_pkf(1, torso=-1.57, left_hip_pitch=-1.5, left_knee=1.8, left_elbow=1.5, right_elbow=1.5)
        set_pkf(2, torso=-1.57, left_hip_pitch=-0.5, left_knee=0.2, left_shoulder_pitch=-0.5, left_elbow=0.5, right_shoulder_pitch=-1.0, right_shoulder_roll=-1.0, right_elbow=0.5)
        set_pkf(3, torso=-0.5, left_hip_pitch=0.0, left_knee=0.2, left_shoulder_pitch=-1.5, left_elbow=0.2, right_shoulder_pitch=-2.0, right_shoulder_roll=-1.5, right_shoulder_yaw=1.0, right_elbow=1.5)
        set_pkf(4, torso=0.5, left_hip_pitch=0.0, left_knee=0.1, left_shoulder_pitch=1.0, left_elbow=0.5, right_shoulder_pitch=1.5, right_shoulder_roll=-0.2, right_shoulder_yaw=0.0, right_elbow=0.1, right_hip_pitch=0.5)
        set_pkf(5, torso=1.2, left_hip_pitch=0.0, left_knee=0.3, left_shoulder_pitch=1.5, left_elbow=1.0, right_shoulder_pitch=2.2, right_shoulder_roll=-1.0, right_shoulder_yaw=-0.5, right_elbow=0.5, right_hip_pitch=1.0, right_knee=1.0)
        
        # Batter Base Keyframes
        self.b_base_keyframes = np.zeros((6, 19))
        def set_bkf(idx, **kwargs):
            for k, v in kwargs.items():
                j_idx = self.b_joint_names.index("b_" + k)
                self.b_base_keyframes[idx, j_idx] = v
        # Stance (Load) - weight on back leg (right knee slightly bent)
        set_bkf(0, torso=0.5, right_knee=0.3, left_shoulder_pitch=0.2, left_elbow=2.0, right_shoulder_pitch=-0.2, right_elbow=1.8)
        # Leg Kick / Tap
        set_bkf(1, torso=0.8, left_hip_pitch=-0.5, left_knee=0.5, right_knee=0.4, left_shoulder_pitch=0.2, left_elbow=2.0, right_shoulder_pitch=-0.2, right_elbow=1.8)
        # Stride
        set_bkf(2, torso=0.8, left_hip_pitch=-0.2, left_knee=0.2, right_knee=0.4, left_shoulder_pitch=0.3, left_elbow=1.8, right_shoulder_pitch=-0.3, right_elbow=1.6)
        # Hip Turn (Torso rotates to -0.5, bat lag - shoulders stay back slightly)
        set_bkf(3, torso=-0.2, left_hip_pitch=0.0, left_knee=0.1, right_knee=0.2, left_shoulder_pitch=0.5, left_shoulder_roll=-1.0, left_elbow=1.2, right_shoulder_pitch=-0.5, right_elbow=1.0)
        # Contact
        set_bkf(4, torso=-1.0, left_hip_pitch=0.0, left_knee=0.0, right_knee=0.1, left_shoulder_pitch=1.5, left_shoulder_roll=-1.5, left_elbow=0.2, right_shoulder_pitch=-1.0, right_elbow=0.2)
        # Follow Through
        set_bkf(5, torso=-1.5, left_hip_pitch=0.0, left_knee=0.0, right_knee=0.0, left_shoulder_pitch=2.0, left_shoulder_roll=-0.5, left_elbow=1.5, right_shoulder_pitch=-0.5, right_elbow=1.5)
        
        self.frame_skip = 2
        self.max_steps = 70
        self.current_step = 0
        self.render_mode = render_mode
        self.viewer = None
        
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        
        self.current_step = 0
        self.p_throw_progress = 0.0
        self.b_swing_progress = 0.0
        self.b_swing_active = False
        self.b_swing_duration = 24
        self.is_released = False
        self.has_contacted = False
        self.contact_step = None
        self.exit_velocity_kmh = 0.0
        self.batted_distance = 0.0
        self.pitch_speed_kmh = 0.0
        self.outcome = "IN_PLAY"
        
        # Random target for pitcher in strike zone
        self.target_x = float(np.random.uniform(-0.12, 0.12))
        self.target_z = float(np.random.uniform(0.70, 0.93))
        self.pitch_speed_kmh = 0.0
        self.outcome = "IN_PLAY"
        self.target_pitch_type = np.random.choice([0, 1, 2])
        self.extra_acc = np.array([0.0, 0.0, 0.0])
        
        # Wind Physics: random wind between -3.0 and 3.0 m/s in X and Y
        self.wind_vector = np.array([
            np.random.uniform(-4.0, 4.0),
            np.random.uniform(-4.0, 4.0),
            0.0
        ])
        
        self.data.eq_active[0] = True # Pitcher holds ball
        
        self.b_current_keyframes = self.b_base_keyframes.copy()
        self.p_current_keyframes = self.p_base_keyframes.copy()
        
        # Initialize stances
        self._set_pitcher_pose(self.p_base_keyframes[0])
        self._set_batter_pose(self.b_base_keyframes[0])
        self._set_batter_pose(self.b_base_keyframes[0])
        mujoco.mj_forward(self.model, self.data)
        
        return self.get_observations()

    def step(self, pitcher_action, batter_action):
        """
        Step both Pitcher AI and Batter AI in the match.
        pitcher_action: [release_timing, z_aim, x_aim, vel_scale]
        batter_action: [swing_trigger, z_delta, x_yaw]
        """
        # Pitcher Parameter Modulation
        p_rel_target = 0.60 + 0.15 * float(np.clip(pitcher_action[0], -1.0, 1.0))
        p_z_aim = float(pitcher_action[1]) * 0.4
        p_x_aim = float(pitcher_action[2]) * 0.3
        p_vel_scale = 0.8 + 1.7 * (float(pitcher_action[3]) + 1.0) / 2.0
        p_total_frames = int(np.clip(16 / p_vel_scale, 8, 24))
        
        self.p_current_keyframes = self.p_base_keyframes.copy()
        self.p_current_keyframes[2:, 10] += p_x_aim
        self.p_current_keyframes[2:, 15] += p_z_aim
        self.p_current_keyframes[2:, 16] -= p_x_aim * 0.5
        
        # Batter Parameter Modulation
        b_trigger = float(batter_action[0])
        b_z_delta = float(batter_action[1])
        b_x_yaw = float(batter_action[2])
        
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        t_remain = max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1]))
        
        # Trigger swing when ball is within strike interception window (t_remain <= 0.070s)
        if not self.b_swing_active and (b_trigger > 0.0) and t_remain <= 0.080 and self.is_released:
            self.b_swing_active = True
            b_pitch_adj = -0.75 - b_z_delta * 0.55
            b_torso_adj = b_x_yaw * 0.35
            self.b_current_keyframes = self.b_base_keyframes.copy()
            self.b_current_keyframes[3, 10] += b_torso_adj
            self.b_current_keyframes[4, 10] += b_torso_adj
            self.b_current_keyframes[3, 15] += b_pitch_adj; self.b_current_keyframes[3, 11] -= b_pitch_adj
            self.b_current_keyframes[4, 15] += b_pitch_adj; self.b_current_keyframes[4, 11] -= b_pitch_adj
            
        dt = self.model.opt.timestep
            
        for _ in range(self.frame_skip):
            # 1. Pitcher execution
            if self.p_throw_progress < 1.0:
                self.p_throw_progress += 1.0 / p_total_frames
                self._update_pitcher_kinematics(self.p_throw_progress)
                
                if not self.is_released and self.p_throw_progress >= p_rel_target:
                    self.is_released = True
                    self.data.eq_active[0] = False
                    base_vy = -18.0 * p_vel_scale
                    base_vz = 2.2 + p_z_aim * 4.0
                    base_vx = -p_x_aim * 3.5
                    
                    if self.target_pitch_type == 0:
                        self.extra_acc = np.array([0.0, 0.0, 3.0])
                        base_vy *= 1.1 
                    elif self.target_pitch_type == 1:
                        self.extra_acc = np.array([4.5, 0.0, 0.0])
                        base_vy *= 0.90
                    else:
                        self.extra_acc = np.array([-1.5, 0.0, -4.5])
                        base_vy *= 0.80
                        
                    self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [base_vx, base_vy, base_vz]
                    bvel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                    self.pitch_speed_kmh = float(np.linalg.norm(bvel) * 3.6)
                    
            if self.is_released:
                # Apply Magnus effect
                self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += self.extra_acc * dt
                
                # Apply aerodynamic drag and wind
                bvel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                v_rel = bvel - self.wind_vector
                speed_rel = np.linalg.norm(v_rel)
                
                # Drag coefficient for baseball k = 0.0054
                drag_acc = -0.0054 * speed_rel * v_rel
                self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += drag_acc * dt
                    
            # 2. Batter execution
            if self.b_swing_active and self.b_swing_progress < 1.0:
                self._update_batter_kinematics(self.b_swing_progress)
                self.b_swing_progress += 1.0 / self.b_swing_duration
                
            mujoco.mj_step(self.model, self.data)
            
            # Check Bat-Ball contact
            if not self.has_contacted and self._check_contact():
                self.has_contacted = True
                self.contact_step = self.current_step
                bvel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                self.exit_velocity_kmh = float(np.linalg.norm(bvel) * 3.6)
                
        self.current_step += 1
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        
        done = False
        post_contact_limit = 350 if self.is_eval_mode else 20
        max_limit = 450 if self.is_eval_mode else self.max_steps
        
        # Check termination
        if self.current_step >= max_limit or ball_pos[1] < -0.5:
            done = True
        elif ball_pos[2] <= 0.05:
            done = True
        elif self.has_contacted and self.current_step > self.contact_step + post_contact_limit:
            done = True
            
        if done:
            self._evaluate_outcome(ball_pos, ball_vel)
            
        return self.get_observations(), done, {
            "outcome": self.outcome,
            "has_contacted": self.has_contacted,
            "pitch_speed_kmh": self.pitch_speed_kmh,
            "exit_velocity_kmh": self.exit_velocity_kmh,
            "batted_distance": self.batted_distance,
            "is_in_strike_zone": getattr(self, "is_in_strike_zone", True)
        }

    def _evaluate_outcome(self, ball_pos, ball_vel):
        if self.has_contacted:
            # Ball was hit
            dist = np.sqrt(ball_pos[0]**2 + (ball_pos[1])**2)
            self.batted_distance = float(dist)
            
            is_foul = ball_pos[1] < np.abs(ball_pos[0])
            
            if is_foul:
                self.outcome = "⚪ FOUL BALL"
            else:
                if dist >= 60.0 and ball_pos[2] > 2.5:
                    self.outcome = "🔥 OUT OF THE PARK HOME RUN!"
                elif dist >= 58.0 and ball_pos[2] <= 2.5:
                    self.outcome = "💥 WALL-BALL DOUBLE!"
                elif dist >= 15.0 and self.exit_velocity_kmh > 40.0:
                    self.outcome = "💥 BASE HIT!"
                else:
                    self.outcome = "⚡ GROUND OUT / FLY OUT"
        else:
            # No contact
            dist_to_zone = np.sqrt((ball_pos[0] - self.target_x)**2 + (ball_pos[2] - self.target_z)**2)
            self.is_in_strike_zone = dist_to_zone <= 0.22
            
            if self.b_swing_active:
                self.outcome = "❌ STRIKE OUT (Swinging)"
            else:
                if self.is_in_strike_zone:
                    self.outcome = "🎯 CALLED STRIKE"
                else:
                    self.outcome = "⚠️ BALL (Walk)"

    def _check_contact(self):
        for i in range(self.data.ncon):
            contact = self.data.contact[i]
            if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \
               (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
                return True
        return False

    def _set_pitcher_pose(self, angles):
        for valid_i, qpos_adr, qvel_adr in zip(self.p_valid_indices, self.p_qpos_adrs, self.p_qvel_adrs):
            self.data.qpos[qpos_adr] = angles[valid_i]
            self.data.qvel[qvel_adr] = 0.0
            
    def _set_batter_pose(self, angles):
        for valid_i, qpos_adr, qvel_adr in zip(self.b_valid_indices, self.b_qpos_adrs, self.b_qvel_adrs):
            self.data.qpos[qpos_adr] = angles[valid_i]
            self.data.qvel[qvel_adr] = 0.0

    def _update_pitcher_kinematics(self, progress):
        num_kfs = len(self.p_current_keyframes)
        scaled = np.clip(progress, 0.0, 1.0) * (num_kfs - 1)
        idx1 = int(np.floor(scaled))
        idx2 = min(idx1 + 1, num_kfs - 1)
        t = scaled - idx1
        angles = (1-t)*self.p_current_keyframes[idx1] + t*self.p_current_keyframes[idx2]
        for valid_i, qpos_adr, qvel_adr in zip(self.p_valid_indices, self.p_qpos_adrs, self.p_qvel_adrs):
            self.data.qpos[qpos_adr] = angles[valid_i]
            self.data.qvel[qvel_adr] = 0.0

    def _update_batter_kinematics(self, progress):
        num_kfs = len(self.b_current_keyframes)
        scaled = np.clip(progress, 0.0, 1.0) * (num_kfs - 1)
        idx1 = int(np.floor(scaled))
        idx2 = min(idx1 + 1, num_kfs - 1)
        t = scaled - idx1
        angles = (1-t)*self.b_current_keyframes[idx1] + t*self.b_current_keyframes[idx2]
        for valid_i, qpos_adr, qvel_adr in zip(self.b_valid_indices, self.b_qpos_adrs, self.b_qvel_adrs):
            self.data.qpos[qpos_adr] = angles[valid_i]
            self.data.qvel[qvel_adr] = 0.0

    def get_observations(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
        
        # Pitcher Obs (16-dim)
        p_target = np.array([self.target_x, self.target_z], dtype=np.float32)
        p_rel_state = np.array([1.0 if self.is_released else 0.0, self.p_throw_progress], dtype=np.float32)
        hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "pitcher_hand_site")
        hand_pos = self.data.site_xpos[hand_site_id].copy()
        
        pitch_type_onehot = np.zeros(3, dtype=np.float32)
        if hasattr(self, "target_pitch_type"):
            pitch_type_onehot[self.target_pitch_type] = 1.0
            
        pitcher_obs = np.concatenate([
            p_target, 
            p_rel_state, 
            ball_pos, 
            ball_vel, 
            hand_pos, 
            pitch_type_onehot
        ]).astype(np.float32)
        
        # Batter Obs (12-dim)
        t_remain = float(max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1])))
        pred_z = float(ball_pos[2] + ball_vel[2] * t_remain - 0.5 * 9.81 * (t_remain ** 2))
        pred_x = float(ball_pos[0] + ball_vel[0] * t_remain)
        z_zone = float((pred_z - 0.815) / 0.135)
        x_zone = float(pred_x / 0.15)
        features = np.array([t_remain, z_zone, x_zone], dtype=np.float32)
        
        # Let's also give batter the pitch type so it can anticipate breaking balls better!
        batter_obs = np.concatenate([ball_pos, ball_vel, features, pitch_type_onehot]).astype(np.float32)
        
        return {"pitcher": pitcher_obs, "batter": batter_obs}
