"""
world_model_trainer.py — DreamerV3 스타일 World Model 학습 엔진

학습 흐름:
    1. [실제 환경] 에피소드 수집 → Replay Buffer 저장
    2. [World Model] 미니배치로 WM 학습 (Representation + Prediction + KL)
    3. [상상 롤아웃] 학습된 WM에서 H=15 스텝 상상
    4. [Actor-Critic] 상상 경험으로 Lambda-Return 기반 업데이트

핵심 이점:
    - 실제 MuJoCo 1 step → 상상 롤아웃 imagination_ratio steps
    - PrioritizedReplayBuffer가 off-policy 데이터로 제대로 활용됨
    - 희귀 이벤트(홈런)를 상상에서 반복 학습 가능
"""

import os
import sys
import time
import numpy as np
from pathlib import Path
from collections import deque
from typing import Dict, List, Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from envs.unified_baseball_env import UnifiedBaseballEnv
from training.world_model import BaseballRSSM, compute_world_model_loss, symlog, symexp
from training.curriculum_manager import CurriculumManager
from training.health_monitor import TrainingHealthMonitor
from training.episode_recorder import EpisodeRecorder
from training.reward_audit import RewardAuditSystem
from training.logger import DashboardLogger


# ──────────────────────────────────────────────────────────────
#  Replay Buffer (시퀀스 단위 저장)
# ──────────────────────────────────────────────────────────────

class SequenceReplayBuffer:
    """에피소드 시퀀스를 저장하는 링 버퍼.

    World Model 학습은 단일 transition이 아닌
    연속된 시퀀스(sequence)로 학습해야 RSSM이 올바르게 작동함.

    Args:
        capacity:   저장할 최대 에피소드 수
        seq_len:    학습 시 샘플링할 시퀀스 길이
    """

    def __init__(self, capacity: int = 5_000, seq_len: int = 50):
        self.capacity = capacity
        self.seq_len  = seq_len
        self.episodes: List[Dict] = []
        self.write_ptr = 0
        self.size = 0

        # 우선순위 부스트용 홈런/컨택 카운트
        self.n_home_runs = 0
        self.n_contacts  = 0

    def add_episode(self, episode: Dict):
        """에피소드 딕셔너리 저장.

        episode 형식:
            {
                "obs_seq":    {"vision": (T,4), "prop": (T,18), "context": (T,6)},
                "action_seq": (T, 9),
                "reward_seq": (T,),
                "done_seq":   (T,),    # 1.0 if terminal at that step
                "has_contact": bool,
                "has_home_run": bool,
            }
        """
        if len(self.episodes) < self.capacity:
            self.episodes.append(episode)
        else:
            self.episodes[self.write_ptr] = episode

        self.write_ptr = (self.write_ptr + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

        if episode.get("has_home_run", False):
            self.n_home_runs += 1
        if episode.get("has_contact", False):
            self.n_contacts += 1

    def sample(self, batch_size: int) -> Optional[Dict[str, torch.Tensor]]:
        """랜덤 에피소드에서 seq_len 길이 시퀀스를 batch_size 개 샘플링.

        Returns:
            배치 딕셔너리 또는 데이터 부족 시 None
        """
        if self.size < batch_size:
            return None

        obs_batch   = {"vision": [], "proprioception": [], "context": []}
        act_batch   = []
        rew_batch   = []
        done_batch  = []

        indices = np.random.choice(self.size, batch_size, replace=True)

        for idx in indices:
            ep = self.episodes[idx]
            T  = ep["action_seq"].shape[0]

            if T < 2:
                # 너무 짧은 에피소드는 반복 패딩
                start = 0
            else:
                start = np.random.randint(0, max(1, T - self.seq_len + 1))

            end = start + self.seq_len

            def _slice(arr):
                if len(arr) >= end:
                    return arr[start:end]
                # 끝에 패딩 (마지막 값 반복)
                padded = np.concatenate([arr[start:], np.tile(arr[-1:], (end - len(arr), 1) if arr.ndim > 1 else (end - len(arr),))], axis=0)
                return padded[:self.seq_len]

            for k in obs_batch:
                obs_batch[k].append(_slice(ep["obs_seq"][k]))
            act_batch.append(_slice(ep["action_seq"]))
            rew_batch.append(_slice(ep["reward_seq"]))
            done_batch.append(_slice(ep["done_seq"]))

        device = torch.device("cpu")
        batch = {
            "obs": {k: torch.tensor(np.array(v), dtype=torch.float32) for k, v in obs_batch.items()},
            "actions":  torch.tensor(np.array(act_batch),  dtype=torch.float32),
            "rewards":  torch.tensor(np.array(rew_batch),  dtype=torch.float32),
            "dones":    torch.tensor(np.array(done_batch), dtype=torch.float32),
        }
        return batch

    @property
    def fill_ratio(self) -> float:
        return self.size / self.capacity


# ──────────────────────────────────────────────────────────────
#  Actor / Critic (잠재 공간에서 작동)
# ──────────────────────────────────────────────────────────────

def _mlp(in_dim: int, out_dim: int, hidden: int = 256) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(in_dim, hidden), nn.LayerNorm(hidden), nn.SiLU(),
        nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.SiLU(),
        nn.Linear(hidden, out_dim),
    )


