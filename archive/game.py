"""
game.py — 대화형 Playable 게임 메인 엔진

학습된 모델(체크포인트)을 로딩하여 유저가 투수 또는 타자로 플레이할 수 있는
터미널 기반 인터랙티브 게임을 제공합니다.

사용법:
    python game.py                    # AI vs AI 관전 모드
    python game.py --role pitcher     # 유저가 투수로 플레이
    python game.py --role batter      # 유저가 타자로 플레이
    python game.py --checkpoint path  # 체크포인트 로드
"""

import argparse
import sys
import time
import numpy as np
from pathlib import Path
from typing import Optional

import torch

from envs.baseball_game_env import BaseballGameEnv
from training.networks import PitcherAgent, BatterAgent, get_device


# ──────────────────────────────────────────────────────────────
#  ASCII 렌더링
# ──────────────────────────────────────────────────────────────

# ANSI 색상 코드
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    DIM = '\033[2m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'


def clear_screen():
    """터미널 화면 초기화."""
    print('\033[2J\033[H', end='')


def render_strike_zone(
    plate_x: float,
    plate_z: float,
    outcome: str,
    count_str: str,
    speed_kmh: float,
    movement_x: float = 0.0,
    movement_z: float = 0.0,
) -> str:
    """ASCII 스트라이크존을 렌더링합니다.

    11×11 그리드로 스트라이크존과 투구 위치를 표시합니다.
    """
    # 존 좌표 (미터 → 그리드 좌표)
    grid_w, grid_h = 11, 11
    sz_left, sz_right = 2, 8     # 그리드 상 존 경계
    sz_bottom, sz_top = 2, 8

    # 투구 위치를 그리드 좌표로 변환
    x_range = (-0.5, 0.5)   # 미터
    z_range = (0.0, 1.5)
    px = int((plate_x - x_range[0]) / (x_range[1] - x_range[0]) * (grid_w - 1))
    pz = int((plate_z - z_range[0]) / (z_range[1] - z_range[0]) * (grid_h - 1))
    px = max(0, min(px, grid_w - 1))
    pz = max(0, min(pz, grid_h - 1))

    # 결과별 색상
    outcome_colors = {
        'called_strike': Colors.RED,
        'swinging_strike': Colors.YELLOW,
        'ball': Colors.BLUE,
        'foul': Colors.YELLOW,
        'single': Colors.GREEN,
        'extra_base': Colors.CYAN,
        'home_run': Colors.MAGENTA,
        'out': Colors.DIM,
    }
    ball_color = outcome_colors.get(outcome, Colors.WHITE)

    # 결과별 이모지
    outcome_labels = {
        'called_strike': '⚡ Called Strike!',
        'swinging_strike': '💨 Swinging Strike!',
        'ball': '🔵 Ball',
        'foul': '⚠️  Foul Ball',
        'single': '🏏 Single!',
        'extra_base': '🔥 Extra Base Hit!',
        'home_run': '🎆 HOME RUN!!!',
        'out': '👊 Out',
        'strikeout': '🔥 STRIKEOUT!!!',
        'walk': '🚶 Walk (Four Balls)',
    }

    lines = []
    lines.append("")
    lines.append(f"  {Colors.BOLD}⚾ {count_str}{Colors.RESET}")
    lines.append(f"  {Colors.DIM}{'─' * 28}{Colors.RESET}")

    # 존 렌더링 (하단 → 상단)
    for row in range(grid_h - 1, -1, -1):
        line = "  "
        for col in range(grid_w):
            is_zone = (sz_left <= col <= sz_right and sz_bottom <= row <= sz_top)
            is_ball_here = (col == px and row == pz)

            if is_ball_here:
                line += f"{ball_color}●{Colors.RESET} "
            elif is_zone:
                # 존 경계선
                if row == sz_bottom or row == sz_top:
                    if col == sz_left or col == sz_right:
                        line += f"{Colors.DIM}+{Colors.RESET} "
                    else:
                        line += f"{Colors.DIM}─{Colors.RESET} "
                elif col == sz_left or col == sz_right:
                    line += f"{Colors.DIM}│{Colors.RESET} "
                else:
                    # 9분할 격자
                    inner_col = (col - sz_left - 1)
                    inner_row = (row - sz_bottom - 1)
                    if inner_col == 1 or inner_col == 3:
                        line += f"{Colors.DIM}·{Colors.RESET} "
                    elif inner_row == 1 or inner_row == 3:
                        line += f"{Colors.DIM}·{Colors.RESET} "
                    else:
                        line += "  "
            else:
                line += f"{Colors.DIM}.{Colors.RESET} "

        lines.append(line)

    lines.append(f"  {Colors.DIM}{'─' * 28}{Colors.RESET}")

    # 결과 출력
    label = outcome_labels.get(outcome, outcome)
    lines.append(f"  {Colors.BOLD}{label}{Colors.RESET}")
    lines.append(
        f"  {Colors.CYAN}Speed: {speed_kmh:.0f} km/h{Colors.RESET} | "
        f"{Colors.YELLOW}Movement: ({movement_x*100:.1f}, {movement_z*100:.1f}) cm{Colors.RESET}"
    )

    return "\n".join(lines)


