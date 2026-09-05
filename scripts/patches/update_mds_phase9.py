with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "r") as f:
    task = f.read()

task = task.replace("[ ] Phase 9", "[x] Phase 9")
task = task.replace("[ ] 내야수(Infielders)", "[x] 내야수(Infielders)")
task = task.replace("[ ] 아웃 카운트", "[x] 아웃 카운트")
task = task.replace("[ ] 완전한 9이닝 야구 경기", "[x] 완전한 9이닝 야구 경기")

with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "w") as f:
    f.write(task)