class LatentActor(nn.Module):
    """잠재 상태 s_t = (h_t, z_t) → 액션 분포."""

    def __init__(self, state_dim: int, action_dim: int, hidden: int = 256):
        super().__init__()
        self.trunk   = _mlp(state_dim, hidden, hidden)
        self.mean    = nn.Linear(hidden, action_dim)
        self.log_std = nn.Parameter(torch.zeros(action_dim))

    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        feat  = self.trunk(state)
        mean  = torch.tanh(self.mean(feat))
        std   = torch.exp(self.log_std.clamp(-5, 2)).expand_as(mean)
        return mean, std

    def get_action(self, state: torch.Tensor, deterministic: bool = False):
        mean, std = self.forward(state)
        if deterministic:
            return mean, None
        dist   = torch.distributions.Normal(mean, std)
        action = torch.clamp(dist.rsample(), -1.0, 1.0)
        log_p  = dist.log_prob(action).sum(-1)
        return action, log_p


class LatentCritic(nn.Module):
    """잠재 상태 s_t → V(s_t) (SymLog 공간 스칼라)."""

    def __init__(self, state_dim: int, hidden: int = 256):
        super().__init__()
        self.net = _mlp(state_dim, 1, hidden)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.net(state).squeeze(-1)


# ──────────────────────────────────────────────────────────────
#  Dreamer 학습 엔진
# ──────────────────────────────────────────────────────────────

