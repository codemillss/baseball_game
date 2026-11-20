# baseball/README.md

원본: [README.md](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/README.md)

SHA256: `78d408abd1ee3c7f33971f2c494df20c5d104a1ea472475173a44077b4b6c9ba`

전체 53행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | # ⚾ AI Robotic Baseball Simulator
    2 | 
    3 | A cutting-edge 3D baseball simulation framework powered by **MuJoCo Physics**, **Reinforcement Learning (Stable-Baselines3)**, and **Multi-Agent Architecture**.
    4 | 
    5 | This project evolves from a simple robotic arm throwing a ball into a fully automated, physics-accurate baseball match complete with MoCap pitching, dynamic aerodynamics, AI umpires, and a 9-inning game state machine.
    6 | 
    7 | ---
    8 | 
    9 | ## 📚 Publications & Comprehensive Documentation
   10 | 
   11 | All technical documentation, peer reviews, and papers have been organized into the [`docs/`](docs/) directory:
   12 | 
   13 | | Document | Format | Description |
   14 | | :--- | :---: | :--- |
   15 | | **🌐 [Interactive Web Monograph](https://codemillss.github.io/baseball_game/)** | **HTML (Live)** | Fully interactive web paper with dark/light mode, lightbox keyframe gallery, and peer review. *(Hosted via GitHub Pages)* |
   16 | | **📥 [30-Page Technical Report (PDF)](docs/REPORT.pdf)** | **PDF (20MB)** | Official publication-grade PDF report with complete formulas, 69 high-res figures, and retrospectives. |
   17 | | **📄 [Academic Paper (Markdown)](docs/PAPER.md)** | **Markdown** | In-depth research paper structured as Introduction - Why - What - How - So What - Retrospective. |
   18 | | **🧪 [Experiment Logs](docs/EXPERIMENT_LOG.md)** | **Markdown** | Chronological record of training parameters and milestone outcomes. |
   19 | | **🎥 [Video Catalog](docs/VIDEO_CATALOG.md)** | **Markdown** | Comprehensive catalog of all 15 phase experiment evaluation videos. |
   20 | 
   21 | ---
   22 | 
   23 | ## 🚀 Key Features
   24 | 
   25 | *   **Mega-Scale RL Pitcher & Batter:** Trained over millions of timesteps using PPO. The batter utilizes `VecFrameStack` (4-frame memory) to track ball acceleration and spin, while the pitcher utilizes Learning Rate Annealing for pinpoint strike zone control.
   26 | *   **Advanced Aerodynamics (Magnus Effect):** The environment mathematically simulates drag and Magnus lift. Fastballs rise (Lift), curveballs drop (Topspin), and sliders sweep (Break) based on the pitch type.
   27 | *   **Trampoline Effect Physics:** Contact between the bat and ball calculates realistic restitution (COR), multiplying exit velocity to simulate real-world home runs and foul balls.
   28 | *   **AI Umpire & Rule Engine:** A mathematically rigorous umpire evaluates 3D trajectories to call Strikes, Balls, Fair hits, Foul balls, and Home Runs precisely.
   29 | *   **Broadcast Director AI:** Automated OpenCV camera management that dynamically switches from a `catcher_cam` (pitching view) to a `tracking_cam` (ball follow view) upon bat contact, overlaying live umpire calls.
   30 | *   **Full 9-Inning State Machine:** Complete logical tracking of bases, outs, innings, balls, strikes, and scores to govern the flow of a standard baseball game.
   31 | *   **Robotic Fielders:** Custom XML models for legless, omni-wheeled catchers and runners built for efficient base-stealing and fielding RL training.
   32 | 
   33 | ## 🛠 Tech Stack
   34 | *   **Physics Engine:** DeepMind MuJoCo (Python Bindings)
   35 | *   **Reinforcement Learning:** Stable-Baselines3 (PPO), Gymnasium
   36 | *   **Computer Vision / Rendering:** OpenCV, MuJoCo Renderer
   37 | *   **Language:** Python 3.11
   38 | 
   39 | ## 📂 Architecture Overview
   40 | *   `/shared_assets/`: Contains all 3D XML robot models (`h1_pitcher.xml`, `h1_fielder.xml`, etc.)
   41 | *   `/cognitive_ai/envs/`: The core gym environments (`pitcher_env.py`, `batter_env.py`, `baseball_match_env.py`) blending physics and RL.
   42 | *   `/cognitive_ai/training/`: PPO training loops including the mega-architecture scaling scripts.
   43 | *   `/cognitive_ai/evaluation/`: Director scripts (`simulate_full_match.py`, `simulate_9_innings.py`) that stitch agents together into a coherent broadcast.
   44 | *   `/final_videos/`: Contains generated `.mp4` renders of the agents in action.
   45 | *   `/docs/`: Comprehensive reports, interactive web monograph, 30-page PDF, and research papers.
   46 | *   `/scripts/`: Diagnostic and patch tools.
   47 | 
   48 | ## 📺 Demo
   49 | To run the fully integrated broadcast match (Pitcher vs Batter with Umpire and camera switching):
   50 | ```bash
   51 | ./run_demo.sh
   52 | ```
   53 | *The resulting video will be saved in `data/eval_videos/phase_8_1_broadcast_match.mp4`.*
````
