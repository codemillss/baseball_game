from gymnasium.envs.registration import register

try:
    from bipedal_baseball.envs.directional_batting_env import DirectionalBattingEnv
    from bipedal_baseball.envs.bipedal_duel_env import BipedalDuelEnv
    _entry = "bipedal_baseball.envs.directional_batting_env:DirectionalBattingEnv"
    _duel_entry = "bipedal_baseball.envs.bipedal_duel_env:BipedalDuelEnv"
except ModuleNotFoundError:
    from envs.directional_batting_env import DirectionalBattingEnv
    from envs.bipedal_duel_env import BipedalDuelEnv
    _entry = "envs.directional_batting_env:DirectionalBattingEnv"
    _duel_entry = "envs.bipedal_duel_env:BipedalDuelEnv"

register(
    id="DirectionalBatting-v0",
    entry_point=_entry,
    max_episode_steps=40,
)

register(
    id="BipedalDuel-v0",
    entry_point=_duel_entry,
    max_episode_steps=55,
)

__all__ = ["DirectionalBattingEnv", "BipedalDuelEnv"]

