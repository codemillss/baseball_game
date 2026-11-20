# baseball/scripts/patches/debug_action.py

원본: [scripts/patches/debug_action.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/debug_action.py)

SHA256: `b72afeeeb51b9670c89e0169c157dab1c0530925772a5d27c9b5e93fd0a45cb9`

전체 5행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | from cognitive_ai.envs.runner_env import RunnerEnv
    2 | env = RunnerEnv()
    3 | obs = env.reset()
    4 | print(env.action_space)
    5 | print(env.action_space.sample())
````
