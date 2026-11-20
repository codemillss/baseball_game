# baseball/cognitive_ai/training/train_match_batter.py

원본: [cognitive_ai/training/train_match_batter.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/training/train_match_batter.py)

SHA256: `c507fe79d41f46f78cf79f2449ada96c3b2c369bf7f448592adcfd45e17b03ea`

전체 87행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BatterMatchTrainingEnv` | ClassDef | 14 | 58 |
| `__init__` | FunctionDef | 18 | 33 |
| `make_p_env` | FunctionDef | 28 | 28 |
| `reset` | FunctionDef | 35 | 39 |
| `step` | FunctionDef | 41 | 58 |
| `train_batter_against_pitcher` | FunctionDef | 60 | 84 |
| `make_env` | FunctionDef | 64 | 65 |

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
   18 |     def __init__(self, pitcher_model_path="checkpoints/pitcher_best/best_model", pitcher_norm_path="checkpoints/pitcher_vec_normalize.pkl"):
   19 |         super().__init__()
   20 |         self.match_env = BaseballMatchEnv()
   21 |         
   22 |         # Batter Observation Space (9-dim)
   23 |         self.observation_space = spaces.Box(low=-100.0, high=100.0, shape=(9,), dtype=np.float32)
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
   51 |             reward += 200.0 + min(info["exit_velocity_kmh"] * 5.0, 100.0) + min(info["batted_distance"] * 5.0, 50.0)
   52 |         elif done:
   53 |             if self.match_env.b_swing_active:
   54 |                 reward -= 30.0 # Whiff penalty
   55 |             else:
   56 |                 reward -= 50.0 # Called strike penalty
   57 |                 
   58 |         return obs["batter"], reward, done, False, info
   59 | 
   60 | def train_batter_against_pitcher():
   61 |     print("🚀 Training Batter Policy Directly Against Live 84.4 km/h Pitcher AI...")
   62 |     os.makedirs("./checkpoints/match_batter_best", exist_ok=True)
   63 |     
   64 |     def make_env():
   65 |         return BatterMatchTrainingEnv()
   66 |         
   67 |     vec_env = DummyVecEnv([make_env])
   68 |     vec_env = VecNormalize(vec_env, norm_obs=True, norm_reward=False, clip_obs=10.)
   69 |     
   70 |     model = PPO(
   71 |         "MlpPolicy",
   72 |         vec_env,
   73 |         verbose=1,
   74 |         learning_rate=1e-3,
   75 |         n_steps=1024,
   76 |         batch_size=64,
   77 |         ent_coef=0.01,
   78 |         gamma=0.99
   79 |     )
   80 |     
   81 |     model.learn(total_timesteps=60000)
   82 |     model.save("./checkpoints/match_batter_best/best_model")
   83 |     vec_env.save("./checkpoints/match_batter_vec_normalize.pkl")
   84 |     print("🎉 Match-Adapted Batter Training Complete!")
   85 | 
   86 | if __name__ == "__main__":
   87 |     train_batter_against_pitcher()
````