def render_hit_result(contact_info: dict) -> str:
    """타격 결과를 ASCII로 표시합니다."""
    if not contact_info:
        return ""

    lines = []
    ev = contact_info.get('exit_speed_kmh', 0)
    la = contact_info.get('launch_angle', 0)
    sa = contact_info.get('spray_angle', 0)
    ss = contact_info.get('sweet_spot_factor', 0)

    lines.append(f"\n  {Colors.BOLD}🏏 Hit Details{Colors.RESET}")
    lines.append(f"  {Colors.DIM}{'─' * 28}{Colors.RESET}")

    # Exit Velocity 바
    ev_bar_len = int(min(ev / 200, 1.0) * 20)
    ev_color = Colors.GREEN if ev > 150 else (Colors.YELLOW if ev > 130 else Colors.RED)
    ev_bar = f"{'█' * ev_bar_len}{'░' * (20 - ev_bar_len)}"
    lines.append(f"  Exit Vel:  {ev_color}{ev:.0f} km/h{Colors.RESET} [{ev_bar}]")

    # Launch Angle
    la_indicator = "↗" if la > 0 else "↘" if la < 0 else "→"
    lines.append(f"  Launch:    {Colors.CYAN}{la:+.1f}°{Colors.RESET} {la_indicator}")

    # Spray Angle
    sa_indicator = "←" if sa > 0 else "→" if sa < 0 else "↑"
    lines.append(f"  Spray:     {Colors.YELLOW}{sa:+.1f}°{Colors.RESET} {sa_indicator}")

    # Sweet Spot
    ss_bar_len = int(ss * 20)
    ss_color = Colors.GREEN if ss > 0.9 else (Colors.YELLOW if ss > 0.7 else Colors.RED)
    ss_bar = f"{'█' * ss_bar_len}{'░' * (20 - ss_bar_len)}"
    lines.append(f"  Sweet Spot:{ss_color} {ss:.0%}{Colors.RESET} [{ss_bar}]")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
#  유저 입력 처리
# ──────────────────────────────────────────────────────────────

def get_pitcher_action_from_user() -> np.ndarray:
    """유저에게 투구 파라미터를 입력받습니다."""
    print(f"\n  {Colors.BOLD}⚾ 투구 설정{Colors.RESET}")
    print(f"  {Colors.DIM}(Enter로 기본값 사용){Colors.RESET}")

    try:
        v = input(f"  속도 [-1=느림, 0=보통, 1=빠름] (0): ").strip()
        v = float(v) if v else 0.0

        x = input(f"  좌우 [-1=좌, 0=중앙, 1=우] (0): ").strip()
        x = float(x) if x else 0.0

        z = input(f"  상하 [-1=낮음, 0=중앙, 1=높음] (0): ").strip()
        z = float(z) if z else 0.0

        spin = input(f"  스핀 [-1=적음, 0=보통, 1=많음] (0): ").strip()
        spin = float(spin) if spin else 0.0

        axis = input(f"  스핀축 [-1=커브, 0=직구, 1=슬라이더] (0): ").strip()
        axis = float(axis) if axis else 0.0

    except (ValueError, EOFError):
        return np.zeros(5, dtype=np.float32)

    action = np.array([v, x, z, spin, axis], dtype=np.float32)
    return np.clip(action, -1.0, 1.0)


