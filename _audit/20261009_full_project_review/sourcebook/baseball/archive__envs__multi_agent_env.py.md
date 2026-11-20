# baseball/archive/envs/multi_agent_env.py

원본: [archive/envs/multi_agent_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/envs/multi_agent_env.py)

SHA256: `c7b127e27315523b4d9d63154d525052cbf986c61e0565220abb6a73fb9ff234`

전체 338행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `EnvConfig` | ClassDef | 22 | 27 |
| `MultiAgentBaseballEnv` | ClassDef | 29 | 338 |
| `__init__` | FunctionDef | 32 | 97 |
| `reset` | FunctionDef | 99 | 120 |
| `_sync_ball_to_hand` | FunctionDef | 122 | 126 |
| `_sync_ball_to_tee` | FunctionDef | 128 | 132 |
| `_get_obs` | FunctionDef | 134 | 168 |
| `step` | FunctionDef | 170 | 323 |
| `_check_contacts` | FunctionDef | 325 | 338 |

## 전체 원문

````text
    1 | """
    2 | multi_agent_env.py — 완전한 분산형 1인칭 Multi-Agent 야구 환경
    3 | 
    4 | 특징:
    5 |   1. 철저한 정보 격리: 타자는 batter_cam만, 투수는 pitcher_cam만 봄 (에고센트릭 시야)
    6 |   2. Action Space: Dict({pitcher: 8-DOF, batter: 9-DOF})
    7 |   3. Observation Space: Dict({pitcher: vision+prop, batter: vision+prop})
    8 |   4. 투구 릴리즈: 투수가 action[7] > 0.5를 입력하면 손에서 공이 홈플레이트를 향해 발사됨
    9 | """
   10 | 
   11 | import numpy as np
   12 | import gymnasium as gym
   13 | from gymnasium import spaces
   14 | import mujoco
   15 | from pathlib import Path
   16 | from typing import Dict, Any, Tuple
   17 | 
   18 | from envs.game_engine import BaseballGameEngine
   19 | from dataclasses import dataclass
   20 | 
   21 | @dataclass
   22 | class EnvConfig:
   23 |     mode: str = "full" # "full", "pitcher_only", "batter_only", "fielder_only"
   24 |     is_tee_ball: bool = False
   25 |     pitch_speed_y: float = -33.3  # m/s (approx 120km/h)
   26 |     strike_zone_scale: float = 1.0
   27 |     bat_speed_reward: bool = True
   28 | 
   29 | class MultiAgentBaseballEnv(gym.Env):
   30 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 60}
   31 | 
   32 |     def __init__(self, xml_path: str = None, frame_skip: int = 4, render_mode: str = "rgb_array", config: EnvConfig = None):
   33 |         super().__init__()
   34 |         self.config = config if config is not None else EnvConfig()
   35 |         if xml_path is None:
   36 |             xml_path = str(Path(__file__).parent.parent / "assets" / "stadium_3d.xml")
   37 | 
   38 |         self.model = mujoco.MjModel.from_xml_path(xml_path)
   39 |         self.data = mujoco.MjData(self.model)
   40 |         self.frame_skip = frame_skip
   41 |         self.render_mode = render_mode
   42 |         self.game_engine = BaseballGameEngine()
   43 | 
   44 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   45 |         self.ball_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   46 |         self.ball_qpos_adr = self.model.jnt_qposadr[self.ball_joint_id]
   47 |         self.ball_qvel_adr = self.model.jnt_dofadr[self.ball_joint_id]
   48 |         
   49 |         self.pitcher_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "pitcher_cam")
   50 |         self.batter_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "batter_cam")
   51 |         self.fielder_cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "fielder_cam")
   52 |         self.release_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "p_release_site")
   53 |         
   54 |         self.bat_barrel_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   55 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   56 |         self.cf_glove_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "cf_glove")
   57 | 
   58 |         # action_spaces
   59 |         self.action_space = spaces.Dict({
   60 |             "pitcher": spaces.Box(low=-1.0, high=1.0, shape=(8,), dtype=np.float32),
   61 |             "batter": spaces.Box(low=-1.0, high=1.0, shape=(9,), dtype=np.float32),
   62 |             "fielder": spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32),
   63 |         })
   64 | 
   65 |         # observation_spaces
   66 |         # vision is 64x64 RGB
   67 |         # pitcher prop: 7 joints (qpos+qvel = 14) + release state (1) = 15D
   68 |         # batter prop: 9 joints (qpos+qvel = 18) = 18D
   69 |         # fielder prop: 3 joints (qpos+qvel = 6) = 6D
   70 |         self.observation_space = spaces.Dict({
   71 |             "pitcher": spaces.Dict({
   72 |                 "vision": spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
   73 |                 "proprioception": spaces.Box(low=-100.0, high=100.0, shape=(15,), dtype=np.float32),
   74 |             }),
   75 |             "batter": spaces.Dict({
   76 |                 "vision": spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
   77 |                 "proprioception": spaces.Box(low=-100.0, high=100.0, shape=(18,), dtype=np.float32),
   78 |             }),
   79 |             "fielder": spaces.Dict({
   80 |                 "vision": spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
   81 |                 "proprioception": spaces.Box(low=-100.0, high=100.0, shape=(6,), dtype=np.float32),
   82 |             })
   83 |         })
   84 | 
   85 |         self.renderer_pitcher = None
   86 |         self.renderer_batter = None
   87 |         self.renderer_fielder = None
   88 |         if self.render_mode == "rgb_array":
   89 |             self.renderer_pitcher = mujoco.Renderer(self.model, height=64, width=64)
   90 |             self.renderer_batter = mujoco.Renderer(self.model, height=64, width=64)
   91 |             self.renderer_fielder = mujoco.Renderer(self.model, height=64, width=64)
   92 | 
   93 |         self.step_count = 0
   94 |         self.max_steps = 150 if self.config.is_tee_ball else 300
   95 |         self.is_released = False
   96 |         self.has_contacted = False
   97 |         self.contact_info = {}
   98 | 
   99 |     def reset(self, *, seed=None, options=None):
  100 |         super().reset(seed=seed)
  101 |         mujoco.mj_resetData(self.model, self.data)
  102 |         
  103 |         self.step_count = 0
  104 |         self.max_steps = 150 if self.config.is_tee_ball else 300
  105 |         self.is_released = False
  106 |         self.has_contacted = False
  107 |         self.is_caught = False
  108 |         self.contact_info = {}
  109 |         
  110 |         mujoco.mj_forward(self.model, self.data)
  111 |         
  112 |         # Move ball to pitcher's hand initially or Tee
  113 |         if self.config.is_tee_ball:
  114 |             self._sync_ball_to_tee()
  115 |         else:
  116 |             self._sync_ball_to_hand()
  117 |             
  118 |         mujoco.mj_forward(self.model, self.data)
  119 | 
  120 |         return self._get_obs(), {}
  121 | 
  122 |     def _sync_ball_to_hand(self):
  123 |         """볼을 투수의 손(p_release_site)에 고정"""
  124 |         hand_pos = self.data.site_xpos[self.release_site_id]
  125 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = hand_pos
  126 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, 0.0, 0.0]
  127 |         
  128 |     def _sync_ball_to_tee(self):
  129 |         """볼을 타자 앞 허공(Tee)에 고정"""
  130 |         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 0.0, 1.0] # 1m height at home plate
  131 |         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, 0.0, 0.0]
  132 |         self.is_released = True # Already "released" so it can be hit
  133 | 
  134 |     def _get_obs(self):
  135 |         obs = {"pitcher": {}, "batter": {}, "fielder": {}}
  136 |         
  137 |         if self.renderer_pitcher and self.renderer_batter and self.renderer_fielder:
  138 |             self.renderer_pitcher.update_scene(self.data, camera="pitcher_cam")
  139 |             obs["pitcher"]["vision"] = self.renderer_pitcher.render().copy()
  140 |             
  141 |             self.renderer_batter.update_scene(self.data, camera="batter_cam")
  142 |             obs["batter"]["vision"] = self.renderer_batter.render().copy()
  143 |             
  144 |             self.renderer_fielder.update_scene(self.data, camera="fielder_cam")
  145 |             obs["fielder"]["vision"] = self.renderer_fielder.render().copy()
  146 |         else:
  147 |             obs["pitcher"]["vision"] = np.zeros((64, 64, 3), dtype=np.uint8)
  148 |             obs["batter"]["vision"] = np.zeros((64, 64, 3), dtype=np.uint8)
  149 |             obs["fielder"]["vision"] = np.zeros((64, 64, 3), dtype=np.uint8)
  150 |             
  151 |         p_joints = ["p_shoulder_pitch", "p_shoulder_yaw", "p_shoulder_roll", 
  152 |                     "p_elbow_flex", "p_elbow_pronate", "p_wrist_flex", "p_wrist_dev"]
  153 |         p_qpos = [self.data.qpos[self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in p_joints]
  154 |         p_qvel = [self.data.qvel[self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in p_joints]
  155 |         obs["pitcher"]["proprioception"] = np.concatenate([p_qpos, p_qvel, [float(self.is_released)]], dtype=np.float32)
  156 | 
  157 |         b_joints = ["head_yaw", "head_pitch", "shoulder_yaw", "shoulder_pitch", "shoulder_roll", 
  158 |                     "elbow_flex", "wrist_yaw", "wrist_pitch", "wrist_roll"]
  159 |         b_qpos = [self.data.qpos[self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in b_joints]
  160 |         b_qvel = [self.data.qvel[self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in b_joints]
  161 |         obs["batter"]["proprioception"] = np.concatenate([b_qpos, b_qvel], dtype=np.float32)
  162 | 
  163 |         f_joints = ["cf_slide_x", "cf_slide_y", "cf_arm_pitch"]
  164 |         f_qpos = [self.data.qpos[self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in f_joints]
  165 |         f_qvel = [self.data.qvel[self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)]] for j in f_joints]
  166 |         obs["fielder"]["proprioception"] = np.concatenate([f_qpos, f_qvel], dtype=np.float32)
  167 | 
  168 |         return obs
  169 | 
  170 |     def step(self, actions: Dict[str, np.ndarray]):
  171 |         p_act = np.clip(actions["pitcher"], -1.0, 1.0)
  172 |         b_act = np.clip(actions["batter"], -1.0, 1.0)
  173 |         f_act = np.clip(actions["fielder"], -1.0, 1.0)
  174 |         
  175 |         # Override actions based on drill mode
  176 |         if self.config.mode == "batter_only":
  177 |             p_act = np.zeros(8, dtype=np.float32)
  178 |             p_act[7] = 1.0 # auto throw
  179 |             f_act = np.zeros(3, dtype=np.float32)
  180 |         elif self.config.mode == "pitcher_only":
  181 |             b_act = np.zeros(9, dtype=np.float32)
  182 |             f_act = np.zeros(3, dtype=np.float32)
  183 |         elif self.config.mode == "fielder_only":
  184 |             p_act = np.zeros(8, dtype=np.float32)
  185 |             p_act[7] = 1.0
  186 |             b_act = np.zeros(9, dtype=np.float32)
  187 | 
  188 |         # Apply Batter controls
  189 |         b_acts = ["head_yaw", "head_pitch", "shoulder_yaw", "shoulder_pitch", "shoulder_roll", 
  190 |                   "elbow_flex", "wrist_yaw", "wrist_pitch", "wrist_roll"]
  191 |         for i, act_name in enumerate(b_acts):
  192 |             act_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, act_name)
  193 |             cr_max = self.model.actuator_ctrlrange[act_id][1]
  194 |             self.data.ctrl[act_id] = b_act[i] * cr_max
  195 | 
  196 |         # Apply Pitcher controls
  197 |         p_acts = ["p_shoulder_pitch", "p_shoulder_yaw", "p_shoulder_roll", 
  198 |                   "p_elbow_flex", "p_elbow_pronate", "p_wrist_flex", "p_wrist_dev"]
  199 |         for i, act_name in enumerate(p_acts):
  200 |             act_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, act_name)
  201 |             cr_max = self.model.actuator_ctrlrange[act_id][1]
  202 |             self.data.ctrl[act_id] = p_act[i] * cr_max
  203 | 
  204 |         # Apply Fielder controls
  205 |         f_acts = ["cf_slide_x", "cf_slide_y", "cf_arm_pitch"]
  206 |         for i, act_name in enumerate(f_acts):
  207 |             act_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, act_name)
  208 |             cr_max = self.model.actuator_ctrlrange[act_id][1]
  209 |             self.data.ctrl[act_id] = f_act[i] * cr_max
  210 | 
  211 |         p_release_intent = p_act[7]
  212 |         
  213 |         for _ in range(self.frame_skip):
  214 |             mujoco.mj_step(self.model, self.data)
  215 |             self._check_contacts()
  216 |             
  217 |             if self.config.is_tee_ball and not self.has_contacted:
  218 |                 self._sync_ball_to_tee()
  219 |             elif not self.is_released:
  220 |                 if p_release_intent > 0.5:
  221 |                     self.is_released = True
  222 |                     
  223 |                     if self.config.mode == "batter_only":
  224 |                         # Batting Machine mode: Spawn at Y=15.0 (near mound) and throw towards home plate (Y=0)
  225 |                         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 15.0, 1.5]
  226 |                         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, self.config.pitch_speed_y, 1.5]
  227 |                     elif self.config.mode == "fielder_only":
  228 |                         # Fielder training: Auto hit a pop fly
  229 |                         self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 0.0, 1.0]
  230 |                         self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [np.random.uniform(-10, 10), 20.0, 30.0]
  231 |                         self.has_contacted = True # Trigger play
  232 |                     else:
  233 |                         # Full / Pitcher mode: Standard release from hand
  234 |                         self.data.qvel[self.ball_qvel_adr+1] = self.config.pitch_speed_y
  235 |                 else:
  236 |                     self._sync_ball_to_hand()
  237 | 
  238 |         self.step_count += 1
  239 |         obs = self._get_obs()
  240 |         
  241 |         rewards = {"pitcher": 0.0, "batter": 0.0, "fielder": 0.0}
  242 |         terminated = {"pitcher": False, "batter": False, "fielder": False, "__all__": False}
  243 |         truncated = {"pitcher": False, "batter": False, "fielder": False, "__all__": False}
  244 |         info = {"pitcher": {}, "batter": {}, "fielder": {}}
  245 | 
  246 |         ball_pos = self.data.xpos[self.ball_body_id]
  247 |         bat_pos = self.data.geom_xpos[self.bat_barrel_id]
  248 |         
  249 |         # Continuous Stance & Swing shaping rewards for Batter
  250 |         if not self.has_contacted and self.config.mode != "pitcher_only":
  251 |             if self.config.is_tee_ball:
  252 |                 # Tee-Ball: Encourage bat to hit the ball continuously
  253 |                 dist = np.linalg.norm(bat_pos - ball_pos)
  254 |                 rewards["batter"] += 0.05 * np.exp(-dist)
  255 |             else:
  256 |                 if ball_pos[1] > 2.0:
  257 |                     # Ball is far (coming from pitcher at +18): Encourage ready stance
  258 |                     stance_rew = 0.01 * max(0, bat_pos[2] - 0.8) + 0.01 * max(0, bat_pos[1])
  259 |                     rewards["batter"] += stance_rew
  260 |                 elif ball_pos[1] >= -1.0 and ball_pos[1] <= 2.0:
  261 |                     # Ball is close: Encourage bat barrel to be near the ball
  262 |                     dist = np.linalg.norm(bat_pos - ball_pos)
  263 |                     swing_rew = 0.02 * np.exp(-dist)
  264 |                     rewards["batter"] += swing_rew
  265 |                 
  266 |             # Energy Penalty (Prevent jittery/alien movements, heavily reduced so batter is not afraid to move)
  267 |             action_penalty = 0.0005 * np.sum(np.square(b_act))
  268 |             rewards["batter"] -= action_penalty
  269 |         
  270 |         if self.is_caught:
  271 |             # 뜬공 아웃 (Catch)
  272 |             rewards["fielder"] += 10.0
  273 |             rewards["batter"] -= 10.0
  274 |             rewards["pitcher"] += 5.0 # Pitcher is happy about the out
  275 |             terminated = {k: True for k in terminated}
  276 |             info["fielder"]["caught"] = True
  277 |             
  278 |         elif self.has_contacted and ball_pos[2] < 0.2:
  279 |             # 땅볼 혹은 안타 (일단 충돌 후 바닥에 닿으면 종료로 간주)
  280 |             rewards["batter"] += 10.0
  281 |             rewards["pitcher"] -= 10.0
  282 |             rewards["fielder"] -= 5.0 # Fielder missed it
  283 |             terminated = {k: True for k in terminated}
  284 |             info["batter"]["contact"] = True
  285 |             
  286 |         elif ball_pos[1] < -1.0 or ball_pos[2] < 0.0:
  287 |             if self.config.is_tee_ball:
  288 |                 # In Tee-ball, if the ball drops to the ground without contact, the batter failed.
  289 |                 rewards["batter"] -= 5.0
  290 |                 terminated = {k: True for k in terminated}
  291 |             else:
  292 |                 bat_speed = np.max(np.abs(b_act[2:7])) # 팔 관절 움직임으로 판단
  293 |                 swung = bat_speed > 0.5
  294 |                 target_x = self.data.qpos[self.ball_qpos_adr]
  295 |                 
  296 |                 # Strike zone based on config
  297 |                 in_sz = abs(target_x) <= (0.25 * self.config.strike_zone_scale)
  298 |                 
  299 |                 if in_sz and swung:
  300 |                     rewards["pitcher"] += 5.0
  301 |                     rewards["batter"] -= 5.0
  302 |                 elif in_sz and not swung:
  303 |                     rewards["pitcher"] += 3.0
  304 |                     rewards["batter"] -= 1.0
  305 |                 else:
  306 |                     rewards["batter"] += 2.0
  307 |                     rewards["pitcher"] -= 2.0
  308 |                     
  309 |                 # Punish batter for doing absolutely nothing if not in tee ball
  310 |                 if not swung and self.config.mode != "pitcher_only":
  311 |                     rewards["batter"] -= 2.0
  312 |                 
  313 |                 terminated = {k: True for k in terminated}
  314 |             
  315 |         # Reward shaping for bat speed on contact
  316 |         if self.has_contacted and self.config.bat_speed_reward:
  317 |             bat_speed = np.max(np.abs(b_act[2:7]))
  318 |             rewards["batter"] += bat_speed * 5.0 # Encourages hard swings
  319 | 
  320 |         if self.step_count >= self.max_steps:
  321 |             truncated = {k: True for k in truncated}
  322 |             
  323 |         return obs, rewards, terminated, truncated, info
  324 | 
  325 |     def _check_contacts(self):
  326 |         for i in range(self.data.ncon):
  327 |             con = self.data.contact[i]
  328 |             g1, g2 = con.geom1, con.geom2
  329 |             
  330 |             # 1. Bat - Ball Contact
  331 |             if not self.has_contacted:
  332 |                 if (g1 == self.ball_geom_id and g2 == self.bat_barrel_id) or (g2 == self.ball_geom_id and g1 == self.bat_barrel_id):
  333 |                     self.has_contacted = True
  334 |             
  335 |             # 2. Glove - Ball Contact (Flyout Catch)
  336 |             if not self.is_caught and self.has_contacted: # Only can catch if hit
  337 |                 if (g1 == self.ball_geom_id and g2 == self.cf_glove_id) or (g2 == self.ball_geom_id and g1 == self.cf_glove_id):
  338 |                     self.is_caught = True
````
