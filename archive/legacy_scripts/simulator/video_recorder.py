"""
video_recorder.py — 3D Baseball Simulation MP4/GIF Video Recorder

MuJoCo 3D 야구 시뮬레이션 화면을 60FPS High-Quality MP4 및 GIF 영상으로
직접 녹화(Record)하여 videos/ 디렉토리에 파일로 저장합니다.
"""

import os
from pathlib import Path
from typing import Optional

import numpy as np
import imageio
import torch

from envs.mujoco_baseball_env import MuJoCoBaseballEnv
from expert.trajectory_solver import AnalyticalTrajectorySolver
from training.networks import BatterPolicy, get_device


class VideoRecorder:
    """3D 시뮬레이션 녹화기."""

    def __init__(self, output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = str(Path(__file__).parent.parent / "videos")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def record_episode(
        self,
        policy_type: str = "expert",  # "expert", "random", "bc", "ppo"
        checkpoint_path: Optional[str] = None,
        save_filename: str = "3d_baseball_simulation.mp4",
        fps: int = 60,
    ) -> str:
        """한 에피소드를 3D offscreen 렌더링으로 녹화하여 MP4 및 GIF 영상으로 저장합니다.

        Args:
            policy_type: 사용할 정책 유형 ("expert", "random", "bc", "ppo")
            checkpoint_path: 로드할 PyTorch 체크포인트 경로
            save_filename: 저장할 파일 이름 (.mp4 또는 .gif)

        Returns:
            저장된 영상 파일 경로
        """
        env = MuJoCoBaseballEnv(render_mode="rgb_array")
        device = get_device()
        solver = AnalyticalTrajectorySolver()

        policy = None
        if policy_type in ("bc", "ppo") and checkpoint_path and os.path.exists(checkpoint_path):
            policy = BatterPolicy(obs_dim=15, action_dim=3).to(device)
            ckpt = torch.load(checkpoint_path, map_location=device)
            state_dict = ckpt.get('policy_state_dict', ckpt)
            policy.load_state_dict(state_dict)
            policy.eval()
            print(f"🎬 {policy_type.upper()} 체크포인트 로드됨: {checkpoint_path}")

        obs, info = env.reset(seed=42)
        done = False
        hidden = None
        frames = []

        ball_pos = obs[0:3]
        ball_vel = obs[3:6]
        t_impact, impact_pos, _ = solver.solve_pitch_impact(ball_pos, ball_vel)

        ep_steps = 0
        print(f"🎥 3D 야구 시뮬레이션 영상 녹화 중... (Mode: {policy_type.upper()})")

        while not done:
            # 1. 3D 렌더링 프레임 캡처
            frame = env.render()
            if frame is not None:
                frames.append(frame)

            # 2. 액션 선택
            if policy_type == "expert":
                time_remaining = t_impact - (ep_steps * 0.002 * env.frame_skip)
                action = solver.solve_inverse_kinematics_swing(obs, impact_pos, time_remaining)

            elif policy is not None:
                obs_t = torch.tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
                with torch.no_grad():
                    action_t, _, _, hidden = policy.get_action(obs_t, hidden, deterministic=True)
                action = action_t.squeeze(0).cpu().numpy()

            else:
                action = env.action_space.sample()

            obs, reward, terminated, truncated, step_info = env.step(action)
            done = terminated or truncated
            ep_steps += 1

        env.close()

        save_path = self.output_dir / save_filename
        gif_path = self.output_dir / save_filename.replace(".mp4", ".gif")

        # MP4 저장
        imageio.mimsave(str(save_path), frames, fps=fps)
        # GIF 도 함께 저장 (포트폴리오 및 문서 삽입용)
        imageio.mimsave(str(gif_path), frames[::2], fps=fps // 2)

        print(f"✅ 3D 시뮬레이션 영상 저장 완료!")
        print(f"   📹 MP4 파일: {save_path}")
        print(f"   🎞️ GIF 파일: {gif_path}\n")

        return str(save_path)


def main():
    recorder = VideoRecorder()
    recorder.record_episode(policy_type="expert", save_filename="expert_swing_3d.mp4")


if __name__ == '__main__':
    main()
