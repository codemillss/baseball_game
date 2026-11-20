"""Bounded read-only-source audit. All output stays beside this script.
Existing checkpoints are local project files explicitly in audit scope.
No training, rendering, network access, or original-file writes.
"""
from pathlib import Path
import os, sys, json, platform, traceback, zipfile, hashlib, pickle
AUDIT = Path(__file__).resolve().parents[1]
ROOT = AUDIT.parents[1]
os.chdir(AUDIT)
sys.path.insert(0, str(ROOT))
os.environ['MPLCONFIGDIR'] = str(AUDIT/'logs/mpl')
import numpy as np
import mujoco, gymnasium, torch, stable_baselines3
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from cognitive_ai.envs.pitcher_env import PitcherEnv
from cognitive_ai.envs.baseball_match_env import BaseballMatchEnv
from cognitive_ai.envs.soft_toss_env import SoftTossEnv
from cognitive_ai.envs.pitching_machine_env import PitchingMachineEnv
from cognitive_ai.envs.breaking_ball_env import BreakingBallEnv
from cognitive_ai.training.train_mlb_batter import BatterMatchTrainingEnv
torch.set_num_threads(1)
def clean(x):
    if isinstance(x, np.ndarray): return x.tolist()
    if isinstance(x, np.generic): return x.item()
    if isinstance(x, Path): return str(x)
    raise TypeError(type(x).__name__)
def emit(kind, **kw):
    row=dict(kind=kind, **kw)
    s=json.dumps(row,ensure_ascii=False,default=clean,allow_nan=False)
    print(s,flush=True)
    with (AUDIT/'logs/runtime_results.jsonl').open('a') as f: f.write(s+'\n')
def case(name, f):
    try: f()
    except Exception as e: emit('error',case=name,type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
def metadata():
    emit('runtime',python=sys.version,platform=platform.platform(),versions={m.__name__:m.__version__ for m in [np,mujoco,gymnasium,torch,stable_baselines3]},device='cpu',command=sys.argv)
    for p in sorted((ROOT/'checkpoints').rglob('*.zip')):
        with zipfile.ZipFile(p) as z:
            d=json.loads(z.read('data'))
            emit('checkpoint',path=p.relative_to(ROOT),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),timesteps=d.get('num_timesteps'),n_steps=d.get('n_steps'),n_envs=d.get('n_envs'),policy=str(d.get('policy_class',{}).get(':type:', '')),obs=str(d.get('observation_space')),action=str(d.get('action_space')),saved_system=z.read('system_info.txt').decode() if 'system_info.txt' in z.namelist() else None)
    for p in sorted((ROOT/'checkpoints').rglob('*.pkl')):
        with p.open('rb') as f: norm=pickle.load(f)
        emit('normalizer',path=p.relative_to(ROOT),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),obs_shape=list(norm.obs_rms.mean.shape),count=norm.obs_rms.count,training=norm.training,norm_reward=norm.norm_reward,mean=norm.obs_rms.mean,var=norm.obs_rms.var)
def smoke():
    for cls in [PitcherEnv,SoftTossEnv,PitchingMachineEnv,BreakingBallEnv]:
        e=cls(); np.random.seed(120); o,_=e.reset(seed=120)
        observations=[o.copy()]; rewards=[]
        action=np.zeros(e.action_space.shape,dtype=np.float32)
        for i in range(100):
            o,r,t,tr,info=e.step(action); observations.append(o.copy()); rewards.append(r)
            if t or tr: break
        reset_obs,_=e.reset(seed=120)
        emit('smoke',env=cls.__name__,obs_shape=e.observation_space.shape,action_shape=e.action_space.shape,finite=bool(np.isfinite(observations).all()),within_space=bool(all(e.observation_space.contains(v) for v in observations)),steps=i+1,terminated=t,truncated=tr,info=info,reward=sum(rewards),dt=e.model.opt.timestep,frame_skip=e.frame_skip,nq=e.model.nq,nv=e.model.nv,nu=e.model.nu,reset_finite=bool(np.isfinite(reset_obs).all()))
        a,_=e.reset(seed=777); b,_=e.reset(seed=777)
        emit('reset_seed',env=cls.__name__,same_seed_equal=bool(np.array_equal(a,b)),max_abs_diff=float(np.max(abs(a-b))))
        e.close()
    e=BaseballMatchEnv(); o=e.reset(seed=5)
    emit('match_observation',shapes={k:v.shape for k,v in o.items()},batter_min=float(o['batter'].min()),batter_max=float(o['batter'].max()),nu=e.model.nu,free_joints=[mujoco.mj_id2name(e.model,mujoco.mjtObj.mjOBJ_JOINT,i) for i in range(e.model.njnt) if e.model.jnt_type[i]==0])
