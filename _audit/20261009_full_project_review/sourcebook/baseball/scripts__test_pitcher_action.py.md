# baseball/scripts/test_pitcher_action.py

원본: [scripts/test_pitcher_action.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/test_pitcher_action.py)

SHA256: `c492b9c75a4f42b5fe90e05ddac8f3a9ba46ddd4ee8376fe112538015fe8625a`

전체 25행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | from cognitive_ai.envs.pitcher_env import PitcherEnv
    2 | from stable_baselines3 import PPO
    3 | from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    4 | import numpy as np
    5 | 
    6 | env = DummyVecEnv([lambda: PitcherEnv()])
    7 | env = VecNormalize.load("checkpoints/mocap_pitcher_vec_normalize.pkl", env)
    8 | env.training = False
    9 | 
   10 | model = PPO.load("checkpoints/mocap_pitcher_best/best_model")
   11 | 
   12 | obs = env.reset()
   13 | action, _ = model.predict(obs, deterministic=True)
   14 | print(f"PitcherEnv action: {action}")
   15 | 
   16 | from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
   17 | b_env = DummyVecEnv([lambda: BatterMatchTrainingEnv(
   18 |     pitcher_model_path="checkpoints/mocap_pitcher_best/best_model",
   19 |     pitcher_norm_path="checkpoints/mocap_pitcher_vec_normalize.pkl"
   20 | )])
   21 | b_obs = b_env.reset()
   22 | # We can access pitcher action by stepping once
   23 | b_env.step(np.array([[0.0, 0.0, 0.0]]))
   24 | print(f"BatterMatchTrainingEnv stepped successfully!")
   25 | 
````
