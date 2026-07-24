"""
dashboard.py — 실시간 학습 모니터링 대시보드 (Simulator Studio)

Dash + Plotly 기반 4-패널 대시보드:
    1. 3D Trajectory Viewer: 공 궤적, 마그누스 힘 벡터, 스윙 궤면
    2. Exit Dynamics Dashboard: Exit Velocity, Launch Angle, Spray Angle
    3. Strike Zone Heatmap: 투구 분포 + 타격 결과 오버레이
    4. Learning Progress Monitor: 승률, Reward, 버퍼 상태

JSON 파일 기반 학습 ↔ 대시보드 데이터 교환.
"""

import json
import os
import numpy as np
from datetime import datetime
from pathlib import Path

import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


# ──────────────────────────────────────────────────────────────
#  데이터 경로 설정
# ──────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data"
METRICS_FILE = DATA_DIR / "training_metrics.json"
PITCH_LOG_FILE = DATA_DIR / "pitch_log.json"

# 스트라이크존 좌표 (미터)
SZ_X_MIN, SZ_X_MAX = -0.2159, 0.2159
SZ_Z_MIN, SZ_Z_MAX = 0.45, 1.05


# ──────────────────────────────────────────────────────────────
#  데이터 로더
# ──────────────────────────────────────────────────────────────

def load_json(filepath: Path) -> list:
    """JSON 파일에서 데이터를 로드합니다."""
    if not filepath.exists():
        return []
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]
    except (json.JSONDecodeError, IOError):
        return []


def save_pitch_data(pitch_data: dict):
    """투구 데이터를 JSON 로그에 추가합니다.

    학습 루프에서 호출하여 대시보드와 데이터를 공유합니다.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_json(PITCH_LOG_FILE)
    existing.append(pitch_data)

    # 최근 5000개만 유지
    if len(existing) > 5000:
        existing = existing[-5000:]

    with open(PITCH_LOG_FILE, 'w') as f:
        json.dump(existing, f, default=str)


def save_training_metrics(metrics: dict):
    """학습 메트릭을 JSON 파일에 추가합니다.

    학습 루프에서 호출하여 대시보드와 데이터를 공유합니다.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_json(METRICS_FILE)
    metrics['timestamp'] = datetime.now().isoformat()
    existing.append(metrics)

    with open(METRICS_FILE, 'w') as f:
        json.dump(existing, f, default=str)


# ──────────────────────────────────────────────────────────────
#  차트 생성 함수
# ──────────────────────────────────────────────────────────────

