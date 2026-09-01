import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback
from cognitive_ai.envs.pitcher_env import PitcherEnv

def train_pitcher():
    print("🚀 Training Humanoid Pitcher Policy (Release & Strike Zone Control)...")
    os.makedirs("./checkpoints/pitcher_best", exist_ok=True)
    
    def make_env():
        return PitcherEnv()
        
    vec_env = DummyVecEnv([make_env])
    vec_env = VecNormalize(vec_env, norm_obs=True, norm_reward=False, clip_obs=10.)
    
    eval_env = DummyVecEnv([make_env])
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
    
    eval_cb = EvalCallback(
        eval_env,
        best_model_save_path='./checkpoints/pitcher_best',
        eval_freq=2000,
        n_eval_episodes=25,
        deterministic=True
    )
    
    model = PPO(
        "MlpPolicy",
        vec_env,
        verbose=1,
        learning_rate=1e-3,
        n_steps=1024,
        batch_size=64,
        n_epochs=10,
        ent_coef=0.01,
        gamma=0.99
    )
    
    model.learn(total_timesteps=80000, callback=eval_cb)
    model.save("./checkpoints/pitcher_final_model")
    vec_env.save("./checkpoints/pitcher_vec_normalize.pkl")
    print("🎉 Pitcher Training Complete!")

if __name__ == "__main__":
    train_pitcher()
