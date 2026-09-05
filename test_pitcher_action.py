from cognitive_ai.envs.pitcher_env import PitcherEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
import numpy as np

env = DummyVecEnv([lambda: PitcherEnv()])
env = VecNormalize.load("checkpoints/mocap_pitcher_vec_normalize.pkl", env)
env.training = False

model = PPO.load("checkpoints/mocap_pitcher_best/best_model")

obs = env.reset()
action, _ = model.predict(obs, deterministic=True)
print(f"PitcherEnv action: {action}")

from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
b_env = DummyVecEnv([lambda: BatterMatchTrainingEnv(
    pitcher_model_path="checkpoints/mocap_pitcher_best/best_model",
    pitcher_norm_path="checkpoints/mocap_pitcher_vec_normalize.pkl"
)])
b_obs = b_env.reset()
# We can access pitcher action by stepping once
b_env.step(np.array([[0.0, 0.0, 0.0]]))
print(f"BatterMatchTrainingEnv stepped successfully!")

