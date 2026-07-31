import torch
import numpy as np
import time
from envs.multi_agent_env import MultiAgentBaseballEnv, EnvConfig
from training.multi_agent_dreamer import SingleAgentBrain

def prep_obs(obs, device):
    vision = torch.tensor(obs["vision"], dtype=torch.float32, device=device).unsqueeze(0).permute(0, 3, 1, 2) / 255.0
    prop = torch.tensor(obs["proprioception"], dtype=torch.float32, device=device).unsqueeze(0)
    return {"vision": vision, "proprioception": prop}

def run_visualization():
    print("Loading Trained Weights for Visualization...")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    
    config = EnvConfig(mode="batter_only", is_tee_ball=False, pitch_speed_y=-25.0, strike_zone_scale=3.0)
    env = MultiAgentBaseballEnv(config=config)
    
    batter = SingleAgentBrain("batter", prop_dim=18, action_dim=9, device=device)
    
    # Load weights
    try:
        batter.load_weights("runs/batter_drills_20260729_151058/batter_final.pt")
        print("Successfully loaded batter_final.pt")
    except Exception as e:
        print("Failed to load weights:", e)
        return

    from mujoco import viewer
    v = viewer.launch_passive(env.model, env.data)
    
    print("Starting 5 Episodes of Visualization...")
    for ep in range(5):
        obs, _ = env.reset()
        h, z = batter.rssm.initial_state(1, device)
        
        # Initial observe
        obs_dict = prep_obs(obs["batter"], device)
        h, z, _ = batter.rssm.observe(obs_dict, torch.zeros(1, 9, device=device), h, z)
        
        for step in range(300):
            # Agent takes action
            with torch.no_grad():
                a_b, _ = batter.actor.get_action(batter.rssm.get_state(h, z))
                
            act_p_np = np.zeros(8, dtype=np.float32)
            act_b_np = a_b.squeeze(0).cpu().numpy()
            act_f_np = np.zeros(3, dtype=np.float32)
            
            # Auto-pitch in batter drills
            if config.mode == "batter_only":
                act_p_np[7] = 1.0
                
            next_obs, rewards, terminated, truncated, _ = env.step({"pitcher": act_p_np, "batter": act_b_np, "fielder": act_f_np})
            
            v.sync()
            time.sleep(0.02) # 50 FPS
            
            if terminated["__all__"] or truncated["__all__"]:
                break
                
            # Observe next state for RNN
            with torch.no_grad():
                obs_dict = prep_obs(next_obs["batter"], device)
                h, z, _ = batter.rssm.observe(obs_dict, a_b, h, z)
                
        print(f"Episode {ep+1} finished.")
        time.sleep(1)
        
    v.close()

if __name__ == "__main__":
    run_visualization()
