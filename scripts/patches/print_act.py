from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from cognitive_ai.envs.baseball_match_env import BaseballMatchEnv
from cognitive_ai.envs.pitcher_env import PitcherEnv
import numpy as np

p_model = PPO.load("checkpoints/mocap_pitcher_best/best_model")

env = BaseballMatchEnv()
env.target_x = 0.0
env.target_z = 0.8
env.target_pitch_type = 0
obs = env.get_observations()
p_obs = obs["pitcher"]
print(f"p_obs: {p_obs}")

dummy = PitcherEnv()
p_norm = VecNormalize.load("checkpoints/mocap_pitcher_vec_normalize.pkl", DummyVecEnv([lambda: dummy]))
p_norm.training = False

# We must reshape p_obs to (1, 16)
p_norm_obs = p_norm.normalize_obs(p_obs.reshape(1, -1))
print(f"p_norm_obs: {p_norm_obs}")

p_action, _ = p_model.predict(p_norm_obs, deterministic=True)
print(f"p_action: {p_action}")
