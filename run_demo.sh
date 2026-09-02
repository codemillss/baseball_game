#!/bin/bash
echo "=================================================="
echo "⚾ STARTING AI BASEBALL SIMULATOR DEMO ⚾"
echo "=================================================="
echo "1. Simulating a Full Broadcast Match (Pitcher vs Batter)..."
.venv/bin/python cognitive_ai/evaluation/simulate_full_match.py
echo ""
echo "2. Simulating a Base Stealing Attempt..."
.venv/bin/python cognitive_ai/evaluation/evaluate_base_stealing.py
echo ""
echo "3. Simulating a full 9-Inning Game State Machine (Text)..."
.venv/bin/python cognitive_ai/evaluation/simulate_9_innings.py | head -n 25
echo "..."
echo ""
echo "✅ Demo Complete! Check the 'final_videos/' directory for rendered MP4s."
