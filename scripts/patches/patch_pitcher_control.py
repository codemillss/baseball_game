import re

with open("cognitive_ai/envs/pitcher_env.py", "r") as f:
    content = f.read()

# We want to add a strike zone reward in the step() function where it calculates distance.
# Currently it uses self.target_x, self.target_z.
# Let's see how the reward is calculated.
