import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.baseball_match_env import BaseballMatchEnv
from cognitive_ai.envs.pitcher_env import PitcherEnv

class BatterMatchTrainingEnv(gym.Env):
    """
    Gym wrapper for training Batter AI directly against the live trained Pitcher AI.
    """
    def __init__(self, pitcher_model_path="checkpoints/mlb_pitcher_best/best_model", pitcher_norm_path="checkpoints/mlb_pitcher_vec_normalize.pkl", is_eval_mode=False):
        super().__init__()
        self.match_env = BaseballMatchEnv(is_eval_mode=is_eval_mode)
        
        # Batter Observation Space (9-dim)
        self.observation_space = spaces.Box(low=-100.0, high=100.0, shape=(12,), dtype=np.float32)
        # Batter Action Space (3-dim): [trigger, z_delta, x_yaw]
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        
        # Load frozen Pitcher Policy
        def make_p_env(): return PitcherEnv()
        p_vec = DummyVecEnv([make_p_env])
        self.p_norm = VecNormalize.load(pitcher_norm_path, p_vec)
        self.p_norm.training = False
        self.p_norm.norm_reward = False
        self.pitcher_model = PPO.load(pitcher_model_path, env=p_vec)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        obs = self.match_env.reset(seed=seed)
        self.last_obs = obs
        return obs["batter"], {}

    def step(self, batter_action):
        # Pitcher acts according to its policy
        p_obs_norm = self.p_norm.normalize_obs(self.last_obs["pitcher"])
        p_action, _ = self.pitcher_model.predict(p_obs_norm, deterministic=False) # Add slight stochasticity for pitch variation
        
        obs, done, info = self.match_env.step(p_action, batter_action)
        self.last_obs = obs
        
        reward = 0.0
        if info["has_contacted"]:
            # Emphasize hitting!
            reward += 300.0 + min(info["exit_velocity_kmh"] * 8.0, 150.0) + min(info["batted_distance"] * 10.0, 100.0)
        elif done:
            if self.match_env.b_swing_active:
                # Swung and missed (Whiff)
                if info.get("is_in_strike_zone", True):
                    reward -= 50.0 # Whiff on strike
                else:
                    reward -= 100.0 # Swung at a bad pitch (Chased ball)
            else:
                # Didn't swing (Took pitch)
                if info.get("is_in_strike_zone", True):
                    reward -= 150.0 # Strikeout looking (Penalty)
                else:
                    reward += 150.0 # Good eye! (Walk / Took a ball)
                
        return obs["batter"], reward, done, False, info

def train_batter_against_pitcher():
    print("🚀 Training Batter Policy Directly Against Live 84.4 km/h Pitcher AI...")
    os.makedirs("./checkpoints/mlb_batter_best", exist_ok=True)
    
    def make_env():
        return BatterMatchTrainingEnv()
        
    vec_env = DummyVecEnv([make_env])
    vec_env = VecNormalize(vec_env, norm_obs=True, norm_reward=False, clip_obs=10.)
    
    model = PPO(
        "MlpPolicy",
        vec_env,
        verbose=1,
        learning_rate=1e-3,
        n_steps=1024,
        batch_size=64,
        ent_coef=0.01,
        gamma=0.99
    )
    
    model.learn(total_timesteps=150000)
    model.save("./checkpoints/mlb_batter_best/best_model")
    vec_env.save("./checkpoints/mlb_batter_vec_normalize.pkl")
    print("🎉 Match-Adapted Batter Training Complete!")

if __name__ == "__main__":
    train_batter_against_pitcher()