def load_policy(path,norm_path,env):
    vec=DummyVecEnv([lambda:env]); norm=VecNormalize.load(str(ROOT/norm_path),vec); norm.training=False; norm.norm_reward=False
    model=PPO.load(str(ROOT/path),env=norm,device='cpu')
    return model,norm
def baseline(label, factory, checkpoint, norm_path, n=10):
    e=factory(); model=norm=None
    try: model,norm=load_policy(checkpoint,norm_path,e)
    except Exception as ex: emit('policy_load_error',task=label,checkpoint=checkpoint,message=str(ex))
    for mode in ['no_trigger' if label!='pitcher' else 'fixed_midpoint','random','rule' if label!='pitcher' else 'fixed_fast',*(['ppo'] if model else [])]:
        for seed in range(100,100+n):
            np.random.seed(seed); torch.manual_seed(seed); rng=np.random.default_rng(seed+9000)
            o,_=e.reset(seed=seed); initial=o.copy(); total=0.; finite=True; contains=True; contacted=False
            for step in range(100):
                if mode=='ppo': act,_=model.predict(norm.normalize_obs(o),deterministic=True)
                elif mode=='random': act=rng.uniform(-1,1,e.action_space.shape).astype(np.float32)
                else:
                    act=np.zeros(e.action_space.shape,dtype=np.float32)
                    if mode=='fixed_fast': act[3]=1
                    elif mode=='no_trigger': act[0]=-1
                    elif mode=='rule':
                        # Explicit unoptimized heuristic derived from documented timing guidance.
                        trigger_t=.12 if label.startswith('machine') else (.10 if label=='breaking' else .125)
                        act[0]=1 if o[6]<=trigger_t else -1
                        act[1]=np.clip((o[7]-.815)/.135 if label=='soft' else o[7],-1,1)
                        if len(act)>2: act[2]=np.clip(o[8],-1,1)
                o,r,t,tr,info=e.step(act);total+=r;finite &= bool(np.isfinite(o).all());contains &= e.observation_space.contains(o);contacted |= bool(getattr(e,'has_contacted',False))
                if t or tr: break
            emit('baseline_episode',task=label,mode=mode,seed=seed,initial=initial,steps=step+1,terminated=t,truncated=tr,reward=float(total),contact=contacted,success=bool(info.get('is_success',contacted)),info=info,finite=finite,within_space=bool(contains),final_ball=e.data.qpos[e.ball_qpos_adr:e.ball_qpos_adr+3].copy(),ctrl_max=float(np.max(np.abs(e.data.ctrl))) if e.model.nu else 0.)
        if norm: emit('frozen_norm',task=label,mode=mode,training=norm.training,count=norm.obs_rms.count)
    e.close()
def match_policy():
    e=BatterMatchTrainingEnv(pitcher_model_path=str(ROOT/'checkpoints/mocap_pitcher_best/best_model'),pitcher_norm_path=str(ROOT/'checkpoints/mocap_pitcher_vec_normalize.pkl'),is_eval_mode=True)
    model,norm=load_policy('checkpoints/mocap_batter_best/best_model.zip','checkpoints/mocap_batter_vec_normalize.pkl',e)
    for mode in ['no_trigger','random','ppo']:
        for seed in range(100,110):
            np.random.seed(seed);torch.manual_seed(seed);rng=np.random.default_rng(seed+9000);o,_=e.reset(seed=seed); initial=o.copy(); total=0; count=0; finite=True; maxabs=float(abs(o).max()); env=e.match_env
            for step in range(460):
                act=model.predict(norm.normalize_obs(o),deterministic=True)[0] if mode=='ppo' else (rng.uniform(-1,1,3).astype(np.float32) if mode=='random' else np.array([-1,0,0],dtype=np.float32))
                o,r,t,tr,info=e.step(act);total+=r;count+=int(info['has_contacted']); finite &= bool(np.isfinite(o).all());maxabs=max(maxabs,float(abs(o).max()))
                if t or tr: break
            emit('match_episode',mode=mode,seed=seed,initial=initial,steps=step+1,reward=total,info=info,contact_reward_steps=count,finite=finite,max_abs_obs=maxabs,final_ball=env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3].copy(),wind=env.wind_vector)
