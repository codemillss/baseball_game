import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
import mujoco
import numpy as np
import cv2

from cognitive_ai.envs.fielder_env import FielderEnv

def main():
    env = DummyVecEnv([lambda: FielderEnv()])
    env = VecNormalize.load("checkpoints/fielder/vec_normalize.pkl", env)
    env.training = False
    env.norm_reward = False
    
    model = PPO.load("checkpoints/fielder/best_model", env=env)
    
    f_env = env.envs[0]
    renderer = mujoco.Renderer(f_env.model, 480, 640)
    
    os.makedirs("data/eval_videos", exist_ok=True)
    video_path = "data/eval_videos/phase_7_1_wheeled_fielder.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, 60.0, (640, 480))
    
    print("=======================================================")
    print("🏟️  WHEELED FIELDER CATCH TEST")
    print("=======================================================")
    
    catches = 0
    attempts = 5
    
    for i in range(attempts):
        obs = env.reset()
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, dones, infos = env.step(action)
            done = dones[0]
            info = infos[0]
            
            renderer.update_scene(f_env.data, camera="tracking_cam")
            frame = renderer.render()
            
            # Add text overlay
            text = f"Attempt: {i+1}/5 | Dist: {info.get('dist', 0.0):.2f}m"
            cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            if done:
                if info.get('catch', False):
                    cv2.putText(frame, "CATCH!", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    catches += 1
                else:
                    cv2.putText(frame, "DROP!", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    
            out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            
            if done:
                # hold final frame for 1 second
                for _ in range(60):
                    out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                    
        result = "✅ CATCH" if info.get('catch', False) else "❌ DROP"
        print(f"  Attempt {i+1}: {result} | Final Dist: {info.get('dist', 0.0):.2f}m")
        
    out.release()
    print("=======================================================")
    print(f"📊 FINAL SCORE: {catches}/{attempts} Catches")
    print(f"🎥 Video saved to: {video_path}")

if __name__ == "__main__":
    main()
