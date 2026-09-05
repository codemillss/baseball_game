with open("VIDEO_CATALOG.md", "r") as f:
    cat = f.read()
if "mocap_match.mp4" not in cat:
    cat += "\n| `mocap_match.mp4` | 3b74... | Phase 6: Pro MoCap Imitation | **하이-레그킥 투구 및 파워 어퍼스윙 타격 폼**이 적용된 극한의 실감형 로봇 대결 영상 | `mocap_pitcher_best`, `mocap_batter_best` |"
    with open("VIDEO_CATALOG.md", "w") as f:
        f.write(cat)

with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "r") as f:
    task = f.read()
task = task.replace("[/] Phase 6", "[x] Phase 6")
with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "w") as f:
    f.write(task)
