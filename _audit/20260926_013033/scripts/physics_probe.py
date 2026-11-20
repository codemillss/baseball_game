"""Bounded audit only; no training and no source/checkpoint writes.

Run from this audit directory with the repository .venv Python. All emitted
records are JSON lines. Synthetic判定 probes are labelled separately from
rollouts; they are never counted as policy successes.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import os
import signal
import sys
import time
from unittest.mock import patch

AUDIT = Path(__file__).resolve().parents[1]
REPO = AUDIT.parent.parent
sys.path.insert(0, str(REPO))
import numpy as np
import mujoco


def emit(kind, **data):
    print(json.dumps({"kind": kind, **data}, ensure_ascii=False,
                     default=lambda x: x.tolist() if isinstance(x, np.ndarray)
                     else x.item() if isinstance(x, np.generic) else str(x)), flush=True)


def jid(model, name):
    return mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)


def bid(model, name):
    return mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)


def metadata(env, name):
    m = env.model
    joints = [{"name": mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j),
               "qposadr": int(m.jnt_qposadr[j]), "dofadr": int(m.jnt_dofadr[j])}
              for j in range(m.njnt)]
    emit("model", env=name, nq=m.nq, nv=m.nv, nu=m.nu, dt=m.opt.timestep,
         joints=joints, eq_active=env.data.eq_active.copy(),
         obs_space=str(env.observation_space), action_space=str(env.action_space))


def load_policy(env, name):
    import torch
    torch.set_num_threads(1)
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    ckpt = REPO / ("checkpoints/teeball_final_model.zip" if name == "tee"
                   else f"checkpoints/{name}/best_model.zip")
    if not ckpt.is_file():
        emit("checkpoint_missing", env=name, path=str(ckpt))
        return None, None
    model = PPO.load(str(ckpt), device="cpu")
    norm = None
    if name != "tee":
        p = REPO / f"checkpoints/{name}/vec_normalize.pkl"
        norm = VecNormalize.load(str(p), DummyVecEnv([lambda: env]))
        norm.training = False
        norm.norm_reward = False
        emit("normalization", env=name, path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
             mean=norm.obs_rms.mean, count=float(norm.obs_rms.count), training=norm.training)
    emit("checkpoint", env=name, path=str(ckpt), sha256=hashlib.sha256(ckpt.read_bytes()).hexdigest(),
         obs_space=str(model.observation_space), action_space=str(model.action_space))
    return model, norm


def rollout(env, name, mode, seed, model=None, norm=None):
    # These legacy environments use np.random globals. Pair initial conditions
    # explicitly; this is separate from the reset(seed) contract probe below.
    np.random.seed(seed)
    obs, _ = env.reset(seed=seed)
    init = env.data.qpos.copy()
    rng = np.random.default_rng(seed + 1000)
    reward_sum = 0.
    obs_violations = 0
    action_extrema = [float("inf"), -float("inf")]
    terminated = truncated = False
    last_info = {}
    max_steps = {"tee": 45, "fielder": 205, "catcher": 155, "runner": 305}[name]
    for step in range(max_steps):
        if mode == "random":
            action = rng.uniform(-1, 1, env.action_space.shape).astype(np.float32)
        elif mode == "trained":
            inp = norm.normalize_obs(obs[None, :])[0] if norm is not None else obs
            action, _ = model.predict(inp, deterministic=True)
        elif mode == "height_rule":
            action = np.array([np.clip((obs[2] - 0.8) / 0.15, -1, 1)], np.float32)
        else:
            action = np.zeros(env.action_space.shape, np.float32)
        action_extrema = [min(action_extrema[0], float(np.min(action))),
                          max(action_extrema[1], float(np.max(action)))]
        obs, reward, terminated, truncated, last_info = env.step(action)
        obs_violations += int(not env.observation_space.contains(obs))
        reward_sum += float(reward)
        if not np.isfinite(obs).all() or not np.isfinite(reward):
            emit("nonfinite", env=name, mode=mode, seed=seed, step=step+1)
            break
        if terminated or truncated:
            break
    actual_xy = None
    if name == "runner":
        mujoco.mj_forward(env.model, env.data)
        actual_xy = env.data.xpos[bid(env.model, "runner_base"), :2].copy()
    if name == "tee":
        success = bool(env.has_contacted)
    elif name in {"fielder", "catcher"}:
        success = bool(last_info.get("catch", False))
    else:
        success = bool(terminated and last_info.get("dist", np.inf) < 1.0)
    emit("rollout", env=name, mode=mode, seed=seed, initial_qpos=init,
         steps=step+1, sim_time=float(env.data.time), reward=reward_sum,
         terminated=bool(terminated), truncated=bool(truncated),
         success_by_environment=success, last_info=last_info,
         finite=bool(np.isfinite(obs).all()), obs_violations=obs_violations,
         action_extrema=action_extrema, actual_runner_xy=actual_xy,
         actual_runner_distance=None if actual_xy is None else float(np.linalg.norm(actual_xy-env.target_pos)))


def task_probes(name):
    if name == "tee":
        from cognitive_ai.envs.teeball_env import TeeBallEnv
        env = TeeBallEnv(xml_path=str(REPO / "shared_assets/h1_baseball.xml"))
    elif name == "fielder":
        from cognitive_ai.envs.fielder_env import FielderEnv
        env = FielderEnv()
    elif name == "catcher":
        from cognitive_ai.envs.catcher_env import CatcherEnv
        env = CatcherEnv()
    elif name == "runner":
        from cognitive_ai.envs.runner_env import RunnerEnv
        env = RunnerEnv()
    metadata(env, name)
    np.random.seed(314)
    first, _ = env.reset(seed=42)
    second, _ = env.reset(seed=42)
    emit("reset_seed_contract", env=name, first=first, second=second,
         exact_equal=bool(np.array_equal(first, second)))

    if name == "runner":
        env.reset(seed=7)
        actual = env.data.xpos[bid(env.model, "runner_base")].copy()
        bj = jid(env.model, "ball_joint")
        emit("runner_index", reported_base=env._get_obs()[:3],
             actual_base_world=actual, ball_xyz=env.data.qpos[env.model.jnt_qposadr[bj]:][:3],
             actual_slide_qpos=[env.data.qpos[env.model.jnt_qposadr[jid(env.model, j)]]
                                for j in ["runner_x", "runner_y", "runner_yaw"]])
        # Synthetic unit test: freeze dynamics and put only BALL at target.
        env.data.qpos[:2] = env.target_pos
        with patch("cognitive_ai.envs.runner_env.mujoco.mj_step", lambda *_: None):
            _, reward, term, trunc, info = env.step(np.zeros(3, np.float32))
        emit("synthetic_runner_false_success", dynamics_frozen=True,
             actual_runner_world_before=actual, ball_at_target=True, reward=reward,
             terminated=term, truncated=trunc, info=info)

    if name == "catcher":
        env.reset(seed=7)
        ids = env.actuator_ids
        emit("catcher_ids", requested_glove="glove_box", requested_id=env.glove_geom_id,
             effective_negative_index_geom=mujoco.mj_id2name(env.model,mujoco.mjtObj.mjOBJ_GEOM, env.model.ngeom-1),
             actual_glove_id=mujoco.mj_name2id(env.model,mujoco.mjtObj.mjOBJ_GEOM,"glove_geom"),
             actuator_ids=ids, used_action_dimensions=[i for i,j in enumerate(ids[:10]) if j >= 0],
             reported_base=env._get_obs()[:3],
             actual_base_world=env.data.xpos[bid(env.model,"catcher_base")].copy())
        # Since no legitimate MuJoCo contact has geom id -1, catch predicate
        # cannot identify the glove. Record actual generated glove contacts.
        env.data.eq_active[:] = 0
        mujoco.mj_forward(env.model, env.data)
        gid=mujoco.mj_name2id(env.model,mujoco.mjtObj.mjOBJ_GEOM,"glove_geom")
        env.data.qpos[env.ball_qpos_adr:env.ball_qpos_adr+3] = env.data.geom_xpos[gid].copy()
        mujoco.mj_forward(env.model, env.data)
        contacts = [(int(c.geom1), int(c.geom2)) for c in env.data.contact]
        with patch("cognitive_ai.envs.catcher_env.mujoco.mj_step", lambda *_: None):
            _, r, term, trunc, info=env.step(np.zeros(12,np.float32))
        emit("synthetic_catcher_actual_contact", dynamics_frozen=True, weld_disabled=True,
             contacts=contacts, true_glove_id=gid, ball_geom=env.ball_geom_id,
             reward=r, terminated=term, info=info)

    if name in {"fielder", "catcher", "runner"}:
        np.random.seed(21)
        env.reset(seed=21)
        bj=jid(env.model,"ball_joint")
        bp=int(env.model.jnt_qposadr[bj]); bv=int(env.model.jnt_dofadr[bj])
        start=env.data.qpos[bp:bp+3].copy(); vel=env.data.qvel[bv:bv+3].copy()
        obs,r,t,tr,info=env.step(np.zeros(env.action_space.shape,np.float32))
        elapsed=float(env.data.time)
        expected=start+vel*elapsed+np.array([0,0,-0.5*9.81*elapsed**2])
        emit("weld_trajectory",env=name,eq_active=env.data.eq_active.copy(),initial_ball_xyz=start,
             initial_ball_velocity=vel,elapsed=elapsed,gravity_only_reference=expected,
             actual_ball_xyz=env.data.qpos[bp:bp+3].copy(),
             actual_ball_velocity=env.data.qvel[bv:bv+3].copy(),
             note="Diagnostic ballistic reference only; current XML also has contacts and an active weld.")

    try:
        model,norm=load_policy(env,name)
    except Exception as exc:
        emit("checkpoint_error",env=name,error=repr(exc))
        model=norm=None
    modes=["zero_action","random"]
    if name=="tee": modes.append("height_rule")
    if model is not None: modes.append("trained")
    for mode in modes:
        for seed in range(5):
            rollout(env,name,mode,seed,model,norm)
    env.close()


def cognitive_probe():
    from cognitive_ai.envs.cognitive_baseball_env import CognitiveBaseballEnv
    env=CognitiveBaseballEnv(xml_path=str(REPO/"shared_assets/h1_baseball.xml"),render_mode=None)
    metadata(env,"cognitive")
    obs,_=env.reset(seed=42)
    emit("cognitive_reset",shape=obs.shape,dtype=str(obs.dtype),space_contains=env.observation_space.contains(obs),
         root_y_id=jid(env.model,"root_y"),resolved_address=env.qpos_adrs[0],ball_address=env.ball_qpos_adr)
    env.data.qpos[env.ball_qpos_adr]=0.123
    env.data.qvel[env.ball_qvel_adr]=0.456
    env._update_swing_kinematics(0.)
    emit("synthetic_cognitive_ball_overwrite",ball_x_after=float(env.data.qpos[env.ball_qpos_adr]),
         ball_vx_after=float(env.data.qvel[env.ball_qvel_adr]),expected_if_not_robot_joint=[0.123,0.456])
    for i in range(3):
        obs,r,t,tr,info=env.step(np.array([1.,0.,0.],np.float32))
        emit("cognitive_step",step=i+1,shape=obs.shape,reward=r,terminated=t,truncated=tr,
             finite=bool(np.isfinite(obs).all()))
        if t or tr:
            env.reset(seed=43)
            break
    env.renderer.close()
    env.close()


if __name__=="__main__":
    signal.alarm(120)
    parser=argparse.ArgumentParser()
    parser.add_argument("--task",choices=["tee","fielder","catcher","runner","cognitive"],required=True)
    args=parser.parse_args()
    emit("execution",python=sys.version,cwd=str(Path.cwd()),task=args.task,
         versions={p:importlib.metadata.version(p) for p in ["mujoco","numpy","gymnasium","stable_baselines3","torch"]},
         command=sys.argv,classification="audit, bounded; no training")
    if args.task=="cognitive": cognitive_probe()
    else: task_probes(args.task)