def create_trajectory_3d(pitch_log: list) -> go.Figure:
    """3D 공 궤적 뷰어를 생성합니다.

    최근 N개의 투구 궤적을 3D 공간에 오버레이합니다.
    """
    fig = go.Figure()

    # 스트라이크존 3D 박스
    sz_x = [SZ_X_MIN, SZ_X_MAX, SZ_X_MAX, SZ_X_MIN, SZ_X_MIN]
    sz_z = [SZ_Z_MIN, SZ_Z_MIN, SZ_Z_MAX, SZ_Z_MAX, SZ_Z_MIN]
    sz_y = [0, 0, 0, 0, 0]

    fig.add_trace(go.Scatter3d(
        x=sz_x, y=sz_y, z=sz_z,
        mode='lines',
        line=dict(color='rgba(255, 100, 100, 0.8)', width=4),
        name='Strike Zone',
        showlegend=True,
    ))

    # 최근 투구 궤적 (최대 10개)
    recent_pitches = pitch_log[-10:] if len(pitch_log) > 10 else pitch_log

    color_map = {
        'called_strike': '#FF4444',
        'swinging_strike': '#FF8800',
        'ball': '#4488FF',
        'foul': '#FFAA00',
        'single': '#44FF44',
        'extra_base': '#44FFAA',
        'home_run': '#FF44FF',
        'out': '#888888',
    }

    for i, pitch in enumerate(recent_pitches):
        traj = pitch.get('trajectory_positions', [])
        if not traj or len(traj) < 2:
            continue

        traj = np.array(traj)
        outcome = pitch.get('outcome', 'ball')
        color = color_map.get(outcome, '#AAAAAA')
        speed = pitch.get('arrival_speed_kmh', 0)

        fig.add_trace(go.Scatter3d(
            x=traj[:, 0], y=traj[:, 1], z=traj[:, 2],
            mode='lines',
            line=dict(color=color, width=3),
            name=f"#{i+1} {outcome} ({speed:.0f}km/h)",
            opacity=0.6 + 0.4 * (i / max(len(recent_pitches) - 1, 1)),
        ))

        # 종착점 마커
        fig.add_trace(go.Scatter3d(
            x=[traj[-1, 0]], y=[traj[-1, 1]], z=[traj[-1, 2]],
            mode='markers',
            marker=dict(size=5, color=color, symbol='circle'),
            showlegend=False,
        ))

    fig.update_layout(
        title=dict(
            text='⚾ 3D Pitch Trajectory Viewer',
            font=dict(size=16, color='#E0E0E0'),
        ),
        scene=dict(
            xaxis=dict(title='X (m)', range=[-0.8, 0.8],
                       backgroundcolor='rgba(20,20,40,0.9)',
                       gridcolor='rgba(100,100,150,0.3)'),
            yaxis=dict(title='Y (m)', range=[-1, 20],
                       backgroundcolor='rgba(20,20,40,0.9)',
                       gridcolor='rgba(100,100,150,0.3)'),
            zaxis=dict(title='Z (m)', range=[-0.5, 3],
                       backgroundcolor='rgba(20,20,40,0.9)',
                       gridcolor='rgba(100,100,150,0.3)'),
            bgcolor='rgba(15,15,30,0.95)',
            camera=dict(eye=dict(x=1.5, y=-1.5, z=0.8)),
        ),
        paper_bgcolor='#0D1117',
        plot_bgcolor='#0D1117',
        font=dict(color='#C9D1D9'),
        legend=dict(
            bgcolor='rgba(30,30,50,0.8)',
            font=dict(size=10, color='#C9D1D9'),
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=500,
    )

    return fig


def create_exit_dynamics(pitch_log: list) -> go.Figure:
    """Exit Dynamics 대시보드를 생성합니다.

    Exit Velocity vs Launch Angle 스캐터 + 분포 히스토그램.
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Exit Velocity vs Launch Angle',
            'Exit Velocity Distribution',
            'Spray Chart',
            'Launch Angle Distribution',
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'histogram'}],
            [{'type': 'scatter'}, {'type': 'histogram'}],
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    # 타격 데이터만 필터링
    hits = [p for p in pitch_log if 'exit_speed_kmh' in p]

    if hits:
        exit_speeds = [h['exit_speed_kmh'] for h in hits]
        launch_angles = [h['launch_angle'] for h in hits]
        spray_angles = [h.get('spray_angle', 0) for h in hits]
        outcomes = [h.get('outcome', 'out') for h in hits]

        color_map = {
            'home_run': '#FF44FF',
            'extra_base': '#44FFAA',
            'single': '#44FF44',
            'out': '#888888',
            'foul': '#FFAA00',
        }
        colors = [color_map.get(o, '#AAAAAA') for o in outcomes]

        # 1. Exit Velocity vs Launch Angle
        fig.add_trace(go.Scatter(
            x=launch_angles, y=exit_speeds,
            mode='markers',
            marker=dict(color=colors, size=6, opacity=0.7),
            text=[f"{o}: {v:.0f}km/h @ {la:.1f}°"
                  for o, v, la in zip(outcomes, exit_speeds, launch_angles)],
            hoverinfo='text',
            showlegend=False,
        ), row=1, col=1)

        # HR 존 표시
        fig.add_shape(
            type='rect', x0=20, x1=40, y0=155, y1=200,
            line=dict(color='rgba(255,68,255,0.4)', dash='dash'),
            fillcolor='rgba(255,68,255,0.1)',
            row=1, col=1,
        )

        # 2. Exit Velocity 히스토그램
        fig.add_trace(go.Histogram(
            x=exit_speeds,
            nbinsx=20,
            marker_color='#58A6FF',
            opacity=0.7,
            showlegend=False,
        ), row=1, col=2)

        # 3. Spray Chart (극좌표 대신 XY scatter)
        # spray_angle을 기반으로 x, y 계산
        spray_x = [v * np.sin(np.radians(a)) for v, a in zip(exit_speeds, spray_angles)]
        spray_y = [v * np.cos(np.radians(a)) for v, a in zip(exit_speeds, spray_angles)]

        fig.add_trace(go.Scatter(
            x=spray_x, y=spray_y,
            mode='markers',
            marker=dict(color=colors, size=5, opacity=0.6),
            showlegend=False,
        ), row=2, col=1)

        # 파울 라인
        for angle in [-45, 45]:
            rad = np.radians(angle)
            fig.add_trace(go.Scatter(
                x=[0, 200 * np.sin(rad)], y=[0, 200 * np.cos(rad)],
                mode='lines',
                line=dict(color='rgba(255,255,100,0.3)', dash='dash'),
                showlegend=False,
            ), row=2, col=1)

        # 4. Launch Angle 히스토그램
        fig.add_trace(go.Histogram(
            x=launch_angles,
            nbinsx=20,
            marker_color='#3FB950',
            opacity=0.7,
            showlegend=False,
        ), row=2, col=2)

    fig.update_layout(
        title=dict(
            text='🏏 Exit Dynamics Dashboard',
            font=dict(size=16, color='#E0E0E0'),
        ),
        paper_bgcolor='#0D1117',
        plot_bgcolor='#161B22',
        font=dict(color='#C9D1D9', size=10),
        margin=dict(l=40, r=20, t=60, b=30),
        height=500,
    )

    # 축 스타일링
    for i in range(1, 3):
        for j in range(1, 3):
            fig.update_xaxes(
                gridcolor='rgba(100,100,150,0.2)',
                zerolinecolor='rgba(100,100,150,0.3)',
                row=i, col=j,
            )
            fig.update_yaxes(
                gridcolor='rgba(100,100,150,0.2)',
                zerolinecolor='rgba(100,100,150,0.3)',
                row=i, col=j,
            )

    return fig


def create_strike_zone_heatmap(pitch_log: list) -> go.Figure:
    """스트라이크존 히트맵을 생성합니다.

    투구 위치 분포 + 결과별 색상 오버레이.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Pitch Location Heatmap', 'Batting Result Map'),
        horizontal_spacing=0.08,
    )

    if pitch_log:
        plate_xs = [p['plate_x'] for p in pitch_log]
        plate_zs = [p['plate_z'] for p in pitch_log]
        outcomes = [p.get('outcome', 'ball') for p in pitch_log]

        # 1. 투구 위치 히트맵 (2D histogram)
        fig.add_trace(go.Histogram2d(
            x=plate_xs, y=plate_zs,
            nbinsx=20, nbinsy=20,
            colorscale=[
                [0, 'rgba(13,17,23,0)'],
                [0.25, 'rgba(30,50,120,0.5)'],
                [0.5, 'rgba(88,166,255,0.7)'],
                [0.75, 'rgba(255,165,0,0.8)'],
                [1.0, 'rgba(255,50,50,1.0)'],
            ],
            showscale=True,
            colorbar=dict(title='Count', x=0.45),
        ), row=1, col=1)

        # 스트라이크존 박스
        for col_idx in [1, 2]:
            fig.add_shape(
                type='rect',
                x0=SZ_X_MIN, x1=SZ_X_MAX,
                y0=SZ_Z_MIN, y1=SZ_Z_MAX,
                line=dict(color='rgba(255,100,100,0.8)', width=2),
                row=1, col=col_idx,
            )

        # 2. 결과별 스캐터
        color_map = {
            'called_strike': '#FF4444',
            'swinging_strike': '#FF8800',
            'ball': '#4488FF',
            'foul': '#FFAA00',
            'single': '#44FF44',
            'extra_base': '#44FFAA',
            'home_run': '#FF44FF',
            'out': '#888888',
        }

        for outcome_type, color in color_map.items():
            xs = [x for x, o in zip(plate_xs, outcomes) if o == outcome_type]
            zs = [z for z, o in zip(plate_zs, outcomes) if o == outcome_type]
            if xs:
                fig.add_trace(go.Scatter(
                    x=xs, y=zs,
                    mode='markers',
                    marker=dict(color=color, size=5, opacity=0.6),
                    name=outcome_type,
                ), row=1, col=2)

    fig.update_layout(
        title=dict(
            text='🎯 Strike Zone Analyzer',
            font=dict(size=16, color='#E0E0E0'),
        ),
        paper_bgcolor='#0D1117',
        plot_bgcolor='#161B22',
        font=dict(color='#C9D1D9', size=10),
        margin=dict(l=40, r=20, t=60, b=30),
        height=500,
        legend=dict(
            bgcolor='rgba(30,30,50,0.8)',
            font=dict(size=9),
        ),
    )

    # 축 라벨 및 범위
    for col_idx in [1, 2]:
        fig.update_xaxes(
            title_text='X (m)', range=[-0.5, 0.5],
            gridcolor='rgba(100,100,150,0.2)', row=1, col=col_idx,
        )
        fig.update_yaxes(
            title_text='Z (m)', range=[0.0, 1.5],
            gridcolor='rgba(100,100,150,0.2)', row=1, col=col_idx,
        )

    return fig


