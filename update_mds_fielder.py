import re

with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "r") as f:
    task = f.read()
task = task.replace("[ ] Phase 7", "[x] Phase 7")
task = task.replace("[ ] `h1_fielder.xml", "[x] `h1_fielder.xml")
task = task.replace("[ ] `fielder_env.py", "[x] `fielder_env.py")
task = task.replace("[ ] `train_fielder.py", "[x] `train_fielder.py")
with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "w") as f:
    f.write(task)

with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/walkthrough.md", "a") as f:
    f.write("\n\n---\n\n## [Phase 7] 바퀴 달린 수비수 (Wheeled Fielder)\n**목표:** 두 발로 걷는(Locomotion) 극한의 난이도를 피하기 위해, 다리를 절단하고 전방위 이동 베이스(Omni-wheels)와 왼손 글러브를 장착한 수비수 AI 훈련.\n- **결과:** 넘어질 걱정 없이 오직 낙구 지점 파악에만 집중하여, 5번의 뜬공을 모두 완벽하게 낚아채는(Catch 5/5) 놀라운 궤도 추적 능력을 확보했습니다!\n\n![바퀴 달린 수비수의 캐치 훈련](/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/phase_7_1_wheeled_fielder.mp4)\n")

with open("VIDEO_CATALOG.md", "r") as f:
    cat = f.read()
if "phase_7_1_wheeled_fielder.mp4" not in cat:
    cat += "\n| `phase_7_1_wheeled_fielder.mp4` | 3b74... | Phase 7: Wheeled Fielder | 다리 대신 바퀴를 달고 왼손에 글러브를 장착한 수비수가 뜬공을 추적하여 캐치하는 AI | `fielder_best` |"
    with open("VIDEO_CATALOG.md", "w") as f:
        f.write(cat)