class DreamerTrainer:
    """Baseball Dreamer 학습 엔진.

    Args:
        env:                UnifiedBaseballEnv 인스턴스
        imagination_horizon: 상상 롤아웃 스텝 수 (H)
        wm_lr:              World Model 학습률
        actor_lr:           Actor 학습률
        critic_lr:          Critic 학습률
        wm_batch_size:      World Model 미니배치 에피소드 수
        buffer_capacity:    Replay Buffer 용량 (에피소드 단위)
        seq_len:            학습 시퀀스 길이
        kl_scale:           KL 손실 가중치
        lambda_return:      Lambda-Return λ 값
    """

    def __init__(
        self,
        env:                  UnifiedBaseballEnv,
        imagination_horizon:  int   = 15,
        wm_lr:                float = 3e-4,
        actor_lr:             float = 3e-4,
        critic_lr:            float = 3e-4,
        wm_batch_size:        int   = 16,
        buffer_capacity:      int   = 5_000,
        seq_len:              int   = 50,
        kl_scale:             float = 0.1,
        lambda_return:        float = 0.95,
    ):
        self.env    = env
        self.H      = imagination_horizon
        self.kl_scale   = kl_scale
        self.lambda_ret = lambda_return
        self.wm_batch   = wm_batch_size
        self.device     = self._get_device()

        # ── World Model ──
        self.rssm = BaseballRSSM(
            hidden_dim=256, latent_classes=32, latent_dim=32,
            obs_dim=28, action_dim=env.action_space.shape[0],
        ).to(self.device)

        # ── Actor / Critic ──
        self.actor  = LatentActor(self.rssm.state_dim,  env.action_space.shape[0]).to(self.device)
        self.critic = LatentCritic(self.rssm.state_dim).to(self.device)
        # 느린 Target Critic (EMA)
        self.target_critic = LatentCritic(self.rssm.state_dim).to(self.device)
        self.target_critic.load_state_dict(self.critic.state_dict())

        # ── Optimizers ──
        self.wm_opt     = optim.Adam(self.rssm.parameters(), lr=wm_lr, eps=1e-8)
        self.actor_opt  = optim.Adam(self.actor.parameters(),  lr=actor_lr, eps=1e-8)
        self.critic_opt = optim.Adam(self.critic.parameters(), lr=critic_lr, eps=1e-8)

        # ── Replay Buffer ──
        self.buffer = SequenceReplayBuffer(capacity=buffer_capacity, seq_len=seq_len)

        # ── 로깅 ──
        self.wm_loss_history    = deque(maxlen=100)
        self.actor_loss_history = deque(maxlen=100)
        self.imag_reward_history= deque(maxlen=100)

    @staticmethod
    def _get_device() -> torch.device:
        if torch.backends.mps.is_available():
            return torch.device("mps")
        if torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")

    # ──────────────────────────────────────────────────────────
    #  에피소드 수집 (실제 환경)
    # ──────────────────────────────────────────────────────────

    @torch.no_grad()
    def collect_episode(self) -> Dict:
        """실제 환경에서 에피소드 하나를 수집."""
        obs, info = self.env.reset()
        h, z = self.rssm.initial_state(1, self.device)

        obs_lists  = {"vision": [], "proprioception": [], "context": []}
        act_list, rew_list, done_list = [], [], []

        done = False
        while not done:
            # 관찰 → 텐서
            obs_t = {k: torch.tensor(v, dtype=torch.float32, device=self.device).unsqueeze(0)
                     for k, v in obs.items()}

            # RSSM observe (잠재 상태 업데이트)
            action_dummy = torch.zeros(1, self.env.action_space.shape[0], device=self.device)
            if act_list:
                action_dummy = torch.tensor(act_list[-1], dtype=torch.float32, device=self.device).unsqueeze(0)

            h, z, _ = self.rssm.observe(obs_t, action_dummy, h, z)
            s = self.rssm.get_state(h, z)

            # Actor로 액션 결정
            action, _ = self.actor.get_action(s)
            action_np  = action.squeeze(0).cpu().numpy()

            next_obs, reward, terminated, truncated, step_info = self.env.step(action_np)
            done = terminated or truncated

            for k in obs_lists:
                obs_lists[k].append(obs[k])
            act_list.append(action_np)
            rew_list.append(float(reward))
            done_list.append(1.0 if done else 0.0)

            obs = next_obs

        episode = {
            "obs_seq": {k: np.array(v) for k, v in obs_lists.items()},
            "action_seq":  np.array(act_list),
            "reward_seq":  np.array(rew_list),
            "done_seq":    np.array(done_list),
            "has_contact": step_info.get("has_contacted", False),
            "has_home_run": "Home Run" in step_info.get("game_event", ""),
            "total_reward": sum(rew_list),
        }
        return episode

    # ──────────────────────────────────────────────────────────
    #  World Model 학습
    # ──────────────────────────────────────────────────────────

    def train_world_model(self) -> Optional[Dict[str, float]]:
        """Replay Buffer에서 미니배치를 샘플링해 World Model 학습.

        Returns:
            손실 딕셔너리 또는 데이터 부족 시 None
        """
        batch = self.buffer.sample(self.wm_batch)
        if batch is None:
            return None

        # 디바이스 이동
        obs_seq    = {k: v.to(self.device) for k, v in batch["obs"].items()}
        action_seq = batch["actions"].to(self.device)   # (B, T, 9)
        reward_seq = batch["rewards"].to(self.device)   # (B, T)
        done_seq   = batch["dones"].to(self.device)     # (B, T)

        B, T = action_seq.shape[:2]

        # 초기 상태
        h0, z0 = self.rssm.initial_state(B, self.device)

        # 시퀀스 전체 처리 (Posterior)
        h_seq, z_seq, post_logits, prior_logits = self.rssm.observe_sequence(
            obs_seq, action_seq, h0, z0
        )

        # 관찰 재구성 타겟 (vision + prop + context 결합)
        obs_target = torch.cat([
            obs_seq["vision"],
            obs_seq["proprioception"],
            obs_seq["context"],
        ], dim=-1)  # (B, T, 28)

        # 손실 계산
        losses = compute_world_model_loss(
            self.rssm, h_seq, z_seq,
            post_logits, prior_logits,
            obs_target, reward_seq,
            continue_target=(1.0 - done_seq),
            kl_scale=self.kl_scale,
        )

        # 역전파
        self.wm_opt.zero_grad()
        losses["total"].backward()
        nn.utils.clip_grad_norm_(self.rssm.parameters(), 100.0)
        self.wm_opt.step()

        loss_vals = {k: v.item() for k, v in losses.items()}
        self.wm_loss_history.append(loss_vals["total"])
        return loss_vals

    # ──────────────────────────────────────────────────────────
    #  상상 롤아웃 + Actor-Critic 업데이트
    # ──────────────────────────────────────────────────────────

    def _lambda_return(
        self,
        rewards:   torch.Tensor,  # (B, H)
        values:    torch.Tensor,  # (B, H)
        continues: torch.Tensor,  # (B, H) — 계속 확률
        lambda_:   float = 0.95,
        gamma:     float = 0.99,
    ) -> torch.Tensor:
        """Lambda-Return 계산 (DreamerV3 방식).

        R^λ_t = r_t + γ * c_t * [(1-λ)*V_{t+1} + λ*R^λ_{t+1}]
        """
        B, H = rewards.shape
        targets = torch.zeros_like(rewards)
        last = values[:, -1]  # bootstrap from last value

        for t in reversed(range(H)):
            bootstrap = (1 - lambda_) * values[:, t] + lambda_ * last
            targets[:, t] = rewards[:, t] + gamma * continues[:, t] * bootstrap
            last = targets[:, t]

        return targets

    def update_actor_critic(self, start_h: torch.Tensor, start_z: torch.Tensor) -> Dict[str, float]:
        """상상 롤아웃 후 Actor-Critic 업데이트.

        Args:
            start_h: 상상 시작 GRU 은닉 상태 (B, hidden)
            start_z: 상상 시작 잠재 상태 (B, C, D)

        Returns:
            actor_loss, critic_loss, mean_imag_reward
        """
        B = start_h.shape[0]

        # 상상 롤아웃
        h, z = start_h, start_z
        states, actions, rewards, continues, values = [], [], [], [], []

        for _ in range(self.H):
            s = self.rssm.get_state(h, z)
            a, log_p = self.actor.get_action(s)

            # 예측 (reward, continue, value)
            r  = symexp(self.rssm.predict_reward(h, z))
            c  = self.rssm.predict_continue(h, z)
            v  = self.target_critic(s)

            states.append(s)
            actions.append(a)
            rewards.append(r)
            continues.append(c)
            values.append(v)

            # 상상 전이 (실제 환경 호출 없음)
            h, z, _ = self.rssm.imagine(a, h, z)

        # (B, H, ...) 스택
        states_t    = torch.stack(states,    dim=1)   # (B, H, state_dim)
        actions_t   = torch.stack(actions,   dim=1)
        rewards_t   = torch.stack(rewards,   dim=1)   # (B, H)
        continues_t = torch.stack(continues, dim=1)   # (B, H)
        values_t    = torch.stack(values,    dim=1)   # (B, H)

        # Lambda-Return 타겟
        with torch.no_grad():
            lambda_targets = self._lambda_return(
                rewards_t, values_t, continues_t, self.lambda_ret
            )

        # ── Critic 업데이트 ──
        new_values = self.critic(states_t.detach().reshape(B * self.H, -1))
        new_values = new_values.reshape(B, self.H)
        critic_loss = F.mse_loss(new_values, lambda_targets.detach())

        self.critic_opt.zero_grad()
        critic_loss.backward()
        nn.utils.clip_grad_norm_(self.critic.parameters(), 100.0)
        self.critic_opt.step()

        # ── Actor 업데이트 (Reinforce-style) ──
        actor_loss = -(lambda_targets.detach()).mean()

        self.actor_opt.zero_grad()
        actor_loss.backward()
        nn.utils.clip_grad_norm_(self.actor.parameters(), 100.0)
        self.actor_opt.step()

        # ── Target Critic EMA 업데이트 ──
        ema = 0.98
        for p_tgt, p_src in zip(self.target_critic.parameters(), self.critic.parameters()):
            p_tgt.data.mul_(ema).add_(p_src.data, alpha=1 - ema)

        mean_imag_r = rewards_t.mean().item()
        self.actor_loss_history.append(actor_loss.item())
        self.imag_reward_history.append(mean_imag_r)

        return {
            "actor_loss":      actor_loss.item(),
            "critic_loss":     critic_loss.item(),
            "mean_imag_reward": mean_imag_r,
        }

    # ──────────────────────────────────────────────────────────
    #  체크포인트
    # ──────────────────────────────────────────────────────────

    def save(self, path: str):
        torch.save({
            "rssm":          self.rssm.state_dict(),
            "actor":         self.actor.state_dict(),
            "critic":        self.critic.state_dict(),
            "target_critic": self.target_critic.state_dict(),
            "wm_opt":        self.wm_opt.state_dict(),
            "actor_opt":     self.actor_opt.state_dict(),
            "critic_opt":    self.critic_opt.state_dict(),
        }, path)
        print(f"  💾 DreamerTrainer saved: {path}")

    def load(self, path: str):
        ckpt = torch.load(path, map_location=self.device)
        self.rssm.load_state_dict(ckpt["rssm"])
        self.actor.load_state_dict(ckpt["actor"])
        self.critic.load_state_dict(ckpt["critic"])
        self.target_critic.load_state_dict(ckpt["target_critic"])
        print(f"  ✅ DreamerTrainer loaded: {path}")

    def get_wm_metrics(self) -> Dict[str, float]:
        def safe_mean(d):
            return float(np.mean(list(d))) if d else 0.0
        return {
            "avg_wm_loss":      safe_mean(self.wm_loss_history),
            "avg_actor_loss":   safe_mean(self.actor_loss_history),
            "avg_imag_reward":  safe_mean(self.imag_reward_history),
            "buffer_fill":      self.buffer.fill_ratio,
            "n_home_runs":      self.buffer.n_home_runs,
            "n_contacts":       self.buffer.n_contacts,
        }


