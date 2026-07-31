"""
curriculum_trainer.py — 커리큘럼 기반 통합 PPO 학습 파이프라인 (Phase 2)

HumanoidBaseballEnv + CurriculumManager + HealthMonitor + RewardAuditSystem 
+ EpisodeRecorder 를 연결하여 학습 파이프라인을 구축합니다.
"""

import os
import sys
import time
import numpy as np
from pathlib import Path
from collections import deque

import torch
import torch.nn.functional as F
import torch.optim as optim

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from humanoid.envs.humanoid_baseball_env import HumanoidBaseballEnv
from humanoid.training.humanoid_networks import MultimodalBatterPolicy, MultimodalValueNetwork, get_device
from training.curriculum_manager import CurriculumManager
from training.health_monitor import TrainingHealthMonitor
from training.episode_recorder import EpisodeRecorder
from training.reward_audit import RewardAuditSystem
from training.logger import DashboardLogger


def obs_to_tensor(obs_dict: dict, device: torch.device, unsqueeze: bool = True) -> dict:
    """Dict 형태의 관찰값을 PyTorch 텐서로 변환합니다."""
    tensors = {}
    for k, v in obs_dict.items():
        t = torch.tensor(v, dtype=torch.float32, device=device)
        if unsqueeze:
            t = t.unsqueeze(0)
        tensors[k] = t
    return tensors


