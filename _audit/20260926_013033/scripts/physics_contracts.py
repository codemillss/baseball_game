"""Synthetic/diagnostic contract checks; NOT policy ablation or success rates."""
from pathlib import Path
import json
import signal
import sys
from unittest.mock import patch
signal.alarm(120)
AUDIT=Path(__file__).resolve().parents[1]
REPO=AUDIT.parent.parent
sys.path.insert(0,str(REPO))
import numpy as np
import mujoco
from cognitive_ai.envs.fielder_env import FielderEnv
from cognitive_ai.envs.catcher_env import CatcherEnv
from cognitive_ai.envs.cognitive_baseball_env import CognitiveBaseballEnv

def emit(kind,**kw):
    print(json.dumps({"kind":kind,**kw},ensure_ascii=False,
                     default=lambda x:x.tolist() if isinstance(x,np.ndarray) else
                     x.item() if isinstance(x,np.generic) else str(x)),flush=True)

# Same state, no actions, one actual physics step. Only the already-present
# weld constraint is disabled in one disposable instance. This is a physics
# mechanism isolation test, never a fair trained-policy component ablation.
for active in [True,False]:
    e=FielderEnv(); obs,_=e.reset(seed=21)
    e.data.eq_active[:]=active
    b=mujoco.mj_name2id(e.model,mujoco.mjtObj.mjOBJ_BODY,"fielder_base")
    p=e.ball_qpos_adr; v=e.ball_qvel_adr
    start=e.data.qpos[p:p+3].copy(); vel=e.data.qvel[v:v+3].copy()
    initial_world=e.data.xpos[b].copy()
    base_qpos=obs[6:9].copy()
    initial_warnings=e.data.warning.number.copy()
    contacts_before=[{"geom1":mujoco.mj_id2name(e.model,mujoco.mjtObj.mjOBJ_GEOM,c.geom1),
                      "geom2":mujoco.mj_id2name(e.model,mujoco.mjtObj.mjOBJ_GEOM,c.geom2),
                      "distance":float(c.dist)} for c in e.data.contact]
    mujoco.mj_step(e.model,e.data)
    emit("one_substep_weld_isolation",eq_active=active,seed=21,dt=e.model.opt.timestep,
         initial_ball=start,initial_velocity=vel,initial_base_world=initial_world,
         reported_base=base_qpos,ball_after=e.data.qpos[p:p+3].copy(),
         initial_contacts=contacts_before,
         velocity_after=e.data.qvel[v:v+3].copy(),
         gravity_only_reference=start+vel*e.model.opt.timestep+
             np.array([0,0,-.5*9.81*e.model.opt.timestep**2]),
         warnings_before=initial_warnings,warnings_after=e.data.warning.number.copy(),
         note="Diagnostic disposable instance; no policy inference and no performance comparison.")
    e.close()

e=CatcherEnv()
outputs=[]
for mask in [False,True]:
    np.random.seed(19);e.reset(seed=19)
    action=np.zeros(12,np.float32)
    if mask:action[7:]=1.
    obs,r,t,tr,info=e.step(action)
    outputs.append((obs.copy(),e.data.qpos.copy(),e.data.ctrl.copy()))
emit("catcher_ignored_actions",varied_dimensions=list(range(7,12)),
     identical_obs=bool(np.array_equal(outputs[0][0],outputs[1][0])),
     identical_qpos=bool(np.array_equal(outputs[0][1],outputs[1][1])),
     identical_ctrl=bool(np.array_equal(outputs[0][2],outputs[1][2])))
e.close()

class SyntheticRenderer:
    def __init__(self,*args,**kwargs):pass
    def update_scene(self,*args,**kwargs):pass
    def render(self):return np.zeros((64,64,3),np.uint8)
    def close(self):pass

# Original image renderer failed CoreGraphics initialization. Stub only this
# external dependency to inspect name resolution/state write. Image output
# below is deliberately synthetic and cannot validate visual observations.
with patch("cognitive_ai.envs.cognitive_baseball_env.mujoco.Renderer",SyntheticRenderer):
    e=CognitiveBaseballEnv(xml_path=str(REPO/"shared_assets/h1_baseball.xml"))
    e.reset(seed=42)
    rootid=mujoco.mj_name2id(e.model,mujoco.mjtObj.mjOBJ_JOINT,"root_y")
    e.data.qpos[e.ball_qpos_adr]=.123
    e.data.qvel[e.ball_qvel_adr]=.456
    e._update_swing_kinematics(0.)
    emit("synthetic_cognitive_lookup",renderer_stubbed=True,root_y_id=rootid,
         mapped_address=int(e.qpos_adrs[0]),ball_address=int(e.ball_qpos_adr),
         requested_ball_values=[.123,.456],
         after_kinematics=[float(e.data.qpos[e.ball_qpos_adr]),float(e.data.qvel[e.ball_qvel_adr])])
    for i in range(3):
        o,r,t,tr,info=e.step(np.array([1.,0.,0.],np.float32))
        emit("synthetic_renderer_cognitive_step",step=i+1,image_is_synthetic=True,
             finite_state=bool(np.isfinite(e.data.qpos).all()),shape=o.shape,reward=r,
             terminated=t,truncated=tr)
        if t or tr:break
    e.close()
