# ⚾ AI Robotic Baseball Simulator

A cutting-edge 3D baseball simulation framework powered by **MuJoCo Physics**, **Reinforcement Learning (Stable-Baselines3)**, and **Multi-Agent Architecture**.

This project evolves from a simple robotic arm throwing a ball into a fully automated, physics-accurate baseball match complete with MoCap pitching, dynamic aerodynamics, AI umpires, and a 9-inning game state machine.

## 🚀 Key Features

*   **Mega-Scale RL Pitcher & Batter:** Trained over millions of timesteps using PPO. The batter utilizes `VecFrameStack` (4-frame memory) to track ball acceleration and spin, while the pitcher utilizes Learning Rate Annealing for pinpoint strike zone control.
*   **Advanced Aerodynamics (Magnus Effect):** The environment mathematically simulates drag and Magnus lift. Fastballs rise (Lift), curveballs drop (Topspin), and sliders sweep (Break) based on the pitch type.
*   **Trampoline Effect Physics:** Contact between the bat and ball calculates realistic restitution (COR), multiplying exit velocity to simulate real-world home runs and foul balls.
*   **AI Umpire & Rule Engine:** A mathematically rigorous umpire evaluates 3D trajectories to call Strikes, Balls, Fair hits, Foul balls, and Home Runs precisely.
*   **Broadcast Director AI:** Automated OpenCV camera management that dynamically switches from a `catcher_cam` (pitching view) to a `tracking_cam` (ball follow view) upon bat contact, overlaying live umpire calls.
*   **Full 9-Inning State Machine:** Complete logical tracking of bases, outs, innings, balls, strikes, and scores to govern the flow of a standard baseball game.
*   **Robotic Fielders:** Custom XML models for legless, omni-wheeled catchers and runners built for efficient base-stealing and fielding RL training.

## 🛠 Tech Stack
*   **Physics Engine:** DeepMind MuJoCo (Python Bindings)
*   **Reinforcement Learning:** Stable-Baselines3 (PPO), Gymnasium
*   **Computer Vision / Rendering:** OpenCV, MuJoCo Renderer
*   **Language:** Python 3.11

## 📂 Architecture Overview
*   `/shared_assets/`: Contains all 3D XML robot models (`h1_pitcher.xml`, `h1_fielder.xml`, etc.)
*   `/cognitive_ai/envs/`: The core gym environments (`pitcher_env.py`, `batter_env.py`, `baseball_match_env.py`) blending physics and RL.
*   `/cognitive_ai/training/`: PPO training loops including the mega-architecture scaling scripts.
*   `/cognitive_ai/evaluation/`: Director scripts (`simulate_full_match.py`, `simulate_9_innings.py`) that stitch agents together into a coherent broadcast.
*   `/final_videos/`: Contains generated `.mp4` renders of the agents in action.

## 📺 Demo
To run the fully integrated broadcast match (Pitcher vs Batter with Umpire and camera switching):
```bash
python cognitive_ai/evaluation/simulate_full_match.py
```
*The resulting video will be saved in `data/eval_videos/phase_8_1_broadcast_match.mp4`.*
