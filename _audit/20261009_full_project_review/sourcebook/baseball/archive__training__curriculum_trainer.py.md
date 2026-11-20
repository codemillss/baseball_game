# baseball/archive/training/curriculum_trainer.py

원본: [archive/training/curriculum_trainer.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/curriculum_trainer.py)

SHA256: `7a0234d78d45e3a73b016d7890c9ceab6f354ee61efc8d252efed2ccfdac24e4`

전체 277행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `obs_to_tensor` | FunctionDef | 31 | 39 |
| `run_curriculum_training` | FunctionDef | 42 | 273 |

## 전체 원문

````text
    1 | """
    2 | curriculum_trainer.py — 커리큘럼 기반 통합 PPO 학습 파이프라인 (Phase 2)
    3 | 
    4 | UnifiedBaseballEnv + CurriculumManager + HealthMonitor + RewardAuditSystem 
    5 | + EpisodeRecorder 를 연결하여 학습 파이프라인을 구축합니다.
    6 | """
    7 | 
    8 | import os
    9 | import sys
   10 | import time
   11 | import numpy as np
   12 | from pathlib import Path
   13 | from collections import deque
   14 | 
   15 | import torch
   16 | import torch.nn.functional as F
   17 | import torch.optim as optim
   18 | 
   19 | sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
   20 | 
   21 | from envs.unified_baseball_env import UnifiedBaseballEnv
   22 | from training.multimodal_networks import MultimodalBatterPolicy, MultimodalValueNetwork, get_device
   23 | from training.curriculum_manager import CurriculumManager
   24 | from training.health_monitor import TrainingHealthMonitor
   25 | from training.episode_recorder import EpisodeRecorder
   26 | from training.reward_audit import RewardAuditSystem
   27 | from training.logger import DashboardLogger
   28 | from training.trainer import TrainingConfig, PPOUpdater  # GAE 계산에 재사용
   29 | 
   30 | 
   31 | def obs_to_tensor(obs_dict: dict, device: torch.device, unsqueeze: bool = True) -> dict:
   32 |     """Dict 형태의 관찰값을 PyTorch 텐서로 변환합니다."""
   33 |     tensors = {}
   34 |     for k, v in obs_dict.items():
   35 |         t = torch.tensor(v, dtype=torch.float32, device=device)
   36 |         if unsqueeze:
   37 |             t = t.unsqueeze(0)
   38 |         tensors[k] = t
   39 |     return tensors
   40 | 
   41 | 
   42 | def run_curriculum_training(
   43 |     total_episodes: int = 300,
   44 |     initial_stage: int = 1,
   45 |     lr: float = 1e-4,
   46 |     record_interval: int = 100,
   47 | ):
   48 |     device = get_device()
   49 |     print("=" * 70)
   50 |     print(" ⚾ 커리큘럼 기반 Phase 2 멀티모달 PPO 학습 시작")
   51 |     print(f"   Device: {device} | Episodes: {total_episodes}")
   52 |     print(f"   Initial Stage: {initial_stage} | Learning Rate: {lr}")
   53 |     print("=" * 70)
   54 | 
   55 |     # ── 환경 (녹화를 위해 rgb_array로 생성) ──
   56 |     env = UnifiedBaseballEnv(curriculum_stage=initial_stage, render_mode="rgb_array")
   57 | 
   58 |     # ── 에이전트 ──
   59 |     act_dim = env.action_space.shape[0]  # 7
   60 | 
   61 |     policy = MultimodalBatterPolicy(action_dim=act_dim, hidden_dim=256, num_layers=2).to(device)
   62 |     value_net = MultimodalValueNetwork(hidden_dim=256).to(device)
   63 |     optimizer = optim.Adam(list(policy.parameters()) + list(value_net.parameters()), lr=lr)
   64 | 
   65 |     # ── 매니저 & 모니터 & 렌더/감사 & 대시보드 로거 ──
   66 |     curriculum = CurriculumManager(initial_stage=initial_stage)
   67 |     monitor = TrainingHealthMonitor()
   68 |     recorder = EpisodeRecorder()
   69 |     auditor = RewardAuditSystem()
   70 |     dashboard_logger = DashboardLogger()
   71 | 
   72 |     # GAE 계산기 초기화 (trainer.py의 PPOUpdater 재사용)
   73 |     ppo_config = TrainingConfig()
   74 |     ppo_config.gamma = 0.99
   75 |     ppo_config.gae_lambda = 0.95
   76 |     ppo_config.n_epochs = 4          # 하드코딩된 3 대신 config에서 관리
   77 |     ppo_config.batch_size = 64
   78 |     ppo_config.clip_eps = 0.2
   79 |     ppo_config.entropy_coef = 0.02
   80 |     ppo_config.value_coef = 0.5
   81 |     ppo_config.max_grad_norm = 0.5
   82 |     updater = PPOUpdater(ppo_config, device)
   83 | 
   84 |     reward_window = deque(maxlen=50)
   85 |     best_contact_rate = 0.0
   86 |     start_time = time.time()
   87 | 
   88 |     for ep in range(1, total_episodes + 1):
   89 |         obs, info = env.reset()
   90 |         done = False
   91 |         hidden = None
   92 | 
   93 |         obs_list, act_list, rew_list, log_prob_list, val_list, next_vision_list = [], [], [], [], [], []
   94 | 
   95 |         while not done:
   96 |             obs_t = obs_to_tensor(obs, device)
   97 | 
   98 |             with torch.no_grad():
   99 |                 action_t, log_prob_t, _, hidden = policy.get_action(obs_t, hidden)
  100 |                 val_t = value_net(obs_t)
  101 | 
  102 |             action = action_t.squeeze(0).cpu().numpy()
  103 |             log_prob = log_prob_t.squeeze(0).cpu().item()
  104 |             value = val_t.squeeze().cpu().item()
  105 | 
  106 |             next_obs, reward, terminated, truncated, step_info = env.step(action)
  107 |             done = terminated or truncated
  108 | 
  109 |             obs_list.append(obs)
  110 |             act_list.append(action)
  111 |             rew_list.append(reward)
  112 |             log_prob_list.append(log_prob)
  113 |             val_list.append(value)
  114 |             next_vision_list.append(next_obs["vision"])
  115 | 
  116 |             obs = next_obs
  117 | 
  118 |         ep_reward = sum(rew_list)
  119 |         reward_window.append(ep_reward)
  120 |         contacted = step_info.get("has_contacted", False)
  121 | 
  122 |         curriculum.record_episode(contacted, step_info)
  123 |         if contacted:
  124 |             auditor.record_hit(step_info, ep_reward)
  125 | 
  126 |         # ── PPO Gradient Update ──
  127 |         if len(obs_list) > 1:
  128 |             # 리스트 딕셔너리 -> 딕셔너리 텐서
  129 |             batch_obs = {
  130 |                 k: torch.tensor(np.array([o[k] for o in obs_list]), dtype=torch.float32, device=device)
  131 |                 for k in obs_list[0].keys()
  132 |             }
  133 |             
  134 |             act_tensor = torch.tensor(np.array(act_list), dtype=torch.float32, device=device)
  135 |             old_log_probs = torch.tensor(np.array(log_prob_list), dtype=torch.float32, device=device)
  136 |             next_vision_tensor = torch.tensor(np.array(next_vision_list), dtype=torch.float32, device=device)
  137 | 
  138 |             # ── GAE 계산 (이전 MC Returns 대체) ──
  139 |             values_np = np.array(val_list, dtype=np.float32)
  140 |             rewards_np = np.array(rew_list, dtype=np.float32)
  141 |             dones_np = np.zeros(len(rew_list), dtype=np.float32)
  142 |             dones_np[-1] = 1.0  # 마지막 스텝은 done
  143 | 
  144 |             # 다음 상태의 가치 추정 (Bootstrap)
  145 |             with torch.no_grad():
  146 |                 last_obs_t = {k: v[-1:] for k, v in batch_obs.items()}
  147 |                 next_val = value_net(last_obs_t).squeeze().cpu().item()
  148 | 
  149 |             advantages_np, returns_np = updater.compute_gae(
  150 |                 rewards_np, values_np, next_val, dones_np
  151 |             )
  152 |             returns_tensor = torch.tensor(returns_np, dtype=torch.float32, device=device)
  153 |             values_tensor = torch.tensor(values_np, dtype=torch.float32, device=device)
  154 |             advantages = torch.tensor(advantages_np, dtype=torch.float32, device=device)
  155 | 
  156 |             if advantages.std() > 1e-8:
  157 |                 advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
  158 | 
  159 |             total_policy_loss = 0.0
  160 |             total_value_loss = 0.0
  161 |             total_entropy = 0.0
  162 |             total_pred_loss = 0.0
  163 | 
  164 |             for _ in range(ppo_config.n_epochs):  # config 기반 epoch 수
  165 |                 new_log_probs, entropy, lstm_out = policy.evaluate_actions(batch_obs, act_tensor)
  166 |                 new_values = value_net(batch_obs).squeeze(-1)
  167 |                 
  168 |                 # Auxiliary Prediction Task
  169 |                 pred_next_vision = policy.predict_next_vision(lstm_out, act_tensor)
  170 |                 pred_loss = F.mse_loss(pred_next_vision, next_vision_tensor)
  171 | 
  172 |                 ratios = torch.exp(new_log_probs - old_log_probs)
  173 |                 surr1 = ratios * advantages
  174 |                 surr2 = torch.clamp(ratios, 0.8, 1.2) * advantages
  175 |                 policy_loss = -torch.min(surr1, surr2).mean()
  176 | 
  177 |                 value_loss = F.mse_loss(new_values, returns_tensor)
  178 |                 entropy_loss = -entropy.mean()
  179 | 
  180 |                 # Add 0.5 * pred_loss to the total loss
  181 |                 loss = policy_loss + 0.5 * value_loss + 0.02 * entropy_loss + 0.5 * pred_loss
  182 | 
  183 |                 optimizer.zero_grad()
  184 |                 loss.backward()
  185 |                 
  186 |                 grad_norm = torch.nn.utils.clip_grad_norm_(
  187 |                     list(policy.parameters()) + list(value_net.parameters()), 0.5
  188 |                 )
  189 |                 optimizer.step()
  190 | 
  191 |                 total_policy_loss += policy_loss.item()
  192 |                 total_value_loss += value_loss.item()
  193 |                 total_entropy += entropy.mean().item()
  194 |                 total_pred_loss += pred_loss.item()
  195 | 
  196 |             metrics = {
  197 |                 "entropy": total_entropy / 3,
  198 |                 "value_loss": total_value_loss / 3,
  199 |                 "policy_loss": total_policy_loss / 3,
  200 |                 "pred_loss": total_pred_loss / 3,
  201 |                 "contact_rate": curriculum.get_contact_rate(),
  202 |                 "reward": ep_reward,
  203 |                 "grad_norm": grad_norm.item() if isinstance(grad_norm, torch.Tensor) else grad_norm,
  204 |             }
  205 |             monitor.record(metrics)
  206 |             
  207 |             # 5 에피소드마다 대시보드 JSON 파일 갱신 (부하 방지)
  208 |             if ep % 5 == 0:
  209 |                 dashboard_logger.log_episode_stats(ep, metrics)
  210 | 
  211 |         if ep % record_interval == 0:
  212 |             recorder.record_episode(env, policy, ep, device)
  213 | 
  214 |         if ep % 50 == 0:
  215 |             new_stage = curriculum.check_and_update()
  216 |             env.set_curriculum_stage(new_stage)
  217 | 
  218 |         if ep % 20 == 0 or ep == total_episodes:
  219 |             cr = curriculum.get_contact_rate()
  220 |             avg_rew = np.mean(list(reward_window)) if reward_window else 0.0
  221 |             elapsed = time.time() - start_time
  222 |             stage = curriculum.current_stage
  223 |             stage_name = env.CURRICULUM[stage]["name"]
  224 | 
  225 |             print(
  226 |                 f"  [EP {ep:4d}/{total_episodes}] "
  227 |                 f"Stage {stage} ({stage_name}) | "
  228 |                 f"CR={cr:.1%} | "
  229 |                 f"Reward={avg_rew:+.2f} | "
  230 |                 f"{elapsed:.0f}s"
  231 |             )
  232 | 
  233 |             ge = env.game_engine
  234 |             inning_str = f"{ge.inning}회{'초' if ge.is_top else '말'}"
  235 |             r_str = f"1루({'O' if ge.runners[0] else 'X'}) 2루({'O' if ge.runners[1] else 'X'}) 3루({'O' if ge.runners[2] else 'X'})"
  236 |             print("  " + "=" * 52)
  237 |             print(f"   ⚾ 10-DOF ROBOT | {inning_str} | OUT: {ge.outs} | HOME {ge.score_home} - {ge.score_away} AWAY")
  238 |             print(f"   🟢 Ball: {ge.balls}  🔴 Strike: {ge.strikes} | 🏃 주자: {r_str}")
  239 |             print("  " + "=" * 52)
  240 | 
  241 |             metrics = {
  242 |                 "contact_rate": cr,
  243 |                 "reward": avg_rew,
  244 |             }
  245 |             dashboard_logger.log_episode_stats(ep, metrics)
  246 | 
  247 |             for alert in monitor.check_health():
  248 |                 print(f"    {alert}")
  249 |             for alert in auditor.audit():
  250 |                 print(f"    {alert}")
  251 | 
  252 |             if cr > best_contact_rate:
  253 |                 best_contact_rate = cr
  254 | 
  255 |     save_dir = Path(__file__).parent.parent / "checkpoints"
  256 |     save_dir.mkdir(parents=True, exist_ok=True)
  257 |     save_path = save_dir / "curriculum_multimodal_policy.pt"
  258 | 
  259 |     torch.save({
  260 |         "policy_state_dict": policy.state_dict(),
  261 |         "value_state_dict": value_net.state_dict(),
  262 |         "curriculum_stage": curriculum.current_stage,
  263 |         "best_contact_rate": best_contact_rate,
  264 |         "episodes": total_episodes,
  265 |     }, save_path)
  266 | 
  267 |     print("\n" + "=" * 70)
  268 |     print(f" 🏆 멀티모달 Phase 2 학습 완료!")
  269 |     print(f"    최종 Stage: {curriculum.current_stage}")
  270 |     print(f"    최고 Contact Rate: {best_contact_rate:.1%}")
  271 |     print(f"    {auditor.get_summary()}")
  272 |     print(f"    체크포인트: {save_path}")
  273 |     print("=" * 70)
  274 | 
  275 | 
  276 | if __name__ == "__main__":
  277 |     run_curriculum_training(total_episodes=1000, initial_stage=1, record_interval=50)
````
