import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import cv2
import mujoco
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from cognitive_ai.envs.pitcher_env import PitcherEnv
from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
import imageio_ffmpeg

def simulate_mocap_match():
    print("\n=======================================================")
    print("🏟️  HUMANOID BASEBALL CHAMPIONSHIP: MOCAP PITCHER VS MOCAP BATTER")
    print("=======================================================")
    
    pitcher_model_path = "checkpoints/mocap_pitcher_best/best_model"
    pitcher_norm_path = "checkpoints/mocap_pitcher_vec_normalize.pkl"
    batter_model_path = "checkpoints/mocap_batter_best/best_model"
    batter_norm_path = "checkpoints/mocap_batter_vec_normalize.pkl"
    
    def make_p_env(): return PitcherEnv()
    def make_b_env(): return BatterMatchTrainingEnv(
        pitcher_model_path=pitcher_model_path,
        pitcher_norm_path=pitcher_norm_path,
        is_eval_mode=True
    )
    
    p_vec = DummyVecEnv([make_p_env])
    p_norm = VecNormalize.load(pitcher_norm_path, p_vec)
    p_norm.training = False
    p_norm.norm_reward = False
    p_model = PPO.load(pitcher_model_path, env=p_norm)
    
    b_vec = DummyVecEnv([make_b_env])
    b_norm = VecNormalize.load(batter_norm_path, b_vec)
    b_norm.training = False
    b_norm.norm_reward = False
    b_model = PPO.load(batter_model_path, env=b_norm)
    
    b_env = b_vec.envs[0].match_env
    
    os.makedirs("data/eval_videos", exist_ok=True)
    video_path_tmp = "data/eval_videos/mocap_match_temp.mp4"
    video_path_final = "data/eval_videos/mocap_match.mp4"
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(video_path_tmp, fourcc, 30, (640, 480))
    
    renderer = mujoco.Renderer(b_env.model, 480, 640)
    
    num_episodes = 5
    print(f"• Total At-Bats: {num_episodes}\n")
    
    hits = 0
    hrs = 0
    sos = 0
    
    for ep in range(1, num_episodes + 1):
        b_norm_obs = b_vec.reset()
        done = False
        
        while not done:
            action, _ = b_model.predict(b_norm_obs, deterministic=True)
            b_norm_obs, reward, dones, infos = b_vec.step(action)
            done = dones[0]
            info = infos[0]
            
            renderer.update_scene(b_env.data, camera="catcher_cam")
            frame = renderer.render()
            
            outcome = info.get('outcome', '')
            if outcome:
                cv2.putText(frame, outcome, (150, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
            
            writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            
            if done:
                # Capture variables right when done occurs (DummyVecEnv resets on the same step, but info contains the terminal state)
                speed = info.get('pitch_speed', b_env.pitch_speed_kmh) 
                exit_vel = info.get('exit_velocity_kmh', 0.0)
                dist = info.get('batted_distance', 0.0)
            
        final_outcome = info.get('outcome', 'UNKNOWN')
        pitch_type_name = ["FASTBALL", "SLIDER", "CURVE"][b_env.target_pitch_type]
        
        print(f"  At-Bat {ep:2d}: {final_outcome:25s} | {pitch_type_name} | Pitch: {speed:.1f} km/h | ExitVel: {exit_vel:.1f} km/h | Dist: {dist:.1f}m")
        
        if "STRIKE OUT" in final_outcome: sos += 1
        if "BASE HIT" in final_outcome or "DOUBLE" in final_outcome or "HOME RUN" in final_outcome: hits += 1
        if "HOME RUN" in final_outcome: hrs += 1
            
    writer.release()
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.system(f"{ffmpeg_exe} -y -i {video_path_tmp} -c:v libx264 -pix_fmt yuv420p {video_path_final} >/dev/null 2>&1")
    os.remove(video_path_tmp)
    
    print("\n=======================================================")
    print("📊 FINAL MATCH BOX SCORE & STATISTICS")
    print("=======================================================")
    print(f"• Total At-Bats   : {num_episodes}")
    print(f"• Hits (안타)     : {hits} (Home Runs: {hrs})")
    print(f"• Strikeouts (삼진): {sos}")
    print(f"🎥 Video Broadcast saved to: {video_path_final}")

if __name__ == "__main__":
    simulate_mocap_match()
