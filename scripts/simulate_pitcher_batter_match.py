"""
Closed-Loop Pitcher vs Batter Duel Simulation.
Combines both trained H1 policies in the unified arena (models/h1_duel_match.xml):
- Pitcher AI: pitches Fastballs, Sliders, and Curveballs into the 9-grid strike zone.
- Batter AI: reads the incoming flight trajectory and executes goal-conditioned directional hits.
Renders full-game broadcast video and extracts visual inspection frames.
"""

import os
import sys
import numpy as np
import cv2
import mujoco

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from stable_baselines3 import PPO


class DuelMatchSimulator:
    def __init__(
        self,
        xml_path="models/h1_duel_match.xml",
        pitcher_model_path="checkpoints/best_pitcher_model.zip",
        batter_model_path="checkpoints/best_phase2_hardened_model.zip",
    ):
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)

        self.pitcher_policy = PPO.load(pitcher_model_path)
        self.batter_policy = PPO.load(batter_model_path)

        # Actuator IDs
        self.p_act_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
        self.b_act_names = ["b_torso", "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"]

        self.p_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.p_act_names]
        self.b_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_act_names]

        self.p_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
        self.p_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]

        self.b_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_act_ids]
        self.b_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_act_ids]

        # Ball
        ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
        self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")
        self.p_hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")
        self.weld_eq_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_EQUALITY, "p_ball_weld")

        # Stances and Gains
        self.p_Kp = np.array([450.0, 350.0, 250.0, 150.0, 150.0], dtype=np.float32)
        self.p_Kd = np.array([35.0,  25.0,  20.0,  12.0,  12.0], dtype=np.float32)

        self.b_Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
        self.b_Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)

        self.p_keyframes = np.array([
            [ 0.00,  0.00, -0.40,  0.00,  1.50],
            [ 0.80,  1.20, -0.60,  0.80,  1.60],
            [ 0.20, -0.20, -0.40,  0.30,  1.00],
            [-0.50, -1.40, -0.20, -0.20,  0.20],
            [-0.90, -1.80, -0.60, -0.50,  0.70],
        ], dtype=np.float32)

        self.b_keyframes = np.array([
            [-0.40, -1.00,  0.00,  0.40,  1.50],
            [-0.60, -1.15,  0.00,  0.60,  1.70],
            [-0.10, -0.70, -0.05,  0.20,  1.20],
            [ 0.50, -0.30, -0.10, -0.10,  0.70],
            [ 1.15,  0.20, -0.08, -0.40,  0.35],
            [ 1.70,  0.80,  0.00, -0.70,  1.20]
        ], dtype=np.float32)

        # Aerodynamic constants
        self.rho = 1.205
        self.r_ball = 0.037
        self.m_ball = 0.145
        self.A_ball = np.pi * (self.r_ball ** 2)
        self.Cd = 0.32
        self.Cl = 0.24

        self.renderer = mujoco.Renderer(self.model, height=480, width=640)

    def run_match_episode(self, episode_idx=0, seed=42):
        np.random.seed(seed)
        mujoco.mj_resetData(self.model, self.data)

        # Pitcher target & pitch type
        target_x = float(np.random.uniform(-0.14, 0.14))
        target_z = float(np.random.uniform(0.70, 0.90))
        pitch_type = int(np.random.choice([0, 1, 2]))
        p_one_hot = np.zeros(3, dtype=np.float32)
        p_one_hot[pitch_type] = 1.0

        if pitch_type == 0:
            speed = float(np.random.uniform(21.5, 23.5))
            spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
            pname = "Fastball"
        elif pitch_type == 1:
            speed = float(np.random.uniform(19.0, 21.0))
            spin = np.array([-30.0, 0.0, 150.0], dtype=np.float32)
            pname = "Slider"
        else:
            speed = float(np.random.uniform(17.0, 19.0))
            spin = np.array([170.0, 0.0, -20.0], dtype=np.float32)
            pname = "Curveball"

        # Batter goal
        target_azimuth_deg = float(np.random.uniform(-30.0, 30.0))
        target_azimuth_rad = float(np.radians(target_azimuth_deg))
        target_launch_deg = float(np.random.uniform(15.0, 28.0))
        target_launch_rad = float(np.radians(target_launch_deg))
        target_exit_vel = 14.0

        b_goal = np.array([target_azimuth_rad, target_launch_rad, target_exit_vel], dtype=np.float32)

        # Set initial poses
        for i, adr in enumerate(self.p_qpos_adrs):
            self.data.qpos[adr] = self.p_keyframes[0, i]
        for i, adr in enumerate(self.b_qpos_adrs):
            self.data.qpos[adr] = self.b_keyframes[0, i]

        if self.weld_eq_id >= 0:
            self.data.eq_active[self.weld_eq_id] = True

        mujoco.mj_forward(self.model, self.data)
        hand_pos = self.data.site_xpos[self.p_hand_site_id]
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
        self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
        mujoco.mj_forward(self.model, self.data)

        # Get Pitcher Action from Policy
        p_obs = np.concatenate([
            np.array([target_x, target_z], dtype=np.float32),
            p_one_hot,
            self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3],
            self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3],
            hand_pos,
            np.zeros(3, dtype=np.float32),
            np.array([self.data.qpos[adr] for adr in self.p_qpos_adrs], dtype=np.float32),
            np.array([0.0], dtype=np.float32),
        ])
        p_act, _ = self.pitcher_policy.predict(p_obs, deterministic=True)

        dt_rel = float(p_act[0]) * 0.030
        dx_aim = float(p_act[1]) * 0.15
        dz_aim = float(p_act[2]) * 0.12
        dv_scale = float(p_act[3]) * 0.15

        nominal_release_step = 22
        actual_release_step = int(np.clip(nominal_release_step + int(dt_rel / 0.01), 18, 26))

        # Modulate pitcher keyframes
        p_kfs = self.p_keyframes.copy()
        p_kfs[2, 0] += dx_aim * 0.5
        p_kfs[3, 0] += dx_aim * 1.0
        p_kfs[3, 1] += dz_aim * 1.2

        # Batter state
        b_prev_act = np.zeros(5, dtype=np.float32)
        b_filtered_act = np.zeros(5, dtype=np.float32)
        swing_triggered = False
        locked_t_trigger = 0.0
        locked_swing_duration = 0.17
        has_contacted = False
        contact_step = -1
        contact_pos = None

        is_released = False
        frames = []
        outcome = "IN_PLAY"

        # 80 steps of 0.01s = 0.8s
        for step in range(80):
            current_time = step * 0.01

            # Pitcher kinematics
            t_norm = step / actual_release_step
            if t_norm < 0.35:
                w = t_norm / 0.35
                p_target = (1 - w) * p_kfs[0] + w * p_kfs[1]
            elif t_norm < 0.70:
                w = (t_norm - 0.35) / 0.35
                p_target = (1 - w) * p_kfs[1] + w * p_kfs[2]
            elif t_norm <= 1.0:
                w = (t_norm - 0.70) / 0.30
                p_target = (1 - w) * p_kfs[2] + w * p_kfs[3]
            else:
                w = min(1.0, (t_norm - 1.0) / 0.40)
                p_target = (1 - w) * p_kfs[3] + w * p_kfs[4]

            # Batter observation & policy predict
            ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
            ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
            t_remain = max(0.0, (ball_pos[1] - 0.20) / abs(ball_vel[1])) if abs(ball_vel[1]) > 1.0 else 0.0
            
            sweet_pos = self.data.site_xpos[self.sweet_spot_id]
            sweet_v = np.zeros(6, dtype=np.float64)
            mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_SITE, self.sweet_spot_id, sweet_v, 0)
            sweet_vel = sweet_v[3:6]

            b_obs = np.concatenate([
                ball_pos,
                ball_vel,
                np.array([t_remain], dtype=np.float32),
                b_goal,
                np.array([self.data.qpos[adr] for adr in self.b_qpos_adrs], dtype=np.float32),
                np.array([self.data.qvel[adr] for adr in self.b_qvel_adrs], dtype=np.float32),
                sweet_pos,
                sweet_vel,
                b_prev_act,
            ])
            b_act, _ = self.batter_policy.predict(b_obs, deterministic=True)
            b_filtered_act = 0.6 * b_filtered_act + 0.4 * b_act
            b_prev_act = b_act.copy()

            # Swing trigger
            dt_lead = float(b_filtered_act[0]) * 0.030
            dz_bat = float(b_filtered_act[1]) * 0.08
            dalpha_plane = float(b_filtered_act[2]) * 0.15
            delbow = float(b_filtered_act[4]) * 0.15

            nom_t_flight = 9.5 / speed
            nom_t_trigger = 0.22 + nom_t_flight - 0.126
            if not swing_triggered and current_time >= (nom_t_trigger + dt_lead):
                swing_triggered = True
                locked_t_trigger = current_time

            b_kfs = self.b_keyframes.copy()
            b_kfs[3, 1] += dz_bat * 0.6
            b_kfs[3, 2] += dalpha_plane * 0.6
            b_kfs[3, 4] += delbow * 0.6
            b_kfs[4, 1] += dz_bat * 1.0
            b_kfs[4, 2] += dalpha_plane * 1.0
            b_kfs[4, 4] += delbow * 1.0

            # Substep physics
            for _ in range(5):
                # Batter target
                if not swing_triggered:
                    b_target = b_kfs[0]
                else:
                    prog = (current_time - locked_t_trigger) / locked_swing_duration
                    if prog < 0.20:
                        b_target = (1.0 - prog/0.20)*b_kfs[0] + (prog/0.20)*b_kfs[1]
                    elif prog < 0.45:
                        b_target = (1.0 - (prog-0.2)/0.25)*b_kfs[1] + ((prog-0.2)/0.25)*b_kfs[2]
                    elif prog < 0.70:
                        b_target = (1.0 - (prog-0.45)/0.25)*b_kfs[2] + ((prog-0.45)/0.25)*b_kfs[3]
                    elif prog < 0.90:
                        b_target = (1.0 - (prog-0.7)/0.20)*b_kfs[3] + ((prog-0.7)/0.20)*b_kfs[4]
                    else:
                        b_target = (1.0 - min(1.0, (prog-0.9)/0.30))*b_kfs[4] + min(1.0, (prog-0.9)/0.30)*b_kfs[5]

                # Low level PD torques
                for i in range(5):
                    # Pitcher
                    qp = self.data.qpos[self.p_qpos_adrs[i]]
                    dqp = self.data.qvel[self.p_qvel_adrs[i]]
                    tau_p = self.p_Kp[i] * (p_target[i] - qp) - self.p_Kd[i] * dqp
                    cr_p = self.model.actuator_ctrlrange[self.p_act_ids[i]]
                    self.data.ctrl[self.p_act_ids[i]] = np.clip(tau_p, cr_p[0], cr_p[1])

                    # Batter
                    qb = self.data.qpos[self.b_qpos_adrs[i]]
                    dqb = self.data.qvel[self.b_qvel_adrs[i]]
                    tau_b = self.b_Kp[i] * (b_target[i] - qb) - self.b_Kd[i] * dqb
                    cr_b = self.model.actuator_ctrlrange[self.b_act_ids[i]]
                    self.data.ctrl[self.b_act_ids[i]] = np.clip(tau_b, cr_b[0], cr_b[1])

                # Release check
                if not is_released and step >= actual_release_step:
                    is_released = True
                    if self.weld_eq_id >= 0:
                        self.data.eq_active[self.weld_eq_id] = False
                    
                    tx = target_x + dx_aim
                    tz = target_z + dz_aim
                    sp = speed * (1.0 + dv_scale)
                    hp = self.data.site_xpos[self.p_hand_site_id]
                    tf = hp[1] / sp
                    vy = -sp
                    vx = (tx - hp[0]) / tf - 0.14
                    drop = 0.5 * 9.81 * (tf ** 2)
                    vz = (tz + drop - hp[2]) / tf
                    if pitch_type == 0:
                        vz += 0.13
                    elif pitch_type == 1:
                        vx -= 0.12
                    elif pitch_type == 2:
                        vz += 0.05
                    self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]

                # Aerodynamics
                if is_released and not has_contacted:
                    v = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                    v_norm = np.linalg.norm(v)
                    if v_norm > 1.0:
                        fd = -0.5 * self.rho * self.Cd * self.A_ball * v_norm * v
                        fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(spin, v)
                        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += (fd + fm) / self.m_ball * 0.002

                mujoco.mj_step(self.model, self.data)

                # Contact check
                for c in range(self.data.ncon):
                    con = self.data.contact[c]
                    g1, g2 = con.geom1, con.geom2
                    if (g1 == self.bat_geom_id and g2 == self.ball_geom_id) or (g2 == self.bat_geom_id and g1 == self.ball_geom_id):
                        if not has_contacted:
                            has_contacted = True
                            contact_step = step
                            contact_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()

            # Render frame
            self.renderer.update_scene(self.data, camera="duel_broadcast_cam")
            frame = self.renderer.render()
            hud = frame.copy()
            cv2.putText(hud, f"DUEL MATCH: Pitcher vs Batter", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(hud, f"Pitch: {pname} ({speed*3.6:.1f} km/h)", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            goal_cat = "PULL" if target_azimuth_deg < -10 else ("PUSH" if target_azimuth_deg > 10 else "CENTER")
            cv2.putText(hud, f"Batter Aim: {goal_cat} ({target_azimuth_deg:+.1f} deg)", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            if has_contacted:
                cv2.putText(hud, "SOLID CONTACT! LINE DRIVE!", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            frames.append(hud)

            if has_contacted and step >= contact_step + 15:
                break
            if ball_pos[1] < -1.5:
                outcome = "STRIKE / MISS"
                break

        if has_contacted:
            bvel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
            if bvel[1] > 0.1:
                outcome = f"FAIR HIT ({goal_cat})"
            else:
                outcome = "FOUL BALL"

        return frames, outcome, pname, speed*3.6, target_azimuth_deg, has_contacted


def main():
    print("=" * 60)
    print("Simulating Closed-Loop Pitcher vs Batter Duel Matches")
    print("=" * 60)
    sim = DuelMatchSimulator()

    all_frames = []
    outcomes = []
    contacts = 0

    os.makedirs("logs/videos", exist_ok=True)

    for match_ep in range(10):
        frames, outcome, pname, spd, aim_deg, contacted = sim.run_match_episode(match_ep, seed=100 + match_ep * 37)
        if contacted:
            contacts += 1
        outcomes.append(outcome)
        print(f"Match #{match_ep+1:2d}: Pitch={pname:10s} ({spd:4.1f} km/h) | Batter Aim={aim_deg:+5.1f}° | Outcome: {outcome}")

        # Save first 3 matches into video reel
        if match_ep < 3:
            all_frames.extend(frames)
            # Add 10 black frames between matches
            blank = np.zeros_like(frames[0])
            for _ in range(10):
                all_frames.append(blank)

    out_video = "logs/videos/pitcher_vs_batter_match.mp4"
    h, w, _ = all_frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_video, fourcc, 50, (w, h))
    for f in all_frames:
        writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
    writer.release()
    print(f"\nSaved closed-loop duel video: {out_video} ({len(all_frames)} frames)")
    print(f"Overall Duel Contact Rate: {(contacts/10)*100:.1f}% ({contacts}/10 matches)")

    sim.renderer.close()

if __name__ == "__main__":
    main()
