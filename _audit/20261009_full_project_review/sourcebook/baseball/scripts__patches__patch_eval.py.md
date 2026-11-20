# baseball/scripts/patches/patch_eval.py

원본: [scripts/patches/patch_eval.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/patch_eval.py)

SHA256: `5dfd6de59ff99e80c4e52d3107625aa243284dacee00d235c6f4bad61e647cc8`

전체 20행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | with open("cognitive_ai/evaluation/evaluate_mocap_match.py", "r") as f:
    2 |     content = f.read()
    3 | 
    4 | # Read speed and exit vel from info instead of b_env
    5 | content = content.replace(
    6 |     "speed = getattr(b_env, 'pitch_speed_kmh', 0.0)",
    7 |     "speed = info.get('release_speed_kmh', 0.0)"
    8 | )
    9 | content = content.replace(
   10 |     "exit_vel = getattr(b_env, 'exit_velocity_kmh', 0.0)",
   11 |     "exit_vel = info.get('exit_velocity_kmh', 0.0)"
   12 | )
   13 | content = content.replace(
   14 |     "dist = getattr(b_env, 'batted_distance', 0.0)",
   15 |     "dist = info.get('batted_distance', 0.0)"
   16 | )
   17 | # Wait, info might not have 'release_speed_kmh'. Let's see what info returns.
   18 | # BaseballMatchEnv step returns info:
   19 | # info = {"outcome": self.outcome, "is_in_strike_zone": is_strike, "has_contacted": self.has_contacted, "exit_velocity_kmh": self.exit_velocity_kmh, "batted_distance": self.batted_distance, "pitch_speed": self.pitch_speed_kmh}
   20 | # Ah, I didn't export pitch_speed. I'll just change the getattr to be inside the while loop BEFORE done resets the env!
````
