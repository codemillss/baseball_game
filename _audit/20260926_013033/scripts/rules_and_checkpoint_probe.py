"""Bounded audit: pure rule functions and ZIP/JSON metadata only; no training/rendering.

Does not deserialize pickle/cloudpickle, mutate the repository's source, or load policy
weights. The synthetic rule cases are NOT policy successes or baseball performance.
"""
import hashlib
import json
import platform
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from cognitive_ai.envs.baseball_game_state import BaseballGameState
from cognitive_ai.envs.baseball_rules import BaseballUmpire


def main():
    rule_cases = []
    for strikes, balls in [(0, 0), (1, 2), (2, 3)]:
        game = BaseballGameState()
        game.strikes, game.balls = strikes, balls
        game.handle_hit("FOUL")
        expected = [min(strikes + 1, 2), balls]
        actual = [game.strikes, game.balls]
        rule_cases.append({"case": "ordinary_foul", "before_strikes_balls": [strikes, balls],
                           "expected": expected, "actual": actual, "passed": expected == actual})
    game = BaseballGameState()
    for _ in range(54 * 3):
        game.handle_pitch("STRIKE")
    rule_cases.append({"case": "54_outs_by_strikeouts", "expected_inning": 10,
                       "actual_inning": game.inning, "actual_is_top": game.is_top,
                       "passed": game.inning == 10 and game.is_top})
    umpire = BaseballUmpire()
    # Segment crosses the volume; neither sampled endpoint lies inside it.
    trajectory = [[0.0, 0.30, 0.8], [0.0, -0.30, 0.8]]
    rule_cases.append({"case": "sampled_segment_crosses_zone", "samples": trajectory,
                       "expected_if_continuous_segment_used": "STRIKE",
                       "actual": umpire.check_pitch_outcome(trajectory),
                       "note": "Synthetic 0.6 m gap, not a claim that a measured project pitch followed it."})
    checkpoints = []
    for path in sorted((ROOT / "checkpoints").rglob("*.zip")):
        with zipfile.ZipFile(path) as z:
            meta = json.loads(z.read("data"))
            # Serialized fields remain strings/dicts; never deserialize them.
            spaces = {}
            for key in ("observation_space", "action_space", "policy_class"):
                item = meta.get(key)
                if isinstance(item, dict):
                    spaces[key] = {k: v for k, v in item.items() if k != ":serialized:" and
                                   k in (":type:", "_shape", "low", "high", "__module__", "__name__")}
                else:
                    spaces[key] = str(item)
            checkpoints.append({"path": str(path.relative_to(ROOT)),
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                "num_timesteps": meta.get("num_timesteps"),
                                "total_timesteps": meta.get("_total_timesteps"),
                                "n_envs": meta.get("n_envs"), "seed": meta.get("seed"),
                                "n_steps": meta.get("n_steps"), "policy_kwargs": meta.get("policy_kwargs"),
                                "spaces": spaces,
                                "sb3_version": z.read("_stable_baselines3_version").decode().strip()})
    print(json.dumps({"python": sys.version, "platform": platform.platform(),
                      "execution_bound": "4 game-state cases, 1 umpire case, finite local checkpoint ZIP inventory",
                      "rule_cases": rule_cases, "checkpoints": checkpoints}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