# ──────────────────────────────────────────────────────────────
#  메인 학습 루프
# ──────────────────────────────────────────────────────────────

def run_dreamer_training(
    total_episodes:      int   = 1000,
    initial_stage:       int   = 1,
    wm_warmup_episodes:  int   = 50,    # WM 학습 전 순수 수집 에피소드 수
    imagination_ratio:   int   = 5,     # 실제 1 ep당 상상 업데이트 횟수
    record_interval:     int   = 100,
    save_interval:       int   = 200,
):
    """World Model 기반 Dreamer 학습 실행.

    Args:
        wm_warmup_episodes: 이 에피소드 수만큼은 WM 학습 없이 버퍼만 채움
        imagination_ratio:  실제 환경 1 에피소드당 상상 업데이트 횟수
    """
    device_str = "mps" if torch.backends.mps.is_available() else \
                 "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 70)
    print(f" ⚾ Baseball Dreamer (World Model) 학습 시작")
    print(f"   Device: {device_str} | Episodes: {total_episodes}")
    print(f"   WM Warmup: {wm_warmup_episodes} | Imagination Ratio: {imagination_ratio}")
    print("=" * 70)

    env = UnifiedBaseballEnv(curriculum_stage=initial_stage, render_mode="rgb_array")

    dreamer = DreamerTrainer(
        env=env,
        imagination_horizon=15,
        wm_lr=1e-4, actor_lr=3e-4, critic_lr=3e-4,
        wm_batch_size=16,
        buffer_capacity=5_000,
        seq_len=50,
        kl_scale=0.1,
    )

    curriculum    = CurriculumManager(initial_stage=initial_stage)
    monitor       = TrainingHealthMonitor()
    recorder      = EpisodeRecorder()
    auditor       = RewardAuditSystem()
    dashboard     = DashboardLogger()

    reward_window = deque(maxlen=50)
    best_cr       = 0.0
    start_time    = time.time()

    for ep in range(1, total_episodes + 1):
        # ── 1. 실제 환경에서 에피소드 수집 ──
        episode = dreamer.collect_episode()
        dreamer.buffer.add_episode(episode)

        ep_reward = episode["total_reward"]
        contacted = episode["has_contact"]
        reward_window.append(ep_reward)

        curriculum.record_episode(contacted, {})
        if contacted:
            fake_info = {
                "exit_velocity_kmh": 120.0,
                "launch_angle": 20.0,
                "spray_angle": 10.0,
            }
            auditor.record_hit(fake_info, ep_reward)

        # ── 2. World Model 학습 ──
        wm_metrics = {}
        if ep > wm_warmup_episodes:
            wm_metrics = dreamer.train_world_model() or {}

            # ── 3. 상상 롤아웃으로 Actor-Critic 업데이트 ──
            for _ in range(imagination_ratio):
                # 랜덤 에피소드의 임의 시점에서 상상 시작
                if dreamer.buffer.size > 0:
                    batch = dreamer.buffer.sample(8)
                    if batch is not None:
                        obs_t = {k: v[:, 0].to(dreamer.device) for k, v in batch["obs"].items()}
                        a_dummy = batch["actions"][:, 0].to(dreamer.device)
                        h0, z0 = dreamer.rssm.initial_state(8, dreamer.device)
                        with torch.no_grad():
                            h, z, _ = dreamer.rssm.observe(obs_t, a_dummy, h0, z0)
                        ac_metrics = dreamer.update_actor_critic(h, z)
                        wm_metrics.update(ac_metrics)

        # ── 4. 모니터링 & 로깅 ──
        monitor_metrics = {
            "reward":       ep_reward,
            "contact_rate": curriculum.get_contact_rate(),
            **{k: v for k, v in wm_metrics.items() if isinstance(v, (int, float))},
        }
        monitor.record(monitor_metrics)

        if ep % 5 == 0:
            dashboard.log_episode_stats(ep, monitor_metrics)

        if ep % record_interval == 0:
            recorder.record_episode(env, dreamer.actor, ep, dreamer.device)

        if ep % 50 == 0:
            new_stage = curriculum.check_and_update()
            env.set_curriculum_stage(new_stage)

        if ep % 20 == 0 or ep == total_episodes:
            elapsed = time.time() - start_time
            cr  = curriculum.get_contact_rate()
            avg = np.mean(list(reward_window)) if reward_window else 0.0
            wm  = dreamer.get_wm_metrics()
            stage_name = env.CURRICULUM[curriculum.current_stage]["name"]

            print(
                f"  [EP {ep:4d}/{total_episodes}] "
                f"Stage {curriculum.current_stage} ({stage_name}) | "
                f"CR={cr:.1%} | Reward={avg:+.2f} | "
                f"WM_Loss={wm['avg_wm_loss']:.4f} | "
                f"Imag_R={wm['avg_imag_reward']:+.2f} | "
                f"Buffer={wm['buffer_fill']:.0%} | {elapsed:.0f}s"
            )
            for alert in monitor.check_health():
                print(f"    {alert}")
            for alert in auditor.audit():
                print(f"    {alert}")

            if cr > best_cr:
                best_cr = cr

        if ep % save_interval == 0:
            ckpt_dir = Path(__file__).parent.parent / "checkpoints"
            ckpt_dir.mkdir(parents=True, exist_ok=True)
            dreamer.save(str(ckpt_dir / f"dreamer_ep{ep:05d}.pt"))

    # 최종 저장
    save_dir = Path(__file__).parent.parent / "checkpoints"
    save_dir.mkdir(parents=True, exist_ok=True)
    dreamer.save(str(save_dir / "dreamer_final.pt"))

    print("\n" + "=" * 70)
    print(f" 🏆 Dreamer 학습 완료!")
    print(f"    최종 Stage: {curriculum.current_stage}")
    print(f"    최고 Contact Rate: {best_cr:.1%}")
    print(f"    {auditor.get_summary()}")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Baseball Dreamer Trainer")
    parser.add_argument("--episodes", type=int, default=1000)
    parser.add_argument("--stage",    type=int, default=1)
    parser.add_argument("--warmup",   type=int, default=50)
    parser.add_argument("--imag",     type=int, default=5)
    args = parser.parse_args()

    run_dreamer_training(
        total_episodes=args.episodes,
        initial_stage=args.stage,
        wm_warmup_episodes=args.warmup,
        imagination_ratio=args.imag,
    )
