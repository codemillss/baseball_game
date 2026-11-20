"""
DirectionalBattingEnv: Phase 1 Goal-Conditioned Precision Batting Environment for H1 Humanoid.
Features:
- Full 19-DoF H1 kinematics with athletic batting stance and upper-body swing actuators.
- Realistic motor torque saturation limits (H1 actuator limits).
- Goal-conditioned directional hitting: Target Azimuth (Pull / Center / Push), Target Launch Angle, Target Exit Velocity.
- Precision sweet-spot contact detection and fair-ball exit trajectory tracking.
"""

import os
import sys
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import mujoco


class DirectionalBattingEnv(gym.Env):
    """
    Phase 1 Goal-Conditioned Directional Batting Environment.
    
    Observation (31 dims):
      [0:3]   Pitched ball pos relative to plate [x, y, z]
      [3:6]   Pitched ball velocity [vx, vy, vz]
      [6]     Time remaining to reach plate (s)
      [7:10]  Goal vector: [target_azimuth_rad, target_launch_angle_rad, target_exit_vel]
      [10:15] Robot swing joint positions [torso, r_pitch, r_roll, r_yaw, r_elbow]
      [15:20] Robot swing joint velocities
      [20:23] Bat sweet spot world pos [x, y, z]
      [23:26] Bat sweet spot linear velocity [vx, vy, vz]
      [26:31] Previous action (5 dims)
      
    Action (5 dims, range [-1, 1]):
      a[0]: Swing timing lead/lag delta: dt in [-0.030, +0.030] s (Pull vs Center vs Push control)
      a[1]: Bat elevation delta: dz in [-0.08, +0.08] m (High vs Low pitch tracking)
      a[2]: Swing plane / attack angle delta: dalpha in [-0.15, +0.15] rad (Launch angle control)
      a[3]: Torso uncoiling duration / power: dpower in [-0.02, +0.02] s (Exit velocity modulation)
      a[4]: Arm extension / reach: delb in [-0.15, +0.15] rad (Inside vs Outside sweet spot alignment)
    """

    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}

    def __init__(
        self,
        xml_path=None,
        render_mode=None,
        frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz control)
        pitch_speed_range=(14.0, 18.0),  # 50 ~ 65 km/h
        pitch_dist=7.5,
    ):
        super().__init__()

        if xml_path is None:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            xml_path = os.path.join(curr_dir, "..", "models", "h1_baseball.xml")

        self.xml_path = xml_path
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        
        # Position H1 batter at home plate batter box
        pelvis_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
        if pelvis_body_id >= 0:
            self.model.body_pos[pelvis_body_id, 0] = -0.90
            self.model.body_pos[pelvis_body_id, 1] = 0.00
            self.model.body_pos[pelvis_body_id, 2] = 0.95

        self.data = mujoco.MjData(self.model)

        self.render_mode = render_mode
        self.frame_skip = frame_skip
        self.dt = self.model.opt.timestep * self.frame_skip  # 0.02 s
        self.pitch_speed_range = pitch_speed_range
        self.pitch_dist = pitch_dist

        # Identify Geoms & Sites
        self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")

        # Freejoint for ball
        ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
        self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]

        # Upper body swing actuators and joints
        self.swing_actuator_names = [
            "torso",
            "right_shoulder_pitch",
            "right_shoulder_roll",
            "right_shoulder_yaw",
            "right_elbow",
        ]
        self.act_ids = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
            for name in self.swing_actuator_names
        ]
        self.jnt_ids = [self.model.actuator_trnid[a, 0] for a in self.act_ids]
        self.qpos_adrs = [self.model.jnt_qposadr[j] for j in self.jnt_ids]
        self.qvel_adrs = [self.model.jnt_dofadr[j] for j in self.jnt_ids]

        # Athletic batting crouch leg joint addresses
        self.leg_joint_names = [
            "left_hip_pitch", "left_knee", "left_hip_roll",
            "right_hip_pitch", "right_knee", "right_hip_roll"
        ]
        self.leg_qpos_adrs = [
            self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, lj)]
            for lj in self.leg_joint_names
        ]

        # Canonical Kinematic Chain Swing Keyframes
        # [torso, rsp, rsr, rsy, relb]
        self.base_keyframes = np.array([
            [-0.40, -1.00,  0.00,  0.40,  1.50],  # 0: Stance
            [-0.60, -1.15,  0.00,  0.60,  1.70],  # 1: Load / Takeback
            [-0.10, -0.70, -0.05,  0.20,  1.20],  # 2: Stride / Uncoil start
            [ 0.50, -0.30, -0.10, -0.10,  0.70],  # 3: Slot / Acceleration
            [ 1.15,  0.20, -0.08, -0.40,  0.35],  # 4: Contact
            [ 1.70,  0.80,  0.00, -0.70,  1.20]   # 5: Follow-through
        ], dtype=np.float32)

        # PD Gains for Upper Body Actuators
        self.Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
        self.Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)

        # Action Space: 5-dim continuous
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(5,), dtype=np.float32)

        # Observation Space: 31-dim continuous
        obs_dim = 7 + 3 + 5 + 5 + 3 + 3 + 5
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )

        # Episode State Variables
        self.current_step = 0
        self.max_steps = 35
        self.prev_action = np.zeros(5, dtype=np.float32)
        self.filtered_action = np.zeros(5, dtype=np.float32)
        self.swing_triggered = False
        self.locked_t_trigger = 0.0
        self.locked_swing_duration = 0.17
        self.has_contacted = False
        self.contact_reward_given = False
        self.contact_step = -1
        self.contact_ball_pos = None
        self.contact_sweet_pos = None
        self.exit_ball_vel = None
        self.min_ball_sweet_dist = 999.0
        self.exit_velocity = 0.0
        self.exit_azimuth_deg = 0.0
        self.exit_launch_deg = 0.0
        self.is_fair_hit = False

        # Viewer / Renderer
        self.renderer = None
        if self.render_mode in ["rgb_array", "human"]:
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)

    def _set_athletic_leg_crouch(self):
        """Maintains stable athletic batting stance legs."""
        for lj, qadr in zip(self.leg_joint_names, self.leg_qpos_adrs):
            if "pitch" in lj:
                self.data.qpos[qadr] = -0.35
            elif "knee" in lj:
                self.data.qpos[qadr] = 0.70
            elif "left_hip_roll" in lj:
                self.data.qpos[qadr] = 0.18
            elif "right_hip_roll" in lj:
                self.data.qpos[qadr] = -0.18

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        self.current_step = 0
        self.prev_action = np.zeros(5, dtype=np.float32)
        self.filtered_action = np.zeros(5, dtype=np.float32)
        self.swing_triggered = False
        self.locked_t_trigger = 0.0
        self.locked_swing_duration = 0.17
        self.has_contacted = False
        self.contact_reward_given = False
        self.contact_step = -1
        self.contact_ball_pos = None
        self.contact_sweet_pos = None
        self.exit_ball_vel = None
        self.min_ball_sweet_dist = 999.0
        self.exit_velocity = 0.0
        self.exit_azimuth_deg = 0.0
        self.exit_launch_deg = 0.0
        self.is_fair_hit = False

        # Set athletic stance
        self._set_athletic_leg_crouch()

        # Initialize upper body joints to stance keyframe
        for i, qadr in enumerate(self.qpos_adrs):
            self.data.qpos[qadr] = self.base_keyframes[0, i]

        # 1. Sample Goal Condition Vector
        # Target Azimuth: Pull (-35° to -10°), Center (-10° to +10°), Push (+10° to +35°)
        target_azimuth_deg = self.np_random.uniform(-35.0, 35.0)
        self.target_azimuth_rad = float(np.radians(target_azimuth_deg))

        # Target Launch Angle: Line Drive to home run trajectory (12° to 32°)
        target_launch_deg = self.np_random.uniform(12.0, 32.0)
        self.target_launch_rad = float(np.radians(target_launch_deg))

        # Target Exit Velocity: 10 to 20 m/s (36 ~ 72 km/h)
        self.target_exit_vel = float(np.random.uniform(10.0, 18.0) if not hasattr(self, 'np_random') else self.np_random.uniform(10.0, 18.0))

        # 2. Sample Pitched Ball Parameters
        pitch_speed = self.np_random.uniform(*self.pitch_speed_range)
        vy = -pitch_speed
        
        # Target arrival coordinate in strike zone (over home plate at y = 0.22m)
        plate_y_contact = 0.22
        t_flight = (self.pitch_dist - plate_y_contact) / abs(vy)
        self.nominal_t_flight = t_flight

        # Inside / Outside pitch variation (0.10m ~ 0.16m over home plate)
        target_x = self.np_random.uniform(0.10, 0.16)
        # Pitch height variation centered on sweet spot hitting plane (0.74m ~ 0.78m)
        target_z = self.np_random.uniform(0.74, 0.78)

        # Calculate initial vertical velocity with gravity drop
        z0 = 0.85
        drop = 0.5 * 9.81 * (t_flight ** 2)
        vz = (target_z + drop - z0) / t_flight

        # Set ball position and velocity
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [target_x, self.pitch_dist, z0]
        self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, vy, vz]
        self.data.qvel[self.ball_qvel_adr+3:self.ball_qvel_adr+6] = [0.0, 0.0, 0.0]

        mujoco.mj_forward(self.model, self.data)

        # Nominal swing trigger time (empirically centered for symmetric Pull/Center/Push coverage)
        self.nominal_t_trigger = t_flight - 0.126
        self.nominal_swing_duration = 0.17

        return self._get_obs(), {}

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        
        # Time remaining to plate
        vy = ball_vel[1]
        t_remain = max(0.0, ball_pos[1] / abs(vy)) if vy < -0.1 else 0.0

        # Goal vector (3 dims)
        goal = np.array([
            self.target_azimuth_rad,
            self.target_launch_rad,
            self.target_exit_vel,
        ], dtype=np.float32)

        # Upper body joint positions and velocities (5 + 5 = 10 dims)
        joint_pos = np.array([self.data.qpos[adr] for adr in self.qpos_adrs], dtype=np.float32)
        joint_vel = np.array([self.data.qvel[adr] for adr in self.qvel_adrs], dtype=np.float32)

        # Bat sweet spot state (3 + 3 = 6 dims)
        sweet_pos = self.data.site_xpos[self.sweet_spot_id].astype(np.float32)
        res = np.zeros(6, dtype=np.float64)
        mujoco.mj_objectVelocity(
            self.model, self.data, mujoco.mjtObj.mjOBJ_SITE,
            self.sweet_spot_id, res, 0
        )
        sweet_vel = res[3:6].astype(np.float32)

        obs = np.concatenate([
            ball_pos,           # 3
            ball_vel,           # 3
            [t_remain],         # 1
            goal,               # 3
            joint_pos,          # 5
            joint_vel,          # 5
            sweet_pos,          # 3
            sweet_vel,          # 3
            self.prev_action,   # 5
        ], dtype=np.float32)

        return obs

    def step(self, action):
        self.current_step += 1
        action = np.clip(action, -1.0, 1.0).astype(np.float32)

        # Exponential moving average filter for smooth continuous action modulation
        self.filtered_action = 0.6 * self.filtered_action + 0.4 * action

        # Unpack Action Modulations:
        # a[0]: Timing delta dt in [-0.030, +0.030] s (Pull < 0, Push > 0)
        dt_timing = float(self.filtered_action[0] * 0.030)
        # a[1]: Bat elevation delta dz in [-0.08, +0.08] m
        d_rsp = float(-self.filtered_action[1] * 0.12)
        # a[2]: Attack angle / plane tilt -> shoulder roll & elbow tilt
        d_tilt = float(self.filtered_action[2] * 0.10)
        # a[3]: Torso uncoiling speed / duration delta in [-0.02, +0.02] s
        d_duration = float(-self.filtered_action[3] * 0.02)
        # a[4]: Extension / sweet spot alignment -> elbow delta
        d_elbow = float(self.filtered_action[4] * 0.15)

        # Swing trigger and duration management:
        sim_time_curr = self.data.time
        if not self.swing_triggered:
            candidate_t_trigger = max(0.04, self.nominal_t_trigger + dt_timing)
            candidate_duration = max(0.12, self.nominal_swing_duration + d_duration)
            if sim_time_curr >= candidate_t_trigger:
                self.swing_triggered = True
                self.locked_t_trigger = candidate_t_trigger
                self.locked_swing_duration = candidate_duration
            t_trigger = candidate_t_trigger
            swing_duration = candidate_duration
        else:
            t_trigger = self.locked_t_trigger
            swing_duration = self.locked_swing_duration

        # Modulate Keyframes for entire hitting phase (Keyframes 3, 4, 5)
        mod_keyframes = self.base_keyframes.copy()
        mod_keyframes[3, 1] += d_rsp * 0.6
        mod_keyframes[4, 1] += d_rsp
        mod_keyframes[5, 1] += d_rsp

        mod_keyframes[3, 2] += d_tilt * 0.6
        mod_keyframes[4, 2] += d_tilt
        mod_keyframes[5, 2] += d_tilt

        mod_keyframes[3, 4] += d_elbow * 0.6
        mod_keyframes[4, 4] += d_elbow
        mod_keyframes[5, 4] += d_elbow

        # Execute physics simulation over frame_skip sub-steps
        for _ in range(self.frame_skip):
            sim_time = self.data.time

            # Compute target upper-body joints
            if sim_time < t_trigger:
                target_q = mod_keyframes[0]
            else:
                progress = np.clip((sim_time - t_trigger) / swing_duration, 0.0, 1.0)
                idx_f = progress * (len(mod_keyframes) - 1)
                idx0 = int(np.floor(idx_f))
                idx1 = min(idx0 + 1, len(mod_keyframes) - 1)
                alpha = idx_f - idx0
                target_q = (1.0 - alpha) * mod_keyframes[idx0] + alpha * mod_keyframes[idx1]

            # Apply PD torques to upper body actuators with torque saturation clipping
            for i, aid in enumerate(self.act_ids):
                q = self.data.qpos[self.qpos_adrs[i]]
                dq = self.data.qvel[self.qvel_adrs[i]]
                tau = self.Kp[i] * (target_q[i] - q) - self.Kd[i] * dq
                ctrl_min = self.model.actuator_ctrlrange[aid, 0]
                ctrl_max = self.model.actuator_ctrlrange[aid, 1]
                self.data.ctrl[aid] = np.clip(tau, ctrl_min, ctrl_max)

            # Step MuJoCo physics
            mujoco.mj_step(self.model, self.data)

            # Track minimum distance between ball and sweet spot
            ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
            sweet_pos = self.data.site_xpos[self.sweet_spot_id]
            dist_curr = float(np.linalg.norm(ball_pos - sweet_pos))
            if dist_curr < self.min_ball_sweet_dist:
                self.min_ball_sweet_dist = dist_curr

            # Detect Bat-Ball Collision
            if self.data.ncon > 0:
                for c in range(self.data.ncon):
                    con = self.data.contact[c]
                    if (con.geom1 == self.bat_geom_id and con.geom2 == self.ball_geom_id) or \
                       (con.geom1 == self.ball_geom_id and con.geom2 == self.bat_geom_id):
                        if not self.has_contacted:
                            self.has_contacted = True
                            self.contact_step = self.current_step
                            self.contact_ball_pos = ball_pos.copy()
                            self.contact_sweet_pos = sweet_pos.copy()
                        break

            # If contact has occurred, track post-contact ball velocity
            if self.has_contacted:
                curr_ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                if curr_ball_vel[1] > 0:
                    self.is_fair_hit = True
                    if self.exit_ball_vel is None or np.linalg.norm(curr_ball_vel) > np.linalg.norm(self.exit_ball_vel):
                        self.exit_ball_vel = curr_ball_vel.copy()
                elif self.exit_ball_vel is None:
                    self.exit_ball_vel = curr_ball_vel.copy()

        # Check termination condition:
        ball_y = self.data.qpos[self.ball_qpos_adr+1]
        terminated = False
        if self.has_contacted:
            if (self.current_step - self.contact_step) >= 6 or ball_y > 4.0:
                terminated = True
        elif ball_y < -0.7:
            terminated = True
        elif self.current_step >= self.max_steps:
            terminated = True

        truncated = (self.current_step >= self.max_steps) and not terminated

        # Reward Computation
        reward, info = self._compute_reward(action)

        self.prev_action = action.copy()
        return self._get_obs(), reward, terminated, truncated, info

    def _compute_reward(self, action):
        reward = 0.0
        info = {
            "contact": self.has_contacted,
            "fair_hit": self.is_fair_hit,
            "min_sweet_dist_cm": self.min_ball_sweet_dist * 100.0,
            "exit_speed_ms": 0.0,
            "exit_azimuth_deg": 0.0,
            "exit_launch_deg": 0.0,
            "sweet_spot_offset_cm": 99.0,
            "azimuth_error_deg": 99.0,
            "launch_error_deg": 99.0,
        }

        # 1. Dense Approach Shaping Reward (continuous guidance towards ball)
        r_approach = float(np.exp(-8.0 * self.min_ball_sweet_dist))
        reward += r_approach

        # 2. Bat-Ball Contact & Precision Trajectory Evaluation (awarded once upon confirmed contact)
        if self.has_contacted and not self.contact_reward_given and self.exit_ball_vel is not None:
            self.contact_reward_given = True
            
            # Base Contact Bonus
            r_contact = 6.0

            # Sweet Spot Precision Contact
            sweet_offset = float(np.linalg.norm(self.contact_sweet_pos - self.contact_ball_pos))
            info["sweet_spot_offset_cm"] = sweet_offset * 100.0
            r_sweet = 5.0 * float(np.exp(-20.0 * sweet_offset))

            vx, vy, vz = self.exit_ball_vel
            exit_speed = float(np.linalg.norm(self.exit_ball_vel))
            info["exit_speed_ms"] = exit_speed
            self.exit_velocity = exit_speed

            if self.is_fair_hit and vy > 0.05:
                # Solid Fair Ball Forward Rebound Bonus
                r_forward = 10.0

                # Spray Azimuth: negative = Left field (Pull), positive = Right field (Push)
                azimuth_rad = float(np.arctan2(vx, vy))
                azimuth_deg = float(np.degrees(azimuth_rad))
                info["exit_azimuth_deg"] = azimuth_deg
                self.exit_azimuth_deg = azimuth_deg

                # Launch Angle: relative to horizontal
                ground_speed = float(np.hypot(vx, vy))
                launch_rad = float(np.arctan2(vz, max(0.1, ground_speed)))
                launch_deg = float(np.degrees(launch_rad))
                info["exit_launch_deg"] = launch_deg
                self.exit_launch_deg = launch_deg

                # Directional Hitting Goal-Conditioning Reward
                azimuth_err_rad = abs(azimuth_rad - self.target_azimuth_rad)
                info["azimuth_error_deg"] = float(np.degrees(azimuth_err_rad))
                # Gaussian + linear gradient support
                r_azimuth = 10.0 * float(np.exp(-0.5 * (azimuth_err_rad / 0.35) ** 2)) + \
                            5.0 * float(max(0.0, 1.0 - azimuth_err_rad / 1.0))

                # Sector Matching Milestone Bonus
                target_deg = float(np.degrees(self.target_azimuth_rad))
                r_sector = 0.0
                if target_deg < -10.0 and azimuth_deg < -10.0:
                    r_sector = 5.0
                elif target_deg > 10.0 and azimuth_deg > 10.0:
                    r_sector = 5.0
                elif abs(target_deg) <= 10.0 and abs(azimuth_deg) <= 10.0:
                    r_sector = 5.0

                # Launch Angle Goal-Conditioning Reward
                launch_err_rad = abs(launch_rad - self.target_launch_rad)
                info["launch_error_deg"] = float(np.degrees(launch_err_rad))
                # Gaussian + linear gradient support
                r_launch = 8.0 * float(np.exp(-0.5 * (launch_err_rad / 0.25) ** 2)) + \
                           4.0 * float(max(0.0, 1.0 - launch_err_rad / 0.6))

                # Exit Velocity Modulation Reward
                r_vel = 5.0 * float(np.clip(exit_speed / max(1.0, self.target_exit_vel), 0.0, 1.5))

                reward += (r_contact + r_sweet + r_forward + r_azimuth + r_sector + r_launch + r_vel)
            else:
                # Foul tip or backward deflection penalty
                reward += (r_contact + r_sweet - 3.0)
                info["exit_azimuth_deg"] = -90.0
                info["exit_launch_deg"] = -30.0

        # Maintain info metrics for active contact
        if self.has_contacted and self.exit_ball_vel is not None:
            info["contact"] = True
            info["fair_hit"] = self.is_fair_hit
            info["exit_speed_ms"] = self.exit_velocity
            info["exit_azimuth_deg"] = self.exit_azimuth_deg
            info["exit_launch_deg"] = self.exit_launch_deg
            if self.is_fair_hit:
                info["azimuth_error_deg"] = abs(self.exit_azimuth_deg - np.degrees(self.target_azimuth_rad))
                info["launch_error_deg"] = abs(self.exit_launch_deg - np.degrees(self.target_launch_rad))
            if self.contact_sweet_pos is not None and self.contact_ball_pos is not None:
                info["sweet_spot_offset_cm"] = float(np.linalg.norm(self.contact_sweet_pos - self.contact_ball_pos)) * 100.0

        # 3. Regularization & Action Smoothness Penalty
        action_penalty = 0.01 * float(np.sum(action ** 2))
        action_rate_penalty = 0.02 * float(np.sum((action - self.prev_action) ** 2))
        reward -= (action_penalty + action_rate_penalty)

        return reward, info

    def render(self):
        if self.render_mode == "rgb_array":
            self.renderer.update_scene(self.data, camera="broadcast_cam")
            return self.renderer.render()
        elif self.render_mode == "human":
            pass

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
