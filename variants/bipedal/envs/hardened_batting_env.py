"""
HardenedBattingEnv: Phase 2 Sim-to-Real Physically Hardened Batting Environment.
Features:
- Communication Latency Buffer (20ms EtherCAT delay queue).
- Strict rated motor torque saturation clipping on all H1 joints (Arm: 18-40 N*m, Torso: 200 N*m).
- Domain Randomization:
  * Bat mass variation (+/- 10%: 0.81 ~ 0.99 kg)
  * Ball restitution variation (COR damping jitter)
  * Vision observation sensor noise (Gaussian jitter on ball tracking)
  * Pitch velocity and course perturbations
- Forward fair-ball contact tracking and goal-conditioned directional control.
"""

import os
import sys
import collections
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import mujoco

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


class HardenedBattingEnv(gym.Env):
    """
    Phase 2 Sim-to-Real Physically Hardened Batting Environment.
    Incorporates latency buffers, strict hardware torque limits, and domain randomization.
    """

    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}

    def __init__(
        self,
        xml_path=None,
        render_mode=None,
        frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz control)
        pitch_speed_range=(14.0, 19.0),
        pitch_dist=7.5,
        latency_steps=1,  # 1 step delay = 20ms
        enable_domain_randomization=True,
    ):
        super().__init__()

        if xml_path is None:
            xml_path = os.path.join(parent_dir, "models", "h1_baseball.xml")

        self.xml_path = xml_path
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        
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
        self.latency_steps = latency_steps
        self.enable_domain_randomization = enable_domain_randomization

        # Identify Geoms & Sites
        self.bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "bat")
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

        # Base nominal bat mass
        self.nominal_bat_mass = float(self.model.body_mass[self.bat_body_id]) if self.bat_body_id >= 0 else 0.90

        # State Variables
        self.current_step = 0
        self.max_steps = 35
        self.action_queue = collections.deque(maxlen=self.latency_steps + 1)
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

        self.renderer = None
        if self.render_mode in ["rgb_array", "human"]:
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)

    def _set_athletic_leg_crouch(self):
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
        self.action_queue.clear()
        for _ in range(self.latency_steps + 1):
            self.action_queue.append(np.zeros(5, dtype=np.float32))

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

        # Domain Randomization
        if self.enable_domain_randomization:
            # 1. Bat mass randomization (+/- 10%)
            mass_scale = float(self.np_random.uniform(0.90, 1.10))
            if self.bat_body_id >= 0:
                self.model.body_mass[self.bat_body_id] = self.nominal_bat_mass * mass_scale

            # 2. Contact restitution jitter
            if hasattr(self.model, 'pair_solimp') and self.model.npair > 0:
                self.model.pair_solimp[0, 0] = float(self.np_random.uniform(0.93, 0.97))

        self._set_athletic_leg_crouch()

        for i, qadr in enumerate(self.qpos_adrs):
            self.data.qpos[qadr] = self.base_keyframes[0, i]

        # Target Goal Vector
        target_azimuth_deg = self.np_random.uniform(-35.0, 35.0)
        self.target_azimuth_rad = float(np.radians(target_azimuth_deg))

        target_launch_deg = self.np_random.uniform(12.0, 32.0)
        self.target_launch_rad = float(np.radians(target_launch_deg))

        self.target_exit_vel = float(self.np_random.uniform(10.0, 18.0))

        # Sample Pitched Ball
        pitch_speed = self.np_random.uniform(*self.pitch_speed_range)
        vy = -pitch_speed
        
        plate_y_contact = 0.22
        t_flight = (self.pitch_dist - plate_y_contact) / abs(vy)
        self.nominal_t_flight = t_flight

        target_x = self.np_random.uniform(0.10, 0.16)
        target_z = self.np_random.uniform(0.74, 0.78)

        z0 = 0.85
        drop = 0.5 * 9.81 * (t_flight ** 2)
        vz = (target_z + drop - z0) / t_flight

        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [target_x, self.pitch_dist, z0]
        self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, vy, vz]
        self.data.qvel[self.ball_qvel_adr+3:self.ball_qvel_adr+6] = [0.0, 0.0, 0.0]

        mujoco.mj_forward(self.model, self.data)

        self.nominal_t_trigger = t_flight - 0.126
        self.nominal_swing_duration = 0.17

        return self._get_obs(), {}

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()

        # Add Gaussian vision sensor observation noise in domain randomization
        if self.enable_domain_randomization:
            ball_pos += self.np_random.normal(0.0, 0.003, size=3)
            ball_vel += self.np_random.normal(0.0, 0.05, size=3)
        
        y_pos = ball_pos[1]
        vy = ball_vel[1]
        t_remain = max(0.0, (y_pos - 0.20) / abs(vy)) if abs(vy) > 1.0 else 0.0

        goals = np.array([
            self.target_azimuth_rad,
            self.target_launch_rad,
            self.target_exit_vel,
        ], dtype=np.float32)

        swing_qpos = np.array([self.data.qpos[adr] for adr in self.qpos_adrs], dtype=np.float32)
        swing_qvel = np.array([self.data.qvel[adr] for adr in self.qvel_adrs], dtype=np.float32)

        sweet_pos = self.data.site_xpos[self.sweet_spot_id]
        sweet_v = np.zeros(6, dtype=np.float64)
        mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_SITE, self.sweet_spot_id, sweet_v, 0)
        sweet_vel = sweet_v[3:6]

        obs = np.concatenate([
            ball_pos,                                    # 3
            ball_vel,                                    # 3
            np.array([t_remain], dtype=np.float32),      # 1
            goals,                                       # 3
            swing_qpos,                                  # 5
            swing_qvel,                                  # 5
            sweet_pos,                                   # 3
            sweet_vel,                                   # 3
            self.prev_action,                            # 5
        ])
        return obs.astype(np.float32)

    def step(self, action):
        action = np.clip(action, -1.0, 1.0).astype(np.float32)

        # 1. Latency Buffer Queue: Push current action, pop delayed action
        self.action_queue.append(action)
        delayed_action = self.action_queue.popleft()

        # EMA action filter for physical smoothness
        self.filtered_action = 0.6 * self.filtered_action + 0.4 * delayed_action

        # Decompose action
        dt_lead_lag = float(self.filtered_action[0]) * 0.030
        dz_bat = float(self.filtered_action[1]) * 0.08
        dalpha_plane = float(self.filtered_action[2]) * 0.15
        dpower_dur = float(self.filtered_action[3]) * 0.02
        delbow_reach = float(self.filtered_action[4]) * 0.15

        current_time = self.current_step * self.dt

        if not self.swing_triggered:
            candidate_trigger = self.nominal_t_trigger + dt_lead_lag
            if current_time >= candidate_trigger:
                self.swing_triggered = True
                self.locked_t_trigger = candidate_trigger
                self.locked_swing_duration = max(0.12, self.nominal_swing_duration + dpower_dur)

        kfs = self.base_keyframes.copy()
        kfs[3, 1] += dz_bat * 0.6
        kfs[3, 2] += dalpha_plane * 0.6
        kfs[3, 4] += delbow_reach * 0.6

        kfs[4, 1] += dz_bat * 1.0
        kfs[4, 2] += dalpha_plane * 1.0
        kfs[4, 4] += delbow_reach * 1.0

        kfs[5, 1] += dz_bat * 0.5
        kfs[5, 2] += dalpha_plane * 0.5

        for _ in range(self.frame_skip):
            self._set_athletic_leg_crouch()

            if not self.swing_triggered:
                q_target = kfs[0]
            else:
                elapsed_swing = current_time - self.locked_t_trigger
                prog = elapsed_swing / self.locked_swing_duration

                if prog < 0.20:
                    w = prog / 0.20
                    q_target = (1.0 - w) * kfs[0] + w * kfs[1]
                elif prog < 0.45:
                    w = (prog - 0.20) / 0.25
                    q_target = (1.0 - w) * kfs[1] + w * kfs[2]
                elif prog < 0.70:
                    w = (prog - 0.45) / 0.25
                    q_target = (1.0 - w) * kfs[2] + w * kfs[3]
                elif prog < 0.90:
                    w = (prog - 0.70) / 0.20
                    q_target = (1.0 - w) * kfs[3] + w * kfs[4]
                else:
                    w = min(1.0, (prog - 0.90) / 0.30)
                    q_target = (1.0 - w) * kfs[4] + w * kfs[5]

            # Low-Level PD Motor Torques with Strict Saturation
            for i in range(5):
                q = self.data.qpos[self.qpos_adrs[i]]
                dq = self.data.qvel[self.qvel_adrs[i]]
                tau = self.Kp[i] * (q_target[i] - q) - self.Kd[i] * dq
                ctrlrange = self.model.actuator_ctrlrange[self.act_ids[i]]
                self.data.ctrl[self.act_ids[i]] = np.clip(tau, ctrlrange[0], ctrlrange[1])

            mujoco.mj_step(self.model, self.data)

            # Contact detection
            for c_idx in range(self.data.ncon):
                con = self.data.contact[c_idx]
                g1, g2 = con.geom1, con.geom2
                if (g1 == self.bat_geom_id and g2 == self.ball_geom_id) or \
                   (g2 == self.bat_geom_id and g1 == self.ball_geom_id):
                    if not self.has_contacted:
                        self.has_contacted = True
                        self.contact_step = self.current_step
                        self.contact_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
                        self.contact_sweet_pos = self.data.site_xpos[self.sweet_spot_id].copy()

            ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
            sweet_pos = self.data.site_xpos[self.sweet_spot_id]
            dist = float(np.linalg.norm(ball_pos - sweet_pos))
            if dist < self.min_ball_sweet_dist:
                self.min_ball_sweet_dist = dist

        self.current_step += 1
        obs = self._get_obs()

        terminated = False
        truncated = False

        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]

        if self.has_contacted and self.current_step >= self.contact_step + 4:
            self.exit_ball_vel = ball_vel.copy()
            vx, vy, vz = self.exit_ball_vel
            speed = float(np.linalg.norm([vx, vy, vz]))
            self.exit_velocity = speed

            if vy > 0.10:
                self.is_fair_hit = True
                self.exit_azimuth_deg = float(np.degrees(np.arctan2(vx, vy)))
                v_horiz = np.sqrt(vx**2 + vy**2)
                self.exit_launch_deg = float(np.degrees(np.arctan2(vz, v_horiz)))
            else:
                self.is_fair_hit = False
                self.exit_azimuth_deg = float(np.degrees(np.arctan2(vx, max(0.1, vy))))
                self.exit_launch_deg = -30.0

            terminated = True
        elif ball_pos[1] < -0.8:
            terminated = True
        elif self.current_step >= self.max_steps:
            truncated = True

        reward = 0.0
        r_approach = float(np.exp(-12.0 * self.min_ball_sweet_dist))
        reward += r_approach

        info = {
            "contact": self.has_contacted,
            "fair_hit": self.is_fair_hit,
            "min_dist_cm": float(self.min_ball_sweet_dist * 100.0),
            "exit_speed_ms": float(self.exit_velocity),
            "exit_speed_kmh": float(self.exit_velocity * 3.6),
            "azimuth_deg": float(self.exit_azimuth_deg),
            "launch_deg": float(self.exit_launch_deg),
            "target_azimuth_deg": float(np.degrees(self.target_azimuth_rad)),
            "target_launch_deg": float(np.degrees(self.target_launch_rad)),
        }

        if terminated and self.has_contacted and not self.contact_reward_given:
            self.contact_reward_given = True
            r_contact = 12.0

            sweet_offset = float(np.linalg.norm(self.contact_ball_pos - self.contact_sweet_pos))
            info["sweet_spot_offset_cm"] = float(sweet_offset * 100.0)
            r_sweet = 8.0 * float(np.exp(-25.0 * sweet_offset))

            r_fair = 0.0
            r_azimuth = 0.0
            r_launch = 0.0
            r_vel = 0.0

            if self.is_fair_hit:
                r_fair = 10.0
                actual_az_rad = np.radians(self.exit_azimuth_deg)
                az_err = abs(actual_az_rad - self.target_azimuth_rad)
                info["azimuth_error_deg"] = float(np.degrees(az_err))

                sigma_az = 0.35
                r_az_gauss = np.exp(- (az_err ** 2) / (2.0 * (sigma_az ** 2)))
                r_az_lin = max(0.0, 1.0 - az_err / 1.0)
                r_azimuth = 8.0 * (0.6 * r_az_gauss + 0.4 * r_az_lin)

                target_deg = np.degrees(self.target_azimuth_rad)
                actual_deg = self.exit_azimuth_deg
                target_sector = "pull" if target_deg < -10 else ("push" if target_deg > 10 else "center")
                actual_sector = "pull" if actual_deg < -10 else ("push" if actual_deg > 10 else "center")
                if target_sector == actual_sector:
                    r_azimuth += 5.0
                    info["sector_matched"] = True

                actual_la_rad = np.radians(self.exit_launch_deg)
                la_err = abs(actual_la_rad - self.target_launch_rad)
                info["launch_error_deg"] = float(np.degrees(la_err))

                sigma_la = 0.25
                r_la_gauss = np.exp(- (la_err ** 2) / (2.0 * (sigma_la ** 2)))
                r_la_lin = max(0.0, 1.0 - la_err / 0.8)
                r_launch = 5.0 * (0.6 * r_la_gauss + 0.4 * r_la_lin)

                r_vel = 4.0 * float(np.clip(self.exit_velocity / 12.0, 0.0, 1.5))
            else:
                r_fair = -10.0
                info["azimuth_error_deg"] = 99.0
                info["launch_error_deg"] = 99.0

            reward += r_contact + r_sweet + r_fair + r_azimuth + r_launch + r_vel

        reward -= 0.015 * float(np.sum(action ** 2))
        reward -= 0.030 * float(np.sum((action - self.prev_action) ** 2))
        self.prev_action = action.copy()

        return obs, reward, terminated, truncated, info

    def render(self):
        if self.render_mode == "rgb_array" and self.renderer is not None:
            self.renderer.update_scene(self.data, camera="broadcast_cam")
            return self.renderer.render()
        return None

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
