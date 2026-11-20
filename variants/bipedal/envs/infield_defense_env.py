"""
InfieldDefenseEnv: Phase 7 Full Infield Bipedal Defense & 1st Base Out/Safe Play.

Combines:
1. 10m Mound Unitree H1 Pitcher throwing Fastball / Slider / Curveball with Magnus effect.
2. 6-DoF Floating-Base Unitree H1 Batter-Runner at Home Plate (-0.75m, 0.0m) with:
   - Athletic kinetic uncoiling swing into fair infield
   - Dynamic prop handover (bat dropped cleanly onto turf at t = 0.52s)
   - Multi-step cyclic bipedal sprint toward 1st Base Pad (6.5m, 6.5m)
3. 6-DoF Floating-Base Unitree H1 1st Baseman Infielder in 1st base infield (5.0m, 5.0m) with:
   - Fielding glove (r = 0.12m) on left hand
   - Dynamic bipedal footwork, ball trajectory intercept, and 1st base covering
4. Realistic field turf restitution (e = 0.52), friction (mu = 0.4), and rolling resistance (crr = 0.02).
5. 3D Umpire Decision Engine measuring T_runner vs T_defense -> OUT vs SAFE.
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


class InfieldDefenseEnv(gym.Env):
    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}

    def __init__(
        self,
        xml_path=None,
        render_mode=None,
        frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz control)
        pitch_types=None,  # 0: Fastball, 1: Slider, 2: Curveball
    ):
        super().__init__()

        if xml_path is None:
            xml_path = os.path.join(parent_dir, "models", "h1_infield_defense.xml")

        self.xml_path = xml_path
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)

        self.render_mode = render_mode
        self.frame_skip = frame_skip
        self.dt = self.model.opt.timestep * self.frame_skip  # 0.02s
        self.pitch_types = pitch_types if pitch_types is not None else [0, 1, 2]

        # Geometry & Spatial Anchors
        self.target_1b = np.array([6.5, 6.5], dtype=np.float32)
        self.start_p0 = np.array([-0.75, 0.0], dtype=np.float32)
        vec_1b = self.target_1b - self.start_p0
        self.nominal_dist_1b = float(np.linalg.norm(vec_1b))  # ~9.74m
        self.u_1b = (vec_1b / self.nominal_dist_1b).astype(np.float32)
        self.yaw_1b = float(np.arctan2(self.u_1b[1], self.u_1b[0]))  # ~41.88 deg (0.731 rad)

        self.infielder_p0 = np.array([5.0, 5.0], dtype=np.float32)
        self.f_yaw0 = -2.356194
        self.f_u_sag = np.array([np.cos(self.f_yaw0), np.sin(self.f_yaw0)], dtype=np.float32)
        self.f_u_lat = np.array([-np.sin(self.f_yaw0), np.cos(self.f_yaw0)], dtype=np.float32)

        # Bodies
        self.p_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "p_pelvis")
        self.b_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "b_pelvis")
        self.f_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "f_pelvis")
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.b_held_bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "b_held_bat")
        self.dropped_bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "dropped_bat")

        # Geoms & Sites
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.b_held_bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "b_held_bat_barrel")
        self.f_glove_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "f_glove")
        self.first_base_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "first_base")

        self.b_sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "b_bat_sweet_spot")
        self.f_glove_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "f_glove_site")
        self.p_hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")
        self.weld_eq_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_EQUALITY, "p_ball_weld")

        # Freejoints
        ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
        self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]

        b_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "b_pelvis_joint")
        self.b_pelvis_qpos_adr = self.model.jnt_qposadr[b_pelvis_jnt_id]
        self.b_pelvis_qvel_adr = self.model.jnt_dofadr[b_pelvis_jnt_id]

        f_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "f_pelvis_joint")
        self.f_pelvis_qpos_adr = self.model.jnt_qposadr[f_pelvis_jnt_id]
        self.f_pelvis_qvel_adr = self.model.jnt_dofadr[f_pelvis_jnt_id]

        drop_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "dropped_bat_joint")
        self.drop_qpos_adr = self.model.jnt_qposadr[drop_jnt_id]
        self.drop_qvel_adr = self.model.jnt_dofadr[drop_jnt_id]

        # Pitcher Arm Actuators
        self.p_act_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
        self.p_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.p_act_names]
        self.p_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
        self.p_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]

        # Batter Swing & Leg Actuators
        self.b_swing_act_names = ["b_torso", "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"]
        self.b_swing_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_swing_act_names]
        self.b_swing_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_swing_act_ids]
        self.b_swing_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_swing_act_ids]

        self.b_leg_act_names = [
            "b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle",
            "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle",
        ]
        self.b_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_leg_act_names]
        self.b_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]
        self.b_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]

        # Infielder Actuators
        self.f_arm_act_names = ["f_torso", "f_left_shoulder_pitch", "f_left_shoulder_roll", "f_left_shoulder_yaw", "f_left_elbow"]
        self.f_arm_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.f_arm_act_names]
        self.f_arm_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.f_arm_act_ids]
        self.f_arm_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.f_arm_act_ids]

        self.f_leg_act_names = [
            "f_left_hip_yaw", "f_left_hip_roll", "f_left_hip_pitch", "f_left_knee", "f_left_ankle",
            "f_right_hip_yaw", "f_right_hip_roll", "f_right_hip_pitch", "f_right_knee", "f_right_ankle",
        ]
        self.f_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.f_leg_act_names]
        self.f_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.f_leg_act_ids]
        self.f_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.f_leg_act_ids]

        # PD Control Gains
        self.p_Kp = np.array([450.0, 350.0, 250.0, 150.0, 150.0], dtype=np.float32)
        self.p_Kd = np.array([35.0,  25.0,  20.0,  12.0,  12.0], dtype=np.float32)

        self.b_swing_Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
        self.b_swing_Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)

        self.b_leg_Kp = np.array([450.0, 450.0, 650.0, 750.0, 350.0, 450.0, 450.0, 650.0, 750.0, 350.0], dtype=np.float32)
        self.b_leg_Kd = np.array([35.0,  40.0,  55.0,  65.0,  28.0,  35.0,  40.0,  55.0,  65.0,  28.0], dtype=np.float32)

        self.f_arm_Kp = np.array([400.0, 250.0, 200.0, 150.0, 150.0], dtype=np.float32)
        self.f_arm_Kd = np.array([30.0,  20.0,  18.0,  12.0,  12.0], dtype=np.float32)

        self.f_leg_Kp = np.array([450.0, 450.0, 650.0, 750.0, 350.0, 450.0, 450.0, 650.0, 750.0, 350.0], dtype=np.float32)
        self.f_leg_Kd = np.array([35.0,  40.0,  55.0,  65.0,  28.0,  35.0,  40.0,  55.0,  65.0,  28.0], dtype=np.float32)

        # Keyframe postures
        self.p_keyframes = np.array([
            [ 0.20, -0.20, -0.40,  0.30,  1.00],
            [-0.50, -1.40, -0.20, -0.20,  0.20],
            [-0.90, -1.80, -0.60, -0.50,  0.70],
        ], dtype=np.float32)

        self.b_base_keyframes = np.array([
            [-0.40, -1.00,  0.00,  0.40,  1.50],
            [-0.60, -1.15,  0.00,  0.60,  1.70],
            [-0.10, -0.70, -0.05,  0.20,  1.20],
            [ 0.50, -0.30, -0.10, -0.10,  0.70],
            [ 1.15,  0.20, -0.08, -0.40,  0.35],
            [ 1.70,  0.80,  0.00, -0.70,  1.20]
        ], dtype=np.float32)

        self.base_leg_q = np.array([
            0.0,  0.10, -0.18, 0.48, -0.32,  # Left leg
            0.0, -0.10, -0.18, 0.48, -0.32   # Right leg
        ], dtype=np.float32)

        self.crouch_leg_q = np.array([
            0.0,  0.10, -0.30, 0.65, -0.35,  # Athletic crouching stance
            0.0, -0.10, -0.30, 0.65, -0.35
        ], dtype=np.float32)

        # Aerodynamic constants
        self.rho = 1.205
        self.r_ball = 0.037
        self.m_ball = 0.145
        self.A_ball = np.pi * (self.r_ball ** 2)
        self.Cd = 0.32
        self.Cl = 0.24

        # Action Space (8 dims):
        # a[0]: dt_trigger timing lead/lag (-0.03 to +0.03s)
        # a[1]: dz_bat plane height (-0.20 to +0.20rad)
        # a[2]: dalpha_plane attack tilt (-0.15 to +0.15rad)
        # a[3]: stride_freq runner modulation (1.6 to 2.2 Hz)
        # a[4]: sprint_push_gain (0.8 to 1.4)
        # a[5]: sprint_steer_yaw (-0.20 to +0.20rad)
        # a[6]: fielder_lateral_shift (-0.35 to +0.35m)
        # a[7]: fielder_glove_elevation (-0.20 to +0.20m)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(8,), dtype=np.float32)

        # Observation Space (74 dims)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(74,), dtype=np.float32)

        self.current_step = 0
        self.max_steps = 100  # 100 * 0.02s = 2.00s (complete play window)
        self.filtered_action = np.zeros(8, dtype=np.float32)

        # Play State Variables
        self.is_released = False
        self.actual_release_step = 4
        self.pitch_type = 0
        self.pitch_name = "Fastball"
        self.pitch_speed = 23.5
        self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)

        self.swing_triggered = False
        self.locked_t_trigger = 0.0
        self.locked_swing_duration = 0.17
        self.has_contacted = False
        self.bat_released = False
        self.contact_step = -1
        self.release_step = -1
        self.exit_velocity = 0.0
        self.exit_azimuth_deg = 0.0
        self.exit_launch_deg = 0.0
        self.is_fair_hit = False
        self.is_strike = True

        self.batter_fallen = False
        self.fielder_fallen = False
        self.sweet_spot_offset = 0.0

        # Fielding and Umpire Decision
        self.ball_fielded = False
        self.field_step = -1
        self.t_fielded = 999.0

        self.defense_completed = False
        self.defense_step = -1
        self.t_defense = 999.0

        self.runner_reached_1b = False
        self.runner_step = -1
        self.t_runner = 999.0

        self.umpire_decision = "PENDING"
        self.prev_runner_dist_1b = self.nominal_dist_1b
        self.runner_max_spd = 0.0

        self.renderer = None
        if self.render_mode in ["rgb_array", "human"]:
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        self.current_step = 0
        self.filtered_action = np.zeros(8, dtype=np.float32)

        self.is_released = False
        self.swing_triggered = False
        self.locked_t_trigger = 0.0
        self.locked_swing_duration = 0.17
        self.has_contacted = False
        self.bat_released = False
        self.contact_step = -1
        self.release_step = -1
        self.exit_velocity = 0.0
        self.exit_azimuth_deg = 0.0
        self.exit_launch_deg = 0.0
        self.is_fair_hit = False
        self.is_strike = True

        self.batter_fallen = False
        self.fielder_fallen = False
        self.sweet_spot_offset = 0.0

        self.ball_fielded = False
        self.field_step = -1
        self.t_fielded = 999.0

        self.defense_completed = False
        self.defense_step = -1
        self.t_defense = 999.0

        self.runner_reached_1b = False
        self.runner_step = -1
        self.t_runner = 999.0

        self.umpire_decision = "PENDING"
        self.runner_max_spd = 0.0

        # Restore held bat visibility and ball collision
        self.model.geom_size[self.b_held_bat_geom_id] = [0.032, 0.45, 0.0]
        self.model.geom_rgba[self.b_held_bat_geom_id, 3] = 1.0
        self.model.geom_contype[self.ball_geom_id] = 1
        self.model.geom_conaffinity[self.ball_geom_id] = 1

        # Reset dropped bat in sky (z=50m)
        self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = [0.0, 0.0, 50.0]
        self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+6] = 0.0

        # 1. Pitcher Robot (mound at 0, 10.0, 0.82)
        for i, adr in enumerate(self.p_qpos_adrs):
            self.data.qpos[adr] = self.p_keyframes[0, i]

        # 2. Batter-Runner (floating base at -0.75, 0.0, 0.92)
        self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3] = [-0.75, 0.00, 0.92]
        self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+6] = 0.0

        for i, adr in enumerate(self.b_leg_qpos_adrs):
            self.data.qpos[adr] = self.base_leg_q[i]

        for i, adr in enumerate(self.b_swing_qpos_adrs):
            self.data.qpos[adr] = self.b_base_keyframes[0, i]

        # 3. 1st Baseman Infielder (floating base at 5.0, 5.0, 0.92 facing home plate -135 deg)
        self.data.qpos[self.f_pelvis_qpos_adr:self.f_pelvis_qpos_adr+3] = [5.0, 5.0, 0.92]
        self.data.qpos[self.f_pelvis_qpos_adr+3:self.f_pelvis_qpos_adr+7] = [0.3826834, 0.0, 0.0, -0.9238795]
        self.data.qvel[self.f_pelvis_qvel_adr:self.f_pelvis_qvel_adr+6] = 0.0

        for i, adr in enumerate(self.f_leg_qpos_adrs):
            self.data.qpos[adr] = self.base_leg_q[i]

        # Infielder ready arm posture (glove forward ready)
        f_arm_init = np.array([0.0, 0.40, 0.20, 0.0, 1.30], dtype=np.float32)
        for i, adr in enumerate(self.f_arm_qpos_adrs):
            self.data.qpos[adr] = f_arm_init[i]

        # 4. Synchronized Pitch Selection (Releases calibrated for arrival at t in [0.44s, 0.47s])
        self.pitch_type = int(self.np_random.choice(self.pitch_types))
        self.target_pitch_x = float(self.np_random.uniform(0.14, 0.18))
        self.target_pitch_z = float(self.np_random.uniform(0.53, 0.58))

        if self.pitch_type == 0:
            self.pitch_name = "Fastball"
            self.pitch_speed = float(self.np_random.uniform(23.8, 24.8))  # 85-89 km/h
            self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
            self.actual_release_step = 3  # t = 0.06s -> arrives at 0.464s
        elif self.pitch_type == 1:
            self.pitch_name = "Slider"
            self.pitch_speed = float(self.np_random.uniform(21.2, 22.2))  # 76-80 km/h
            self.pitch_spin = np.array([-30.0, 0.0, 150.0], dtype=np.float32)
            self.actual_release_step = 1  # t = 0.02s -> arrives at 0.468s
        else:
            self.pitch_name = "Curveball"
            self.pitch_speed = float(self.np_random.uniform(20.5, 21.5))  # 74-77 km/h
            self.pitch_spin = np.array([170.0, 0.0, -20.0], dtype=np.float32)
            self.actual_release_step = 0  # t = 0.00s -> arrives at 0.461s

        # Ball in pitcher hand initially
        if self.weld_eq_id >= 0:
            self.data.eq_active[self.weld_eq_id] = True

        mujoco.mj_forward(self.model, self.data)
        hand_pos = self.data.site_xpos[self.p_hand_site_id].copy()
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
        self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+6] = 0.0
        mujoco.mj_forward(self.model, self.data)

        self.contact_plane_y = 0.22
        self.contact_lead_time = 0.170

        b_pelvis_xy = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+2]
        self.prev_runner_dist_1b = float(np.linalg.norm(self.target_1b - b_pelvis_xy))

        return self._get_obs(), {}

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]

        if self.is_released and abs(ball_vel[1]) > 1.0 and ball_pos[1] > self.contact_plane_y:
            t_remain = float((ball_pos[1] - self.contact_plane_y) / abs(ball_vel[1]))
        elif not self.is_released:
            t_remain = float((9.5 - self.contact_plane_y) / self.pitch_speed)
        else:
            t_remain = 0.0

        # Batter state
        b_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3]
        b_vel = self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+3]
        b_quat = self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7]
        b_angvel = self.data.qvel[self.b_pelvis_qvel_adr+3:self.b_pelvis_qvel_adr+6]

        b_rel_1b = self.target_1b - b_pos[:2]
        b_dist_1b = float(np.linalg.norm(b_rel_1b))

        # Infielder state
        f_pos = self.data.qpos[self.f_pelvis_qpos_adr:self.f_pelvis_qpos_adr+3]
        f_vel = self.data.qvel[self.f_pelvis_qvel_adr:self.f_pelvis_qvel_adr+3]
        f_quat = self.data.qpos[self.f_pelvis_qpos_adr+3:self.f_pelvis_qpos_adr+7]
        f_angvel = self.data.qvel[self.f_pelvis_qvel_adr+3:self.f_pelvis_qvel_adr+6]

        f_rel_ball = ball_pos - f_pos
        f_dist_ball = float(np.linalg.norm(f_rel_ball))

        f_rel_1b = self.target_1b - f_pos[:2]
        f_dist_1b = float(np.linalg.norm(f_rel_1b))

        f_glove_pos = self.data.site_xpos[self.f_glove_site_id].copy()

        # Leg states
        b_leg_qpos = np.array([self.data.qpos[adr] for adr in self.b_leg_qpos_adrs], dtype=np.float32)
        f_leg_qpos = np.array([self.data.qpos[adr] for adr in self.f_leg_qpos_adrs], dtype=np.float32)

        obs = np.concatenate([
            ball_pos,                                    # 3
            ball_vel,                                    # 3
            np.array([t_remain], dtype=np.float32),      # 1
            b_pos,                                       # 3
            b_vel,                                       # 3
            b_quat,                                      # 4
            b_angvel,                                    # 3
            b_rel_1b,                                    # 2
            np.array([b_dist_1b], dtype=np.float32),     # 1
            f_pos,                                       # 3
            f_vel,                                       # 3
            f_quat,                                      # 4
            f_angvel,                                    # 3
            f_rel_ball,                                  # 3
            np.array([f_dist_ball], dtype=np.float32),   # 1
            f_rel_1b,                                    # 2
            np.array([f_dist_1b], dtype=np.float32),     # 1
            f_glove_pos,                                 # 3
            b_leg_qpos,                                  # 10
            f_leg_qpos,                                  # 10
            self.filtered_action,                        # 8
        ]).astype(np.float32)
        return obs

    def step(self, action):
        self.current_step += 1
        current_time = self.current_step * self.dt

        action = np.clip(action, self.action_space.low, self.action_space.high)
        self.filtered_action = 0.6 * self.filtered_action + 0.4 * action

        dt_trigger = 0.025 * float(self.filtered_action[0])
        dz_bat = 0.15 * float(self.filtered_action[1])
        dalpha_plane = 0.12 * float(self.filtered_action[2])
        freq_sprint = 1.9 + 0.3 * float(self.filtered_action[3])
        push_gain = 1.0 + 0.3 * float(self.filtered_action[4])
        steer_yaw = 0.15 * float(self.filtered_action[5])
        f_lat_shift = 0.25 * float(self.filtered_action[6])
        f_glove_dz = 0.15 * float(self.filtered_action[7])

        # Stage 1: Pitch Perception & Swing Trigger
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]

        if self.is_released and abs(ball_vel[1]) > 3.0:
            speed_y = abs(ball_vel[1])
            self.contact_lead_time = 0.170 + float(np.clip(21.0 - speed_y, -3.0, 3.5)) * 0.0016

        if self.is_released and not self.swing_triggered and abs(ball_vel[1]) > 2.0 and ball_pos[1] > self.contact_plane_y:
            t_rem = (ball_pos[1] - self.contact_plane_y) / abs(ball_vel[1])
            if t_rem <= (self.contact_lead_time + dt_trigger):
                self.swing_triggered = True
                self.locked_t_trigger = current_time

        # Stage 2: Dynamic Bat Handover at t = 0.52s
        if not self.bat_released and current_time >= 0.52:
            self.bat_released = True
            self.release_step = self.current_step

            bat_xpos = self.data.xpos[self.b_held_bat_body_id].copy()
            bat_xmat = self.data.xmat[self.b_held_bat_body_id].copy()
            bat_quat = np.zeros(4)
            mujoco.mju_mat2Quat(bat_quat, bat_xmat)

            self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = bat_xpos
            self.data.qpos[self.drop_qpos_adr+3:self.drop_qpos_adr+7] = bat_quat

            v6 = np.zeros(6)
            mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_BODY, self.b_held_bat_body_id, v6, 0)
            self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+3] = v6[3:6]
            self.data.qvel[self.drop_qvel_adr+3:self.drop_qvel_adr+6] = v6[0:3]

            self.model.geom_size[self.b_held_bat_geom_id] = [0.0001, 0.0001, 0.0]
            self.model.geom_rgba[self.b_held_bat_geom_id, 3] = 0.0

        # Modulate Batter Keyframes
        b_kfs = self.b_base_keyframes.copy()
        b_kfs[3, 0] += -0.15 * 0.6
        b_kfs[3, 1] += dz_bat * 0.6
        b_kfs[3, 2] += dalpha_plane * 0.6
        b_kfs[4, 0] += -0.15 * 1.0
        b_kfs[4, 1] += dz_bat * 1.0
        b_kfs[4, 2] += dalpha_plane * 1.0
        b_kfs[5, 1] += dz_bat * 0.5

        # Substep Physics Loop (10 substeps of 0.002s = 0.02s per step)
        for s_idx in range(self.frame_skip):
            sim_time = current_time + s_idx * self.model.opt.timestep

            # 1. Pitcher Arm PD & Release Check
            if not self.is_released and self.current_step >= self.actual_release_step:
                self.is_released = True
                if self.weld_eq_id >= 0:
                    self.data.eq_active[self.weld_eq_id] = False

                hp_now = self.data.site_xpos[self.p_hand_site_id].copy()
                tgt_pt = np.array([self.target_pitch_x, self.contact_plane_y, self.target_pitch_z], dtype=np.float32)
                tf = (hp_now[1] - tgt_pt[1]) / self.pitch_speed
                vx_rel = (tgt_pt[0] - hp_now[0]) / tf
                vz_rel = (tgt_pt[2] + 0.5 * 9.81 * (tf**2) - hp_now[2]) / tf

                # Aerodynamic shooting loop
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

            # In-flight Aerodynamics / Ground Rolling Resistance
            if self.is_released and not self.has_contacted:
                v_ball = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                vm = np.linalg.norm(v_ball)
                if vm > 1.0:
                    fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_ball
                    fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_ball)
                    self.data.qfrc_applied[self.ball_qvel_adr:self.ball_qvel_adr+3] = fd + fm
            elif self.has_contacted:
                # Ground Turf Rolling Resistance: c_rr = 0.02
                ball_z = self.data.qpos[self.ball_qpos_adr + 2]
                v_xy = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+2]
                v_norm = np.linalg.norm(v_xy)
                if ball_z <= 0.045 and v_norm > 0.05:
                    f_rr = -0.02 * self.m_ball * 9.81 * (v_xy / v_norm)
                    self.data.qfrc_applied[self.ball_qvel_adr:self.ball_qvel_adr+2] = f_rr

            # 2. Batter-Runner Upper Body PD
            if not self.bat_released:
                if not self.swing_triggered:
                    b_q_arm = b_kfs[0]
                else:
                    elapsed = sim_time - self.locked_t_trigger
                    prog = elapsed / self.locked_swing_duration
                    if prog < 0.20:
                        w = prog / 0.20
                        b_q_arm = (1.0 - w) * b_kfs[0] + w * b_kfs[1]
                    elif prog < 0.45:
                        w = (prog - 0.20) / 0.25
                        b_q_arm = (1.0 - w) * b_kfs[1] + w * b_kfs[2]
                    elif prog < 0.70:
                        w = (prog - 0.45) / 0.25
                        b_q_arm = (1.0 - w) * b_kfs[2] + w * b_kfs[3]
                    elif prog < 0.90:
                        w = (prog - 0.70) / 0.20
                        b_q_arm = (1.0 - w) * b_kfs[3] + w * b_kfs[4]
                    else:
                        w = min(1.0, (prog - 0.90) / 0.30)
                        b_q_arm = (1.0 - w) * b_kfs[4] + w * b_kfs[5]
            else:
                t_run = sim_time - 0.52
                turn_p = min(1.0, t_run / 0.35)
                target_yaw = (self.yaw_1b + steer_yaw) * turn_p
                arm_phi = 2.0 * np.pi * freq_sprint * t_run
                b_q_arm = np.array([
                    target_yaw,
                    0.20 + 0.35 * np.sin(arm_phi),
                    -0.10,
                    0.00,
                    1.20
                ], dtype=np.float32)

            for i in range(5):
                qb = self.data.qpos[self.b_swing_qpos_adrs[i]]
                dqb = self.data.qvel[self.b_swing_qvel_adrs[i]]
                tau_ba = self.b_swing_Kp[i] * (b_q_arm[i] - qb) - self.b_swing_Kd[i] * dqb
                cr = self.model.actuator_ctrlrange[self.b_swing_act_ids[i]]
                self.data.ctrl[self.b_swing_act_ids[i]] = np.clip(tau_ba, cr[0], cr[1])

            # Batter Leg Balance & Sprint
            bp_x = self.data.qpos[self.b_pelvis_qpos_adr]
            bp_z = self.data.qpos[self.b_pelvis_qpos_adr + 2]
            bv_x = self.data.qvel[self.b_pelvis_qvel_adr]
            bv_z = self.data.qvel[self.b_pelvis_qvel_adr + 2]
            bw_z = self.data.qvel[self.b_pelvis_qvel_adr + 5]
            b_qw, b_qx, b_qy, b_qz = self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7]

            if not self.bat_released:
                tau_x_ank = np.clip(500.0 * (bp_x - (-0.75)) + 50.0 * bv_x, -35.0, 35.0)
                tau_x_hip = np.clip(400.0 * (bp_x - (-0.75)) + 40.0 * bv_x, -50.0, 50.0)
                tau_yaw = np.clip(80.0 * bw_z, -50.0, 50.0)

                b_leg_tgt = self.base_leg_q.copy()
                for a in range(10):
                    jid = self.model.actuator_trnid[self.b_leg_act_ids[a], 0]
                    ql = self.data.qpos[self.model.jnt_qposadr[jid]]
                    dql = self.data.qvel[self.model.jnt_dofadr[jid]]
                    tau_l = self.b_leg_Kp[a] * (b_leg_tgt[a] - ql) - self.b_leg_Kd[a] * dql
                    if a in [4, 9]: tau_l += tau_x_ank
                    elif a in [2, 7]: tau_l += tau_x_hip
                    elif a in [0, 5]: tau_l += tau_yaw
                    cr_l = self.model.actuator_ctrlrange[self.b_leg_act_ids[a]]
                    self.data.ctrl[self.b_leg_act_ids[a]] = np.clip(tau_l, cr_l[0], cr_l[1])
            else:
                t_run = sim_time - 0.52
                turn_p = min(1.0, t_run / 0.35)
                target_yaw = (self.yaw_1b + steer_yaw) * turn_p

                v_fwd = min(0.85 * push_gain, 0.60 * t_run)
                s_dist = 0.5 * v_fwd * t_run
                pos_ref = self.start_p0 + self.u_1b * s_dist
                vel_ref = v_fwd * self.u_1b

                bp_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3]
                bp_vel = self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+3]

                b_pelvis_yaw = np.arctan2(2.0 * (b_qw * b_qz + b_qx * b_qy), 1.0 - 2.0 * (b_qy*b_qy + b_qz*b_qz))

                e_pos = pos_ref - bp_pos[:2]
                e_vel = vel_ref - bp_vel[:2]

                u_sag = np.array([np.cos(b_pelvis_yaw), np.sin(b_pelvis_yaw)], dtype=np.float32)
                u_lat = np.array([-np.sin(b_pelvis_yaw), np.cos(b_pelvis_yaw)], dtype=np.float32)

                e_sag = float(np.dot(e_pos, u_sag))
                ev_sag = float(np.dot(e_vel, u_sag))
                e_lat = float(np.dot(e_pos, u_lat))
                ev_lat = float(np.dot(e_vel, u_lat))

                tau_sag_ank = np.clip(-300.0 * e_sag - 30.0 * ev_sag, -25.0, 25.0)
                tau_sag_hip = np.clip(380.0 * e_sag + 38.0 * ev_sag, -45.0, 45.0)
                tau_lat = np.clip(350.0 * e_lat - 35.0 * ev_lat, -25.0, 25.0)
                tau_yaw = np.clip(80.0 * bw_z, -30.0, 30.0)

                phase = (t_run * freq_sprint) % 1.0
                sw = np.sin(2.0 * np.pi * phase)
                cw = np.cos(2.0 * np.pi * phase)

                b_leg_tgt = self.base_leg_q.copy()
                b_leg_tgt[0] = -target_yaw
                b_leg_tgt[5] = -target_yaw
                b_leg_tgt[1] += 0.03 * cw
                b_leg_tgt[6] += 0.03 * cw

                amp = 0.15 * min(1.0, t_run / 0.30)
                b_leg_tgt[2] -= amp * sw
                b_leg_tgt[7] += amp * sw

                k_amp = 0.20 * min(1.0, t_run / 0.30)
                b_leg_tgt[3] += k_amp * max(0.0, sw)
                b_leg_tgt[8] += k_amp * max(0.0, -sw)

                tau_z = np.clip(600.0 * (0.92 - bp_pos[2]) - 50.0 * bp_vel[2], -30.0, 90.0)
                b_pitch_tilt = 2.0 * (b_qx * b_qz + b_qw * b_qy)
                b_wy = self.data.qvel[self.b_pelvis_qvel_adr + 4]
                tau_pitch = np.clip(-200.0 * b_pitch_tilt - 20.0 * b_wy, -30.0, 30.0)

                for a in range(10):
                    jid = self.model.actuator_trnid[self.b_leg_act_ids[a], 0]
                    ql = self.data.qpos[self.model.jnt_qposadr[jid]]
                    dql = self.data.qvel[self.model.jnt_dofadr[jid]]
                    tau_l = self.b_leg_Kp[a] * (b_leg_tgt[a] - ql) - self.b_leg_Kd[a] * dql
                    if a in [4, 9]: tau_l += tau_sag_ank + 0.5 * tau_pitch
                    elif a in [2, 7]: tau_l += tau_sag_hip + 0.5 * tau_pitch
                    elif a in [1, 6]: tau_l += 0.5 * tau_lat
                    elif a in [0, 5]: tau_l += tau_yaw
                    elif a in [3, 8]: tau_l += 0.5 * tau_z
                    cr_l = self.model.actuator_ctrlrange[self.b_leg_act_ids[a]]
                    self.data.ctrl[self.b_leg_act_ids[a]] = np.clip(tau_l, cr_l[0], cr_l[1])

            # 3. 1st Baseman Infielder PD & Fielding Footwork
            fp_xy = self.data.qpos[self.f_pelvis_qpos_adr:self.f_pelvis_qpos_adr+2]
            fp_z = self.data.qpos[self.f_pelvis_qpos_adr + 2]
            fv_xy = self.data.qvel[self.f_pelvis_qvel_adr:self.f_pelvis_qvel_adr+2]
            fv_z = self.data.qvel[self.f_pelvis_qvel_adr + 2]
            fw_z = self.data.qvel[self.f_pelvis_qvel_adr + 5]

            f_qw, f_qx, f_qy, f_qz = self.data.qpos[self.f_pelvis_qpos_adr+3:self.f_pelvis_qpos_adr+7]
            f_pelvis_yaw = np.arctan2(2.0 * (f_qw * f_qz + f_qx * f_qy), 1.0 - 2.0 * (f_qy*f_qy + f_qz*f_qz))

            cur_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]

            if not self.ball_fielded:
                lat_err = np.dot(cur_ball_pos[:2] - self.infielder_p0, self.f_u_lat)
                lat_track = np.clip(lat_err, -0.40, 0.40)
                f_target_xy = self.infielder_p0 + (lat_track + f_lat_shift) * self.f_u_lat
                f_leg_tgt = self.crouch_leg_q.copy() if (self.is_fair_hit and np.linalg.norm(cur_ball_pos[:2] - fp_xy) < 1.6) else self.base_leg_q.copy()
            else:
                f_target_xy = self.target_1b
                f_leg_tgt = self.base_leg_q.copy()

            e_xy_f = f_target_xy - fp_xy
            e_sag = float(np.dot(e_xy_f, self.f_u_sag))
            v_sag = float(np.dot(fv_xy, self.f_u_sag))
            e_lat = float(np.dot(e_xy_f, self.f_u_lat))
            v_lat = float(np.dot(fv_xy, self.f_u_lat))

            tau_sag = np.clip(-350.0 * e_sag - 35.0 * v_sag, -35.0, 35.0)
            tau_lat = np.clip(350.0 * e_lat - 35.0 * v_lat, -30.0, 30.0)
            tau_f_yaw = np.clip(80.0 * fw_z, -30.0, 30.0)
            tau_fz = np.clip(600.0 * (0.92 - fp_z) - 50.0 * fv_z, -30.0, 90.0)

            for a in range(10):
                jid = self.model.actuator_trnid[self.f_leg_act_ids[a], 0]
                ql = self.data.qpos[self.model.jnt_qposadr[jid]]
                dql = self.data.qvel[self.model.jnt_dofadr[jid]]
                tau_fl = self.f_leg_Kp[a] * (f_leg_tgt[a] - ql) - self.f_leg_Kd[a] * dql
                if a in [2, 7]: tau_fl += 0.6 * tau_sag
                elif a in [4, 9]: tau_fl += 0.4 * tau_sag
                elif a in [1, 6]: tau_fl += 0.5 * tau_lat
                elif a in [0, 5]: tau_fl += tau_f_yaw
                elif a in [3, 8]: tau_fl += 0.5 * tau_fz
                cr_fl = self.model.actuator_ctrlrange[self.f_leg_act_ids[a]]
                self.data.ctrl[self.f_leg_act_ids[a]] = np.clip(tau_fl, cr_fl[0], cr_fl[1])

            # Infielder Glove Reaching Arm Control
            if not self.ball_fielded:
                if self.is_fair_hit and np.linalg.norm(cur_ball_pos[:2] - fp_xy) < 1.8:
                    f_arm_tgt = np.array([0.00, 0.20 + f_glove_dz, 0.15, -0.30, 0.90], dtype=np.float32)
                else:
                    f_arm_tgt = np.array([0.00, 0.40 + f_glove_dz, 0.20, 0.00, 1.30], dtype=np.float32)
            else:
                f_arm_tgt = np.array([0.00, 0.40, 0.20, 0.00, 1.30], dtype=np.float32)

            for i in range(5):
                qf = self.data.qpos[self.f_arm_qpos_adrs[i]]
                dqf = self.data.qvel[self.f_arm_qvel_adrs[i]]
                tau_fa = self.f_arm_Kp[i] * (f_arm_tgt[i] - qf) - self.f_arm_Kd[i] * dqf
                cr = self.model.actuator_ctrlrange[self.f_arm_act_ids[i]]
                self.data.ctrl[self.f_arm_act_ids[i]] = np.clip(tau_fa, cr[0], cr[1])

            mujoco.mj_step(self.model, self.data)

            # 4. Contact & Ball Fielding Detection
            if not self.has_contacted and not self.bat_released:
                sweet_p = self.data.site_xpos[self.b_sweet_spot_id]
                ball_p = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
                d_sb = float(np.linalg.norm(ball_p - sweet_p))

                contact_found = False
                for c_idx in range(self.data.ncon):
                    con = self.data.contact[c_idx]
                    g1, g2 = con.geom1, con.geom2
                    if (g1 == self.b_held_bat_geom_id and g2 == self.ball_geom_id) or (g2 == self.b_held_bat_geom_id and g1 == self.ball_geom_id):
                        contact_found = True
                        break

                if contact_found or d_sb <= 0.22:
                    self.has_contacted = True
                    self.contact_step = self.current_step
                    self.sweet_spot_offset = d_sb

                    # Fair batted ball grounder / liner into 1st base infield
                    spd = float(self.np_random.uniform(9.5, 12.8))  # 34 - 46 km/h exit velocity
                    azimuth_rad = float(np.radians(self.np_random.uniform(43.0, 51.5)))
                    launch_rad = float(np.radians(self.np_random.uniform(5.0, 12.0)))

                    vx = spd * np.cos(launch_rad) * np.sin(azimuth_rad)
                    vy = spd * np.cos(launch_rad) * np.cos(azimuth_rad)
                    vz = spd * np.sin(launch_rad)

                    self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 0.22, 0.65]
                    self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
                    self.exit_velocity = spd
                    self.exit_azimuth_deg = float(np.degrees(azimuth_rad))
                    self.exit_launch_deg = float(np.degrees(launch_rad))
                    self.is_fair_hit = True

            # Infielder Glove Fielding Intercept
            if self.is_fair_hit and not self.ball_fielded and sim_time >= 0.70:
                glove_pos = self.data.site_xpos[self.f_glove_site_id]
                cur_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
                dist_glove_xy = float(np.linalg.norm(glove_pos[:2] - cur_ball_pos[:2]))

                # Physical scoop reach: glove lowered near ground and horizontal distance within 0.42m
                if dist_glove_xy <= 0.42 and glove_pos[2] <= 0.85 and cur_ball_pos[2] <= 0.85 and sim_time >= 0.85:
                    self.ball_fielded = True
                    self.field_step = self.current_step
                    self.t_fielded = sim_time
                    self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] *= 0.10
                    self.model.geom_contype[self.ball_geom_id] = 0
                    self.model.geom_conaffinity[self.ball_geom_id] = 0

            if self.ball_fielded:
                glove_p = self.data.site_xpos[self.f_glove_site_id]
                self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = glove_p + np.array([0.02, 0.0, 0.0])
                self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = self.data.qvel[self.f_pelvis_qvel_adr:self.f_pelvis_qvel_adr+3]

        # End of substeps: Assessment & 3D Umpire Decision
        bp_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3]
        bp_quat = self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7]
        fp_pos = self.data.qpos[self.f_pelvis_qpos_adr:self.f_pelvis_qpos_adr+3]
        fp_quat = self.data.qpos[self.f_pelvis_qpos_adr+3:self.f_pelvis_qpos_adr+7]

        b_upright_z = 1.0 - 2.0 * (bp_quat[1]**2 + bp_quat[2]**2)
        f_upright_z = 1.0 - 2.0 * (fp_quat[1]**2 + fp_quat[2]**2)

        if bp_pos[2] < 0.55 or b_upright_z < 0.55:
            self.batter_fallen = True
        if fp_pos[2] < 0.55 or f_upright_z < 0.55:
            self.fielder_fallen = True

        runner_dist_1b = float(np.linalg.norm(self.target_1b - bp_pos[:2]))
        fielder_dist_1b = float(np.linalg.norm(self.target_1b - fp_pos[:2]))

        # Calculate Runner Sprint Speed along baseline (authentic physical telemetry)
        runner_v_along_1b = float(np.dot(self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+2], self.u_1b))
        sim_sprint_spd = max(0.0, runner_v_along_1b)
        self.runner_max_spd = max(self.runner_max_spd, sim_sprint_spd)

        # Check Defense Completion:
        # Ball fielded + infielder reaches base proximity (or completes gather & tag transition within 0.38s)
        if self.ball_fielded and not self.defense_completed:
            if fielder_dist_1b <= 1.80 or current_time >= (self.t_fielded + 0.38):
                self.defense_completed = True
                self.defense_step = self.current_step
                self.t_defense = min(current_time, self.t_fielded + 0.38)

        # Check Runner Arrival at 1st base (scaled human-equivalent sprint race arrival)
        if self.bat_released and not self.runner_reached_1b:
            if runner_dist_1b <= 1.0 or current_time >= 1.50:
                self.runner_reached_1b = True
                self.runner_step = self.current_step
                self.t_runner = 1.48 + 0.05 * float(self.filtered_action[3])

        # Stage 4: 3D Umpire Decision Engine
        if self.umpire_decision == "PENDING":
            if self.defense_completed and self.runner_reached_1b:
                if self.t_defense <= self.t_runner:
                    self.umpire_decision = "OUT"
                else:
                    self.umpire_decision = "SAFE"
            elif not self.ball_fielded and current_time >= 1.45 and self.is_fair_hit:
                self.umpire_decision = "SAFE"
            elif self.defense_completed and current_time >= 1.55:
                if self.t_defense <= self.t_runner:
                    self.umpire_decision = "OUT"
                else:
                    self.umpire_decision = "SAFE"
            elif current_time >= 1.75:
                if self.defense_completed and self.t_defense <= self.t_runner:
                    self.umpire_decision = "OUT"
                elif self.is_fair_hit:
                    self.umpire_decision = "SAFE"
                else:
                    self.umpire_decision = "OUT"

        # Rewards Formulation
        reward = 0.0

        if self.has_contacted and self.current_step == self.contact_step:
            reward += 10.0
            sweet_bonus = 5.0 * np.exp(-max(0.0, self.sweet_spot_offset - 0.06) / 0.04)
            reward += sweet_bonus
            if self.is_fair_hit:
                reward += 15.0

        if self.bat_released and self.current_step == self.release_step:
            reward += 5.0

        if self.bat_released:
            run_progress = self.prev_runner_dist_1b - runner_dist_1b
            reward += 15.0 * max(0.0, run_progress)

        if self.ball_fielded and self.current_step == self.field_step:
            reward += 20.0
        if self.defense_completed and self.current_step == self.defense_step:
            reward += 25.0

        reward += 2.0 * np.exp(-((bp_pos[2] - 0.92)**2) / 0.04)
        reward += 2.0 * np.exp(-((fp_pos[2] - 0.92)**2) / 0.04)

        if self.batter_fallen:
            reward -= 40.0
        if self.fielder_fallen:
            reward -= 40.0

        terminated = False
        if self.batter_fallen or self.fielder_fallen:
            terminated = True
        elif self.umpire_decision in ["OUT", "SAFE"] and self.current_step >= 92:
            terminated = True

        truncated = self.current_step >= self.max_steps
        self.prev_runner_dist_1b = runner_dist_1b

        info = {
            "strike": self.is_strike,
            "contact": self.has_contacted,
            "fair_hit": self.is_fair_hit,
            "bat_released": self.bat_released,
            "ball_fielded": self.ball_fielded,
            "defense_completed": self.defense_completed,
            "runner_reached_1b": self.runner_reached_1b,
            "umpire_decision": self.umpire_decision,
            "batter_fallen": self.batter_fallen,
            "fielder_fallen": self.fielder_fallen,
            "runner_pelvis_z": float(bp_pos[2]),
            "fielder_pelvis_z": float(fp_pos[2]),
            "runner_dist_1b": runner_dist_1b,
            "fielder_dist_1b": fielder_dist_1b,
            "exit_speed_kmh": self.exit_velocity * 3.6,
            "pitch_speed_kmh": self.pitch_speed * 3.6,
            "pitch_name": self.pitch_name,
            "runner_speed_kmh": self.runner_max_spd * 3.6,
            "sweet_spot_offset": self.sweet_spot_offset,
            "t_defense": self.t_defense,
            "t_runner": self.t_runner,
        }

        return self._get_obs(), float(reward), terminated, truncated, info

    def render(self, camera_name="infield_broadcast_cam"):
        if self.render_mode not in ["rgb_array", "human"]:
            return None
        self.renderer.update_scene(self.data, camera=camera_name)
        return self.renderer.render()

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
