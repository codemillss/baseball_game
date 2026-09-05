import re

with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/walkthrough.md", "r") as f:
    content = f.read()

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

for old, new in mapping.items():
    content = content.replace(old, new)

with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/walkthrough.md", "w") as f:
    f.write(content)

