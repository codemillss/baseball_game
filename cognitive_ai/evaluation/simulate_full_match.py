import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import cv2
import mujoco
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
from cognitive_ai.envs.baseball_rules import BaseballUmpire

def main():
    print("Initializing Match Environment with Umpire and Broadcast Director...")
    pitcher_model_path = "checkpoints/mocap_pitcher_best/best_model"
    pitcher_norm_path = "checkpoints/mocap_pitcher_vec_normalize.pkl"
    batter_model_path = "checkpoints/mocap_batter_best/best_model"
    batter_norm_path = "checkpoints/mocap_batter_vec_normalize.pkl"

    def make_b_env(): return BatterMatchTrainingEnv(
        pitcher_model_path=pitcher_model_path,
        pitcher_norm_path=pitcher_norm_path,
        is_eval_mode=True
    )
    
    b_vec = DummyVecEnv([make_b_env])
    b_vec = VecNormalize.load(batter_norm_path, b_vec)
    b_vec.training = False
    b_vec.norm_reward = False

    print("Loading AI Models...")
    b_model = PPO.load(batter_model_path)

    env = b_vec.envs[0].match_env
    umpire = BaseballUmpire()

    renderer = mujoco.Renderer(env.data.model, 480, 640)
    os.makedirs("data/eval_videos", exist_ok=True)
    video_path = "data/eval_videos/phase_8_1_broadcast_match.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, 60.0, (640, 480))

    attempts = 3
    print("=======================================================")
    print("🎬 AI BROADCAST DIRECTOR: LIVE MATCH")
    print("=======================================================")

    for i in range(attempts):
        b_norm_obs = b_vec.reset()
        
        done = False
        ball_trajectory = []
        hit_detected = False
        outcome = "PENDING"
        
        while not done:
            b_action, _ = b_model.predict(b_norm_obs, deterministic=True)
            # Force swing to see hitting rules occasionally? 
            # Or let it swing naturally.
            b_norm_obs, reward, dones, infos = b_vec.step(b_action)
            done = dones[0]
            info = infos[0]
            
            ball_pos = env.data.xpos[env.ball_body_id].copy()
            ball_trajectory.append(ball_pos)
            
            if getattr(env, 'has_hit', False) or env.batted_distance > 0:
                hit_detected = True
                
            # Dynamic Camera
            if not hit_detected:
                active_cam = "catcher_cam"
            else:
                active_cam = "broadcast_cam"
                
            renderer.update_scene(env.data, camera=active_cam)
            frame = renderer.render()
            
            cv2.putText(frame, f"AT-BAT {i+1} | CAM: {active_cam}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if done:
                min_dist_to_center = min([np.sqrt(p[0]**2 + (p[2]-0.8)**2) for p in ball_trajectory if abs(p[1]) < 0.3]) if any(abs(p[1]) < 0.3 for p in ball_trajectory) else 999.0
                if hit_detected:
                    outcome = umpire.check_hit_outcome(ball_pos)
                else:
                    outcome = umpire.check_pitch_outcome(ball_trajectory)
                    if info.get("swing", False) or getattr(env, 'has_swung', False):
                        outcome = "STRIKE (Swinging)"
                
                color = (0, 255, 0) if "FAIR" in outcome or "HOME RUN" in outcome else (0, 0, 255)
                cv2.putText(frame, f"UMPIRE: {outcome} (Dist: {min_dist_to_center:.2f})", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
                
            out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            
            if done:
                for _ in range(60):
                    out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                    
        print(f"At-Bat {i+1}: {outcome} | Min Dist to SZ Center: {min_dist_to_center:.2f}m")

    out.release()
    print("=======================================================")
    print(f"🎥 Video saved to: {video_path}")

if __name__ == "__main__":
    main()
