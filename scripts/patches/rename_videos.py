import os
import shutil

ARTIFACTS_DIR = "/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7"
FINAL_VIDEOS_DIR = "/Users/jin10000/Desktop/mini-project/baseball/final_videos"

mapping = {
    "soft_toss_evaluation.mp4": "phase_1_1_soft_toss_initial.mp4",
    "soft_toss_normalized_eval.mp4": "phase_1_2_soft_toss_normalized.mp4",
    "latest_evaluation.mp4": "phase_1_3_soft_toss_advanced.mp4",
    "breaking_ball_evaluation.mp4": "phase_1_4_breaking_ball.mp4",
    "pitching_50kmh_eval.mp4": "phase_2_1_pitching_50kmh.mp4",
    "pitching_80kmh_eval.mp4": "phase_2_2_pitching_80kmh.mp4",
    "pitcher_evaluation.mp4": "phase_2_3_pitcher_final.mp4",
    "baseball_match_duel.mp4": "phase_3_1_match_duel.mp4",
    "mlb_baseball_match.mp4": "phase_4_1_mlb_match.mp4",
    "stadium_match.mp4": "phase_5_1_stadium_match.mp4",
    "mocap_preview.mp4": "phase_6_1_mocap_preview.mp4",
    "mocap_match.mp4": "phase_6_2_mocap_match.mp4"
}

for old_name, new_name in mapping.items():
    old_path = os.path.join(ARTIFACTS_DIR, old_name)
    if os.path.exists(old_path):
        # 1. Copy to final_videos dir
        shutil.copy2(old_path, os.path.join(FINAL_VIDEOS_DIR, new_name))
        
        # 2. Rename in artifacts dir
        new_artifact_path = os.path.join(ARTIFACTS_DIR, new_name)
        os.rename(old_path, new_artifact_path)
        print(f"Renamed {old_name} -> {new_name}")
    else:
        print(f"Warning: {old_name} not found in artifacts dir.")

