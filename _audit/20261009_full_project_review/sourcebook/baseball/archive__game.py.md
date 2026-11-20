# baseball/archive/game.py

원본: [archive/game.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/game.py)

SHA256: `cc618886f2978f52ced61fdc9cac94d388ed7842cfc7aeab7bea8db8a3200662`

전체 567행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `Colors` | ClassDef | 32 | 45 |
| `clear_screen` | FunctionDef | 48 | 50 |
| `render_strike_zone` | FunctionDef | 53 | 154 |
| `render_hit_result` | FunctionDef | 157 | 191 |
| `get_pitcher_action_from_user` | FunctionDef | 198 | 223 |
| `get_batter_action_from_user` | FunctionDef | 226 | 253 |
| `BaseballGame` | ClassDef | 260 | 513 |
| `__init__` | FunctionDef | 266 | 299 |
| `_load_checkpoint` | FunctionDef | 301 | 305 |
| `_get_ai_pitcher_action` | FunctionDef | 307 | 314 |
| `_get_ai_batter_action` | FunctionDef | 316 | 323 |
| `play_at_bat` | FunctionDef | 325 | 446 |
| `_print_header` | FunctionDef | 448 | 457 |
| `run` | FunctionDef | 459 | 485 |
| `_print_game_summary` | FunctionDef | 487 | 513 |
| `main` | FunctionDef | 520 | 563 |

## 전체 원문

