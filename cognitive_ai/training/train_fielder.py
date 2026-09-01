import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback

from cognitive_ai.envs.fielder_env import FielderEnv

def main():
    env = DummyVecEnv([lambda: FielderEnv()])
    env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
    
    os.makedirs("checkpoints/fielder", exist_ok=True)
    
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=256,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=1,
        device="cpu"
    )
    
    model.learn(total_timesteps=300000)
    
    model.save("checkpoints/fielder/best_model")
    env.save("checkpoints/fielder/vec_normalize.pkl")
    print("Fielder training complete!")

if __name__ == "__main__":
    main()
