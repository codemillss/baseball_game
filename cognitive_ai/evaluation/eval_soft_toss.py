import os
import sys
import numpy as np
import mujoco
import cv2
from pathlib import Path
from stable_baselines3 import PPO

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.soft_toss_env import SoftTossEnv

def evaluate_soft_toss(
    model_path: str = "checkpoints/soft_toss_best_model/best_model",
    num_episodes: int = 10,
    output_filename: str = "soft_toss_evaluation.mp4"
):
    if not os.path.exists(model_path + ".zip"):
        model_path = "checkpoints/soft_toss_final_model"
        
    print(f"🎬 Evaluating Soft-Toss Model: {model_path} ({num_episodes} episodes)...")
    
    env = SoftTossEnv()
    renderer = mujoco.Renderer(env.model, height=480, width=640)
    model = PPO.load(model_path)
    
    video_dir = Path("data/eval_videos")
    video_dir.mkdir(parents=True, exist_ok=True)
    video_path = video_dir / output_filename
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
    
    hits = 0
    details = []
    
    for ep in range(num_episodes):
        obs, _ = env.reset()
        done = False
        step = 0
        ep_hit = False
        contact_step = None
        
        while not done and step < 60:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            step += 1
            
            renderer.update_scene(env.data, camera="side_cam")
            rgb_frame = renderer.render()
            bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            
            # HUD overlay
            ball_pos = env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3]
            trigger_text = "SWING!" if action[0] > 0 else "WATCHING"
            cv2.putText(bgr_frame, f"Ep {ep+1} | Step {step} | {trigger_text}", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(bgr_frame, f"Ball Y: {ball_pos[1]:.2f}m | Z: {ball_pos[2]:.2f}m | Act Z: {action[1]:.2f}", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            if reward > 50 and not ep_hit:
                ep_hit = True
                contact_step = step
                cv2.putText(bgr_frame, "💥 CONTACT / HIT!", (200, 120),
                            cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
            elif ep_hit:
                cv2.putText(bgr_frame, "💥 HIT!", (20, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            
            writer.write(bgr_frame)
            
        if ep_hit:
            hits += 1
            
        status = "✅ HIT" if ep_hit else "❌ MISS"
        print(f"  Episode {ep+1:2d}: {status} (Contact Step: {contact_step}, Final Ball Z: {ball_pos[2]:.2f}m)")
        details.append({"episode": ep+1, "hit": ep_hit, "step": contact_step, "ball_z": float(ball_pos[2])})
        
        # Black frame transition
        black = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(8):
            writer.write(black)
            
    writer.release()
    env.close()
    
    hit_rate = (hits / num_episodes) * 100.0
    print(f"\n📊 Soft-Toss Evaluation Result: {hit_rate:.1f}% ({hits}/{num_episodes})")
    print(f"🎥 Video saved to: {video_path}")
    return hit_rate, str(video_path), details

if __name__ == "__main__":
    evaluate_soft_toss()
