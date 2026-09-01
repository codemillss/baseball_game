import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import cv2
import mujoco
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from cognitive_ai.envs.catcher_env import CatcherEnv
from cognitive_ai.envs.runner_env import RunnerEnv

def main():
    print("Initializing Catcher and Runner Environments...")
    c_vec = DummyVecEnv([lambda: CatcherEnv()])
    c_vec = VecNormalize.load("checkpoints/catcher/vec_normalize.pkl", c_vec)
    c_vec.training = False
    c_vec.norm_reward = False
    
    r_vec = DummyVecEnv([lambda: RunnerEnv()])
    r_vec = VecNormalize.load("checkpoints/runner/vec_normalize.pkl", r_vec)
    r_vec.training = False
    r_vec.norm_reward = False

    print("Loading AI Models...")
    c_model = PPO.load("checkpoints/catcher/best_model")
    r_model = PPO.load("checkpoints/runner/best_model")

    c_env = c_vec.envs[0]
    r_env = r_vec.envs[0]
    
    # We will render using Runner's environment, but we will step both.
    # Actually, rendering both in one environment requires merging them into h1_baseball_match.xml!
    # For now, let's just do a quick unit test video of the Runner reaching 2nd base.
    renderer = mujoco.Renderer(r_env.model, 480, 640)
    
    os.makedirs("data/eval_videos", exist_ok=True)
    video_path = "data/eval_videos/phase_8_3_base_stealing.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, 60.0, (640, 480))

    print("=======================================================")
    print("🏃 RUNNER: STEALING 2ND BASE TEST")
    print("=======================================================")

    for i in range(1):
        r_norm_obs = r_vec.reset()
        done = False
        
        while not done:
            action, _ = r_model.predict(r_norm_obs, deterministic=True)
            r_norm_obs, reward, dones, infos = r_vec.step(action)
            done = dones[0]
            info = infos[0]
            
            renderer.update_scene(r_env.data, camera="tracking_cam")
            frame = renderer.render()
            
            dist = info.get("dist", 0.0)
            cv2.putText(frame, f"STEALING 2ND BASE | Dist: {dist:.1f}m", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            if done:
                if dist < 1.0:
                    cv2.putText(frame, "SAFE! (Base Stolen)", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "OUT! (Failed to reach)", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
            out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            if done:
                for _ in range(60):
                    out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                    
        print(f"Runner Attempt {i+1} Final Dist: {dist:.1f}m")

    out.release()
    print("=======================================================")
    print(f"🎥 Video saved to: {video_path}")

if __name__ == "__main__":
    main()
