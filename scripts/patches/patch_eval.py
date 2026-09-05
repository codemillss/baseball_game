with open("cognitive_ai/evaluation/evaluate_mocap_match.py", "r") as f:
    content = f.read()

# Read speed and exit vel from info instead of b_env
content = content.replace(
    "speed = getattr(b_env, 'pitch_speed_kmh', 0.0)",
    "speed = info.get('release_speed_kmh', 0.0)"
)
content = content.replace(
    "exit_vel = getattr(b_env, 'exit_velocity_kmh', 0.0)",
    "exit_vel = info.get('exit_velocity_kmh', 0.0)"
)
content = content.replace(
    "dist = getattr(b_env, 'batted_distance', 0.0)",
    "dist = info.get('batted_distance', 0.0)"
)
# Wait, info might not have 'release_speed_kmh'. Let's see what info returns.
# BaseballMatchEnv step returns info:
# info = {"outcome": self.outcome, "is_in_strike_zone": is_strike, "has_contacted": self.has_contacted, "exit_velocity_kmh": self.exit_velocity_kmh, "batted_distance": self.batted_distance, "pitch_speed": self.pitch_speed_kmh}
# Ah, I didn't export pitch_speed. I'll just change the getattr to be inside the while loop BEFORE done resets the env!
