"""Two bounded one-step synthetic environments. No project policy performance claim."""
import json
import platform
import sys

import gymnasium as gym
import numpy as np
import stable_baselines3
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize


class OneStepEnv(gym.Env):
    def __init__(self):
        self.observation_space = gym.spaces.Box(-100, 100, (1,), dtype=np.float32)
        self.action_space = gym.spaces.Box(-1, 1, (1,), dtype=np.float32)
        self.position = -10.0

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.position = -10.0
        return np.array([self.position], dtype=np.float32), {}

    def step(self, action):
        self.position = 99.0
        return np.array([self.position], dtype=np.float32), 5.0, True, False, {"final_position": 99.0}


def main():
    raw = DummyVecEnv([OneStepEnv])
    raw.reset()
    obs, reward, done, info = raw.step(np.array([[0.0]], dtype=np.float32))
    result = {"python": sys.version, "platform": platform.platform(),
              "stable_baselines3": stable_baselines3.__version__,
              "boundary": "2 synthetic one-step episodes, no renderer, no model, no training",
              "autoreset": {"done": bool(done[0]), "returned_obs": obs.tolist(),
                            "terminal_observation": info[0]["terminal_observation"].tolist(),
                            "raw_state_after_step": raw.envs[0].position,
                            "terminal_info_position": info[0]["final_position"]}}
    raw.close()
    # Same defaults as train_mega_architecture.py eval_env configuration.
    normalized = VecNormalize(DummyVecEnv([OneStepEnv]), norm_obs=True, norm_reward=True, clip_obs=10.0)
    before = [float(normalized.obs_rms.count), float(normalized.ret_rms.count)]
    normalized.reset()
    _, rewards, _, _ = normalized.step(np.array([[0.0]], dtype=np.float32))
    after = [float(normalized.obs_rms.count), float(normalized.ret_rms.count)]
    result["mega_eval_defaults"] = {"training": normalized.training,
                                    "norm_reward": normalized.norm_reward,
                                    "obs_and_return_count_before": before,
                                    "obs_and_return_count_after": after,
                                    "raw_reward": 5.0, "returned_reward": float(rewards[0])}
    normalized.close()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
