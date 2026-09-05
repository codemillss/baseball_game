from gymnasium.envs.registration import register

try:
    from bipedal_baseball.envs.directional_batting_env import DirectionalBattingEnv
    _entry = "bipedal_baseball.envs.directional_batting_env:DirectionalBattingEnv"
except ModuleNotFoundError:
    from envs.directional_batting_env import DirectionalBattingEnv
    _entry = "envs.directional_batting_env:DirectionalBattingEnv"

register(
    id="DirectionalBatting-v0",
    entry_point=_entry,
    max_episode_steps=40,
)

__all__ = ["DirectionalBattingEnv"]
