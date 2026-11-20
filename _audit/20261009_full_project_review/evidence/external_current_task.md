# Phase 12: Human-like Batter Biomechanics & Rock-Solid Catcher Balance

## Tasks

- [x] **Step 1**: Diagnose current problems in env
- [x] **Step 2**: Apply targeted fixes to `athletic_duel_env.py`
  - [x] 2a. Strengthen lead-foot plant (4000×spring, 120N)
  - [x] 2b. Strengthen catcher torques (2200 / 2800 / 800 Kp)
  - [x] 2c. Tighten catcher fallen threshold (0.40→0.45)
  - [x] 2d. Torso Kp 800→850 (stronger waist rotation)
  - [x] 2e. Left-foot planted reward 1.5→3.5
  - [x] 2f. Catcher drift reward + fall -20 penalty
  - [x] 2g. Off-speed pitch height blend prediction (0.35s window)
  - [x] 2h. Calibrated leg Kp for swing-vs-stability balance
- [x] **Step 3**: PPO training (25k steps)
- [x] **Step 4**: Fine-tune (50k more steps) — 65k total, ep_rew_mean=549
- [x] **Step 5**: 50-episode benchmark eval
  - Lead foot: 0.00cm ✅
  - Hand distance: 0.45cm ✅
  - Fastball: 93.3% ✅
  - Curveball: 50.0% ✅
  - Slider: 10.5% ✅
  - Peak exit: 105.3 km/h ✅
- [x] **Step 6**: Render multi-cam GIFs + keyframes
- [x] **Step 7**: Visual inspect — batter left foot flat, arms together, waist rotating, catcher squat stable ✅
- [x] **Step 8**: Append Entry 12 to RESEARCH_LOG.md (with final results)
- [x] **Step 9**: Update walkthrough.md
- [x] **Step 10**: Local git commit `ec3f854`
