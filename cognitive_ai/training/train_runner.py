import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize
from cognitive_ai.envs.runner_env import RunnerEnv

def make_env():
    return RunnerEnv()

if __name__ == "__main__":
    num_envs = 16
    env = SubprocVecEnv([make_env for _ in range(num_envs)])
    env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
    
    model = PPO("MlpPolicy", env, verbose=1, n_steps=512, batch_size=256,
                learning_rate=3e-4, clip_range=0.2, ent_coef=0.01)
                
    print("Training Runner...")
    model.learn(total_timesteps=100_000)
    
    os.makedirs("checkpoints/runner", exist_ok=True)
    model.save("checkpoints/runner/best_model")
    env.save("checkpoints/runner/vec_normalize.pkl")
    print("Runner training complete!")
