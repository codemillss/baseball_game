import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback
from cognitive_ai.envs.pitching_machine_env import PitchingMachineEnv

def train_curriculum():
    os.makedirs("./checkpoints/pitching_50kmh_best", exist_ok=True)
    os.makedirs("./checkpoints/pitching_80kmh_best", exist_ok=True)
    
    # ----------------------------------------------------
    # STAGE 1: 50~55 km/h Training (10m Distance)
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("🚀 STAGE 1: Training on 50~55 km/h Pitches (10m Distance)...")
    print("="*50)
    
    def make_env_50():
        return PitchingMachineEnv(target_speed_kmh=50)
        
    vec_env_50 = DummyVecEnv([make_env_50])
    vec_env_50 = VecNormalize(vec_env_50, norm_obs=True, norm_reward=False, clip_obs=10.)
    
    eval_env_50 = DummyVecEnv([make_env_50])
    eval_env_50 = VecNormalize(eval_env_50, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
    
    eval_cb_50 = EvalCallback(
        eval_env_50,
        best_model_save_path='./checkpoints/pitching_50kmh_best',
        eval_freq=2000,
        n_eval_episodes=20,
        deterministic=True
    )
    
    model_50 = PPO(
        "MlpPolicy",
        vec_env_50,
        verbose=1,
        learning_rate=1e-3,
        n_steps=1024,
        batch_size=64,
        ent_coef=0.005,
        gamma=0.99
    )
    
    model_50.learn(total_timesteps=60000, callback=eval_cb_50)
    model_50.save("./checkpoints/pitching_50kmh_final_model")
    vec_env_50.save("./checkpoints/pitching_50kmh_vec_normalize.pkl")
    print("✅ Stage 1 (50 km/h) Complete!")
    
    # ----------------------------------------------------
    # STAGE 2: 75~80 km/h Fine-tuning (15m Distance)
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("🚀 STAGE 2: Transferring & Training on 75~80 km/h Pitches (15m Distance)...")
    print("="*50)
    
    def make_env_80():
        return PitchingMachineEnv(target_speed_kmh=80)
        
    vec_env_80 = DummyVecEnv([make_env_80])
    vec_env_80 = VecNormalize(vec_env_80, norm_obs=True, norm_reward=False, clip_obs=10.)
    
    eval_env_80 = DummyVecEnv([make_env_80])
    eval_env_80 = VecNormalize(eval_env_80, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
    
    eval_cb_80 = EvalCallback(
        eval_env_80,
        best_model_save_path='./checkpoints/pitching_80kmh_best',
        eval_freq=2000,
        n_eval_episodes=20,
        deterministic=True
    )
    
    # Load Stage 1 weights and transfer to 80 km/h
    model_80 = PPO.load(
        "./checkpoints/pitching_50kmh_best/best_model",
        env=vec_env_80,
        learning_rate=1e-3,
        ent_coef=0.01
    )
    
    model_80.learn(total_timesteps=80000, callback=eval_cb_80)
    model_80.save("./checkpoints/pitching_80kmh_final_model")
    vec_env_80.save("./checkpoints/pitching_80kmh_vec_normalize.pkl")
    print("🎉 STAGE 2 (80 km/h) Curriculum Training Complete!")

if __name__ == "__main__":
    train_curriculum()
