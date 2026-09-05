from cognitive_ai.envs.runner_env import RunnerEnv
env = RunnerEnv()
obs = env.reset()
print(env.action_space)
print(env.action_space.sample())
