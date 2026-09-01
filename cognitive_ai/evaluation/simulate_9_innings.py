import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import time
from cognitive_ai.envs.baseball_game_state import BaseballGameState
import random

def simulate_game():
    game = BaseballGameState()
    print("=======================================================")
    print("🏟️  FULL 9-INNING BASEBALL SIMULATION START")
    print("=======================================================")
    
    while game.inning <= 9:
        # Simulate AI Umpire outcomes for speed
        # In the full system, this is fed by the MuJoCo + PPO environment
        r = random.random()
        if r < 0.1: outcome = "HOME RUN"
        elif r < 0.3: outcome = "FAIR"
        elif r < 0.4: outcome = "FOUL"
        elif r < 0.7: outcome = "STRIKE"
        else: outcome = "BALL"
        
        if outcome in ["STRIKE", "BALL"]:
            game.handle_pitch(outcome)
        else:
            game.handle_hit(outcome)
            
        print(f"Outcome: {outcome.ljust(10)} | {game.get_scoreboard()}")
        time.sleep(0.01) # fast simulation
        
    print("=======================================================")
    print(f"🏆 FINAL SCORE: AWAY {game.score_away} - {game.score_home} HOME")
    print("=======================================================")

if __name__ == "__main__":
    simulate_game()
