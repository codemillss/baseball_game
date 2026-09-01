import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback
from cognitive_ai.envs.pitcher_env import PitcherEnv

def train_pitcher():
    print("🚀 Fine-tuning MoCap Pitcher Policy (Ohtani Style Kinematics)...")
    os.makedirs("./checkpoints/mocap_pitcher_best", exist_ok=True)
    
    def make_env():
        return PitcherEnv()
        
    vec_env = DummyVecEnv([make_env])
    # Load old VecNormalize
    vec_env = VecNormalize.load("./checkpoints/mlb_pitcher_vec_normalize.pkl", vec_env)
    vec_env.training = True
    vec_env.norm_reward = False
    
    eval_env = DummyVecEnv([make_env])
    eval_env = VecNormalize.load("./checkpoints/mlb_pitcher_vec_normalize.pkl", eval_env)
    eval_env.training = False
    eval_env.norm_reward = False
    
    eval_cb = EvalCallback(
        eval_env,
        best_model_save_path='./checkpoints/mocap_pitcher_best',
        eval_freq=2000,
        n_eval_episodes=25,
        deterministic=True
    )
    
    # Load old pre-trained model!
    print("Loading pre-trained mlb_pitcher_best...")
    model = PPO.load("./checkpoints/mlb_pitcher_best/best_model", env=vec_env, custom_objects={
        "learning_rate": 5e-4, # Lower LR for fine-tuning
        "ent_coef": 0.05       # Slight exploration to find new aim points
    })
    
    # Fine-tune for only 50k steps (since it already knows how to pitch!)
    model.learn(total_timesteps=60000, callback=eval_cb)
    vec_env.save("./checkpoints/mocap_pitcher_vec_normalize.pkl")
    print("🎉 MoCap Pitcher Fine-tuning Complete!")

if __name__ == "__main__":
    train_pitcher()