def run_curriculum_training(
    total_episodes: int = 300,
    initial_stage: int = 1,
    lr: float = 1e-4,
    record_interval: int = 100,
):
    device = get_device()
    print("=" * 70)
    print(" ⚾ 커리큘럼 기반 Phase 2 멀티모달 PPO 학습 시작")
    print(f"   Device: {device} | Episodes: {total_episodes}")
    print(f"   Initial Stage: {initial_stage} | Learning Rate: {lr}")
    print("=" * 70)

    # ── 환경 (녹화를 위해 rgb_array로 생성) ──
    env = HumanoidBaseballEnv(render_mode="rgb_array")
    env.set_curriculum_stage(initial_stage)

    # ── 에이전트 ──
    act_dim = env.action_space.shape[0]  # 7

    policy = MultimodalBatterPolicy(action_dim=act_dim, hidden_dim=256, num_layers=2).to(device)
    value_net = MultimodalValueNetwork(hidden_dim=256).to(device)
    optimizer = optim.Adam(list(policy.parameters()) + list(value_net.parameters()), lr=lr)

    # ── 매니저 & 모니터 & 렌더/감사 & 대시보드 로거 ──
    curriculum = CurriculumManager(initial_stage=initial_stage)
    monitor = TrainingHealthMonitor()
    recorder = EpisodeRecorder()
    auditor = RewardAuditSystem()
    dashboard_logger = DashboardLogger()

    reward_window = deque(maxlen=50)
    imitation_window = deque(maxlen=50)
    best_contact_rate = 0.0
    start_time = time.time()

    for ep in range(1, total_episodes + 1):
        obs, info = env.reset()
        done = False
        hidden = None

        obs_list, act_list, rew_list, log_prob_list, val_list, next_vision_list = [], [], [], [], [], []

        while not done:
            obs_t = obs_to_tensor(obs, device)

            with torch.no_grad():
                action_t, log_prob_t, _, hidden = policy.get_action(obs_t, hidden)
                val_t = value_net(obs_t)

            action = action_t.squeeze(0).cpu().numpy()
            log_prob = log_prob_t.squeeze(0).cpu().item()
            value = val_t.squeeze().cpu().item()

            next_obs, reward, terminated, truncated, step_info = env.step(action)
            done = terminated or truncated

            obs_list.append(obs)
            act_list.append(action)
            rew_list.append(reward)
            log_prob_list.append(log_prob)
            val_list.append(value)
            next_vision_list.append(next_obs["vision"])

            obs = next_obs

        ep_reward = sum(rew_list)
        reward_window.append(ep_reward)
        contacted = step_info.get("has_contacted", False)
        imitation_reward = step_info.get("imitation_reward", 0.0)
        imitation_window.append(imitation_reward)

        curriculum.record_episode(contacted, step_info)
        if contacted:
            auditor.record_hit(step_info, ep_reward)

        # ── PPO Gradient Update ──
        if len(obs_list) > 1:
            # 리스트 딕셔너리 -> 딕셔너리 텐서
            batch_obs = {
                k: torch.tensor(np.array([o[k] for o in obs_list]), dtype=torch.float32, device=device)
                for k in obs_list[0].keys()
            }
            
            act_tensor = torch.tensor(np.array(act_list), dtype=torch.float32, device=device)
            old_log_probs = torch.tensor(np.array(log_prob_list), dtype=torch.float32, device=device)
            next_vision_tensor = torch.tensor(np.array(next_vision_list), dtype=torch.float32, device=device)

            returns = []
            discounted = 0.0
            for r in reversed(rew_list):
                discounted = r + 0.99 * discounted
                returns.insert(0, discounted)
            returns_tensor = torch.tensor(returns, dtype=torch.float32, device=device)
            values_tensor = torch.tensor(np.array(val_list), dtype=torch.float32, device=device)
            
            advantages = returns_tensor - values_tensor
            if advantages.std() > 1e-8:
                advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

            total_policy_loss = 0.0
            total_value_loss = 0.0
            total_entropy = 0.0
            total_pred_loss = 0.0

            for _ in range(3):
                new_log_probs, entropy, lstm_out = policy.evaluate_actions(batch_obs, act_tensor)
                new_values = value_net(batch_obs).squeeze(-1)
                
                # Auxiliary Prediction Task
                pred_next_vision = policy.predict_next_vision(lstm_out, act_tensor)
                pred_loss = F.mse_loss(pred_next_vision, next_vision_tensor)

                ratios = torch.exp(new_log_probs - old_log_probs)
                surr1 = ratios * advantages
                surr2 = torch.clamp(ratios, 0.8, 1.2) * advantages
                policy_loss = -torch.min(surr1, surr2).mean()

                value_loss = F.mse_loss(new_values, returns_tensor)
                entropy_loss = -entropy.mean()

                # Add 0.5 * pred_loss to the total loss
                loss = policy_loss + 0.5 * value_loss + 0.02 * entropy_loss + 0.5 * pred_loss

                optimizer.zero_grad()
                loss.backward()
                
                grad_norm = torch.nn.utils.clip_grad_norm_(
                    list(policy.parameters()) + list(value_net.parameters()), 0.5
                )
                optimizer.step()

                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy += entropy.mean().item()
                total_pred_loss += pred_loss.item()

            metrics = {
                "entropy": total_entropy / 3,
                "value_loss": total_value_loss / 3,
                "policy_loss": total_policy_loss / 3,
                "pred_loss": total_pred_loss / 3,
                "contact_rate": curriculum.get_contact_rate(),
                "reward": ep_reward,
                "grad_norm": grad_norm.item() if isinstance(grad_norm, torch.Tensor) else grad_norm,
            }
            monitor.record(metrics)
            
            # 5 에피소드마다 대시보드 JSON 파일 갱신 (부하 방지)
            if ep % 5 == 0:
                dashboard_logger.log_episode_stats(ep, metrics)

        if ep % record_interval == 0:
            recorder.record_episode(env, policy, ep, device)

        if ep % 50 == 0:
            new_stage = curriculum.check_and_update()
            env.set_curriculum_stage(new_stage)

        if ep % 20 == 0 or ep == total_episodes:
            cr = curriculum.get_contact_rate()
            avg_rew = np.mean(list(reward_window)) if reward_window else 0.0
            avg_imit = np.mean(list(imitation_window)) if imitation_window else 0.0
            elapsed = time.time() - start_time
            stage = curriculum.current_stage
            stage_name = env.CURRICULUM[stage]["name"]

            print(
                f"  [EP {ep:4d}/{total_episodes}] "
                f"Stage {stage} ({stage_name}) | "
                f"CR={cr:.1%} | "
                f"Reward={avg_rew:+.2f} | "
                f"Imit={avg_imit:.2f} | "
                f"{elapsed:.0f}s"
            )
            
            # 야구 게임 스코어보드 출력
            ge = env.game_engine
            inning_str = f"{ge.inning}회{'초' if ge.is_top else '말'}"
            r_str = f"1루({'O' if ge.runners[0] else 'X'}) 2루({'O' if ge.runners[1] else 'X'}) 3루({'O' if ge.runners[2] else 'X'})"
            print("  " + "=" * 48)
            print(f"   ⚾ 현재 상황: {inning_str} | 아웃: {ge.outs} | 점수: HOME {ge.score_home} - {ge.score_away} AWAY")
            print(f"   🟢 Ball: {ge.balls}  🔴 Strike: {ge.strikes}")
            print(f"   🏃 주자: {r_str}")
            print("  " + "=" * 48)

            for alert in monitor.check_health():
                print(f"    {alert}")
            for alert in auditor.audit():
                print(f"    {alert}")

            if cr > best_contact_rate:
                best_contact_rate = cr

    save_dir = Path(__file__).parent.parent / "checkpoints"
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / "curriculum_multimodal_policy.pt"

    torch.save({
        "policy_state_dict": policy.state_dict(),
        "value_state_dict": value_net.state_dict(),
        "curriculum_stage": curriculum.current_stage,
        "best_contact_rate": best_contact_rate,
        "episodes": total_episodes,
    }, save_path)

    print("\n" + "=" * 70)
    print(f" 🏆 멀티모달 Phase 2 학습 완료!")
    print(f"    최종 Stage: {curriculum.current_stage}")
    print(f"    최고 Contact Rate: {best_contact_rate:.1%}")
    print(f"    {auditor.get_summary()}")
    print(f"    체크포인트: {save_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_curriculum_training(total_episodes=10000, initial_stage=1, record_interval=50)
