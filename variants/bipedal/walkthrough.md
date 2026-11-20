# ⚾ Phase 7: Full Infield Bipedal Defense & 1st Base Out/Safe Play

## 1. Executive Summary
In Phase 7, we achieved the complete multi-agent stadium realization of infield baseball defense and base running with three simultaneous Unitree H1 humanoid robots:
1. **10m Mound Pitcher (`p_`)**: Delivers realistic aerodynamic fastballs, sliders, and curveballs into the strike zone.
2. **6-DoF Floating-Base Batter-Runner (`b_`)**: Executes dynamic kinetic uncoiling swing, zero-weld bat drop prop handover at $t = 0.52\text{s}$, and high-speed bipedal sprint toward 1st base ($20.3\text{ km/h}$).
3. **6-DoF Floating-Base 1st Baseman Infielder (`f_`)**: Stands at 1st base with an athletic ready stance, equipped with a left-hand fielding glove ($r = 0.12\text{m}$), tracking and intercepting batted ground balls.
4. **3D Umpire Decision Engine**: Formally evaluates runner arrival time ($T_{runner}$) versus defensive play completion time ($T_{defense}$) with 1ms resolution to render definitive **OUT** vs **SAFE** calls with TV broadcast HUD graphics.

Both moving humanoids operate under strict unanchored 6-DoF floating-base dynamics without artificial guide rails, pin joints, or sky-hooks, achieving **100.0% balance survival (0 falls across all 50 benchmark episodes)**.

---

## 2. Quantitative 50-Episode Benchmark Results

Evaluating over 50 consecutive episodes with randomized pitch types (Fastball, Slider, Curveball) and live 4-stage execution:

| Metric | Phase 7 Measured Value | Target Criterion | Physical Assessment |
| :--- | :---: | :---: | :--- |
| **Batter Balance Survival Rate** | **100.0% (50/50)** | $100.0\%$ | **Zero falls across all 50 episodes (100% upright)** |
| **Fielder Balance Survival Rate** | **100.0% (50/50)** | $100.0\%$ | **Zero falls on unanchored 6-DoF pelvis (100% upright)** |
| **Bat Contact Success Rate** | **100.0% (50/50)** | $\ge 80.0\%$ | **All 3 pitch types met with solid barrel contact** |
| **Fair-Hit Grounder/Liner Rate** | **100.0% (50/50)** | $\ge 60.0\%$ | **100% batted into fair right infield territory** |
| **Fielder Intercept Rate** | **52.0% (26/50)** | $50.0 \sim 60.0\%$ | **Realistic fielding reach ($d_{xy} \le 1.65\text{m}$)** |
| **3D Umpire OUT Rate** | **52.0% (26/50)** | $40.0 \sim 60.0\%$ | **Fielded grounders beaten out to 1B ($T_{def} \le T_{1B}$)** |
| **3D Umpire SAFE Rate** | **48.0% (24/50)** | $40.0 \sim 60.0\%$ | **Unfielded/leak balls allow runner safe arrival** |
| **Mean Exit Velocity** | **39.14 km/h** | $32.0 \sim 48.0\text{ km/h}$ | **Authentic infield grounder exit speeds (up to 45.6 km/h)** |
| **Mean Runner Sprint Speed** | **20.34 km/h** | $20.0 \sim 25.0\text{ km/h}$ | **Bipedal sprint velocity along 1st baseline** |
| **Mean Batter Pelvis Z** | **0.969 m** | $\ge 0.85\text{ m}$ | **Rock-solid upright bipedal stance during swing & run** |
| **Mean Fielder Pelvis Z** | **0.885 m** | $\ge 0.80\text{ m}$ | **Stable fielding crouch posture without tipping** |

### Breakdown by Pitch Type
- **Fastball (19 episodes, mean speed 87.53 km/h)**: 100% contact, 100% fair hits, 47.4% fielded, **47.4% OUT / 52.6% SAFE**, 40.33 km/h exit velocity, 20.25 km/h sprint.
- **Curveball (14 episodes, mean speed 75.85 km/h)**: 100% contact, 100% fair hits, 50.0% fielded, **50.0% OUT / 50.0% SAFE**, 39.73 km/h exit velocity, 20.53 km/h sprint.
- **Slider (17 episodes, mean speed 78.05 km/h)**: 100% contact, 100% fair hits, 58.8% fielded, **58.8% OUT / 41.2% SAFE**, 37.33 km/h exit velocity, 20.30 km/h sprint.

---

## 3. Key Physical Breakthroughs & Architectural Solutions

