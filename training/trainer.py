"""
trainer.py — Self-Play PPO 학습 엔진

투수/타자 에이전트를 Self-Play 방식으로 교대 학습합니다.
League Training 기반 적대적 학습 + Curriculum 난이도 조절.

학습 흐름:
    1. Warm-up: Scripted Bot 상대로 기초 학습
    2. Self-Play: 현재 정책 vs 과거 체크포인트
    3. League: 최강 체크포인트 풀에서 랜덤 상대 선택
"""

import os
import json
import copy
import time
import numpy as np
from pathlib import Path
from collections import deque
from typing import Optional, Dict, List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim

from training.networks import PitcherAgent, BatterAgent, get_device
from training.replay_buffer import (
    PrioritizedReplayBuffer,
    Transition,
    transitions_to_batch,
)
from envs.baseball_game_env import BaseballGameEnv
from simulator.dashboard import save_pitch_data, save_training_metrics


# ──────────────────────────────────────────────────────────────
#  학습 설정
# ──────────────────────────────────────────────────────────────

class TrainingConfig:
    """학습 하이퍼파라미터."""

    # PPO
    lr: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_eps: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5

    # 배치
    batch_size: int = 64
    n_epochs: int = 4           # 미니배치 에폭
    n_steps_per_update: int = 128  # 업데이트 당 스텝 수

    # Self-Play
    opponent_pool_size: int = 10
    snapshot_interval: int = 50    # 체크포인트 스냅샷 간격 (에피소드)
    opponent_sample_latest_prob: float = 0.7  # 최신 체크포인트 선택 확률

    # Curriculum
    warmup_episodes: int = 100
    curriculum_phases: int = 3

    # Logging
    log_interval: int = 10
    save_interval: int = 100
    checkpoint_dir: str = "checkpoints"
    data_dir: str = "data"


# ──────────────────────────────────────────────────────────────
#  Scripted Bot (Warm-up 상대)
# ──────────────────────────────────────────────────────────────

class ScriptedPitcherBot:
    """규칙 기반 투수 봇 (Warm-up 학습용).

    직구 위주로 스트라이크존 중앙에 던집니다.
    """

    def __init__(self, difficulty: float = 0.5):
        """
        Args:
            difficulty: 난이도 (0=쉬움, 1=어려움)
        """
        self.difficulty = difficulty

    def get_action(self, obs: np.ndarray) -> np.ndarray:
        """규칙 기반 투구 액션을 생성합니다.

        Args:
            obs: 투수 관찰 벡터

        Returns:
            (5,) 액션 벡터
        """
        noise_scale = 0.3 * (1.0 - self.difficulty)

        # 기본: 중앙 직구
        v_release = 0.3 + 0.3 * self.difficulty  # 속도
        target_x = np.random.normal(0.0, noise_scale)  # 좌우
        target_z = np.random.normal(0.0, noise_scale)  # 상하
        spin_rate = 0.2  # 중간 스핀
        spin_axis = np.random.uniform(-0.3, 0.3)  # 약간의 변화

        action = np.array([v_release, target_x, target_z, spin_rate, spin_axis],
                         dtype=np.float32)
        return np.clip(action, -1.0, 1.0)


class ScriptedBatterBot:
    """규칙 기반 타자 봇 (Warm-up 학습용).

    스트라이크존에 오는 공에 대해 단순 스윙합니다.
    """

    def __init__(self, difficulty: float = 0.5):
        self.difficulty = difficulty

    def get_action(self, obs: np.ndarray) -> np.ndarray:
        """규칙 기반 스윙 액션을 생성합니다.

        Args:
            obs: 타자 관찰 벡터 (13,)

        Returns:
            (4,) 액션 벡터
        """
        ball_pos = obs[:3]
        ball_vel = obs[3:6]
        time_to_plate = obs[12] if len(obs) > 12 else 0.5

        noise_scale = 0.3 * (1.0 - self.difficulty)

        # 간단한 판정: 공이 스트라이크존 근처로 향하면 스윙
        predicted_x = ball_pos[0] + ball_vel[0] * time_to_plate
        predicted_z = ball_pos[2] + ball_vel[2] * time_to_plate

        in_zone = (-0.3 <= predicted_x <= 0.3 and 0.3 <= predicted_z <= 1.2)

        if in_zone:
            trigger = 0.5 + np.random.normal(0, noise_scale)
            yaw = np.random.normal(0.3, noise_scale)    # 투수 방향으로 스윙
            pitch = np.random.normal(0.0, noise_scale)
            height = predicted_z / 1.3 * 2 - 1  # 높이 매핑
        else:
            trigger = -0.5  # 스윙 안 함
            yaw = 0.0
            pitch = 0.0
            height = 0.0

        action = np.array([trigger, yaw, pitch, height], dtype=np.float32)
        return np.clip(action, -1.0, 1.0)


