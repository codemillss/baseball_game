"""
BipedalDuelEnv: Phase 5 Full-Stadium Whole-Body Bipedal Pitcher vs Batter Closed-Loop Duel.

Combines:
- Live 10m Mound H1 Pitcher throwing Fastball (80-88 km/h), Slider (70-78 km/h), and Curveball (62-70 km/h)
  with aerodynamic drag & Magnus lift/drop/break.
- Full 19-DoF H1 Whole-Body Bipedal Batter on 6-DoF Floating Base Pelvis at home plate (Zero-Cheating).
- Real-time pitch perception: continuous ball tracking [x, v, t_remain], dynamic swing timing trigger,
  adaptive swing plane height / tilt / reach modulation, and athletic bipedal ZMP balance control.
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


class BipedalDuelEnv(gym.Env):
    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}

    def __init__(
        self,
        xml_path=None,
        render_mode=None,
        frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz control loop)
        pitch_types=None,  # list of allowed pitch types [0, 1, 2] (0: Fastball, 1: Slider, 2: Curveball)
    ):
        super().__init__()

        if xml_path is None:
            xml_path = os.path.join(parent_dir, "models", "h1_bipedal_duel.xml")

        self.xml_path = xml_path
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)

        self.render_mode = render_mode
        self.frame_skip = frame_skip
        self.dt = self.model.opt.timestep * self.frame_skip  # 0.02s
        self.pitch_types = pitch_types if pitch_types is not None else [0, 1, 2]

        # Identify Bodies & Sites
        self.p_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "p_pelvis")
        self.b_pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "b_pelvis")
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")

        self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")
        self.p_hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")
        self.weld_eq_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_EQUALITY, "p_ball_weld")

        # Joints & Freejoints
        ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
        self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]

        b_pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "b_pelvis_joint")
        self.b_pelvis_qpos_adr = self.model.jnt_qposadr[b_pelvis_jnt_id]
        self.b_pelvis_qvel_adr = self.model.jnt_dofadr[b_pelvis_jnt_id]

        # Pitcher Arm Actuators [torso, rsp, rsr, rsy, relb]
        self.p_act_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
        self.p_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.p_act_names]
        self.p_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
        self.p_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]

        # Batter Swing Actuators [torso, rsp, rsr, rsy, relb]
        self.b_swing_act_names = ["b_torso", "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"]
        self.b_swing_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_swing_act_names]
        self.b_swing_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_swing_act_ids]
        self.b_swing_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_swing_act_ids]

        # Batter Leg Actuators (10 motors for whole-body balance)
        self.b_leg_act_names = [
            "b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle",
            "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle",
        ]
        self.b_leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_leg_act_names]
        self.b_leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]
        self.b_leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_leg_act_ids]

        # Stance & Swing Gains
        self.p_Kp = np.array([450.0, 350.0, 250.0, 150.0, 150.0], dtype=np.float32)
        self.p_Kd = np.array([35.0,  25.0,  20.0,  12.0,  12.0], dtype=np.float32)

        self.b_swing_Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
        self.b_swing_Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)

        self.b_leg_Kp = np.array([350.0, 350.0, 450.0, 500.0, 250.0, 350.0, 350.0, 450.0, 500.0, 250.0], dtype=np.float32)
        self.b_leg_Kd = np.array([30.0,  30.0,  40.0,  45.0,  20.0,  30.0,  30.0,  40.0,  45.0,  20.0], dtype=np.float32)

        # Pitcher keyframes
        self.p_keyframes = np.array([
            [ 0.00,  0.00, -0.40,  0.00,  1.50],
            [ 0.80,  1.20, -0.60,  0.80,  1.60],
            [ 0.20, -0.20, -0.40,  0.30,  1.00],
            [-0.50, -1.40, -0.20, -0.20,  0.20],
            [-0.90, -1.80, -0.60, -0.50,  0.70],
        ], dtype=np.float32)

        # Batter athletic batting keyframes
        self.b_base_keyframes = np.array([
            [-0.40, -1.00,  0.00,  0.40,  1.50],
            [-0.60, -1.15,  0.00,  0.60,  1.70],
            [-0.10, -0.70, -0.05,  0.20,  1.20],
            [ 0.50, -0.30, -0.10, -0.10,  0.70],
            [ 1.15,  0.20, -0.08, -0.40,  0.35],
            [ 1.70,  0.80,  0.00, -0.70,  1.20]
        ], dtype=np.float32)

        # Batter nominal leg stance
        self.b_base_leg_q = np.array([
            0.0, 0.12, -0.35, 0.65, -0.30,  # Left leg
            0.0,-0.12, -0.35, 0.65, -0.30   # Right leg
        ], dtype=np.float32)

        # Aerodynamic constants
        self.rho = 1.205
        self.r_ball = 0.037
        self.m_ball = 0.145
        self.A_ball = np.pi * (self.r_ball ** 2)
        self.Cd = 0.32
        self.Cl = 0.24

        # Action: 6 dims for Whole-Body Batter
        # a[0]: dt_lead_lag swing timing adjustment (-0.040 to +0.040s)
        # a[1]: dz_bat plane height adjustment (-0.25 to +0.25rad)
        # a[2]: dalpha_plane attack tilt angle adjustment (-0.16 to +0.16rad)
        # a[3]: dpower_dur swing duration adjustment (-0.02 to +0.02s)
        # a[4]: delbow_reach elbow reach adjustment (-0.20 to +0.20rad)
        # a[5]: dweight_shift leg front/back load transfer (-0.10 to +0.10rad)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)

        # Observation: 38 dims (Full match with Phase 3 whole-body observation layout)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(38,), dtype=np.float32)

        self.current_step = 0
        self.max_steps = 55
        self.prev_action = np.zeros(6, dtype=np.float32)
        self.filtered_action = np.zeros(6, dtype=np.float32)

        self.swing_triggered = False
        self.locked_t_trigger = 0.0
        self.locked_swing_duration = 0.17
        self.has_contacted = False
        self.contact_reward_given = False
        self.contact_step = -1
        self.contact_ball_pos = None
        self.contact_sweet_pos = None
        self.exit_velocity = 0.0
        self.exit_azimuth_deg = 0.0
        self.exit_launch_deg = 0.0
        self.is_fair_hit = False
        self.has_fallen = False
        self.is_strike = False

        self.is_released = False
        self.actual_release_step = 22
        self.pitch_type = 0
        self.pitch_name = "Fastball"
        self.pitch_speed = 22.5
        self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
        self.target_pitch_x = 0.08
        self.target_pitch_z = 0.58
        self.contact_plane_y = -0.16
        self.contact_lead_time = 0.200
        self.nominal_swing_duration = 0.17

        self.rel_vx = 0.0
        self.rel_vy = -22.5
        self.rel_vz = 0.0

        self.renderer = None
        if self.render_mode in ["rgb_array", "human"]:
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        self.current_step = 0
        self.prev_action = np.zeros(6, dtype=np.float32)
        self.filtered_action = np.zeros(6, dtype=np.float32)
        self.swing_triggered = False
        self.locked_t_trigger = 0.0
        self.locked_swing_duration = 0.17
        self.has_contacted = False
        self.contact_reward_given = False
        self.contact_step = -1
        self.contact_ball_pos = None
        self.contact_sweet_pos = None
        self.exit_velocity = 0.0
        self.exit_azimuth_deg = 0.0
        self.exit_launch_deg = 0.0
        self.is_fair_hit = False
        self.has_fallen = False
        self.is_strike = False
        self.is_released = False

        # 1. Pitch Type & Target Configuration across Strike Zone
        self.pitch_type = int(self.np_random.choice(self.pitch_types))
        self.target_pitch_x = float(self.np_random.uniform(0.06, 0.14))
        self.target_pitch_z = float(self.np_random.uniform(0.55, 0.65))

        if self.pitch_type == 0:
            self.pitch_name = "Fastball"
            self.pitch_speed = float(self.np_random.uniform(22.0, 24.0))  # 79.2 - 86.4 km/h
            self.pitch_spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
        elif self.pitch_type == 1:
            self.pitch_name = "Slider"
            self.pitch_speed = float(self.np_random.uniform(19.5, 21.5))  # 70.2 - 77.4 km/h
            self.pitch_spin = np.array([-30.0, 0.0, 150.0], dtype=np.float32)
        else:
            self.pitch_name = "Curveball"
            self.pitch_speed = float(self.np_random.uniform(17.5, 19.5))  # 63.0 - 70.2 km/h
            self.pitch_spin = np.array([170.0, 0.0, -20.0], dtype=np.float32)

        dt_pitcher_rel = float(self.np_random.uniform(-0.010, 0.010))
        self.actual_release_step = int(np.clip(22 + int(dt_pitcher_rel / self.dt), 20, 24))

        # 2. Batter Goal Condition Vector (Pull / Center / Push)
        target_azimuth_deg = float(self.np_random.uniform(-30.0, 30.0))
        self.target_azimuth_rad = float(np.radians(target_azimuth_deg))
        target_launch_deg = float(self.np_random.uniform(14.0, 30.0))
        self.target_launch_rad = float(np.radians(target_launch_deg))
        self.target_exit_vel = float(self.np_random.uniform(12.0, 18.0))

        # 3. Initialize Pitcher Robot
        for i, adr in enumerate(self.p_qpos_adrs):
            self.data.qpos[adr] = self.p_keyframes[0, i]

        # 4. Initialize Batter Robot (Full 6-DoF Pelvis Floating Base at x = -0.75m)
        self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3] = [-0.75, 0.00, 0.88]
        self.data.qpos[self.b_pelvis_qpos_adr+3:self.b_pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+6] = 0.0

        for i, adr in enumerate(self.b_leg_qpos_adrs):
            self.data.qpos[adr] = self.b_base_leg_q[i]

        for i, adr in enumerate(self.b_swing_qpos_adrs):
            self.data.qpos[adr] = self.b_base_keyframes[0, i]

        # 5. Connect ball to pitcher hand via weld
        if self.weld_eq_id >= 0:
            self.data.eq_active[self.weld_eq_id] = True

        mujoco.mj_forward(self.model, self.data)
        hand_pos = self.data.site_xpos[self.p_hand_site_id].copy()
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
        self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+6] = 0.0
        mujoco.mj_forward(self.model, self.data)

        return self._get_obs(), {}

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        
        # Time remaining to contact plane (y = -0.16m)
        if self.is_released and abs(ball_vel[1]) > 1.0 and ball_pos[1] > self.contact_plane_y:
            t_remain = float((ball_pos[1] - self.contact_plane_y) / abs(ball_vel[1]))
        elif not self.is_released:
            est_vy = self.pitch_speed
            t_remain = float((9.4 - self.contact_plane_y) / est_vy + (self.actual_release_step - self.current_step) * self.dt)
        else:
            t_remain = 0.0

        goals = np.array([self.target_azimuth_rad, self.target_launch_rad, self.target_exit_vel], dtype=np.float32)
        swing_qpos = np.array([self.data.qpos[adr] for adr in self.b_swing_qpos_adrs], dtype=np.float32)
        swing_qvel = np.array([self.data.qvel[adr] for adr in self.b_swing_qvel_adrs], dtype=np.float32)

        sweet_pos = self.data.site_xpos[self.sweet_spot_id]
        sweet_v = np.zeros(6, dtype=np.float64)
        mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_SITE, self.sweet_spot_id, sweet_v, 0)
        sweet_vel = sweet_v[3:6]

        pelvis_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3]
        pelvis_vel = self.data.qvel[self.b_pelvis_qvel_adr:self.b_pelvis_qvel_adr+3]

        obs = np.concatenate([
            ball_pos,                                    # 3
            ball_vel,                                    # 3
            np.array([t_remain], dtype=np.float32),      # 1
            goals,                                       # 3
            swing_qpos,                                  # 5
            swing_qvel,                                  # 5
            sweet_pos,                                   # 3
            sweet_vel,                                   # 3
            pelvis_pos,                                  # 3
            pelvis_vel,                                  # 3
            self.prev_action,                            # 6
        ])
        return obs.astype(np.float32)

    def step(self, action):
        action = np.clip(action, -1.0, 1.0).astype(np.float32)
        self.filtered_action = 0.6 * self.filtered_action + 0.4 * action

        dt_lead_lag = float(self.filtered_action[0]) * 0.040
        dz_bat = float(self.filtered_action[1]) * 0.25
        dalpha_plane = float(self.filtered_action[2]) * 0.16
        dpower_dur = float(self.filtered_action[3]) * 0.02
        delbow_reach = float(self.filtered_action[4]) * 0.20
        dweight_shift = float(self.filtered_action[5]) * 0.10

        current_time = self.current_step * self.dt

        # Dynamic Swing Trigger based on real-time pitch perception:
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        
        if self.is_released and abs(ball_vel[1]) > 3.0 and ball_pos[1] > self.contact_plane_y:
            t_remain = (ball_pos[1] - self.contact_plane_y) / abs(ball_vel[1])
            trigger_lead = self.contact_lead_time + dt_lead_lag
            if not self.swing_triggered and t_remain <= trigger_lead:
                self.swing_triggered = True
                self.locked_t_trigger = current_time
                self.locked_swing_duration = max(0.13, self.nominal_swing_duration + dpower_dur)

        # Modulate Batter Keyframes
        b_kfs = self.b_base_keyframes.copy()
        b_kfs[3, 1] += dz_bat * 0.6
        b_kfs[3, 2] += dalpha_plane * 0.6
        b_kfs[3, 4] += delbow_reach * 0.6
        b_kfs[4, 1] += dz_bat * 1.0
        b_kfs[4, 2] += dalpha_plane * 1.0
        b_kfs[4, 4] += delbow_reach * 1.0
        b_kfs[5, 1] += dz_bat * 0.5
        b_kfs[5, 2] += dalpha_plane * 0.5

        # Dynamic Leg Target with Athletic Weight Shift
        b_leg_target = self.b_base_leg_q.copy()
        if self.swing_triggered:
            b_leg_target[2] -= dweight_shift # left hip brace forward
            b_leg_target[7] += dweight_shift # right hip drive

        # Substep Physics (frame_skip = 10 substeps of 0.002s = 0.02s per env step)
        for s_idx in range(self.frame_skip):
            sim_time = current_time + s_idx * self.model.opt.timestep

            # 1. Pitcher Arm Kinematics & PD Control
            t_norm = (self.current_step + s_idx / self.frame_skip) / self.actual_release_step
            if t_norm < 0.35:
                w = t_norm / 0.35
                p_target = (1.0 - w) * self.p_keyframes[0] + w * self.p_keyframes[1]
            elif t_norm < 0.70:
                w = (t_norm - 0.35) / 0.35
                p_target = (1.0 - w) * self.p_keyframes[1] + w * self.p_keyframes[2]
            elif t_norm <= 1.0:
                w = (t_norm - 0.70) / 0.30
                p_target = (1.0 - w) * self.p_keyframes[2] + w * self.p_keyframes[3]
            else:
                w = min(1.0, (t_norm - 1.0) / 0.40)
                p_target = (1.0 - w) * self.p_keyframes[3] + w * self.p_keyframes[4]

            for i in range(5):
                qp = self.data.qpos[self.p_qpos_adrs[i]]
                dqp = self.data.qvel[self.p_qvel_adrs[i]]
                tau_p = self.p_Kp[i] * (p_target[i] - qp) - self.p_Kd[i] * dqp
                cr_p = self.model.actuator_ctrlrange[self.p_act_ids[i]]
                self.data.ctrl[self.p_act_ids[i]] = np.clip(tau_p, cr_p[0], cr_p[1])

            # 2. Batter Arm Kinematics & PD Control
            if not self.swing_triggered:
                b_target = b_kfs[0]
            else:
                elapsed = sim_time - self.locked_t_trigger
                prog = elapsed / self.locked_swing_duration
                if prog < 0.20:
                    w = prog / 0.20
                    b_target = (1.0 - w) * b_kfs[0] + w * b_kfs[1]
                elif prog < 0.45:
                    w = (prog - 0.20) / 0.25
                    b_target = (1.0 - w) * b_kfs[1] + w * b_kfs[2]
                elif prog < 0.70:
                    w = (prog - 0.45) / 0.25
                    b_target = (1.0 - w) * b_kfs[2] + w * b_kfs[3]
                elif prog < 0.90:
                    w = (prog - 0.70) / 0.20
                    b_target = (1.0 - w) * b_kfs[3] + w * b_kfs[4]
                else:
                    w = min(1.0, (prog - 0.90) / 0.30)
                    b_target = (1.0 - w) * b_kfs[4] + w * b_kfs[5]

            for i in range(5):
                qb = self.data.qpos[self.b_swing_qpos_adrs[i]]
                dqb = self.data.qvel[self.b_swing_qvel_adrs[i]]
                tau_b = self.b_swing_Kp[i] * (b_target[i] - qb) - self.b_swing_Kd[i] * dqb
                cr_b = self.model.actuator_ctrlrange[self.b_swing_act_ids[i]]
                self.data.ctrl[self.b_swing_act_ids[i]] = np.clip(tau_b, cr_b[0], cr_b[1])

            # 3. Batter Leg Stance Balance PD Control (10 Leg Motors)
            for a in range(10):
                jid = self.model.actuator_trnid[self.b_leg_act_ids[a], 0]
                ql = self.data.qpos[self.model.jnt_qposadr[jid]]
                dql = self.data.qvel[self.model.jnt_dofadr[jid]]
                tau_l = self.b_leg_Kp[a] * (b_leg_target[a] - ql) - self.b_leg_Kd[a] * dql
                cr_l = self.model.actuator_ctrlrange[self.b_leg_act_ids[a]]
                self.data.ctrl[self.b_leg_act_ids[a]] = np.clip(tau_l, cr_l[0], cr_l[1])

            # 4. Ball Release Check: Solve aerodynamic release from actual hand pos at release moment
            if not self.is_released and self.current_step >= self.actual_release_step:
                self.is_released = True
                if self.weld_eq_id >= 0:
                    self.data.eq_active[self.weld_eq_id] = False

                hp_now = self.data.site_xpos[self.p_hand_site_id].copy()
                target_pt = np.array([self.target_pitch_x, self.contact_plane_y, self.target_pitch_z], dtype=np.float32)
                tf = (hp_now[1] - target_pt[1]) / self.pitch_speed
                vx_rel = (target_pt[0] - hp_now[0]) / tf
                vz_rel = (target_pt[2] + 0.5 * 9.81 * (tf**2) - hp_now[2]) / tf

                # Aerodynamic Shooting Loop
                for _ in range(3):
                    p_s = hp_now.copy()
                    v_s = np.array([vx_rel, -self.pitch_speed, vz_rel], dtype=np.float32)
                    while p_s[1] > target_pt[1]:
                        vm = np.linalg.norm(v_s)
                        fd = -0.5 * self.rho * self.Cd * self.A_ball * vm * v_s
                        fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v_s)
                        acc = (fd + fm) / self.m_ball + np.array([0, 0, -9.81], dtype=np.float32)
                        v_s += acc * 0.002
                        p_s += v_s * 0.002
                    err = p_s - target_pt
                    vx_rel -= err[0] / tf
                    vz_rel -= err[2] / tf

                self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx_rel, -self.pitch_speed, vz_rel]

            # 5. Aerodynamic Drag & Magnus Force on Baseball
            if self.is_released and not self.has_contacted:
                v = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                v_norm = np.linalg.norm(v)
                if v_norm > 1.0:
                    f_drag = -0.5 * self.rho * self.Cd * self.A_ball * v_norm * v
                    f_magnus = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(self.pitch_spin, v)
                    self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += (f_drag + f_magnus) / self.m_ball * self.model.opt.timestep

            # MuJoCo Physics Step
            mujoco.mj_step(self.model, self.data)

            # 6. Contact Detection (Bat Barrel vs Baseball)
            for c_idx in range(self.data.ncon):
                con = self.data.contact[c_idx]
                g1, g2 = con.geom1, con.geom2
                if (g1 == self.bat_geom_id and g2 == self.ball_geom_id) or (g2 == self.bat_geom_id and g1 == self.ball_geom_id):
                    if not self.has_contacted:
                        self.has_contacted = True
                        self.contact_step = self.current_step
                        self.contact_ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
                        self.contact_sweet_pos = self.data.site_xpos[self.sweet_spot_id].copy()

        self.current_step += 1
        obs = self._get_obs()

        # Check Strike Zone at Plate (y <= 0.0m)
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        if ball_pos[1] <= 0.10:
            if abs(ball_pos[0]) <= 0.216 and 0.45 <= ball_pos[2] <= 0.85:
                self.is_strike = True

        # Pelvis Balance & Fall Detection
        pelvis_pos = self.data.qpos[self.b_pelvis_qpos_adr:self.b_pelvis_qpos_adr+3]
        pelvis_z = pelvis_pos[2]
        if pelvis_z < 0.65:
            self.has_fallen = True

        terminated = False
        truncated = False

        if self.has_contacted:
            vx, vy, vz = ball_vel
            self.exit_velocity = float(np.linalg.norm(ball_vel))
            if vy > 0.10:
                self.is_fair_hit = True
                self.exit_azimuth_deg = float(np.degrees(np.arctan2(vx, vy)))
                v_horiz = np.sqrt(vx**2 + vy**2)
                self.exit_launch_deg = float(np.degrees(np.arctan2(vz, v_horiz)))

        if self.has_fallen:
            terminated = True
        elif self.has_contacted and self.current_step >= self.contact_step + 8:
            terminated = True
        elif ball_pos[1] < -1.0:
            terminated = True
        elif self.current_step >= self.max_steps:
            truncated = True

        # Reward Formulation
        reward = 0.0

        # 1. Bipedal Standing Balance Reward
        r_balance = 5.0 * np.exp(-15.0 * ((pelvis_z - 0.88) ** 2))
        reward += r_balance

        if self.has_fallen:
            reward -= 50.0

        sweet_err_cm = float(np.linalg.norm(self.contact_ball_pos - self.contact_sweet_pos) * 100.0) if (self.has_contacted and self.contact_ball_pos is not None) else 0.0

        info = {
            "contact": self.has_contacted,
            "fair_hit": self.is_fair_hit,
            "has_fallen": self.has_fallen,
            "pelvis_z": float(pelvis_z),
            "exit_speed_kmh": float(self.exit_velocity * 3.6),
            "azimuth_deg": float(self.exit_azimuth_deg),
            "pitch_name": self.pitch_name,
            "pitch_speed_kmh": float(self.pitch_speed * 3.6),
            "sweet_offset_cm": sweet_err_cm,
            "is_strike": self.is_strike,
        }

        # 2. Contact, Sweet Spot, and Fair Hit Rewards
        if terminated and self.has_contacted and not self.contact_reward_given:
            self.contact_reward_given = True
            r_contact = 15.0
            sweet_offset = float(np.linalg.norm(self.contact_ball_pos - self.contact_sweet_pos))
            r_sweet = 10.0 * float(np.exp(-25.0 * sweet_offset))
            r_fair = 12.0 if self.is_fair_hit else -5.0

            # Directional aim reward
            az_err = abs(np.radians(self.exit_azimuth_deg) - self.target_azimuth_rad)
            r_aim = 5.0 * float(np.exp(-10.0 * (az_err ** 2)))

            # Exit speed bonus
            r_speed = 0.25 * float(self.exit_velocity)

            reward += r_contact + r_sweet + r_fair + r_aim + r_speed

        reward -= 0.01 * float(np.sum(action ** 2))
        self.prev_action = action.copy()

        return obs, reward, terminated, truncated, info

    def render(self, camera_name="duel_broadcast_cam"):
        if self.render_mode == "rgb_array" and self.renderer is not None:
            self.renderer.update_scene(self.data, camera=camera_name)
            return self.renderer.render()
        return None

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
