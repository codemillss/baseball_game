# baseball/archive/envs/baseball_game_env.py

원본: [archive/envs/baseball_game_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/envs/baseball_game_env.py)

SHA256: `0b045350353c2ef18bafc8cbc45dcf851a73cae7906af3938b3a9d65282f527d`

전체 486행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BaseballGameEnv` | ClassDef | 56 | 486 |
| `__init__` | FunctionDef | 73 | 132 |
| `_reset_count` | FunctionDef | 134 | 141 |
| `_get_pitcher_obs` | FunctionDef | 143 | 152 |
| `_get_batter_obs` | FunctionDef | 154 | 175 |
| `reset` | FunctionDef | 177 | 213 |
| `step` | FunctionDef | 215 | 345 |
| `_judge_outcome` | FunctionDef | 347 | 415 |
| `get_batter_trajectory_observations` | FunctionDef | 417 | 449 |
| `render` | FunctionDef | 451 | 455 |
| `_render_ansi` | FunctionDef | 457 | 486 |

## 전체 원문

````text
    1 | """
    2 | baseball_game_env.py — End-to-End Multi-Agent Gymnasium 환경
    3 | 
    4 | 투수(Pitcher)와 타자(Batter)의 대결을 Gymnasium 호환 환경으로 래핑합니다.
    5 | 각 에피소드는 1타석(최대 ~12구) 단위로 진행됩니다.
    6 | 
    7 | 에피소드 흐름:
    8 |     1. 투수가 Action 출력 → PitcherMechanism이 궤적 시뮬레이션
    9 |     2. 궤적을 시간 스텝별로 나누어 타자에게 Observation 제공
   10 |     3. 타자가 스윙 여부/토크 결정
   11 |     4. 충돌 판정 → 결과(Strike/Ball/Foul/Hit/HR) 판정
   12 |     5. Zero-sum Reward 배분
   13 | """
   14 | 
   15 | import gymnasium as gym
   16 | from gymnasium import spaces
   17 | import numpy as np
   18 | from typing import Optional, Tuple, Dict, Any
   19 | 
   20 | from envs.pitcher_mechanism import (
   21 |     PitcherMechanism,
   22 |     BallPhysics,
   23 |     PitchConfig,
   24 |     StrikeZone,
   25 | )
   26 | from envs.batter_mechanism import (
   27 |     BatterMechanism,
   28 |     BatModel,
   29 |     SwingConfig,
   30 | )
   31 | 
   32 | 
   33 | # ──────────────────────────────────────────────────────────────
   34 | #  Reward 상수
   35 | # ──────────────────────────────────────────────────────────────
   36 | 
   37 | REWARDS = {
   38 |     # 결과: (pitcher_reward, batter_reward)
   39 |     'called_strike':    (+1.0, -1.0),
   40 |     'swinging_strike':  (+1.5, -1.5),
   41 |     'ball':             (-1.0, +0.5),
   42 |     'foul':             (+0.3, -0.3),
   43 |     'out':              (+1.0, -1.0),
   44 |     'single':           (-2.0, +2.0),
   45 |     'extra_base':       (-3.0, +3.0),
   46 |     'home_run':         (-5.0, +5.0),
   47 |     'strikeout':        (+3.0, -3.0),   # 삼진 보너스
   48 |     'walk':             (-3.0, +3.0),   # 볼넷 보너스
   49 | }
   50 | 
   51 | 
   52 | # ──────────────────────────────────────────────────────────────
   53 | #  Multi-Agent 환경
   54 | # ──────────────────────────────────────────────────────────────
   55 | 
   56 | class BaseballGameEnv(gym.Env):
   57 |     """End-to-End Baseball Multi-Agent Gymnasium 환경.
   58 | 
   59 |     두 에이전트(Pitcher, Batter)가 교대로 행동하는 턴 기반 환경입니다.
   60 |     한 '투구'가 환경의 한 스텝에 해당합니다.
   61 | 
   62 |     Observation Space:
   63 |         Pitcher: [strikes, balls, prev_result, prev_plate_x, prev_plate_z, batter_stance] → Box(6)
   64 |         Batter:  [ball_pos(3), ball_vel(3), bat_pos(3), bat_vel(3), time_to_plate] → Box(13)
   65 | 
   66 |     Action Space:
   67 |         Pitcher: [v_release, θ_x, θ_z, ω_spin, a_axis] → Box(5)
   68 |         Batter:  [t_trigger, θ_yaw, θ_pitch, z_height] → Box(4)
   69 |     """
   70 | 
   71 |     metadata = {'render_modes': ['human', 'ansi'], 'render_fps': 30}
   72 | 
   73 |     def __init__(
   74 |         self,
   75 |         render_mode: Optional[str] = None,
   76 |         trajectory_substeps: int = 10,
   77 |     ):
   78 |         """
   79 |         Args:
   80 |             render_mode: 렌더링 모드 ('human', 'ansi', None)
   81 |             trajectory_substeps: 타자에게 제공할 궤적 관찰 시점 수
   82 |         """
   83 |         super().__init__()
   84 |         self.render_mode = render_mode
   85 |         self.trajectory_substeps = trajectory_substeps
   86 | 
   87 |         # 물리 엔진 초기화
   88 |         self.pitcher_mech = PitcherMechanism()
   89 |         self.batter_mech = BatterMechanism()
   90 |         self.strike_zone = StrikeZone()
   91 | 
   92 |         # ── Observation Spaces ──
   93 |         self.pitcher_obs_space = spaces.Box(
   94 |             low=np.array([0, 0, -1, -0.5, 0.0, 0], dtype=np.float32),
   95 |             high=np.array([2, 3, 5, 0.5, 1.5, 1], dtype=np.float32),
   96 |             dtype=np.float32,
   97 |         )
   98 |         self.batter_obs_space = spaces.Box(
   99 |             low=-np.ones(13, dtype=np.float32) * 100.0,
  100 |             high=np.ones(13, dtype=np.float32) * 100.0,
  101 |             dtype=np.float32,
  102 |         )
  103 | 
  104 |         # Gymnasium 호환을 위한 결합 space (실제로는 에이전트별 사용)
  105 |         self.observation_space = spaces.Dict({
  106 |             'pitcher': self.pitcher_obs_space,
  107 |             'batter': self.batter_obs_space,
  108 |         })
  109 | 
  110 |         # ── Action Spaces ──
  111 |         self.pitcher_action_space = spaces.Box(
  112 |             low=-np.ones(5, dtype=np.float32),
  113 |             high=np.ones(5, dtype=np.float32),
  114 |             dtype=np.float32,
  115 |         )
  116 |         self.batter_action_space = spaces.Box(
  117 |             low=-np.ones(4, dtype=np.float32),
  118 |             high=np.ones(4, dtype=np.float32),
  119 |             dtype=np.float32,
  120 |         )
  121 | 
  122 |         self.action_space = spaces.Dict({
  123 |             'pitcher': self.pitcher_action_space,
  124 |             'batter': self.batter_action_space,
  125 |         })
  126 | 
  127 |         # ── 게임 상태 ──
  128 |         self._reset_count()
  129 | 
  130 |         # ── 에피소드 데이터 수집 (Dashboard 연동) ──
  131 |         self.episode_data = []
  132 |         self.pitch_count = 0
  133 | 
  134 |     def _reset_count(self):
  135 |         """카운트를 초기화합니다."""
  136 |         self.strikes = 0
  137 |         self.balls = 0
  138 |         self.prev_result = 0   # 0=없음, 1=strike, 2=ball, 3=foul, 4=hit, 5=HR
  139 |         self.prev_plate_x = 0.0
  140 |         self.prev_plate_z = 0.75  # 존 중앙
  141 |         self.batter_stance = 0    # 0=우타, 1=좌타
  142 | 
  143 |     def _get_pitcher_obs(self) -> np.ndarray:
  144 |         """투수 관찰 벡터를 생성합니다."""
  145 |         return np.array([
  146 |             self.strikes,
  147 |             self.balls,
  148 |             self.prev_result,
  149 |             self.prev_plate_x,
  150 |             self.prev_plate_z,
  151 |             self.batter_stance,
  152 |         ], dtype=np.float32)
  153 | 
  154 |     def _get_batter_obs(
  155 |         self,
  156 |         ball_pos: np.ndarray,
  157 |         ball_vel: np.ndarray,
  158 |         bat_state: Optional[dict] = None,
  159 |         time_to_plate: float = 0.5,
  160 |     ) -> np.ndarray:
  161 |         """타자 관찰 벡터를 생성합니다."""
  162 |         if bat_state is None:
  163 |             bat_pos = np.zeros(3, dtype=np.float32)
  164 |             bat_vel = np.zeros(3, dtype=np.float32)
  165 |         else:
  166 |             bat_pos = bat_state['sweet_spot_position'].astype(np.float32)
  167 |             bat_vel = bat_state['sweet_spot_velocity'].astype(np.float32)
  168 | 
  169 |         return np.concatenate([
  170 |             ball_pos.astype(np.float32),
  171 |             ball_vel.astype(np.float32),
  172 |             bat_pos,
  173 |             bat_vel,
  174 |             [float(time_to_plate)],
  175 |         ]).astype(np.float32)
  176 | 
  177 |     def reset(
  178 |         self,
  179 |         seed: Optional[int] = None,
  180 |         options: Optional[dict] = None,
  181 |     ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
  182 |         """환경을 초기화합니다.
  183 | 
  184 |         Returns:
  185 |             (observations, info)
  186 |         """
  187 |         super().reset(seed=seed)
  188 |         self._reset_count()
  189 |         self.episode_data = []
  190 |         self.pitch_count = 0
  191 | 
  192 |         # 타자 스탠스 랜덤
  193 |         if self.np_random is not None:
  194 |             self.batter_stance = int(self.np_random.integers(0, 2))
  195 |         else:
  196 |             self.batter_stance = np.random.randint(0, 2)
  197 | 
  198 |         obs = {
  199 |             'pitcher': self._get_pitcher_obs(),
  200 |             'batter': self._get_batter_obs(
  201 |                 ball_pos=np.array([0.0, 18.44, 1.85]),
  202 |                 ball_vel=np.array([0.0, 0.0, 0.0]),
  203 |                 time_to_plate=0.5,
  204 |             ),
  205 |         }
  206 | 
  207 |         info = {
  208 |             'strikes': self.strikes,
  209 |             'balls': self.balls,
  210 |             'pitch_count': self.pitch_count,
  211 |         }
  212 | 
  213 |         return obs, info
  214 | 
  215 |     def step(
  216 |         self,
  217 |         action: Dict[str, np.ndarray],
  218 |     ) -> Tuple[Dict[str, np.ndarray], Dict[str, float], bool, bool, Dict[str, Any]]:
  219 |         """한 투구 사이클을 실행합니다.
  220 | 
  221 |         Args:
  222 |             action: {'pitcher': (5,), 'batter': (4,)} 액션 딕셔너리
  223 | 
  224 |         Returns:
  225 |             (obs, rewards, terminated, truncated, info)
  226 |         """
  227 |         pitcher_action = action['pitcher']
  228 |         batter_action = action['batter']
  229 | 
  230 |         # ── 1. 투구 시뮬레이션 ──
  231 |         pitch_result = self.pitcher_mech.pitch(pitcher_action)
  232 |         trajectory = pitch_result['trajectory']
  233 |         plate_x = pitch_result['plate_x']
  234 |         plate_z = pitch_result['plate_z']
  235 |         flight_time = trajectory['flight_time']
  236 | 
  237 |         # ── 2. 타자 스윙 판정 ──
  238 |         # 타자의 스윙 시작 시간: 공이 홈플레이트 부근에 도달하기 ~0.15초 전
  239 |         swing_start_time = max(0.0, flight_time - 0.20)
  240 | 
  241 |         swing_result = self.batter_mech.swing_and_check(
  242 |             action=batter_action,
  243 |             ball_trajectory_positions=trajectory['positions'],
  244 |             ball_trajectory_velocities=trajectory['velocities'],
  245 |             ball_trajectory_times=trajectory['times'],
  246 |             swing_start_time=swing_start_time,
  247 |         )
  248 | 
  249 |         # ── 3. 결과 판정 ──
  250 |         pitch_outcome = self._judge_outcome(
  251 |             swing_result, plate_x, plate_z
  252 |         )
  253 | 
  254 |         # ── 4. Reward 계산 ──
  255 |         reward_key = pitch_outcome['reward_key']
  256 |         pitcher_reward, batter_reward = REWARDS[reward_key]
  257 |         rewards = {
  258 |             'pitcher': pitcher_reward,
  259 |             'batter': batter_reward,
  260 |         }
  261 | 
  262 |         # ── 5. 카운트 업데이트 ──
  263 |         terminated = False
  264 |         self.pitch_count += 1
  265 | 
  266 |         if reward_key in ('called_strike', 'swinging_strike'):
  267 |             self.strikes += 1
  268 |             self.prev_result = 1
  269 |             if self.strikes >= 3:
  270 |                 # 삼진 보너스
  271 |                 p_bonus, b_bonus = REWARDS['strikeout']
  272 |                 rewards['pitcher'] += p_bonus
  273 |                 rewards['batter'] += b_bonus
  274 |                 terminated = True
  275 |         elif reward_key == 'ball':
  276 |             self.balls += 1
  277 |             self.prev_result = 2
  278 |             if self.balls >= 4:
  279 |                 # 볼넷 보너스
  280 |                 p_bonus, b_bonus = REWARDS['walk']
  281 |                 rewards['pitcher'] += p_bonus
  282 |                 rewards['batter'] += b_bonus
  283 |                 terminated = True
  284 |         elif reward_key == 'foul':
  285 |             if self.strikes < 2:
  286 |                 self.strikes += 1
  287 |             self.prev_result = 3
  288 |         elif reward_key in ('single', 'extra_base', 'home_run', 'out'):
  289 |             self.prev_result = 4 if reward_key != 'home_run' else 5
  290 |             terminated = True
  291 | 
  292 |         self.prev_plate_x = plate_x
  293 |         self.prev_plate_z = plate_z
  294 | 
  295 |         # 최대 투구 수 제한 (truncation)
  296 |         truncated = self.pitch_count >= 20
  297 | 
  298 |         # ── 6. 에피소드 데이터 수집 ──
  299 |         pitch_data = {
  300 |             'pitch_number': self.pitch_count,
  301 |             'plate_x': plate_x,
  302 |             'plate_z': plate_z,
  303 |             'arrival_speed_kmh': pitch_result['arrival_speed_kmh'],
  304 |             'spin_rate': pitch_result['params']['spin_rate_rpm'],
  305 |             'spin_axis': pitch_result['params']['spin_axis_angle'],
  306 |             'movement_x': pitch_result['movement_x'],
  307 |             'movement_z': pitch_result['movement_z'],
  308 |             'outcome': reward_key,
  309 |             'trajectory_positions': trajectory['positions'].tolist(),
  310 |             'strikes': self.strikes,
  311 |             'balls': self.balls,
  312 |         }
  313 | 
  314 |         if swing_result['result'] == 'hit' and swing_result['contact_info']:
  315 |             ci = swing_result['contact_info']
  316 |             pitch_data.update({
  317 |                 'exit_speed_kmh': ci['exit_speed_kmh'],
  318 |                 'launch_angle': ci['launch_angle'],
  319 |                 'spray_angle': ci['spray_angle'],
  320 |                 'sweet_spot_factor': ci['sweet_spot_factor'],
  321 |             })
  322 | 
  323 |         self.episode_data.append(pitch_data)
  324 | 
  325 |         # ── 7. 다음 관찰 ──
  326 |         # 타자에게는 공의 초기 상태를 다시 제공 (다음 투구 대기)
  327 |         obs = {
  328 |             'pitcher': self._get_pitcher_obs(),
  329 |             'batter': self._get_batter_obs(
  330 |                 ball_pos=trajectory['positions'][0],
  331 |                 ball_vel=trajectory['velocities'][0],
  332 |                 time_to_plate=flight_time,
  333 |             ),
  334 |         }
  335 | 
  336 |         info = {
  337 |             'pitch_outcome': pitch_outcome,
  338 |             'pitch_data': pitch_data,
  339 |             'strikes': self.strikes,
  340 |             'balls': self.balls,
  341 |             'pitch_count': self.pitch_count,
  342 |             'episode_data': self.episode_data,
  343 |         }
  344 | 
  345 |         return obs, rewards, terminated, truncated, info
  346 | 
  347 |     def _judge_outcome(
  348 |         self,
  349 |         swing_result: dict,
  350 |         plate_x: float,
  351 |         plate_z: float,
  352 |     ) -> dict:
  353 |         """투구/타격 결과를 종합 판정합니다.
  354 | 
  355 |         Args:
  356 |             swing_result: BatterMechanism.swing_and_check() 결과
  357 |             plate_x: 홈플레이트 통과 x 좌표
  358 |             plate_z: 홈플레이트 통과 z 좌표
  359 | 
  360 |         Returns:
  361 |             dict:
  362 |                 'reward_key': REWARDS 테이블 키
  363 |                 'description': 결과 설명 문자열
  364 |                 'is_strike_zone': 스트라이크존 내 여부
  365 |         """
  366 |         is_in_zone = self.strike_zone.is_strike(plate_x, plate_z)
  367 | 
  368 |         if swing_result['result'] == 'no_swing':
  369 |             # 방망이를 꺼내지 않음
  370 |             if is_in_zone:
  371 |                 return {
  372 |                     'reward_key': 'called_strike',
  373 |                     'description': '보송 스트라이크 (Called Strike)',
  374 |                     'is_strike_zone': True,
  375 |                 }
  376 |             else:
  377 |                 return {
  378 |                     'reward_key': 'ball',
  379 |                     'description': '볼 (Ball)',
  380 |                     'is_strike_zone': False,
  381 |                 }
  382 | 
  383 |         elif swing_result['result'] == 'swing_miss':
  384 |             # 헛스윙
  385 |             return {
  386 |                 'reward_key': 'swinging_strike',
  387 |                 'description': '헛스윙 (Swinging Strike)',
  388 |                 'is_strike_zone': is_in_zone,
  389 |             }
  390 | 
  391 |         elif swing_result['result'] == 'hit':
  392 |             # 타격 성공 → 타구 분류
  393 |             contact_info = swing_result['contact_info']
  394 |             hit_type = self.batter_mech.classify_hit(contact_info)
  395 | 
  396 |             descriptions = {
  397 |                 'foul': '파울 (Foul Ball)',
  398 |                 'home_run': '홈런! (Home Run!) 🎆',
  399 |                 'extra_base': '장타! (Extra Base Hit)',
  400 |                 'single': '안타 (Single)',
  401 |                 'out': '아웃 (Out)',
  402 |             }
  403 | 
  404 |             return {
  405 |                 'reward_key': hit_type,
  406 |                 'description': descriptions.get(hit_type, hit_type),
  407 |                 'is_strike_zone': is_in_zone,
  408 |                 'contact_info': contact_info,
  409 |             }
  410 | 
  411 |         return {
  412 |             'reward_key': 'ball',
  413 |             'description': '알 수 없는 결과',
  414 |             'is_strike_zone': is_in_zone,
  415 |         }
  416 | 
  417 |     def get_batter_trajectory_observations(
  418 |         self,
  419 |         trajectory: dict,
  420 |     ) -> list:
  421 |         """공 궤적을 시간 분할하여 타자 관찰 시퀀스를 생성합니다.
  422 | 
  423 |         LSTM 기반 타자 정책에 입력할 시계열 데이터를 생성합니다.
  424 | 
  425 |         Args:
  426 |             trajectory: PitcherMechanism.pitch()['trajectory'] 결과
  427 | 
  428 |         Returns:
  429 |             list of (observation, time) 튜플
  430 |         """
  431 |         positions = trajectory['positions']
  432 |         velocities = trajectory['velocities']
  433 |         times = trajectory['times']
  434 | 
  435 |         n = len(times)
  436 |         step = max(1, n // self.trajectory_substeps)
  437 |         indices = list(range(0, n, step))[:self.trajectory_substeps]
  438 | 
  439 |         observations = []
  440 |         for idx in indices:
  441 |             time_to_plate = times[-1] - times[idx]
  442 |             obs = self._get_batter_obs(
  443 |                 ball_pos=positions[idx],
  444 |                 ball_vel=velocities[idx],
  445 |                 time_to_plate=time_to_plate,
  446 |             )
  447 |             observations.append((obs, times[idx]))
  448 | 
  449 |         return observations
  450 | 
  451 |     def render(self) -> Optional[str]:
  452 |         """환경 상태를 렌더링합니다."""
  453 |         if self.render_mode == 'ansi':
  454 |             return self._render_ansi()
  455 |         return None
  456 | 
  457 |     def _render_ansi(self) -> str:
  458 |         """ASCII 텍스트로 스트라이크존과 카운트를 표시합니다."""
  459 |         sz = self.strike_zone
  460 |         lines = []
  461 |         lines.append(f"  ⚾ Count: {self.balls}B - {self.strikes}S")
  462 |         lines.append(f"  {'─' * 25}")
  463 | 
  464 |         # 9분할 스트라이크존 (3×3)
  465 |         zone_width = 7
  466 |         for row in range(2, -1, -1):  # 상 → 하
  467 |             row_str = "  │"
  468 |             for col in range(3):
  469 |                 cell = f" {'·':^{zone_width-2}} "
  470 |                 # 마지막 투구 위치 표시
  471 |                 loc = sz.zone_location(self.prev_plate_x, self.prev_plate_z)
  472 |                 if loc == (col, row):
  473 |                     cell = f" {'●':^{zone_width-2}} "
  474 |                 row_str += cell + "│"
  475 |             lines.append(row_str)
  476 |             if row > 0:
  477 |                 lines.append(f"  │{'─' * zone_width}│{'─' * zone_width}│{'─' * zone_width}│")
  478 | 
  479 |         lines.append(f"  {'─' * 25}")
  480 | 
  481 |         if self.episode_data:
  482 |             last = self.episode_data[-1]
  483 |             lines.append(f"  Last: {last['outcome']} | "
  484 |                         f"{last['arrival_speed_kmh']:.0f}km/h")
  485 | 
  486 |         return "\n".join(lines)
````
