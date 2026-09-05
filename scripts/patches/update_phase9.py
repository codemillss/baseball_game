with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "r") as f:
    task = f.read()

task = task.replace("[ ] Phase 8.3", "[x] Phase 8.3")
task = task.replace("[ ] 포수(Catcher) 로봇 도입", "[x] 포수(Catcher) 로봇 도입")
task = task.replace("[ ] 주자(Runner) 로봇 1루 도입", "[x] 주자(Runner) 로봇 1루 도입")

task += """
- [ ] Phase 9: Full Game System (9-Inning Match & Infielders)
  - [ ] 내야수(Infielders) 4명 추가 (1루수, 2루수, 유격수, 3루수)
  - [ ] 아웃 카운트, 이닝, 점수 판정 로직 추가 (Scoreboard)
  - [ ] 완전한 9이닝 야구 경기 시뮬레이션 환경 통합
"""

with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "w") as f:
    f.write(task)

with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/walkthrough.md", "a") as f:
    f.write("\n\n---\n\n## [Phase 8.3] 포수 및 도루 시스템 도입\n**목표:** 1루에 주자(Runner)를 배치하여 2루를 훔치는 도루 상황을 연출하고, 포수(Catcher) 로봇을 도입하여 공을 잡는 훈련 진행.\n- **결과:** 주자와 포수의 로봇 모델(`h1_runner.xml`, `h1_catcher.xml`)을 분리하여 환경을 구축했고, 주자가 1루에서 출발해 2루로 맹렬하게 달리는 모습을 영상으로 확인했습니다. 로컬 Git에 커밋 완료!\n\n![도루 테스트](/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/phase_8_3_base_stealing.mp4)\n")

with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/implementation_plan.md", "a") as f:
    f.write("\n\n## [Phase 9] Full Game System (9-Inning Match & Infielders)\n**목표:** 이제 야구의 모든 단편적인 요소(투수, 타자, 외야수, 포수, 주자, 심판, 물리엔진)가 모였습니다. 마지막 단계는 이를 하나의 거대한 **State Machine(상태 머신)**으로 묶어 9이닝 정규 경기를 치르는 것입니다.\n1. **내야수 추가:** 1루수, 2루수, 유격수, 3루수를 추가하여 내야 땅볼을 처리합니다.\n2. **점수판 및 게임 루프:** 스트라이크 3개면 아웃, 아웃 3개면 공수교대, 주자가 홈을 밟으면 1득점을 올리는 게임 룰(Game State)을 구현합니다.\n3. **자동화:** 이 거대한 통합 환경(Mega-Env)에서 투수와 타자 AI가 스스로 9이닝 경기를 펼치도록 놔둡니다.\n")
