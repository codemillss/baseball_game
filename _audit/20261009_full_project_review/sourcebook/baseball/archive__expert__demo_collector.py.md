# baseball/archive/expert/demo_collector.py

원본: [archive/expert/demo_collector.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/expert/demo_collector.py)

SHA256: `0103843142fa6a5d595fe03f77910e48ea0d9b108eaba8a00570210f2382b40d`

전체 112행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `ExpertDemoCollector` | ClassDef | 19 | 103 |
| `__init__` | FunctionDef | 22 | 28 |
| `collect_demos` | FunctionDef | 30 | 103 |
| `main` | FunctionDef | 106 | 108 |

## 전체 원문

````text
    1 | """
    2 | demo_collector.py — Expert Demonstration Dataset Collector
    3 | 
    4 | Analytical Physics IK Solver 기반의 Rule-based Expert Bot을 구동하여
    5 | Stage 1 Behavioral Cloning (BC) pre-training에 사용되는 고품질
    6 | Expert State-Action Trajectory 데이터셋(.npz)을 자동 수집합니다.
    7 | """
    8 | 
    9 | import os
   10 | from pathlib import Path
   11 | from typing import Optional, Dict, List
   12 | 
   13 | import numpy as np
   14 | 
   15 | from envs.mujoco_baseball_env import MuJoCoBaseballEnv
   16 | from expert.trajectory_solver import AnalyticalTrajectorySolver
   17 | 
   18 | 
   19 | class ExpertDemoCollector:
   20 |     """고품질 전문가 스윙 데이터 수집기."""
   21 | 
   22 |     def __init__(self, output_dir: Optional[str] = None):
   23 |         if output_dir is None:
   24 |             output_dir = str(Path(__file__).parent.parent / "data" / "expert_demos")
   25 | 
   26 |         self.output_dir = Path(output_dir)
   27 |         self.output_dir.mkdir(parents=True, exist_ok=True)
   28 |         self.solver = AnalyticalTrajectorySolver()
   29 | 
   30 |     def collect_demos(self, n_episodes: int = 100, save_filename: str = "expert_demos.npz") -> str:
   31 |         """N개의 에피소드에서 전문가 스윙 데이터 트래젝토리를 수집합니다.
   32 | 
   33 |         Returns:
   34 |             저장된 .npz 데이터셋 파일 경로
   35 |         """
   36 |         env = MuJoCoBaseballEnv()
   37 | 
   38 |         obs_list: List[np.ndarray] = []
   39 |         action_list: List[np.ndarray] = []
   40 |         reward_list: List[float] = []
   41 | 
   42 |         total_contacts = 0
   43 |         total_episodes = 0
   44 | 
   45 |         print(f"⚾ Expert Demo 수집 시작 ({n_episodes} episodes)...")
   46 | 
   47 |         for ep in range(n_episodes):
   48 |             obs, info = env.reset()
   49 |             done = False
   50 | 
   51 |             # 초기 위치/속도로 궤적 역산
   52 |             ball_pos = obs[0:3]
   53 |             ball_vel = obs[3:6]
   54 |             t_impact, impact_pos, _ = self.solver.solve_pitch_impact(ball_pos, ball_vel)
   55 | 
   56 |             ep_steps = 0
   57 |             while not done:
   58 |                 # 잔여 시간 계산
   59 |                 time_remaining = t_impact - (ep_steps * 0.002 * env.frame_skip)
   60 | 
   61 |                 # IK 스윙 액션 산출
   62 |                 action = self.solver.solve_inverse_kinematics_swing(obs, impact_pos, time_remaining)
   63 | 
   64 |                 next_obs, reward, terminated, truncated, step_info = env.step(action)
   65 |                 done = terminated or truncated
   66 | 
   67 |                 # 데이터 수집 (정타/스윙 구간 위주)
   68 |                 obs_list.append(obs)
   69 |                 action_list.append(action)
   70 |                 reward_list.append(reward)
   71 | 
   72 |                 obs = next_obs
   73 |                 ep_steps += 1
   74 | 
   75 |                 if step_info.get('has_contacted', False):
   76 |                     total_contacts += 1
   77 | 
   78 |             total_episodes += 1
   79 |             if (ep + 1) % max(1, n_episodes // 5) == 0:
   80 |                 print(f"   [{ep+1}/{n_episodes}] Contact Rate: {total_contacts/total_episodes:.1%}")
   81 | 
   82 |         env.close()
   83 | 
   84 |         # NumPy 배열 변환
   85 |         obs_arr = np.array(obs_list, dtype=np.float32)
   86 |         act_arr = np.array(action_list, dtype=np.float32)
   87 |         rew_arr = np.array(reward_list, dtype=np.float32)
   88 | 
   89 |         save_path = self.output_dir / save_filename
   90 |         np.savez_compressed(
   91 |             save_path,
   92 |             observations=obs_arr,
   93 |             actions=act_arr,
   94 |             rewards=rew_arr,
   95 |             n_episodes=n_episodes,
   96 |             contact_rate=total_contacts / total_episodes,
   97 |         )
   98 | 
   99 |         print(f"💾 Expert Demo 데이터셋 저장 완료: {save_path}")
  100 |         print(f"   - 총 Samples: {len(obs_arr):,}개")
  101 |         print(f"   - Final Contact Rate: {total_contacts/total_episodes:.1%}")
  102 | 
  103 |         return str(save_path)
  104 | 
  105 | 
  106 | def main():
  107 |     collector = ExpertDemoCollector()
  108 |     collector.collect_demos(n_episodes=100)
  109 | 
  110 | 
  111 | if __name__ == '__main__':
  112 |     main()
````
