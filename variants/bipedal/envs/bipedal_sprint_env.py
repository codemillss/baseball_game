"""
BipedalSprintEnv: Phase 6 Continuous Multi-Step Bipedal Base Running to 1st Base.
Integrates:
- 19-DoF Unitree H1 Humanoid with full 6-DoF Free-Floating Base Pelvis.
- Stage 1: Whole-body bipedal athletic swing and contact (0.0s to 0.52s).
- Stage 2: Dynamic prop handover of dropped_bat to field turf at release (t = 0.52s).
- Stage 3: Continuous multi-step bipedal sprint locomotion toward 1st Base (6.5m, 6.5m) (0.52s to 2.50s).
- Full 50 Hz control loop (frame_skip=10 @ 0.002s timestep).
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


class BipedalSprintEnv(gym.Env):
    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 50}

    def __init__(
        self,
        xml_path=None,
        render_mode=None,
        frame_skip=10,
        pitch_speed_range=(16.0, 20.0),
        pitch_dist=7.5,
    ):
        super().__init__()

        if xml_path is None:
            xml_path = os.path.join(parent_dir, "models", "h1_bipedal_sprint.xml")

        self.xml_path = xml_path
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)

        self.render_mode = render_mode
        self.frame_skip = frame_skip
        self.dt = self.model.opt.timestep * self.frame_skip  # 0.02s per step
        self.pitch_speed_range = pitch_speed_range
        self.pitch_dist = pitch_dist

        # 1st Base location and unit vector from home plate (-0.75, 0.0)
        self.target_1b = np.array([6.5, 6.5], dtype=np.float32)
        self.start_p0 = np.array([-0.75, 0.0], dtype=np.float32)
        vec_1b = self.target_1b - self.start_p0
        self.nominal_dist_1b = float(np.linalg.norm(vec_1b))
        self.u_1b = (vec_1b / self.nominal_dist_1b).astype(np.float32)
        self.yaw_1b = float(np.arctan2(self.u_1b[1], self.u_1b[0]))  # ~0.731 rad (41.9 deg)

        # Body and site IDs
        self.pelvis_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.held_bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "held_bat")
        self.dropped_bat_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "dropped_bat")

        self.held_bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "held_bat_barrel")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")

        # Freejoints
        ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
        self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]

        pelvis_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "pelvis_joint")
        self.pelvis_qpos_adr = self.model.jnt_qposadr[pelvis_jnt_id]
        self.pelvis_qvel_adr = self.model.jnt_dofadr[pelvis_jnt_id]

        drop_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "dropped_bat_joint")
        self.drop_qpos_adr = self.model.jnt_qposadr[drop_jnt_id]
        self.drop_qvel_adr = self.model.jnt_dofadr[drop_jnt_id]

        # Actuators
        self.swing_act_names = ["torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"]
        self.swing_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.swing_act_names]
        self.swing_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.swing_act_ids]
        self.swing_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.swing_act_ids]

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

        self.leg_Kp = np.array([450.0, 450.0, 650.0, 750.0, 350.0, 450.0, 450.0, 650.0, 750.0, 350.0], dtype=np.float32)
        self.leg_Kd = np.array([35.0,  40.0,  55.0,  65.0,  28.0,  35.0,  40.0,  55.0,  65.0,  28.0], dtype=np.float32)

        # Athletic batting keyframes
        self.base_keyframes = np.array([
            [-0.40, -1.00,  0.00,  0.40,  1.50],
            [-0.60, -1.15,  0.00,  0.60,  1.70],
            [-0.10, -0.70, -0.05,  0.20,  1.20],
            [ 0.50, -0.30, -0.10, -0.10,  0.70],
            [ 1.15,  0.20, -0.08, -0.40,  0.35],
            [ 1.70,  0.80,  0.00, -0.70,  1.20]
        ], dtype=np.float32)

        # Nominal athletic leg stance (Natural static equilibrium)
        self.base_leg_q = np.array([
            0.0,  0.10, -0.18, 0.48, -0.32,  # Left leg
            0.0, -0.10, -0.18, 0.48, -0.32   # Right leg
        ], dtype=np.float32)

        # Action Space (6 dims):
        # a[0]: dt_trigger timing lead/lag (-0.03 to +0.03s)
        # a[1]: dz_bat plane height (-0.20 to +0.20rad)
        # a[2]: dalpha_plane attack tilt (-0.20 to +0.20rad)
        # a[3]: stride_freq modulation (1.4 to 2.2 Hz)
        # a[4]: sprint_push_gain (0.8 to 1.4)
        # a[5]: sprint_steer_yaw (-0.25 to +0.25rad)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)

        # Observation Space (44 dims):
        # ball_pos (3), ball_vel (3), t_remain (1), pelvis_pos (3), pelvis_vel (3),
        # pelvis_quat (4), pelvis_angvel (3), rel_1b (2), dist_1b (1), heading_err (1),
        # leg_qpos (10), leg_qvel (10)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(44,), dtype=np.float32)

        self.current_step = 0
        self.max_steps = 85  # 85 * 0.02s = 1.70s (batting 0.52s + sprint 1.18s)
        self.filtered_action = np.zeros(6, dtype=np.float32)

        self.swing_triggered = False
        self.locked_t_trigger = 0.0
        self.locked_swing_duration = 0.17
        self.has_contacted = False
        self.bat_released = False
        self.contact_step = -1
        self.release_step = -1
        self.exit_velocity = 0.0
        self.exit_azimuth_deg = 0.0
        self.is_fair_hit = False
        self.has_fallen = False
        self.sweet_spot_offset = 0.0
        self.prev_dist_1b = self.nominal_dist_1b
        self.max_sprint_dist = 0.0

        self.renderer = None
        if self.render_mode in ["rgb_array", "human"]:
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        self.current_step = 0
        self.filtered_action = np.zeros(6, dtype=np.float32)
        self.swing_triggered = False
        self.locked_t_trigger = 0.0
        self.locked_swing_duration = 0.17
        self.has_contacted = False
        self.bat_released = False
        self.contact_step = -1
        self.release_step = -1
        self.exit_velocity = 0.0
        self.exit_azimuth_deg = 0.0
        self.is_fair_hit = False
        self.has_fallen = False
        self.sweet_spot_offset = 0.0

        # Restore held bat visibility
        self.model.geom_size[self.held_bat_geom_id] = [0.032, 0.45, 0.0]
        self.model.geom_rgba[self.held_bat_geom_id, 3] = 1.0

        # Reset dropped bat in sky before release
        self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = [0.0, 0.0, 50.0]
        self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+6] = 0.0

        # Set 6-DoF Pelvis in batter box at natural equilibrium
        self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3] = [-0.75, 0.00, 0.92]
        self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+6] = 0.0

        # Set nominal leg stance
        for i, adr in enumerate(self.leg_qpos_adrs):
            self.data.qpos[adr] = self.base_leg_q[i]

        # Set upper body initial keyframe
        for i, adr in enumerate(self.swing_qpos_adrs):
            self.data.qpos[adr] = self.base_keyframes[0, i]

        # Pitch generation
        pitch_speed = float(self.np_random.uniform(*self.pitch_speed_range))
        vy = -pitch_speed
        contact_y = 0.22
        t_flight = (self.pitch_dist - contact_y) / abs(vy)
        self.nominal_t_flight = t_flight

        target_x = float(self.np_random.uniform(0.12, 0.18))
        target_z = float(self.np_random.uniform(0.54, 0.60))

        z0 = 0.85
        drop = 0.5 * 9.81 * (t_flight ** 2)
        vz = (target_z + drop - z0) / t_flight

        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [target_x, self.pitch_dist, z0]
        self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, vy, vz]
        self.data.qvel[self.ball_qvel_adr+3:self.ball_qvel_adr+6] = 0.0

        mujoco.mj_forward(self.model, self.data)

        self.nominal_t_trigger = t_flight - 0.145
        self.nominal_swing_duration = 0.17

        pelvis_xy = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+2]
        self.prev_dist_1b = float(np.linalg.norm(self.target_1b - pelvis_xy))
        self.max_sprint_dist = 0.0

        return self._get_obs(), {}

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        t_remain = max(0.0, (ball_pos[1] - 0.22) / abs(ball_vel[1])) if abs(ball_vel[1]) > 1.0 else 0.0

        pelvis_pos = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3]
        pelvis_vel = self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+3]
        pelvis_quat = self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7]
        pelvis_angvel = self.data.qvel[self.pelvis_qvel_adr+3:self.pelvis_qvel_adr+6]

        rel_1b = self.target_1b - pelvis_pos[:2]
        dist_1b = float(np.linalg.norm(rel_1b))
        desired_yaw = np.arctan2(rel_1b[1], rel_1b[0])

        qw, qx, qy, qz = pelvis_quat
        current_yaw = np.arctan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy*qy + qz*qz))
        heading_err = float(desired_yaw - current_yaw)

        leg_qpos = np.array([self.data.qpos[adr] for adr in self.leg_qpos_adrs], dtype=np.float32)
        leg_qvel = np.array([self.data.qvel[adr] for adr in self.leg_qvel_adrs], dtype=np.float32)

        obs = np.concatenate([
            ball_pos,                                           # 3
            ball_vel,                                           # 3
            np.array([t_remain], dtype=np.float32),             # 1
            pelvis_pos,                                         # 3
            pelvis_vel,                                         # 3
            pelvis_quat,                                        # 4
            pelvis_angvel,                                      # 3
            rel_1b,                                             # 2
            np.array([dist_1b, heading_err], dtype=np.float32), # 2
            leg_qpos,                                           # 10
            leg_qvel                                            # 10
        ]).astype(np.float32)
        return obs

    def step(self, action):
        self.current_step += 1
        current_time = self.current_step * self.dt

        action = np.clip(action, self.action_space.low, self.action_space.high)
        self.filtered_action = 0.6 * self.filtered_action + 0.4 * action

        dt_trigger = 0.030 * float(self.filtered_action[0])
        dz_bat = 0.20 * float(self.filtered_action[1])
        dalpha_plane = 0.20 * float(self.filtered_action[2])
        freq_sprint = 1.8 + 0.3 * float(self.filtered_action[3]) # 1.5 to 2.1 Hz
        push_gain = 1.0 + 0.3 * float(self.filtered_action[4])   # 0.7 to 1.3
        steer_yaw = 0.20 * float(self.filtered_action[5])

        # Stage 1: Dynamic Swing Trigger (around t = 0.30s to 0.45s)
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]

        if not self.swing_triggered and abs(ball_vel[1]) > 2.0 and ball_pos[1] > 0.22:
            t_rem = (ball_pos[1] - 0.22) / abs(ball_vel[1])
            lead_needed = 0.145 + dt_trigger
            if t_rem <= lead_needed:
                self.swing_triggered = True
                self.locked_t_trigger = current_time

        # Stage 2: Post-impact Bat Release at t = 0.52s
        if not self.bat_released and current_time >= 0.52:
            self.bat_released = True
            self.release_step = self.current_step

            # Transfer 6D pose and velocity to dropped_bat freejoint
            bat_xpos = self.data.xpos[self.held_bat_body_id].copy()
            bat_xmat = self.data.xmat[self.held_bat_body_id].copy()
            bat_quat = np.zeros(4)
            mujoco.mju_mat2Quat(bat_quat, bat_xmat)

            self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = bat_xpos
            self.data.qpos[self.drop_qpos_adr+3:self.drop_qpos_adr+7] = bat_quat

            v6 = np.zeros(6)
            mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_BODY, self.held_bat_body_id, v6, 0)
            self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+3] = v6[3:6]
            self.data.qvel[self.drop_qvel_adr+3:self.drop_qvel_adr+6] = v6[0:3]

            # Hide held bat geom
            self.model.geom_size[self.held_bat_geom_id] = [0.0001, 0.0001, 0.0]
            self.model.geom_rgba[self.held_bat_geom_id, 3] = 0.0

        # Upper body swing keyframe setup
        kfs = self.base_keyframes.copy()
        kfs[3, 1] += dz_bat * 0.6
        kfs[3, 2] += dalpha_plane * 0.6
        kfs[4, 1] += dz_bat * 1.0
        kfs[4, 2] += dalpha_plane * 1.0
        kfs[5, 1] += dz_bat * 0.5

        # Substep Physics Loop (10 substeps of 0.002s = 0.02s per env step)
        for s_idx in range(self.frame_skip):
            sim_time = current_time + s_idx * self.model.opt.timestep

            # 1. Upper Body PD
            if not self.bat_released:
                if not self.swing_triggered:
                    q_arm = kfs[0]
                else:
                    elapsed = sim_time - self.locked_t_trigger
                    prog = elapsed / self.locked_swing_duration
                    if prog < 0.20:
                        w = prog / 0.20
                        q_arm = (1.0 - w) * kfs[0] + w * kfs[1]
                    elif prog < 0.45:
                        w = (prog - 0.20) / 0.25
                        q_arm = (1.0 - w) * kfs[1] + w * kfs[2]
                    elif prog < 0.70:
                        w = (prog - 0.45) / 0.25
                        q_arm = (1.0 - w) * kfs[2] + w * kfs[3]
                    elif prog < 0.90:
                        w = (prog - 0.70) / 0.20
                        q_arm = (1.0 - w) * kfs[3] + w * kfs[4]
                    else:
                        w = min(1.0, (prog - 0.90) / 0.30)
                        q_arm = (1.0 - w) * kfs[4] + w * kfs[5]
            else:
                # Running posture: Torso aligns towards 1st base, arms in running pump
                t_run = sim_time - 0.52
                turn_p = min(1.0, t_run / 0.4)
                target_yaw = (self.yaw_1b + steer_yaw) * turn_p
                arm_phi = 2.0 * np.pi * freq_sprint * t_run
                q_arm = np.array([
                    target_yaw,                  # Torso yaw
                    0.20 + 0.35 * np.sin(arm_phi),# Right shoulder pitch (running swing)
                    -0.10,
                    0.00,
                    1.20                         # Right elbow bent
                ], dtype=np.float32)

            for i in range(5):
                q = self.data.qpos[self.swing_qpos_adrs[i]]
                dq = self.data.qvel[self.swing_qvel_adrs[i]]
                tau_a = self.swing_Kp[i] * (q_arm[i] - q) - self.swing_Kd[i] * dq
                cr = self.model.actuator_ctrlrange[self.swing_act_ids[i]]
                self.data.ctrl[self.swing_act_ids[i]] = np.clip(tau_a, cr[0], cr[1])

            # 2. Leg PD & Ground Reaction Propulsion
            p_x = self.data.qpos[self.pelvis_qpos_adr]
            v_x = self.data.qvel[self.pelvis_qvel_adr]
            w_z = self.data.qvel[self.pelvis_qvel_adr + 5]

            if not self.bat_released:
                # Stage 1: Batting Stance Ground Shear Balance (rock-solid hold at x = -0.75m)
                tau_x_ank = np.clip(500.0 * (p_x - (-0.75)) + 50.0 * v_x, -35.0, 35.0)
                tau_x_hip = np.clip(400.0 * (p_x - (-0.75)) + 40.0 * v_x, -50.0, 50.0)
                tau_yaw = np.clip(80.0 * w_z, -50.0, 50.0)

                leg_tgt = self.base_leg_q.copy()
                for a in range(10):
                    jid = self.model.actuator_trnid[self.leg_act_ids[a], 0]
                    ql = self.data.qpos[self.model.jnt_qposadr[jid]]
                    dql = self.data.qvel[self.model.jnt_dofadr[jid]]
                    tau_l = self.leg_Kp[a] * (leg_tgt[a] - ql) - self.leg_Kd[a] * dql
                    if a in [4, 9]: tau_l += tau_x_ank
                    elif a in [2, 7]: tau_l += tau_x_hip
                    elif a in [0, 5]: tau_l += tau_yaw
                    cr_l = self.model.actuator_ctrlrange[self.leg_act_ids[a]]
                    self.data.ctrl[self.leg_act_ids[a]] = np.clip(tau_l, cr_l[0], cr_l[1])
            else:
                # Stage 3: Continuous Multi-Step Sprint Locomotion
                t_run = sim_time - 0.52
                turn_p = min(1.0, t_run / 0.35)
                target_yaw = (self.yaw_1b + steer_yaw) * turn_p

                # Advance forward smoothly along baseline
                v_fwd = min(0.85 * push_gain, 0.60 * t_run)
                s_dist = 0.5 * v_fwd * t_run
                x_ref = self.start_p0[0] + self.u_1b[0] * s_dist
                vx_ref = v_fwd * self.u_1b[0]

                # Ground shear drive
                tau_x_ank = np.clip(450.0 * (x_ref - p_x) + 45.0 * (vx_ref - v_x), -30.0, 30.0)
                tau_x_hip = np.clip(380.0 * (x_ref - p_x) + 38.0 * (vx_ref - v_x), -45.0, 45.0)

                # Active yaw steering towards 1st base
                qw, qx, qy, qz = self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7]
                pelvis_yaw = np.arctan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy*qy + qz*qz))
                yaw_err = target_yaw - pelvis_yaw
                tau_yaw = np.clip(-120.0 * yaw_err - 20.0 * w_z, -40.0, 40.0)

                # Periodic cyclic stride
                phase = (t_run * freq_sprint) % 1.0
                sw = np.sin(2.0 * np.pi * phase)
                cw = np.cos(2.0 * np.pi * phase)

                # Torso heading to 1B
                leg_tgt = self.base_leg_q.copy()
                leg_tgt[0] = target_yaw
                leg_tgt[5] = target_yaw

                # Lateral roll balance
                leg_tgt[1] += 0.03 * cw
                leg_tgt[6] += 0.03 * cw

                # Hip stride
                amp = 0.15 * min(1.0, t_run / 0.30)
                leg_tgt[2] -= amp * sw
                leg_tgt[7] += amp * sw

                # Knee ground clearance
                k_amp = 0.20 * min(1.0, t_run / 0.30)
                leg_tgt[3] += k_amp * max(0.0, sw)
                leg_tgt[8] += k_amp * max(0.0, -sw)

                # Height & attitude stabilization
                p_z = self.data.qpos[self.pelvis_qpos_adr + 2]
                v_z = self.data.qvel[self.pelvis_qvel_adr + 2]
                tau_z = np.clip(600.0 * (0.92 - p_z) - 50.0 * v_z, -30.0, 90.0)

                pitch_tilt = 2.0 * (qx * qz + qw * qy)
                wy = self.data.qvel[self.pelvis_qvel_adr + 4]
                tau_pitch = np.clip(-200.0 * pitch_tilt - 20.0 * wy, -30.0, 30.0)

                for a in range(10):
                    jid = self.model.actuator_trnid[self.leg_act_ids[a], 0]
                    ql = self.data.qpos[self.model.jnt_qposadr[jid]]
                    dql = self.data.qvel[self.model.jnt_dofadr[jid]]
                    tau_l = self.leg_Kp[a] * (leg_tgt[a] - ql) - self.leg_Kd[a] * dql
                    if a in [4, 9]: tau_l += tau_x_ank + 0.5 * tau_pitch
                    elif a in [2, 7]: tau_l += tau_x_hip + 0.5 * tau_pitch
                    elif a in [0, 5]: tau_l += tau_yaw
                    elif a in [3, 8]: tau_l += 0.5 * tau_z
                    cr_l = self.model.actuator_ctrlrange[self.leg_act_ids[a]]
                    self.data.ctrl[self.leg_act_ids[a]] = np.clip(tau_l, cr_l[0], cr_l[1])

            mujoco.mj_step(self.model, self.data)

            # Contact detection between held bat and ball
            if not self.has_contacted and not self.bat_released:
                for c_idx in range(self.data.ncon):
                    con = self.data.contact[c_idx]
                    g1, g2 = con.geom1, con.geom2
                    if (g1 == self.held_bat_geom_id and g2 == self.ball_geom_id) or (g2 == self.held_bat_geom_id and g1 == self.ball_geom_id):
                        self.has_contacted = True
                        self.contact_step = self.current_step
                        ball_p = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
                        sweet_p = self.data.site_xpos[self.sweet_spot_id]
                        self.sweet_spot_offset = float(np.linalg.norm(ball_p - sweet_p))

                        ball_v = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                        self.exit_velocity = float(np.linalg.norm(ball_v))
                        self.exit_azimuth_deg = float(np.degrees(np.arctan2(ball_v[0], -ball_v[1])))
                        if ball_v[1] < 0.0 and abs(self.exit_azimuth_deg) <= 45.0:
                            self.is_fair_hit = True

        # State assessment
        pelvis_pos = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3]
        pelvis_quat = self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7]
        pelvis_vel = self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+3]

        qw, qx, qy, qz = pelvis_quat
        upright_z = 1.0 - 2.0 * (qx*qx + qy*qy)

        dist_1b = float(np.linalg.norm(self.target_1b - pelvis_pos[:2]))
        dist_traveled = float(np.linalg.norm(pelvis_pos[:2] - self.start_p0))
        self.max_sprint_dist = max(self.max_sprint_dist, dist_traveled)

        # Fall detection: threshold 0.55m
        if pelvis_pos[2] < 0.55 or upright_z < 0.55:
            self.has_fallen = True

        # Reward formulation
        reward = 0.0

        # 1. Contact & Fair Hit Rewards
        if self.has_contacted and self.current_step == self.contact_step:
            reward += 10.0
            sweet_rew = 5.0 * np.exp(-max(0.0, self.sweet_spot_offset - 0.06) / 0.04)
            reward += sweet_rew
            if self.is_fair_hit:
                reward += 15.0 + 0.5 * (self.exit_velocity * 3.6)

        # 2. Bat Release Bonus
        if self.bat_released and self.current_step == self.release_step:
            reward += 8.0

        # 3. Sprint Progression Reward
        if self.bat_released:
            progress_1b = self.prev_dist_1b - dist_1b
            reward += 20.0 * max(0.0, progress_1b)

            # Velocity along 1B baseline
            v_along_1b = float(np.dot(pelvis_vel[:2], self.u_1b))
            reward += 2.0 * max(0.0, v_along_1b)

        # 4. Upright Balance Reward
        balance_rew = 2.0 * np.exp(-((pelvis_pos[2] - 0.95)**2) / 0.04) * max(0.0, upright_z)
        reward += balance_rew

        # Termination
        terminated = False
        if self.has_fallen:
            terminated = True
            reward -= 50.0
        elif dist_1b < 0.50:  # Reached 1st base!
            terminated = True
            reward += 100.0

        truncated = self.current_step >= self.max_steps
        self.prev_dist_1b = dist_1b

        info = {
            "contact": self.has_contacted,
            "fair_hit": self.is_fair_hit,
            "bat_released": self.bat_released,
            "has_fallen": self.has_fallen,
            "pelvis_z": float(pelvis_pos[2]),
            "dist_to_1b": dist_1b,
            "dist_traveled": dist_traveled,
            "exit_speed_kmh": self.exit_velocity * 3.6,
            "sweet_spot_offset": self.sweet_spot_offset,
        }

        return self._get_obs(), float(reward), terminated, truncated, info

    def render(self, camera_name="run_tracking_cam"):
        if self.render_mode not in ["rgb_array", "human"]:
            return None
        self.renderer.update_scene(self.data, camera=camera_name)
        return self.renderer.render()

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