def get_batter_action_from_user(time_hint: float = 0.5) -> np.ndarray:
    """유저에게 스윙 여부와 파라미터를 입력받습니다."""
    print(f"\n  {Colors.BOLD}🏏 타격 결정{Colors.RESET}")
    print(f"  {Colors.DIM}(투구 도착 예상: {time_hint:.2f}초){Colors.RESET}")

    try:
        swing = input(f"  스윙? [y/n] (n): ").strip().lower()

        if swing in ('y', 'yes', 'ㅛ'):
            trigger = 0.8

            yaw = input(f"  스윙 방향 [-1=당기기, 0=중앙, 1=밀어치기] (0.3): ").strip()
            yaw = float(yaw) if yaw else 0.3

            pitch = input(f"  배트 각도 [-1=다운, 0=수평, 1=어퍼컷] (0): ").strip()
            pitch = float(pitch) if pitch else 0.0

            height = input(f"  높이 [-1=낮게, 0=중간, 1=높게] (0): ").strip()
            height = float(height) if height else 0.0
        else:
            trigger = -0.8
            yaw, pitch, height = 0.0, 0.0, 0.0

    except (ValueError, EOFError):
        return np.array([-0.8, 0.0, 0.0, 0.0], dtype=np.float32)

    action = np.array([trigger, yaw, pitch, height], dtype=np.float32)
    return np.clip(action, -1.0, 1.0)


# ──────────────────────────────────────────────────────────────
#  게임 엔진
# ──────────────────────────────────────────────────────────────

