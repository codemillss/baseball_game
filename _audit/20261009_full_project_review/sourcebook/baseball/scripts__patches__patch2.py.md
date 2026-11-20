# baseball/scripts/patches/patch2.py

원본: [scripts/patches/patch2.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/patch2.py)

SHA256: `19a5f3e154e8d179b87cd6bcf8f6d1797b2d9a3e55f3f59f2a03ef7f189567b8`

전체 12행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import re
    2 | 
    3 | with open("cognitive_ai/envs/pitcher_env.py", "r") as f:
    4 |     content = f.read()
    5 | 
    6 | content = content.replace(
    7 |     "self.data.qvel[self.qvel_adrs[i]] = 0.0",
    8 |     ""
    9 | )
   10 | 
   11 | with open("cognitive_ai/envs/pitcher_env.py", "w") as f:
   12 |     f.write(content)
````
