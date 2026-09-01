import os
import sys
import time
from stable_baselines3 import PPO

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cognitive_ai.envs.teeball_env import TeeBallEnv

def watch_trained_agent():
    print("🚀 Loading Trained Tee-ball Agent...")
    
    # Load the best model or final model
    model_path = "checkpoints/teeball_best_model/best_model"
    if not os.path.exists(model_path + ".zip"):
        model_path = "checkpoints/teeball_final_model"
        
    if not os.path.exists(model_path + ".zip"):
        print(f"❌ Model not found at {model_path}. Run training first.")
        return
        
    model = PPO.load(model_path)
    env = TeeBallEnv(xml_path="shared_assets/h1_baseball.xml", render_mode="human")
    
    print("⚾ Agent loaded! Starting simulation... (Close window or Ctrl+C to stop)")
    
    ep = 0
    try:
        while True:
            ep += 1
            obs, _ = env.reset()
            done = False
            step = 0
            
            while not done:
                action, _states = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                step += 1
                
                # Smooth viewing
                time.sleep(0.02)
                
                if reward > 50:
                    print(f"💥 [Episode {ep}] HIT THE BALL! (Ball Z: {obs[2]:.2f}m, Step: {step})")
                    
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
    finally:
        env.close()

if __name__ == "__main__":
    watch_trained_agent()
