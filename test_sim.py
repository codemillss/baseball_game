import numpy as np
import mujoco
from envs.athletic_duel_env import AthleticDuelEnv

MOD_W_X = np.array([-1.52, -0.699, 1.23, 0.096, 0.789, -3.251, 0.47, -1.369, 2.589])
MOD_W_Z = np.array([0.423, -0.633, -0.2, 0.114, -0.34, 0.292, -0.542, 0.364, -1.12])

hit_count = 0
pitch_hits = {'Fastball': [0, 0], 'Slider': [0, 0], 'Curveball': [0, 0]}

for seed in range(30):
    env = AthleticDuelEnv()
    obs, _ = env.reset(seed=seed * 100 + 42)
    env.c_pelvis_y_target = -0.850
    env.c_pelvis_z_target = 0.800
    env.data.qpos[env.c_pelvis_qpos_adr:env.c_pelvis_qpos_adr+3] = [0.0, -0.850, 0.800]
    mujoco.mj_forward(env.model, env.data)
    
    p_name = env.pitch_name
    pitch_hits[p_name][1] += 1
    
    for step in range(50):
        curr_time = (env.current_step) * env.dt
        b_p = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
        b_v = env.data.qvel[env.ball_qvel_adr:env.ball_qvel_adr+3]
        
        if env.is_released and abs(b_v[1]) > 3.0 and b_p[1] > 0.0:
            speed_y = abs(b_v[1])
            base_lead = 0.255 + (21.6 - speed_y) * 0.006
            t_rem = b_p[1] / speed_y
            if not env.swing_triggered and t_rem <= base_lead:
                env.swing_triggered = True
                env.locked_t_trigger = curr_time
                env.locked_swing_duration = 0.220

        for s_idx in range(env.frame_skip):
            sim_time = curr_time + s_idx * env.model.opt.timestep
            if not env.is_released and env.current_step >= 2:
                env.is_released = True
                hp_now = env.data.site_xpos[env.p_hand_site_id].copy()
                tgt_pt = np.array([env.target_pitch_x, 0.0, env.target_pitch_z], dtype=np.float32)
                tf = (hp_now[1] - tgt_pt[1]) / env.pitch_speed
                vx_rel = (tgt_pt[0] - hp_now[0]) / tf
                vz_rel = (tgt_pt[2] + 0.5 * 9.81 * (tf**2) - hp_now[2]) / tf
                env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3] = hp_now
                env.data.qvel[env.ball_qvel_adr:env.ball_qvel_adr+3] = [vx_rel, -env.pitch_speed, vz_rel]

            if not env.swing_triggered:
                b_upper_cmd = list(env.b_swing_keyframes[0])
                b_target_x = -1.10
                shift = 0.0
            else:
                t_sw = sim_time - env.locked_t_trigger
                prog = t_sw / env.locked_swing_duration
                shift = np.clip(prog, 0.0, 1.0)
                if prog < 0.20:
                    w = prog / 0.20
                    b_upper_cmd = [(1-w)*env.b_swing_keyframes[0][j] + w*env.b_swing_keyframes[1][j] for j in range(9)]
                elif prog < 0.45:
                    w = (prog - 0.20) / 0.25
                    b_upper_cmd = [(1-w)*env.b_swing_keyframes[1][j] + w*env.b_swing_keyframes[2][j] for j in range(9)]
                elif prog < 0.70:
                    w = (prog - 0.45) / 0.25
                    b_upper_cmd = [(1-w)*env.b_swing_keyframes[2][j] + w*env.b_swing_keyframes[3][j] for j in range(9)]
                elif prog < 0.90:
                    w = (prog - 0.70) / 0.20
                    b_upper_cmd = [(1-w)*env.b_swing_keyframes[3][j] + w*env.b_swing_keyframes[4][j] for j in range(9)]
                else:
                    w = min(1.0, (prog - 0.90) / 0.30)
                    b_upper_cmd = [(1-w)*env.b_swing_keyframes[4][j] + w*env.b_swing_keyframes[5][j] for j in range(9)]

                b_p = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
                b_v = env.data.qvel[env.ball_qvel_adr:env.ball_qvel_adr+3]
                if env.is_released and abs(b_v[1]) > 1.0:
                    t_to_plate = max(0.0, b_p[1] / abs(b_v[1]))
                    pred_plate_x = float(b_p[0] + b_v[0] * t_to_plate)
                    pred_plate_z = float(b_p[2] + b_v[2] * t_to_plate - 0.5 * 9.81 * (t_to_plate ** 2))
                else:
                    pred_plate_x = float(env.target_pitch_x)
                    pred_plate_z = float(env.target_pitch_z)

                dx = pred_plate_x - (-0.05)
                dz = pred_plate_z - 0.83
                for j in range(9):
                    b_upper_cmd[j] += dx * MOD_W_X[j] + dz * MOD_W_Z[j]
                b_target_x = -1.10 + np.clip(dx * 0.35, -0.03, 0.06)

            b_leg_curr = env.b_base_legs.copy()
            if env.swing_triggered:
                b_leg_curr[0] += shift * 0.30
                b_leg_curr[5] += shift * 0.30
                b_leg_curr[7] += shift * 0.20
                b_leg_curr[2] -= shift * 0.15
                b_leg_curr[8] -= shift * 0.15
                b_leg_curr[9] += shift * 0.30
                b_leg_curr[3] -= shift * 0.06
                b_leg_curr[4] -= shift * 0.04

            curr_ball_pos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
            if not env.is_hit and curr_ball_pos[1] <= 0.40:
                sweet_pos = env.data.site_xpos[env.sweet_spot_id]
                d_contact = float(np.linalg.norm(curr_ball_pos - sweet_pos))
                has_col = any(
                    (env.data.contact[c].geom1 == env.bat_geom_id and env.data.contact[c].geom2 == env.ball_geom_id) or
                    (env.data.contact[c].geom2 == env.bat_geom_id and env.data.contact[c].geom1 == env.ball_geom_id)
                    for c in range(env.data.ncon)
                )
                if has_col or (d_contact <= 0.18 and abs(curr_ball_pos[1] - sweet_pos[1]) <= 0.09):
                    env.is_hit = True

            cp_x = env.data.qpos[env.c_pelvis_qpos_adr]
            cp_y = env.data.qpos[env.c_pelvis_qpos_adr + 1]
            cp_z = env.data.qpos[env.c_pelvis_qpos_adr + 2]
            cv_x = env.data.qvel[env.c_pelvis_qvel_adr]
            cv_y = env.data.qvel[env.c_pelvis_qvel_adr + 1]
            cv_z = env.data.qvel[env.c_pelvis_qvel_adr + 2]
            cw_z = env.data.qvel[env.c_pelvis_qvel_adr + 5]

            c_tau_hip = np.clip(-1800.0 * (env.c_pelvis_y_target - cp_y) - 80.0 * cv_y, -150.0, 150.0)
            c_tau_sag_ank = -np.clip(1200.0 * (env.c_pelvis_y_target - cp_y) - 80.0 * cv_y, -60.0, 60.0)
            c_tau_height_knee = -np.clip(2500.0 * (env.c_pelvis_z_target - cp_z) - 200.0 * cv_z, -200.0, 200.0)
            c_tau_lat_roll = np.clip(600.0 * (env.c_pelvis_x_target - cp_x) - 60.0 * cv_x, -60.0, 60.0)
            c_tau_yaw = np.clip(-100.0 * cw_z, -50.0, 50.0)

            for i, a_id in enumerate(env.c_leg_act_ids):
                adr = env.c_leg_qpos_adrs[i]
                tau = env.c_leg_Kp[i] * (env.q_squat_legs[i] - env.data.qpos[adr]) - env.c_leg_Kd[i] * env.data.qvel[env.c_leg_qvel_adrs[i]]
                if i in [2, 7]: tau += c_tau_hip
                elif i in [4, 9]: tau += c_tau_sag_ank
                elif i in [3, 8]: tau += c_tau_height_knee
                elif i in [1, 6]: tau += (c_tau_lat_roll if i == 1 else -c_tau_lat_roll)
                elif i in [0, 5]: tau += c_tau_yaw
                env.data.ctrl[a_id] = np.clip(tau, -250.0, 250.0)

            for i, a_id in enumerate(env.c_upper_act_ids):
                adr = env.c_upper_qpos_adrs[i]
                tau = env.c_upper_Kp * (env.q_squat_upper[i] - env.data.qpos[adr]) - env.c_upper_Kd * env.data.qvel[env.c_upper_qvel_adrs[i]]
                env.data.ctrl[a_id] = np.clip(tau, -40.0, 40.0)

            for i, a_id in enumerate(env.b_upper_act_ids):
                adr = env.b_upper_qpos_adrs[i]
                tau = env.b_upper_Kp[i] * (b_upper_cmd[i] - env.data.qpos[adr]) - env.b_upper_Kd[i] * env.data.qvel[env.b_upper_qvel_adrs[i]]
                env.data.ctrl[a_id] = np.clip(tau, -200.0, 200.0)

            p_x = env.data.qpos[env.b_pelvis_qpos_adr]
            p_y = env.data.qpos[env.b_pelvis_qpos_adr + 1]
            v_x = env.data.qvel[env.b_pelvis_qvel_adr]
            v_y = env.data.qvel[env.b_pelvis_qvel_adr + 1]
            w_z = env.data.qvel[env.b_pelvis_qvel_adr + 5]

            l_foot_z = env.data.xpos[env.b_left_ankle_id][2] - 0.065
            l_foot_vz = env.data.qvel[env.b_left_ankle_dof]
            tau_plant_knee = -np.clip(3000.0 * max(0.0, l_foot_z) + 120.0 * l_foot_vz, 0.0, 180.0)
            tau_plant_ank = -np.clip(1000.0 * max(0.0, l_foot_z), 0.0, 50.0)

            y_shift = shift * 0.06 if env.swing_triggered else 0.00
            tau_x_ank = np.clip(500.0 * (p_x - b_target_x) + 50.0 * v_x, -35.0, 35.0)
            tau_x_hip = np.clip(400.0 * (p_x - b_target_x) + 40.0 * v_x, -50.0, 50.0)
            tau_y_shift = np.clip(600.0 * ((env.b_pelvis_y_target + y_shift) - p_y) - 60.0 * v_y, -60.0, 60.0)
            tau_yaw = np.clip(80.0 * w_z, -50.0, 50.0)

            for i, a_id in enumerate(env.b_leg_act_ids):
                adr = env.b_leg_qpos_adrs[i]
                tau = env.b_leg_Kp[i] * (b_leg_curr[i] - env.data.qpos[adr]) - env.b_leg_Kd[i] * env.data.qvel[env.b_leg_qvel_adrs[i]]
                if i == 3: tau += tau_plant_knee
                elif i == 4: tau += tau_plant_ank + tau_x_ank
                elif i == 9: tau += tau_x_ank
                elif i in [2, 7]: tau += tau_x_hip + (tau_y_shift if i == 7 else -tau_y_shift * 0.5)
                elif i in [0, 5]: tau += tau_yaw
                env.data.ctrl[a_id] = np.clip(tau, -250.0, 250.0)

            mujoco.mj_step(env.model, env.data)
        env.current_step += 1

    if env.is_hit:
        hit_count += 1
        pitch_hits[p_name][0] += 1

print(f'Total Hits: {hit_count}/30 = {hit_count/30*100:.1f}%')
for p, (h, tot) in pitch_hits.items():
    print(f'  {p:10s}: {h}/{tot} = {h/max(1, tot)*100:.1f}%')
