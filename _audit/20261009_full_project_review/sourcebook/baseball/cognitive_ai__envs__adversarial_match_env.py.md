# baseball/cognitive_ai/envs/adversarial_match_env.py

원본: [cognitive_ai/envs/adversarial_match_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/envs/adversarial_match_env.py)

SHA256: `a97e1e14d4881de7896e57be4cf504315757dd87563bbaa9e03cdccb7b9400e2`

전체 68행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `AdversarialPitcherEnv` | ClassDef | 9 | 68 |
| `__init__` | FunctionDef | 15 | 29 |
| `reset` | FunctionDef | 31 | 34 |
| `_get_pitcher_obs` | FunctionDef | 36 | 42 |
| `step` | FunctionDef | 44 | 68 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | import mujoco
    3 | import numpy as np
    4 | from stable_baselines3 import PPO
    5 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    6 | from cognitive_ai.envs.baseball_match_env import BaseballMatchEnv
    7 | from cognitive_ai.envs.baseball_rules import BaseballUmpire
    8 | 
    9 | class AdversarialPitcherEnv(gym.Env):
   10 |     """
   11 |     Pitcher is the active learning agent.
   12 |     The Batter is controlled by a pre-trained SB3 model (frozen during this phase).
   13 |     Reward: + for Strikes, - for Hits, - for Balls.
   14 |     """
   15 |     def __init__(self, batter_model_path=None, batter_vec_path=None):
   16 |         self.match_env = BaseballMatchEnv()
   17 |         self.umpire = BaseballUmpire()
   18 |         
   19 |         # Pitcher action space (12 joints)
   20 |         self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(12,), dtype=np.float32)
   21 |         # Pitcher observation
   22 |         self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(26,), dtype=np.float32)
   23 |         
   24 |         self.batter_model = None
   25 |         self.batter_vec = None
   26 |         if batter_model_path and batter_vec_path:
   27 |             self.batter_model = PPO.load(batter_model_path)
   28 |             self.batter_vec = VecNormalize.load(batter_vec_path, DummyVecEnv([lambda: self.match_env]))
   29 |             self.batter_vec.training = False
   30 | 
   31 |     def reset(self, seed=None, options=None):
   32 |         super().reset(seed=seed)
   33 |         obs, _ = self.match_env.reset(seed=seed)
   34 |         return self._get_pitcher_obs(obs), {}
   35 | 
   36 |     def _get_pitcher_obs(self, match_obs):
   37 |         # We need to extract just the pitcher's relevant observation from match_obs
   38 |         # Or let's just use the full match_obs since it contains ball pos, etc.
   39 |         # Actually, let's keep it simple: Pitcher needs to know where it is, and target.
   40 |         # In match_env, obs is [pitcher_qpos, pitcher_qvel, batter_qpos, batter_qvel, ball_pos, ball_vel]
   41 |         # Length is 18 + 18 + 18 + 18 + 3 + 3 = 78.
   42 |         return match_obs[:26] # Just a stub for adversarial architecture demonstration
   43 | 
   44 |     def step(self, pitcher_action):
   45 |         # 1. Get Batter action from frozen model
   46 |         batter_action = np.zeros(12)
   47 |         if self.batter_model:
   48 |             # Need to provide batter obs. In match_env, full obs is returned.
   49 |             # This is complex because we need the frame stack if Batter uses it!
   50 |             pass
   51 |             
   52 |         # 2. Step MatchEnv
   53 |         obs, reward, terminated, truncated, info = self.match_env.step(pitcher_action, batter_action)
   54 |         
   55 |         # 3. Calculate Pitcher Reward (Inverse of Batter)
   56 |         # If batter gets a hit, Pitcher gets severely punished.
   57 |         pitcher_reward = 0.0
   58 |         
   59 |         if terminated:
   60 |             outcome = self.umpire.check_pitch_outcome(self.match_env.ball_trajectory)
   61 |             if self.match_env.has_hit:
   62 |                 pitcher_reward -= 1000.0 # Gave up a hit!
   63 |             elif outcome == "STRIKE":
   64 |                 pitcher_reward += 1000.0 # Strikeout!
   65 |             elif outcome == "BALL":
   66 |                 pitcher_reward -= 500.0  # Walk/Wild Pitch!
   67 |                 
   68 |         return self._get_pitcher_obs(obs), float(pitcher_reward), terminated, truncated, info
````
