with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    content = f.read()

content = content.replace(
    'return self.get_observations(), reward, terminated, truncated, {"outcome": self.outcome',
    'return self.get_observations(), reward, terminated, truncated, {"pitch_speed": self.pitch_speed_kmh, "outcome": self.outcome'
)

with open("cognitive_ai/envs/baseball_match_env.py", "w") as f:
    f.write(content)
