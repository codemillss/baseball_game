import os
import sys
import numpy as np
import mujoco
import cv2
from pathlib import Path
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.soft_toss_env import SoftTossEnv

def eval_normalized(
    model_path="checkpoints/soft_toss_best_model/best_model",
    norm_path="checkpoints/soft_toss_vec_normalize.pkl",
    num_episodes=10,
    output_filename="soft_toss_normalized_eval.mp4"
):
    print(f"🎬 Evaluating Normalized Soft-Toss Agent: {model_path}...")
    
    def make_env():
        return SoftTossEnv()
        
    vec_env = DummyVecEnv([make_env])
    if os.path.exists(norm_path):
        vec_env = VecNormalize.load(norm_path, vec_env)
        vec_env.training = False
        vec_env.norm_reward = False
        
    model = PPO.load(model_path, env=vec_env)
    
    # Renderer for video
    raw_env = vec_env.envs[0]
    renderer = mujoco.Renderer(raw_env.model, height=480, width=640)
    
    video_dir = Path("data/eval_videos")
    video_dir.mkdir(parents=True, exist_ok=True)
    video_path = video_dir / output_filename
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
    
    hits = 0
    details = []
    
    for ep in range(num_episodes):
        obs = vec_env.reset()
        done = False
        step = 0
        ep_hit = False
        contact_step = None
        
        while not done and step < 50:
            action, _ = model.predict(obs, deterministic=True)
            obs, rewards, dones, infos = vec_env.step(action)
            done = dones[0]
            step += 1
            
            # Check if this step was contact
            if "episode" in infos[0]:
                ep_rew = infos[0]["episode"]["r"]
                if ep_rew > 50:
                    ep_hit = True
                    contact_step = step
            elif rewards[0] > 50:
                ep_hit = True
                contact_step = step
                
            renderer.update_scene(raw_env.data, camera="side_cam")
            rgb_frame = renderer.render()
            bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            
            ball_pos = raw_env.data.qpos[raw_env.ball_qpos_adr:raw_env.ball_qpos_adr+3]
            trigger_text = "SWING!" if action[0][0] > 0 else "WATCHING"
            cv2.putText(bgr_frame, f"Ep {ep+1} | Step {step} | {trigger_text}", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(bgr_frame, f"Ball Y: {ball_pos[1]:.2f}m | Z: {ball_pos[2]:.2f}m | Act Z: {action[0][1]:.2f}", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            if rewards[0] > 50 and not ep_hit:
                ep_hit = True
                contact_step = step
                cv2.putText(bgr_frame, "💥 CONTACT / HIT!", (200, 120),
                            cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
            elif ep_hit:
                cv2.putText(bgr_frame, "💥 HIT!", (20, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            
            writer.write(bgr_frame)
            
        if ep_hit or raw_env.has_contacted:
            hits += 1
            ep_hit = True
            
        status = "✅ HIT" if ep_hit else "❌ MISS"
        print(f"  Episode {ep+1:2d}: {status} (Contact Step: {contact_step}, Ball Z: {ball_pos[2]:.2f}m)")
        details.append({"episode": ep+1, "hit": ep_hit, "step": contact_step, "ball_z": float(ball_pos[2])})
        
        # Black frame transition
        black = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(8):
            writer.write(black)
            
    writer.release()
    vec_env.close()
    
    hit_rate = (hits / num_episodes) * 100.0
    print(f"\n📊 Normalized Soft-Toss Evaluation Result: {hit_rate:.1f}% ({hits}/{num_episodes})")
    print(f"🎥 Video saved to: {video_path}")
    return hit_rate, str(video_path), details

if __name__ == "__main__":
    eval_normalized()
