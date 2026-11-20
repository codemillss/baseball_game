# baseball/scripts/patches/rename_videos.py

원본: [scripts/patches/rename_videos.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/rename_videos.py)

SHA256: `85042985c291a9b464cac096bce8fa4c060c5ba7ab7fcca55be53e16de9cbc3c`

전체 34행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import os
    2 | import shutil
    3 | 
    4 | ARTIFACTS_DIR = "/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7"
    5 | FINAL_VIDEOS_DIR = "/Users/jin10000/Desktop/mini-project/baseball/final_videos"
    6 | 
    7 | mapping = {
    8 |     "soft_toss_evaluation.mp4": "phase_1_1_soft_toss_initial.mp4",
    9 |     "soft_toss_normalized_eval.mp4": "phase_1_2_soft_toss_normalized.mp4",
   10 |     "latest_evaluation.mp4": "phase_1_3_soft_toss_advanced.mp4",
   11 |     "breaking_ball_evaluation.mp4": "phase_1_4_breaking_ball.mp4",
   12 |     "pitching_50kmh_eval.mp4": "phase_2_1_pitching_50kmh.mp4",
   13 |     "pitching_80kmh_eval.mp4": "phase_2_2_pitching_80kmh.mp4",
   14 |     "pitcher_evaluation.mp4": "phase_2_3_pitcher_final.mp4",
   15 |     "baseball_match_duel.mp4": "phase_3_1_match_duel.mp4",
   16 |     "mlb_baseball_match.mp4": "phase_4_1_mlb_match.mp4",
   17 |     "stadium_match.mp4": "phase_5_1_stadium_match.mp4",
   18 |     "mocap_preview.mp4": "phase_6_1_mocap_preview.mp4",
   19 |     "mocap_match.mp4": "phase_6_2_mocap_match.mp4"
   20 | }
   21 | 
   22 | for old_name, new_name in mapping.items():
   23 |     old_path = os.path.join(ARTIFACTS_DIR, old_name)
   24 |     if os.path.exists(old_path):
   25 |         # 1. Copy to final_videos dir
   26 |         shutil.copy2(old_path, os.path.join(FINAL_VIDEOS_DIR, new_name))
   27 |         
   28 |         # 2. Rename in artifacts dir
   29 |         new_artifact_path = os.path.join(ARTIFACTS_DIR, new_name)
   30 |         os.rename(old_path, new_artifact_path)
   31 |         print(f"Renamed {old_name} -> {new_name}")
   32 |     else:
   33 |         print(f"Warning: {old_name} not found in artifacts dir.")
   34 | 
````
