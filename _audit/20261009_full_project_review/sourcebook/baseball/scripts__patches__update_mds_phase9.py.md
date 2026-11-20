# baseball/scripts/patches/update_mds_phase9.py

원본: [scripts/patches/update_mds_phase9.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/update_mds_phase9.py)

SHA256: `6b2b6cfda632cabc091ab33246ba780fcbd3ae288ef11d8be5139204861c656a`

전체 10행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "r") as f:
    2 |     task = f.read()
    3 | 
    4 | task = task.replace("[ ] Phase 9", "[x] Phase 9")
    5 | task = task.replace("[ ] 내야수(Infielders)", "[x] 내야수(Infielders)")
    6 | task = task.replace("[ ] 아웃 카운트", "[x] 아웃 카운트")
    7 | task = task.replace("[ ] 완전한 9이닝 야구 경기", "[x] 완전한 9이닝 야구 경기")
    8 | 
    9 | with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "w") as f:
   10 |     f.write(task)
````
