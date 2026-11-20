"""One checkpoint episode trace to expose warning/time reset behind catch flag."""
from physics_probe import emit, load_policy, REPO
import signal
signal.alarm(120)
import numpy as np
import mujoco
from cognitive_ai.envs.fielder_env import FielderEnv
env=FielderEnv()
model,norm=load_policy(env,"fielder")
obs,_=env.reset(seed=0)
emit("initial",seed=0,obs=obs,time=env.data.time,eq_active=env.data.eq_active.copy())
for i in range(12):
    action,_=model.predict(norm.normalize_obs(obs[None,:])[0],deterministic=True)
    before=env.data.time
    warnings_before=env.data.warning.number.copy()
    obs,r,t,tr,info=env.step(action)
    emit("step_trace",step=i+1,action=action,time_before=before,time_after=env.data.time,
         expected_elapsed=env.dt,actual_elapsed=env.data.time-before,
         warning_number_before=warnings_before,warning_number_after=env.data.warning.number.copy(),
         warning_lastinfo=env.data.warning.lastinfo.copy(),finite_qpos=bool(np.isfinite(env.data.qpos).all()),
         finite_qvel=bool(np.isfinite(env.data.qvel).all()),ball_site=env.data.site_xpos[env.ball_site_id].copy(),
         glove_site=env.data.site_xpos[env.glove_site_id].copy(),obs=obs,reward=r,terminated=t,truncated=tr,info=info)
    if t or tr:break
env.close()
