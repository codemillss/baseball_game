"""
live_viewer.py — Real-Time Native 3D GUI Viewer Popup Window

MuJoCo 3.x Native Passive Viewer(GLFW)를 구동하여 macOS 화면상에 
실제 고해상도 3D 야구장, 3D 공 궤적, 3D 배트 스윙을 실시간 60FPS 
GUI 팝업 윈도우(Popup Window)로 띄워 관전합니다.
"""

import time
import os
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import mujoco
import mujoco.viewer

from envs.mujoco_baseball_env import MuJoCoBaseballEnv
from expert.trajectory_solver import AnalyticalTrajectorySolver
from training.networks import BatterPolicy, get_device


class Live3DViewer:
    """실시간 3D GUI 팝업 뷰어."""

    def __init__(self, xml_path: Optional[str] = None):
        if xml_path is None:
            xml_path = str(Path(__file__).parent.parent / "assets" / "stadium_3d.xml")

        self.xml_path = xml_path
        self.solver = AnalyticalTrajectorySolver()

    def launch(
        self,
        mode: str = "expert",  # "expert", "random", "bc", "ppo"
        checkpoint_path: Optional[str] = None,
        n_episodes: int = 5,
    ):
        """macOS 3D 팝업 윈도우를 열고 실시간 시뮬레이션을 렌더링합니다."""
        env = MuJoCoBaseballEnv()
        device = get_device()

        policy = None
        if mode in ("bc", "ppo") and checkpoint_path and os.path.exists(checkpoint_path):
            policy = BatterPolicy(obs_dim=15, action_dim=3).to(device)
            ckpt = torch.load(checkpoint_path, map_location=device)
            state_dict = ckpt.get('policy_state_dict', ckpt)
            policy.load_state_dict(state_dict)
            policy.eval()
            print(f"🎬 3D Viewer: {mode.upper()} 모델 체크포인트 로드 완료 ({checkpoint_path})")

        print("\n" + "=" * 60)
        print(f"🖥️ MuJoCo 3D GUI 팝업 윈도우를 실행합니다 (Mode: {mode.upper()})...")
        print("   * 화면에 3D OpenGL 팝업 창이 열립니다.")
        print("   * 마우스 좌클릭 드래그: 360도 3D 카메라 회전")
        print("   * 마우스 우클릭 드래그: 3D 카메라이동 / 휠: 확대 및 축소")
        print("=" * 60 + "\n")

        # Native GLFW 팝업 윈도우 실행
        with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
            for ep in range(1, n_episodes + 1):
                obs, info = env.reset()
                done = False
                hidden = None

                ball_pos = obs[0:3]
                ball_vel = obs[3:6]
                t_impact, impact_pos, _ = self.solver.solve_pitch_impact(ball_pos, ball_vel)

                ep_steps = 0
                print(f"⚾ 3D GUI 팝업 - 타석 {ep}/{n_episodes} 진행 중...")

                while viewer.is_running() and not done:
                    step_start = time.time()

                    # 액션 선택
                    if mode == "expert":
                        time_remaining = t_impact - (ep_steps * 0.002 * env.frame_skip)
                        action = self.solver.solve_inverse_kinematics_swing(obs, impact_pos, time_remaining)
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

                    # 3D 팝업 윈도우 동기화 갱신
                    viewer.sync()

                    # 60 FPS 제어 (1/60초 = 0.016초)
                    time_until_next_frame = env.model.opt.timestep * env.frame_skip - (time.time() - step_start)
                    if time_until_next_frame > 0:
                        time.sleep(time_until_next_frame)

                if step_info.get('has_contacted', False):
                    ev = step_info.get('exit_velocity_kmh', 0.0)
                    print(f"   🏏 HIT! 타구 속도: {ev:.1f} km/h")

                time.sleep(0.5)

        env.close()
        print("✅ 3D GUI 팝업 시뮬레이션이 종료되었습니다.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="3D Baseball GUI Live Viewer Popup")
    parser.add_argument("--mode", type=str, default="expert", choices=["expert", "random", "bc", "ppo"])
    parser.add_argument("--checkpoint", type=str, default=None)
    parser.add_argument("--episodes", type=int, default=5)
    args = parser.parse_args()

    viewer = Live3DViewer()
    viewer.launch(mode=args.mode, checkpoint_path=args.checkpoint, n_episodes=args.episodes)


if __name__ == '__main__':
    main()
