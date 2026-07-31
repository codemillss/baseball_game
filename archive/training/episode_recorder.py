"""
episode_recorder.py — 학습 에피소드 자동 시각화 및 녹화

일정 에피소드마다 3D 환경의 렌더링 영상을 MP4 비디오로 자동 저장합니다.
사람이 직접 보상 악용(Reward Hacking) 여부를 눈으로 검증할 수 있게 합니다.

지원되는 정책 타입:
  - MultimodalBatterPolicy : get_action(obs_dict, hidden, deterministic=True)
  - LatentActor             : get_action(state, deterministic=True)  → RSSM와 연동
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Any
import torch

from training.logger import DashboardLogger

class EpisodeRecorder:
    """학습 중 에피소드 렌더링 결과를 비디오로 저장하는 클래스."""

    def __init__(self, save_dir: str = "videos", fps: int = 30):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.fps = fps

    def record_episode(
        self,
        env: Any,
        policy: Any,
        episode_idx: int,
        device: torch.device,
        max_steps: int = 300,
        rssm: Any = None,
    ) -> str:
        """한 에피소드를 시뮬레이션하고 MP4 파일로 녹화합니다.

        Args:
            env: 렌더링 가능한 UnifiedBaseballEnv ('rgb_array' 모드 필요)
            policy: 타자 정책 모델
            episode_idx: 에피소드 번호
            device: 모델 디바이스
            max_steps: 최대 스텝
            rssm: LatentActor 사용 시 BaseballRSSM 인스턴스

        Returns:
            저장된 비디오 파일 경로
        """
        # 임시로 렌더링 모드 설정 (원래 환경이 rgb_array여야 작동함)
        if env.render_mode != "rgb_array":
            print("⚠️ 경고: 환경이 'rgb_array' 모드가 아닙니다. 녹화를 건너뜁니다.")
            return ""

        obs, info = env.reset()
        frames = []
        hidden = None
        done = False
        step = 0

        # 초기 프레임
        import mujoco
        video_renderer = mujoco.Renderer(env.model, height=480, width=640)
        
        multi_frames = []
        cameras = [
            ("batter_cam", "1st Person (Batter)"), 
            ("pitcher_cam", "Pitcher View"), 
            ("catcher_cam", "Catcher View"), 
            ("broadcaster_cam", "Broadcaster View")
        ]
        for cam_name, label in cameras:
            video_renderer.update_scene(env.data, camera=cam_name)
            cam_frame = video_renderer.render().copy()
            cv2.putText(cam_frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
            multi_frames.append(cam_frame)
        top_row = np.hstack((multi_frames[0], multi_frames[1]))
        bottom_row = np.hstack((multi_frames[2], multi_frames[3]))
        frames.append(np.vstack((top_row, bottom_row)))

        while not done and step < max_steps:
            with torch.no_grad():
                if rssm is not None:
                    # LatentActor 모드: RSSM 연동
                    obs_t = {k: torch.tensor(v, dtype=torch.float32, device=device).unsqueeze(0)
                             for k, v in obs.items()}
                    a_prev = action_t if 'action_t' in dir() else \
                             torch.zeros(1, env.action_space.shape[0], device=device)
                    hidden_h, hidden_z = hidden if hidden else rssm.initial_state(1, device)
                    hidden_h, hidden_z, _ = rssm.observe(obs_t, a_prev, hidden_h, hidden_z)
                    s = rssm.get_state(hidden_h, hidden_z)
                    action_t, _ = policy.get_action(s, deterministic=True)
                    hidden = (hidden_h, hidden_z)
                elif hasattr(policy, 'get_action') and 'hidden' in policy.get_action.__code__.co_varnames:
                    # MultimodalBatterPolicy 모드 (LSTM hidden state 있음)
                    obs_t = {k: torch.tensor(v, dtype=torch.float32, device=device).unsqueeze(0)
                             for k, v in obs.items()}
                    action_t, _, _, hidden = policy.get_action(obs_t, hidden, deterministic=True)
                else:
                    # Fallback: 단순 MLP 스타일
                    obs_t = {k: torch.tensor(v, dtype=torch.float32, device=device).unsqueeze(0)
                             for k, v in obs.items()}
                    action_t, _ = policy.get_action(obs_t, deterministic=True)

            action = action_t.squeeze(0).cpu().numpy()
            
            obs, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            multi_frames = []
            cameras = [
                ("batter_cam", "1st Person (Batter)"), 
                ("pitcher_cam", "Pitcher View"), 
                ("catcher_cam", "Catcher View"), 
                ("broadcaster_cam", "Broadcaster View")
            ]
                
            for cam_name, label in cameras:
                video_renderer.update_scene(env.data, camera=cam_name)
                # Copy frame to avoid reference issues
                cam_frame = video_renderer.render().copy()
                # Add label using cv2
                cv2.putText(cam_frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
                multi_frames.append(cam_frame)
            
            # Composite 2x2 Grid
            top_row = np.hstack((multi_frames[0], multi_frames[1]))
            bottom_row = np.hstack((multi_frames[2], multi_frames[3]))
            grid_frame = np.vstack((top_row, bottom_row))
            
            frames.append(grid_frame)
            
            step += 1

        if not frames:
            return ""

        # 'result' 키가 없을 수 있음 (UnifiedBaseballEnv vs BaseballGameEnv)
        result_str = info.get('result', info.get('game_event', 'UNKNOWN'))
        # 파일명에 안전한 문자만 사용
        result_str = result_str.replace(' ', '_').replace('/', '-')[:20]
        filename = self.save_dir / f"ep_{episode_idx:04d}_stage_{info.get('stage', 0)}_{result_str}.mp4"
        
        # OpenCV 비디오 저장 (BGR 변환 필요)
        height, width, _ = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        out = cv2.VideoWriter(str(filename), fourcc, self.fps, (width, height))
        if not out.isOpened():
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(str(filename), fourcc, self.fps, (width, height))

        for f in frames:
            # MuJoCo 렌더링은 RGB, OpenCV는 BGR
            out.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
        
        out.release()
        
        # Log to Dashboard
        logger = DashboardLogger()
        # Extract just the filename without directory path for the web frontend
        logger.log_video(episode_idx, info['stage'], filename.name)
        
        print(f"  🎬 에피소드 비디오 저장됨: {filename}")
        return str(filename)