class BaseballGame:
    """대화형 야구 게임 엔진.

    학습된 AI 또는 유저가 투수/타자로 플레이합니다.
    """

    def __init__(
        self,
        role: str = 'spectator',
        checkpoint_path: Optional[str] = None,
        delay: float = 1.0,
    ):
        """
        Args:
            role: 'spectator' (관전), 'pitcher' (유저가 투수), 'batter' (유저가 타자)
            checkpoint_path: 학습된 모델 체크포인트 경로
            delay: AI 행동 간 딜레이 (초)
        """
        self.role = role
        self.delay = delay
        self.device = get_device()

        # 환경
        self.env = BaseballGameEnv()

        # AI 에이전트
        self.pitcher_agent = PitcherAgent().to(self.device)
        self.batter_agent = BatterAgent().to(self.device)

        # 체크포인트 로드
        if checkpoint_path and Path(checkpoint_path).exists():
            self._load_checkpoint(checkpoint_path)
            print(f"  {Colors.GREEN}✅ 체크포인트 로드 완료{Colors.RESET}")
        else:
            print(f"  {Colors.YELLOW}⚠️  체크포인트 없음 — 랜덤 가중치 사용{Colors.RESET}")

        # 통계
        self.games_played = 0
        self.pitcher_total_wins = 0
        self.batter_total_wins = 0

    def _load_checkpoint(self, path: str):
        """체크포인트를 로드합니다."""
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        self.pitcher_agent.load_state_dict(checkpoint['pitcher_state_dict'])
        self.batter_agent.load_state_dict(checkpoint['batter_state_dict'])

    def _get_ai_pitcher_action(self, obs: np.ndarray) -> np.ndarray:
        """AI 투수의 액션을 생성합니다."""
        obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        with torch.no_grad():
            action, _, _, _ = self.pitcher_agent.get_action_and_value(
                obs_tensor, deterministic=True
            )
        return action.cpu().numpy().squeeze()

    def _get_ai_batter_action(self, obs: np.ndarray) -> np.ndarray:
        """AI 타자의 액션을 생성합니다."""
        obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        with torch.no_grad():
            action, _, _, _, _ = self.batter_agent.get_action_and_value(
                obs_tensor, deterministic=True
            )
        return action.cpu().numpy().squeeze()

    def play_at_bat(self) -> dict:
        """1타석(At-Bat)을 실행합니다.

        Returns:
            타석 결과 딕셔너리
        """
        obs, info = self.env.reset()
        pitcher_obs = obs['pitcher']
        batter_obs = obs['batter']

        terminated = False
        truncated = False
        pitch_num = 0
        results = []

        clear_screen()
        self._print_header()

        while not terminated and not truncated:
            pitch_num += 1
            strikes = int(pitcher_obs[0])
            balls = int(pitcher_obs[1])
            count_str = f"Count: {balls}B - {strikes}S  |  Pitch #{pitch_num}"

            print(f"\n  {Colors.DIM}{'═' * 40}{Colors.RESET}")
            print(f"  {Colors.BOLD}Pitch #{pitch_num}{Colors.RESET}  |  "
                  f"{Colors.RED}{'●' * strikes}{'○' * (2 - strikes)}{Colors.RESET} "
                  f"{Colors.BLUE}{'●' * balls}{'○' * (3 - balls)}{Colors.RESET}")

            # 투수 액션
            if self.role == 'pitcher':
                pitcher_action = get_pitcher_action_from_user()
            else:
                pitcher_action = self._get_ai_pitcher_action(pitcher_obs)
                if self.role == 'spectator':
                    time.sleep(self.delay * 0.5)

            # 타자 액션
            if self.role == 'batter':
                batter_action = get_batter_action_from_user(
                    time_hint=batter_obs[12] if len(batter_obs) > 12 else 0.5
                )
            else:
                batter_action = self._get_ai_batter_action(batter_obs)

            # 환경 스텝
            action = {'pitcher': pitcher_action, 'batter': batter_action}
            next_obs, rewards, terminated, truncated, info = self.env.step(action)

            # 결과 표시
            pitch_data = info.get('pitch_data', {})
            pitch_outcome = info.get('pitch_outcome', {})

            outcome_key = pitch_outcome.get('reward_key', 'ball')
            plate_x = pitch_data.get('plate_x', 0.0)
            plate_z = pitch_data.get('plate_z', 0.75)
            speed = pitch_data.get('arrival_speed_kmh', 130.0)
            mv_x = pitch_data.get('movement_x', 0.0)
            mv_z = pitch_data.get('movement_z', 0.0)

            zone_render = render_strike_zone(
                plate_x, plate_z, outcome_key, count_str,
                speed, mv_x, mv_z,
            )
            print(zone_render)

            # 타격 결과 표시
            contact_info = pitch_outcome.get('contact_info')
            if contact_info:
                print(render_hit_result(contact_info))

            results.append(outcome_key)

            # 다음 관찰
            pitcher_obs = next_obs['pitcher']
            batter_obs = next_obs['batter']

            if self.role == 'spectator':
                time.sleep(self.delay)

        # 타석 종료
        final_strikes = int(pitcher_obs[0])
        final_balls = int(pitcher_obs[1])

        if final_strikes >= 3:
            at_bat_result = 'strikeout'
            winner = 'pitcher'
            print(f"\n  {Colors.RED}{Colors.BOLD}🔥 STRIKEOUT!!! ── "
                  f"삼진 아웃!{Colors.RESET}")
        elif final_balls >= 4:
            at_bat_result = 'walk'
            winner = 'batter'
            print(f"\n  {Colors.BLUE}{Colors.BOLD}🚶 WALK ── "
                  f"볼넷 출루!{Colors.RESET}")
        elif 'home_run' in results:
            at_bat_result = 'home_run'
            winner = 'batter'
            print(f"\n  {Colors.MAGENTA}{Colors.BOLD}🎆 HOME RUN!!! ── "
                  f"홈런!{Colors.RESET}")
        elif any(r in ('single', 'extra_base') for r in results):
            at_bat_result = 'hit'
            winner = 'batter'
            print(f"\n  {Colors.GREEN}{Colors.BOLD}🏏 HIT! ── "
                  f"안타!{Colors.RESET}")
        else:
            at_bat_result = 'out'
            winner = 'pitcher'
            print(f"\n  {Colors.DIM}{Colors.BOLD}👊 OUT ── "
                  f"아웃!{Colors.RESET}")

        if winner == 'pitcher':
            self.pitcher_total_wins += 1
        else:
            self.batter_total_wins += 1
        self.games_played += 1

        return {
            'result': at_bat_result,
            'winner': winner,
            'pitches': pitch_num,
            'outcomes': results,
        }

    def _print_header(self):
        """게임 헤더를 출력합니다."""
        print(f"""
  {Colors.BOLD}╔══════════════════════════════════════════╗
  ║     ⚾  BASEBALL RL GAME ENGINE  ⚾     ║
  ╚══════════════════════════════════════════╝{Colors.RESET}

  {Colors.DIM}Role: {self.role.upper()}{Colors.RESET}
  {Colors.DIM}Games: {self.games_played} | P-Wins: {self.pitcher_total_wins} | B-Wins: {self.batter_total_wins}{Colors.RESET}
""")

    def run(self, n_at_bats: int = 9):
        """N 타석 게임을 실행합니다.

        Args:
            n_at_bats: 실행할 타석 수 (기본 9)
        """
        print(f"\n  {Colors.BOLD}⚾ {n_at_bats}타석 게임을 시작합니다!{Colors.RESET}")
        print(f"  {Colors.DIM}Role: {self.role}{Colors.RESET}\n")

        game_results = []

        for i in range(n_at_bats):
            print(f"\n  {Colors.BOLD}{'═' * 40}{Colors.RESET}")
            print(f"  {Colors.BOLD}  📋 타석 {i+1}/{n_at_bats}{Colors.RESET}")
            print(f"  {Colors.BOLD}{'═' * 40}{Colors.RESET}")

            result = self.play_at_bat()
            game_results.append(result)

            if i < n_at_bats - 1:
                try:
                    input(f"\n  {Colors.DIM}Press Enter to continue...{Colors.RESET}")
                except EOFError:
                    break

        # 최종 결과
        self._print_game_summary(game_results)

    def _print_game_summary(self, results: list):
        """게임 종료 후 종합 결과를 표시합니다."""
        clear_screen()

        total = len(results)
        hits = sum(1 for r in results if r['winner'] == 'batter')
        outs = total - hits
        hrs = sum(1 for r in results if r['result'] == 'home_run')
        ks = sum(1 for r in results if r['result'] == 'strikeout')
        walks = sum(1 for r in results if r['result'] == 'walk')
        avg_pitches = np.mean([r['pitches'] for r in results])

        print(f"""
  {Colors.BOLD}╔══════════════════════════════════════════╗
  ║          ⚾  GAME SUMMARY  ⚾           ║
  ╠══════════════════════════════════════════╣{Colors.RESET}
  ║  At-Bats:    {total:3d}                         ║
  ║  {Colors.GREEN}Hits:        {hits:3d}{Colors.RESET}   (AVG: .{int(hits/max(total,1)*1000):03d})       ║
  ║  {Colors.RED}Outs:        {outs:3d}{Colors.RESET}                         ║
  ║  {Colors.MAGENTA}Home Runs:   {hrs:3d}{Colors.RESET}                         ║
  ║  {Colors.YELLOW}Strikeouts:  {ks:3d}{Colors.RESET}                         ║
  ║  {Colors.BLUE}Walks:       {walks:3d}{Colors.RESET}                         ║
  ║  Avg Pitches: {avg_pitches:.1f}                       ║
  {Colors.BOLD}╠══════════════════════════════════════════╣
  ║  Pitcher Wins: {self.pitcher_total_wins:3d}  |  Batter Wins: {self.batter_total_wins:3d}  ║
  ╚══════════════════════════════════════════╝{Colors.RESET}
""")


