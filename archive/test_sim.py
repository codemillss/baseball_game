import numpy as np
from envs.multi_agent_env import MultiAgentBaseballEnv, EnvConfig

config = EnvConfig(mode="batter_only", is_tee_ball=False, pitch_speed_y=-25.0)
env = MultiAgentBaseballEnv(config=config, render_mode="rgb_array")
env.reset()

print("Initial Ball Pos:", env.data.xpos[env.ball_body_id])
for i in range(10):
    actions = {
        "pitcher": np.zeros(8, dtype=np.float32),
        "batter": np.zeros(9, dtype=np.float32),
        "fielder": np.zeros(3, dtype=np.float32)
    }
    env.step(actions)
    print(f"Step {i+1} Ball Pos:", env.data.xpos[env.ball_body_id], "Vel:", env.data.qvel[env.ball_qvel_adr:env.ball_qvel_adr+3])
