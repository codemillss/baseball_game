# baseball/scripts/patches/patch_pitcher_control.py

원본: [scripts/patches/patch_pitcher_control.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/patch_pitcher_control.py)

SHA256: `3fdd7a5289cb69efe3ad1d33ba38464f99479d6fc8b6f8f82afe8766ef053100`

전체 8행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import re
    2 | 
    3 | with open("cognitive_ai/envs/pitcher_env.py", "r") as f:
    4 |     content = f.read()
    5 | 
    6 | # We want to add a strike zone reward in the step() function where it calculates distance.
    7 | # Currently it uses self.target_x, self.target_z.
    8 | # Let's see how the reward is calculated.
````