# ──────────────────────────────────────────────────────────────
#  메인 실행
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='⚾ Baseball RL Interactive Game',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python game.py                         # AI vs AI 관전
  python game.py --role pitcher          # 유저가 투수
  python game.py --role batter           # 유저가 타자
  python game.py --checkpoint ckpt.pt    # 체크포인트 로드
  python game.py --at-bats 3             # 3타석 게임
        """
    )
    parser.add_argument(
        '--role', type=str, default='spectator',
        choices=['spectator', 'pitcher', 'batter'],
        help='유저 역할 (spectator/pitcher/batter)',
    )
    parser.add_argument(
        '--checkpoint', type=str, default=None,
        help='학습된 모델 체크포인트 경로',
    )
    parser.add_argument(
        '--at-bats', type=int, default=9,
        help='실행할 타석 수 (기본 9)',
    )
    parser.add_argument(
        '--delay', type=float, default=1.0,
        help='AI 행동 간 딜레이 (초, 관전 모드)',
    )

    args = parser.parse_args()

    game = BaseballGame(
        role=args.role,
        checkpoint_path=args.checkpoint,
        delay=args.delay,
    )

    try:
        game.run(n_at_bats=args.at_bats)
    except KeyboardInterrupt:
        print(f"\n\n  {Colors.DIM}게임이 중단되었습니다.{Colors.RESET}")
        game._print_game_summary([])


if __name__ == '__main__':
    main()
