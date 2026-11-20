"""
PitcherPrecisionEnv: Goal-Conditioned Humanoid Pitcher Precision Environment for Unitree H1.
Features:
- Full 19-DoF H1 pitching kinematics with athletic mound stance.
- True PD motor torque control with rated actuator saturation clipping.
- Goal-conditioned 9-grid strike zone target tracking (High/Mid/Low x Inside/Center/Outside).
- 3 distinct pitch repertoires: 4-seam Fastball, Slider, Curveball with aerodynamic drag and Magnus force.
- Continuous action space modulating release timing, 3D aiming angles, and pitch speed.
"""

import os
import sys
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import mujoco

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


class PitcherPrecisionEnv(gym.Env):
    """
    Goal-Conditioned Humanoid Pitcher Precision Environment.

    Observation Space (23 dims):
      [0:2]   Target strike zone coordinate over home plate [target_x, target_z] (m)
      [2:5]   Target pitch type one-hot: [Fastball, Slider, Curveball]
      [5:8]   Current ball position [x, y, z] (m)
      [8:11]  Current ball velocity [vx, vy, vz] (m/s)
      [11:14] Pitcher hand site position [x, y, z] (m)
      [14:17] Pitcher hand site velocity [vx, vy, vz] (m/s)
      [17:22] Pitching arm joint positions [torso, rsp, rsr, rsy, relb] (rad)
      [22]    Throw progress (0.0 to 1.0)

    Action Space (4 dims, continuous in [-1, 1]):
      a[0]: Release timing offset: dt in [-0.030, +0.030] s
      a[1]: Horizontal aim course: dx in [-0.15, +0.15] m
      a[2]: Vertical elevation aim: dz in [-0.12, +0.12] m
      a[3]: Arm acceleration / velocity scaling: dv in [-0.15, +0.15]
    """

    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}

    def __init__(
        self,
        xml_path=None,
        render_mode=None,
        frame_skip=5,  # 5 * 0.002s = 0.010s per step (100 Hz control)
        mound_y=10.0,
    ):
        super().__init__()

        if xml_path is None:
            xml_path = os.path.join(parent_dir, "models", "h1_pitcher.xml")

        self.xml_path = xml_path
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)

        self.render_mode = render_mode
        self.frame_skip = frame_skip
        self.dt = self.model.opt.timestep * self.frame_skip
        self.mound_y = mound_y

        # Geoms & Sites
        self.hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "pitcher_hand_site")
        self.target_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "pitch_target_point")
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.weld_eq_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_EQUALITY, "ball_weld")

        # Freejoint for ball
        ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
        self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]

        # Pitching joints and actuators: [torso, rsp, rsr, rsy, relb]
        self.pitch_actuator_names = [
            "torso",
            "right_shoulder_pitch",
            "right_shoulder_roll",
            "right_shoulder_yaw",
            "right_elbow",
        ]
        self.act_ids = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
            for name in self.pitch_actuator_names
        ]
        self.jnt_ids = [self.model.actuator_trnid[a, 0] for a in self.act_ids]
        self.qpos_adrs = [self.model.jnt_qposadr[j] for j in self.jnt_ids]
        self.qvel_adrs = [self.model.jnt_dofadr[j] for j in self.jnt_ids]

        # Leg joints for stance
        self.leg_joint_names = [
            "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
            "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
        ]
        self.leg_qpos_adrs = [
            self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)]
            for n in self.leg_joint_names
        ]

        # Canonical Pitching Keyframes
        # [torso, rsp, rsr, rsy, relb]
        self.base_keyframes = np.array([
            [ 0.00,  0.00, -0.40,  0.00,  1.50],  # 0: Set (glove at chest)
            [ 0.80,  1.20, -0.60,  0.80,  1.60],  # 1: Cocking (back & up)
            [ 0.20, -0.20, -0.40,  0.30,  1.00],  # 2: Acceleration
            [-0.50, -1.40, -0.20, -0.20,  0.20],  # 3: Release
            [-0.90, -1.80, -0.60, -0.50,  0.70],  # 4: Follow-through
        ], dtype=np.float32)

        # PD Controller gains for Pitching Arm
        self.Kp = np.array([450.0, 350.0, 250.0, 150.0, 150.0], dtype=np.float32)
        self.Kd = np.array([35.0,  25.0,  20.0,  12.0,  12.0], dtype=np.float32)

        # Aerodynamic Constants
        self.rho = 1.205  # kg/m^3 (air density)
        self.r_ball = 0.037  # m (radius)
        self.m_ball = 0.145  # kg (mass)
        self.A_ball = np.pi * (self.r_ball ** 2)
        self.Cd = 0.32  # drag coefficient
        self.Cl = 0.24  # lift coefficient

        # Spaces
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(23,), dtype=np.float32)

        # State Variables
        self.current_step = 0
        self.max_steps = 100
        self.is_released = False
        self.release_step = -1
        self.release_speed_ms = 0.0
        self.release_speed_kmh = 0.0
        self.reached_plate = False
        self.plate_crossing_pos = None
        self.plate_crossing_vel = None
        self.min_dist_to_target = 999.0
        self.prev_action = np.zeros(4, dtype=np.float32)

        self.renderer = None
        if self.render_mode in ["rgb_array", "human"]:
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)

    def _set_pitcher_stance(self):
        """Sets a firm athletic pitcher mound stance."""
        for n, adr in zip(self.leg_joint_names, self.leg_qpos_adrs):
            if "left_hip_pitch" in n:
                self.data.qpos[adr] = -0.30
            elif "left_knee" in n:
                self.data.qpos[adr] = 0.50
            elif "right_hip_pitch" in n:
                self.data.qpos[adr] = 0.10
            elif "right_knee" in n:
                self.data.qpos[adr] = 0.20
            elif "yaw" in n or "roll" in n or "ankle" in n:
                self.data.qpos[adr] = 0.0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        self.current_step = 0
        self.is_released = False
        self.release_step = -1
        self.release_speed_ms = 0.0
        self.release_speed_kmh = 0.0
        self.reached_plate = False
        self.plate_crossing_pos = None
        self.plate_crossing_vel = None
        self.min_dist_to_target = 999.0
        self.prev_action = np.zeros(4, dtype=np.float32)

        # 1. Sample 9-Grid Strike Zone Target
        # Grid X: [-0.15, +0.15], Grid Z: [0.68, 0.92]
        self.target_x = float(self.np_random.uniform(-0.15, 0.15))
        self.target_z = float(self.np_random.uniform(0.68, 0.92))

        # Update visual target marker
        if self.target_site_id >= 0:
            self.model.site_pos[self.target_site_id] = [self.target_x, 0.0, self.target_z]

        # 2. Sample Pitch Type
        # 0: Fastball, 1: Slider, 2: Curveball
        self.pitch_type = int(self.np_random.integers(0, 3))
        self.pitch_one_hot = np.zeros(3, dtype=np.float32)
        self.pitch_one_hot[self.pitch_type] = 1.0

        # Base nominal velocity and spin according to pitch type
        if self.pitch_type == 0:
            # 4-Seam Fastball: 75 ~ 88 km/h (21 ~ 24.5 m/s), backspin
            self.nominal_speed = float(self.np_random.uniform(21.0, 24.0))
            self.nominal_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
        elif self.pitch_type == 1:
            # Slider: 68 ~ 78 km/h (19 ~ 21.6 m/s), lateral break
            self.nominal_speed = float(self.np_random.uniform(19.0, 21.5))
            self.nominal_spin = np.array([-30.0, 0.0, 150.0], dtype=np.float32)
        else:
            # Curveball: 60 ~ 70 km/h (16.7 ~ 19.5 m/s), 12-to-6 drop
            self.nominal_speed = float(self.np_random.uniform(17.0, 19.5))
            self.nominal_spin = np.array([170.0, 0.0, -20.0], dtype=np.float32)

        # Setup stance and arm initial keyframe
        self._set_pitcher_stance()
        for i, adr in enumerate(self.qpos_adrs):
            self.data.qpos[adr] = self.base_keyframes[0, i]

        # Activate weld constraint to pitcher hand
        if self.weld_eq_id >= 0:
            self.data.eq_active[self.weld_eq_id] = True

        mujoco.mj_forward(self.model, self.data)

        # Sync ball initial position to hand site
        hand_pos = self.data.site_xpos[self.hand_site_id]
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
        self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+6] = 0.0

        mujoco.mj_forward(self.model, self.data)

        return self._get_obs(), {}

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        hand_pos = self.data.site_xpos[self.hand_site_id]

        hand_v = np.zeros(6, dtype=np.float64)
        mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_SITE, self.hand_site_id, hand_v, 0)
        hand_vel = hand_v[3:6]

        arm_qpos = np.array([self.data.qpos[adr] for adr in self.qpos_adrs], dtype=np.float32)
        progress = float(self.current_step / self.max_steps)

        obs = np.concatenate([
            np.array([self.target_x, self.target_z], dtype=np.float32),  # 2
            self.pitch_one_hot,                                          # 3
            ball_pos,                                                    # 3
            ball_vel,                                                    # 3
            hand_pos,                                                    # 3
            hand_vel,                                                    # 3
            arm_qpos,                                                    # 5
            np.array([progress], dtype=np.float32),                       # 1
        ])
        return obs.astype(np.float32)

    def step(self, action):
        action = np.clip(action, -1.0, 1.0).astype(np.float32)

        # Action modulations:
        # a[0]: release timing offset [-0.030, +0.030] s
        # a[1]: horizontal aim course [-0.15, +0.15] m
        # a[2]: vertical elevation aim [-0.12, +0.12] m
        # a[3]: speed scale [-0.15, +0.15]
        dt_rel = float(action[0]) * 0.030
        dx_aim = float(action[1]) * 0.15
        dz_aim = float(action[2]) * 0.12
        dv_scale = float(action[3]) * 0.15

        nominal_release_step = 22
        actual_release_step = int(np.clip(nominal_release_step + int(dt_rel / self.dt), 18, 26))

        # Modulate Keyframes for aiming
        kfs = self.base_keyframes.copy()
        kfs[2, 0] += dx_aim * 0.5
        kfs[3, 0] += dx_aim * 1.0
        kfs[3, 1] += dz_aim * 1.2
        kfs[3, 2] += dx_aim * 0.3

        substep_dt = self.model.opt.timestep  # 0.002s

        for _ in range(self.frame_skip):
            # 1. Interpolate keyframes for arm motion
            t_norm = self.current_step / actual_release_step
            if t_norm < 0.35:
                w = t_norm / 0.35
                q_target = (1 - w) * kfs[0] + w * kfs[1]
            elif t_norm < 0.70:
                w = (t_norm - 0.35) / 0.35
                q_target = (1 - w) * kfs[1] + w * kfs[2]
            elif t_norm <= 1.0:
                w = (t_norm - 0.70) / 0.30
                q_target = (1 - w) * kfs[2] + w * kfs[3]
            else:
                w = min(1.0, (t_norm - 1.0) / 0.40)
                q_target = (1 - w) * kfs[3] + w * kfs[4]

            # 2. Low-Level PD Motor Torque with Saturation
            for i in range(5):
                q = self.data.qpos[self.qpos_adrs[i]]
                dq = self.data.qvel[self.qvel_adrs[i]]
                tau = self.Kp[i] * (q_target[i] - q) - self.Kd[i] * dq
                ctrlrange = self.model.actuator_ctrlrange[self.act_ids[i]]
                self.data.ctrl[self.act_ids[i]] = np.clip(tau, ctrlrange[0], ctrlrange[1])

            # 3. Release Ball at Release Step
            if not self.is_released and self.current_step >= actual_release_step:
                self.is_released = True
                self.release_step = self.current_step
                if self.weld_eq_id >= 0:
                    self.data.eq_active[self.weld_eq_id] = False

                # Desired target coordinates at home plate (y = 0.0m)
                tx = self.target_x + dx_aim
                tz = self.target_z + dz_aim
                speed = self.nominal_speed * (1.0 + dv_scale)

                curr_hand_pos = self.data.site_xpos[self.hand_site_id]
                x0, y0, z0 = curr_hand_pos[0], curr_hand_pos[1], curr_hand_pos[2]
                dy = y0 - 0.0
                t_f = dy / speed
                vy = -speed
                vx = (tx - x0) / t_f

                # Gravity drop compensation
                drop = 0.5 * 9.81 * (t_f ** 2)
                vz = (tz + drop - z0) / t_f

                # Calibrated baseline and aerodynamic spin compensation
                vx -= 0.14
                if self.pitch_type == 0:  # Fastball backspin lifts the ball
                    vz += 0.13
                elif self.pitch_type == 1:  # Slider breaks right (+X)
                    vx -= 0.12
                elif self.pitch_type == 2:  # Curveball drops down (-Z)
                    vz += 0.05

                self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
                self.release_speed_ms = float(np.linalg.norm([vx, vy, vz]))
                self.release_speed_kmh = float(self.release_speed_ms * 3.6)

            # 4. Aerodynamic Drag and Magnus Forces in Flight
            if self.is_released:
                v = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                v_norm = np.linalg.norm(v)
                if v_norm > 1.0:
                    f_drag = -0.5 * self.rho * self.Cd * self.A_ball * v_norm * v
                    f_magnus = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.nominal_spin, v)
                    a_aero = (f_drag + f_magnus) / self.m_ball
                    self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += a_aero * substep_dt

            mujoco.mj_step(self.model, self.data)

            # Check Home Plate crossing
            ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
            if ball_pos[1] <= 0.0 and not self.reached_plate and self.is_released:
                self.reached_plate = True
                self.plate_crossing_pos = ball_pos.copy()
                self.plate_crossing_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
                dist = np.sqrt((ball_pos[0] - self.target_x)**2 + (ball_pos[2] - self.target_z)**2)
                self.min_dist_to_target = float(dist)

        self.current_step += 1
        obs = self._get_obs()

        terminated = False
        truncated = False
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]

        if self.reached_plate:
            terminated = True
        elif ball_pos[2] <= 0.04 and self.is_released:  # Dirt pitch
            terminated = True
        elif self.current_step >= self.max_steps:
            truncated = True

        # Reward Calculation
        reward = 0.0
        info = {
            "target_x": self.target_x,
            "target_z": self.target_z,
            "pitch_type": self.pitch_type,
            "is_released": self.is_released,
            "release_speed_kmh": self.release_speed_kmh,
            "reached_plate": self.reached_plate,
            "min_dist_to_target": self.min_dist_to_target,
            "is_strike": False,
        }

        if terminated and self.reached_plate:
            dist = self.min_dist_to_target
            # Dense Gaussian target reward (sigma = 7 cm)
            r_target = 18.0 * np.exp(- (dist ** 2) / (2.0 * (0.07 ** 2)))
            # Linear guide gradient
            r_linear = np.clip(1.0 - dist / 0.25, -1.0, 1.0) * 10.0

            # Strike zone check: official MLB width 17 in (+/- 0.216m), height [0.65, 0.95]
            is_strike = (abs(self.plate_crossing_pos[0]) <= 0.216) and (0.65 <= self.plate_crossing_pos[2] <= 0.95)
            r_strike = 15.0 if is_strike else -6.0
            info["is_strike"] = is_strike

            # Velocity bonus
            r_vel = 4.0 * np.clip(self.release_speed_kmh / 80.0, 0.5, 1.2)

            reward += r_target + r_linear + r_strike + r_vel
            info["dist_error_cm"] = float(dist * 100.0)
        elif terminated and not self.reached_plate:
            reward -= 20.0
            info["dist_error_cm"] = 99.0

        # Action regularizations
        reward -= 0.01 * float(np.sum(action ** 2))
        reward -= 0.02 * float(np.sum((action - self.prev_action) ** 2))
        self.prev_action = action.copy()

        return obs, reward, terminated, truncated, info

    def render(self):
        if self.render_mode == "rgb_array" and self.renderer is not None:
            self.renderer.update_scene(self.data, camera="catcher_cam")
            return self.renderer.render()
        return None

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
