import sys
import os
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize, VecFrameStack
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.utils import set_random_seed
from typing import Callable

# Import environments
from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
from cognitive_ai.envs.pitcher_env import PitcherEnv

def linear_schedule(initial_value: float) -> Callable[[float], float]:
    """
    Linear learning rate schedule.
    :param initial_value: Initial learning rate.
    :return: schedule that computes current learning rate depending on remaining progress
    """
    def func(progress_remaining: float) -> float:
        """
        Progress will decrease from 1 (beginning) to 0.
        """
        return progress_remaining * initial_value
    return func

def make_batter_env(seed, rank):
    def _init():
        env = BatterMatchTrainingEnv()
        env.reset(seed=seed + rank)
        return env
    return _init

def make_pitcher_env(seed, rank):
    def _init():
        env = PitcherEnv()
        env.reset(seed=seed + rank)
        return env
    return _init

def train_mega_batter():
    print("==================================================")
    print("🔥 STARTING MEGA TRAINING: BATTER (FRAME STACKING) 🔥")
    print("==================================================")
    
    num_envs = 16
    env = SubprocVecEnv([make_batter_env(42, i) for i in range(num_envs)])
    env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
    
    # NEW ARCHITECTURE: Frame Stacking (4 frames) to detect curveball spin/acceleration
    env = VecFrameStack(env, n_stack=4)
    
    eval_env = SubprocVecEnv([make_batter_env(42, 99)])
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=True, clip_obs=10.)
    eval_env = VecFrameStack(eval_env, n_stack=4)
    
    os.makedirs("checkpoints/mega_batter", exist_ok=True)
    
    # Auto-evaluator callback
    eval_callback = EvalCallback(eval_env, best_model_save_path='checkpoints/mega_batter/',
                                 log_path='checkpoints/mega_batter/logs/', eval_freq=20000,
                                 deterministic=True, render=False)
    
    model = PPO("MlpPolicy", env, verbose=1, 
                n_steps=2048, batch_size=512, 
                learning_rate=linear_schedule(5e-4), # Annealing LR
                clip_range=0.2, ent_coef=0.01,
                tensorboard_log="checkpoints/mega_batter/tb_logs/")
                
    model.learn(total_timesteps=2_000_000, callback=eval_callback)
    env.save("checkpoints/mega_batter/vec_normalize.pkl")
    print("Mega Batter Training Complete!")

def train_mega_pitcher():
    print("==================================================")
    print("🔥 STARTING MEGA TRAINING: PITCHER (ANNEALING) 🔥")
    print("==================================================")
    
    num_envs = 16
    env = SubprocVecEnv([make_pitcher_env(42, i) for i in range(num_envs)])
    env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
    
    eval_env = SubprocVecEnv([make_pitcher_env(42, 99)])
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=True, clip_obs=10.)
    
    os.makedirs("checkpoints/mega_pitcher", exist_ok=True)
    
    eval_callback = EvalCallback(eval_env, best_model_save_path='checkpoints/mega_pitcher/',
                                 log_path='checkpoints/mega_pitcher/logs/', eval_freq=20000,
                                 deterministic=True, render=False)
                                 
    model = PPO("MlpPolicy", env, verbose=1, 
                n_steps=1024, batch_size=256, 
                learning_rate=linear_schedule(3e-4), 
                clip_range=0.2, ent_coef=0.01,
                tensorboard_log="checkpoints/mega_pitcher/tb_logs/")
                
    model.learn(total_timesteps=2_000_000, callback=eval_callback)
    env.save("checkpoints/mega_pitcher/vec_normalize.pkl")
    print("Mega Pitcher Training Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", type=str, choices=["batter", "pitcher", "both"], default="both")
    args = parser.parse_args()
    
    if args.role in ["pitcher", "both"]:
        train_mega_pitcher()
    if args.role in ["batter", "both"]:
        train_mega_batter()
