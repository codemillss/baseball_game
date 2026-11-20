# baseball/archive/training/visualize_latent.py

원본: [archive/training/visualize_latent.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/visualize_latent.py)

SHA256: `7cba43aa0ea886260b50aede7af4b823ad96fe69c24917964e55a043ad85a681`

전체 88행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `collect_latent_states` | FunctionDef | 18 | 57 |
| `prep_obs` | FunctionDef | 29 | 32 |
| `visualize_umap` | FunctionDef | 59 | 73 |

## 전체 원문

````text
    1 | """
    2 | visualize_latent.py — World Model 잠재 공간(Latent Space) 시각화
    3 | 
    4 | 학습된 World Model(투수/타자)의 잠재 상태(z_t)를 수집한 후,
    5 | UMAP을 사용해 2D로 축소하여 시각화합니다.
    6 | 서로 다른 상황(예: 스트라이크 vs 볼, 헛스윙 vs 컨택)이 
    7 | 잠재 공간 상에서 군집화(Clustering)되는지 확인할 수 있습니다.
    8 | """
    9 | 
   10 | import torch
   11 | import numpy as np
   12 | import matplotlib.pyplot as plt
   13 | import umap
   14 | from pathlib import Path
   15 | from training.multi_agent_world_model import BaseballVisionRSSM
   16 | from envs.multi_agent_env import MultiAgentBaseballEnv
   17 | 
   18 | def collect_latent_states(rssm: BaseballVisionRSSM, env: MultiAgentBaseballEnv, agent_type: str, num_episodes: int = 10):
   19 |     device = next(rssm.parameters()).device
   20 |     latents = []
   21 |     labels = []  # 0: 볼, 1: 스트라이크, 2: 컨택
   22 |     
   23 |     for ep in range(num_episodes):
   24 |         obs, _ = env.reset()
   25 |         h, z = rssm.initial_state(1, device)
   26 |         done = False
   27 |         
   28 |         while not done:
   29 |             def prep_obs(o):
   30 |                 v = torch.tensor(o["vision"], dtype=torch.float32, device=device).permute(2, 0, 1).unsqueeze(0) / 255.0
   31 |                 p = torch.tensor(o["proprioception"], dtype=torch.float32, device=device).unsqueeze(0)
   32 |                 return {"vision": v, "proprioception": p}
   33 | 
   34 |             obs_agent = prep_obs(obs[agent_type])
   35 |             a_dummy = torch.zeros(1, 8 if agent_type == 'pitcher' else 9, device=device)
   36 |             
   37 |             h, z, _ = rssm.observe(obs_agent, a_dummy, h, z)
   38 |             state = rssm.get_state(h, z).squeeze(0).cpu().detach().numpy()
   39 |             latents.append(state)
   40 |             
   41 |             # Action (Random for collection)
   42 |             act_p = np.random.uniform(-1, 1, size=8)
   43 |             if np.random.rand() < 0.1: act_p[7] = 1.0 # Release ball
   44 |             act_b = np.random.uniform(-1, 1, size=9)
   45 |             
   46 |             obs, rew, term, trunc, info = env.step({"pitcher": act_p, "batter": act_b})
   47 |             done = term["__all__"] or trunc["__all__"]
   48 |             
   49 |             # Label based on reward logic
   50 |             if info.get(agent_type, {}).get("contact", False):
   51 |                 labels.append(2)
   52 |             elif rew[agent_type] > 1.0: # Strike / Swing
   53 |                 labels.append(1)
   54 |             else:
   55 |                 labels.append(0)
   56 |                 
   57 |     return np.array(latents), np.array(labels)
   58 | 
   59 | def visualize_umap(latents, labels, title="Latent Space (UMAP)", filename="umap.png"):
   60 |     print(f"Running UMAP on {len(latents)} latent states...")
   61 |     reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, metric='euclidean')
   62 |     embedding = reducer.fit_transform(latents)
   63 |     
   64 |     plt.figure(figsize=(8, 6))
   65 |     scatter = plt.scatter(embedding[:, 0], embedding[:, 1], c=labels, cmap='viridis', s=10, alpha=0.7)
   66 |     cbar = plt.colorbar(scatter)
   67 |     cbar.set_ticks([0, 1, 2])
   68 |     cbar.set_ticklabels(['Ball', 'Strike/Swing', 'Contact'])
   69 |     
   70 |     plt.title(title)
   71 |     plt.tight_layout()
   72 |     plt.savefig(filename)
   73 |     print(f"Saved visualization to {filename}")
   74 | 
   75 | if __name__ == "__main__":
   76 |     device = torch.device("cpu")
   77 |     print("Loading Pitcher World Model...")
   78 |     pitcher_rssm = BaseballVisionRSSM(15, 8).to(device)
   79 |     
   80 |     # In practice, you would load a trained checkpoint here
   81 |     # pitcher_rssm.load_state_dict(torch.load("checkpoints/pitcher_wm.pt"))
   82 |     
   83 |     env = MultiAgentBaseballEnv(render_mode="rgb_array")
   84 |     
   85 |     print("Collecting data (this may take a moment due to rendering)...")
   86 |     latents, labels = collect_latent_states(pitcher_rssm, env, "pitcher", num_episodes=5)
   87 |     
   88 |     visualize_umap(latents, labels, title="Pitcher Latent Space (Untrained)", filename="pitcher_umap.png")
````
