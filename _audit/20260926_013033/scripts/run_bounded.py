"""Run audit subprocesses with timeout and save exact command/output metadata."""
from pathlib import Path
import sys,os,subprocess,json,time
A=Path(__file__).resolve().parents[1];R=A.parents[1]
for name in ['shared_assets','checkpoints']:
    p=A/name
    if not p.exists(): p.symlink_to(R/name,target_is_directory=True)
mode=sys.argv[1]
suffix=sys.argv[2] if len(sys.argv)>2 else ''
cmd=[str(R/'.venv/bin/python'),'-B',str(A/'scripts/runtime_audit.py'),mode]
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','MPLCONFIGDIR':str(A/'logs/mpl'),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
t=time.time();output=A/'logs'/f'{mode}{suffix}_stdout.txt'
if output.exists():raise FileExistsError(output)
with output.open('w') as f:
    try:
        p=subprocess.run(cmd,cwd=A,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180)
        status=p.returncode
    except subprocess.TimeoutExpired:status='timeout180s'
record={'command':cmd,'cwd':str(A),'env_overrides':{k:env[k] for k in ['PYTHONDONTWRITEBYTECODE','MPLCONFIGDIR','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS']},'elapsed_seconds':time.time()-t,'returncode':status,'stdout':str(output),'expectation':{'metadata':'record existing checkpoint identity and runtime versions','smoke':'imports/reset/steps/reset, finite obs, termination branches','baseline':'paired 10-case small baseline; not population performance estimate','match':'demo checkpoint loading and 30 bounded paired episodes','followup':'targeted controlled checks and correctly paired 80kmh normalizer'}[mode]}
with (A/'logs/commands.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
print(json.dumps(record,ensure_ascii=False))
