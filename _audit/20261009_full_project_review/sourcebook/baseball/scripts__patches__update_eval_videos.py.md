# baseball/scripts/patches/update_eval_videos.py

원본: [scripts/patches/update_eval_videos.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/update_eval_videos.py)

SHA256: `bf771d24cd147644bc71e7acaac1a80247f2b7aab41ef06e37c9a99d49149288`

전체 25행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import os
    2 | import shutil
    3 | 
    4 | EVAL_DIR = "/Users/jin10000/Desktop/mini-project/baseball/data/eval_videos"
    5 | 
    6 | mapping = {
    7 |     "soft_toss_evaluation.mp4": "phase_1_1_soft_toss_initial.mp4",
    8 |     "soft_toss_normalized_eval.mp4": "phase_1_2_soft_toss_normalized.mp4",
    9 |     "latest_evaluation.mp4": "phase_1_3_soft_toss_advanced.mp4",
   10 |     "breaking_ball_evaluation.mp4": "phase_1_4_breaking_ball.mp4",
   11 |     "pitching_50kmh_eval.mp4": "phase_2_1_pitching_50kmh.mp4",
   12 |     "pitching_80kmh_eval.mp4": "phase_2_2_pitching_80kmh.mp4",
   13 |     "pitcher_evaluation.mp4": "phase_2_3_pitcher_final.mp4",
   14 |     "baseball_match_duel.mp4": "phase_3_1_match_duel.mp4",
   15 |     "mlb_baseball_match.mp4": "phase_4_1_mlb_match.mp4",
   16 |     "stadium_match.mp4": "phase_5_1_stadium_match.mp4",
   17 |     "mocap_preview.mp4": "phase_6_1_mocap_preview.mp4",
   18 |     "mocap_match.mp4": "phase_6_2_mocap_match.mp4"
   19 | }
   20 | 
   21 | for old, new in mapping.items():
   22 |     old_path = os.path.join(EVAL_DIR, old)
   23 |     if os.path.exists(old_path):
   24 |         os.rename(old_path, os.path.join(EVAL_DIR, new))
   25 |         print(f"Renamed {old} -> {new}")
````
