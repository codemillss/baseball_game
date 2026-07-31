"""
demo_collector.py — Expert Demonstration Dataset Collector

Analytical Physics IK Solver 기반의 Rule-based Expert Bot을 구동하여
Stage 1 Behavioral Cloning (BC) pre-training에 사용되는 고품질
Expert State-Action Trajectory 데이터셋(.npz)을 자동 수집합니다.
"""

import os
from pathlib import Path
from typing import Optional, Dict, List

import numpy as np

from envs.mujoco_baseball_env import MuJoCoBaseballEnv
from expert.trajectory_solver import AnalyticalTrajectorySolver


class ExpertDemoCollector:
    """고품질 전문가 스윙 데이터 수집기."""

    def __init__(self, output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = str(Path(__file__).parent.parent / "data" / "expert_demos")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.solver = AnalyticalTrajectorySolver()

    def collect_demos(self, n_episodes: int = 100, save_filename: str = "expert_demos.npz") -> str:
        """N개의 에피소드에서 전문가 스윙 데이터 트래젝토리를 수집합니다.

        Returns:
            저장된 .npz 데이터셋 파일 경로
        """
        env = MuJoCoBaseballEnv()

        obs_list: List[np.ndarray] = []
        action_list: List[np.ndarray] = []
        reward_list: List[float] = []

        total_contacts = 0
        total_episodes = 0

        print(f"⚾ Expert Demo 수집 시작 ({n_episodes} episodes)...")

        for ep in range(n_episodes):
            obs, info = env.reset()
            done = False

            # 초기 위치/속도로 궤적 역산
            ball_pos = obs[0:3]
            ball_vel = obs[3:6]
            t_impact, impact_pos, _ = self.solver.solve_pitch_impact(ball_pos, ball_vel)

            ep_steps = 0
            while not done:
                # 잔여 시간 계산
                time_remaining = t_impact - (ep_steps * 0.002 * env.frame_skip)

                # IK 스윙 액션 산출
                action = self.solver.solve_inverse_kinematics_swing(obs, impact_pos, time_remaining)

                next_obs, reward, terminated, truncated, step_info = env.step(action)
                done = terminated or truncated

                # 데이터 수집 (정타/스윙 구간 위주)
                obs_list.append(obs)
                action_list.append(action)
                reward_list.append(reward)

                obs = next_obs
                ep_steps += 1

                if step_info.get('has_contacted', False):
                    total_contacts += 1

            total_episodes += 1
            if (ep + 1) % max(1, n_episodes // 5) == 0:
                print(f"   [{ep+1}/{n_episodes}] Contact Rate: {total_contacts/total_episodes:.1%}")

        env.close()

        # NumPy 배열 변환
        obs_arr = np.array(obs_list, dtype=np.float32)
        act_arr = np.array(action_list, dtype=np.float32)
        rew_arr = np.array(reward_list, dtype=np.float32)

        save_path = self.output_dir / save_filename
        np.savez_compressed(
            save_path,
            observations=obs_arr,
            actions=act_arr,
            rewards=rew_arr,
            n_episodes=n_episodes,
            contact_rate=total_contacts / total_episodes,
        )

        print(f"💾 Expert Demo 데이터셋 저장 완료: {save_path}")
        print(f"   - 총 Samples: {len(obs_arr):,}개")
        print(f"   - Final Contact Rate: {total_contacts/total_episodes:.1%}")

        return str(save_path)


def main():
    collector = ExpertDemoCollector()
    collector.collect_demos(n_episodes=100)


if __name__ == '__main__':
    main()
