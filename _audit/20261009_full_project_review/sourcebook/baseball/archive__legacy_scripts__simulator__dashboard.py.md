# baseball/archive/legacy_scripts/simulator/dashboard.py

원본: [archive/legacy_scripts/simulator/dashboard.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_scripts/simulator/dashboard.py)

SHA256: `687f80eac5d9676fc526d50fe4bb82d954929622d52a63c8081200e8b4882d4a`

전체 751행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `load_json` | FunctionDef | 44 | 53 |
| `save_pitch_data` | FunctionDef | 56 | 70 |
| `save_training_metrics` | FunctionDef | 73 | 84 |
| `create_trajectory_3d` | FunctionDef | 91 | 180 |
| `create_exit_dynamics` | FunctionDef | 183 | 307 |
| `create_strike_zone_heatmap` | FunctionDef | 310 | 401 |
| `create_learning_progress` | FunctionDef | 404 | 523 |
| `create_app` | FunctionDef | 530 | 687 |
| `load_data` | FunctionDef | 633 | 648 |
| `update_trajectory` | FunctionDef | 655 | 658 |
| `update_exit_dynamics` | FunctionDef | 664 | 667 |
| `update_strike_zone` | FunctionDef | 673 | 676 |
| `update_learning` | FunctionDef | 682 | 685 |
| `_badge_style` | FunctionDef | 694 | 704 |
| `_hex_to_rgb` | FunctionDef | 707 | 710 |
| `_panel` | FunctionDef | 713 | 734 |
| `main` | FunctionDef | 741 | 747 |

## 전체 원문