````text
    1 | """
    2 | game.py — 대화형 Playable 게임 메인 엔진
    3 | 
    4 | 학습된 모델(체크포인트)을 로딩하여 유저가 투수 또는 타자로 플레이할 수 있는
    5 | 터미널 기반 인터랙티브 게임을 제공합니다.
    6 | 
    7 | 사용법:
    8 |     python game.py                    # AI vs AI 관전 모드
    9 |     python game.py --role pitcher     # 유저가 투수로 플레이
   10 |     python game.py --role batter      # 유저가 타자로 플레이
   11 |     python game.py --checkpoint path  # 체크포인트 로드
   12 | """
   13 | 
   14 | import argparse
   15 | import sys
   16 | import time
   17 | import numpy as np
   18 | from pathlib import Path
   19 | from typing import Optional
   20 | 
   21 | import torch
   22 | 
   23 | from envs.baseball_game_env import BaseballGameEnv
   24 | from training.networks import PitcherAgent, BatterAgent, get_device
   25 | 
   26 | 
   27 | # ──────────────────────────────────────────────────────────────
   28 | #  ASCII 렌더링
   29 | # ──────────────────────────────────────────────────────────────
   30 | 
   31 | # ANSI 색상 코드
   32 | class Colors:
   33 |     RESET = '\033[0m'
   34 |     BOLD = '\033[1m'
   35 |     RED = '\033[91m'
   36 |     GREEN = '\033[92m'
   37 |     YELLOW = '\033[93m'
   38 |     BLUE = '\033[94m'
   39 |     MAGENTA = '\033[95m'
   40 |     CYAN = '\033[96m'
   41 |     WHITE = '\033[97m'
   42 |     DIM = '\033[2m'
   43 |     BG_RED = '\033[41m'
   44 |     BG_GREEN = '\033[42m'
   45 |     BG_BLUE = '\033[44m'
   46 | 
   47 | 
   48 | def clear_screen():
   49 |     """터미널 화면 초기화."""
   50 |     print('\033[2J\033[H', end='')
   51 | 
   52 | 
   53 | def render_strike_zone(
   54 |     plate_x: float,
   55 |     plate_z: float,
   56 |     outcome: str,
   57 |     count_str: str,
   58 |     speed_kmh: float,
   59 |     movement_x: float = 0.0,
   60 |     movement_z: float = 0.0,
   61 | ) -> str:
   62 |     """ASCII 스트라이크존을 렌더링합니다.
   63 | 
   64 |     11×11 그리드로 스트라이크존과 투구 위치를 표시합니다.
   65 |     """
   66 |     # 존 좌표 (미터 → 그리드 좌표)
   67 |     grid_w, grid_h = 11, 11
   68 |     sz_left, sz_right = 2, 8     # 그리드 상 존 경계
   69 |     sz_bottom, sz_top = 2, 8
   70 | 
   71 |     # 투구 위치를 그리드 좌표로 변환
   72 |     x_range = (-0.5, 0.5)   # 미터
   73 |     z_range = (0.0, 1.5)
   74 |     px = int((plate_x - x_range[0]) / (x_range[1] - x_range[0]) * (grid_w - 1))
   75 |     pz = int((plate_z - z_range[0]) / (z_range[1] - z_range[0]) * (grid_h - 1))
   76 |     px = max(0, min(px, grid_w - 1))
   77 |     pz = max(0, min(pz, grid_h - 1))
   78 | 
   79 |     # 결과별 색상
   80 |     outcome_colors = {
   81 |         'called_strike': Colors.RED,
   82 |         'swinging_strike': Colors.YELLOW,
   83 |         'ball': Colors.BLUE,
   84 |         'foul': Colors.YELLOW,
   85 |         'single': Colors.GREEN,
   86 |         'extra_base': Colors.CYAN,
   87 |         'home_run': Colors.MAGENTA,
   88 |         'out': Colors.DIM,
   89 |     }
   90 |     ball_color = outcome_colors.get(outcome, Colors.WHITE)
   91 | 
   92 |     # 결과별 이모지
   93 |     outcome_labels = {
   94 |         'called_strike': '⚡ Called Strike!',
   95 |         'swinging_strike': '💨 Swinging Strike!',
   96 |         'ball': '🔵 Ball',
   97 |         'foul': '⚠️  Foul Ball',
   98 |         'single': '🏏 Single!',
   99 |         'extra_base': '🔥 Extra Base Hit!',
  100 |         'home_run': '🎆 HOME RUN!!!',
  101 |         'out': '👊 Out',
  102 |         'strikeout': '🔥 STRIKEOUT!!!',
  103 |         'walk': '🚶 Walk (Four Balls)',
  104 |     }
  105 | 
  106 |     lines = []
  107 |     lines.append("")
  108 |     lines.append(f"  {Colors.BOLD}⚾ {count_str}{Colors.RESET}")
  109 |     lines.append(f"  {Colors.DIM}{'─' * 28}{Colors.RESET}")
  110 | 
  111 |     # 존 렌더링 (하단 → 상단)
  112 |     for row in range(grid_h - 1, -1, -1):
  113 |         line = "  "
  114 |         for col in range(grid_w):
  115 |             is_zone = (sz_left <= col <= sz_right and sz_bottom <= row <= sz_top)
  116 |             is_ball_here = (col == px and row == pz)
  117 | 
  118 |             if is_ball_here:
  119 |                 line += f"{ball_color}●{Colors.RESET} "
  120 |             elif is_zone:
  121 |                 # 존 경계선
  122 |                 if row == sz_bottom or row == sz_top:
  123 |                     if col == sz_left or col == sz_right:
  124 |                         line += f"{Colors.DIM}+{Colors.RESET} "
  125 |                     else:
  126 |                         line += f"{Colors.DIM}─{Colors.RESET} "
  127 |                 elif col == sz_left or col == sz_right:
  128 |                     line += f"{Colors.DIM}│{Colors.RESET} "
  129 |                 else:
  130 |                     # 9분할 격자
  131 |                     inner_col = (col - sz_left - 1)
  132 |                     inner_row = (row - sz_bottom - 1)
  133 |                     if inner_col == 1 or inner_col == 3:
  134 |                         line += f"{Colors.DIM}·{Colors.RESET} "
  135 |                     elif inner_row == 1 or inner_row == 3:
  136 |                         line += f"{Colors.DIM}·{Colors.RESET} "
  137 |                     else:
  138 |                         line += "  "
  139 |             else:
  140 |                 line += f"{Colors.DIM}.{Colors.RESET} "
  141 | 
  142 |         lines.append(line)
  143 | 
  144 |     lines.append(f"  {Colors.DIM}{'─' * 28}{Colors.RESET}")
  145 | 
  146 |     # 결과 출력
  147 |     label = outcome_labels.get(outcome, outcome)
  148 |     lines.append(f"  {Colors.BOLD}{label}{Colors.RESET}")
  149 |     lines.append(
  150 |         f"  {Colors.CYAN}Speed: {speed_kmh:.0f} km/h{Colors.RESET} | "
  151 |         f"{Colors.YELLOW}Movement: ({movement_x*100:.1f}, {movement_z*100:.1f}) cm{Colors.RESET}"
  152 |     )
  153 | 
  154 |     return "\n".join(lines)
  155 | 
  156 | 
  157 | def render_hit_result(contact_info: dict) -> str:
  158 |     """타격 결과를 ASCII로 표시합니다."""
  159 |     if not contact_info:
  160 |         return ""
  161 | 
  162 |     lines = []
  163 |     ev = contact_info.get('exit_speed_kmh', 0)
  164 |     la = contact_info.get('launch_angle', 0)
  165 |     sa = contact_info.get('spray_angle', 0)
  166 |     ss = contact_info.get('sweet_spot_factor', 0)
  167 | 
  168 |     lines.append(f"\n  {Colors.BOLD}🏏 Hit Details{Colors.RESET}")
  169 |     lines.append(f"  {Colors.DIM}{'─' * 28}{Colors.RESET}")
  170 | 
  171 |     # Exit Velocity 바
  172 |     ev_bar_len = int(min(ev / 200, 1.0) * 20)
  173 |     ev_color = Colors.GREEN if ev > 150 else (Colors.YELLOW if ev > 130 else Colors.RED)
  174 |     ev_bar = f"{'█' * ev_bar_len}{'░' * (20 - ev_bar_len)}"
  175 |     lines.append(f"  Exit Vel:  {ev_color}{ev:.0f} km/h{Colors.RESET} [{ev_bar}]")
  176 | 
  177 |     # Launch Angle
  178 |     la_indicator = "↗" if la > 0 else "↘" if la < 0 else "→"
  179 |     lines.append(f"  Launch:    {Colors.CYAN}{la:+.1f}°{Colors.RESET} {la_indicator}")
  180 | 
  181 |     # Spray Angle
  182 |     sa_indicator = "←" if sa > 0 else "→" if sa < 0 else "↑"
  183 |     lines.append(f"  Spray:     {Colors.YELLOW}{sa:+.1f}°{Colors.RESET} {sa_indicator}")
  184 | 
  185 |     # Sweet Spot
  186 |     ss_bar_len = int(ss * 20)
  187 |     ss_color = Colors.GREEN if ss > 0.9 else (Colors.YELLOW if ss > 0.7 else Colors.RED)
  188 |     ss_bar = f"{'█' * ss_bar_len}{'░' * (20 - ss_bar_len)}"
  189 |     lines.append(f"  Sweet Spot:{ss_color} {ss:.0%}{Colors.RESET} [{ss_bar}]")
  190 | 
  191 |     return "\n".join(lines)
  192 | 
  193 | 
  194 | # ──────────────────────────────────────────────────────────────
  195 | #  유저 입력 처리
  196 | # ──────────────────────────────────────────────────────────────
  197 | 
  198 | def get_pitcher_action_from_user() -> np.ndarray:
  199 |     """유저에게 투구 파라미터를 입력받습니다."""
  200 |     print(f"\n  {Colors.BOLD}⚾ 투구 설정{Colors.RESET}")
  201 |     print(f"  {Colors.DIM}(Enter로 기본값 사용){Colors.RESET}")
  202 | 
  203 |     try:
  204 |         v = input(f"  속도 [-1=느림, 0=보통, 1=빠름] (0): ").strip()
  205 |         v = float(v) if v else 0.0
  206 | 
  207 |         x = input(f"  좌우 [-1=좌, 0=중앙, 1=우] (0): ").strip()
  208 |         x = float(x) if x else 0.0
  209 | 
  210 |         z = input(f"  상하 [-1=낮음, 0=중앙, 1=높음] (0): ").strip()
  211 |         z = float(z) if z else 0.0
  212 | 
  213 |         spin = input(f"  스핀 [-1=적음, 0=보통, 1=많음] (0): ").strip()
  214 |         spin = float(spin) if spin else 0.0
  215 | 
  216 |         axis = input(f"  스핀축 [-1=커브, 0=직구, 1=슬라이더] (0): ").strip()
  217 |         axis = float(axis) if axis else 0.0
  218 | 
  219 |     except (ValueError, EOFError):
  220 |         return np.zeros(5, dtype=np.float32)
  221 | 
  222 |     action = np.array([v, x, z, spin, axis], dtype=np.float32)
  223 |     return np.clip(action, -1.0, 1.0)
  224 | 
  225 | 
  226 | def get_batter_action_from_user(time_hint: float = 0.5) -> np.ndarray:
  227 |     """유저에게 스윙 여부와 파라미터를 입력받습니다."""
  228 |     print(f"\n  {Colors.BOLD}🏏 타격 결정{Colors.RESET}")
  229 |     print(f"  {Colors.DIM}(투구 도착 예상: {time_hint:.2f}초){Colors.RESET}")
  230 | 
  231 |     try:
  232 |         swing = input(f"  스윙? [y/n] (n): ").strip().lower()
  233 | 
  234 |         if swing in ('y', 'yes', 'ㅛ'):
  235 |             trigger = 0.8
  236 | 
  237 |             yaw = input(f"  스윙 방향 [-1=당기기, 0=중앙, 1=밀어치기] (0.3): ").strip()
  238 |             yaw = float(yaw) if yaw else 0.3
  239 | 
  240 |             pitch = input(f"  배트 각도 [-1=다운, 0=수평, 1=어퍼컷] (0): ").strip()
  241 |             pitch = float(pitch) if pitch else 0.0
  242 | 
  243 |             height = input(f"  높이 [-1=낮게, 0=중간, 1=높게] (0): ").strip()
  244 |             height = float(height) if height else 0.0
  245 |         else:
  246 |             trigger = -0.8
  247 |             yaw, pitch, height = 0.0, 0.0, 0.0
  248 | 
  249 |     except (ValueError, EOFError):
  250 |         return np.array([-0.8, 0.0, 0.0, 0.0], dtype=np.float32)
  251 | 
  252 |     action = np.array([trigger, yaw, pitch, height], dtype=np.float32)
  253 |     return np.clip(action, -1.0, 1.0)
  254 | 
  255 | 
  256 | # ──────────────────────────────────────────────────────────────
  257 | #  게임 엔진
  258 | # ──────────────────────────────────────────────────────────────
  259 | 
  260 | class BaseballGame:
  261 |     """대화형 야구 게임 엔진.
  262 | 
  263 |     학습된 AI 또는 유저가 투수/타자로 플레이합니다.
  264 |     """
  265 | 
  266 |     def __init__(
  267 |         self,
  268 |         role: str = 'spectator',
  269 |         checkpoint_path: Optional[str] = None,
  270 |         delay: float = 1.0,
  271 |     ):
  272 |         """
  273 |         Args:
  274 |             role: 'spectator' (관전), 'pitcher' (유저가 투수), 'batter' (유저가 타자)
  275 |             checkpoint_path: 학습된 모델 체크포인트 경로
  276 |             delay: AI 행동 간 딜레이 (초)
  277 |         """
  278 |         self.role = role
  279 |         self.delay = delay
  280 |         self.device = get_device()
  281 | 
  282 |         # 환경
  283 |         self.env = BaseballGameEnv()
  284 | 
  285 |         # AI 에이전트
  286 |         self.pitcher_agent = PitcherAgent().to(self.device)
  287 |         self.batter_agent = BatterAgent().to(self.device)
  288 | 
  289 |         # 체크포인트 로드
  290 |         if checkpoint_path and Path(checkpoint_path).exists():
  291 |             self._load_checkpoint(checkpoint_path)
  292 |             print(f"  {Colors.GREEN}✅ 체크포인트 로드 완료{Colors.RESET}")
  293 |         else:
  294 |             print(f"  {Colors.YELLOW}⚠️  체크포인트 없음 — 랜덤 가중치 사용{Colors.RESET}")
  295 | 
  296 |         # 통계
  297 |         self.games_played = 0
  298 |         self.pitcher_total_wins = 0
  299 |         self.batter_total_wins = 0
  300 | 
  301 |     def _load_checkpoint(self, path: str):
  302 |         """체크포인트를 로드합니다."""
  303 |         checkpoint = torch.load(path, map_location=self.device, weights_only=False)
  304 |         self.pitcher_agent.load_state_dict(checkpoint['pitcher_state_dict'])
  305 |         self.batter_agent.load_state_dict(checkpoint['batter_state_dict'])
  306 | 
  307 |     def _get_ai_pitcher_action(self, obs: np.ndarray) -> np.ndarray:
  308 |         """AI 투수의 액션을 생성합니다."""
  309 |         obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
  310 |         with torch.no_grad():
  311 |             action, _, _, _ = self.pitcher_agent.get_action_and_value(
  312 |                 obs_tensor, deterministic=True
  313 |             )
  314 |         return action.cpu().numpy().squeeze()
  315 | 
  316 |     def _get_ai_batter_action(self, obs: np.ndarray) -> np.ndarray:
  317 |         """AI 타자의 액션을 생성합니다."""
  318 |         obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
  319 |         with torch.no_grad():
  320 |             action, _, _, _, _ = self.batter_agent.get_action_and_value(
  321 |                 obs_tensor, deterministic=True
  322 |             )
  323 |         return action.cpu().numpy().squeeze()
  324 | 
  325 |     def play_at_bat(self) -> dict:
  326 |         """1타석(At-Bat)을 실행합니다.
  327 | 
  328 |         Returns:
  329 |             타석 결과 딕셔너리
  330 |         """
  331 |         obs, info = self.env.reset()
  332 |         pitcher_obs = obs['pitcher']
  333 |         batter_obs = obs['batter']
  334 | 
  335 |         terminated = False
  336 |         truncated = False
  337 |         pitch_num = 0
  338 |         results = []
  339 | 
  340 |         clear_screen()
  341 |         self._print_header()
  342 | 
  343 |         while not terminated and not truncated:
  344 |             pitch_num += 1
  345 |             strikes = int(pitcher_obs[0])
  346 |             balls = int(pitcher_obs[1])
  347 |             count_str = f"Count: {balls}B - {strikes}S  |  Pitch #{pitch_num}"
  348 | 
  349 |             print(f"\n  {Colors.DIM}{'═' * 40}{Colors.RESET}")
  350 |             print(f"  {Colors.BOLD}Pitch #{pitch_num}{Colors.RESET}  |  "
  351 |                   f"{Colors.RED}{'●' * strikes}{'○' * (2 - strikes)}{Colors.RESET} "
  352 |                   f"{Colors.BLUE}{'●' * balls}{'○' * (3 - balls)}{Colors.RESET}")
  353 | 
  354 |             # 투수 액션
  355 |             if self.role == 'pitcher':
  356 |                 pitcher_action = get_pitcher_action_from_user()
  357 |             else:
  358 |                 pitcher_action = self._get_ai_pitcher_action(pitcher_obs)
  359 |                 if self.role == 'spectator':
  360 |                     time.sleep(self.delay * 0.5)
  361 | 
  362 |             # 타자 액션
  363 |             if self.role == 'batter':
  364 |                 batter_action = get_batter_action_from_user(
  365 |                     time_hint=batter_obs[12] if len(batter_obs) > 12 else 0.5
  366 |                 )
  367 |             else:
  368 |                 batter_action = self._get_ai_batter_action(batter_obs)
  369 | 
  370 |             # 환경 스텝
  371 |             action = {'pitcher': pitcher_action, 'batter': batter_action}
  372 |             next_obs, rewards, terminated, truncated, info = self.env.step(action)
  373 | 
  374 |             # 결과 표시
  375 |             pitch_data = info.get('pitch_data', {})
  376 |             pitch_outcome = info.get('pitch_outcome', {})
  377 | 
  378 |             outcome_key = pitch_outcome.get('reward_key', 'ball')
  379 |             plate_x = pitch_data.get('plate_x', 0.0)
  380 |             plate_z = pitch_data.get('plate_z', 0.75)
  381 |             speed = pitch_data.get('arrival_speed_kmh', 130.0)
  382 |             mv_x = pitch_data.get('movement_x', 0.0)
  383 |             mv_z = pitch_data.get('movement_z', 0.0)
  384 | 
  385 |             zone_render = render_strike_zone(
  386 |                 plate_x, plate_z, outcome_key, count_str,
  387 |                 speed, mv_x, mv_z,
  388 |             )
  389 |             print(zone_render)
  390 | 
  391 |             # 타격 결과 표시
  392 |             contact_info = pitch_outcome.get('contact_info')
  393 |             if contact_info:
  394 |                 print(render_hit_result(contact_info))
  395 | 
  396 |             results.append(outcome_key)
  397 | 
  398 |             # 다음 관찰
  399 |             pitcher_obs = next_obs['pitcher']
  400 |             batter_obs = next_obs['batter']
  401 | 
  402 |             if self.role == 'spectator':
  403 |                 time.sleep(self.delay)
  404 | 
  405 |         # 타석 종료
  406 |         final_strikes = int(pitcher_obs[0])
  407 |         final_balls = int(pitcher_obs[1])
  408 | 
  409 |         if final_strikes >= 3:
  410 |             at_bat_result = 'strikeout'
  411 |             winner = 'pitcher'
  412 |             print(f"\n  {Colors.RED}{Colors.BOLD}🔥 STRIKEOUT!!! ── "
  413 |                   f"삼진 아웃!{Colors.RESET}")
  414 |         elif final_balls >= 4:
  415 |             at_bat_result = 'walk'
  416 |             winner = 'batter'
  417 |             print(f"\n  {Colors.BLUE}{Colors.BOLD}🚶 WALK ── "
  418 |                   f"볼넷 출루!{Colors.RESET}")
  419 |         elif 'home_run' in results:
  420 |             at_bat_result = 'home_run'
  421 |             winner = 'batter'
  422 |             print(f"\n  {Colors.MAGENTA}{Colors.BOLD}🎆 HOME RUN!!! ── "
  423 |                   f"홈런!{Colors.RESET}")
  424 |         elif any(r in ('single', 'extra_base') for r in results):
  425 |             at_bat_result = 'hit'
  426 |             winner = 'batter'
  427 |             print(f"\n  {Colors.GREEN}{Colors.BOLD}🏏 HIT! ── "
  428 |                   f"안타!{Colors.RESET}")
  429 |         else:
  430 |             at_bat_result = 'out'
  431 |             winner = 'pitcher'
  432 |             print(f"\n  {Colors.DIM}{Colors.BOLD}👊 OUT ── "
  433 |                   f"아웃!{Colors.RESET}")
  434 | 
  435 |         if winner == 'pitcher':
  436 |             self.pitcher_total_wins += 1
  437 |         else:
  438 |             self.batter_total_wins += 1
  439 |         self.games_played += 1
  440 | 
  441 |         return {
  442 |             'result': at_bat_result,
  443 |             'winner': winner,
  444 |             'pitches': pitch_num,
  445 |             'outcomes': results,
  446 |         }
  447 | 
  448 |     def _print_header(self):
  449 |         """게임 헤더를 출력합니다."""
  450 |         print(f"""
  451 |   {Colors.BOLD}╔══════════════════════════════════════════╗
  452 |   ║     ⚾  BASEBALL RL GAME ENGINE  ⚾     ║
  453 |   ╚══════════════════════════════════════════╝{Colors.RESET}
  454 | 
  455 |   {Colors.DIM}Role: {self.role.upper()}{Colors.RESET}
  456 |   {Colors.DIM}Games: {self.games_played} | P-Wins: {self.pitcher_total_wins} | B-Wins: {self.batter_total_wins}{Colors.RESET}
  457 | """)
  458 | 
  459 |     def run(self, n_at_bats: int = 9):
  460 |         """N 타석 게임을 실행합니다.
  461 | 
  462 |         Args:
  463 |             n_at_bats: 실행할 타석 수 (기본 9)
  464 |         """
  465 |         print(f"\n  {Colors.BOLD}⚾ {n_at_bats}타석 게임을 시작합니다!{Colors.RESET}")
  466 |         print(f"  {Colors.DIM}Role: {self.role}{Colors.RESET}\n")
  467 | 
  468 |         game_results = []
  469 | 
  470 |         for i in range(n_at_bats):
  471 |             print(f"\n  {Colors.BOLD}{'═' * 40}{Colors.RESET}")
  472 |             print(f"  {Colors.BOLD}  📋 타석 {i+1}/{n_at_bats}{Colors.RESET}")
  473 |             print(f"  {Colors.BOLD}{'═' * 40}{Colors.RESET}")
  474 | 
  475 |             result = self.play_at_bat()
  476 |             game_results.append(result)
  477 | 
  478 |             if i < n_at_bats - 1:
  479 |                 try:
  480 |                     input(f"\n  {Colors.DIM}Press Enter to continue...{Colors.RESET}")
  481 |                 except EOFError:
  482 |                     break
  483 | 
  484 |         # 최종 결과
  485 |         self._print_game_summary(game_results)
  486 | 
  487 |     def _print_game_summary(self, results: list):
  488 |         """게임 종료 후 종합 결과를 표시합니다."""
  489 |         clear_screen()
  490 | 
  491 |         total = len(results)
  492 |         hits = sum(1 for r in results if r['winner'] == 'batter')
  493 |         outs = total - hits
  494 |         hrs = sum(1 for r in results if r['result'] == 'home_run')
  495 |         ks = sum(1 for r in results if r['result'] == 'strikeout')
  496 |         walks = sum(1 for r in results if r['result'] == 'walk')
  497 |         avg_pitches = np.mean([r['pitches'] for r in results])
  498 | 
  499 |         print(f"""
  500 |   {Colors.BOLD}╔══════════════════════════════════════════╗
  501 |   ║          ⚾  GAME SUMMARY  ⚾           ║
  502 |   ╠══════════════════════════════════════════╣{Colors.RESET}
  503 |   ║  At-Bats:    {total:3d}                         ║
  504 |   ║  {Colors.GREEN}Hits:        {hits:3d}{Colors.RESET}   (AVG: .{int(hits/max(total,1)*1000):03d})       ║
  505 |   ║  {Colors.RED}Outs:        {outs:3d}{Colors.RESET}                         ║
  506 |   ║  {Colors.MAGENTA}Home Runs:   {hrs:3d}{Colors.RESET}                         ║
  507 |   ║  {Colors.YELLOW}Strikeouts:  {ks:3d}{Colors.RESET}                         ║
  508 |   ║  {Colors.BLUE}Walks:       {walks:3d}{Colors.RESET}                         ║
  509 |   ║  Avg Pitches: {avg_pitches:.1f}                       ║
  510 |   {Colors.BOLD}╠══════════════════════════════════════════╣
  511 |   ║  Pitcher Wins: {self.pitcher_total_wins:3d}  |  Batter Wins: {self.batter_total_wins:3d}  ║
  512 |   ╚══════════════════════════════════════════╝{Colors.RESET}
  513 | """)
  514 | 
  515 | 
  516 | # ──────────────────────────────────────────────────────────────
  517 | #  메인 실행
  518 | # ──────────────────────────────────────────────────────────────
  519 | 
  520 | def main():
  521 |     parser = argparse.ArgumentParser(
  522 |         description='⚾ Baseball RL Interactive Game',
  523 |         formatter_class=argparse.RawDescriptionHelpFormatter,
  524 |         epilog="""
  525 | Examples:
  526 |   python game.py                         # AI vs AI 관전
  527 |   python game.py --role pitcher          # 유저가 투수
  528 |   python game.py --role batter           # 유저가 타자
  529 |   python game.py --checkpoint ckpt.pt    # 체크포인트 로드
  530 |   python game.py --at-bats 3             # 3타석 게임
  531 |         """
  532 |     )
  533 |     parser.add_argument(
  534 |         '--role', type=str, default='spectator',
  535 |         choices=['spectator', 'pitcher', 'batter'],
  536 |         help='유저 역할 (spectator/pitcher/batter)',
  537 |     )
  538 |     parser.add_argument(
  539 |         '--checkpoint', type=str, default=None,
  540 |         help='학습된 모델 체크포인트 경로',
  541 |     )
  542 |     parser.add_argument(
  543 |         '--at-bats', type=int, default=9,
  544 |         help='실행할 타석 수 (기본 9)',
  545 |     )
  546 |     parser.add_argument(
  547 |         '--delay', type=float, default=1.0,
  548 |         help='AI 행동 간 딜레이 (초, 관전 모드)',
  549 |     )
  550 | 
  551 |     args = parser.parse_args()
  552 | 
  553 |     game = BaseballGame(
  554 |         role=args.role,
  555 |         checkpoint_path=args.checkpoint,
  556 |         delay=args.delay,
  557 |     )
  558 | 
  559 |     try:
  560 |         game.run(n_at_bats=args.at_bats)
  561 |     except KeyboardInterrupt:
  562 |         print(f"\n\n  {Colors.DIM}게임이 중단되었습니다.{Colors.RESET}")
  563 |         game._print_game_summary([])
  564 | 
  565 | 
  566 | if __name__ == '__main__':
  567 |     main()
````
