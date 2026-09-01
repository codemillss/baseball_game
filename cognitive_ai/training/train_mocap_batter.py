import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback
from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv

def train_batter():
    print("🚀 Fine-tuning MoCap Batter Policy (Ohtani Style Kinematics)...")
    os.makedirs("./checkpoints/mocap_batter_best", exist_ok=True)
    
    # We load the mocap_pitcher_best so the Batter faces the MoCap pitcher!
    def make_env():
        return BatterMatchTrainingEnv(
            pitcher_model_path="checkpoints/mocap_pitcher_best/best_model",
            pitcher_norm_path="checkpoints/mocap_pitcher_vec_normalize.pkl"
        )
        
    vec_env = DummyVecEnv([make_env])
    vec_env = VecNormalize.load("./checkpoints/mlb_batter_vec_normalize.pkl", vec_env)
    vec_env.training = True
    vec_env.norm_reward = False
    
    eval_env = DummyVecEnv([make_env])
    eval_env = VecNormalize.load("./checkpoints/mlb_batter_vec_normalize.pkl", eval_env)
    eval_env.training = False
    eval_env.norm_reward = False
    
    eval_cb = EvalCallback(
        eval_env,
        best_model_save_path='./checkpoints/mocap_batter_best',
        eval_freq=2000,
        n_eval_episodes=25,
        deterministic=True
    )
    
    print("Loading pre-trained mlb_batter_best...")
    model = PPO.load("./checkpoints/mlb_batter_best/best_model", env=vec_env, custom_objects={
        "learning_rate": 5e-4,
        "ent_coef": 0.05
    })
    
    # Fine-tune for 60k steps
    model.learn(total_timesteps=60000, callback=eval_cb)
    vec_env.save("./checkpoints/mocap_batter_vec_normalize.pkl")
    print("🎉 MoCap Batter Fine-tuning Complete!")

if __name__ == "__main__":
    train_batter()
