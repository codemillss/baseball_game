# baseball/archive/training/episode_recorder.py

원본: [archive/training/episode_recorder.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/episode_recorder.py)

SHA256: `b97a0efec05bd40c6b0e2f88ad7ab25e82e1c21df0405e7ef02d3ba1e70717b1`

전체 164행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `EpisodeRecorder` | ClassDef | 20 | 164 |
| `__init__` | FunctionDef | 23 | 26 |
| `record_episode` | FunctionDef | 28 | 164 |

## 전체 원문

````text
    1 | """
    2 | episode_recorder.py — 학습 에피소드 자동 시각화 및 녹화
    3 | 
    4 | 일정 에피소드마다 3D 환경의 렌더링 영상을 MP4 비디오로 자동 저장합니다.
    5 | 사람이 직접 보상 악용(Reward Hacking) 여부를 눈으로 검증할 수 있게 합니다.
    6 | 
    7 | 지원되는 정책 타입:
    8 |   - MultimodalBatterPolicy : get_action(obs_dict, hidden, deterministic=True)
    9 |   - LatentActor             : get_action(state, deterministic=True)  → RSSM와 연동
   10 | """
   11 | 
   12 | import cv2
   13 | import numpy as np
   14 | from pathlib import Path
   15 | from typing import Any
   16 | import torch
   17 | 
   18 | from training.logger import DashboardLogger
   19 | 
   20 | class EpisodeRecorder:
   21 |     """학습 중 에피소드 렌더링 결과를 비디오로 저장하는 클래스."""
   22 | 
   23 |     def __init__(self, save_dir: str = "videos", fps: int = 30):
   24 |         self.save_dir = Path(save_dir)
   25 |         self.save_dir.mkdir(parents=True, exist_ok=True)
   26 |         self.fps = fps
   27 | 
   28 |     def record_episode(
   29 |         self,
   30 |         env: Any,
   31 |         policy: Any,
   32 |         episode_idx: int,
   33 |         device: torch.device,
   34 |         max_steps: int = 300,
   35 |         rssm: Any = None,
   36 |     ) -> str:
   37 |         """한 에피소드를 시뮬레이션하고 MP4 파일로 녹화합니다.
   38 | 
   39 |         Args:
   40 |             env: 렌더링 가능한 UnifiedBaseballEnv ('rgb_array' 모드 필요)
   41 |             policy: 타자 정책 모델
   42 |             episode_idx: 에피소드 번호
   43 |             device: 모델 디바이스
   44 |             max_steps: 최대 스텝
   45 |             rssm: LatentActor 사용 시 BaseballRSSM 인스턴스
   46 | 
   47 |         Returns:
   48 |             저장된 비디오 파일 경로
   49 |         """
   50 |         # 임시로 렌더링 모드 설정 (원래 환경이 rgb_array여야 작동함)
   51 |         if env.render_mode != "rgb_array":
   52 |             print("⚠️ 경고: 환경이 'rgb_array' 모드가 아닙니다. 녹화를 건너뜁니다.")
   53 |             return ""
   54 | 
   55 |         obs, info = env.reset()
   56 |         frames = []
   57 |         hidden = None
   58 |         done = False
   59 |         step = 0
   60 | 
   61 |         # 초기 프레임
   62 |         import mujoco
   63 |         video_renderer = mujoco.Renderer(env.model, height=480, width=640)
   64 |         
   65 |         multi_frames = []
   66 |         cameras = [
   67 |             ("batter_cam", "1st Person (Batter)"), 
   68 |             ("pitcher_cam", "Pitcher View"), 
   69 |             ("catcher_cam", "Catcher View"), 
   70 |             ("broadcaster_cam", "Broadcaster View")
   71 |         ]
   72 |         for cam_name, label in cameras:
   73 |             video_renderer.update_scene(env.data, camera=cam_name)
   74 |             cam_frame = video_renderer.render().copy()
   75 |             cv2.putText(cam_frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
   76 |             multi_frames.append(cam_frame)
   77 |         top_row = np.hstack((multi_frames[0], multi_frames[1]))
   78 |         bottom_row = np.hstack((multi_frames[2], multi_frames[3]))
   79 |         frames.append(np.vstack((top_row, bottom_row)))
   80 | 
   81 |         while not done and step < max_steps:
   82 |             with torch.no_grad():
   83 |                 if rssm is not None:
   84 |                     # LatentActor 모드: RSSM 연동
   85 |                     obs_t = {k: torch.tensor(v, dtype=torch.float32, device=device).unsqueeze(0)
   86 |                              for k, v in obs.items()}
   87 |                     a_prev = action_t if 'action_t' in dir() else \
   88 |                              torch.zeros(1, env.action_space.shape[0], device=device)
   89 |                     hidden_h, hidden_z = hidden if hidden else rssm.initial_state(1, device)
   90 |                     hidden_h, hidden_z, _ = rssm.observe(obs_t, a_prev, hidden_h, hidden_z)
   91 |                     s = rssm.get_state(hidden_h, hidden_z)
   92 |                     action_t, _ = policy.get_action(s, deterministic=True)
   93 |                     hidden = (hidden_h, hidden_z)
   94 |                 elif hasattr(policy, 'get_action') and 'hidden' in policy.get_action.__code__.co_varnames:
   95 |                     # MultimodalBatterPolicy 모드 (LSTM hidden state 있음)
   96 |                     obs_t = {k: torch.tensor(v, dtype=torch.float32, device=device).unsqueeze(0)
   97 |                              for k, v in obs.items()}
   98 |                     action_t, _, _, hidden = policy.get_action(obs_t, hidden, deterministic=True)
   99 |                 else:
  100 |                     # Fallback: 단순 MLP 스타일
  101 |                     obs_t = {k: torch.tensor(v, dtype=torch.float32, device=device).unsqueeze(0)
  102 |                              for k, v in obs.items()}
  103 |                     action_t, _ = policy.get_action(obs_t, deterministic=True)
  104 | 
  105 |             action = action_t.squeeze(0).cpu().numpy()
  106 |             
  107 |             obs, _, terminated, truncated, info = env.step(action)
  108 |             done = terminated or truncated
  109 | 
  110 |             multi_frames = []
  111 |             cameras = [
  112 |                 ("batter_cam", "1st Person (Batter)"), 
  113 |                 ("pitcher_cam", "Pitcher View"), 
  114 |                 ("catcher_cam", "Catcher View"), 
  115 |                 ("broadcaster_cam", "Broadcaster View")
  116 |             ]
  117 |                 
  118 |             for cam_name, label in cameras:
  119 |                 video_renderer.update_scene(env.data, camera=cam_name)
  120 |                 # Copy frame to avoid reference issues
  121 |                 cam_frame = video_renderer.render().copy()
  122 |                 # Add label using cv2
  123 |                 cv2.putText(cam_frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
  124 |                 multi_frames.append(cam_frame)
  125 |             
  126 |             # Composite 2x2 Grid
  127 |             top_row = np.hstack((multi_frames[0], multi_frames[1]))
  128 |             bottom_row = np.hstack((multi_frames[2], multi_frames[3]))
  129 |             grid_frame = np.vstack((top_row, bottom_row))
  130 |             
  131 |             frames.append(grid_frame)
  132 |             
  133 |             step += 1
  134 | 
  135 |         if not frames:
  136 |             return ""
  137 | 
  138 |         # 'result' 키가 없을 수 있음 (UnifiedBaseballEnv vs BaseballGameEnv)
  139 |         result_str = info.get('result', info.get('game_event', 'UNKNOWN'))
  140 |         # 파일명에 안전한 문자만 사용
  141 |         result_str = result_str.replace(' ', '_').replace('/', '-')[:20]
  142 |         filename = self.save_dir / f"ep_{episode_idx:04d}_stage_{info.get('stage', 0)}_{result_str}.mp4"
  143 |         
  144 |         # OpenCV 비디오 저장 (BGR 변환 필요)
  145 |         height, width, _ = frames[0].shape
  146 |         fourcc = cv2.VideoWriter_fourcc(*"avc1")
  147 |         out = cv2.VideoWriter(str(filename), fourcc, self.fps, (width, height))
  148 |         if not out.isOpened():
  149 |             fourcc = cv2.VideoWriter_fourcc(*"mp4v")
  150 |             out = cv2.VideoWriter(str(filename), fourcc, self.fps, (width, height))
  151 | 
  152 |         for f in frames:
  153 |             # MuJoCo 렌더링은 RGB, OpenCV는 BGR
  154 |             out.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
  155 |         
  156 |         out.release()
  157 |         
  158 |         # Log to Dashboard
  159 |         logger = DashboardLogger()
  160 |         # Extract just the filename without directory path for the web frontend
  161 |         logger.log_video(episode_idx, info['stage'], filename.name)
  162 |         
  163 |         print(f"  🎬 에피소드 비디오 저장됨: {filename}")
  164 |         return str(filename)
````
