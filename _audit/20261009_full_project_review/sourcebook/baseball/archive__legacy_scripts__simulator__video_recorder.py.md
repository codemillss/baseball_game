# baseball/archive/legacy_scripts/simulator/video_recorder.py

원본: [archive/legacy_scripts/simulator/video_recorder.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_scripts/simulator/video_recorder.py)

SHA256: `e9cd2953525a3930d55db2683fe9e975dd0d70d73e10dd93720b2e97da43b1dc`

전체 120행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `VideoRecorder` | ClassDef | 21 | 111 |
| `__init__` | FunctionDef | 24 | 29 |
| `record_episode` | FunctionDef | 31 | 111 |
| `main` | FunctionDef | 114 | 116 |

## 전체 원문

````text
    1 | """
    2 | video_recorder.py — 3D Baseball Simulation MP4/GIF Video Recorder
    3 | 
    4 | MuJoCo 3D 야구 시뮬레이션 화면을 60FPS High-Quality MP4 및 GIF 영상으로
    5 | 직접 녹화(Record)하여 videos/ 디렉토리에 파일로 저장합니다.
    6 | """
    7 | 
    8 | import os
    9 | from pathlib import Path
   10 | from typing import Optional
   11 | 
   12 | import numpy as np
   13 | import imageio
   14 | import torch
   15 | 
   16 | from envs.mujoco_baseball_env import MuJoCoBaseballEnv
   17 | from expert.trajectory_solver import AnalyticalTrajectorySolver
   18 | from training.networks import BatterPolicy, get_device
   19 | 
   20 | 
   21 | class VideoRecorder:
   22 |     """3D 시뮬레이션 녹화기."""
   23 | 
   24 |     def __init__(self, output_dir: Optional[str] = None):
   25 |         if output_dir is None:
   26 |             output_dir = str(Path(__file__).parent.parent / "videos")
   27 | 
   28 |         self.output_dir = Path(output_dir)
   29 |         self.output_dir.mkdir(parents=True, exist_ok=True)
   30 | 
   31 |     def record_episode(
   32 |         self,
   33 |         policy_type: str = "expert",  # "expert", "random", "bc", "ppo"
   34 |         checkpoint_path: Optional[str] = None,
   35 |         save_filename: str = "3d_baseball_simulation.mp4",
   36 |         fps: int = 60,
   37 |     ) -> str:
   38 |         """한 에피소드를 3D offscreen 렌더링으로 녹화하여 MP4 및 GIF 영상으로 저장합니다.
   39 | 
   40 |         Args:
   41 |             policy_type: 사용할 정책 유형 ("expert", "random", "bc", "ppo")
   42 |             checkpoint_path: 로드할 PyTorch 체크포인트 경로
   43 |             save_filename: 저장할 파일 이름 (.mp4 또는 .gif)
   44 | 
   45 |         Returns:
   46 |             저장된 영상 파일 경로
   47 |         """
   48 |         env = MuJoCoBaseballEnv(render_mode="rgb_array")
   49 |         device = get_device()
   50 |         solver = AnalyticalTrajectorySolver()
   51 | 
   52 |         policy = None
   53 |         if policy_type in ("bc", "ppo") and checkpoint_path and os.path.exists(checkpoint_path):
   54 |             policy = BatterPolicy(obs_dim=15, action_dim=3).to(device)
   55 |             ckpt = torch.load(checkpoint_path, map_location=device)
   56 |             state_dict = ckpt.get('policy_state_dict', ckpt)
   57 |             policy.load_state_dict(state_dict)
   58 |             policy.eval()
   59 |             print(f"🎬 {policy_type.upper()} 체크포인트 로드됨: {checkpoint_path}")
   60 | 
   61 |         obs, info = env.reset(seed=42)
   62 |         done = False
   63 |         hidden = None
   64 |         frames = []
   65 | 
   66 |         ball_pos = obs[0:3]
   67 |         ball_vel = obs[3:6]
   68 |         t_impact, impact_pos, _ = solver.solve_pitch_impact(ball_pos, ball_vel)
   69 | 
   70 |         ep_steps = 0
   71 |         print(f"🎥 3D 야구 시뮬레이션 영상 녹화 중... (Mode: {policy_type.upper()})")
   72 | 
   73 |         while not done:
   74 |             # 1. 3D 렌더링 프레임 캡처
   75 |             frame = env.render()
   76 |             if frame is not None:
   77 |                 frames.append(frame)
   78 | 
   79 |             # 2. 액션 선택
   80 |             if policy_type == "expert":
   81 |                 time_remaining = t_impact - (ep_steps * 0.002 * env.frame_skip)
   82 |                 action = solver.solve_inverse_kinematics_swing(obs, impact_pos, time_remaining)
   83 | 
   84 |             elif policy is not None:
   85 |                 obs_t = torch.tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
   86 |                 with torch.no_grad():
   87 |                     action_t, _, _, hidden = policy.get_action(obs_t, hidden, deterministic=True)
   88 |                 action = action_t.squeeze(0).cpu().numpy()
   89 | 
   90 |             else:
   91 |                 action = env.action_space.sample()
   92 | 
   93 |             obs, reward, terminated, truncated, step_info = env.step(action)
   94 |             done = terminated or truncated
   95 |             ep_steps += 1
   96 | 
   97 |         env.close()
   98 | 
   99 |         save_path = self.output_dir / save_filename
  100 |         gif_path = self.output_dir / save_filename.replace(".mp4", ".gif")
  101 | 
  102 |         # MP4 저장
  103 |         imageio.mimsave(str(save_path), frames, fps=fps)
  104 |         # GIF 도 함께 저장 (포트폴리오 및 문서 삽입용)
  105 |         imageio.mimsave(str(gif_path), frames[::2], fps=fps // 2)
  106 | 
  107 |         print(f"✅ 3D 시뮬레이션 영상 저장 완료!")
  108 |         print(f"   📹 MP4 파일: {save_path}")
  109 |         print(f"   🎞️ GIF 파일: {gif_path}\n")
  110 | 
  111 |         return str(save_path)
  112 | 
  113 | 
  114 | def main():
  115 |     recorder = VideoRecorder()
  116 |     recorder.record_episode(policy_type="expert", save_filename="expert_swing_3d.mp4")
  117 | 
  118 | 
  119 | if __name__ == '__main__':
  120 |     main()
````
