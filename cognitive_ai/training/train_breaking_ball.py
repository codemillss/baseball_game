import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback
from cognitive_ai.envs.breaking_ball_env import BreakingBallEnv

def train_breaking_balls():
    print("🚀 Training 3D Swing Policy on Breaking Balls (Fastball, Slider, Curveball)...")
    os.makedirs("./checkpoints/breaking_ball_best", exist_ok=True)
    
    def make_env():
        return BreakingBallEnv()
        
    vec_env = DummyVecEnv([make_env])
    vec_env = VecNormalize(vec_env, norm_obs=True, norm_reward=False, clip_obs=10.)
    
    eval_env = DummyVecEnv([make_env])
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
    
    eval_cb = EvalCallback(
        eval_env,
        best_model_save_path='./checkpoints/breaking_ball_best',
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
        ent_coef=0.01,
        gamma=0.99
    )
    
    model.learn(total_timesteps=100000, callback=eval_cb)
    model.save("./checkpoints/breaking_ball_final_model")
    vec_env.save("./checkpoints/breaking_ball_vec_normalize.pkl")
    print("🎉 Breaking Ball Training Complete!")

if __name__ == "__main__":
    train_breaking_balls()
