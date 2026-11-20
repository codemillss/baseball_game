# baseball/cognitive_ai/training/train_mlb_batter.py

원본: [cognitive_ai/training/train_mlb_batter.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_mlb_batter.py)

SHA256: `35d2762db01ccab1f454c814beea13e1e6eacb950e56a0403910a9e58dd47444`

전체 96행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BatterMatchTrainingEnv` | ClassDef | 14 | 67 |
| `__init__` | FunctionDef | 18 | 33 |
| `make_p_env` | FunctionDef | 28 | 28 |
| `reset` | FunctionDef | 35 | 39 |
| `step` | FunctionDef | 41 | 67 |
| `train_batter_against_pitcher` | FunctionDef | 69 | 93 |
| `make_env` | FunctionDef | 73 | 74 |

## 전체 원문

````text
    1 | import gymnasium as gym
    2 | from gymnasium import spaces
    3 | import mujoco
    4 | import numpy as np
    5 | from stable_baselines3 import PPO
    6 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    7 | import os
    8 | import sys
    9 | 
   10 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
   11 | from cognitive_ai.envs.baseball_match_env import BaseballMatchEnv
   12 | from cognitive_ai.envs.pitcher_env import PitcherEnv
   13 | 
   14 | class BatterMatchTrainingEnv(gym.Env):
   15 |     """
   16 |     Gym wrapper for training Batter AI directly against the live trained Pitcher AI.
   17 |     """
   18 |     def __init__(self, pitcher_model_path="checkpoints/mlb_pitcher_best/best_model", pitcher_norm_path="checkpoints/mlb_pitcher_vec_normalize.pkl", is_eval_mode=False):
   19 |         super().__init__()
   20 |         self.match_env = BaseballMatchEnv(is_eval_mode=is_eval_mode)
   21 |         
   22 |         # Batter Observation Space (9-dim)
   23 |         self.observation_space = spaces.Box(low=-100.0, high=100.0, shape=(12,), dtype=np.float32)
   24 |         # Batter Action Space (3-dim): [trigger, z_delta, x_yaw]
   25 |         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
   26 |         
   27 |         # Load frozen Pitcher Policy
   28 |         def make_p_env(): return PitcherEnv()
   29 |         p_vec = DummyVecEnv([make_p_env])
   30 |         self.p_norm = VecNormalize.load(pitcher_norm_path, p_vec)
   31 |         self.p_norm.training = False
   32 |         self.p_norm.norm_reward = False
   33 |         self.pitcher_model = PPO.load(pitcher_model_path, env=p_vec)
   34 | 
   35 |     def reset(self, seed=None, options=None):
   36 |         super().reset(seed=seed)
   37 |         obs = self.match_env.reset(seed=seed)
   38 |         self.last_obs = obs
   39 |         return obs["batter"], {}
   40 | 
   41 |     def step(self, batter_action):
   42 |         # Pitcher acts according to its policy
   43 |         p_obs_norm = self.p_norm.normalize_obs(self.last_obs["pitcher"])
   44 |         p_action, _ = self.pitcher_model.predict(p_obs_norm, deterministic=False) # Add slight stochasticity for pitch variation
   45 |         
   46 |         obs, done, info = self.match_env.step(p_action, batter_action)
   47 |         self.last_obs = obs
   48 |         
   49 |         reward = 0.0
   50 |         if info["has_contacted"]:
   51 |             # Emphasize hitting!
   52 |             reward += 300.0 + min(info["exit_velocity_kmh"] * 8.0, 150.0) + min(info["batted_distance"] * 10.0, 100.0)
   53 |         elif done:
   54 |             if self.match_env.b_swing_active:
   55 |                 # Swung and missed (Whiff)
   56 |                 if info.get("is_in_strike_zone", True):
   57 |                     reward -= 50.0 # Whiff on strike
   58 |                 else:
   59 |                     reward -= 100.0 # Swung at a bad pitch (Chased ball)
   60 |             else:
   61 |                 # Didn't swing (Took pitch)
   62 |                 if info.get("is_in_strike_zone", True):
   63 |                     reward -= 150.0 # Strikeout looking (Penalty)
   64 |                 else:
   65 |                     reward += 150.0 # Good eye! (Walk / Took a ball)
   66 |                 
   67 |         return obs["batter"], reward, done, False, info
   68 | 
   69 | def train_batter_against_pitcher():
   70 |     print("🚀 Training Batter Policy Directly Against Live 84.4 km/h Pitcher AI...")
   71 |     os.makedirs("./checkpoints/mlb_batter_best", exist_ok=True)
   72 |     
   73 |     def make_env():
   74 |         return BatterMatchTrainingEnv()
   75 |         
   76 |     vec_env = DummyVecEnv([make_env])
   77 |     vec_env = VecNormalize(vec_env, norm_obs=True, norm_reward=False, clip_obs=10.)
   78 |     
   79 |     model = PPO(
   80 |         "MlpPolicy",
   81 |         vec_env,
   82 |         verbose=1,
   83 |         learning_rate=1e-3,
   84 |         n_steps=1024,
   85 |         batch_size=64,
   86 |         ent_coef=0.01,
   87 |         gamma=0.99
   88 |     )
   89 |     
   90 |     model.learn(total_timesteps=150000)
   91 |     model.save("./checkpoints/mlb_batter_best/best_model")
   92 |     vec_env.save("./checkpoints/mlb_batter_vec_normalize.pkl")
   93 |     print("🎉 Match-Adapted Batter Training Complete!")
   94 | 
   95 | if __name__ == "__main__":
   96 |     train_batter_against_pitcher()
````
