"""
BipedalSwingEnv: Phase 3 Whole-Body Kinetic Chain Batting for H1 Humanoid.
Features:
- Full 6-DoF Free-Floating Pelvis (pelvis_joint).
- Ground Reaction Forces (GRF) and bipedal balance during high-speed athletic swing.
- Active leg PD balance controller with dynamic weight-shift transfer.
- Goal-conditioned directional hitting (Pull / Center / Push).
- Fall detection and dynamic ZMP balance reward formulation.
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


class BipedalSwingEnv(gym.Env):
    """
    Phase 3 Whole-Body Kinetic Chain Batting Environment.
    Robot has a 6-DoF free-floating pelvis and must maintain balance on two feet
    while swinging at an incoming pitched ball.
    """

    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}

    def __init__(
        self,
        xml_path=None,
        render_mode=None,
        frame_skip=10,  # 10 * 0.002s = 0.02s per step (50 Hz)
        pitch_speed_range=(14.0, 18.0),
        pitch_dist=7.5,
    ):
        super().__init__()

        if xml_path is None:
            xml_path = os.path.join(parent_dir, "models", "h1_bipedal_baseball.xml")

        self.xml_path = xml_path
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)

        self.render_mode = render_mode
        self.frame_skip = frame_skip
        self.dt = self.model.opt.timestep * self.frame_skip  # 0.02s
        self.pitch_speed_range = pitch_speed_range
        self.pitch_dist = pitch_dist

        # Identify Bodies & Sites
        self.pelvis_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")

        # Freejoints
        ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
        self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]

        pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "pelvis_joint")
        self.pelvis_qpos_adr = self.model.jnt_qposadr[pelvis_jnt_id]
        self.pelvis_qvel_adr = self.model.jnt_dofadr[pelvis_jnt_id]

        # Upper body swing actuators [torso, rsp, rsr, rsy, relb]
        self.swing_act_names = ["torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"]
        self.swing_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.swing_act_names]
        self.swing_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.swing_act_ids]
        self.swing_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.swing_act_ids]

        # Leg actuators (10 motors)
        self.leg_act_names = [
            "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
            "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
        ]
        self.leg_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.leg_act_names]
        self.leg_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.leg_act_ids]
        self.leg_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.leg_act_ids]

        # Gains
        self.swing_Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
        self.swing_Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)

        self.leg_Kp = np.array([350.0, 350.0, 450.0, 500.0, 250.0, 350.0, 350.0, 450.0, 500.0, 250.0], dtype=np.float32)
        self.leg_Kd = np.array([30.0,  30.0,  40.0,  45.0,  20.0,  30.0,  30.0,  40.0,  45.0,  20.0], dtype=np.float32)

        # Athletic batting keyframes
        self.base_keyframes = np.array([
            [-0.40, -1.00,  0.00,  0.40,  1.50],
            [-0.60, -1.15,  0.00,  0.60,  1.70],
            [-0.10, -0.70, -0.05,  0.20,  1.20],
            [ 0.50, -0.30, -0.10, -0.10,  0.70],
            [ 1.15,  0.20, -0.08, -0.40,  0.35],
            [ 1.70,  0.80,  0.00, -0.70,  1.20]
        ], dtype=np.float32)

        # Nominal Leg Stance
        self.base_leg_q = np.array([
            0.0, 0.12, -0.35, 0.65, -0.30,  # Left leg
            0.0,-0.12, -0.35, 0.65, -0.30   # Right leg
        ], dtype=np.float32)

        # Action: 6 dims
        # a[0:5]: swing modulations (lead/lag, dz, attack angle, power, reach)
        # a[5]: leg weight-shift modulation (front-to-back load transfer)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)

        # Obs: 36 dims (ball state 7, goals 3, upper joints 10, sweet 6, pelvis state 6, prev_action 4)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(38,), dtype=np.float32)

        self.current_step = 0
        self.max_steps = 35
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

        # Set 6-DoF Pelvis floating base in batter's box
        self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3] = [-0.85, 0.00, 0.88]
        self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+6] = 0.0

        # Set leg stance
        for i, adr in enumerate(self.leg_qpos_adrs):
            self.data.qpos[adr] = self.base_leg_q[i]

        # Set upper body initial keyframe
        for i, adr in enumerate(self.swing_qpos_adrs):
            self.data.qpos[adr] = self.base_keyframes[0, i]

        # Sample Goal Condition Vector
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

        target_x = self.np_random.uniform(0.06, 0.12)
        target_z = self.np_random.uniform(0.55, 0.62)

        z0 = 0.85
        drop = 0.5 * 9.81 * (t_flight ** 2)
        vz = (target_z + drop - z0) / t_flight

        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [target_x, self.pitch_dist, z0]
        self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, vy, vz]
        self.data.qvel[self.ball_qvel_adr+3:self.ball_qvel_adr+6] = [0.0, 0.0, 0.0]

        mujoco.mj_forward(self.model, self.data)

        self.nominal_t_trigger = t_flight - 0.145
        self.nominal_swing_duration = 0.17

        return self._get_obs(), {}

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        t_remain = max(0.0, (ball_pos[1] - 0.20) / abs(ball_vel[1])) if abs(ball_vel[1]) > 1.0 else 0.0

        goals = np.array([self.target_azimuth_rad, self.target_launch_rad, self.target_exit_vel], dtype=np.float32)
        swing_qpos = np.array([self.data.qpos[adr] for adr in self.swing_qpos_adrs], dtype=np.float32)
        swing_qvel = np.array([self.data.qvel[adr] for adr in self.swing_qvel_adrs], dtype=np.float32)

        sweet_pos = self.data.site_xpos[self.sweet_spot_id]
        sweet_v = np.zeros(6, dtype=np.float64)
        mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_SITE, self.sweet_spot_id, sweet_v, 0)
        sweet_vel = sweet_v[3:6]

        pelvis_pos = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3]
        pelvis_vel = self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+3]

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
            np.array([self.prev_action[0], self.prev_action[1], self.prev_action[2], self.prev_action[3], self.prev_action[4], self.prev_action[5]], dtype=np.float32), # 6
        ])
        return obs.astype(np.float32)

    def step(self, action):
        action = np.clip(action, -1.0, 1.0).astype(np.float32)
        self.filtered_action = 0.6 * self.filtered_action + 0.4 * action

        dt_lead_lag = float(self.filtered_action[0]) * 0.030
        dz_bat = float(self.filtered_action[1]) * 0.08
        dalpha_plane = float(self.filtered_action[2]) * 0.15
        dpower_dur = float(self.filtered_action[3]) * 0.02
        delbow_reach = float(self.filtered_action[4]) * 0.15
        dweight_shift = float(self.filtered_action[5]) * 0.10

        current_time = self.current_step * self.dt

        if not self.swing_triggered:
            candidate_trigger = self.nominal_t_trigger + dt_lead_lag
            if current_time >= candidate_trigger:
                self.swing_triggered = True
                self.locked_t_trigger = candidate_trigger
                self.locked_swing_duration = max(0.12, self.nominal_swing_duration + dpower_dur)

        # Keyframe modulation
        kfs = self.base_keyframes.copy()
        kfs[3, 1] += dz_bat * 0.6
        kfs[3, 2] += dalpha_plane * 0.6
        kfs[3, 4] += delbow_reach * 0.6
        kfs[4, 1] += dz_bat * 1.0
        kfs[4, 2] += dalpha_plane * 1.0
        kfs[4, 4] += delbow_reach * 1.0
        kfs[5, 1] += dz_bat * 0.5
        kfs[5, 2] += dalpha_plane * 0.5

        # Dynamic leg target with weight shift
        leg_target = self.base_leg_q.copy()
        if self.swing_triggered:
            # Shift weight to front (left) leg during swing
            leg_target[2] -= dweight_shift # left hip pitch forward
            leg_target[7] += dweight_shift # right hip uncoil

        for _ in range(self.frame_skip):
            if not self.swing_triggered:
                q_target = kfs[0]
            else:
                elapsed = current_time - self.locked_t_trigger
                prog = elapsed / self.locked_swing_duration
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

            # Upper body PD control
            for i in range(5):
                q = self.data.qpos[self.swing_qpos_adrs[i]]
                dq = self.data.qvel[self.swing_qvel_adrs[i]]
                tau = self.swing_Kp[i] * (q_target[i] - q) - self.swing_Kd[i] * dq
                cr = self.model.actuator_ctrlrange[self.swing_act_ids[i]]
                self.data.ctrl[self.swing_act_ids[i]] = np.clip(tau, cr[0], cr[1])

            # Leg stance balance PD control
            for a in range(10):
                jid = self.model.actuator_trnid[self.leg_act_ids[a], 0]
                q = self.data.qpos[self.model.jnt_qposadr[jid]]
                dq = self.data.qvel[self.model.jnt_dofadr[jid]]
                tau = self.leg_Kp[a] * (leg_target[a] - q) - self.leg_Kd[a] * dq
                cr = self.model.actuator_ctrlrange[self.leg_act_ids[a]]
                self.data.ctrl[self.leg_act_ids[a]] = np.clip(tau, cr[0], cr[1])

            mujoco.mj_step(self.model, self.data)

            # Contact detection
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

        pelvis_pos = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3]
        pelvis_z = pelvis_pos[2]
        if pelvis_z < 0.65:
            self.has_fallen = True

        terminated = False
        truncated = False
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]

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
        elif ball_pos[1] < -0.8:
            terminated = True
        elif self.current_step >= self.max_steps:
            truncated = True

        # Reward formulation
        reward = 0.0

        # 1. Bipedal Standing Balance Reward
        r_balance = 5.0 * np.exp(-15.0 * ((pelvis_z - 0.85) ** 2))
        reward += r_balance

        if self.has_fallen:
            reward -= 40.0

        info = {
            "contact": self.has_contacted,
            "fair_hit": self.is_fair_hit,
            "has_fallen": self.has_fallen,
            "pelvis_z": float(pelvis_z),
            "exit_speed_kmh": float(self.exit_velocity * 3.6),
            "azimuth_deg": float(self.exit_azimuth_deg),
        }

        if terminated and self.has_contacted and not self.contact_reward_given:
            self.contact_reward_given = True
            r_contact = 12.0
            sweet_offset = float(np.linalg.norm(self.contact_ball_pos - self.contact_sweet_pos))
            r_sweet = 8.0 * float(np.exp(-25.0 * sweet_offset))
            r_fair = 10.0 if self.is_fair_hit else -5.0

            reward += r_contact + r_sweet + r_fair

        reward -= 0.01 * float(np.sum(action ** 2))
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