````text
    1 | """
    2 | dashboard.py — 실시간 학습 모니터링 대시보드 (Simulator Studio)
    3 | 
    4 | Dash + Plotly 기반 4-패널 대시보드:
    5 |     1. 3D Trajectory Viewer: 공 궤적, 마그누스 힘 벡터, 스윙 궤면
    6 |     2. Exit Dynamics Dashboard: Exit Velocity, Launch Angle, Spray Angle
    7 |     3. Strike Zone Heatmap: 투구 분포 + 타격 결과 오버레이
    8 |     4. Learning Progress Monitor: 승률, Reward, 버퍼 상태
    9 | 
   10 | JSON 파일 기반 학습 ↔ 대시보드 데이터 교환.
   11 | """
   12 | 
   13 | import json
   14 | import os
   15 | import numpy as np
   16 | from datetime import datetime
   17 | from pathlib import Path
   18 | 
   19 | import dash
   20 | from dash import dcc, html, callback_context
   21 | from dash.dependencies import Input, Output, State
   22 | import plotly.graph_objects as go
   23 | import plotly.express as px
   24 | from plotly.subplots import make_subplots
   25 | 
   26 | 
   27 | # ──────────────────────────────────────────────────────────────
   28 | #  데이터 경로 설정
   29 | # ──────────────────────────────────────────────────────────────
   30 | 
   31 | DATA_DIR = Path(__file__).parent.parent / "data"
   32 | METRICS_FILE = DATA_DIR / "training_metrics.json"
   33 | PITCH_LOG_FILE = DATA_DIR / "pitch_log.json"
   34 | 
   35 | # 스트라이크존 좌표 (미터)
   36 | SZ_X_MIN, SZ_X_MAX = -0.2159, 0.2159
   37 | SZ_Z_MIN, SZ_Z_MAX = 0.45, 1.05
   38 | 
   39 | 
   40 | # ──────────────────────────────────────────────────────────────
   41 | #  데이터 로더
   42 | # ──────────────────────────────────────────────────────────────
   43 | 
   44 | def load_json(filepath: Path) -> list:
   45 |     """JSON 파일에서 데이터를 로드합니다."""
   46 |     if not filepath.exists():
   47 |         return []
   48 |     try:
   49 |         with open(filepath, 'r') as f:
   50 |             data = json.load(f)
   51 |         return data if isinstance(data, list) else [data]
   52 |     except (json.JSONDecodeError, IOError):
   53 |         return []
   54 | 
   55 | 
   56 | def save_pitch_data(pitch_data: dict):
   57 |     """투구 데이터를 JSON 로그에 추가합니다.
   58 | 
   59 |     학습 루프에서 호출하여 대시보드와 데이터를 공유합니다.
   60 |     """
   61 |     DATA_DIR.mkdir(parents=True, exist_ok=True)
   62 |     existing = load_json(PITCH_LOG_FILE)
   63 |     existing.append(pitch_data)
   64 | 
   65 |     # 최근 5000개만 유지
   66 |     if len(existing) > 5000:
   67 |         existing = existing[-5000:]
   68 | 
   69 |     with open(PITCH_LOG_FILE, 'w') as f:
   70 |         json.dump(existing, f, default=str)
   71 | 
   72 | 
   73 | def save_training_metrics(metrics: dict):
   74 |     """학습 메트릭을 JSON 파일에 추가합니다.
   75 | 
   76 |     학습 루프에서 호출하여 대시보드와 데이터를 공유합니다.
   77 |     """
   78 |     DATA_DIR.mkdir(parents=True, exist_ok=True)
   79 |     existing = load_json(METRICS_FILE)
   80 |     metrics['timestamp'] = datetime.now().isoformat()
   81 |     existing.append(metrics)
   82 | 
   83 |     with open(METRICS_FILE, 'w') as f:
   84 |         json.dump(existing, f, default=str)
   85 | 
   86 | 
   87 | # ──────────────────────────────────────────────────────────────
   88 | #  차트 생성 함수
   89 | # ──────────────────────────────────────────────────────────────
   90 | 
   91 | def create_trajectory_3d(pitch_log: list) -> go.Figure:
   92 |     """3D 공 궤적 뷰어를 생성합니다.
   93 | 
   94 |     최근 N개의 투구 궤적을 3D 공간에 오버레이합니다.
   95 |     """
   96 |     fig = go.Figure()
   97 | 
   98 |     # 스트라이크존 3D 박스
   99 |     sz_x = [SZ_X_MIN, SZ_X_MAX, SZ_X_MAX, SZ_X_MIN, SZ_X_MIN]
  100 |     sz_z = [SZ_Z_MIN, SZ_Z_MIN, SZ_Z_MAX, SZ_Z_MAX, SZ_Z_MIN]
  101 |     sz_y = [0, 0, 0, 0, 0]
  102 | 
  103 |     fig.add_trace(go.Scatter3d(
  104 |         x=sz_x, y=sz_y, z=sz_z,
  105 |         mode='lines',
  106 |         line=dict(color='rgba(255, 100, 100, 0.8)', width=4),
  107 |         name='Strike Zone',
  108 |         showlegend=True,
  109 |     ))
  110 | 
  111 |     # 최근 투구 궤적 (최대 10개)
  112 |     recent_pitches = pitch_log[-10:] if len(pitch_log) > 10 else pitch_log
  113 | 
  114 |     color_map = {
  115 |         'called_strike': '#FF4444',
  116 |         'swinging_strike': '#FF8800',
  117 |         'ball': '#4488FF',
  118 |         'foul': '#FFAA00',
  119 |         'single': '#44FF44',
  120 |         'extra_base': '#44FFAA',
  121 |         'home_run': '#FF44FF',
  122 |         'out': '#888888',
  123 |     }
  124 | 
  125 |     for i, pitch in enumerate(recent_pitches):
  126 |         traj = pitch.get('trajectory_positions', [])
  127 |         if not traj or len(traj) < 2:
  128 |             continue
  129 | 
  130 |         traj = np.array(traj)
  131 |         outcome = pitch.get('outcome', 'ball')
  132 |         color = color_map.get(outcome, '#AAAAAA')
  133 |         speed = pitch.get('arrival_speed_kmh', 0)
  134 | 
  135 |         fig.add_trace(go.Scatter3d(
  136 |             x=traj[:, 0], y=traj[:, 1], z=traj[:, 2],
  137 |             mode='lines',
  138 |             line=dict(color=color, width=3),
  139 |             name=f"#{i+1} {outcome} ({speed:.0f}km/h)",
  140 |             opacity=0.6 + 0.4 * (i / max(len(recent_pitches) - 1, 1)),
  141 |         ))
  142 | 
  143 |         # 종착점 마커
  144 |         fig.add_trace(go.Scatter3d(
  145 |             x=[traj[-1, 0]], y=[traj[-1, 1]], z=[traj[-1, 2]],
  146 |             mode='markers',
  147 |             marker=dict(size=5, color=color, symbol='circle'),
  148 |             showlegend=False,
  149 |         ))
  150 | 
  151 |     fig.update_layout(
  152 |         title=dict(
  153 |             text='⚾ 3D Pitch Trajectory Viewer',
  154 |             font=dict(size=16, color='#E0E0E0'),
  155 |         ),
  156 |         scene=dict(
  157 |             xaxis=dict(title='X (m)', range=[-0.8, 0.8],
  158 |                        backgroundcolor='rgba(20,20,40,0.9)',
  159 |                        gridcolor='rgba(100,100,150,0.3)'),
  160 |             yaxis=dict(title='Y (m)', range=[-1, 20],
  161 |                        backgroundcolor='rgba(20,20,40,0.9)',
  162 |                        gridcolor='rgba(100,100,150,0.3)'),
  163 |             zaxis=dict(title='Z (m)', range=[-0.5, 3],
  164 |                        backgroundcolor='rgba(20,20,40,0.9)',
  165 |                        gridcolor='rgba(100,100,150,0.3)'),
  166 |             bgcolor='rgba(15,15,30,0.95)',
  167 |             camera=dict(eye=dict(x=1.5, y=-1.5, z=0.8)),
  168 |         ),
  169 |         paper_bgcolor='#0D1117',
  170 |         plot_bgcolor='#0D1117',
  171 |         font=dict(color='#C9D1D9'),
  172 |         legend=dict(
  173 |             bgcolor='rgba(30,30,50,0.8)',
  174 |             font=dict(size=10, color='#C9D1D9'),
  175 |         ),
  176 |         margin=dict(l=0, r=0, t=40, b=0),
  177 |         height=500,
  178 |     )
  179 | 
  180 |     return fig
  181 | 
  182 | 
  183 | def create_exit_dynamics(pitch_log: list) -> go.Figure:
  184 |     """Exit Dynamics 대시보드를 생성합니다.
  185 | 
  186 |     Exit Velocity vs Launch Angle 스캐터 + 분포 히스토그램.
  187 |     """
  188 |     fig = make_subplots(
  189 |         rows=2, cols=2,
  190 |         subplot_titles=(
  191 |             'Exit Velocity vs Launch Angle',
  192 |             'Exit Velocity Distribution',
  193 |             'Spray Chart',
  194 |             'Launch Angle Distribution',
  195 |         ),
  196 |         specs=[
  197 |             [{'type': 'scatter'}, {'type': 'histogram'}],
  198 |             [{'type': 'scatter'}, {'type': 'histogram'}],
  199 |         ],
  200 |         vertical_spacing=0.12,
  201 |         horizontal_spacing=0.08,
  202 |     )
  203 | 
  204 |     # 타격 데이터만 필터링
  205 |     hits = [p for p in pitch_log if 'exit_speed_kmh' in p]
  206 | 
  207 |     if hits:
  208 |         exit_speeds = [h['exit_speed_kmh'] for h in hits]
  209 |         launch_angles = [h['launch_angle'] for h in hits]
  210 |         spray_angles = [h.get('spray_angle', 0) for h in hits]
  211 |         outcomes = [h.get('outcome', 'out') for h in hits]
  212 | 
  213 |         color_map = {
  214 |             'home_run': '#FF44FF',
  215 |             'extra_base': '#44FFAA',
  216 |             'single': '#44FF44',
  217 |             'out': '#888888',
  218 |             'foul': '#FFAA00',
  219 |         }
  220 |         colors = [color_map.get(o, '#AAAAAA') for o in outcomes]
  221 | 
  222 |         # 1. Exit Velocity vs Launch Angle
  223 |         fig.add_trace(go.Scatter(
  224 |             x=launch_angles, y=exit_speeds,
  225 |             mode='markers',
  226 |             marker=dict(color=colors, size=6, opacity=0.7),
  227 |             text=[f"{o}: {v:.0f}km/h @ {la:.1f}°"
  228 |                   for o, v, la in zip(outcomes, exit_speeds, launch_angles)],
  229 |             hoverinfo='text',
  230 |             showlegend=False,
  231 |         ), row=1, col=1)
  232 | 
  233 |         # HR 존 표시
  234 |         fig.add_shape(
  235 |             type='rect', x0=20, x1=40, y0=155, y1=200,
  236 |             line=dict(color='rgba(255,68,255,0.4)', dash='dash'),
  237 |             fillcolor='rgba(255,68,255,0.1)',
  238 |             row=1, col=1,
  239 |         )
  240 | 
  241 |         # 2. Exit Velocity 히스토그램
  242 |         fig.add_trace(go.Histogram(
  243 |             x=exit_speeds,
  244 |             nbinsx=20,
  245 |             marker_color='#58A6FF',
  246 |             opacity=0.7,
  247 |             showlegend=False,
  248 |         ), row=1, col=2)
  249 | 
  250 |         # 3. Spray Chart (극좌표 대신 XY scatter)
  251 |         # spray_angle을 기반으로 x, y 계산
  252 |         spray_x = [v * np.sin(np.radians(a)) for v, a in zip(exit_speeds, spray_angles)]
  253 |         spray_y = [v * np.cos(np.radians(a)) for v, a in zip(exit_speeds, spray_angles)]
  254 | 
  255 |         fig.add_trace(go.Scatter(
  256 |             x=spray_x, y=spray_y,
  257 |             mode='markers',
  258 |             marker=dict(color=colors, size=5, opacity=0.6),
  259 |             showlegend=False,
  260 |         ), row=2, col=1)
  261 | 
  262 |         # 파울 라인
  263 |         for angle in [-45, 45]:
  264 |             rad = np.radians(angle)
  265 |             fig.add_trace(go.Scatter(
  266 |                 x=[0, 200 * np.sin(rad)], y=[0, 200 * np.cos(rad)],
  267 |                 mode='lines',
  268 |                 line=dict(color='rgba(255,255,100,0.3)', dash='dash'),
  269 |                 showlegend=False,
  270 |             ), row=2, col=1)
  271 | 
  272 |         # 4. Launch Angle 히스토그램
  273 |         fig.add_trace(go.Histogram(
  274 |             x=launch_angles,
  275 |             nbinsx=20,
  276 |             marker_color='#3FB950',
  277 |             opacity=0.7,
  278 |             showlegend=False,
  279 |         ), row=2, col=2)
  280 | 
  281 |     fig.update_layout(
  282 |         title=dict(
  283 |             text='🏏 Exit Dynamics Dashboard',
  284 |             font=dict(size=16, color='#E0E0E0'),
  285 |         ),
  286 |         paper_bgcolor='#0D1117',
  287 |         plot_bgcolor='#161B22',
  288 |         font=dict(color='#C9D1D9', size=10),
  289 |         margin=dict(l=40, r=20, t=60, b=30),
  290 |         height=500,
  291 |     )
  292 | 
  293 |     # 축 스타일링
  294 |     for i in range(1, 3):
  295 |         for j in range(1, 3):
  296 |             fig.update_xaxes(
  297 |                 gridcolor='rgba(100,100,150,0.2)',
  298 |                 zerolinecolor='rgba(100,100,150,0.3)',
  299 |                 row=i, col=j,
  300 |             )
  301 |             fig.update_yaxes(
  302 |                 gridcolor='rgba(100,100,150,0.2)',
  303 |                 zerolinecolor='rgba(100,100,150,0.3)',
  304 |                 row=i, col=j,
  305 |             )
  306 | 
  307 |     return fig
  308 | 
  309 | 
  310 | def create_strike_zone_heatmap(pitch_log: list) -> go.Figure:
  311 |     """스트라이크존 히트맵을 생성합니다.
  312 | 
  313 |     투구 위치 분포 + 결과별 색상 오버레이.
  314 |     """
  315 |     fig = make_subplots(
  316 |         rows=1, cols=2,
  317 |         subplot_titles=('Pitch Location Heatmap', 'Batting Result Map'),
  318 |         horizontal_spacing=0.08,
  319 |     )
  320 | 
  321 |     if pitch_log:
  322 |         plate_xs = [p['plate_x'] for p in pitch_log]
  323 |         plate_zs = [p['plate_z'] for p in pitch_log]
  324 |         outcomes = [p.get('outcome', 'ball') for p in pitch_log]
  325 | 
  326 |         # 1. 투구 위치 히트맵 (2D histogram)
  327 |         fig.add_trace(go.Histogram2d(
  328 |             x=plate_xs, y=plate_zs,
  329 |             nbinsx=20, nbinsy=20,
  330 |             colorscale=[
  331 |                 [0, 'rgba(13,17,23,0)'],
  332 |                 [0.25, 'rgba(30,50,120,0.5)'],
  333 |                 [0.5, 'rgba(88,166,255,0.7)'],
  334 |                 [0.75, 'rgba(255,165,0,0.8)'],
  335 |                 [1.0, 'rgba(255,50,50,1.0)'],
  336 |             ],
  337 |             showscale=True,
  338 |             colorbar=dict(title='Count', x=0.45),
  339 |         ), row=1, col=1)
  340 | 
  341 |         # 스트라이크존 박스
  342 |         for col_idx in [1, 2]:
  343 |             fig.add_shape(
  344 |                 type='rect',
  345 |                 x0=SZ_X_MIN, x1=SZ_X_MAX,
  346 |                 y0=SZ_Z_MIN, y1=SZ_Z_MAX,
  347 |                 line=dict(color='rgba(255,100,100,0.8)', width=2),
  348 |                 row=1, col=col_idx,
  349 |             )
  350 | 
  351 |         # 2. 결과별 스캐터
  352 |         color_map = {
  353 |             'called_strike': '#FF4444',
  354 |             'swinging_strike': '#FF8800',
  355 |             'ball': '#4488FF',
  356 |             'foul': '#FFAA00',
  357 |             'single': '#44FF44',
  358 |             'extra_base': '#44FFAA',
  359 |             'home_run': '#FF44FF',
  360 |             'out': '#888888',
  361 |         }
  362 | 
  363 |         for outcome_type, color in color_map.items():
  364 |             xs = [x for x, o in zip(plate_xs, outcomes) if o == outcome_type]
  365 |             zs = [z for z, o in zip(plate_zs, outcomes) if o == outcome_type]
  366 |             if xs:
  367 |                 fig.add_trace(go.Scatter(
  368 |                     x=xs, y=zs,
  369 |                     mode='markers',
  370 |                     marker=dict(color=color, size=5, opacity=0.6),
  371 |                     name=outcome_type,
  372 |                 ), row=1, col=2)
  373 | 
  374 |     fig.update_layout(
  375 |         title=dict(
  376 |             text='🎯 Strike Zone Analyzer',
  377 |             font=dict(size=16, color='#E0E0E0'),
  378 |         ),
  379 |         paper_bgcolor='#0D1117',
  380 |         plot_bgcolor='#161B22',
  381 |         font=dict(color='#C9D1D9', size=10),
  382 |         margin=dict(l=40, r=20, t=60, b=30),
  383 |         height=500,
  384 |         legend=dict(
  385 |             bgcolor='rgba(30,30,50,0.8)',
  386 |             font=dict(size=9),
  387 |         ),
  388 |     )
  389 | 
  390 |     # 축 라벨 및 범위
  391 |     for col_idx in [1, 2]:
  392 |         fig.update_xaxes(
  393 |             title_text='X (m)', range=[-0.5, 0.5],
  394 |             gridcolor='rgba(100,100,150,0.2)', row=1, col=col_idx,
  395 |         )
  396 |         fig.update_yaxes(
  397 |             title_text='Z (m)', range=[0.0, 1.5],
  398 |             gridcolor='rgba(100,100,150,0.2)', row=1, col=col_idx,
  399 |         )
  400 | 
  401 |     return fig
  402 | 
  403 | 
  404 | def create_learning_progress(metrics: list) -> go.Figure:
  405 |     """학습 진행 모니터를 생성합니다.
  406 | 
  407 |     Self-Play 승률, Reward, Buffer 상태를 추적합니다.
  408 |     """
  409 |     fig = make_subplots(
  410 |         rows=2, cols=2,
  411 |         subplot_titles=(
  412 |             'Win Rate (Pitcher vs Batter)',
  413 |             'Average Reward',
  414 |             'Replay Buffer Status',
  415 |             'Special Events',
  416 |         ),
  417 |         vertical_spacing=0.12,
  418 |         horizontal_spacing=0.08,
  419 |     )
  420 | 
  421 |     if metrics:
  422 |         episodes = list(range(1, len(metrics) + 1))
  423 | 
  424 |         # 1. 승률 그래프
  425 |         pitcher_wr = [m.get('pitcher_win_rate', 0.5) for m in metrics]
  426 |         batter_wr = [m.get('batter_win_rate', 0.5) for m in metrics]
  427 | 
  428 |         fig.add_trace(go.Scatter(
  429 |             x=episodes, y=pitcher_wr,
  430 |             mode='lines',
  431 |             name='Pitcher WR',
  432 |             line=dict(color='#FF6B6B', width=2),
  433 |         ), row=1, col=1)
  434 | 
  435 |         fig.add_trace(go.Scatter(
  436 |             x=episodes, y=batter_wr,
  437 |             mode='lines',
  438 |             name='Batter WR',
  439 |             line=dict(color='#4ECDC4', width=2),
  440 |         ), row=1, col=1)
  441 | 
  442 |         # 50% 라인
  443 |         fig.add_hline(y=0.5, line_dash='dash',
  444 |                       line_color='rgba(255,255,255,0.3)', row=1, col=1)
  445 | 
  446 |         # 2. 평균 Reward
  447 |         p_rewards = [m.get('pitcher_avg_reward', 0) for m in metrics]
  448 |         b_rewards = [m.get('batter_avg_reward', 0) for m in metrics]
  449 | 
  450 |         fig.add_trace(go.Scatter(
  451 |             x=episodes, y=p_rewards,
  452 |             mode='lines',
  453 |             name='Pitcher Reward',
  454 |             line=dict(color='#FF6B6B', width=2),
  455 |         ), row=1, col=2)
  456 | 
  457 |         fig.add_trace(go.Scatter(
  458 |             x=episodes, y=b_rewards,
  459 |             mode='lines',
  460 |             name='Batter Reward',
  461 |             line=dict(color='#4ECDC4', width=2),
  462 |         ), row=1, col=2)
  463 | 
  464 |         # 3. 버퍼 상태
  465 |         buffer_fill = [m.get('buffer_fill_ratio', 0) for m in metrics]
  466 | 
  467 |         fig.add_trace(go.Scatter(
  468 |             x=episodes, y=buffer_fill,
  469 |             mode='lines+markers',
  470 |             name='Buffer Fill',
  471 |             line=dict(color='#58A6FF', width=2),
  472 |             marker=dict(size=3),
  473 |             fill='tozeroy',
  474 |             fillcolor='rgba(88,166,255,0.1)',
  475 |         ), row=2, col=1)
  476 | 
  477 |         # 4. 특수 이벤트 (홈런/삼진 비율)
  478 |         hr_rates = [m.get('home_run_rate', 0) for m in metrics]
  479 |         k_rates = [m.get('strikeout_rate', 0) for m in metrics]
  480 | 
  481 |         fig.add_trace(go.Scatter(
  482 |             x=episodes, y=hr_rates,
  483 |             mode='lines',
  484 |             name='HR Rate',
  485 |             line=dict(color='#FF44FF', width=2),
  486 |         ), row=2, col=2)
  487 | 
  488 |         fig.add_trace(go.Scatter(
  489 |             x=episodes, y=k_rates,
  490 |             mode='lines',
  491 |             name='K Rate',
  492 |             line=dict(color='#FFAA00', width=2),
  493 |         ), row=2, col=2)
  494 | 
  495 |     fig.update_layout(
  496 |         title=dict(
  497 |             text='📈 Learning Progress Monitor',
  498 |             font=dict(size=16, color='#E0E0E0'),
  499 |         ),
  500 |         paper_bgcolor='#0D1117',
  501 |         plot_bgcolor='#161B22',
  502 |         font=dict(color='#C9D1D9', size=10),
  503 |         margin=dict(l=40, r=20, t=60, b=30),
  504 |         height=500,
  505 |         legend=dict(
  506 |             bgcolor='rgba(30,30,50,0.8)',
  507 |             font=dict(size=9),
  508 |             orientation='h',
  509 |             yanchor='bottom',
  510 |             y=-0.15,
  511 |         ),
  512 |     )
  513 | 
  514 |     for i in range(1, 3):
  515 |         for j in range(1, 3):
  516 |             fig.update_xaxes(
  517 |                 gridcolor='rgba(100,100,150,0.2)', row=i, col=j,
  518 |             )
  519 |             fig.update_yaxes(
  520 |                 gridcolor='rgba(100,100,150,0.2)', row=i, col=j,
  521 |             )
  522 | 
  523 |     return fig
  524 | 
  525 | 
  526 | # ──────────────────────────────────────────────────────────────
  527 | #  Dash 앱 생성
  528 | # ──────────────────────────────────────────────────────────────
  529 | 
  530 | def create_app() -> dash.Dash:
  531 |     """Dash 앱을 생성하고 레이아웃/콜백을 설정합니다."""
  532 | 
  533 |     app = dash.Dash(
  534 |         __name__,
  535 |         title='⚾ Baseball RL Simulator Studio',
  536 |         update_title='Updating...',
  537 |     )
  538 | 
  539 |     # ── 레이아웃 ──
  540 |     app.layout = html.Div(
  541 |         style={
  542 |             'backgroundColor': '#0D1117',
  543 |             'minHeight': '100vh',
  544 |             'fontFamily': "'Inter', 'Segoe UI', sans-serif",
  545 |             'padding': '20px',
  546 |         },
  547 |         children=[
  548 |             # 헤더
  549 |             html.Div(
  550 |                 style={
  551 |                     'textAlign': 'center',
  552 |                     'marginBottom': '20px',
  553 |                     'padding': '20px',
  554 |                     'background': 'linear-gradient(135deg, #1a1a3e 0%, #0d1117 100%)',
  555 |                     'borderRadius': '12px',
  556 |                     'border': '1px solid rgba(88,166,255,0.2)',
  557 |                     'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
  558 |                 },
  559 |                 children=[
  560 |                     html.H1(
  561 |                         '⚾ Baseball RL Simulator Studio',
  562 |                         style={
  563 |                             'color': '#E0E0E0',
  564 |                             'margin': '0',
  565 |                             'fontSize': '28px',
  566 |                             'fontWeight': '700',
  567 |                             'letterSpacing': '1px',
  568 |                         },
  569 |                     ),
  570 |                     html.P(
  571 |                         'End-to-End Reinforcement Learning Training Monitor',
  572 |                         style={
  573 |                             'color': '#8B949E',
  574 |                             'margin': '8px 0 0 0',
  575 |                             'fontSize': '14px',
  576 |                         },
  577 |                     ),
  578 |                     # 상태 배지
  579 |                     html.Div(
  580 |                         style={'marginTop': '12px', 'display': 'flex',
  581 |                                'justifyContent': 'center', 'gap': '16px'},
  582 |                         children=[
  583 |                             html.Span(id='badge-pitches',
  584 |                                       style=_badge_style('#58A6FF')),
  585 |                             html.Span(id='badge-hits',
  586 |                                       style=_badge_style('#3FB950')),
  587 |                             html.Span(id='badge-hrs',
  588 |                                       style=_badge_style('#FF44FF')),
  589 |                         ],
  590 |                     ),
  591 |                 ],
  592 |             ),
  593 | 
  594 |             # 4패널 그리드
  595 |             html.Div(
  596 |                 style={
  597 |                     'display': 'grid',
  598 |                     'gridTemplateColumns': '1fr 1fr',
  599 |                     'gap': '16px',
  600 |                 },
  601 |                 children=[
  602 |                     _panel('3d-trajectory', '⚾ 3D Trajectory Viewer'),
  603 |                     _panel('exit-dynamics', '🏏 Exit Dynamics'),
  604 |                     _panel('strike-zone', '🎯 Strike Zone Heatmap'),
  605 |                     _panel('learning-progress', '📈 Learning Progress'),
  606 |                 ],
  607 |             ),
  608 | 
  609 |             # 자동 갱신 인터벌 (1초)
  610 |             dcc.Interval(
  611 |                 id='auto-refresh',
  612 |                 interval=1000,  # ms
  613 |                 n_intervals=0,
  614 |             ),
  615 | 
  616 |             # 데이터 저장소
  617 |             dcc.Store(id='pitch-data-store'),
  618 |             dcc.Store(id='metrics-store'),
  619 |         ],
  620 |     )
  621 | 
  622 |     # ── 콜백: 데이터 로드 ──
  623 |     @app.callback(
  624 |         [
  625 |             Output('pitch-data-store', 'data'),
  626 |             Output('metrics-store', 'data'),
  627 |             Output('badge-pitches', 'children'),
  628 |             Output('badge-hits', 'children'),
  629 |             Output('badge-hrs', 'children'),
  630 |         ],
  631 |         [Input('auto-refresh', 'n_intervals')],
  632 |     )
  633 |     def load_data(n):
  634 |         pitch_log = load_json(PITCH_LOG_FILE)
  635 |         metrics = load_json(METRICS_FILE)
  636 | 
  637 |         n_pitches = len(pitch_log)
  638 |         n_hits = sum(1 for p in pitch_log if p.get('outcome') in
  639 |                      ('single', 'extra_base', 'home_run'))
  640 |         n_hrs = sum(1 for p in pitch_log if p.get('outcome') == 'home_run')
  641 | 
  642 |         return (
  643 |             pitch_log,
  644 |             metrics,
  645 |             f"🎯 {n_pitches} Pitches",
  646 |             f"🏏 {n_hits} Hits",
  647 |             f"💥 {n_hrs} HRs",
  648 |         )
  649 | 
  650 |     # ── 콜백: 차트 업데이트 ──
  651 |     @app.callback(
  652 |         Output('3d-trajectory', 'figure'),
  653 |         [Input('pitch-data-store', 'data')],
  654 |     )
  655 |     def update_trajectory(pitch_log):
  656 |         if not pitch_log:
  657 |             return create_trajectory_3d([])
  658 |         return create_trajectory_3d(pitch_log)
  659 | 
  660 |     @app.callback(
  661 |         Output('exit-dynamics', 'figure'),
  662 |         [Input('pitch-data-store', 'data')],
  663 |     )
  664 |     def update_exit_dynamics(pitch_log):
  665 |         if not pitch_log:
  666 |             return create_exit_dynamics([])
  667 |         return create_exit_dynamics(pitch_log)
  668 | 
  669 |     @app.callback(
  670 |         Output('strike-zone', 'figure'),
  671 |         [Input('pitch-data-store', 'data')],
  672 |     )
  673 |     def update_strike_zone(pitch_log):
  674 |         if not pitch_log:
  675 |             return create_strike_zone_heatmap([])
  676 |         return create_strike_zone_heatmap(pitch_log)
  677 | 
  678 |     @app.callback(
  679 |         Output('learning-progress', 'figure'),
  680 |         [Input('metrics-store', 'data')],
  681 |     )
  682 |     def update_learning(metrics):
  683 |         if not metrics:
  684 |             return create_learning_progress([])
  685 |         return create_learning_progress(metrics)
  686 | 
  687 |     return app
  688 | 
  689 | 
  690 | # ──────────────────────────────────────────────────────────────
  691 | #  UI 헬퍼
  692 | # ──────────────────────────────────────────────────────────────
  693 | 
  694 | def _badge_style(color: str) -> dict:
  695 |     """상태 배지 CSS."""
  696 |     return {
  697 |         'backgroundColor': f'rgba({_hex_to_rgb(color)}, 0.15)',
  698 |         'color': color,
  699 |         'padding': '4px 12px',
  700 |         'borderRadius': '20px',
  701 |         'fontSize': '12px',
  702 |         'fontWeight': '600',
  703 |         'border': f'1px solid rgba({_hex_to_rgb(color)}, 0.3)',
  704 |     }
  705 | 
  706 | 
  707 | def _hex_to_rgb(hex_color: str) -> str:
  708 |     """#RRGGBB → 'R,G,B' 변환."""
  709 |     h = hex_color.lstrip('#')
  710 |     return ','.join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))
  711 | 
  712 | 
  713 | def _panel(graph_id: str, title: str) -> html.Div:
  714 |     """대시보드 패널 컴포넌트."""
  715 |     return html.Div(
  716 |         style={
  717 |             'backgroundColor': '#161B22',
  718 |             'borderRadius': '12px',
  719 |             'border': '1px solid rgba(88,166,255,0.1)',
  720 |             'padding': '12px',
  721 |             'boxShadow': '0 2px 10px rgba(0,0,0,0.2)',
  722 |         },
  723 |         children=[
  724 |             dcc.Graph(
  725 |                 id=graph_id,
  726 |                 style={'height': '100%'},
  727 |                 config={
  728 |                     'displayModeBar': True,
  729 |                     'displaylogo': False,
  730 |                     'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
  731 |                 },
  732 |             ),
  733 |         ],
  734 |     )
  735 | 
  736 | 
  737 | # ──────────────────────────────────────────────────────────────
  738 | #  메인 실행
  739 | # ──────────────────────────────────────────────────────────────
  740 | 
  741 | def main():
  742 |     """대시보드 서버를 시작합니다."""
  743 |     DATA_DIR.mkdir(parents=True, exist_ok=True)
  744 |     app = create_app()
  745 |     print("⚾ Baseball RL Simulator Studio 시작...")
  746 |     print("   브라우저에서 http://127.0.0.1:8050 을 열어주세요")
  747 |     app.run(debug=True, host='0.0.0.0', port=8050)
  748 | 
  749 | 
  750 | if __name__ == '__main__':
  751 |     main()
````
