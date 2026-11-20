# baseball/scripts/patches/update_mds.py

원본: [scripts/patches/update_mds.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/update_mds.py)

SHA256: `a86127953cc7ed2b512236b5ca66aac28c083e6dfedab874953dedeb24bfc769`

전체 12행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | with open("VIDEO_CATALOG.md", "r") as f:
    2 |     cat = f.read()
    3 | if "mocap_match.mp4" not in cat:
    4 |     cat += "\n| `mocap_match.mp4` | 3b74... | Phase 6: Pro MoCap Imitation | **하이-레그킥 투구 및 파워 어퍼스윙 타격 폼**이 적용된 극한의 실감형 로봇 대결 영상 | `mocap_pitcher_best`, `mocap_batter_best` |"
    5 |     with open("VIDEO_CATALOG.md", "w") as f:
    6 |         f.write(cat)
    7 | 
    8 | with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "r") as f:
    9 |     task = f.read()
   10 | task = task.replace("[/] Phase 6", "[x] Phase 6")
   11 | with open("/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/task.md", "w") as f:
   12 |     f.write(task)
````