### 1. Glove-Ball MuJoCo Pair Contact Penetration Bug Fix
- **Root Cause**: An initial `<pair geom1="f_glove" geom2="ball_geom">` contact specification created a $-13.5\text{ cm}$ negative penetration spike when the fielded ball was anchored into the glove pocket. MuJoCo's constraint solver produced an explosive $\approx 5,000\text{ N}$ normal contact force that drove the fielder's arm into the ground, violently destabilizing the 6-DoF pelvis.
- **Solution**: Designated `f_glove` as non-colliding (`contype="0" conaffinity="0"`), purged the `<pair>` element, and implemented smooth kinematic pocket attachment upon scoop. Zero force spikes, zero chatter.

### 2. Coordinate-Aligned Floating-Base Balance Controller for Skew Heading
- **Root Cause**: The 1st baseman stands angled at $\psi_0 = -135^\circ$ ($-2.356\text{ rad}$) facing home plate. Direct world $X/Y$ error feedback to ankle pitch and hip roll caused $45^\circ$ cross-axis coupling, causing the fielder to slide diagonally and lose balance.
- **Solution**: Decomposed pelvis error into local sagittal ($\mathbf{u}_{sag}$) and lateral ($\mathbf{u}_{lat}$) body axes:
  $$e_{sag} = \mathbf{e}_{pos} \cdot \mathbf{u}_{sag}, \quad e_{lat} = \mathbf{e}_{pos} \cdot \mathbf{u}_{lat}$$
  Routed $e_{sag}$ purely to ankle and hip pitch, $e_{lat}$ purely to hip roll, and added active yaw damping $+80\omega_z$ to hip yaw, achieving unconditional 100% balance survival.

### 3. Aerodynamic Pitch Arrival Synchronization
- Micro-step release scheduling (Fastball: step 3 / $t=0.06\text{s}$, Slider: step 1 / $t=0.02\text{s}$, Curveball: step 0 / $t=0.00\text{s}$) synchronized home plate arrival to a narrow $7\text{ms}$ window ($t \in [0.461\text{s}, 0.468\text{s}]$), enabling 100% barrel contact across all deliveries.

---

## 4. Visual Keyframe Verification

Keyframes extracted from the 50 FPS broadcast video (`logs/videos/phase7_infield_defense.mp4`):

### 1. Pitch & Swing (Step 22, $t = 0.44\text{s}$)
![Pitch & Swing](logs/phase7_pitch_and_swing.png)
*10m mound pitcher delivers an 87.4 km/h fastball; 6-DoF floating-base batter initiates uncoiling swing while 1st baseman readies in athletic stance.*

### 2. Bat Drop Prop Handover (Step 27, $t = 0.54\text{s}$)
![Bat Drop Handover](logs/phase7_bat_drop_and_sprint.png)
*Solid barrel impact launches a 45.6 km/h grounder into fair territory; batter drops the bat smoothly onto the turf and begins accelerating toward 1st base ($19.9\text{ km/h}$).*

### 3. Sprint vs Infield Defense Intercept (Step 53, $t = 1.06\text{s}$)
![Fielder Intercept](logs/phase7_fielder_intercept.png)
*1st baseman holds 6-DoF bipedal balance ($z = 0.99\text{m}$) and intercepts the ground ball with glove scoop; runner sprints at $20.2\text{ km/h}$ down the baseline.*

### 4. 1st Base Race & 3D Umpire Decision (Step 80, $t = 1.60\text{s}$)
![3D Umpire Call](logs/phase7_umpire_call.png)
*Fielder completes tag/throw at $T_{def} = 1.32\text{s}$ prior to runner arrival ($T_{1B} = 1.60\text{s}$); 3D Umpire Engine renders bold blue **OUT** call on broadcast HUD.*

---

## 5. Artifacts & Codebase
- [models/h1_infield_defense.xml](file:///Users/jin10000/Desktop/mini-project/bipedal_baseball/models/h1_infield_defense.xml): 3-humanoid stadium model (64 bodies, 61 joints, 57 actuators, 164 geoms).
- [envs/infield_defense_env.py](file:///Users/jin10000/Desktop/mini-project/bipedal_baseball/envs/infield_defense_env.py): 4-stage multi-agent environment with 3D Umpire Decision Engine.
- [scripts/build_infield_defense_xml.py](file:///Users/jin10000/Desktop/mini-project/bipedal_baseball/scripts/build_infield_defense_xml.py): XML compiler and geometry builder.
- [scripts/train_infield_defense.py](file:///Users/jin10000/Desktop/mini-project/bipedal_baseball/scripts/train_infield_defense.py): Multi-objective PPO training script.
- [scripts/eval_infield_defense.py](file:///Users/jin10000/Desktop/mini-project/bipedal_baseball/scripts/eval_infield_defense.py): 50-episode quantitative evaluator and broadcast renderer.
- `checkpoints/best_phase7_infield_defense_model.zip`: Phase 7 trained PPO model.
- `logs/videos/phase7_infield_defense.mp4`: 50 FPS broadcast video with TV-style HUD.
- `logs/phase7_benchmark_metrics.csv`: 50-episode quantitative metric log.
