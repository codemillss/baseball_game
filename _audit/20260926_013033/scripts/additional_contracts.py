"""Small bounded cases omitted from the first runtime pass; no source changes."""
from runtime_audit import *
from cognitive_ai.envs.adversarial_match_env import AdversarialPitcherEnv
from cognitive_ai.envs.baseball_rules import BaseballUmpire
o,info=AdversarialPitcherEnv().reset(seed=1)
emit('adversarial_reset_return',type=type(o).__name__,value=o,expected_shape=[26])
u=BaseballUmpire()
trajectory=[np.array([0,.3,.8]),np.array([0,-.3,.8])]
emit('synthetic_umpire_segment',trajectory=trajectory,result=u.check_pitch_outcome(trajectory),segment_crosses_box=True)
e=BaseballMatchEnv();e.reset();e.has_contacted=False;e.b_swing_active=False;e.target_x=0;e.target_z=.815
e._evaluate_outcome(np.array([0,-.51,.815]),np.array([0,-30,0]))
emit('synthetic_strike_semantics',match=e.outcome,point_y=-.51,umpire=u.check_pitch_outcome([np.array([0,-.51,.815])]),note='Match ignores plate-crossing history; synthetic boundary comparison')
# Confirm claim drift in the original state, then inspect the normalization saturation.
e=BatterMatchTrainingEnv(pitcher_model_path=str(ROOT/'checkpoints/mocap_pitcher_best/best_model'),pitcher_norm_path=str(ROOT/'checkpoints/mocap_pitcher_vec_normalize.pkl'))
np.random.seed(100);o,_=e.reset(seed=100)
b,n=load_policy('checkpoints/mocap_batter_best/best_model.zip','checkpoints/mocap_batter_vec_normalize.pkl',e)
emit('match_reset_bounds',raw=o,within_space=e.observation_space.contains(o),normalized=n.normalize_obs(o),normalizer_mean=n.obs_rms.mean)
