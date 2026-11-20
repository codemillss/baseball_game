# baseball/scripts/patches/patch_info.py

원본: [scripts/patches/patch_info.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/patch_info.py)

SHA256: `74ff3f959ad01f5b1daa5f697cbbd9dc3b9d88b4c6991886f50e5fbf9dbefc56`

전체 10행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    2 |     content = f.read()
    3 | 
    4 | content = content.replace(
    5 |     'return self.get_observations(), reward, terminated, truncated, {"outcome": self.outcome',
    6 |     'return self.get_observations(), reward, terminated, truncated, {"pitch_speed": self.pitch_speed_kmh, "outcome": self.outcome'
    7 | )
    8 | 
    9 | with open("cognitive_ai/envs/baseball_match_env.py", "w") as f:
   10 |     f.write(content)
````
