import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback
from cognitive_ai.envs.pitching_machine_env import PitchingMachineEnv

def train_80kmh_deep():
    print("🚀 Deep Training on 80 km/h Pitches (150k steps)...")
    
    def make_env():
        return PitchingMachineEnv(target_speed_kmh=80)
        
    vec_env = DummyVecEnv([make_env])
    vec_env = VecNormalize(vec_env, norm_obs=True, norm_reward=False, clip_obs=10.)
    
    eval_env = DummyVecEnv([make_env])
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10., training=False)
    
    eval_cb = EvalCallback(
        eval_env,
        best_model_save_path='./checkpoints/pitching_80kmh_deep_best',
        eval_freq=2500,
        n_eval_episodes=30,
        deterministic=True
    )
    
    model = PPO(
        "MlpPolicy",
        vec_env,
        verbose=1,
        learning_rate=5e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        ent_coef=0.01,
        gamma=0.99
    )
    
    model.learn(total_timesteps=150000, callback=eval_cb)
    model.save("./checkpoints/pitching_80kmh_deep_final")
    vec_env.save("./checkpoints/pitching_80kmh_deep_norm.pkl")
    print("✅ Deep 80 km/h Training Complete!")

if __name__ == "__main__":
    train_80kmh_deep()
