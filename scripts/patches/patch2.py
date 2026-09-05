import re

with open("cognitive_ai/envs/pitcher_env.py", "r") as f:
    content = f.read()

content = content.replace(
    "self.data.qvel[self.qvel_adrs[i]] = 0.0",
    ""
)

with open("cognitive_ai/envs/pitcher_env.py", "w") as f:
    f.write(content)
