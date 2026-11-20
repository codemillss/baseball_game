"""
HitAndRunEnv: Phase 4 Hit-and-Run Locomotion Transition for H1 Humanoid.
Features:
- Full 6-DoF Free-Floating Pelvis (pelvis_joint).
- 19-DoF Unitree H1 humanoid model with real motor torque limits.
- Stage 1: Goal-conditioned athletic bipedal swing and precision contact (100% Phase 3 kinematics).
- Stage 2: Post-impact bat release via dynamic handover to freejoint dropped_bat (bat drops and tumbles on turf).
- Stage 3: Dynamic bipedal sprint locomotion toward 1st Base (x=6.5m, y=6.5m).
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


class HitAndRunEnv(gym.Env):
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
            xml_path = os.path.join(parent_dir, "models", "h1_hit_and_run.xml")

        self.xml_path = xml_path
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)

        self.render_mode = render_mode
        self.frame_skip = frame_skip
        self.dt = self.model.opt.timestep * self.frame_skip  # 0.02s
        self.pitch_speed_range = pitch_speed_range
        self.pitch_dist = pitch_dist

        # 1st Base target
        self.target_1b = np.array([6.5, 6.5], dtype=np.float32)

        # Bodies, Geoms, Sites
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

        self.leg_Kp = np.array([350.0, 400.0, 500.0, 550.0, 250.0, 350.0, 400.0, 500.0, 550.0, 250.0], dtype=np.float32)
        self.leg_Kd = np.array([30.0,  35.0,  45.0,  50.0,  20.0,  30.0,  35.0,  45.0,  50.0,  20.0], dtype=np.float32)

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
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(41,), dtype=np.float32)

        self.current_step = 0
        self.max_steps = 35  # 35 * 0.02s = 0.70s (pitch + swing + contact + bat drop + sprint launch)
        self.prev_action = np.zeros(6, dtype=np.float32)
        self.filtered_action = np.zeros(6, dtype=np.float32)

        self.swing_triggered = False
        self.locked_t_trigger = 0.0
        self.locked_swing_duration = 0.17
        self.has_contacted = False
        self.bat_released = False
        self.contact_step = -1
        self.release_step = -1
        self.contact_ball_pos = None
        self.contact_sweet_pos = None
        self.exit_velocity = 0.0
        self.exit_azimuth_deg = 0.0
        self.is_fair_hit = False
        self.has_fallen = False
        self.start_dist_1b = 9.81
        self.prev_dist_1b = 9.81

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
        self.bat_released = False
        self.contact_step = -1
        self.release_step = -1
        self.contact_ball_pos = None
        self.contact_sweet_pos = None
        self.exit_velocity = 0.0
        self.exit_azimuth_deg = 0.0
        self.is_fair_hit = False
        self.has_fallen = False

        # Restore held bat visibility
        self.model.geom_size[self.held_bat_geom_id] = [0.032, 0.45, 0.0]
        self.model.geom_rgba[self.held_bat_geom_id, 3] = 1.0

        # Reset dropped bat underground
        self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = [0.0, 0.0, -10.0]
        self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+6] = 0.0

        # Set 6-DoF Pelvis in batter box
        self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3] = [-0.85, 0.00, 0.88]
        self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+6] = 0.0

        # Set nominal leg stance
        for i, adr in enumerate(self.leg_qpos_adrs):
            self.data.qpos[adr] = self.base_leg_q[i]

        # Set upper body initial keyframe
        for i, adr in enumerate(self.swing_qpos_adrs):
            self.data.qpos[adr] = self.base_keyframes[0, i]

        # Draw Goal Condition
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

        pelvis_xy = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+2]
        self.start_dist_1b = float(np.linalg.norm(self.target_1b - pelvis_xy))
        self.prev_dist_1b = self.start_dist_1b

        return self._get_obs(), {}

    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        t_remain = max(0.0, (ball_pos[1] - 0.20) / abs(ball_vel[1])) if abs(ball_vel[1]) > 1.0 else 0.0

        pelvis_pos = self.data.qpos[self.pelvis_qpos_adr:self.pelvis_qpos_adr+3]
        pelvis_vel = self.data.qvel[self.pelvis_qvel_adr:self.pelvis_qvel_adr+3]
        pelvis_quat = self.data.qpos[self.pelvis_qpos_adr+3:self.pelvis_qpos_adr+7]

        rel_1b = self.target_1b - pelvis_pos[:2]
        dist_1b = float(np.linalg.norm(rel_1b))
        desired_yaw = np.arctan2(rel_1b[1], rel_1b[0])

        qw, qx, qy, qz = pelvis_quat
        current_yaw = np.arctan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy*qy + qz*qz))
        heading_err = float(desired_yaw - current_yaw)

        leg_qpos = np.array([self.data.qpos[adr] for adr in self.leg_qpos_adrs], dtype=np.float32)
        stage_idx = 0.0 if not self.swing_triggered else (1.0 if not self.bat_released else 2.0)

        obs = np.concatenate([
            ball_pos,                                    # 3
            ball_vel,                                    # 3
            np.array([t_remain], dtype=np.float32),      # 1
            pelvis_pos,                                  # 3
            pelvis_vel,                                  # 3
            pelvis_quat,                                 # 4
            rel_1b,                                      # 2
            np.array([dist_1b, heading_err], dtype=np.float32), # 2
            np.array([stage_idx, 1.0 if self.bat_released else 0.0, 1.0 if self.has_contacted else 0.0], dtype=np.float32), # 3
            leg_qpos,                                    # 10
            self.prev_action,                            # 6
            np.array([float(self.exit_velocity)], dtype=np.float32), # 1
        ])
        return obs.astype(np.float32)

    def step(self, action):
        action = np.clip(action, -1.0, 1.0).astype(np.float32)
        self.filtered_action = 0.6 * self.filtered_action + 0.4 * action

        current_time = self.current_step * self.dt

        dt_lead_lag = float(self.filtered_action[0]) * 0.030
        dz_bat = float(self.filtered_action[1]) * 0.08
        dalpha_plane = float(self.filtered_action[2]) * 0.15
        dpower_dur = float(self.filtered_action[3]) * 0.02
        delbow_reach = float(self.filtered_action[4]) * 0.15
        dweight_shift = float(self.filtered_action[5]) * 0.10

        if not self.swing_triggered:
            candidate_trigger = self.nominal_t_trigger + dt_lead_lag
            if current_time >= candidate_trigger:
                self.swing_triggered = True
                self.locked_t_trigger = candidate_trigger
                self.locked_swing_duration = max(0.12, self.nominal_swing_duration + dpower_dur)

        # Post-contact bat release handover
        if self.swing_triggered and not self.bat_released:
            if (self.has_contacted and self.current_step >= self.contact_step + 4) or (current_time >= self.locked_t_trigger + 0.22):
                self.bat_released = True
                self.release_step = self.current_step

                # Seamless handover to dropped_bat freejoint
                self.data.qpos[self.drop_qpos_adr:self.drop_qpos_adr+3] = self.data.xpos[self.held_bat_body_id]
                self.data.qpos[self.drop_qpos_adr+3:self.drop_qpos_adr+7] = self.data.xquat[self.held_bat_body_id]
                v6 = np.zeros(6, dtype=np.float64)
                mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_BODY, self.held_bat_body_id, v6, 0)
                self.data.qvel[self.drop_qvel_adr:self.drop_qvel_adr+3] = v6[3:6]
                self.data.qvel[self.drop_qvel_adr+3:self.drop_qvel_adr+6] = v6[0:3]

                # Hide held bat
                self.model.geom_size[self.held_bat_geom_id] = [0.0001, 0.0001, 0.0]
                self.model.geom_rgba[self.held_bat_geom_id, 3] = 0.0

        # Trajectory computation
        kfs = self.base_keyframes.copy()
        kfs[3, 1] += dz_bat * 0.6
        kfs[3, 2] += dalpha_plane * 0.6
        kfs[3, 4] += delbow_reach * 0.6
        kfs[4, 1] += dz_bat * 1.0
        kfs[4, 2] += dalpha_plane * 1.0
        kfs[4, 4] += delbow_reach * 1.0
        kfs[5, 1] += dz_bat * 0.5
        kfs[5, 2] += dalpha_plane * 0.5

        leg_target = self.base_leg_q.copy()
        if self.swing_triggered and not self.bat_released:
            leg_target[2] -= dweight_shift
            leg_target[7] += dweight_shift
        elif self.bat_released:
            # Sprint transition modulation: step towards 1st base
            prog_sprint = min(1.0, (self.current_step - self.release_step) / 10.0)
            steer = 0.25 * float(self.filtered_action[4])
            leg_target[0] += (0.20 + steer) * prog_sprint  # Hip yaw towards 1st base
            leg_target[5] += (0.20 + steer) * prog_sprint
            leg_target[2] -= 0.15 * prog_sprint # forward stride
            leg_target[7] += 0.10 * prog_sprint # back leg push-off

        for _ in range(self.frame_skip):
            if not self.bat_released:
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
            else:
                # Running posture: Torso aligns towards 1st base, right arm tucks
                prog_sprint = min(1.0, (self.current_step - self.release_step) / 10.0)
                q_target = np.array([
                    0.40 * prog_sprint, # Torso towards 1st base
                    0.20 * prog_sprint,
                    -0.10,
                    0.00,
                    1.20 # Elbow bent for sprint
                ], dtype=np.float32)

            # Apply Upper body PD
            for i in range(5):
                q = self.data.qpos[self.swing_qpos_adrs[i]]
                dq = self.data.qvel[self.swing_qvel_adrs[i]]
                tau = self.swing_Kp[i] * (q_target[i] - q) - self.swing_Kd[i] * dq
                cr = self.model.actuator_ctrlrange[self.swing_act_ids[i]]
                self.data.ctrl[self.swing_act_ids[i]] = np.clip(tau, cr[0], cr[1])

            # Apply Leg PD
            for a in range(10):
                jid = self.model.actuator_trnid[self.leg_act_ids[a], 0]
                q = self.data.qpos[self.model.jnt_qposadr[jid]]
                dq = self.data.qvel[self.model.jnt_dofadr[jid]]
                tau = self.leg_Kp[a] * (leg_target[a] - q) - self.leg_Kd[a] * dq
                cr = self.model.actuator_ctrlrange[self.leg_act_ids[a]]
                self.data.ctrl[self.leg_act_ids[a]] = np.clip(tau, cr[0], cr[1])

            mujoco.mj_step(self.model, self.data)

            # Contact detection between held bat and ball
            if not self.has_contacted and not self.bat_released:
                for c_idx in range(self.data.ncon):
                    con = self.data.contact[c_idx]
                    g1, g2 = con.geom1, con.geom2
                    if (g1 == self.held_bat_geom_id and g2 == self.ball_geom_id) or (g2 == self.held_bat_geom_id and g1 == self.ball_geom_id):
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

        if self.has_contacted:
            ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
            self.exit_velocity = float(np.linalg.norm(ball_vel))
            if ball_vel[1] > 0.10:
                self.is_fair_hit = True
                self.exit_azimuth_deg = float(np.degrees(np.arctan2(ball_vel[0], ball_vel[1])))

        curr_dist_1b = float(np.linalg.norm(self.target_1b - pelvis_pos[:2]))
        dist_traveled = float(self.start_dist_1b - curr_dist_1b)
        progress_1b = self.prev_dist_1b - curr_dist_1b
        self.prev_dist_1b = curr_dist_1b

        terminated = False
        truncated = False

        if self.has_fallen:
            terminated = True
        elif self.current_step >= self.max_steps:
            truncated = True

        # Rewards
        reward = 0.0
        # Dynamic balance reward
        reward += 5.0 * float(np.exp(-15.0 * ((pelvis_z - 0.88) ** 2)))

        if self.has_fallen:
            reward -= 40.0

        if self.has_contacted and self.current_step == self.contact_step + 1:
            reward += 15.0
            if self.is_fair_hit:
                reward += 12.0

        if self.bat_released:
            reward += 25.0 * max(0.0, progress_1b)
            # Yaw alignment towards 1st base
            reward += 3.0 * float(np.exp(-5.0 * (obs[18] ** 2)))

        reward -= 0.005 * float(np.sum(action ** 2))
        self.prev_action = action.copy()

        info = {
            "contact": self.has_contacted,
            "fair_hit": self.is_fair_hit,
            "bat_released": self.bat_released,
            "has_fallen": self.has_fallen,
            "dist_to_1b": curr_dist_1b,
            "dist_traveled": dist_traveled,
            "pelvis_z": float(pelvis_z),
            "exit_speed_kmh": float(self.exit_velocity * 3.6),
            "azimuth_deg": float(self.exit_azimuth_deg),
        }

        return obs, reward, terminated, truncated, info

    def render(self, camera_name="run_tracking_cam"):
        if self.render_mode == "rgb_array" and self.renderer is not None:
            self.renderer.update_scene(self.data, camera=camera_name)
            return self.renderer.render()
        return None

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
