"""Repeat only the bounded pure-Python rule probes; never train or load a policy."""
from pathlib import Path
import ast
import hashlib
import json

OUT = Path(__file__).resolve().parent
BASEBALL = OUT.parent.parent.parent

def exact_class(path, name):
    source = path.read_text()
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(path), 'exec'), namespace)
    return namespace[name], hashlib.sha256(source.encode()).hexdigest()

def main():
    cls, game_hash = exact_class(BASEBALL / 'cognitive_ai/envs/baseball_game_state.py', 'BaseballGameState')
    cases = []
    for balls, strikes in [(1, 1), (3, 2), (0, 2)]:
        state = cls()
        state.balls, state.strikes = balls, strikes
        state.handle_hit('FOUL')
        expected = {'balls': balls, 'strikes': min(strikes + 1, 2)}
        actual = {'balls': state.balls, 'strikes': state.strikes}
        cases.append({'case': 'ordinary_foul', 'before': [balls, strikes], 'expected': expected, 'actual': actual, 'matches': expected == actual})
    state = cls()
    for _ in range(3):
        state.handle_pitch('STRIKE')
    cases.append({'case': 'three_strikes', 'outs': state.outs, 'strikes': state.strikes})
    state = cls()
    for _ in range(4):
        state.handle_pitch('BALL')
    cases.append({'case': 'four_balls', 'bases': state.bases, 'balls': state.balls})
    umpire_class, rule_hash = exact_class(BASEBALL / 'cognitive_ai/envs/baseball_rules.py', 'BaseballUmpire')
    umpire = umpire_class()
    endpoints = [[0, .3, .8], [0, -.3, .8]]
    midpoint = [0, 0, .8]
    # Neither of these methods uses numpy; the hit-outcome method is not called.
    crossing = {'endpoints': endpoints, 'midpoint': midpoint, 'midpoint_inside': umpire.is_in_strike_zone(midpoint), 'endpoints_result': umpire.check_pitch_outcome(endpoints), 'with_midpoint_result': umpire.check_pitch_outcome([endpoints[0], midpoint, endpoints[1]])}
    print(json.dumps({'scope': 'Pure GameState and synthetic pitch point contract only', 'game_source_sha256': game_hash, 'rule_source_sha256': rule_hash, 'game_cases': cases, 'crossing': crossing}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