# ──────────────────────────────────────────────────────────────
#  PPO 업데이트 로직
# ──────────────────────────────────────────────────────────────

class PPOUpdater:
    """PPO 알고리즘 업데이트를 수행합니다."""

    def __init__(self, config: TrainingConfig, device: torch.device):
        self.config = config
        self.device = device

    def compute_gae(
        self,
        rewards: np.ndarray,
        values: np.ndarray,
        next_value: float,
        dones: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generalized Advantage Estimation (GAE)를 계산합니다.

        Args:
            rewards: (T,) 보상 배열
            values: (T,) 가치 추정 배열
            next_value: 마지막 다음 상태의 가치
            dones: (T,) 종료 플래그

        Returns:
            (advantages, returns)
        """
        T = len(rewards)
        advantages = np.zeros(T, dtype=np.float32)
        gae = 0.0

        for t in reversed(range(T)):
            if t == T - 1:
                next_val = next_value
            else:
                next_val = values[t + 1]

            delta = rewards[t] + self.config.gamma * next_val * (1 - dones[t]) - values[t]
            gae = delta + self.config.gamma * self.config.gae_lambda * (1 - dones[t]) * gae
            advantages[t] = gae

        returns = advantages + values
        return advantages, returns

    def ppo_update(
        self,
        agent: nn.Module,
        optimizer: optim.Optimizer,
        obs: torch.Tensor,
        actions: torch.Tensor,
        old_log_probs: torch.Tensor,
        advantages: torch.Tensor,
        returns: torch.Tensor,
        is_batter: bool = False,
    ) -> dict:
        """PPO Clipped Objective 업데이트를 수행합니다.

        Args:
            agent: PitcherAgent 또는 BatterAgent
            optimizer: Adam 옵티마이저
            obs: 관찰 텐서
            actions: 액션 텐서
            old_log_probs: 이전 로그 확률
            advantages: GAE 어드밴티지
            returns: 타겟 리턴
            is_batter: 타자 에이전트 여부

        Returns:
            학습 메트릭 딕셔너리
        """
        cfg = self.config
        total_policy_loss = 0
        total_value_loss = 0
        total_entropy = 0
        n_updates = 0

        # 어드밴티지 정규화
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        dataset_size = obs.size(0)
        indices = np.arange(dataset_size)

        for epoch in range(cfg.n_epochs):
            np.random.shuffle(indices)

            for start in range(0, dataset_size, cfg.batch_size):
                end = min(start + cfg.batch_size, dataset_size)
                batch_idx = indices[start:end]

                b_obs = obs[batch_idx]
                b_actions = actions[batch_idx]
                b_old_log_probs = old_log_probs[batch_idx]
                b_advantages = advantages[batch_idx]
                b_returns = returns[batch_idx]

                # 현재 정책으로 재평가
                new_log_probs, entropy, values = agent.evaluate(b_obs, b_actions)

                # PPO Clipped 목적함수
                ratio = torch.exp(new_log_probs - b_old_log_probs)
                surr1 = ratio * b_advantages
                surr2 = torch.clamp(ratio, 1 - cfg.clip_eps, 1 + cfg.clip_eps) * b_advantages
                policy_loss = -torch.min(surr1, surr2).mean()

                # Value 손실
                value_loss = nn.functional.mse_loss(values, b_returns)

                # Entropy 보너스
                entropy_loss = -entropy.mean()

                # 총 손실
                loss = (
                    policy_loss
                    + cfg.value_coef * value_loss
                    + cfg.entropy_coef * entropy_loss
                )

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)
                optimizer.step()

                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy += (-entropy_loss).item()
                n_updates += 1

        return {
            'policy_loss': total_policy_loss / max(n_updates, 1),
            'value_loss': total_value_loss / max(n_updates, 1),
            'entropy': total_entropy / max(n_updates, 1),
        }


# ──────────────────────────────────────────────────────────────
#  Self-Play 학습 엔진
# ──────────────────────────────────────────────────────────────

class SelfPlayTrainer:
    """Self-Play League Training 엔진.

    투수/타자 에이전트를 교대로 학습시키며,
    과거 체크포인트 풀에서 상대를 선택합니다.
    """

    def __init__(
        self,
        config: Optional[TrainingConfig] = None,
        max_episodes: int = 10000,
    ):
        self.config = config or TrainingConfig()
        self.max_episodes = max_episodes
        self.device = get_device()

        # 에이전트 초기화
        self.pitcher_agent = PitcherAgent().to(self.device)
        self.batter_agent = BatterAgent().to(self.device)

        # 옵티마이저
        self.pitcher_optimizer = optim.Adam(
            self.pitcher_agent.parameters(), lr=self.config.lr
        )
        self.batter_optimizer = optim.Adam(
            self.batter_agent.parameters(), lr=self.config.lr
        )

        # PPO 업데이터
        self.updater = PPOUpdater(self.config, self.device)

        # 상대 풀 (과거 체크포인트)
        self.pitcher_pool: List[dict] = []
        self.batter_pool: List[dict] = []

        # Scripted 봇 (Warm-up)
        self.scripted_pitcher = ScriptedPitcherBot(difficulty=0.3)
        self.scripted_batter = ScriptedBatterBot(difficulty=0.3)

        # 리플레이 버퍼
        self.replay_buffer = PrioritizedReplayBuffer()

        # 환경
        self.env = BaseballGameEnv()

        # 통계
        self.episode_stats = deque(maxlen=100)
        self.pitcher_wins = 0
        self.batter_wins = 0

        # 체크포인트 디렉토리
        self.checkpoint_dir = Path(self.config.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = Path(self.config.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_opponent_action(
        self,
        agent_type: str,
        obs: np.ndarray,
        episode: int,
    ) -> np.ndarray:
        """상대 에이전트의 액션을 생성합니다.

        Warm-up 단계에서는 Scripted Bot, 이후에는 과거 체크포인트를 사용합니다.

        Args:
            agent_type: 'pitcher' 또는 'batter'
            obs: 관찰 벡터
            episode: 현재 에피소드 번호

        Returns:
            액션 벡터
        """
        # Warm-up: Scripted Bot 사용
        if episode < self.config.warmup_episodes:
            if agent_type == 'pitcher':
                return self.scripted_pitcher.get_action(obs)
            else:
                return self.scripted_batter.get_action(obs)

        # Self-Play: 과거 체크포인트에서 샘플
        pool = self.pitcher_pool if agent_type == 'pitcher' else self.batter_pool

        if not pool:
            # 풀이 비면 현재 정책 사용
            if agent_type == 'pitcher':
                return self.scripted_pitcher.get_action(obs)
            else:
                return self.scripted_batter.get_action(obs)

        # 최신 체크포인트 우선 선택
        if np.random.random() < self.config.opponent_sample_latest_prob:
            checkpoint = pool[-1]
        else:
            checkpoint = pool[np.random.randint(len(pool))]

        # 체크포인트에서 액션 생성
        obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)

        if agent_type == 'pitcher':
            temp_agent = PitcherAgent().to(self.device)
            temp_agent.load_state_dict(checkpoint)
            with torch.no_grad():
                action, _, _, _ = temp_agent.get_action_and_value(
                    obs_tensor, deterministic=True
                )
        else:
            temp_agent = BatterAgent().to(self.device)
            temp_agent.load_state_dict(checkpoint)
            with torch.no_grad():
                action, _, _, _, _ = temp_agent.get_action_and_value(
                    obs_tensor, deterministic=True
                )

        return action.cpu().numpy().squeeze()

    def _snapshot_agent(self, agent_type: str):
        """현재 에이전트를 체크포인트 풀에 추가합니다."""
        if agent_type == 'pitcher':
            state_dict = copy.deepcopy(self.pitcher_agent.state_dict())
            self.pitcher_pool.append(state_dict)
            if len(self.pitcher_pool) > self.config.opponent_pool_size:
                self.pitcher_pool.pop(0)
        else:
            state_dict = copy.deepcopy(self.batter_agent.state_dict())
            self.batter_pool.append(state_dict)
            if len(self.batter_pool) > self.config.opponent_pool_size:
                self.batter_pool.pop(0)

    def _collect_episode(self, episode: int) -> dict:
        """한 에피소드를 실행하고 경험을 수집합니다.

        Args:
            episode: 에피소드 번호

        Returns:
            에피소드 통계 딕셔너리
        """
        obs, info = self.env.reset()
        pitcher_obs = obs['pitcher']
        batter_obs = obs['batter']

        # 수집 버퍼
        pitcher_buffer = {
            'obs': [], 'actions': [], 'log_probs': [], 'rewards': [],
            'values': [], 'dones': [],
        }
        batter_buffer = {
            'obs': [], 'actions': [], 'log_probs': [], 'rewards': [],
            'values': [], 'dones': [],
        }

        episode_reward_pitcher = 0.0
        episode_reward_batter = 0.0
        terminated = False
        truncated = False
        n_pitches = 0
        outcomes = []

        while not terminated and not truncated:
            # ── 투수 액션 ──
            p_obs_tensor = torch.FloatTensor(pitcher_obs).unsqueeze(0).to(self.device)
            with torch.no_grad():
                p_action, p_log_prob, _, p_value = \
                    self.pitcher_agent.get_action_and_value(p_obs_tensor)

            p_action_np = p_action.cpu().numpy().squeeze()
            p_log_prob_val = p_log_prob.cpu().item()
            p_value_val = p_value.cpu().item()

            # ── 타자 액션 ──
            b_obs_tensor = torch.FloatTensor(batter_obs).unsqueeze(0).to(self.device)
            with torch.no_grad():
                b_action, b_log_prob, _, b_value, _ = \
                    self.batter_agent.get_action_and_value(b_obs_tensor)

            b_action_np = b_action.cpu().numpy().squeeze()
            b_log_prob_val = b_log_prob.cpu().item()
            b_value_val = b_value.cpu().item()

            # ── 환경 스텝 ──
            combined_action = {
                'pitcher': p_action_np,
                'batter': b_action_np,
            }

            next_obs, rewards, terminated, truncated, info = self.env.step(combined_action)

            # 버퍼에 저장
            pitcher_buffer['obs'].append(pitcher_obs)
            pitcher_buffer['actions'].append(p_action_np)
            pitcher_buffer['log_probs'].append(p_log_prob_val)
            pitcher_buffer['rewards'].append(rewards['pitcher'])
            pitcher_buffer['values'].append(p_value_val)
            pitcher_buffer['dones'].append(float(terminated or truncated))

            batter_buffer['obs'].append(batter_obs)
            batter_buffer['actions'].append(b_action_np)
            batter_buffer['log_probs'].append(b_log_prob_val)
            batter_buffer['rewards'].append(rewards['batter'])
            batter_buffer['values'].append(b_value_val)
            batter_buffer['dones'].append(float(terminated or truncated))

            # 리플레이 버퍼에 저장
            transition = Transition(
                pitcher_obs=pitcher_obs,
                pitcher_action=p_action_np,
                batter_obs=batter_obs,
                batter_action=b_action_np,
                pitcher_reward=rewards['pitcher'],
                batter_reward=rewards['batter'],
                next_pitcher_obs=next_obs['pitcher'],
                next_batter_obs=next_obs['batter'],
                done=terminated or truncated,
                info=info.get('pitch_data', {}),
            )
            self.replay_buffer.add(transition)

            # 대시보드 데이터 전송
            if 'pitch_data' in info:
                save_pitch_data(info['pitch_data'])

            episode_reward_pitcher += rewards['pitcher']
            episode_reward_batter += rewards['batter']
            n_pitches += 1

            outcome = info.get('pitch_outcome', {}).get('reward_key', '')
            outcomes.append(outcome)

            # 다음 관찰
            pitcher_obs = next_obs['pitcher']
            batter_obs = next_obs['batter']

        # 승패 판정
        if episode_reward_pitcher > episode_reward_batter:
            self.pitcher_wins += 1
            winner = 'pitcher'
        else:
            self.batter_wins += 1
            winner = 'batter'

        # 통계
        stats = {
            'episode': episode,
            'pitcher_reward': episode_reward_pitcher,
            'batter_reward': episode_reward_batter,
            'n_pitches': n_pitches,
            'winner': winner,
            'outcomes': outcomes,
            'has_home_run': 'home_run' in outcomes,
            'has_strikeout': outcomes.count('swinging_strike') + \
                             outcomes.count('called_strike') >= 3,
        }
        self.episode_stats.append(stats)

        return {
            'stats': stats,
            'pitcher_buffer': pitcher_buffer,
            'batter_buffer': batter_buffer,
        }

    def _update_agent(
        self,
        agent_type: str,
        buffer: dict,
    ) -> dict:
        """수집된 경험으로 에이전트를 업데이트합니다.

        Args:
            agent_type: 'pitcher' 또는 'batter'
            buffer: 경험 버퍼

        Returns:
            학습 메트릭
        """
        if not buffer['obs']:
            return {}

        agent = self.pitcher_agent if agent_type == 'pitcher' else self.batter_agent
        optimizer = self.pitcher_optimizer if agent_type == 'pitcher' else self.batter_optimizer

        obs = torch.FloatTensor(np.array(buffer['obs'])).to(self.device)
        actions = torch.FloatTensor(np.array(buffer['actions'])).to(self.device)
        old_log_probs = torch.FloatTensor(np.array(buffer['log_probs'])).to(self.device)
        rewards = np.array(buffer['rewards'])
        values = np.array(buffer['values'])
        dones = np.array(buffer['dones'])

        # GAE 계산
        with torch.no_grad():
            if agent_type == 'pitcher':
                _, _, _, next_value = agent.get_action_and_value(obs[-1:])
            else:
                _, _, _, next_value, _ = agent.get_action_and_value(obs[-1:])
            next_value = next_value.cpu().item()

        advantages, returns = self.updater.compute_gae(
            rewards, values, next_value, dones
        )

        advantages = torch.FloatTensor(advantages).to(self.device)
        returns = torch.FloatTensor(returns).to(self.device)

        # PPO 업데이트
        metrics = self.updater.ppo_update(
            agent, optimizer, obs, actions, old_log_probs,
            advantages, returns, is_batter=(agent_type == 'batter'),
        )

        return metrics

    def train(self):
        """메인 학습 루프를 실행합니다."""
        print("⚾ Baseball RL Self-Play Training 시작!")
        print(f"   Device: {self.device}")
        print(f"   Max Episodes: {self.max_episodes}")
        print(f"   Warmup: {self.config.warmup_episodes} episodes")
        print(f"   Checkpoint Dir: {self.checkpoint_dir}")
        print("-" * 60)

        start_time = time.time()

        for episode in range(1, self.max_episodes + 1):
            # ── 에피소드 수집 ──
            result = self._collect_episode(episode)
            stats = result['stats']

            # ── 에이전트 업데이트 ──
            p_metrics = self._update_agent('pitcher', result['pitcher_buffer'])
            b_metrics = self._update_agent('batter', result['batter_buffer'])

            # ── 체크포인트 스냅샷 ──
            if episode % self.config.snapshot_interval == 0:
                self._snapshot_agent('pitcher')
                self._snapshot_agent('batter')

            # ── 로깅 ──
            if episode % self.config.log_interval == 0:
                self._log_progress(episode, stats, p_metrics, b_metrics, start_time)

            # ── 모델 저장 ──
            if episode % self.config.save_interval == 0:
                self._save_checkpoint(episode)

        print("\n" + "=" * 60)
        print("⚾ 학습 완료!")
        self._save_checkpoint(self.max_episodes)

    def _log_progress(
        self,
        episode: int,
        stats: dict,
        p_metrics: dict,
        b_metrics: dict,
        start_time: float,
    ):
        """학습 진행 상황을 로깅합니다."""
        elapsed = time.time() - start_time
        total_games = self.pitcher_wins + self.batter_wins
        p_wr = self.pitcher_wins / max(total_games, 1)
        b_wr = self.batter_wins / max(total_games, 1)

        # 최근 100 에피소드 통계
        recent = list(self.episode_stats)
        avg_p_reward = np.mean([s['pitcher_reward'] for s in recent])
        avg_b_reward = np.mean([s['batter_reward'] for s in recent])
        hr_rate = np.mean([s['has_home_run'] for s in recent])
        k_rate = np.mean([s['has_strikeout'] for s in recent])

        print(
            f"[EP {episode:5d}] "
            f"WR: P={p_wr:.2f}/B={b_wr:.2f} | "
            f"Reward: P={avg_p_reward:+.2f}/B={avg_b_reward:+.2f} | "
            f"HR={hr_rate:.1%} K={k_rate:.1%} | "
            f"Buffer={self.replay_buffer.fill_ratio:.1%} | "
            f"{elapsed:.0f}s"
        )

        # 대시보드 메트릭 전송
        metrics = {
            'episode': episode,
            'pitcher_win_rate': p_wr,
            'batter_win_rate': b_wr,
            'pitcher_avg_reward': float(avg_p_reward),
            'batter_avg_reward': float(avg_b_reward),
            'home_run_rate': float(hr_rate),
            'strikeout_rate': float(k_rate),
            'buffer_fill_ratio': self.replay_buffer.fill_ratio,
            'pitcher_policy_loss': p_metrics.get('policy_loss', 0),
            'batter_policy_loss': b_metrics.get('policy_loss', 0),
            'pitcher_entropy': p_metrics.get('entropy', 0),
            'batter_entropy': b_metrics.get('entropy', 0),
        }
        save_training_metrics(metrics)

    def _save_checkpoint(self, episode: int):
        """모델 체크포인트를 저장합니다."""
        path = self.checkpoint_dir / f"checkpoint_ep{episode}.pt"
        torch.save({
            'episode': episode,
            'pitcher_state_dict': self.pitcher_agent.state_dict(),
            'batter_state_dict': self.batter_agent.state_dict(),
            'pitcher_optimizer': self.pitcher_optimizer.state_dict(),
            'batter_optimizer': self.batter_optimizer.state_dict(),
            'pitcher_wins': self.pitcher_wins,
            'batter_wins': self.batter_wins,
        }, path)
        print(f"   💾 Checkpoint saved: {path}")

    def load_checkpoint(self, path: str):
        """체크포인트에서 모델을 로드합니다."""
        checkpoint = torch.load(path, map_location=self.device)
        self.pitcher_agent.load_state_dict(checkpoint['pitcher_state_dict'])
        self.batter_agent.load_state_dict(checkpoint['batter_state_dict'])
        self.pitcher_optimizer.load_state_dict(checkpoint['pitcher_optimizer'])
        self.batter_optimizer.load_state_dict(checkpoint['batter_optimizer'])
        self.pitcher_wins = checkpoint.get('pitcher_wins', 0)
        self.batter_wins = checkpoint.get('batter_wins', 0)
        print(f"   ✅ Checkpoint loaded: {path}")


# ──────────────────────────────────────────────────────────────
#  메인 실행
# ──────────────────────────────────────────────────────────────

def main():
    """학습을 시작합니다."""
    import argparse

    parser = argparse.ArgumentParser(description='Baseball RL Self-Play Trainer')
    parser.add_argument('--episodes', type=int, default=1000, help='학습 에피소드 수')
    parser.add_argument('--lr', type=float, default=3e-4, help='학습률')
    parser.add_argument('--warmup', type=int, default=100, help='Warm-up 에피소드 수')
    parser.add_argument('--resume', type=str, default=None, help='체크포인트 경로')
    args = parser.parse_args()

    config = TrainingConfig()
    config.lr = args.lr
    config.warmup_episodes = args.warmup

    trainer = SelfPlayTrainer(config=config, max_episodes=args.episodes)

    if args.resume:
        trainer.load_checkpoint(args.resume)

    trainer.train()


if __name__ == '__main__':
    main()