def synthetic():
    # These are branch tests, NOT successful policy episodes.
    for label,pos in [('strike',[0,.19,.815]),('ball',[.8,.19,.815]),('ground',[0,3,.02]),('timeout',[0,3,1])]:
        e=PitcherEnv();e.reset(seed=1);e.target_x=0;e.target_z=.815;e.is_released=True;e.throw_progress=1;e.data.eq_active[0]=False;e.data.qpos[e.ball_qpos_adr:e.ball_qpos_adr+3]=pos;e.data.qvel[:]=0
        if label=='timeout':e.current_step=e.max_steps-1
        mujoco.mj_forward(e.model,e.data);o,r,t,tr,info=e.step(np.zeros(4));emit('synthetic_branch',label=label,reward=r,terminated=t,truncated=tr,info=info)
    p=PitcherEnv();p.reset();m=BaseballMatchEnv();m.reset()
    for e in [p,m]:
        e.target_x=.11;e.target_z=.88;e.is_released=True;e.data.qpos[e.ball_qpos_adr:e.ball_qpos_adr+3]=[.12,3.4,.56];e.data.qvel[e.ball_qvel_adr:e.ball_qvel_adr+3]=[1,2,3]
        if isinstance(e,PitcherEnv):e.throw_progress=.42
        else:e.p_throw_progress=.42
        mujoco.mj_forward(e.model,e.data)
    emit('synthetic_observation_contract',pitcher=p._get_obs(),match=m.get_observations()['pitcher'],note='Semantically identical ball/progress state; hand positions differ with XML. Indices 3..12 permuted.')
    m=BaseballMatchEnv();m.reset();m.is_in_strike_zone=False;m.reset();emit('synthetic_reset_stale',field='is_in_strike_zone',value=m.is_in_strike_zone)
    # Contact predicate is MuJoCo contact based, not a distance threshold.
    m=BaseballMatchEnv();m.reset(); m.data.eq_active[0]=False;m.data.qpos[m.ball_qpos_adr:m.ball_qpos_adr+3]=m.data.geom_xpos[m.bat_geom_id];mujoco.mj_forward(m.model,m.data)
    emit('synthetic_contact',ncon=m.data.ncon,detected=m._check_contact())
    # Measure combined aerodynamics separately, without changing actual source.
    m=BaseballMatchEnv();m.reset();m.is_released=True;m.target_pitch_type=0;m.extra_acc=np.array([0,0,3.]);m.wind_vector[:]=0;m.data.qvel[m.ball_qvel_adr:m.ball_qvel_adr+3]=[0,-30,0];m._apply_aerodynamics()
    mass=m.model.body_mass[m.ball_body_id];force=m.data.xfrc_applied[m.ball_body_id,:3].copy()
    emit('synthetic_aerodynamics',mass=mass,xfrc_force=force,xfrc_acceleration=force/mass,additional_direct_acceleration=m.extra_acc-.0054*30*np.array([0,-30,0]))
