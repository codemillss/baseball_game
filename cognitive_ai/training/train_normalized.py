import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback
from cognitive_ai.envs.soft_toss_env import SoftTossEnv

def train_normalized():
    print("🚀 Training Soft-Toss with VecNormalize...")
    
    def make_env():
        return SoftTossEnv()
        
    vec_env = DummyVecEnv([make_env])
    vec_env = VecNormalize(vec_env, norm_obs=True, norm_reward=False, clip_obs=10.)
    
    eval_env = DummyVecEnv([make_env])
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
    
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path='./checkpoints/soft_toss_best_model',
        eval_freq=2000,
        n_eval_episodes=20,
        deterministic=True
    )
    
    model = PPO(
        "MlpPolicy",
        vec_env,
        verbose=1,
        learning_rate=1e-3,
        n_steps=1024,
        batch_size=64,
        ent_coef=0.005,
        gamma=0.99
    )
    
    model.learn(total_timesteps=80000, callback=eval_callback)
    model.save("./checkpoints/soft_toss_final_model")
    vec_env.save("./checkpoints/soft_toss_vec_normalize.pkl")
    print("✅ Training Complete with VecNormalize!")

if __name__ == "__main__":
    train_normalized()
