import os
import sys
import numpy as np
import mujoco
import cv2
from pathlib import Path
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.baseball_match_env import BaseballMatchEnv
from cognitive_ai.envs.pitcher_env import PitcherEnv
from cognitive_ai.envs.breaking_ball_env import BreakingBallEnv

def simulate_pitcher_vs_batter_match(
    pitcher_model_path="checkpoints/pitcher_best/best_model",
    pitcher_norm_path="checkpoints/pitcher_vec_normalize.pkl",
    batter_model_path="checkpoints/breaking_ball_best/best_model",
    batter_norm_path="checkpoints/breaking_ball_vec_normalize.pkl",
    num_at_bats=15,
    output_filename="baseball_match_duel.mp4"
):
    print(f"\n=======================================================")
    print(f"🏟️  HUMANOID BASEBALL CHAMPIONSHIP: PITCHER VS BATTER")
    print(f"=======================================================")
    print(f"• Pitcher Model: {pitcher_model_path}")
    print(f"• Batter Model : {batter_model_path}")
    print(f"• Total At-Bats: {num_at_bats}\n")
    
    # Setup Environments for Normalizer Loaders
    def make_p_env(): return PitcherEnv()
    def make_b_env(): return BreakingBallEnv()
    
    p_vec = DummyVecEnv([make_p_env])
    p_norm = VecNormalize.load(pitcher_norm_path, p_vec)
    p_norm.training = False
    p_norm.norm_reward = False
    
    b_vec = DummyVecEnv([make_b_env])
    b_norm = VecNormalize.load(batter_norm_path, b_vec)
    b_norm.training = False
    b_norm.norm_reward = False
    
    pitcher_model = PPO.load(pitcher_model_path, env=p_vec)
    batter_model = PPO.load(batter_model_path, env=b_vec)
    
    match_env = BaseballMatchEnv()
    renderer = mujoco.Renderer(match_env.model, height=480, width=640)
    
    video_dir = Path("data/eval_videos")
    video_dir.mkdir(parents=True, exist_ok=True)
    video_path = video_dir / output_filename
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
    
    stats = {"HITS": 0, "HOMERUNS": 0, "STRIKEOUTS": 0, "WALKS": 0, "OUTS": 0}
    
    for ab in range(num_at_bats):
        obs = match_env.reset()
        done = False
        step = 0
        
        while not done and step < 70:
            # Normalize observations
            p_obs_norm = p_norm.normalize_obs(obs["pitcher"])
            b_obs_norm = b_norm.normalize_obs(obs["batter"])
            
            # Predict actions from both AI models
            p_act, _ = pitcher_model.predict(p_obs_norm, deterministic=True)
            b_act, _ = batter_model.predict(b_obs_norm, deterministic=True)
            
            # Step the full live match environment
            obs, done, info = match_env.step(p_act, b_act)
            step += 1
            
            # Dynamic camera switching: Broadcast angle for pitch flight, Batter view on swing
            cam_name = "broadcast_cam" if step < 28 or not match_env.has_contacted else "batter_focus_cam"
            renderer.update_scene(match_env.data, camera=cam_name)
            rgb_frame = renderer.render()
            bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            
            # Broadcast HUD Scoreboard
            p_speed = match_env.pitch_speed_kmh
            exit_vel = match_env.exit_velocity_kmh
            
            # Draw header banner
            cv2.rectangle(bgr_frame, (0, 0), (640, 45), (20, 20, 20), -1)
            cv2.putText(bgr_frame, f"AT-BAT {ab+1:2d}/{num_at_bats} | PITCH: {p_speed:.1f} km/h", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(bgr_frame, f"H: {stats['HITS']} | HR: {stats['HOMERUNS']} | K: {stats['STRIKEOUTS']}", (420, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
            
            if match_env.has_contacted:
                cv2.putText(bgr_frame, f"💥 CONTACT! Exit Vel: {exit_vel:.1f} km/h", (140, 100),
                            cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2)
            elif match_env.b_swing_active:
                cv2.putText(bgr_frame, f"SWING!", (260, 100),
                            cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 200, 255), 2)
                            
            if done:
                # Show Outcome Splash
                cv2.rectangle(bgr_frame, (100, 200), (540, 280), (0, 0, 0), -1)
                cv2.putText(bgr_frame, f"{info['outcome']}", (120, 250),
                            cv2.FONT_HERSHEY_DUPLEX, 0.85, (255, 255, 255), 2)
                            
            writer.write(bgr_frame)
            
        # Update match scoreboard
        outcome = info["outcome"]
        if "HOME RUN" in outcome:
            stats["HOMERUNS"] += 1
            stats["HITS"] += 1
        elif "BASE HIT" in outcome:
            stats["HITS"] += 1
        elif "STRIKE OUT" in outcome or "CALLED STRIKE" in outcome:
            stats["STRIKEOUTS"] += 1
        elif "BALL" in outcome:
            stats["WALKS"] += 1
        else:
            stats["OUTS"] += 1
            
        print(f"  At-Bat {ab+1:2d}: {outcome:26s} | Pitch: {info['pitch_speed_kmh']:.1f} km/h | ExitVel: {info['exit_velocity_kmh']:.1f} km/h | Dist: {info['batted_distance']:.1f}m")
        
        black = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(8):
            writer.write(black)
            
    writer.release()
    p_vec.close()
    b_vec.close()
    
    batting_avg = (stats['HITS'] / (num_at_bats - stats['WALKS'])) if (num_at_bats - stats['WALKS']) > 0 else 0.0
    print(f"\n=======================================================")
    print(f"📊 FINAL MATCH BOX SCORE & STATISTICS")
    print(f"=======================================================")
    print(f"• Total At-Bats   : {num_at_bats}")
    print(f"• Hits (안타)     : {stats['HITS']} (Home Runs: {stats['HOMERUNS']})")
    print(f"• Strikeouts (삼진): {stats['STRIKEOUTS']}")
    print(f"• Batting Average : {batting_avg:.3f} (타율 .{(int(batting_avg*1000)):03d})")
    print(f"🎥 Video Broadcast saved to: {video_path}")
    return stats, str(video_path)

if __name__ == "__main__":
    simulate_pitcher_vs_batter_match()
