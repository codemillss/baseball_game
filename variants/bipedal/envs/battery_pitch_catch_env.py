import os
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import mujoco

class BatteryPitchCatchEnv(gym.Env):
    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}

    def __init__(self, render_mode=None):
        super().__init__()
        self.render_mode = render_mode

        model_path = os.path.abspath("models/h1_battery_pitch_catch.xml")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        self.model = mujoco.MjModel.from_xml_path(model_path)
        self.data = mujoco.MjData(self.model)

        self.frame_skip = 10
        self.dt = self.model.opt.timestep * self.frame_skip

        self.pitch_types = [0, 1, 2]
        self.pitch_type = 0
        self.pitch_name = "Fastball"
        self.pitch_speed = 24.0
        self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
        self.actual_release_step = 2

        self.rho = 1.205
        self.r_ball = 0.037
        self.m_ball = 0.145
        self.A_ball = np.pi * (self.r_ball ** 2)
        self.Cd = 0.32
        self.Cl = 0.24

        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_qpos_adr = self.model.jnt_qposadr[self.ball_jnt_id]
        self.ball_qvel_adr = self.model.jnt_dofadr[self.ball_jnt_id]

        self.p_hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")
        self.c_mitt_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "c_mitt_site")
        self.strike_zone_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "strike_zone")

        self.c_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "c_pelvis_joint")
        self.c_pelvis_qpos_adr = self.model.jnt_qposadr[self.c_pelvis_jnt_id]
        self.c_pelvis_qvel_adr = self.model.jnt_dofadr[self.c_pelvis_jnt_id]

        self.p_act_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
        self.p_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.p_act_names]
        self.p_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]

        self.c_leg_act_names = [
            "c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle",
            "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle",
        ]
        self.c_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.c_leg_act_names]
        self.c_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.c_leg_act_ids]
        self.c_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.c_leg_act_ids]

        self.c_upper_act_names = [
            "c_torso",
            "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow",
            "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"
        ]
        self.c_upper_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.c_upper_act_names]
        self.c_upper_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.c_upper_act_ids]
        self.c_upper_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.c_upper_act_ids]

        self.c_leg_Kp = np.array([450.0, 450.0, 650.0, 750.0, 350.0, 450.0, 450.0, 650.0, 750.0, 350.0], dtype=np.float32)
        self.c_leg_Kd = np.array([35.0,  40.0,  55.0,  65.0,  28.0,  35.0,  40.0,  55.0,  65.0,  28.0], dtype=np.float32)

        self.c_upper_Kp = np.array([350.0, 150.0, 150.0, 100.0, 80.0, 150.0, 150.0, 100.0, 80.0], dtype=np.float32)
        self.c_upper_Kd = np.array([30.0,  15.0,  15.0,  10.0,  8.0,  15.0,  15.0,  10.0,  8.0], dtype=np.float32)

        self.q_squat_legs = np.array([
            0.00,  0.18, -1.15, 1.88, -0.75,
            0.00, -0.18, -1.15, 1.88, -0.75
        ], dtype=np.float32)

        self.q_squat_upper = np.array([
            0.00,
           -0.50, -0.30, -0.30, 0.20,
           -0.60, -0.20,  0.00, 1.50
        ], dtype=np.float32)

        self.p_keyframes = np.array([
            [ 0.20, -0.20, -0.40,  0.30,  1.00],
            [-0.50, -1.40, -0.20, -0.20,  0.20],
            [-0.90, -1.80, -0.60, -0.50,  0.70],
        ], dtype=np.float32)

        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(5,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(42,), dtype=np.float32)

        self.current_step = 0
        self.max_steps = 45
        self.is_released = False
        self.ball_caught = False
        self.catch_step = -1
        self.target_pitch_x = 0.0
        self.target_pitch_z = 0.85
        self.catcher_fallen = False
        self.plate_cross_z = 0.0
        self.plate_cross_x = 0.0
        self.plate_crossed = False
        self.is_strike = False
        self.framing_error = 0.0

        self.renderer = None
        if self.render_mode in ["rgb_array", "human"]:
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        self.current_step = 0
        self.is_released = False
        self.ball_caught = False
        self.catch_step = -1
        self.catcher_fallen = False
        self.plate_crossed = False
        self.is_strike = False
        self.framing_error = 0.0

        for i, adr in enumerate(self.p_qpos_adrs):
            self.data.qpos[adr] = self.p_keyframes[0, i]

        self.data.qpos[self.c_pelvis_qpos_adr:self.c_pelvis_qpos_adr+3] = [0.0, -0.95, 0.55]
        self.data.qpos[self.c_pelvis_qpos_adr+3:self.c_pelvis_qpos_adr+7] = [0.7071068, 0.0, 0.0, 0.7071068]
        self.data.qvel[self.c_pelvis_qvel_adr:self.c_pelvis_qvel_adr+6] = 0.0

        for i, adr in enumerate(self.c_leg_qpos_adrs):
            self.data.qpos[adr] = self.q_squat_legs[i]

        for i, adr in enumerate(self.c_upper_qpos_adrs):
            self.data.qpos[adr] = self.q_squat_upper[i]

        self.pitch_type = int(self.np_random.choice(self.pitch_types))

        if self.pitch_type == 0:
            self.pitch_name = "Fastball"
            self.pitch_speed = float(self.np_random.uniform(23.6, 24.6))
            self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
            self.target_pitch_x = float(self.np_random.uniform(-0.12, 0.12))
            self.target_pitch_z = float(self.np_random.uniform(0.82, 0.94))
            self.actual_release_step = 2
        elif self.pitch_type == 1:
            self.pitch_name = "Slider"
            self.pitch_speed = float(self.np_random.uniform(21.2, 22.2))
            self.pitch_spin = np.array([-30.0, 0.0, 150.0], dtype=np.float32)
            self.target_pitch_x = float(self.np_random.uniform(0.02, 0.15))
            self.target_pitch_z = float(self.np_random.uniform(0.72, 0.85))
            self.actual_release_step = 1
        else:
            self.pitch_name = "Curveball"
            self.pitch_speed = float(self.np_random.uniform(19.8, 20.8))
            self.pitch_spin = np.array([170.0, 0.0, -20.0], dtype=np.float32)
            self.target_pitch_x = float(self.np_random.uniform(-0.08, 0.08))
            self.target_pitch_z = float(self.np_random.uniform(0.68, 0.78))
            self.actual_release_step = 0

        mujoco.mj_forward(self.model, self.data)
        hand_pos = self.data.site_xpos[self.p_hand_site_id].copy()
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
        self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+6] = 0.0
        mujoco.mj_forward(self.model, self.data)

        return self._get_obs(), {}

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()

        if self.is_released and abs(ball_vel[1]) > 1.0 and ball_pos[1] > -0.90:
            t_remain = float((ball_pos[1] - (-0.90)) / abs(ball_vel[1]))
        elif not self.is_released:
            t_remain = float(10.0 / self.pitch_speed)
        else:
            t_remain = 0.0

        c_pos = self.data.qpos[self.c_pelvis_qpos_adr:self.c_pelvis_qpos_adr+3].copy()
        c_quat = self.data.qpos[self.c_pelvis_qpos_adr+3:self.c_pelvis_qpos_adr+7].copy()
        c_vel = self.data.qvel[self.c_pelvis_qvel_adr:self.c_pelvis_qvel_adr+3].copy()
        c_angvel = self.data.qvel[self.c_pelvis_qvel_adr+3:self.c_pelvis_qvel_adr+6].copy()

        mitt_pos = self.data.site_xpos[self.c_mitt_site_id].copy()
        mitt_vel = np.zeros(3, dtype=np.float32)

        target_pos = np.array([self.target_pitch_x, 0.0, self.target_pitch_z], dtype=np.float32)

        leg_q = [self.data.qpos[adr] for adr in self.c_leg_qpos_adrs]
        torso_q = [self.data.qpos[self.c_upper_qpos_adrs[0]]]
        arm_q = [self.data.qpos[self.c_upper_qpos_adrs[1]], self.data.qpos[self.c_upper_qpos_adrs[4]]]
        c_joint_q = np.array(leg_q + torso_q + arm_q, dtype=np.float32)

        obs = np.concatenate([
            ball_pos,
            ball_vel,
            np.array([t_remain], dtype=np.float32),
            c_pos,
            c_quat,
            c_vel,
            c_angvel,
            mitt_pos,
            mitt_vel,
            target_pos,
            c_joint_q
        ]).astype(np.float32)

        return obs

    def step(self, action):
        self.current_step += 1
        current_time = (self.current_step - 1) * self.dt

        dx_mitt = float(action[0]) * 0.18
        dz_mitt = float(action[1]) * 0.18
        dy_mitt = float(action[2]) * 0.08
        d_squat_z = float(action[3]) * 0.03
        d_tilt = float(action[4]) * 0.05

        if self.current_step < 2:
            p_pose = self.p_keyframes[0]
        elif self.current_step < 4:
            p_pose = self.p_keyframes[1]
        else:
            p_pose = self.p_keyframes[2]

        q_arm_tgt = self.q_squat_upper.copy()
        # Analytical Jacobian mapping covering the entire strike zone volume:
        # Torso yaw and shoulder roll control lateral reach (dx)
        # Shoulder pitch and elbow control vertical reach (dz)
        q_arm_tgt[0] += -1.8 * dx_mitt
        q_arm_tgt[1] += -2.5 * dz_mitt + 0.3 * dy_mitt
        q_arm_tgt[2] += -1.5 * dx_mitt
        q_arm_tgt[4] += -2.0 * dz_mitt - 0.5 * dy_mitt

        q_leg_tgt = self.q_squat_legs.copy()
        q_leg_tgt[2] += -0.3 * d_squat_z
        q_leg_tgt[3] += 0.6 * d_squat_z
        q_leg_tgt[7] += -0.3 * d_squat_z
        q_leg_tgt[8] += 0.6 * d_squat_z

        for s_idx in range(self.frame_skip):
            sim_time = current_time + s_idx * self.model.opt.timestep

            if not self.is_released and self.current_step >= self.actual_release_step:
                self.is_released = True
                hp_now = self.data.site_xpos[self.p_hand_site_id].copy()
                tgt_pt = np.array([self.target_pitch_x, 0.0, self.target_pitch_z], dtype=np.float32)
                tf = (hp_now[1] - tgt_pt[1]) / self.pitch_speed
                vx_rel = (tgt_pt[0] - hp_now[0]) / tf
                vz_rel = (tgt_pt[2] + 0.5 * 9.81 * (tf**2) - hp_now[2]) / tf

                for _ in range(3):
                    p_s = hp_now.copy()
                    v_s = np.array([vx_rel, -self.pitch_speed, vz_rel], dtype=np.float32)
                    while p_s[1] > tgt_pt[1]:
                        vm = np.linalg.norm(v_s)
                        fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_s
                        fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_s)
                        acc = (fd + fm) / self.m_ball + np.array([0, 0, -9.81], dtype=np.float32)
                        v_s += acc * 0.002
                        p_s += v_s * 0.002
                    err_x = tgt_pt[0] - p_s[0]
                    err_z = tgt_pt[2] - p_s[2]
                    vx_rel += err_x / tf
                    vz_rel += err_z / tf

                self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hp_now
                self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx_rel, -self.pitch_speed, vz_rel]

            if self.is_released and not self.ball_caught:
                v_ball = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                vm = np.linalg.norm(v_ball)
                if vm > 1.0:
                    fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_ball
                    fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_ball)
                    self.data.qfrc_applied[self.ball_qvel_adr:self.ball_qvel_adr+3] = fd + fm

            # Plate Crossing Check
            ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
            if not self.plate_crossed and ball_pos[1] <= 0.0:
                self.plate_crossed = True
                self.plate_cross_x = ball_pos[0]
                self.plate_cross_z = ball_pos[2]
                if abs(self.plate_cross_x) <= 0.22 and (0.65 <= self.plate_cross_z <= 1.05):
                    self.is_strike = True

            # Catch Detection at Catcher Mitt Plane (y <= -0.75m)
            mitt_pos = self.data.site_xpos[self.c_mitt_site_id]
            if not self.ball_caught and ball_pos[1] <= (mitt_pos[1] + 0.12):
                d_planar = float(np.sqrt((ball_pos[0] - mitt_pos[0])**2 + (ball_pos[2] - mitt_pos[2])**2))
                if d_planar <= 0.18:
                    self.ball_caught = True
                    self.catch_step = self.current_step
                    self.framing_error = d_planar

            if self.ball_caught:
                self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = mitt_pos + np.array([0.0, 0.02, 0.0])
                self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = 0.0

            # Pitcher control
            for i, a_id in enumerate(self.p_act_ids):
                adr = self.p_qpos_adrs[i]
                q_cur = self.data.qpos[adr]
                q_dot = self.data.qvel[self.model.jnt_dofadr[self.model.actuator_trnid[a_id, 0]]]
                tau = 350.0 * (p_pose[i] - q_cur) - 25.0 * q_dot
                self.data.ctrl[a_id] = np.clip(tau, -60.0, 60.0)

            # Catcher upper body
            for i, a_id in enumerate(self.c_upper_act_ids):
                adr = self.c_upper_qpos_adrs[i]
                q_cur = self.data.qpos[adr]
                q_dot = self.data.qvel[self.c_upper_qvel_adrs[i]]
                tau = self.c_upper_Kp[i] * (q_arm_tgt[i] - q_cur) - self.c_upper_Kd[i] * q_dot
                self.data.ctrl[a_id] = np.clip(tau, -40.0, 40.0)

            # Catcher legs
            for i, a_id in enumerate(self.c_leg_act_ids):
                adr = self.c_leg_qpos_adrs[i]
                q_cur = self.data.qpos[adr]
                q_dot = self.data.qvel[self.c_leg_qvel_adrs[i]]
                tau = self.c_leg_Kp[i] * (q_leg_tgt[i] - q_cur) - self.c_leg_Kd[i] * q_dot
                self.data.ctrl[a_id] = np.clip(tau, -200.0, 200.0)

            mujoco.mj_step(self.model, self.data)

        # Catcher fall check: only true fall if pelvis drops below ground or flips
        c_z = self.data.qpos[self.c_pelvis_qpos_adr + 2]
        if c_z < 0.20 or c_z > 0.95:
            self.catcher_fallen = True

        # Reward
        reward = 0.0
        mitt_pos = self.data.site_xpos[self.c_mitt_site_id]
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        d_planar = float(np.sqrt((ball_pos[0] - mitt_pos[0])**2 + (ball_pos[2] - mitt_pos[2])**2))
        reward += 2.0 * np.exp(-10.0 * (d_planar ** 2))

        if self.ball_caught:
            reward += 15.0

        if self.plate_crossed and self.is_strike:
            reward += 5.0

        if not self.catcher_fallen:
            reward += 0.5
        else:
            reward -= 15.0

        terminated = False
        ball_y = self.data.qpos[self.ball_qpos_adr + 1]
        if self.catcher_fallen or self.ball_caught or ball_y < -1.10 or self.current_step >= self.max_steps:
            terminated = True

        info = {
            "pitch_type": self.pitch_name,
            "pitch_speed_kmh": self.pitch_speed * 3.6,
            "ball_caught": self.ball_caught,
            "is_strike": self.is_strike,
            "framing_error_cm": self.framing_error * 100.0 if self.ball_caught else d_planar * 100.0,
            "catcher_fallen": self.catcher_fallen,
            "plate_cross_x": self.plate_cross_x,
            "plate_cross_z": self.plate_cross_z,
            "catcher_pelvis_z": c_z
        }

        return self._get_obs(), reward, terminated, False, info

    def render(self):
        if self.renderer is None:
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)
        cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "battery_broadcast_cam")
        self.renderer.update_scene(self.data, camera=cam_id)
        return self.renderer.render()

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
