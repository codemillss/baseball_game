# baseball/archive/legacy_scripts/simulator/live_viewer.py

원본: [archive/legacy_scripts/simulator/live_viewer.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_scripts/simulator/live_viewer.py)

SHA256: `854440a30874f81bd8ded2281a44afc75d0df02b351e7098f4e73bc1b215d0ea`

전체 124행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `Live3DViewer` | ClassDef | 24 | 108 |
| `__init__` | FunctionDef | 27 | 32 |
| `launch` | FunctionDef | 34 | 108 |
| `main` | FunctionDef | 111 | 120 |

## 전체 원문

````text
    1 | """
    2 | live_viewer.py — Real-Time Native 3D GUI Viewer Popup Window
    3 | 
    4 | MuJoCo 3.x Native Passive Viewer(GLFW)를 구동하여 macOS 화면상에 
    5 | 실제 고해상도 3D 야구장, 3D 공 궤적, 3D 배트 스윙을 실시간 60FPS 
    6 | GUI 팝업 윈도우(Popup Window)로 띄워 관전합니다.
    7 | """
    8 | 
    9 | import time
   10 | import os
   11 | from pathlib import Path
   12 | from typing import Optional
   13 | 
   14 | import numpy as np
   15 | import torch
   16 | import mujoco
   17 | import mujoco.viewer
   18 | 
   19 | from envs.mujoco_baseball_env import MuJoCoBaseballEnv
   20 | from expert.trajectory_solver import AnalyticalTrajectorySolver
   21 | from training.networks import BatterPolicy, get_device
   22 | 
   23 | 
   24 | class Live3DViewer:
   25 |     """실시간 3D GUI 팝업 뷰어."""
   26 | 
   27 |     def __init__(self, xml_path: Optional[str] = None):
   28 |         if xml_path is None:
   29 |             xml_path = str(Path(__file__).parent.parent / "assets" / "stadium_3d.xml")
   30 | 
   31 |         self.xml_path = xml_path
   32 |         self.solver = AnalyticalTrajectorySolver()
   33 | 
   34 |     def launch(
   35 |         self,
   36 |         mode: str = "expert",  # "expert", "random", "bc", "ppo"
   37 |         checkpoint_path: Optional[str] = None,
   38 |         n_episodes: int = 5,
   39 |     ):
   40 |         """macOS 3D 팝업 윈도우를 열고 실시간 시뮬레이션을 렌더링합니다."""
   41 |         env = MuJoCoBaseballEnv()
   42 |         device = get_device()
   43 | 
   44 |         policy = None
   45 |         if mode in ("bc", "ppo") and checkpoint_path and os.path.exists(checkpoint_path):
   46 |             policy = BatterPolicy(obs_dim=15, action_dim=3).to(device)
   47 |             ckpt = torch.load(checkpoint_path, map_location=device)
   48 |             state_dict = ckpt.get('policy_state_dict', ckpt)
   49 |             policy.load_state_dict(state_dict)
   50 |             policy.eval()
   51 |             print(f"🎬 3D Viewer: {mode.upper()} 모델 체크포인트 로드 완료 ({checkpoint_path})")
   52 | 
   53 |         print("\n" + "=" * 60)
   54 |         print(f"🖥️ MuJoCo 3D GUI 팝업 윈도우를 실행합니다 (Mode: {mode.upper()})...")
   55 |         print("   * 화면에 3D OpenGL 팝업 창이 열립니다.")
   56 |         print("   * 마우스 좌클릭 드래그: 360도 3D 카메라 회전")
   57 |         print("   * 마우스 우클릭 드래그: 3D 카메라이동 / 휠: 확대 및 축소")
   58 |         print("=" * 60 + "\n")
   59 | 
   60 |         # Native GLFW 팝업 윈도우 실행
   61 |         with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
   62 |             for ep in range(1, n_episodes + 1):
   63 |                 obs, info = env.reset()
   64 |                 done = False
   65 |                 hidden = None
   66 | 
   67 |                 ball_pos = obs[0:3]
   68 |                 ball_vel = obs[3:6]
   69 |                 t_impact, impact_pos, _ = self.solver.solve_pitch_impact(ball_pos, ball_vel)
   70 | 
   71 |                 ep_steps = 0
   72 |                 print(f"⚾ 3D GUI 팝업 - 타석 {ep}/{n_episodes} 진행 중...")
   73 | 
   74 |                 while viewer.is_running() and not done:
   75 |                     step_start = time.time()
   76 | 
   77 |                     # 액션 선택
   78 |                     if mode == "expert":
   79 |                         time_remaining = t_impact - (ep_steps * 0.002 * env.frame_skip)
   80 |                         action = self.solver.solve_inverse_kinematics_swing(obs, impact_pos, time_remaining)
   81 |                     elif policy is not None:
   82 |                         obs_t = torch.tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
   83 |                         with torch.no_grad():
   84 |                             action_t, _, _, hidden = policy.get_action(obs_t, hidden, deterministic=True)
   85 |                         action = action_t.squeeze(0).cpu().numpy()
   86 |                     else:
   87 |                         action = env.action_space.sample()
   88 | 
   89 |                     obs, reward, terminated, truncated, step_info = env.step(action)
   90 |                     done = terminated or truncated
   91 |                     ep_steps += 1
   92 | 
   93 |                     # 3D 팝업 윈도우 동기화 갱신
   94 |                     viewer.sync()
   95 | 
   96 |                     # 60 FPS 제어 (1/60초 = 0.016초)
   97 |                     time_until_next_frame = env.model.opt.timestep * env.frame_skip - (time.time() - step_start)
   98 |                     if time_until_next_frame > 0:
   99 |                         time.sleep(time_until_next_frame)
  100 | 
  101 |                 if step_info.get('has_contacted', False):
  102 |                     ev = step_info.get('exit_velocity_kmh', 0.0)
  103 |                     print(f"   🏏 HIT! 타구 속도: {ev:.1f} km/h")
  104 | 
  105 |                 time.sleep(0.5)
  106 | 
  107 |         env.close()
  108 |         print("✅ 3D GUI 팝업 시뮬레이션이 종료되었습니다.")
  109 | 
  110 | 
  111 | def main():
  112 |     import argparse
  113 |     parser = argparse.ArgumentParser(description="3D Baseball GUI Live Viewer Popup")
  114 |     parser.add_argument("--mode", type=str, default="expert", choices=["expert", "random", "bc", "ppo"])
  115 |     parser.add_argument("--checkpoint", type=str, default=None)
  116 |     parser.add_argument("--episodes", type=int, default=5)
  117 |     args = parser.parse_args()
  118 | 
  119 |     viewer = Live3DViewer()
  120 |     viewer.launch(mode=args.mode, checkpoint_path=args.checkpoint, n_episodes=args.episodes)
  121 | 
  122 | 
  123 | if __name__ == '__main__':
  124 |     main()
````
