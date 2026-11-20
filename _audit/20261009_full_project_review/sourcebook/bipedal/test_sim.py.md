# bipedal/test_sim.py

원본: [test_sim.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/test_sim.py)

SHA256: `888ad1e46a81c0dd51ca840cf523feb87f741f863d403a2dab935a8fe41fc388`

전체 181행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import numpy as np
    2 | import mujoco
    3 | from envs.athletic_duel_env import AthleticDuelEnv
    4 | 
    5 | MOD_W_X = np.array([-1.52, -0.699, 1.23, 0.096, 0.789, -3.251, 0.47, -1.369, 2.589])
    6 | MOD_W_Z = np.array([0.423, -0.633, -0.2, 0.114, -0.34, 0.292, -0.542, 0.364, -1.12])
    7 | 
    8 | hit_count = 0
    9 | pitch_hits = {'Fastball': [0, 0], 'Slider': [0, 0], 'Curveball': [0, 0]}
   10 | 
   11 | for seed in range(30):
   12 |     env = AthleticDuelEnv()
   13 |     obs, _ = env.reset(seed=seed * 100 + 42)
   14 |     env.c_pelvis_y_target = -0.850
   15 |     env.c_pelvis_z_target = 0.800
   16 |     env.data.qpos[env.c_pelvis_qpos_adr:env.c_pelvis_qpos_adr+3] = [0.0, -0.850, 0.800]
   17 |     mujoco.mj_forward(env.model, env.data)
   18 |     
   19 |     p_name = env.pitch_name
   20 |     pitch_hits[p_name][1] += 1
   21 |     
   22 |     for step in range(50):
   23 |         curr_time = (env.current_step) * env.dt
   24 |         b_p = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
   25 |         b_v = env.data.qvel[env.ball_qvel_adr:env.ball_qvel_adr+3]
   26 |         
   27 |         if env.is_released and abs(b_v[1]) > 3.0 and b_p[1] > 0.0:
   28 |             speed_y = abs(b_v[1])
   29 |             base_lead = 0.255 + (21.6 - speed_y) * 0.006
   30 |             t_rem = b_p[1] / speed_y
   31 |             if not env.swing_triggered and t_rem <= base_lead:
   32 |                 env.swing_triggered = True
   33 |                 env.locked_t_trigger = curr_time
   34 |                 env.locked_swing_duration = 0.220
   35 | 
   36 |         for s_idx in range(env.frame_skip):
   37 |             sim_time = curr_time + s_idx * env.model.opt.timestep
   38 |             if not env.is_released and env.current_step >= 2:
   39 |                 env.is_released = True
   40 |                 hp_now = env.data.site_xpos[env.p_hand_site_id].copy()
   41 |                 tgt_pt = np.array([env.target_pitch_x, 0.0, env.target_pitch_z], dtype=np.float32)
   42 |                 tf = (hp_now[1] - tgt_pt[1]) / env.pitch_speed
   43 |                 vx_rel = (tgt_pt[0] - hp_now[0]) / tf
   44 |                 vz_rel = (tgt_pt[2] + 0.5 * 9.81 * (tf**2) - hp_now[2]) / tf
   45 |                 env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3] = hp_now
   46 |                 env.data.qvel[env.ball_qvel_adr:env.ball_qvel_adr+3] = [vx_rel, -env.pitch_speed, vz_rel]
   47 | 
   48 |             if not env.swing_triggered:
   49 |                 b_upper_cmd = list(env.b_swing_keyframes[0])
   50 |                 b_target_x = -1.10
   51 |                 shift = 0.0
   52 |             else:
   53 |                 t_sw = sim_time - env.locked_t_trigger
   54 |                 prog = t_sw / env.locked_swing_duration
   55 |                 shift = np.clip(prog, 0.0, 1.0)
   56 |                 if prog < 0.20:
   57 |                     w = prog / 0.20
   58 |                     b_upper_cmd = [(1-w)*env.b_swing_keyframes[0][j] + w*env.b_swing_keyframes[1][j] for j in range(9)]
   59 |                 elif prog < 0.45:
   60 |                     w = (prog - 0.20) / 0.25
   61 |                     b_upper_cmd = [(1-w)*env.b_swing_keyframes[1][j] + w*env.b_swing_keyframes[2][j] for j in range(9)]
   62 |                 elif prog < 0.70:
   63 |                     w = (prog - 0.45) / 0.25
   64 |                     b_upper_cmd = [(1-w)*env.b_swing_keyframes[2][j] + w*env.b_swing_keyframes[3][j] for j in range(9)]
   65 |                 elif prog < 0.90:
   66 |                     w = (prog - 0.70) / 0.20
   67 |                     b_upper_cmd = [(1-w)*env.b_swing_keyframes[3][j] + w*env.b_swing_keyframes[4][j] for j in range(9)]
   68 |                 else:
   69 |                     w = min(1.0, (prog - 0.90) / 0.30)
   70 |                     b_upper_cmd = [(1-w)*env.b_swing_keyframes[4][j] + w*env.b_swing_keyframes[5][j] for j in range(9)]
   71 | 
   72 |                 b_p = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
   73 |                 b_v = env.data.qvel[env.ball_qvel_adr:env.ball_qvel_adr+3]
   74 |                 if env.is_released and abs(b_v[1]) > 1.0:
   75 |                     t_to_plate = max(0.0, b_p[1] / abs(b_v[1]))
   76 |                     pred_plate_x = float(b_p[0] + b_v[0] * t_to_plate)
   77 |                     pred_plate_z = float(b_p[2] + b_v[2] * t_to_plate - 0.5 * 9.81 * (t_to_plate ** 2))
   78 |                 else:
   79 |                     pred_plate_x = float(env.target_pitch_x)
   80 |                     pred_plate_z = float(env.target_pitch_z)
   81 | 
   82 |                 dx = pred_plate_x - (-0.05)
   83 |                 dz = pred_plate_z - 0.83
   84 |                 for j in range(9):
   85 |                     b_upper_cmd[j] += dx * MOD_W_X[j] + dz * MOD_W_Z[j]
   86 |                 b_target_x = -1.10 + np.clip(dx * 0.35, -0.03, 0.06)
   87 | 
   88 |             b_leg_curr = env.b_base_legs.copy()
   89 |             if env.swing_triggered:
   90 |                 b_leg_curr[0] += shift * 0.30
   91 |                 b_leg_curr[5] += shift * 0.30
   92 |                 b_leg_curr[7] += shift * 0.20
   93 |                 b_leg_curr[2] -= shift * 0.15
   94 |                 b_leg_curr[8] -= shift * 0.15
   95 |                 b_leg_curr[9] += shift * 0.30
   96 |                 b_leg_curr[3] -= shift * 0.06
   97 |                 b_leg_curr[4] -= shift * 0.04
   98 | 
   99 |             curr_ball_pos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
  100 |             if not env.is_hit and curr_ball_pos[1] <= 0.40:
  101 |                 sweet_pos = env.data.site_xpos[env.sweet_spot_id]
  102 |                 d_contact = float(np.linalg.norm(curr_ball_pos - sweet_pos))
  103 |                 has_col = any(
  104 |                     (env.data.contact[c].geom1 == env.bat_geom_id and env.data.contact[c].geom2 == env.ball_geom_id) or
  105 |                     (env.data.contact[c].geom2 == env.bat_geom_id and env.data.contact[c].geom1 == env.ball_geom_id)
  106 |                     for c in range(env.data.ncon)
  107 |                 )
  108 |                 if has_col or (d_contact <= 0.18 and abs(curr_ball_pos[1] - sweet_pos[1]) <= 0.09):
  109 |                     env.is_hit = True
  110 | 
  111 |             cp_x = env.data.qpos[env.c_pelvis_qpos_adr]
  112 |             cp_y = env.data.qpos[env.c_pelvis_qpos_adr + 1]
  113 |             cp_z = env.data.qpos[env.c_pelvis_qpos_adr + 2]
  114 |             cv_x = env.data.qvel[env.c_pelvis_qvel_adr]
  115 |             cv_y = env.data.qvel[env.c_pelvis_qvel_adr + 1]
  116 |             cv_z = env.data.qvel[env.c_pelvis_qvel_adr + 2]
  117 |             cw_z = env.data.qvel[env.c_pelvis_qvel_adr + 5]
  118 | 
  119 |             c_tau_hip = np.clip(-1800.0 * (env.c_pelvis_y_target - cp_y) - 80.0 * cv_y, -150.0, 150.0)
  120 |             c_tau_sag_ank = -np.clip(1200.0 * (env.c_pelvis_y_target - cp_y) - 80.0 * cv_y, -60.0, 60.0)
  121 |             c_tau_height_knee = -np.clip(2500.0 * (env.c_pelvis_z_target - cp_z) - 200.0 * cv_z, -200.0, 200.0)
  122 |             c_tau_lat_roll = np.clip(600.0 * (env.c_pelvis_x_target - cp_x) - 60.0 * cv_x, -60.0, 60.0)
  123 |             c_tau_yaw = np.clip(-100.0 * cw_z, -50.0, 50.0)
  124 | 
  125 |             for i, a_id in enumerate(env.c_leg_act_ids):
  126 |                 adr = env.c_leg_qpos_adrs[i]
  127 |                 tau = env.c_leg_Kp[i] * (env.q_squat_legs[i] - env.data.qpos[adr]) - env.c_leg_Kd[i] * env.data.qvel[env.c_leg_qvel_adrs[i]]
  128 |                 if i in [2, 7]: tau += c_tau_hip
  129 |                 elif i in [4, 9]: tau += c_tau_sag_ank
  130 |                 elif i in [3, 8]: tau += c_tau_height_knee
  131 |                 elif i in [1, 6]: tau += (c_tau_lat_roll if i == 1 else -c_tau_lat_roll)
  132 |                 elif i in [0, 5]: tau += c_tau_yaw
  133 |                 env.data.ctrl[a_id] = np.clip(tau, -250.0, 250.0)
  134 | 
  135 |             for i, a_id in enumerate(env.c_upper_act_ids):
  136 |                 adr = env.c_upper_qpos_adrs[i]
  137 |                 tau = env.c_upper_Kp * (env.q_squat_upper[i] - env.data.qpos[adr]) - env.c_upper_Kd * env.data.qvel[env.c_upper_qvel_adrs[i]]
  138 |                 env.data.ctrl[a_id] = np.clip(tau, -40.0, 40.0)
  139 | 
  140 |             for i, a_id in enumerate(env.b_upper_act_ids):
  141 |                 adr = env.b_upper_qpos_adrs[i]
  142 |                 tau = env.b_upper_Kp[i] * (b_upper_cmd[i] - env.data.qpos[adr]) - env.b_upper_Kd[i] * env.data.qvel[env.b_upper_qvel_adrs[i]]
  143 |                 env.data.ctrl[a_id] = np.clip(tau, -200.0, 200.0)
  144 | 
  145 |             p_x = env.data.qpos[env.b_pelvis_qpos_adr]
  146 |             p_y = env.data.qpos[env.b_pelvis_qpos_adr + 1]
  147 |             v_x = env.data.qvel[env.b_pelvis_qvel_adr]
  148 |             v_y = env.data.qvel[env.b_pelvis_qvel_adr + 1]
  149 |             w_z = env.data.qvel[env.b_pelvis_qvel_adr + 5]
  150 | 
  151 |             l_foot_z = env.data.xpos[env.b_left_ankle_id][2] - 0.065
  152 |             l_foot_vz = env.data.qvel[env.b_left_ankle_dof]
  153 |             tau_plant_knee = -np.clip(3000.0 * max(0.0, l_foot_z) + 120.0 * l_foot_vz, 0.0, 180.0)
  154 |             tau_plant_ank = -np.clip(1000.0 * max(0.0, l_foot_z), 0.0, 50.0)
  155 | 
  156 |             y_shift = shift * 0.06 if env.swing_triggered else 0.00
  157 |             tau_x_ank = np.clip(500.0 * (p_x - b_target_x) + 50.0 * v_x, -35.0, 35.0)
  158 |             tau_x_hip = np.clip(400.0 * (p_x - b_target_x) + 40.0 * v_x, -50.0, 50.0)
  159 |             tau_y_shift = np.clip(600.0 * ((env.b_pelvis_y_target + y_shift) - p_y) - 60.0 * v_y, -60.0, 60.0)
  160 |             tau_yaw = np.clip(80.0 * w_z, -50.0, 50.0)
  161 | 
  162 |             for i, a_id in enumerate(env.b_leg_act_ids):
  163 |                 adr = env.b_leg_qpos_adrs[i]
  164 |                 tau = env.b_leg_Kp[i] * (b_leg_curr[i] - env.data.qpos[adr]) - env.b_leg_Kd[i] * env.data.qvel[env.b_leg_qvel_adrs[i]]
  165 |                 if i == 3: tau += tau_plant_knee
  166 |                 elif i == 4: tau += tau_plant_ank + tau_x_ank
  167 |                 elif i == 9: tau += tau_x_ank
  168 |                 elif i in [2, 7]: tau += tau_x_hip + (tau_y_shift if i == 7 else -tau_y_shift * 0.5)
  169 |                 elif i in [0, 5]: tau += tau_yaw
  170 |                 env.data.ctrl[a_id] = np.clip(tau, -250.0, 250.0)
  171 | 
  172 |             mujoco.mj_step(env.model, env.data)
  173 |         env.current_step += 1
  174 | 
  175 |     if env.is_hit:
  176 |         hit_count += 1
  177 |         pitch_hits[p_name][0] += 1
  178 | 
  179 | print(f'Total Hits: {hit_count}/30 = {hit_count/30*100:.1f}%')
  180 | for p, (h, tot) in pitch_hits.items():
  181 |     print(f'  {p:10s}: {h}/{tot} = {h/max(1, tot)*100:.1f}%')
````
