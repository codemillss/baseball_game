"""
visualize_latent.py — World Model 잠재 공간(Latent Space) 시각화

학습된 World Model(투수/타자)의 잠재 상태(z_t)를 수집한 후,
UMAP을 사용해 2D로 축소하여 시각화합니다.
서로 다른 상황(예: 스트라이크 vs 볼, 헛스윙 vs 컨택)이 
잠재 공간 상에서 군집화(Clustering)되는지 확인할 수 있습니다.
"""

import torch
import numpy as np
import matplotlib.pyplot as plt
import umap
from pathlib import Path
from training.multi_agent_world_model import BaseballVisionRSSM
from envs.multi_agent_env import MultiAgentBaseballEnv

def collect_latent_states(rssm: BaseballVisionRSSM, env: MultiAgentBaseballEnv, agent_type: str, num_episodes: int = 10):
    device = next(rssm.parameters()).device
    latents = []
    labels = []  # 0: 볼, 1: 스트라이크, 2: 컨택
    
    for ep in range(num_episodes):
        obs, _ = env.reset()
        h, z = rssm.initial_state(1, device)
        done = False
        
        while not done:
            def prep_obs(o):
                v = torch.tensor(o["vision"], dtype=torch.float32, device=device).permute(2, 0, 1).unsqueeze(0) / 255.0
                p = torch.tensor(o["proprioception"], dtype=torch.float32, device=device).unsqueeze(0)
                return {"vision": v, "proprioception": p}

            obs_agent = prep_obs(obs[agent_type])
            a_dummy = torch.zeros(1, 8 if agent_type == 'pitcher' else 9, device=device)
            
            h, z, _ = rssm.observe(obs_agent, a_dummy, h, z)
            state = rssm.get_state(h, z).squeeze(0).cpu().detach().numpy()
            latents.append(state)
            
            # Action (Random for collection)
            act_p = np.random.uniform(-1, 1, size=8)
            if np.random.rand() < 0.1: act_p[7] = 1.0 # Release ball
            act_b = np.random.uniform(-1, 1, size=9)
            
            obs, rew, term, trunc, info = env.step({"pitcher": act_p, "batter": act_b})
            done = term["__all__"] or trunc["__all__"]
            
            # Label based on reward logic
            if info.get(agent_type, {}).get("contact", False):
                labels.append(2)
            elif rew[agent_type] > 1.0: # Strike / Swing
                labels.append(1)
            else:
                labels.append(0)
                
    return np.array(latents), np.array(labels)

def visualize_umap(latents, labels, title="Latent Space (UMAP)", filename="umap.png"):
    print(f"Running UMAP on {len(latents)} latent states...")
    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, metric='euclidean')
    embedding = reducer.fit_transform(latents)
    
    plt.figure(figsize=(8, 6))
    scatter = plt.scatter(embedding[:, 0], embedding[:, 1], c=labels, cmap='viridis', s=10, alpha=0.7)
    cbar = plt.colorbar(scatter)
    cbar.set_ticks([0, 1, 2])
    cbar.set_ticklabels(['Ball', 'Strike/Swing', 'Contact'])
    
    plt.title(title)
    plt.tight_layout()
    plt.savefig(filename)
    print(f"Saved visualization to {filename}")

if __name__ == "__main__":
    device = torch.device("cpu")
    print("Loading Pitcher World Model...")
    pitcher_rssm = BaseballVisionRSSM(15, 8).to(device)
    
    # In practice, you would load a trained checkpoint here
    # pitcher_rssm.load_state_dict(torch.load("checkpoints/pitcher_wm.pt"))
    
    env = MultiAgentBaseballEnv(render_mode="rgb_array")
    
    print("Collecting data (this may take a moment due to rendering)...")
    latents, labels = collect_latent_states(pitcher_rssm, env, "pitcher", num_episodes=5)
    
    visualize_umap(latents, labels, title="Pitcher Latent Space (Untrained)", filename="pitcher_umap.png")
