"""Recompute summary and verify initial-case pairing from saved audit results only."""
from pathlib import Path
import json,collections
A=Path(__file__).resolve().parents[1]
rows=[json.loads(s) for s in (A/'logs/runtime_results.jsonl').read_text().splitlines()]
groups=collections.defaultdict(list);pairs=collections.defaultdict(list)
for r in rows:
    if r['kind']=='baseline_episode':
        groups[(r['task'],r['mode'])].append(r)
        pairs[(r['task'],r['seed'])].append(r['initial'])
    elif r['kind']=='match_episode':pairs[('match',r['seed'])].append(r['initial'])
summary={'baseline':[], 'initial_case_pairing':[], 'notes':['machine80 first pass paired deep checkpoint with regular norm by audit error; excluded from final comparison. Use machine80_correct_norm.','Counts describe small diagnostic cases, not population success estimates.']}
for (task,mode),v in groups.items():
    summary['baseline'].append({'task':task,'mode':mode,'n':len(v),'success':sum(x['success'] for x in v),'mean_reward':sum(x['reward'] for x in v)/len(v),'all_finite':all(x['finite'] for x in v),'terminated':sum(x['terminated'] for x in v),'truncated':sum(x['truncated'] for x in v)})
for (task,seed),obs in pairs.items():summary['initial_case_pairing'].append({'task':task,'seed':seed,'n_modes':len(obs),'identical':all(x==obs[0] for x in obs)})
out=A/'logs/analysis_summary.json'
with out.open('x') as f:json.dump(summary,f,ensure_ascii=False,indent=2)
print(json.dumps({'summary':str(out),'all_initial_pairs_identical':all(x['identical'] for x in summary['initial_case_pairing']),'group_count':len(groups)},ensure_ascii=False))
