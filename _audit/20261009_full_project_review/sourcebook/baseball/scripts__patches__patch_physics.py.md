# baseball/scripts/patches/patch_physics.py

원본: [scripts/patches/patch_physics.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/patch_physics.py)

SHA256: `8a2e011d5006753f6d108cfe22620caf8b3e318657d56e4e7f27e0e3444b3c39`

전체 8행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import re
    2 | 
    3 | with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    4 |     content = f.read()
    5 | 
    6 | # We will inject `_apply_aerodynamics` into `BaseballMatchEnv`
    7 | # First, let's find the step() method.
    8 | print(content.find("def step(self, action):"))
````
