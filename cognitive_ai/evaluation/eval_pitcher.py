import os
import sys
import numpy as np
import mujoco
import cv2
from pathlib import Path
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.pitcher_env import PitcherEnv

def evaluate_pitcher(
    model_path="checkpoints/pitcher_best/best_model",
    norm_path="checkpoints/pitcher_vec_normalize.pkl",
    num_episodes=15,
    output_filename="pitcher_evaluation.mp4"
):
    print(f"\n🎬 Evaluating Embodied Pitcher Model: {model_path} ({num_episodes} episodes)...")
    
    def make_env():
        return PitcherEnv()
        
    vec_env = DummyVecEnv([make_env])
    if os.path.exists(norm_path):
        vec_env = VecNormalize.load(norm_path, vec_env)
        vec_env.training = False
        vec_env.norm_reward = False
        
    model = PPO.load(model_path, env=vec_env)
    raw_env = vec_env.envs[0]
    renderer = mujoco.Renderer(raw_env.model, height=480, width=640)
    
    video_dir = Path("data/eval_videos")
    video_dir.mkdir(parents=True, exist_ok=True)
    video_path = video_dir / output_filename
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
    
    strikes = 0
    total_speed = 0.0
    
    for ep in range(num_episodes):
        obs = vec_env.reset()
        done = False
        step = 0
        is_strike = False
        final_speed = 0.0
        final_dist = 999.0
        
        while not done and step < 70:
            action, _ = model.predict(obs, deterministic=True)
            obs, rewards, dones, infos = vec_env.step(action)
            done = dones[0]
            info = infos[0]
            step += 1
            
            # Switch camera view dynamically: Behind pitcher during windup, catcher during arrival
            cam_name = "side_cam" if step < 25 else "catcher_cam"
            renderer.update_scene(raw_env.data, camera=cam_name)
            rgb_frame = renderer.render()
            bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            
            ball_pos = raw_env.data.qpos[raw_env.ball_qpos_adr:raw_env.ball_qpos_adr+3]
            speed = raw_env.release_speed_kmh
            final_speed = speed
            
            rel_text = "RELEASED" if raw_env.is_released else "WINDUP"
            
            # HUD overlay
            cv2.putText(bgr_frame, f"Ep {ep+1:2d} | State: {rel_text} | Speed: {speed:.1f} km/h", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(bgr_frame, f"Target: ({raw_env.target_x:.2f}, {raw_env.target_z:.2f}) | Ball Y: {ball_pos[1]:.2f}m", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            if "release_speed_kmh" in info:
                final_speed = info["release_speed_kmh"]
            if "min_dist" in info:
                final_dist = info["min_dist"]
            if "reached_plate" in info:
                is_strike = (info["reached_plate"] and info["min_dist"] <= 0.20)
                
            writer.write(bgr_frame)
            
        if is_strike:
            strikes += 1
        total_speed += final_speed
        
        status = "🔥 STRIKE" if is_strike else "⚠️ BALL"
        print(f"  Episode {ep+1:2d}: {status} | Speed={final_speed:.1f} km/h, MissDist={final_dist*100:.1f} cm")
        
        black = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(6):
            writer.write(black)
            
    writer.release()
    vec_env.close()
    
    strike_rate = (strikes / num_episodes) * 100.0
    avg_speed = total_speed / num_episodes
    print(f"\n📊 Overall Pitcher Results:")
    print(f"   • Strike Rate : {strike_rate:.1f}% ({strikes}/{num_episodes})")
    print(f"   • Avg Velocity: {avg_speed:.1f} km/h")
    print(f"🎥 Video saved to: {video_path}")
    return strike_rate, str(video_path)

if __name__ == "__main__":
    evaluate_pitcher()
