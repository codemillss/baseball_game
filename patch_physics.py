import re

with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    content = f.read()

# We will inject `_apply_aerodynamics` into `BaseballMatchEnv`
# First, let's find the step() method.
print(content.find("def step(self, action):"))
