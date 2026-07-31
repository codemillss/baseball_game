import os
import sys
import numpy as np
import torch
import mujoco

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from envs.mujoco_baseball_env import MuJoCoBaseballEnv
from expert.trajectory_solver import AnalyticalTrajectorySolver

class Baseball9InningGameEngine:
    """9이닝 완전 자동 야구 경기 엔진 및 박스스코어 생성기."""

    def __init__(self):
        self.env = MuJoCoBaseballEnv()
        self.solver = AnalyticalTrajectorySolver()

        # Box Score Stats
        self.away_scores = [0] * 9
        self.home_scores = [0] * 9
        self.away_hits = 0
        self.home_hits = 0
        self.away_hrs = 0
        self.home_hrs = 0
        self.away_errors = 0
        self.home_errors = 0

    def play_full_game(self) -> dict:
        """9이닝 경기 전체를 자동 시뮬레이션합니다."""
        print("==================================================")
        print(" 🏟️ 9이닝 완전 자동 프로야구 경기 시뮬레이션 시작")
        print("==================================================")

        for inning in range(9):
            # 초 (Top Inning - Away Team Batting)
            self._play_half_inning(inning, is_home=False)
            # 말 (Bottom Inning - Home Team Batting)
            self._play_half_inning(inning, is_home=True)

        self._print_box_score()
        return self._get_game_summary()

    def _play_half_inning(self, inning_idx: int, is_home: bool):
        outs = 0
        balls = 0
        strikes = 0
        bases = [False, False, False] # 1st, 2nd, 3rd Base

        half_str = "말 (Home)" if is_home else "초 (Away)"
        print(f"\n📢 [{inning_idx+1}회{half_str}] 이닝 시작...")

        while outs < 3:
            obs, info = self.env.reset()
            ball_pos = obs[0:3]
            ball_vel = obs[3:6]
            t_impact, impact_pos, _ = self.solver.solve_pitch_impact(ball_pos, ball_vel)

            done = False
            ep_steps = 0
            has_hit = False

            while not done:
                time_remaining = t_impact - (ep_steps * 0.002 * self.env.frame_skip)
                action = self.solver.solve_inverse_kinematics_swing(obs, impact_pos, time_remaining)

                obs, reward, terminated, truncated, step_info = self.env.step(action)
                done = terminated or truncated
                ep_steps += 1

                if step_info.get('has_contacted', False) and not has_hit:
                    has_hit = True
                    exit_velo = step_info.get('exit_velocity_kmh', 0.0)
                    launch_ang = step_info.get('launch_angle', 0.0)

                    # Determine Play Outcome
                    if exit_velo >= 140.0 and 20.0 <= launch_ang <= 40.0:
                        print(f"   🚀 HOME RUN!! (Exit Velo: {exit_velo:.1f} km/h, Launch Angle: {launch_ang:.1f}°)")
                        runs = 1 + sum(bases)
                        if is_home:
                            self.home_scores[inning_idx] += runs
                            self.home_hits += 1
                            self.home_hrs += 1
                        else:
                            self.away_scores[inning_idx] += runs
                            self.away_hits += 1
                            self.away_hrs += 1
                        bases = [False, False, False]
                    elif exit_velo >= 115.0:
                        print(f"   ⚡ 안타 (Hit)! (Exit Velo: {exit_velo:.1f} km/h)")
                        if is_home:
                            self.home_hits += 1
                        else:
                            self.away_hits += 1
                        # Base running logic
                        if bases[2]:
                            if is_home: self.home_scores[inning_idx] += 1
                            else: self.away_scores[inning_idx] += 1
                        bases = [True, bases[0], bases[1]]
                    else:
                        print(f"   🟤 아웃 (Out - Grounder/Fly)")
                        outs += 1

            if not has_hit:
                print("   ⚾ 삼진/아웃 (Strikeout/Out)")
                outs += 1

        print(f" 🔚 [{inning_idx+1}회{half_str}] 이닝 종료 (3아웃)")

    def _print_box_score(self):
        away_total_r = sum(self.away_scores)
        home_total_r = sum(self.home_scores)

        print("\n=========================================================================")
        print(" 📊 9이닝 최종 경기 박스스코어 (BOX SCORE)")
        print("=========================================================================")
        print("TEAM   | 1  2  3  4  5  6  7  8  9 |  R   H   E  HR")
        print("-------+---------------------------+----------------")
        away_str = " ".join([f"{s:2d}" for s in self.away_scores])
        home_str = " ".join([f"{s:2d}" for s in self.home_scores])
        print(f"AWAY   | {away_str} | {away_total_r:2d}  {self.away_hits:2d}  {self.away_errors:2d}  {self.away_hrs:2d}")
        print(f"HOME   | {home_str} | {home_total_r:2d}  {self.home_hits:2d}  {self.home_errors:2d}  {self.home_hrs:2d}")
        print("=========================================================================")
        winner = "HOME TEAM WIN! 🎉" if home_total_r >= away_total_r else "AWAY TEAM WIN! 🎉"
        print(f" 🏆 승리 팀: {winner}\n")

    def _get_game_summary(self) -> dict:
        return {
            "away_runs": sum(self.away_scores),
            "home_runs": sum(self.home_scores),
            "away_hits": self.away_hits,
            "home_hits": self.home_hits,
            "away_hrs": self.away_hrs,
            "home_hrs": self.home_hrs,
        }

if __name__ == "__main__":
    engine = Baseball9InningGameEngine()
    engine.play_full_game()
