# bipedal/envs/__init__.py

원본: [envs/__init__.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/envs/__init__.py)

SHA256: `3a49867010b71d9d58d2867b7e7214f1200e17d0ac65f489a740c29f8811b3a1`

전체 27행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | from gymnasium.envs.registration import register
    2 | 
    3 | try:
    4 |     from bipedal_baseball.envs.directional_batting_env import DirectionalBattingEnv
    5 |     from bipedal_baseball.envs.bipedal_duel_env import BipedalDuelEnv
    6 |     _entry = "bipedal_baseball.envs.directional_batting_env:DirectionalBattingEnv"
    7 |     _duel_entry = "bipedal_baseball.envs.bipedal_duel_env:BipedalDuelEnv"
    8 | except ModuleNotFoundError:
    9 |     from envs.directional_batting_env import DirectionalBattingEnv
   10 |     from envs.bipedal_duel_env import BipedalDuelEnv
   11 |     _entry = "envs.directional_batting_env:DirectionalBattingEnv"
   12 |     _duel_entry = "envs.bipedal_duel_env:BipedalDuelEnv"
   13 | 
   14 | register(
   15 |     id="DirectionalBatting-v0",
   16 |     entry_point=_entry,
   17 |     max_episode_steps=40,
   18 | )
   19 | 
   20 | register(
   21 |     id="BipedalDuel-v0",
   22 |     entry_point=_duel_entry,
   23 |     max_episode_steps=55,
   24 | )
   25 | 
   26 | __all__ = ["DirectionalBattingEnv", "BipedalDuelEnv"]
   27 | 
````
