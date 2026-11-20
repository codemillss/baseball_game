# baseball/archive/visualize_trained.py

원본: [archive/visualize_trained.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/visualize_trained.py)

SHA256: `5d94a64159ec4da6aa1742974e469038aeebcd07538d09df0b57b9101a32596e`

전체 73행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `prep_obs` | FunctionDef | 7 | 10 |
| `run_visualization` | FunctionDef | 12 | 70 |

## 전체 원문

````text
    1 | import torch
    2 | import numpy as np
    3 | import time
    4 | from envs.multi_agent_env import MultiAgentBaseballEnv, EnvConfig
    5 | from training.multi_agent_dreamer import SingleAgentBrain
    6 | 
    7 | def prep_obs(obs, device):
    8 |     vision = torch.tensor(obs["vision"], dtype=torch.float32, device=device).unsqueeze(0).permute(0, 3, 1, 2) / 255.0
    9 |     prop = torch.tensor(obs["proprioception"], dtype=torch.float32, device=device).unsqueeze(0)
   10 |     return {"vision": vision, "proprioception": prop}
   11 | 
   12 | def run_visualization():
   13 |     print("Loading Trained Weights for Visualization...")
   14 |     device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
   15 |     
   16 |     config = EnvConfig(mode="batter_only", is_tee_ball=False, pitch_speed_y=-25.0, strike_zone_scale=3.0)
   17 |     env = MultiAgentBaseballEnv(config=config)
   18 |     
   19 |     batter = SingleAgentBrain("batter", prop_dim=18, action_dim=9, device=device)
   20 |     
   21 |     # Load weights
   22 |     try:
   23 |         batter.load_weights("runs/batter_drills_20260729_151058/batter_final.pt")
   24 |         print("Successfully loaded batter_final.pt")
   25 |     except Exception as e:
   26 |         print("Failed to load weights:", e)
   27 |         return
   28 | 
   29 |     from mujoco import viewer
   30 |     v = viewer.launch_passive(env.model, env.data)
   31 |     
   32 |     print("Starting 5 Episodes of Visualization...")
   33 |     for ep in range(5):
   34 |         obs, _ = env.reset()
   35 |         h, z = batter.rssm.initial_state(1, device)
   36 |         
   37 |         # Initial observe
   38 |         obs_dict = prep_obs(obs["batter"], device)
   39 |         h, z, _ = batter.rssm.observe(obs_dict, torch.zeros(1, 9, device=device), h, z)
   40 |         
   41 |         for step in range(300):
   42 |             # Agent takes action
   43 |             with torch.no_grad():
   44 |                 a_b, _ = batter.actor.get_action(batter.rssm.get_state(h, z))
   45 |                 
   46 |             act_p_np = np.zeros(8, dtype=np.float32)
   47 |             act_b_np = a_b.squeeze(0).cpu().numpy()
   48 |             act_f_np = np.zeros(3, dtype=np.float32)
   49 |             
   50 |             # Auto-pitch in batter drills
   51 |             if config.mode == "batter_only":
   52 |                 act_p_np[7] = 1.0
   53 |                 
   54 |             next_obs, rewards, terminated, truncated, _ = env.step({"pitcher": act_p_np, "batter": act_b_np, "fielder": act_f_np})
   55 |             
   56 |             v.sync()
   57 |             time.sleep(0.02) # 50 FPS
   58 |             
   59 |             if terminated["__all__"] or truncated["__all__"]:
   60 |                 break
   61 |                 
   62 |             # Observe next state for RNN
   63 |             with torch.no_grad():
   64 |                 obs_dict = prep_obs(next_obs["batter"], device)
   65 |                 h, z, _ = batter.rssm.observe(obs_dict, a_b, h, z)
   66 |                 
   67 |         print(f"Episode {ep+1} finished.")
   68 |         time.sleep(1)
   69 |         
   70 |     v.close()
   71 | 
   72 | if __name__ == "__main__":
   73 |     run_visualization()
````