def create_learning_progress(metrics: list) -> go.Figure:
    """학습 진행 모니터를 생성합니다.

    Self-Play 승률, Reward, Buffer 상태를 추적합니다.
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Win Rate (Pitcher vs Batter)',
            'Average Reward',
            'Replay Buffer Status',
            'Special Events',
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    if metrics:
        episodes = list(range(1, len(metrics) + 1))

        # 1. 승률 그래프
        pitcher_wr = [m.get('pitcher_win_rate', 0.5) for m in metrics]
        batter_wr = [m.get('batter_win_rate', 0.5) for m in metrics]

        fig.add_trace(go.Scatter(
            x=episodes, y=pitcher_wr,
            mode='lines',
            name='Pitcher WR',
            line=dict(color='#FF6B6B', width=2),
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=episodes, y=batter_wr,
            mode='lines',
            name='Batter WR',
            line=dict(color='#4ECDC4', width=2),
        ), row=1, col=1)

        # 50% 라인
        fig.add_hline(y=0.5, line_dash='dash',
                      line_color='rgba(255,255,255,0.3)', row=1, col=1)

        # 2. 평균 Reward
        p_rewards = [m.get('pitcher_avg_reward', 0) for m in metrics]
        b_rewards = [m.get('batter_avg_reward', 0) for m in metrics]

        fig.add_trace(go.Scatter(
            x=episodes, y=p_rewards,
            mode='lines',
            name='Pitcher Reward',
            line=dict(color='#FF6B6B', width=2),
        ), row=1, col=2)

        fig.add_trace(go.Scatter(
            x=episodes, y=b_rewards,
            mode='lines',
            name='Batter Reward',
            line=dict(color='#4ECDC4', width=2),
        ), row=1, col=2)

        # 3. 버퍼 상태
        buffer_fill = [m.get('buffer_fill_ratio', 0) for m in metrics]

        fig.add_trace(go.Scatter(
            x=episodes, y=buffer_fill,
            mode='lines+markers',
            name='Buffer Fill',
            line=dict(color='#58A6FF', width=2),
            marker=dict(size=3),
            fill='tozeroy',
            fillcolor='rgba(88,166,255,0.1)',
        ), row=2, col=1)

        # 4. 특수 이벤트 (홈런/삼진 비율)
        hr_rates = [m.get('home_run_rate', 0) for m in metrics]
        k_rates = [m.get('strikeout_rate', 0) for m in metrics]

        fig.add_trace(go.Scatter(
            x=episodes, y=hr_rates,
            mode='lines',
            name='HR Rate',
            line=dict(color='#FF44FF', width=2),
        ), row=2, col=2)

        fig.add_trace(go.Scatter(
            x=episodes, y=k_rates,
            mode='lines',
            name='K Rate',
            line=dict(color='#FFAA00', width=2),
        ), row=2, col=2)

    fig.update_layout(
        title=dict(
            text='📈 Learning Progress Monitor',
            font=dict(size=16, color='#E0E0E0'),
        ),
        paper_bgcolor='#0D1117',
        plot_bgcolor='#161B22',
        font=dict(color='#C9D1D9', size=10),
        margin=dict(l=40, r=20, t=60, b=30),
        height=500,
        legend=dict(
            bgcolor='rgba(30,30,50,0.8)',
            font=dict(size=9),
            orientation='h',
            yanchor='bottom',
            y=-0.15,
        ),
    )

    for i in range(1, 3):
        for j in range(1, 3):
            fig.update_xaxes(
                gridcolor='rgba(100,100,150,0.2)', row=i, col=j,
            )
            fig.update_yaxes(
                gridcolor='rgba(100,100,150,0.2)', row=i, col=j,
            )

    return fig


# ──────────────────────────────────────────────────────────────
#  Dash 앱 생성
# ──────────────────────────────────────────────────────────────

def create_app() -> dash.Dash:
    """Dash 앱을 생성하고 레이아웃/콜백을 설정합니다."""

    app = dash.Dash(
        __name__,
        title='⚾ Baseball RL Simulator Studio',
        update_title='Updating...',
    )

    # ── 레이아웃 ──
    app.layout = html.Div(
        style={
            'backgroundColor': '#0D1117',
            'minHeight': '100vh',
            'fontFamily': "'Inter', 'Segoe UI', sans-serif",
            'padding': '20px',
        },
        children=[
            # 헤더
            html.Div(
                style={
                    'textAlign': 'center',
                    'marginBottom': '20px',
                    'padding': '20px',
                    'background': 'linear-gradient(135deg, #1a1a3e 0%, #0d1117 100%)',
                    'borderRadius': '12px',
                    'border': '1px solid rgba(88,166,255,0.2)',
                    'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                },
                children=[
                    html.H1(
                        '⚾ Baseball RL Simulator Studio',
                        style={
                            'color': '#E0E0E0',
                            'margin': '0',
                            'fontSize': '28px',
                            'fontWeight': '700',
                            'letterSpacing': '1px',
                        },
                    ),
                    html.P(
                        'End-to-End Reinforcement Learning Training Monitor',
                        style={
                            'color': '#8B949E',
                            'margin': '8px 0 0 0',
                            'fontSize': '14px',
                        },
                    ),
                    # 상태 배지
                    html.Div(
                        style={'marginTop': '12px', 'display': 'flex',
                               'justifyContent': 'center', 'gap': '16px'},
                        children=[
                            html.Span(id='badge-pitches',
                                      style=_badge_style('#58A6FF')),
                            html.Span(id='badge-hits',
                                      style=_badge_style('#3FB950')),
                            html.Span(id='badge-hrs',
                                      style=_badge_style('#FF44FF')),
                        ],
                    ),
                ],
            ),

            # 4패널 그리드
            html.Div(
                style={
                    'display': 'grid',
                    'gridTemplateColumns': '1fr 1fr',
                    'gap': '16px',
                },
                children=[
                    _panel('3d-trajectory', '⚾ 3D Trajectory Viewer'),
                    _panel('exit-dynamics', '🏏 Exit Dynamics'),
                    _panel('strike-zone', '🎯 Strike Zone Heatmap'),
                    _panel('learning-progress', '📈 Learning Progress'),
                ],
            ),

            # 자동 갱신 인터벌 (1초)
            dcc.Interval(
                id='auto-refresh',
                interval=1000,  # ms
                n_intervals=0,
            ),

            # 데이터 저장소
            dcc.Store(id='pitch-data-store'),
            dcc.Store(id='metrics-store'),
        ],
    )

    # ── 콜백: 데이터 로드 ──
    @app.callback(
        [
            Output('pitch-data-store', 'data'),
            Output('metrics-store', 'data'),
            Output('badge-pitches', 'children'),
            Output('badge-hits', 'children'),
            Output('badge-hrs', 'children'),
        ],
        [Input('auto-refresh', 'n_intervals')],
    )
    def load_data(n):
        pitch_log = load_json(PITCH_LOG_FILE)
        metrics = load_json(METRICS_FILE)

        n_pitches = len(pitch_log)
        n_hits = sum(1 for p in pitch_log if p.get('outcome') in
                     ('single', 'extra_base', 'home_run'))
        n_hrs = sum(1 for p in pitch_log if p.get('outcome') == 'home_run')

        return (
            pitch_log,
            metrics,
            f"🎯 {n_pitches} Pitches",
            f"🏏 {n_hits} Hits",
            f"💥 {n_hrs} HRs",
        )

    # ── 콜백: 차트 업데이트 ──
    @app.callback(
        Output('3d-trajectory', 'figure'),
        [Input('pitch-data-store', 'data')],
    )
    def update_trajectory(pitch_log):
        if not pitch_log:
            return create_trajectory_3d([])
        return create_trajectory_3d(pitch_log)

    @app.callback(
        Output('exit-dynamics', 'figure'),
        [Input('pitch-data-store', 'data')],
    )
    def update_exit_dynamics(pitch_log):
        if not pitch_log:
            return create_exit_dynamics([])
        return create_exit_dynamics(pitch_log)

    @app.callback(
        Output('strike-zone', 'figure'),
        [Input('pitch-data-store', 'data')],
    )
    def update_strike_zone(pitch_log):
        if not pitch_log:
            return create_strike_zone_heatmap([])
        return create_strike_zone_heatmap(pitch_log)

    @app.callback(
        Output('learning-progress', 'figure'),
        [Input('metrics-store', 'data')],
    )
    def update_learning(metrics):
        if not metrics:
            return create_learning_progress([])
        return create_learning_progress(metrics)

    return app


# ──────────────────────────────────────────────────────────────
#  UI 헬퍼
# ──────────────────────────────────────────────────────────────

def _badge_style(color: str) -> dict:
    """상태 배지 CSS."""
    return {
        'backgroundColor': f'rgba({_hex_to_rgb(color)}, 0.15)',
        'color': color,
        'padding': '4px 12px',
        'borderRadius': '20px',
        'fontSize': '12px',
        'fontWeight': '600',
        'border': f'1px solid rgba({_hex_to_rgb(color)}, 0.3)',
    }


def _hex_to_rgb(hex_color: str) -> str:
    """#RRGGBB → 'R,G,B' 변환."""
    h = hex_color.lstrip('#')
    return ','.join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))


def _panel(graph_id: str, title: str) -> html.Div:
    """대시보드 패널 컴포넌트."""
    return html.Div(
        style={
            'backgroundColor': '#161B22',
            'borderRadius': '12px',
            'border': '1px solid rgba(88,166,255,0.1)',
            'padding': '12px',
            'boxShadow': '0 2px 10px rgba(0,0,0,0.2)',
        },
        children=[
            dcc.Graph(
                id=graph_id,
                style={'height': '100%'},
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                },
            ),
        ],
    )


# ──────────────────────────────────────────────────────────────
#  메인 실행
# ──────────────────────────────────────────────────────────────

def main():
    """대시보드 서버를 시작합니다."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    app = create_app()
    print("⚾ Baseball RL Simulator Studio 시작...")
    print("   브라우저에서 http://127.0.0.1:8050 을 열어주세요")
    app.run(debug=True, host='0.0.0.0', port=8050)


if __name__ == '__main__':
    main()
