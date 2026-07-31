"""
baseball_game_env.py — End-to-End Multi-Agent Gymnasium 환경

투수(Pitcher)와 타자(Batter)의 대결을 Gymnasium 호환 환경으로 래핑합니다.
각 에피소드는 1타석(최대 ~12구) 단위로 진행됩니다.

에피소드 흐름:
    1. 투수가 Action 출력 → PitcherMechanism이 궤적 시뮬레이션
    2. 궤적을 시간 스텝별로 나누어 타자에게 Observation 제공
    3. 타자가 스윙 여부/토크 결정
    4. 충돌 판정 → 결과(Strike/Ball/Foul/Hit/HR) 판정
    5. Zero-sum Reward 배분
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Optional, Tuple, Dict, Any

from envs.pitcher_mechanism import (
    PitcherMechanism,
    BallPhysics,
    PitchConfig,
    StrikeZone,
)
from envs.batter_mechanism import (
    BatterMechanism,
    BatModel,
    SwingConfig,
)


# ──────────────────────────────────────────────────────────────
#  Reward 상수
# ──────────────────────────────────────────────────────────────

REWARDS = {
    # 결과: (pitcher_reward, batter_reward)
    'called_strike':    (+1.0, -1.0),
    'swinging_strike':  (+1.5, -1.5),
    'ball':             (-1.0, +0.5),
    'foul':             (+0.3, -0.3),
    'out':              (+1.0, -1.0),
    'single':           (-2.0, +2.0),
    'extra_base':       (-3.0, +3.0),
    'home_run':         (-5.0, +5.0),
    'strikeout':        (+3.0, -3.0),   # 삼진 보너스
    'walk':             (-3.0, +3.0),   # 볼넷 보너스
}


# ──────────────────────────────────────────────────────────────
#  Multi-Agent 환경
# ──────────────────────────────────────────────────────────────

class BaseballGameEnv(gym.Env):
    """End-to-End Baseball Multi-Agent Gymnasium 환경.

    두 에이전트(Pitcher, Batter)가 교대로 행동하는 턴 기반 환경입니다.
    한 '투구'가 환경의 한 스텝에 해당합니다.

    Observation Space:
        Pitcher: [strikes, balls, prev_result, prev_plate_x, prev_plate_z, batter_stance] → Box(6)
        Batter:  [ball_pos(3), ball_vel(3), bat_pos(3), bat_vel(3), time_to_plate] → Box(13)

    Action Space:
        Pitcher: [v_release, θ_x, θ_z, ω_spin, a_axis] → Box(5)
        Batter:  [t_trigger, θ_yaw, θ_pitch, z_height] → Box(4)
    """

    metadata = {'render_modes': ['human', 'ansi'], 'render_fps': 30}

    def __init__(
        self,
        render_mode: Optional[str] = None,
        trajectory_substeps: int = 10,
    ):
        """
        Args:
            render_mode: 렌더링 모드 ('human', 'ansi', None)
            trajectory_substeps: 타자에게 제공할 궤적 관찰 시점 수
        """
        super().__init__()
        self.render_mode = render_mode
        self.trajectory_substeps = trajectory_substeps

        # 물리 엔진 초기화
        self.pitcher_mech = PitcherMechanism()
        self.batter_mech = BatterMechanism()
        self.strike_zone = StrikeZone()

        # ── Observation Spaces ──
        self.pitcher_obs_space = spaces.Box(
            low=np.array([0, 0, -1, -0.5, 0.0, 0], dtype=np.float32),
            high=np.array([2, 3, 5, 0.5, 1.5, 1], dtype=np.float32),
            dtype=np.float32,
        )
        self.batter_obs_space = spaces.Box(
            low=-np.ones(13, dtype=np.float32) * 100.0,
            high=np.ones(13, dtype=np.float32) * 100.0,
            dtype=np.float32,
        )

        # Gymnasium 호환을 위한 결합 space (실제로는 에이전트별 사용)
        self.observation_space = spaces.Dict({
            'pitcher': self.pitcher_obs_space,
            'batter': self.batter_obs_space,
        })

        # ── Action Spaces ──
        self.pitcher_action_space = spaces.Box(
            low=-np.ones(5, dtype=np.float32),
            high=np.ones(5, dtype=np.float32),
            dtype=np.float32,
        )
        self.batter_action_space = spaces.Box(
            low=-np.ones(4, dtype=np.float32),
            high=np.ones(4, dtype=np.float32),
            dtype=np.float32,
        )

        self.action_space = spaces.Dict({
            'pitcher': self.pitcher_action_space,
            'batter': self.batter_action_space,
        })

        # ── 게임 상태 ──
        self._reset_count()

        # ── 에피소드 데이터 수집 (Dashboard 연동) ──
        self.episode_data = []
        self.pitch_count = 0

    def _reset_count(self):
        """카운트를 초기화합니다."""
        self.strikes = 0
        self.balls = 0
        self.prev_result = 0   # 0=없음, 1=strike, 2=ball, 3=foul, 4=hit, 5=HR
        self.prev_plate_x = 0.0
        self.prev_plate_z = 0.75  # 존 중앙
        self.batter_stance = 0    # 0=우타, 1=좌타

    def _get_pitcher_obs(self) -> np.ndarray:
        """투수 관찰 벡터를 생성합니다."""
        return np.array([
            self.strikes,
            self.balls,
            self.prev_result,
            self.prev_plate_x,
            self.prev_plate_z,
            self.batter_stance,
        ], dtype=np.float32)

    def _get_batter_obs(
        self,
        ball_pos: np.ndarray,
        ball_vel: np.ndarray,
        bat_state: Optional[dict] = None,
        time_to_plate: float = 0.5,
    ) -> np.ndarray:
        """타자 관찰 벡터를 생성합니다."""
        if bat_state is None:
            bat_pos = np.zeros(3, dtype=np.float32)
            bat_vel = np.zeros(3, dtype=np.float32)
        else:
            bat_pos = bat_state['sweet_spot_position'].astype(np.float32)
            bat_vel = bat_state['sweet_spot_velocity'].astype(np.float32)

        return np.concatenate([
            ball_pos.astype(np.float32),
            ball_vel.astype(np.float32),
            bat_pos,
            bat_vel,
            [float(time_to_plate)],
        ]).astype(np.float32)

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[dict] = None,
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """환경을 초기화합니다.

        Returns:
            (observations, info)
        """
        super().reset(seed=seed)
        self._reset_count()
        self.episode_data = []
        self.pitch_count = 0

        # 타자 스탠스 랜덤
        if self.np_random is not None:
            self.batter_stance = int(self.np_random.integers(0, 2))
        else:
            self.batter_stance = np.random.randint(0, 2)

        obs = {
            'pitcher': self._get_pitcher_obs(),
            'batter': self._get_batter_obs(
                ball_pos=np.array([0.0, 18.44, 1.85]),
                ball_vel=np.array([0.0, 0.0, 0.0]),
                time_to_plate=0.5,
            ),
        }

        info = {
            'strikes': self.strikes,
            'balls': self.balls,
            'pitch_count': self.pitch_count,
        }

        return obs, info

    def step(
        self,
        action: Dict[str, np.ndarray],
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, float], bool, bool, Dict[str, Any]]:
        """한 투구 사이클을 실행합니다.

        Args:
            action: {'pitcher': (5,), 'batter': (4,)} 액션 딕셔너리

        Returns:
            (obs, rewards, terminated, truncated, info)
        """
        pitcher_action = action['pitcher']
        batter_action = action['batter']

        # ── 1. 투구 시뮬레이션 ──
        pitch_result = self.pitcher_mech.pitch(pitcher_action)
        trajectory = pitch_result['trajectory']
        plate_x = pitch_result['plate_x']
        plate_z = pitch_result['plate_z']
        flight_time = trajectory['flight_time']

        # ── 2. 타자 스윙 판정 ──
        # 타자의 스윙 시작 시간: 공이 홈플레이트 부근에 도달하기 ~0.15초 전
        swing_start_time = max(0.0, flight_time - 0.20)

        swing_result = self.batter_mech.swing_and_check(
            action=batter_action,
            ball_trajectory_positions=trajectory['positions'],
            ball_trajectory_velocities=trajectory['velocities'],
            ball_trajectory_times=trajectory['times'],
            swing_start_time=swing_start_time,
        )

        # ── 3. 결과 판정 ──
        pitch_outcome = self._judge_outcome(
            swing_result, plate_x, plate_z
        )

        # ── 4. Reward 계산 ──
        reward_key = pitch_outcome['reward_key']
        pitcher_reward, batter_reward = REWARDS[reward_key]
        rewards = {
            'pitcher': pitcher_reward,
            'batter': batter_reward,
        }

        # ── 5. 카운트 업데이트 ──
        terminated = False
        self.pitch_count += 1

        if reward_key in ('called_strike', 'swinging_strike'):
            self.strikes += 1
            self.prev_result = 1
            if self.strikes >= 3:
                # 삼진 보너스
                p_bonus, b_bonus = REWARDS['strikeout']
                rewards['pitcher'] += p_bonus
                rewards['batter'] += b_bonus
                terminated = True
        elif reward_key == 'ball':
            self.balls += 1
            self.prev_result = 2
            if self.balls >= 4:
                # 볼넷 보너스
                p_bonus, b_bonus = REWARDS['walk']
                rewards['pitcher'] += p_bonus
                rewards['batter'] += b_bonus
                terminated = True
        elif reward_key == 'foul':
            if self.strikes < 2:
                self.strikes += 1
            self.prev_result = 3
        elif reward_key in ('single', 'extra_base', 'home_run', 'out'):
            self.prev_result = 4 if reward_key != 'home_run' else 5
            terminated = True

        self.prev_plate_x = plate_x
        self.prev_plate_z = plate_z

        # 최대 투구 수 제한 (truncation)
        truncated = self.pitch_count >= 20

        # ── 6. 에피소드 데이터 수집 ──
        pitch_data = {
            'pitch_number': self.pitch_count,
            'plate_x': plate_x,
            'plate_z': plate_z,
            'arrival_speed_kmh': pitch_result['arrival_speed_kmh'],
            'spin_rate': pitch_result['params']['spin_rate_rpm'],
            'spin_axis': pitch_result['params']['spin_axis_angle'],
            'movement_x': pitch_result['movement_x'],
            'movement_z': pitch_result['movement_z'],
            'outcome': reward_key,
            'trajectory_positions': trajectory['positions'].tolist(),
            'strikes': self.strikes,
            'balls': self.balls,
        }

        if swing_result['result'] == 'hit' and swing_result['contact_info']:
            ci = swing_result['contact_info']
            pitch_data.update({
                'exit_speed_kmh': ci['exit_speed_kmh'],
                'launch_angle': ci['launch_angle'],
                'spray_angle': ci['spray_angle'],
                'sweet_spot_factor': ci['sweet_spot_factor'],
            })

        self.episode_data.append(pitch_data)

        # ── 7. 다음 관찰 ──
        # 타자에게는 공의 초기 상태를 다시 제공 (다음 투구 대기)
        obs = {
            'pitcher': self._get_pitcher_obs(),
            'batter': self._get_batter_obs(
                ball_pos=trajectory['positions'][0],
                ball_vel=trajectory['velocities'][0],
                time_to_plate=flight_time,
            ),
        }

        info = {
            'pitch_outcome': pitch_outcome,
            'pitch_data': pitch_data,
            'strikes': self.strikes,
            'balls': self.balls,
            'pitch_count': self.pitch_count,
            'episode_data': self.episode_data,
        }

        return obs, rewards, terminated, truncated, info

    def _judge_outcome(
        self,
        swing_result: dict,
        plate_x: float,
        plate_z: float,
    ) -> dict:
        """투구/타격 결과를 종합 판정합니다.

        Args:
            swing_result: BatterMechanism.swing_and_check() 결과
            plate_x: 홈플레이트 통과 x 좌표
            plate_z: 홈플레이트 통과 z 좌표

        Returns:
            dict:
                'reward_key': REWARDS 테이블 키
                'description': 결과 설명 문자열
                'is_strike_zone': 스트라이크존 내 여부
        """
        is_in_zone = self.strike_zone.is_strike(plate_x, plate_z)

        if swing_result['result'] == 'no_swing':
            # 방망이를 꺼내지 않음
            if is_in_zone:
                return {
                    'reward_key': 'called_strike',
                    'description': '보송 스트라이크 (Called Strike)',
                    'is_strike_zone': True,
                }
            else:
                return {
                    'reward_key': 'ball',
                    'description': '볼 (Ball)',
                    'is_strike_zone': False,
                }

        elif swing_result['result'] == 'swing_miss':
            # 헛스윙
            return {
                'reward_key': 'swinging_strike',
                'description': '헛스윙 (Swinging Strike)',
                'is_strike_zone': is_in_zone,
            }

        elif swing_result['result'] == 'hit':
            # 타격 성공 → 타구 분류
            contact_info = swing_result['contact_info']
            hit_type = self.batter_mech.classify_hit(contact_info)

            descriptions = {
                'foul': '파울 (Foul Ball)',
                'home_run': '홈런! (Home Run!) 🎆',
                'extra_base': '장타! (Extra Base Hit)',
                'single': '안타 (Single)',
                'out': '아웃 (Out)',
            }

            return {
                'reward_key': hit_type,
                'description': descriptions.get(hit_type, hit_type),
                'is_strike_zone': is_in_zone,
                'contact_info': contact_info,
            }

        return {
            'reward_key': 'ball',
            'description': '알 수 없는 결과',
            'is_strike_zone': is_in_zone,
        }

    def get_batter_trajectory_observations(
        self,
        trajectory: dict,
    ) -> list:
        """공 궤적을 시간 분할하여 타자 관찰 시퀀스를 생성합니다.

        LSTM 기반 타자 정책에 입력할 시계열 데이터를 생성합니다.

        Args:
            trajectory: PitcherMechanism.pitch()['trajectory'] 결과

        Returns:
            list of (observation, time) 튜플
        """
        positions = trajectory['positions']
        velocities = trajectory['velocities']
        times = trajectory['times']

        n = len(times)
        step = max(1, n // self.trajectory_substeps)
        indices = list(range(0, n, step))[:self.trajectory_substeps]

        observations = []
        for idx in indices:
            time_to_plate = times[-1] - times[idx]
            obs = self._get_batter_obs(
                ball_pos=positions[idx],
                ball_vel=velocities[idx],
                time_to_plate=time_to_plate,
            )
            observations.append((obs, times[idx]))

        return observations

    def render(self) -> Optional[str]:
        """환경 상태를 렌더링합니다."""
        if self.render_mode == 'ansi':
            return self._render_ansi()
        return None

    def _render_ansi(self) -> str:
        """ASCII 텍스트로 스트라이크존과 카운트를 표시합니다."""
        sz = self.strike_zone
        lines = []
        lines.append(f"  ⚾ Count: {self.balls}B - {self.strikes}S")
        lines.append(f"  {'─' * 25}")

        # 9분할 스트라이크존 (3×3)
        zone_width = 7
        for row in range(2, -1, -1):  # 상 → 하
            row_str = "  │"
            for col in range(3):
                cell = f" {'·':^{zone_width-2}} "
                # 마지막 투구 위치 표시
                loc = sz.zone_location(self.prev_plate_x, self.prev_plate_z)
                if loc == (col, row):
                    cell = f" {'●':^{zone_width-2}} "
                row_str += cell + "│"
            lines.append(row_str)
            if row > 0:
                lines.append(f"  │{'─' * zone_width}│{'─' * zone_width}│{'─' * zone_width}│")

        lines.append(f"  {'─' * 25}")

        if self.episode_data:
            last = self.episode_data[-1]
            lines.append(f"  Last: {last['outcome']} | "
                        f"{last['arrival_speed_kmh']:.0f}km/h")

        return "\n".join(lines)
