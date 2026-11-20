# baseball/scripts/patches/update_mds_8_1.py

원본: [scripts/patches/update_mds_8_1.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/update_mds_8_1.py)

SHA256: `75e7082b21c48a1caddbf7fc28333d071cb93628e2d6fdcb665cdc597cdb17c3`

전체 12행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "r") as f:
    2 |     task = f.read()
    3 | task = task.replace("[ ] Phase 8.1", "[x] Phase 8.1")
    4 | task = task.replace("[ ] `h1_baseball_match.xml`에 스트라이크 존", "[x] `h1_baseball_match.xml`에 스트라이크 존")
    5 | task = task.replace("[ ] `baseball_rules.py` 구현", "[x] `baseball_rules.py` 구현")
    6 | task = task.replace("[ ] AI 방송 중계 카메라", "[x] AI 방송 중계 카메라")
    7 | with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "w") as f:
    8 |     f.write(task)
    9 | 
   10 | with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/walkthrough.md", "a") as f:
   11 |     f.write("\n\n---\n\n## [Phase 8.1] 자동 심판(Umpire) 규칙 적용 및 방송 중계 AI\n**목표:** 공이 3D 센서 박스(스트라이크 존)를 통과하는지 여부를 계산하여 완벽하게 스트라이크/볼을 자동 판정하고, 타격 후 타구의 방향에 따라 카메라 앵글이 자동 스위칭되도록 연출.\n- **결과:** 화면 좌측 하단에 심판 AI의 실시간 판정(BALL/STRIKE/FAIR 등)이 송출되며, 실제 야구와 동일한 긴장감을 주는 카메라 다이렉팅을 시각적으로 확인했습니다!\n\n![AI 방송 중계 통합 매치](/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/phase_8_1_broadcast_match.mp4)\n")
   12 | 
````
