import numpy as np
import mujoco
from cognitive_ai.envs.pitcher_env import PitcherEnv
from cognitive_ai.envs.baseball_match_env import BaseballMatchEnv

p_env = PitcherEnv()
p_env.reset()
obs1 = p_env._get_obs()

b_env = BaseballMatchEnv()
b_env.reset()
obs2, _ = b_env.get_observations()

print(f"PitcherEnv obs shape: {obs1.shape}")
print(f"BaseballMatchEnv obs shape: {obs2.shape}")

print("PitcherEnv Obs:", obs1)
print("BaseballMatchEnv Obs:", obs2)
