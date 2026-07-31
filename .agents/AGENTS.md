# Baseball AI Project Core Rules & Context

This file contains the core project context and architectural principles for the 3D Baseball AI project. Agents must strictly adhere to these principles when writing code or making design decisions in this workspace.

## 1. Core Architecture (Egocentric Vision)
- **Environment**: MuJoCo 3D physics (`stadium_3d.xml`).
- **Observation Space**: STRICTLY Egocentric Vision. Pitchers only see through `pitcher_cam`, Batters through `batter_cam`, Fielders through `fielder_cam`. 
- **Anti-Cheating Rule**: NEVER pass global ground-truth states (like exact ball 3D coordinates) directly into the neural network observations. The agents must infer the ball's position solely from their 64x64 pixel vision and their proprioception.

## 2. Agent Definitions
- **Batter**: 9-DOF fixed-base robotic arm.
- **Pitcher**: 8-DOF fixed-base robotic arm with a manual `release_intent` action.
- **Fielder**: 3-DOF mobile robot (X, Y sliding + Glove pitch).

## 3. Curriculum Learning Strategy (CRITICAL)
- **NO Tabula Rasa Self-Play**: Do NOT train agents adversarially from scratch. This leads to the "Moving Target Problem", Noisy Gradients, and Degenerate Equilibria (e.g., Pitcher refusing to throw, Batter bunting forever).
- **Isolated Drills First**: Agents MUST be trained in isolated modes first (`batter_drills`, `pitcher_drills`, `fielder_drills`) using the `EnvConfig` wrapper in `multi_agent_env.py` (e.g., Tee-ball mode for batter).
- **Reward Shaping**: Use `bat_speed_reward` and non-swing penalties to prevent reward hacking (infinite bunting).

## 4. Future Scaling (9v9)
- **Parameter Sharing**: Use a single `FielderBrain` and duplicate its weights across all fielders to save compute.
- **Communication**: To coordinate (e.g., avoid collisions), fielders will eventually share latent vectors via a Transformer network.
