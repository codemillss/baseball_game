from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
import numpy as np

def make_b_env(): 
    return BatterMatchTrainingEnv(
        pitcher_model_path="checkpoints/mocap_pitcher_best/best_model",
        pitcher_norm_path="checkpoints/mocap_pitcher_vec_normalize.pkl",
        is_eval_mode=True
    )

b_vec = DummyVecEnv([make_b_env])
b_norm = VecNormalize.load("checkpoints/mocap_batter_vec_normalize.pkl", b_vec)
b_norm.training = False
b_norm.norm_reward = False

b_model = PPO.load("checkpoints/mocap_batter_best/best_model", env=b_norm)

b_env = b_vec.envs[0].match_env

obs = b_vec.reset()
done = False

step = 0
while not done:
    action, _ = b_model.predict(obs, deterministic=True)
    obs, reward, dones, infos = b_vec.step(action)
    done = dones[0]
    info = infos[0]
    
    print(f"Step {step}: p_throw_progress={b_env.p_throw_progress:.3f}, is_rel={b_env.is_released}, pitch_speed={b_env.pitch_speed_kmh:.1f}, ball_y={b_env.data.qpos[b_env.ball_qpos_adr+1]:.1f}")
    step += 1

print("Done! Outcome:", info.get('outcome'))
