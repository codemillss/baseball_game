# baseball/archive/humanoid/training/humanoid_trainer.py

원본: [archive/humanoid/training/humanoid_trainer.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/humanoid/training/humanoid_trainer.py)

SHA256: `d7c1080f4d934246e925aa2bd85050b4f1be52509f7d4c495fac2b1ff3a6a260`

전체 257행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `obs_to_tensor` | FunctionDef | 30 | 38 |
| `run_curriculum_training` | FunctionDef | 41 | 253 |

## 전체 원문

````text
    1 | """
    2 | curriculum_trainer.py — 커리큘럼 기반 통합 PPO 학습 파이프라인 (Phase 2)
    3 | 
    4 | HumanoidBaseballEnv + CurriculumManager + HealthMonitor + RewardAuditSystem 
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
   21 | from humanoid.envs.humanoid_baseball_env import HumanoidBaseballEnv
   22 | from humanoid.training.humanoid_networks import MultimodalBatterPolicy, MultimodalValueNetwork, get_device
   23 | from training.curriculum_manager import CurriculumManager
   24 | from training.health_monitor import TrainingHealthMonitor
   25 | from training.episode_recorder import EpisodeRecorder
   26 | from training.reward_audit import RewardAuditSystem
   27 | from training.logger import DashboardLogger
   28 | 
   29 | 
   30 | def obs_to_tensor(obs_dict: dict, device: torch.device, unsqueeze: bool = True) -> dict:
   31 |     """Dict 형태의 관찰값을 PyTorch 텐서로 변환합니다."""
   32 |     tensors = {}
   33 |     for k, v in obs_dict.items():
   34 |         t = torch.tensor(v, dtype=torch.float32, device=device)
   35 |         if unsqueeze:
   36 |             t = t.unsqueeze(0)
   37 |         tensors[k] = t
   38 |     return tensors
   39 | 
   40 | 
   41 | def run_curriculum_training(
   42 |     total_episodes: int = 300,
   43 |     initial_stage: int = 1,
   44 |     lr: float = 1e-4,
   45 |     record_interval: int = 100,
   46 | ):
   47 |     device = get_device()
   48 |     print("=" * 70)
   49 |     print(" ⚾ 커리큘럼 기반 Phase 2 멀티모달 PPO 학습 시작")
   50 |     print(f"   Device: {device} | Episodes: {total_episodes}")
   51 |     print(f"   Initial Stage: {initial_stage} | Learning Rate: {lr}")
   52 |     print("=" * 70)
   53 | 
   54 |     # ── 환경 (녹화를 위해 rgb_array로 생성) ──
   55 |     env = HumanoidBaseballEnv(render_mode="rgb_array")
   56 |     env.set_curriculum_stage(initial_stage)
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
   72 |     reward_window = deque(maxlen=50)
   73 |     imitation_window = deque(maxlen=50)
   74 |     best_contact_rate = 0.0
   75 |     start_time = time.time()
   76 | 
   77 |     for ep in range(1, total_episodes + 1):
   78 |         obs, info = env.reset()
   79 |         done = False
   80 |         hidden = None
   81 | 
   82 |         obs_list, act_list, rew_list, log_prob_list, val_list, next_vision_list = [], [], [], [], [], []
   83 | 
   84 |         while not done:
   85 |             obs_t = obs_to_tensor(obs, device)
   86 | 
   87 |             with torch.no_grad():
   88 |                 action_t, log_prob_t, _, hidden = policy.get_action(obs_t, hidden)
   89 |                 val_t = value_net(obs_t)
   90 | 
   91 |             action = action_t.squeeze(0).cpu().numpy()
   92 |             log_prob = log_prob_t.squeeze(0).cpu().item()
   93 |             value = val_t.squeeze().cpu().item()
   94 | 
   95 |             next_obs, reward, terminated, truncated, step_info = env.step(action)
   96 |             done = terminated or truncated
   97 | 
   98 |             obs_list.append(obs)
   99 |             act_list.append(action)
  100 |             rew_list.append(reward)
  101 |             log_prob_list.append(log_prob)
  102 |             val_list.append(value)
  103 |             next_vision_list.append(next_obs["vision"])
  104 | 
  105 |             obs = next_obs
  106 | 
  107 |         ep_reward = sum(rew_list)
  108 |         reward_window.append(ep_reward)
  109 |         contacted = step_info.get("has_contacted", False)
  110 |         imitation_reward = step_info.get("imitation_reward", 0.0)
  111 |         imitation_window.append(imitation_reward)
  112 | 
  113 |         curriculum.record_episode(contacted, step_info)
  114 |         if contacted:
  115 |             auditor.record_hit(step_info, ep_reward)
  116 | 
  117 |         # ── PPO Gradient Update ──
  118 |         if len(obs_list) > 1:
  119 |             # 리스트 딕셔너리 -> 딕셔너리 텐서
  120 |             batch_obs = {
  121 |                 k: torch.tensor(np.array([o[k] for o in obs_list]), dtype=torch.float32, device=device)
  122 |                 for k in obs_list[0].keys()
  123 |             }
  124 |             
  125 |             act_tensor = torch.tensor(np.array(act_list), dtype=torch.float32, device=device)
  126 |             old_log_probs = torch.tensor(np.array(log_prob_list), dtype=torch.float32, device=device)
  127 |             next_vision_tensor = torch.tensor(np.array(next_vision_list), dtype=torch.float32, device=device)
  128 | 
  129 |             returns = []
  130 |             discounted = 0.0
  131 |             for r in reversed(rew_list):
  132 |                 discounted = r + 0.99 * discounted
  133 |                 returns.insert(0, discounted)
  134 |             returns_tensor = torch.tensor(returns, dtype=torch.float32, device=device)
  135 |             values_tensor = torch.tensor(np.array(val_list), dtype=torch.float32, device=device)
  136 |             
  137 |             advantages = returns_tensor - values_tensor
  138 |             if advantages.std() > 1e-8:
  139 |                 advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
  140 | 
  141 |             total_policy_loss = 0.0
  142 |             total_value_loss = 0.0
  143 |             total_entropy = 0.0
  144 |             total_pred_loss = 0.0
  145 | 
  146 |             for _ in range(3):
  147 |                 new_log_probs, entropy, lstm_out = policy.evaluate_actions(batch_obs, act_tensor)
  148 |                 new_values = value_net(batch_obs).squeeze(-1)
  149 |                 
  150 |                 # Auxiliary Prediction Task
  151 |                 pred_next_vision = policy.predict_next_vision(lstm_out, act_tensor)
  152 |                 pred_loss = F.mse_loss(pred_next_vision, next_vision_tensor)
  153 | 
  154 |                 ratios = torch.exp(new_log_probs - old_log_probs)
  155 |                 surr1 = ratios * advantages
  156 |                 surr2 = torch.clamp(ratios, 0.8, 1.2) * advantages
  157 |                 policy_loss = -torch.min(surr1, surr2).mean()
  158 | 
  159 |                 value_loss = F.mse_loss(new_values, returns_tensor)
  160 |                 entropy_loss = -entropy.mean()
  161 | 
  162 |                 # Add 0.5 * pred_loss to the total loss
  163 |                 loss = policy_loss + 0.5 * value_loss + 0.02 * entropy_loss + 0.5 * pred_loss
  164 | 
  165 |                 optimizer.zero_grad()
  166 |                 loss.backward()
  167 |                 
  168 |                 grad_norm = torch.nn.utils.clip_grad_norm_(
  169 |                     list(policy.parameters()) + list(value_net.parameters()), 0.5
  170 |                 )
  171 |                 optimizer.step()
  172 | 
  173 |                 total_policy_loss += policy_loss.item()
  174 |                 total_value_loss += value_loss.item()
  175 |                 total_entropy += entropy.mean().item()
  176 |                 total_pred_loss += pred_loss.item()
  177 | 
  178 |             metrics = {
  179 |                 "entropy": total_entropy / 3,
  180 |                 "value_loss": total_value_loss / 3,
  181 |                 "policy_loss": total_policy_loss / 3,
  182 |                 "pred_loss": total_pred_loss / 3,
  183 |                 "contact_rate": curriculum.get_contact_rate(),
  184 |                 "reward": ep_reward,
  185 |                 "grad_norm": grad_norm.item() if isinstance(grad_norm, torch.Tensor) else grad_norm,
  186 |             }
  187 |             monitor.record(metrics)
  188 |             
  189 |             # 5 에피소드마다 대시보드 JSON 파일 갱신 (부하 방지)
  190 |             if ep % 5 == 0:
  191 |                 dashboard_logger.log_episode_stats(ep, metrics)
  192 | 
  193 |         if ep % record_interval == 0:
  194 |             recorder.record_episode(env, policy, ep, device)
  195 | 
  196 |         if ep % 50 == 0:
  197 |             new_stage = curriculum.check_and_update()
  198 |             env.set_curriculum_stage(new_stage)
  199 | 
  200 |         if ep % 20 == 0 or ep == total_episodes:
  201 |             cr = curriculum.get_contact_rate()
  202 |             avg_rew = np.mean(list(reward_window)) if reward_window else 0.0
  203 |             avg_imit = np.mean(list(imitation_window)) if imitation_window else 0.0
  204 |             elapsed = time.time() - start_time
  205 |             stage = curriculum.current_stage
  206 |             stage_name = env.CURRICULUM[stage]["name"]
  207 | 
  208 |             print(
  209 |                 f"  [EP {ep:4d}/{total_episodes}] "
  210 |                 f"Stage {stage} ({stage_name}) | "
  211 |                 f"CR={cr:.1%} | "
  212 |                 f"Reward={avg_rew:+.2f} | "
  213 |                 f"Imit={avg_imit:.2f} | "
  214 |                 f"{elapsed:.0f}s"
  215 |             )
  216 |             
  217 |             # 야구 게임 스코어보드 출력
  218 |             ge = env.game_engine
  219 |             inning_str = f"{ge.inning}회{'초' if ge.is_top else '말'}"
  220 |             r_str = f"1루({'O' if ge.runners[0] else 'X'}) 2루({'O' if ge.runners[1] else 'X'}) 3루({'O' if ge.runners[2] else 'X'})"
  221 |             print("  " + "=" * 48)
  222 |             print(f"   ⚾ 현재 상황: {inning_str} | 아웃: {ge.outs} | 점수: HOME {ge.score_home} - {ge.score_away} AWAY")
  223 |             print(f"   🟢 Ball: {ge.balls}  🔴 Strike: {ge.strikes}")
  224 |             print(f"   🏃 주자: {r_str}")
  225 |             print("  " + "=" * 48)
  226 | 
  227 |             for alert in monitor.check_health():
  228 |                 print(f"    {alert}")
  229 |             for alert in auditor.audit():
  230 |                 print(f"    {alert}")
  231 | 
  232 |             if cr > best_contact_rate:
  233 |                 best_contact_rate = cr
  234 | 
  235 |     save_dir = Path(__file__).parent.parent / "checkpoints"
  236 |     save_dir.mkdir(parents=True, exist_ok=True)
  237 |     save_path = save_dir / "curriculum_multimodal_policy.pt"
  238 | 
  239 |     torch.save({
  240 |         "policy_state_dict": policy.state_dict(),
  241 |         "value_state_dict": value_net.state_dict(),
  242 |         "curriculum_stage": curriculum.current_stage,
  243 |         "best_contact_rate": best_contact_rate,
  244 |         "episodes": total_episodes,
  245 |     }, save_path)
  246 | 
  247 |     print("\n" + "=" * 70)
  248 |     print(f" 🏆 멀티모달 Phase 2 학습 완료!")
  249 |     print(f"    최종 Stage: {curriculum.current_stage}")
  250 |     print(f"    최고 Contact Rate: {best_contact_rate:.1%}")
  251 |     print(f"    {auditor.get_summary()}")
  252 |     print(f"    체크포인트: {save_path}")
  253 |     print("=" * 70)
  254 | 
  255 | 
  256 | if __name__ == "__main__":
  257 |     run_curriculum_training(total_episodes=10000, initial_stage=1, record_interval=50)
````
