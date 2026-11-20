# baseball/cognitive_ai/evaluation/evaluate_mocap_match.py

원본: [cognitive_ai/evaluation/evaluate_mocap_match.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/evaluation/evaluate_mocap_match.py)

SHA256: `671f2a208d271a5b31494f28570c5ca808067c86e7ea55998306b266fd0a3f4e`

전체 109행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `simulate_mocap_match` | FunctionDef | 13 | 106 |
| `make_p_env` | FunctionDef | 23 | 23 |
| `make_b_env` | FunctionDef | 24 | 28 |

## 전체 원문

````text
    1 | import os
    2 | import sys
    3 | sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    4 | 
    5 | import cv2
    6 | import mujoco
    7 | from stable_baselines3 import PPO
    8 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    9 | from cognitive_ai.envs.pitcher_env import PitcherEnv
   10 | from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
   11 | import imageio_ffmpeg
   12 | 
   13 | def simulate_mocap_match():
   14 |     print("\n=======================================================")
   15 |     print("🏟️  HUMANOID BASEBALL CHAMPIONSHIP: MOCAP PITCHER VS MOCAP BATTER")
   16 |     print("=======================================================")
   17 |     
   18 |     pitcher_model_path = "checkpoints/mocap_pitcher_best/best_model"
   19 |     pitcher_norm_path = "checkpoints/mocap_pitcher_vec_normalize.pkl"
   20 |     batter_model_path = "checkpoints/mocap_batter_best/best_model"
   21 |     batter_norm_path = "checkpoints/mocap_batter_vec_normalize.pkl"
   22 |     
   23 |     def make_p_env(): return PitcherEnv()
   24 |     def make_b_env(): return BatterMatchTrainingEnv(
   25 |         pitcher_model_path=pitcher_model_path,
   26 |         pitcher_norm_path=pitcher_norm_path,
   27 |         is_eval_mode=True
   28 |     )
   29 |     
   30 |     p_vec = DummyVecEnv([make_p_env])
   31 |     p_norm = VecNormalize.load(pitcher_norm_path, p_vec)
   32 |     p_norm.training = False
   33 |     p_norm.norm_reward = False
   34 |     p_model = PPO.load(pitcher_model_path, env=p_norm)
   35 |     
   36 |     b_vec = DummyVecEnv([make_b_env])
   37 |     b_norm = VecNormalize.load(batter_norm_path, b_vec)
   38 |     b_norm.training = False
   39 |     b_norm.norm_reward = False
   40 |     b_model = PPO.load(batter_model_path, env=b_norm)
   41 |     
   42 |     b_env = b_vec.envs[0].match_env
   43 |     
   44 |     os.makedirs("data/eval_videos", exist_ok=True)
   45 |     video_path_tmp = "data/eval_videos/mocap_match_temp.mp4"
   46 |     video_path_final = "data/eval_videos/mocap_match.mp4"
   47 |     
   48 |     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   49 |     writer = cv2.VideoWriter(video_path_tmp, fourcc, 30, (640, 480))
   50 |     
   51 |     renderer = mujoco.Renderer(b_env.model, 480, 640)
   52 |     
   53 |     num_episodes = 5
   54 |     print(f"• Total At-Bats: {num_episodes}\n")
   55 |     
   56 |     hits = 0
   57 |     hrs = 0
   58 |     sos = 0
   59 |     
   60 |     for ep in range(1, num_episodes + 1):
   61 |         b_norm_obs = b_vec.reset()
   62 |         done = False
   63 |         
   64 |         while not done:
   65 |             action, _ = b_model.predict(b_norm_obs, deterministic=True)
   66 |             b_norm_obs, reward, dones, infos = b_vec.step(action)
   67 |             done = dones[0]
   68 |             info = infos[0]
   69 |             
   70 |             renderer.update_scene(b_env.data, camera="catcher_cam")
   71 |             frame = renderer.render()
   72 |             
   73 |             outcome = info.get('outcome', '')
   74 |             if outcome:
   75 |                 cv2.putText(frame, outcome, (150, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
   76 |             
   77 |             writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
   78 |             
   79 |             if done:
   80 |                 # Capture variables right when done occurs (DummyVecEnv resets on the same step, but info contains the terminal state)
   81 |                 speed = info.get('pitch_speed', b_env.pitch_speed_kmh) 
   82 |                 exit_vel = info.get('exit_velocity_kmh', 0.0)
   83 |                 dist = info.get('batted_distance', 0.0)
   84 |             
   85 |         final_outcome = info.get('outcome', 'UNKNOWN')
   86 |         pitch_type_name = ["FASTBALL", "SLIDER", "CURVE"][b_env.target_pitch_type]
   87 |         
   88 |         print(f"  At-Bat {ep:2d}: {final_outcome:25s} | {pitch_type_name} | Pitch: {speed:.1f} km/h | ExitVel: {exit_vel:.1f} km/h | Dist: {dist:.1f}m")
   89 |         
   90 |         if "STRIKE OUT" in final_outcome: sos += 1
   91 |         if "BASE HIT" in final_outcome or "DOUBLE" in final_outcome or "HOME RUN" in final_outcome: hits += 1
   92 |         if "HOME RUN" in final_outcome: hrs += 1
   93 |             
   94 |     writer.release()
   95 |     
   96 |     ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
   97 |     os.system(f"{ffmpeg_exe} -y -i {video_path_tmp} -c:v libx264 -pix_fmt yuv420p {video_path_final} >/dev/null 2>&1")
   98 |     os.remove(video_path_tmp)
   99 |     
  100 |     print("\n=======================================================")
  101 |     print("📊 FINAL MATCH BOX SCORE & STATISTICS")
  102 |     print("=======================================================")
  103 |     print(f"• Total At-Bats   : {num_episodes}")
  104 |     print(f"• Hits (안타)     : {hits} (Home Runs: {hrs})")
  105 |     print(f"• Strikeouts (삼진): {sos}")
  106 |     print(f"🎥 Video Broadcast saved to: {video_path_final}")
  107 | 
  108 | if __name__ == "__main__":
  109 |     simulate_mocap_match()
````