def followup():
    baseline('machine80_correct_norm',lambda:PitchingMachineEnv(target_speed_kmh=80),'checkpoints/pitching_80kmh_deep_best/best_model.zip','checkpoints/pitching_80kmh_deep_norm.pkl')
    # Original evaluation entrypoint's old pitcher checkpoint pairing.
    def old_pitcher():
        e=PitcherEnv();model,norm=load_policy('checkpoints/pitcher_best/best_model.zip','checkpoints/pitcher_vec_normalize.pkl',e)
        o,_=e.reset();emit('old_pitcher_load',action=model.predict(norm.normalize_obs(o),deterministic=True)[0])
    case('original_eval_pitcher_pair',old_pitcher)
    from cognitive_ai.envs.adversarial_match_env import AdversarialPitcherEnv
    case('adversarial_reset',lambda:AdversarialPitcherEnv().reset(seed=1))
    # After-trigger action has no physical effect, yet changes miss reward.
    for cls in [PitchingMachineEnv,BreakingBallEnv]:
        rows=[]
        for tail in [-1,1]:
            e=cls();np.random.seed(120);o,_=e.reset(seed=120);acts=[];total=0
            for step in range(100):
                a=np.zeros(e.action_space.shape,dtype=np.float32)
                if e.swing_active:a[1:]=tail
                else:a[0]=1
                o,r,t,tr,info=e.step(a);total+=r;acts.append(a.copy())
                if t or tr:break
            rows.append(dict(tail=tail,steps=step+1,total=float(total),qpos=e.data.qpos.copy(),contact=e.has_contacted,trigger=getattr(e,'trigger_t_remain',None)))
        emit('synthetic_post_trigger_reward',env=cls.__name__,same_final_qpos=bool(np.array_equal(rows[0]['qpos'],rows[1]['qpos'])),rewards=[r['total'] for r in rows],contact=[r['contact'] for r in rows],steps=[r['steps'] for r in rows])
    # Evaluate actual VecEnv autoreset handling on a forced near-terminal instance.
    e=BatterMatchTrainingEnv(pitcher_model_path=str(ROOT/'checkpoints/mocap_pitcher_best/best_model'),pitcher_norm_path=str(ROOT/'checkpoints/mocap_pitcher_vec_normalize.pkl'),is_eval_mode=True)
    v=DummyVecEnv([lambda:e]);v.reset();m=e.match_env
    m.is_released=True;m.p_throw_progress=1;m.has_contacted=True;m.contact_step=0;m.current_step=449;m.data.eq_active[0]=False;m.data.qpos[m.ball_qpos_adr:m.ball_qpos_adr+3]=[0,20,3];m.data.qvel[:]=0;mujoco.mj_forward(m.model,m.data)
    o,r,d,infos=v.step(np.array([[-1,0,0]],dtype=np.float32))
    emit('synthetic_demo_autoreset',done=d,info=infos[0],raw_ball=m.data.qpos[m.ball_qpos_adr:m.ball_qpos_adr+3].copy(),demo_hit_detected=bool(getattr(m,'has_hit',False) or m.batted_distance>0),raw_has_contacted=m.has_contacted,note='Forced contact flag tests reporting only, not physical success')
    # Load mega frame-stacked batter with the architecture actually used for training.
    from stable_baselines3.common.vec_env import VecFrameStack
    e=BatterMatchTrainingEnv();v=DummyVecEnv([lambda:e]);n=VecNormalize.load(str(ROOT/'checkpoints/mega_batter/vec_normalize.pkl'),v);n.training=False;n.norm_reward=False;s=VecFrameStack(n,n_stack=4);b=PPO.load(str(ROOT/'checkpoints/mega_batter/best_model'),env=s,device='cpu')
    np.random.seed(100);torch.manual_seed(100);o=s.reset();a,_=b.predict(o,deterministic=True);o,r,d,info=s.step(a)
    emit('mega_batter_inference',obs_shape=o.shape,action=a,finite=bool(np.isfinite(o).all()),normalizer_count=n.obs_rms.count,done=d)
if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'all'
    if mode in ['metadata','all']:case('metadata',metadata)
    if mode in ['smoke','all']:case('smoke',smoke);case('synthetic',synthetic)
    if mode in ['baseline','all']:
        for args in [('soft',SoftTossEnv,'checkpoints/soft_toss_best_model/best_model.zip','checkpoints/soft_toss_vec_normalize.pkl'),('machine50',lambda:PitchingMachineEnv(target_speed_kmh=50),'checkpoints/pitching_50kmh_best/best_model.zip','checkpoints/pitching_50kmh_vec_normalize.pkl'),('machine80',lambda:PitchingMachineEnv(target_speed_kmh=80),'checkpoints/pitching_80kmh_deep_best/best_model.zip','checkpoints/pitching_80kmh_vec_normalize.pkl'),('breaking',BreakingBallEnv,'checkpoints/breaking_ball_best/best_model.zip','checkpoints/breaking_ball_vec_normalize.pkl'),('pitcher',PitcherEnv,'checkpoints/mega_pitcher/best_model.zip','checkpoints/mega_pitcher/vec_normalize.pkl')]:case(args[0],lambda args=args:baseline(*args))
    if mode in ['match','all']:case('match',match_policy)
    if mode=='followup':case('followup',followup)
