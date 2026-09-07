"""
AthleticDuelEnv: Unified Whole-Body Stadium Duel with Deep-Knee Athletic Batter Stance,
10m Pitcher Mound, 6-DoF Deep-Squat Catcher, and Standardized Strike Zone.
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


class AthleticDuelEnv(gym.Env):
    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}

    def __init__(
        self,
        xml_path=None,
        render_mode=None,
        frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz)
        pitch_types=None,  # 0: Fastball, 1: Slider, 2: Curveball
    ):
        super().__init__()

        if xml_path is None:
            xml_path = os.path.join(parent_dir, "models", "h1_athletic_duel.xml")

        self.xml_path = xml_path
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)

        self.render_mode = render_mode
        self.frame_skip = frame_skip
        self.dt = self.model.opt.timestep * self.frame_skip
        self.pitch_types = pitch_types if pitch_types is not None else [0, 1, 2]

        # Bodies & Sites
        self.p_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "p_pelvis")
        self.c_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "c_pelvis")
        self.b_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "b_pelvis")
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")

        self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")
        self.c_mitt_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "c_mitt_site")
        self.p_hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")

        # Freejoints
        ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
        self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]

        c_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "c_pelvis_joint")
        self.c_pelvis_qpos_adr = self.model.jnt_qposadr[c_pelvis_jnt_id]
        self.c_pelvis_qvel_adr = self.model.jnt_dofadr[c_pelvis_jnt_id]

        b_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "b_pelvis_joint")
        self.b_pelvis_qpos_adr = self.model.jnt_qposadr[b_pelvis_jnt_id]
        self.b_pelvis_qvel_adr = self.model.jnt_dofadr[b_pelvis_jnt_id]

        # Pitcher Actuators
        self.p_act_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
        self.p_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.p_act_names]
        self.p_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
        self.p_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]

        # Catcher Upper & Legs
        self.c_upper_names = ["c_torso", "c_left_shoulder_pitch", "c_left_shoulder_roll", "c_left_shoulder_yaw", "c_left_elbow", "c_right_shoulder_pitch", "c_right_shoulder_roll", "c_right_shoulder_yaw", "c_right_elbow"]
        self.c_upper_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.c_upper_names]
        self.c_upper_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.c_upper_act_ids]
        self.c_upper_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.c_upper_act_ids]

        self.c_leg_names = ["c_left_hip_yaw", "c_left_hip_roll", "c_left_hip_pitch", "c_left_knee", "c_left_ankle", "c_right_hip_yaw", "c_right_hip_roll", "c_right_hip_pitch", "c_right_knee", "c_right_ankle"]
        self.c_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.c_leg_names]
        self.c_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.c_leg_act_ids]
        self.c_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.c_leg_act_ids]

        # Batter Upper (Two-Handed Coordination)
        self.b_upper_names = ["b_torso", "b_left_shoulder_pitch", "b_left_shoulder_roll", "b_left_shoulder_yaw", "b_left_elbow", "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"]
        self.b_upper_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_upper_names]
        self.b_upper_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_upper_act_ids]
        self.b_upper_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_upper_act_ids]

        # Batter Legs (10 DoF Whole-Body ZMP Balance)
        self.b_leg_names = ["b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle", "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle"]
        self.b_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_leg_names]
        self.b_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]
        self.b_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]

        # PD Gains
        self.p_Kp = 350.0
        self.p_Kd = 25.0
        self.c_leg_Kp = np.array([200, 200, 300, 400, 100, 200, 200, 300, 400, 100], dtype=np.float32)
        self.c_leg_Kd = np.array([20, 20, 30, 40, 10, 20, 20, 30, 40, 10], dtype=np.float32)
        self.c_upper_Kp = 60.0
        self.c_upper_Kd = 6.0

        self.b_leg_Kp = np.array([350, 350, 450, 500, 200, 350, 350, 450, 500, 200], dtype=np.float32)
        self.b_leg_Kd = np.array([30, 30, 40, 45, 18, 30, 30, 40, 45, 18], dtype=np.float32)
        self.b_upper_Kp = np.array([600, 200, 150, 100, 120, 300, 200, 150, 180], dtype=np.float32)
        self.b_upper_Kd = np.array([40, 15, 12, 8, 10, 25, 15, 12, 14], dtype=np.float32)

        # Catcher Postures
        self.q_squat_legs = np.array([0.0, 0.0, -1.15, 1.88, -0.75, 0.0, 0.0, -1.15, 1.88, -0.75], dtype=np.float32)
        self.q_squat_upper = np.array([0.0, -0.50, -0.30, -0.30, 0.20, -0.60, -0.20, 0.0, 1.50], dtype=np.float32)

        # Batter Deep-Knee Athletic Stance
        # knee = 0.65 rad (~37.2 deg), hip_pitch = -0.28 rad, ankle = -0.37 rad (rock-solid ground contact at z = 0.95m)
        self.b_base_legs = np.array([0.0, 0.12, -0.28, 0.65, -0.37, 0.0, -0.12, -0.28, 0.65, -0.37], dtype=np.float32)

        # Calibrated 6-Keyframe Kinetic Swing Sequence for Strike Zone (z ~ 0.82m)
        self.b_swing_keyframes = np.array([
            [-0.25, -0.50, -1.10, -0.50, 0.55],  # 0: Ready Stance (Cocked upright bat at 42 deg)
            [-0.35, -0.65, -0.80, -0.40, 0.85],  # 1: Stride / Load
            [-0.05, -0.80, -0.20, -0.15, 1.05],  # 2: Slot / Uncoil
            [ 0.35, -0.65, -0.15, -0.15, 1.00],  # 3: Impact (z ~ 0.80-0.85m at home plate)
            [ 0.85, -0.40, -0.05, -0.25, 0.90],  # 4: Full Extension
            [ 1.35, -0.55,  0.25, -0.40, 1.25]   # 5: High Follow-through
        ], dtype=np.float32)

        self.p_keyframes = np.array([
            [ 0.20, -0.20, -0.40,  0.30,  1.00],
            [-0.50, -1.40, -0.20, -0.20,  0.20],
            [-0.90, -1.80, -0.60, -0.50,  0.70],
        ], dtype=np.float32)

        # Aerodynamics constants
        self.rho = 1.205
        self.r_ball = 0.037
        self.m_ball = 0.145
        self.A_ball = np.pi * (self.r_ball ** 2)
        self.Cd = 0.32
        self.Cl = 0.24

        # Action: 6 dims for Whole-Body Batter
        # a[0]: dt_lead swing timing adjustment (-0.030 to +0.030s)
        # a[1]: dz_bat plane height adjustment (-0.15 to +0.15rad)
        # a[2]: dalpha_tilt attack tilt angle adjustment (-0.10 to +0.10rad)
        # a[3]: dpower_dur swing duration adjustment (-0.020 to +0.020s)
        # a[4]: dknee_crouch knee flexion depth adjustment (-0.06 to +0.06rad)
        # a[5]: dweight_shift ankle ZMP balance adjustment (-0.06 to +0.06rad)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(51,), dtype=np.float32)

        # Episode state variables
        self.current_step = 0
        self.max_steps = 55
        self.is_released = False
        self.plate_crossed = False
        self.plate_cross_x = 0.0
        self.plate_cross_z = 0.0
        self.is_strike = False
        self.is_hit = False
        self.is_fair = False
        self.contact_step = -1
        self.sweet_spot_error = 0.0
        self.exit_velocity = 0.0
        self.exit_heading = 0.0
        self.catcher_caught = False
        self.catcher_fallen = False
        self.batter_fallen = False
        self.framing_error = 0.0

        self.swing_triggered = False
        self.locked_t_trigger = 0.0
        self.locked_swing_duration = 0.200

        self.renderer = None
        if self.render_mode in ["rgb_array", "human"]:
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        self.current_step = 0
        self.is_released = False
        self.plate_crossed = False
        self.plate_cross_x = 0.0
        self.plate_cross_z = 0.0
        self.is_strike = False
        self.is_hit = False
        self.is_fair = False
        self.contact_step = -1
        self.sweet_spot_error = 0.0
        self.exit_velocity = 0.0
        self.exit_heading = 0.0
        self.catcher_caught = False
        self.catcher_fallen = False
        self.batter_fallen = False
        self.framing_error = 0.0

        self.swing_triggered = False
        self.locked_t_trigger = 0.0
        self.locked_swing_duration = 0.200

        # Pitch selection
        p_choice = int(self.np_random.choice(self.pitch_types))
        if p_choice == 0:
            self.pitch_name = "Fastball"
            self.pitch_speed = float(self.np_random.uniform(23.6, 24.7))  # 85-89 km/h
            self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
            self.target_pitch_x = float(self.np_random.uniform(-0.12, 0.12))
            self.target_pitch_z = float(self.np_random.uniform(0.82, 0.94))
        elif p_choice == 1:
            self.pitch_name = "Slider"
            self.pitch_speed = float(self.np_random.uniform(21.1, 22.2))  # 76-80 km/h
            self.pitch_spin = np.array([40.0, 0.0, 150.0], dtype=np.float32)
            self.target_pitch_x = float(self.np_random.uniform(0.02, 0.15))
            self.target_pitch_z = float(self.np_random.uniform(0.72, 0.85))
        else:
            self.pitch_name = "Curveball"
            self.pitch_speed = float(self.np_random.uniform(19.7, 20.8))  # 71-75 km/h
            self.pitch_spin = np.array([170.0, 0.0, -30.0], dtype=np.float32)
            self.target_pitch_x = float(self.np_random.uniform(-0.08, 0.08))
            self.target_pitch_z = float(self.np_random.uniform(0.68, 0.78))

        # Setup Pitcher
        for i, adr in enumerate(self.p_qpos_adrs):
            self.data.qpos[adr] = self.p_keyframes[0, i]

        # Setup Catcher Deep Squat behind Home Plate
        self.data.qpos[self.c_pelvis_qpos_adr:self.c_pelvis_qpos_adr+3] = [0.0, -0.95, 0.69]
        self.data.qpos[self.c_pelvis_qpos_adr+3:self.c_pelvis_qpos_adr+7] = [0.7071068, 0.0, 0.0, 0.7071068]
        self.data.qvel[self.c_pelvis_qvel_adr:self.c_pelvis_qvel_adr+6] = 0.0
        for i, adr in enumerate(self.c_leg_qpos_adrs):
            self.data.qpos[adr] = self.q_squat_legs[i]
        for i, adr in enumerate(self.c_upper_qpos_adrs):
            self.data.qpos[adr] = self.q_squat_upper[i]

        # Setup Batter Deep-Knee Athletic Stance in Batter's Box (x = -1.10, z = 0.95)
        self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3] = [-1.10, 0.00, 0.95]
        self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+6] = 0.0
        for i, adr in enumerate(self.b_leg_qpos_adrs):
            self.data.qpos[adr] = self.b_base_legs[i]

        torso_val = self.b_swing_keyframes[0, 0]
        b_upper_init = np.array([
            torso_val,
            -0.30 - 0.50 * torso_val,
             0.45 - 0.20 * torso_val,
             0.70 + 0.30 * torso_val,
             1.20 - 0.40 * torso_val,
            self.b_swing_keyframes[0, 1],
            self.b_swing_keyframes[0, 2],
            self.b_swing_keyframes[0, 3],
            self.b_swing_keyframes[0, 4]
        ], dtype=np.float32)
        for i, adr in enumerate(self.b_upper_qpos_adrs):
            self.data.qpos[adr] = b_upper_init[i]

        # Place ball in pitcher's hand
        mujoco.mj_forward(self.model, self.data)
        hand_pos = self.data.site_xpos[self.p_hand_site_id].copy()
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+6] = 0.0
        mujoco.mj_forward(self.model, self.data)

        self.flight_time_nominal = float(10.0 / self.pitch_speed)

        return self._get_obs(), {}

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()

        if self.is_released and abs(ball_vel[1]) > 1.0 and ball_pos[1] > 0.0:
            t_remain = float(ball_pos[1] / abs(ball_vel[1]))
        elif not self.is_released:
            t_remain = float(self.flight_time_nominal)
        else:
            t_remain = 0.0

        b_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3].copy()
        b_quat = self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7].copy()
        b_vel = self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+3].copy()
        b_angvel = self.data.qvel[self.b_pelvis_qvel_adr+3:self.b_pelvis_qvel_adr+6].copy()

        sweet_pos = self.data.site_xpos[self.sweet_spot_id].copy()
        sweet_vel = np.zeros(3, dtype=np.float32)

        target_pos = np.array([self.target_pitch_x, 0.0, self.target_pitch_z], dtype=np.float32)

        leg_q = [self.data.qpos[adr] for adr in self.b_leg_qpos_adrs]
        upper_q = [self.data.qpos[adr] for adr in self.b_upper_qpos_adrs]
        joint_q = np.array(leg_q + upper_q, dtype=np.float32)

        obs = np.concatenate([
            ball_pos,
            ball_vel,
            self.pitch_spin * 0.01,
            np.array([t_remain], dtype=np.float32),
            b_pos,
            b_quat,
            b_vel,
            b_angvel,
            sweet_pos,
            sweet_vel,
            target_pos,
            joint_q
        ]).astype(np.float32)

        return obs

    def step(self, action):
        self.current_step += 1
        current_time = (self.current_step - 1) * self.dt

        # Unpack action modulations
        dt_lead = float(action[0]) * 0.030
        dz_plane = float(action[1]) * 0.15
        dalpha_tilt = float(action[2]) * 0.10
        dpower_dur = float(action[3]) * 0.020
        dknee_crouch = float(action[4]) * 0.06
        dweight_shift = float(action[5]) * 0.06

        # 1. Pitcher kinematics
        if self.current_step < 2:
            p_pose = self.p_keyframes[0]
        elif self.current_step < 4:
            p_pose = self.p_keyframes[1]
        else:
            p_pose = self.p_keyframes[2]

        # 2. Catcher target framing (moves mitt toward predicted pitch arrival at y = -0.65)
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        mitt_pos = self.data.site_xpos[self.c_mitt_site_id]

        if self.is_released and not self.is_hit and abs(ball_vel[1]) > 1.0 and ball_vel[1] < -0.5:
            dt_arr = max(0.0, (-0.65 - ball_pos[1]) / ball_vel[1])
            pred_x = ball_pos[0] + ball_vel[0] * dt_arr
            pred_z = ball_pos[2] + ball_vel[2] * dt_arr - 0.5 * 9.81 * (dt_arr**2)
        else:
            pred_x = self.target_pitch_x
            pred_z = self.target_pitch_z

        ex_mitt = float(np.clip((pred_x - mitt_pos[0]) * 1.5, -0.20, 0.20))
        ez_mitt = float(np.clip((pred_z - mitt_pos[2]) * 1.5, -0.20, 0.20))

        c_arm_tgt = self.q_squat_upper.copy()
        c_arm_tgt[0] += -1.8 * ex_mitt
        c_arm_tgt[1] += -2.5 * ez_mitt
        c_arm_tgt[2] += -1.5 * ex_mitt
        c_arm_tgt[4] += -2.0 * ez_mitt

        c_leg_tgt = self.q_squat_legs.copy()

        # 3. Dynamic In-Flight Perception & Swing Trigger
        if self.is_released and abs(ball_vel[1]) > 3.0 and ball_pos[1] > 0.0:
            speed_y = abs(ball_vel[1])
            # Linear speed-adaptive lead time:
            # Fastball (~24 m/s) -> ~0.221s
            # Slider (~21.6 m/s) -> ~0.245s
            # Curveball (~20.2 m/s) -> ~0.259s
            base_lead = 0.245 + (21.6 - speed_y) * 0.0100
            trigger_lead = base_lead + dt_lead
            t_rem = ball_pos[1] / speed_y
            if not self.swing_triggered and t_rem <= trigger_lead:
                self.swing_triggered = True
                self.locked_t_trigger = current_time
                self.locked_swing_duration = max(0.16, 0.200 + dpower_dur)

        # 4. Batter Stance Legs (with dynamic crouch modulation)
        b_leg_cmd = self.b_base_legs.copy()
        b_leg_cmd[3] += dknee_crouch  # Left knee
        b_leg_cmd[8] += dknee_crouch  # Right knee
        b_leg_cmd[2] += -0.5 * dknee_crouch
        b_leg_cmd[7] += -0.5 * dknee_crouch

        # Sub-step simulation loop
        for s_idx in range(self.frame_skip):
            sim_time = current_time + s_idx * self.model.opt.timestep

            # Pitch release at step 2
            if not self.is_released and self.current_step >= 2:
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
                    vx_rel += (tgt_pt[0] - p_s[0]) / tf
                    vz_rel += (tgt_pt[2] - p_s[2]) / tf

                self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hp_now
                self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx_rel, -self.pitch_speed, vz_rel]

            # Direct Aerodynamics Integration on Ball
            if self.is_released and not self.is_hit and not self.catcher_caught:
                v_ball = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                vm = np.linalg.norm(v_ball)
                if vm > 1.0:
                    fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_ball
                    fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_ball)
                    self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += (fd + fm) / self.m_ball * self.model.opt.timestep

            # Batter Arm Kinematic Progression
            if not self.swing_triggered:
                b_r_tgt = list(self.b_swing_keyframes[0])
            else:
                t_sw = sim_time - self.locked_t_trigger
                prog = t_sw / self.locked_swing_duration
                if prog < 0.20:
                    w = prog / 0.20
                    b_r_tgt = [(1-w)*self.b_swing_keyframes[0][j] + w*self.b_swing_keyframes[1][j] for j in range(5)]
                elif prog < 0.45:
                    w = (prog - 0.20) / 0.25
                    b_r_tgt = [(1-w)*self.b_swing_keyframes[1][j] + w*self.b_swing_keyframes[2][j] for j in range(5)]
                elif prog < 0.70:
                    w = (prog - 0.45) / 0.25
                    b_r_tgt = [(1-w)*self.b_swing_keyframes[2][j] + w*self.b_swing_keyframes[3][j] for j in range(5)]
                elif prog < 0.90:
                    w = (prog - 0.70) / 0.20
                    b_r_tgt = [(1-w)*self.b_swing_keyframes[3][j] + w*self.b_swing_keyframes[4][j] for j in range(5)]
                else:
                    w = min(1.0, (prog - 0.90) / 0.30)
                    b_r_tgt = [(1-w)*self.b_swing_keyframes[4][j] + w*self.b_swing_keyframes[5][j] for j in range(5)]

                # Vertical height tracking & tilt modulation
                dz = (self.target_pitch_z - 0.80) * 0.50 + dz_plane
                b_r_tgt[1] += -dz
                b_r_tgt[2] += dalpha_tilt

            torso_val = b_r_tgt[0]
            b_upper_cmd = [
                torso_val,
                -0.30 - 0.50 * torso_val,
                 0.45 - 0.20 * torso_val,
                 0.70 + 0.30 * torso_val,
                 1.20 - 0.40 * torso_val,
                b_r_tgt[1], b_r_tgt[2], b_r_tgt[3], b_r_tgt[4]
            ]

            # Dynamic Weight Shift Transfer during swing
            b_leg_curr = b_leg_cmd.copy()
            if self.swing_triggered:
                prog = (sim_time - self.locked_t_trigger) / self.locked_swing_duration
                shift = np.clip(prog, 0.0, 1.0) * 0.10
                b_leg_curr[2] -= shift  # drive forward onto front hip
                b_leg_curr[7] += shift

            # Plate Crossing Check (y = 0.0)
            curr_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
            if not self.plate_crossed and curr_ball_pos[1] <= 0.0:
                self.plate_crossed = True
                self.plate_cross_x = curr_ball_pos[0]
                self.plate_cross_z = curr_ball_pos[2]
                if abs(self.plate_cross_x) <= 0.22 and (0.65 <= self.plate_cross_z <= 1.05):
                    self.is_strike = True

            # Bat-Ball Physical Contact Detection
            if not self.is_hit and curr_ball_pos[1] <= 0.40:
                sweet_pos = self.data.site_xpos[self.sweet_spot_id]
                d_contact = float(np.linalg.norm(curr_ball_pos - sweet_pos))

                has_collision = False
                for c_idx in range(self.data.ncon):
                    con = self.data.contact[c_idx]
                    g1, g2 = con.geom1, con.geom2
                    if (g1 == self.bat_geom_id and g2 == self.ball_geom_id) or \
                       (g2 == self.bat_geom_id and g1 == self.ball_geom_id):
                        has_collision = True
                        break

                if has_collision or (d_contact <= 0.18 and abs(curr_ball_pos[1] - sweet_pos[1]) <= 0.09):
                    self.is_hit = True
                    self.contact_step = self.current_step
                    self.sweet_spot_error = d_contact

                    # Elastic impact restitution (COR = 0.55)
                    v_in = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                    v_rebound = 0.55 * abs(v_in[1]) + 15.0
                    vx_out = float(self.np_random.uniform(3.0, 9.0))   # Fair spray angle into field
                    vz_out = float(self.np_random.uniform(2.0, 5.0))   # Line drive / fly ball
                    self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx_out, v_rebound, vz_out]

                    self.exit_velocity = float(np.linalg.norm([vx_out, v_rebound, vz_out])) * 3.6
                    self.exit_heading = float(np.degrees(np.arctan2(vx_out, v_rebound)))
                    if 0.0 <= self.exit_heading <= 90.0:
                        self.is_fair = True

            # Catcher Catch Detection (if ball not hit and crosses mitt plane)
            if not self.is_hit and not self.catcher_caught and curr_ball_pos[1] <= (mitt_pos[1] + 0.12):
                d_planar = float(np.sqrt((curr_ball_pos[0] - mitt_pos[0])**2 + (curr_ball_pos[2] - mitt_pos[2])**2))
                if d_planar <= 0.18:
                    self.catcher_caught = True
                    self.framing_error = d_planar

            if self.catcher_caught:
                self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = mitt_pos + np.array([0.0, 0.02, 0.0])
                self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = 0.0

            # Actuator Controls:
            # 1. Pitcher
            for i, a_id in enumerate(self.p_act_ids):
                adr = self.p_qpos_adrs[i]
                q_cur = self.data.qpos[adr]
                q_dot = self.data.qvel[self.model.jnt_dofadr[self.model.actuator_trnid[a_id, 0]]]
                tau = self.p_Kp * (p_pose[i] - q_cur) - self.p_Kd * q_dot
                self.data.ctrl[a_id] = np.clip(tau, -60.0, 60.0)

            # 2. Catcher Upper
            for i, a_id in enumerate(self.c_upper_act_ids):
                adr = self.c_upper_qpos_adrs[i]
                q_cur = self.data.qpos[adr]
                q_dot = self.data.qvel[self.c_upper_qvel_adrs[i]]
                tau = self.c_upper_Kp * (c_arm_tgt[i] - q_cur) - self.c_upper_Kd * q_dot
                self.data.ctrl[a_id] = np.clip(tau, -40.0, 40.0)

            # 3. Catcher Legs
            for i, a_id in enumerate(self.c_leg_act_ids):
                adr = self.c_leg_qpos_adrs[i]
                q_cur = self.data.qpos[adr]
                q_dot = self.data.qvel[self.c_leg_qvel_adrs[i]]
                tau = self.c_leg_Kp[i] * (c_leg_tgt[i] - q_cur) - self.c_leg_Kd[i] * q_dot
                self.data.ctrl[a_id] = np.clip(tau, -200.0, 200.0)

            # 4. Batter Upper Body PD
            for i, a_id in enumerate(self.b_upper_act_ids):
                adr = self.b_upper_qpos_adrs[i]
                q_cur = self.data.qpos[adr]
                q_dot = self.data.qvel[self.b_upper_qvel_adrs[i]]
                tau = self.b_upper_Kp[i] * (b_upper_cmd[i] - q_cur) - self.b_upper_Kd[i] * q_dot
                self.data.ctrl[a_id] = np.clip(tau, -180.0, 180.0)

            # 5. Batter Legs with Active Ground Reaction Shear & Yaw Balancing
            p_x = self.data.qpos[self.b_pelvis_qpos_adr]
            v_x = self.data.qvel[self.b_pelvis_qvel_adr]
            w_z = self.data.qvel[self.b_pelvis_qvel_adr + 5]

            tau_x_ank = np.clip(500.0 * (p_x - (-1.10)) + 50.0 * v_x, -35.0, 35.0)
            tau_x_hip = np.clip(400.0 * (p_x - (-1.10)) + 40.0 * v_x, -50.0, 50.0)
            tau_yaw = np.clip(80.0 * w_z, -50.0, 50.0)

            for i, a_id in enumerate(self.b_leg_act_ids):
                adr = self.b_leg_qpos_adrs[i]
                q_cur = self.data.qpos[adr]
                q_dot = self.data.qvel[self.b_leg_qvel_adrs[i]]
                cmd = b_leg_curr[i]
                if i in [4, 9]:
                    cmd += dweight_shift
                tau = self.b_leg_Kp[i] * (cmd - q_cur) - self.b_leg_Kd[i] * q_dot
                if i in [4, 9]:
                    tau += tau_x_ank
                elif i in [2, 7]:
                    tau += tau_x_hip
                elif i in [0, 5]:
                    tau += tau_yaw
                self.data.ctrl[a_id] = np.clip(tau, -250.0, 250.0)

            mujoco.mj_step(self.model, self.data)

        # Fall Checks
        c_z = float(self.data.qpos[self.c_pelvis_qpos_adr + 2])
        if c_z < 0.20 or c_z > 0.95:
            self.catcher_fallen = True

        b_z = float(self.data.qpos[self.b_pelvis_qpos_adr + 2])
        if b_z < 0.60 or b_z > 1.15:
            self.batter_fallen = True

        # Reward formulation
        reward = 0.0
        sweet_pos = self.data.site_xpos[self.sweet_spot_id]
        ball_p = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        d_sw = float(np.linalg.norm(ball_p - sweet_pos))

        reward += 3.0 * np.exp(-10.0 * (d_sw ** 2))

        if self.is_hit:
            reward += 25.0
            reward += 0.5 * (self.exit_velocity / 3.6)
            if self.is_fair:
                reward += 15.0

        if not self.batter_fallen:
            reward += 1.0
        else:
            reward -= 25.0

        if self.catcher_caught and not self.is_hit:
            reward += 8.0

        # Termination condition
        terminated = False
        ball_y = self.data.qpos[self.ball_qpos_adr + 1]
        if self.batter_fallen or self.catcher_fallen:
            terminated = True
        elif self.is_hit and self.current_step >= (self.contact_step + 12):
            terminated = True
        elif not self.is_hit and (self.catcher_caught or ball_y < -1.10):
            terminated = True
        elif self.current_step >= self.max_steps:
            terminated = True

        info = {
            "pitch_type": self.pitch_name,
            "pitch_speed_kmh": self.pitch_speed * 3.6,
            "is_strike": self.is_strike,
            "is_hit": self.is_hit,
            "is_fair": self.is_fair,
            "sweet_spot_error_cm": self.sweet_spot_error * 100.0 if self.is_hit else d_sw * 100.0,
            "exit_velocity_kmh": self.exit_velocity,
            "exit_heading_deg": self.exit_heading,
            "batter_fallen": self.batter_fallen,
            "catcher_fallen": self.catcher_fallen,
            "catcher_caught": self.catcher_caught,
            "batter_pelvis_z": b_z,
            "catcher_pelvis_z": c_z,
            "plate_cross_x": self.plate_cross_x,
            "plate_cross_z": self.plate_cross_z
        }

        return self._get_obs(), reward, terminated, False, info

    def render(self):
        if self.renderer is None:
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)
        cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "duel_broadcast_cam")
        self.renderer.update_scene(self.data, camera=cam_id)
        return self.renderer.render()

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
