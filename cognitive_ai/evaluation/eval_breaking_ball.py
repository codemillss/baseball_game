import os
import sys
import numpy as np
import mujoco
import cv2
from pathlib import Path
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.breaking_ball_env import BreakingBallEnv

def evaluate_breaking_balls(
    model_path="checkpoints/breaking_ball_best/best_model",
    norm_path="checkpoints/breaking_ball_vec_normalize.pkl",
    num_episodes=15,
    output_filename="breaking_ball_evaluation.mp4"
):
    print(f"\n🎬 Evaluating 3D Breaking Ball Model: {model_path} ({num_episodes} episodes)...")
    
    def make_env():
        return BreakingBallEnv()
        
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
    
    pitch_stats = {"FASTBALL": {"hits": 0, "total": 0}, "SLIDER": {"hits": 0, "total": 0}, "CURVE": {"hits": 0, "total": 0}}
    total_hits = 0
    
    for ep in range(num_episodes):
        obs = vec_env.reset()
        done = False
        step = 0
        ep_hit = False
        contact_step = None
        p_type = raw_env.pitch_type
        pitch_stats[p_type]["total"] += 1
        
        while not done and step < 60:
            action, _ = model.predict(obs, deterministic=True)
            obs, rewards, dones, infos = vec_env.step(action)
            done = dones[0]
            step += 1
            
            if "episode" in infos[0]:
                if infos[0]["episode"]["r"] > 50:
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
            
            # HUD overlay
            cv2.putText(bgr_frame, f"Ep {ep+1} | Pitch: {p_type} | {trigger_text}", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(bgr_frame, f"Ball X: {ball_pos[0]:.2f}m | Z: {ball_pos[2]:.2f}m | Yaw: {action[0][2]:.2f}", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            if ep_hit and step == contact_step:
                cv2.putText(bgr_frame, f"💥 {p_type} HIT!", (180, 120),
                            cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
                            
            writer.write(bgr_frame)
            
        if ep_hit:
            total_hits += 1
            pitch_stats[p_type]["hits"] += 1
            
        status = "✅ HIT" if ep_hit else "❌ MISS"
        print(f"  Episode {ep+1:2d} [{p_type:8s}]: {status} (Contact Step: {contact_step})")
        
        black = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(6):
            writer.write(black)
            
    writer.release()
    vec_env.close()
    
    hit_rate = (total_hits / num_episodes) * 100.0
    print(f"\n📊 Overall Breaking Ball Result: {hit_rate:.1f}% ({total_hits}/{num_episodes})")
    for pt, s in pitch_stats.items():
        if s["total"] > 0:
            print(f"   • {pt:8s}: {s['hits']/s['total']*100:.1f}% ({s['hits']}/{s['total']})")
    print(f"🎥 Video saved to: {video_path}")
    return hit_rate, str(video_path)

if __name__ == "__main__":
    evaluate_breaking_balls()
