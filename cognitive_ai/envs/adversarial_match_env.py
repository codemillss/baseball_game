import gymnasium as gym
import mujoco
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from cognitive_ai.envs.baseball_match_env import BaseballMatchEnv
from cognitive_ai.envs.baseball_rules import BaseballUmpire

class AdversarialPitcherEnv(gym.Env):
    """
    Pitcher is the active learning agent.
    The Batter is controlled by a pre-trained SB3 model (frozen during this phase).
    Reward: + for Strikes, - for Hits, - for Balls.
    """
    def __init__(self, batter_model_path=None, batter_vec_path=None):
        self.match_env = BaseballMatchEnv()
        self.umpire = BaseballUmpire()
        
        # Pitcher action space (12 joints)
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(12,), dtype=np.float32)
        # Pitcher observation
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(26,), dtype=np.float32)
        
        self.batter_model = None
        self.batter_vec = None
        if batter_model_path and batter_vec_path:
            self.batter_model = PPO.load(batter_model_path)
            self.batter_vec = VecNormalize.load(batter_vec_path, DummyVecEnv([lambda: self.match_env]))
            self.batter_vec.training = False

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        obs, _ = self.match_env.reset(seed=seed)
        return self._get_pitcher_obs(obs), {}

    def _get_pitcher_obs(self, match_obs):
        # We need to extract just the pitcher's relevant observation from match_obs
        # Or let's just use the full match_obs since it contains ball pos, etc.
        # Actually, let's keep it simple: Pitcher needs to know where it is, and target.
        # In match_env, obs is [pitcher_qpos, pitcher_qvel, batter_qpos, batter_qvel, ball_pos, ball_vel]
        # Length is 18 + 18 + 18 + 18 + 3 + 3 = 78.
        return match_obs[:26] # Just a stub for adversarial architecture demonstration

    def step(self, pitcher_action):
        # 1. Get Batter action from frozen model
        batter_action = np.zeros(12)
        if self.batter_model:
            # Need to provide batter obs. In match_env, full obs is returned.
            # This is complex because we need the frame stack if Batter uses it!
            pass
            
        # 2. Step MatchEnv
        obs, reward, terminated, truncated, info = self.match_env.step(pitcher_action, batter_action)
        
        # 3. Calculate Pitcher Reward (Inverse of Batter)
        # If batter gets a hit, Pitcher gets severely punished.
        pitcher_reward = 0.0
        
        if terminated:
            outcome = self.umpire.check_pitch_outcome(self.match_env.ball_trajectory)
            if self.match_env.has_hit:
                pitcher_reward -= 1000.0 # Gave up a hit!
            elif outcome == "STRIKE":
                pitcher_reward += 1000.0 # Strikeout!
            elif outcome == "BALL":
                pitcher_reward -= 500.0  # Walk/Wild Pitch!
                
        return self._get_pitcher_obs(obs), float(pitcher_reward), terminated, truncated, info
