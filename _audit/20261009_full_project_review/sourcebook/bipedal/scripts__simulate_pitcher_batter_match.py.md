# bipedal/scripts/simulate_pitcher_batter_match.py

원본: [scripts/simulate_pitcher_batter_match.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/simulate_pitcher_batter_match.py)

SHA256: `504ada84f6047626f75d83cd77907941ec299426319a70ba01450ef2d91c04a3`

전체 391행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `DuelMatchSimulator` | ClassDef | 22 | 348 |
| `__init__` | FunctionDef | 23 | 90 |
| `run_match_episode` | FunctionDef | 92 | 348 |
| `main` | FunctionDef | 351 | 388 |

## 전체 원문

````text
    1 | """
    2 | Closed-Loop Pitcher vs Batter Duel Simulation.
    3 | Combines both trained H1 policies in the unified arena (models/h1_duel_match.xml):
    4 | - Pitcher AI: pitches Fastballs, Sliders, and Curveballs into the 9-grid strike zone.
    5 | - Batter AI: reads the incoming flight trajectory and executes goal-conditioned directional hits.
    6 | Renders full-game broadcast video and extracts visual inspection frames.
    7 | """
    8 | 
    9 | import os
   10 | import sys
   11 | import numpy as np
   12 | import cv2
   13 | import mujoco
   14 | 
   15 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   16 | if BASE_DIR not in sys.path:
   17 |     sys.path.insert(0, BASE_DIR)
   18 | 
   19 | from stable_baselines3 import PPO
   20 | 
   21 | 
   22 | class DuelMatchSimulator:
   23 |     def __init__(
   24 |         self,
   25 |         xml_path="models/h1_duel_match.xml",
   26 |         pitcher_model_path="checkpoints/best_pitcher_model.zip",
   27 |         batter_model_path="checkpoints/best_phase2_hardened_model.zip",
   28 |     ):
   29 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   30 |         self.data = mujoco.MjData(self.model)
   31 | 
   32 |         self.pitcher_policy = PPO.load(pitcher_model_path)
   33 |         self.batter_policy = PPO.load(batter_model_path)
   34 | 
   35 |         # Actuator IDs
   36 |         self.p_act_names = ["p_torso", "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"]
   37 |         self.b_act_names = ["b_torso", "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"]
   38 | 
   39 |         self.p_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.p_act_names]
   40 |         self.b_act_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in self.b_act_names]
   41 | 
   42 |         self.p_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
   43 |         self.p_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.p_act_ids]
   44 | 
   45 |         self.b_qpos_adrs = [self.model.jnt_qposadr[self.model.actuator_trnid[a, 0]] for a in self.b_act_ids]
   46 |         self.b_qvel_adrs = [self.model.jnt_dofadr[self.model.actuator_trnid[a, 0]] for a in self.b_act_ids]
   47 | 
   48 |         # Ball
   49 |         ball_jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   50 |         self.ball_qpos_adr = self.model.jnt_qposadr[ball_jnt_id]
   51 |         self.ball_qvel_adr = self.model.jnt_dofadr[ball_jnt_id]
   52 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   53 |         self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   54 |         self.sweet_spot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "bat_sweet_spot")
   55 |         self.p_hand_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_pitcher_hand_site")
   56 |         self.weld_eq_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_EQUALITY, "p_ball_weld")
   57 | 
   58 |         # Stances and Gains
   59 |         self.p_Kp = np.array([450.0, 350.0, 250.0, 150.0, 150.0], dtype=np.float32)
   60 |         self.p_Kd = np.array([35.0,  25.0,  20.0,  12.0,  12.0], dtype=np.float32)
   61 | 
   62 |         self.b_Kp = np.array([450.0, 250.0, 180.0, 120.0, 120.0], dtype=np.float32)
   63 |         self.b_Kd = np.array([35.0,  20.0,  15.0,  10.0,  10.0], dtype=np.float32)
   64 | 
   65 |         self.p_keyframes = np.array([
   66 |             [ 0.00,  0.00, -0.40,  0.00,  1.50],
   67 |             [ 0.80,  1.20, -0.60,  0.80,  1.60],
   68 |             [ 0.20, -0.20, -0.40,  0.30,  1.00],
   69 |             [-0.50, -1.40, -0.20, -0.20,  0.20],
   70 |             [-0.90, -1.80, -0.60, -0.50,  0.70],
   71 |         ], dtype=np.float32)
   72 | 
   73 |         self.b_keyframes = np.array([
   74 |             [-0.40, -1.00,  0.00,  0.40,  1.50],
   75 |             [-0.60, -1.15,  0.00,  0.60,  1.70],
   76 |             [-0.10, -0.70, -0.05,  0.20,  1.20],
   77 |             [ 0.50, -0.30, -0.10, -0.10,  0.70],
   78 |             [ 1.15,  0.20, -0.08, -0.40,  0.35],
   79 |             [ 1.70,  0.80,  0.00, -0.70,  1.20]
   80 |         ], dtype=np.float32)
   81 | 
   82 |         # Aerodynamic constants
   83 |         self.rho = 1.205
   84 |         self.r_ball = 0.037
   85 |         self.m_ball = 0.145
   86 |         self.A_ball = np.pi * (self.r_ball ** 2)
   87 |         self.Cd = 0.32
   88 |         self.Cl = 0.24
   89 | 
   90 |         self.renderer = mujoco.Renderer(self.model, height=480, width=640)
   91 | 
   92 |     def run_match_episode(self, episode_idx=0, seed=42):
   93 |         np.random.seed(seed)
   94 |         mujoco.mj_resetData(self.model, self.data)
   95 | 
   96 |         # Pitcher target & pitch type
   97 |         target_x = float(np.random.uniform(-0.14, 0.14))
   98 |         target_z = float(np.random.uniform(0.70, 0.90))
   99 |         pitch_type = int(np.random.choice([0, 1, 2]))
  100 |         p_one_hot = np.zeros(3, dtype=np.float32)
  101 |         p_one_hot[pitch_type] = 1.0
  102 | 
  103 |         if pitch_type == 0:
  104 |             speed = float(np.random.uniform(21.5, 23.5))
  105 |             spin = np.array([-180.0, 0.0, 0.0], dtype=np.float32)
  106 |             pname = "Fastball"
  107 |         elif pitch_type == 1:
  108 |             speed = float(np.random.uniform(19.0, 21.0))
  109 |             spin = np.array([-30.0, 0.0, 150.0], dtype=np.float32)
  110 |             pname = "Slider"
  111 |         else:
  112 |             speed = float(np.random.uniform(17.0, 19.0))
  113 |             spin = np.array([170.0, 0.0, -20.0], dtype=np.float32)
  114 |             pname = "Curveball"
  115 | 
  116 |         # Batter goal
  117 |         target_azimuth_deg = float(np.random.uniform(-30.0, 30.0))
  118 |         target_azimuth_rad = float(np.radians(target_azimuth_deg))
  119 |         target_launch_deg = float(np.random.uniform(15.0, 28.0))
  120 |         target_launch_rad = float(np.radians(target_launch_deg))
  121 |         target_exit_vel = 14.0
  122 | 
  123 |         b_goal = np.array([target_azimuth_rad, target_launch_rad, target_exit_vel], dtype=np.float32)
  124 | 
  125 |         # Set initial poses
  126 |         for i, adr in enumerate(self.p_qpos_adrs):
  127 |             self.data.qpos[adr] = self.p_keyframes[0, i]
  128 |         for i, adr in enumerate(self.b_qpos_adrs):
  129 |             self.data.qpos[adr] = self.b_keyframes[0, i]
  130 | 
  131 |         if self.weld_eq_id >= 0:
  132 |             self.data.eq_active[self.weld_eq_id] = True
  133 | 
  134 |         mujoco.mj_forward(self.model, self.data)
  135 |         hand_pos = self.data.site_xpos[self.p_hand_site_id]
  136 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
  137 |         self.data.qpos[self.ball_qpos_adr+3:self.ball_qpos_adr+7] = [1.0, 0.0, 0.0, 0.0]
  138 |         mujoco.mj_forward(self.model, self.data)
  139 | 
  140 |         # Get Pitcher Action from Policy
  141 |         p_obs = np.concatenate([
  142 |             np.array([target_x, target_z], dtype=np.float32),
  143 |             p_one_hot,
  144 |             self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3],
  145 |             self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3],
  146 |             hand_pos,
  147 |             np.zeros(3, dtype=np.float32),
  148 |             np.array([self.data.qpos[adr] for adr in self.p_qpos_adrs], dtype=np.float32),
  149 |             np.array([0.0], dtype=np.float32),
  150 |         ])
  151 |         p_act, _ = self.pitcher_policy.predict(p_obs, deterministic=True)
  152 | 
  153 |         dt_rel = float(p_act[0]) * 0.030
  154 |         dx_aim = float(p_act[1]) * 0.15
  155 |         dz_aim = float(p_act[2]) * 0.12
  156 |         dv_scale = float(p_act[3]) * 0.15
  157 | 
  158 |         nominal_release_step = 22
  159 |         actual_release_step = int(np.clip(nominal_release_step + int(dt_rel / 0.01), 18, 26))
  160 | 
  161 |         # Modulate pitcher keyframes
  162 |         p_kfs = self.p_keyframes.copy()
  163 |         p_kfs[2, 0] += dx_aim * 0.5
  164 |         p_kfs[3, 0] += dx_aim * 1.0
  165 |         p_kfs[3, 1] += dz_aim * 1.2
  166 | 
  167 |         # Batter state
  168 |         b_prev_act = np.zeros(5, dtype=np.float32)
  169 |         b_filtered_act = np.zeros(5, dtype=np.float32)
  170 |         swing_triggered = False
  171 |         locked_t_trigger = 0.0
  172 |         locked_swing_duration = 0.17
  173 |         has_contacted = False
  174 |         contact_step = -1
  175 |         contact_pos = None
  176 | 
  177 |         is_released = False
  178 |         frames = []
  179 |         outcome = "IN_PLAY"
  180 | 
  181 |         # 80 steps of 0.01s = 0.8s
  182 |         for step in range(80):
  183 |             current_time = step * 0.01
  184 | 
  185 |             # Pitcher kinematics
  186 |             t_norm = step / actual_release_step
  187 |             if t_norm < 0.35:
  188 |                 w = t_norm / 0.35
  189 |                 p_target = (1 - w) * p_kfs[0] + w * p_kfs[1]
  190 |             elif t_norm < 0.70:
  191 |                 w = (t_norm - 0.35) / 0.35
  192 |                 p_target = (1 - w) * p_kfs[1] + w * p_kfs[2]
  193 |             elif t_norm <= 1.0:
  194 |                 w = (t_norm - 0.70) / 0.30
  195 |                 p_target = (1 - w) * p_kfs[2] + w * p_kfs[3]
  196 |             else:
  197 |                 w = min(1.0, (t_norm - 1.0) / 0.40)
  198 |                 p_target = (1 - w) * p_kfs[3] + w * p_kfs[4]
  199 | 
  200 |             # Batter observation & policy predict
  201 |             ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  202 |             ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
  203 |             t_remain = max(0.0, (ball_pos[1] - 0.20) / abs(ball_vel[1])) if abs(ball_vel[1]) > 1.0 else 0.0
  204 |             
  205 |             sweet_pos = self.data.site_xpos[self.sweet_spot_id]
  206 |             sweet_v = np.zeros(6, dtype=np.float64)
  207 |             mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_SITE, self.sweet_spot_id, sweet_v, 0)
  208 |             sweet_vel = sweet_v[3:6]
  209 | 
  210 |             b_obs = np.concatenate([
  211 |                 ball_pos,
  212 |                 ball_vel,
  213 |                 np.array([t_remain], dtype=np.float32),
  214 |                 b_goal,
  215 |                 np.array([self.data.qpos[adr] for adr in self.b_qpos_adrs], dtype=np.float32),
  216 |                 np.array([self.data.qvel[adr] for adr in self.b_qvel_adrs], dtype=np.float32),
  217 |                 sweet_pos,
  218 |                 sweet_vel,
  219 |                 b_prev_act,
  220 |             ])
  221 |             b_act, _ = self.batter_policy.predict(b_obs, deterministic=True)
  222 |             b_filtered_act = 0.6 * b_filtered_act + 0.4 * b_act
  223 |             b_prev_act = b_act.copy()
  224 | 
  225 |             # Swing trigger
  226 |             dt_lead = float(b_filtered_act[0]) * 0.030
  227 |             dz_bat = float(b_filtered_act[1]) * 0.08
  228 |             dalpha_plane = float(b_filtered_act[2]) * 0.15
  229 |             delbow = float(b_filtered_act[4]) * 0.15
  230 | 
  231 |             nom_t_flight = 9.5 / speed
  232 |             nom_t_trigger = 0.22 + nom_t_flight - 0.126
  233 |             if not swing_triggered and current_time >= (nom_t_trigger + dt_lead):
  234 |                 swing_triggered = True
  235 |                 locked_t_trigger = current_time
  236 | 
  237 |             b_kfs = self.b_keyframes.copy()
  238 |             b_kfs[3, 1] += dz_bat * 0.6
  239 |             b_kfs[3, 2] += dalpha_plane * 0.6
  240 |             b_kfs[3, 4] += delbow * 0.6
  241 |             b_kfs[4, 1] += dz_bat * 1.0
  242 |             b_kfs[4, 2] += dalpha_plane * 1.0
  243 |             b_kfs[4, 4] += delbow * 1.0
  244 | 
  245 |             # Substep physics
  246 |             for _ in range(5):
  247 |                 # Batter target
  248 |                 if not swing_triggered:
  249 |                     b_target = b_kfs[0]
  250 |                 else:
  251 |                     prog = (current_time - locked_t_trigger) / locked_swing_duration
  252 |                     if prog < 0.20:
  253 |                         b_target = (1.0 - prog/0.20)*b_kfs[0] + (prog/0.20)*b_kfs[1]
  254 |                     elif prog < 0.45:
  255 |                         b_target = (1.0 - (prog-0.2)/0.25)*b_kfs[1] + ((prog-0.2)/0.25)*b_kfs[2]
  256 |                     elif prog < 0.70:
  257 |                         b_target = (1.0 - (prog-0.45)/0.25)*b_kfs[2] + ((prog-0.45)/0.25)*b_kfs[3]
  258 |                     elif prog < 0.90:
  259 |                         b_target = (1.0 - (prog-0.7)/0.20)*b_kfs[3] + ((prog-0.7)/0.20)*b_kfs[4]
  260 |                     else:
  261 |                         b_target = (1.0 - min(1.0, (prog-0.9)/0.30))*b_kfs[4] + min(1.0, (prog-0.9)/0.30)*b_kfs[5]
  262 | 
  263 |                 # Low level PD torques
  264 |                 for i in range(5):
  265 |                     # Pitcher
  266 |                     qp = self.data.qpos[self.p_qpos_adrs[i]]
  267 |                     dqp = self.data.qvel[self.p_qvel_adrs[i]]
  268 |                     tau_p = self.p_Kp[i] * (p_target[i] - qp) - self.p_Kd[i] * dqp
  269 |                     cr_p = self.model.actuator_ctrlrange[self.p_act_ids[i]]
  270 |                     self.data.ctrl[self.p_act_ids[i]] = np.clip(tau_p, cr_p[0], cr_p[1])
  271 | 
  272 |                     # Batter
  273 |                     qb = self.data.qpos[self.b_qpos_adrs[i]]
  274 |                     dqb = self.data.qvel[self.b_qvel_adrs[i]]
  275 |                     tau_b = self.b_Kp[i] * (b_target[i] - qb) - self.b_Kd[i] * dqb
  276 |                     cr_b = self.model.actuator_ctrlrange[self.b_act_ids[i]]
  277 |                     self.data.ctrl[self.b_act_ids[i]] = np.clip(tau_b, cr_b[0], cr_b[1])
  278 | 
  279 |                 # Release check
  280 |                 if not is_released and step >= actual_release_step:
  281 |                     is_released = True
  282 |                     if self.weld_eq_id >= 0:
  283 |                         self.data.eq_active[self.weld_eq_id] = False
  284 |                     
  285 |                     tx = target_x + dx_aim
  286 |                     tz = target_z + dz_aim
  287 |                     sp = speed * (1.0 + dv_scale)
  288 |                     hp = self.data.site_xpos[self.p_hand_site_id]
  289 |                     tf = hp[1] / sp
  290 |                     vy = -sp
  291 |                     vx = (tx - hp[0]) / tf - 0.14
  292 |                     drop = 0.5 * 9.81 * (tf ** 2)
  293 |                     vz = (tz + drop - hp[2]) / tf
  294 |                     if pitch_type == 0:
  295 |                         vz += 0.13
  296 |                     elif pitch_type == 1:
  297 |                         vx -= 0.12
  298 |                     elif pitch_type == 2:
  299 |                         vz += 0.05
  300 |                     self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
  301 | 
  302 |                 # Aerodynamics
  303 |                 if is_released and not has_contacted:
  304 |                     v = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  305 |                     v_norm = np.linalg.norm(v)
  306 |                     if v_norm > 1.0:
  307 |                         fd = -0.5 * self.rho * self.Cd * self.A_ball * v_norm * v
  308 |                         fm = 0.5 * self.rho * self.Cl * self.A_ball * self.r_ball * np.cross(spin, v)
  309 |                         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] += (fd + fm) / self.m_ball * 0.002
  310 | 
  311 |                 mujoco.mj_step(self.model, self.data)
  312 | 
  313 |                 # Contact check
  314 |                 for c in range(self.data.ncon):
  315 |                     con = self.data.contact[c]
  316 |                     g1, g2 = con.geom1, con.geom2
  317 |                     if (g1 == self.bat_geom_id and g2 == self.ball_geom_id) or (g2 == self.bat_geom_id and g1 == self.ball_geom_id):
  318 |                         if not has_contacted:
  319 |                             has_contacted = True
  320 |                             contact_step = step
  321 |                             contact_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
  322 | 
  323 |             # Render frame
  324 |             self.renderer.update_scene(self.data, camera="duel_broadcast_cam")
  325 |             frame = self.renderer.render()
  326 |             hud = frame.copy()
  327 |             cv2.putText(hud, f"DUEL MATCH: Pitcher vs Batter", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
  328 |             cv2.putText(hud, f"Pitch: {pname} ({speed*3.6:.1f} km/h)", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
  329 |             goal_cat = "PULL" if target_azimuth_deg < -10 else ("PUSH" if target_azimuth_deg > 10 else "CENTER")
  330 |             cv2.putText(hud, f"Batter Aim: {goal_cat} ({target_azimuth_deg:+.1f} deg)", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
  331 |             if has_contacted:
  332 |                 cv2.putText(hud, "SOLID CONTACT! LINE DRIVE!", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
  333 |             frames.append(hud)
  334 | 
  335 |             if has_contacted and step >= contact_step + 15:
  336 |                 break
  337 |             if ball_pos[1] < -1.5:
  338 |                 outcome = "STRIKE / MISS"
  339 |                 break
  340 | 
  341 |         if has_contacted:
  342 |             bvel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
  343 |             if bvel[1] > 0.1:
  344 |                 outcome = f"FAIR HIT ({goal_cat})"
  345 |             else:
  346 |                 outcome = "FOUL BALL"
  347 | 
  348 |         return frames, outcome, pname, speed*3.6, target_azimuth_deg, has_contacted
  349 | 
  350 | 
  351 | def main():
  352 |     print("=" * 60)
  353 |     print("Simulating Closed-Loop Pitcher vs Batter Duel Matches")
  354 |     print("=" * 60)
  355 |     sim = DuelMatchSimulator()
  356 | 
  357 |     all_frames = []
  358 |     outcomes = []
  359 |     contacts = 0
  360 | 
  361 |     os.makedirs("logs/videos", exist_ok=True)
  362 | 
  363 |     for match_ep in range(10):
  364 |         frames, outcome, pname, spd, aim_deg, contacted = sim.run_match_episode(match_ep, seed=100 + match_ep * 37)
  365 |         if contacted:
  366 |             contacts += 1
  367 |         outcomes.append(outcome)
  368 |         print(f"Match #{match_ep+1:2d}: Pitch={pname:10s} ({spd:4.1f} km/h) | Batter Aim={aim_deg:+5.1f}° | Outcome: {outcome}")
  369 | 
  370 |         # Save first 3 matches into video reel
  371 |         if match_ep < 3:
  372 |             all_frames.extend(frames)
  373 |             # Add 10 black frames between matches
  374 |             blank = np.zeros_like(frames[0])
  375 |             for _ in range(10):
  376 |                 all_frames.append(blank)
  377 | 
  378 |     out_video = "logs/videos/pitcher_vs_batter_match.mp4"
  379 |     h, w, _ = all_frames[0].shape
  380 |     fourcc = cv2.VideoWriter_fourcc(*"mp4v")
  381 |     writer = cv2.VideoWriter(out_video, fourcc, 50, (w, h))
  382 |     for f in all_frames:
  383 |         writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
  384 |     writer.release()
  385 |     print(f"\nSaved closed-loop duel video: {out_video} ({len(all_frames)} frames)")
  386 |     print(f"Overall Duel Contact Rate: {(contacts/10)*100:.1f}% ({contacts}/10 matches)")
  387 | 
  388 |     sim.renderer.close()
  389 | 
  390 | if __name__ == "__main__":
  391 |     main()
````
