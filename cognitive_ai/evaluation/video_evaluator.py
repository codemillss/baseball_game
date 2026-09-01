import os
import sys
import numpy as np
import mujoco
import cv2
from pathlib import Path
from stable_baselines3 import PPO

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.teeball_env import TeeBallEnv

class VideoEvaluator:
    """
    AI Autonomous Video Evaluation & Diagnostic System
    - Records offscreen 3D simulation video (MP4)
    - Extracts contact frames and metrics
    - Analyzes physics, kinematics, and failure modes
    """
    def __init__(
        self,
        xml_path: str = "shared_assets/h1_baseball.xml",
        video_dir: str = "data/eval_videos",
        width: int = 640,
        height: int = 480,
        fps: int = 30,
    ):
        self.xml_path = xml_path
        self.video_dir = Path(video_dir)
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.width = width
        self.height = height
        self.fps = fps

    def record_and_evaluate(
        self,
        model_path: str,
        num_episodes: int = 3,
        camera_name: str = "side_cam",
        output_filename: str = "latest_evaluation.mp4"
    ) -> dict:
        """
        Runs evaluation episodes, records video, and computes diagnostic metrics.
        """
        env = TeeBallEnv(xml_path=self.xml_path, render_mode=None)
        renderer = mujoco.Renderer(env.model, height=self.height, width=self.width)
        
        # Load model
        model = PPO.load(model_path)
        
        video_path = self.video_dir / output_filename
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(video_path), fourcc, self.fps, (self.width, self.height))
        
        metrics = {
            "num_episodes": num_episodes,
            "hits": 0,
            "misses": 0,
            "hit_details": [],
            "video_path": str(video_path),
        }
        
        for ep in range(num_episodes):
            obs, _ = env.reset()
            done = False
            step = 0
            ep_frames = []
            ep_hit = False
            contact_step = None
            
            ball_initial_z = float(obs[2])
            
            while not done and step < 80:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                step += 1
                
                # Render frame
                renderer.update_scene(env.data, camera=camera_name)
                rgb_frame = renderer.render()
                
                # Convert RGB to BGR for OpenCV
                bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
                
                # Add HUD / Telemetry overlay
                cv2.putText(bgr_frame, f"Ep {ep+1} | Step {step} | SWING", (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(bgr_frame, f"Ball Z: {ball_initial_z:.2f}m | Action Z: {float(action[0]):.2f}", (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                
                if reward > 50 and not ep_hit:
                    ep_hit = True
                    contact_step = step
                    cv2.putText(bgr_frame, "💥 CONTACT / HIT!", (self.width // 2 - 100, 100),
                                cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
                elif ep_hit:
                    cv2.putText(bgr_frame, "💥 HIT!", (20, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                
                writer.write(bgr_frame)
                ep_frames.append(bgr_frame)
                
            if ep_hit:
                metrics["hits"] += 1
            else:
                metrics["misses"] += 1
                
            metrics["hit_details"].append({
                "episode": ep + 1,
                "ball_z": round(ball_initial_z, 3),
                "hit": ep_hit,
                "contact_step": contact_step,
                "total_steps": step,
            })
            
            # Add brief pause frame between episodes
            black_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            for _ in range(10):
                writer.write(black_frame)
                
        writer.release()
        env.close()
        
        metrics["hit_rate"] = (metrics["hits"] / num_episodes) * 100.0
        return metrics

if __name__ == "__main__":
    evaluator = VideoEvaluator()
    model_file = "checkpoints/teeball_best_model/best_model"
    if not os.path.exists(model_file + ".zip"):
        model_file = "checkpoints/teeball_final_model"
        
    print(f"🎬 Recording evaluation video for: {model_file}...")
    results = evaluator.record_and_evaluate(model_file, num_episodes=5)
    print("\n📊 Evaluation Summary:")
    print(f"  - Hit Rate: {results['hit_rate']:.1f}% ({results['hits']}/{results['num_episodes']})")
    print(f"  - Video saved to: {results['video_path']}")
    for d in results['hit_details']:
        status = "✅ HIT" if d['hit'] else "❌ MISS"
        print(f"    Episode {d['episode']}: Ball Z={d['ball_z']}m -> {status} (Step {d['contact_step']})")
