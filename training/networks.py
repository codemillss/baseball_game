"""
networks.py — PyTorch Actor-Critic 신경망

투수(MLP)와 타자(LSTM) 정책 네트워크 및 공유 Value 네트워크를 정의합니다.

Architecture:
    PitcherPolicy: MLP(6 → 256 → 256 → 128 → 5) + Tanh output
    BatterPolicy:  LSTM(13 → 128h → 128 → 4) + Tanh output
    ValueNetwork:  MLP(obs_dim → 256 → 256 → 1)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Normal
import numpy as np
from typing import Tuple, Optional


# ──────────────────────────────────────────────────────────────
#  공통 유틸리티
# ──────────────────────────────────────────────────────────────

def get_device() -> torch.device:
    """사용 가능한 최적 디바이스를 반환합니다."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def layer_init(layer: nn.Linear, std: float = np.sqrt(2), bias_const: float = 0.0):
    """PPO 스타일 직교 초기화."""
    nn.init.orthogonal_(layer.weight, std)
    nn.init.constant_(layer.bias, bias_const)
    return layer


# ──────────────────────────────────────────────────────────────
#  투수 정책 네트워크 (MLP)
# ──────────────────────────────────────────────────────────────

class PitcherPolicy(nn.Module):
    """투수 정책 네트워크.

    MLP 구조: 카운트와 이전 투구 이력으로 결정하므로 순차 구조 불필요.
    SiLU 활성화 + LayerNorm 적용.

    Input:  obs_dim (6) = [strikes, balls, prev_result, prev_plate_x, prev_plate_z, stance]
    Output: action_dim (5) = [v_release, θ_x, θ_z, ω_spin, a_axis]
    """

    def __init__(self, obs_dim: int = 6, action_dim: int = 5, hidden_dim: int = 256):
        super().__init__()

        self.actor_backbone = nn.Sequential(
            layer_init(nn.Linear(obs_dim, hidden_dim)),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
            layer_init(nn.Linear(hidden_dim, hidden_dim)),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
            layer_init(nn.Linear(hidden_dim, hidden_dim // 2)),
            nn.LayerNorm(hidden_dim // 2),
            nn.SiLU(),
        )

        # 평균과 로그 분산을 분리 출력
        self.mean_head = layer_init(nn.Linear(hidden_dim // 2, action_dim), std=0.01)
        self.log_std = nn.Parameter(torch.zeros(action_dim))

    def forward(self, obs: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """순전파: 관찰 → (평균, 로그 표준편차)

        Args:
            obs: (batch, obs_dim) 관찰 텐서

        Returns:
            (mean, log_std): 액션 분포의 평균과 로그 표준편차
        """
        features = self.actor_backbone(obs)
        mean = torch.tanh(self.mean_head(features))  # [-1, 1] 범위
        log_std = self.log_std.expand_as(mean)
        return mean, log_std

    def get_action(
        self,
        obs: torch.Tensor,
        deterministic: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """액션 샘플링 및 로그 확률 계산.

        Args:
            obs: (batch, obs_dim) 관찰 텐서
            deterministic: True이면 평균값 반환 (평가 시)

        Returns:
            (action, log_prob, entropy)
        """
        mean, log_std = self.forward(obs)
        std = torch.exp(log_std.clamp(-5, 2))
        dist = Normal(mean, std)

        if deterministic:
            action = mean
        else:
            action = dist.rsample()  # Reparameterization trick

        action = torch.clamp(action, -1.0, 1.0)

        log_prob = dist.log_prob(action).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)

        return action, log_prob, entropy

    def evaluate_actions(
        self,
        obs: torch.Tensor,
        actions: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """주어진 액션의 로그 확률과 엔트로피를 평가합니다.

        PPO 업데이트 시 사용됩니다.

        Args:
            obs: (batch, obs_dim) 관찰 텐서
            actions: (batch, action_dim) 액션 텐서

        Returns:
            (log_prob, entropy)
        """
        mean, log_std = self.forward(obs)
        std = torch.exp(log_std.clamp(-5, 2))
        dist = Normal(mean, std)

        log_prob = dist.log_prob(actions).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)

        return log_prob, entropy


# ──────────────────────────────────────────────────────────────
#  타자 정책 네트워크 (LSTM)
# ──────────────────────────────────────────────────────────────

class BatterPolicy(nn.Module):
    """타자 정책 네트워크.

    LSTM 구조: 시시각각 변하는 공 궤적의 시계열 패턴을 포착합니다.
    공이 날아오는 동안 여러 프레임의 관찰을 순차적으로 처리합니다.

    Input:  obs_dim (13) = [ball_pos(3), ball_vel(3), bat_pos(3), bat_vel(3), time_to_plate]
    Output: action_dim (4) = [t_trigger, θ_yaw, θ_pitch, z_height]
    """

    def __init__(
        self,
        obs_dim: int = 13,
        action_dim: int = 4,
        hidden_dim: int = 128,
        num_layers: int = 2,
    ):
        super().__init__()

        # 입력 임베딩
        self.input_embed = nn.Sequential(
            layer_init(nn.Linear(obs_dim, hidden_dim)),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
        )

        # LSTM 코어
        self.lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.1 if num_layers > 1 else 0.0,
        )

        # 출력 헤드
        self.output_net = nn.Sequential(
            layer_init(nn.Linear(hidden_dim, hidden_dim)),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
        )

        self.mean_head = layer_init(nn.Linear(hidden_dim, action_dim), std=0.01)
        self.log_std = nn.Parameter(torch.zeros(action_dim))

        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

    def init_hidden(self, batch_size: int = 1, device: Optional[torch.device] = None):
        """LSTM 은닉 상태를 초기화합니다."""
        if device is None:
            device = next(self.parameters()).device
        h = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
        c = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
        return (h, c)

    def forward(
        self,
        obs_seq: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """순전파: 관찰 시퀀스 → (평균, 로그 표준편차, 은닉 상태)

        Args:
            obs_seq: (batch, seq_len, obs_dim) 관찰 시퀀스
                     또는 (batch, obs_dim) 단일 프레임
            hidden: LSTM 은닉 상태 (h, c) 또는 None

        Returns:
            (mean, log_std, hidden)
        """
        if obs_seq.dim() == 2:
            # 단일 프레임 → 시퀀스 차원 추가
            obs_seq = obs_seq.unsqueeze(1)

        batch_size = obs_seq.size(0)

        # 입력 임베딩
        embedded = self.input_embed(obs_seq)  # (batch, seq, hidden)

        # LSTM
        if hidden is None:
            hidden = self.init_hidden(batch_size, obs_seq.device)

        lstm_out, hidden = self.lstm(embedded, hidden)

        # 마지막 시퀀스의 출력 사용
        last_out = lstm_out[:, -1, :]  # (batch, hidden)

        # 출력 네트워크
        features = self.output_net(last_out)
        mean = torch.tanh(self.mean_head(features))
        log_std = self.log_std.expand_as(mean)

        return mean, log_std, hidden

    def get_action(
        self,
        obs_seq: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        deterministic: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, Tuple]:
        """액션 샘플링.

        Args:
            obs_seq: 관찰 시퀀스
            hidden: LSTM 은닉 상태
            deterministic: True이면 평균값 반환

        Returns:
            (action, log_prob, entropy, hidden)
        """
        mean, log_std, hidden = self.forward(obs_seq, hidden)
        std = torch.exp(log_std.clamp(-5, 2))
        dist = Normal(mean, std)

        if deterministic:
            action = mean
        else:
            action = dist.rsample()

        action = torch.clamp(action, -1.0, 1.0)

        log_prob = dist.log_prob(action).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)

        return action, log_prob, entropy, hidden

    def evaluate_actions(
        self,
        obs_seq: torch.Tensor,
        actions: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """주어진 액션 평가.

        Args:
            obs_seq: 관찰 시퀀스
            actions: 액션 텐서
            hidden: LSTM 은닉 상태

        Returns:
            (log_prob, entropy)
        """
        mean, log_std, _ = self.forward(obs_seq, hidden)
        std = torch.exp(log_std.clamp(-5, 2))
        dist = Normal(mean, std)

        log_prob = dist.log_prob(actions).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)

        return log_prob, entropy


# ──────────────────────────────────────────────────────────────
#  Value 네트워크 (Critic)
# ──────────────────────────────────────────────────────────────

class ValueNetwork(nn.Module):
    """상태 가치 함수 네트워크 (Critic).

    투수와 타자 각각의 가치 추정에 사용됩니다.
    MLP(obs_dim → 256 → 256 → 1)

    Args:
        obs_dim: 관찰 벡터 차원
    """

    def __init__(self, obs_dim: int, hidden_dim: int = 256):
        super().__init__()

        self.network = nn.Sequential(
            layer_init(nn.Linear(obs_dim, hidden_dim)),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
            layer_init(nn.Linear(hidden_dim, hidden_dim)),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
            layer_init(nn.Linear(hidden_dim, 1), std=1.0),
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        """상태 가치 추정.

        Args:
            obs: (batch, obs_dim) 관찰 텐서

        Returns:
            (batch, 1) 가치 추정값
        """
        return self.network(obs)


# ──────────────────────────────────────────────────────────────
#  통합 에이전트 래퍼
# ──────────────────────────────────────────────────────────────

class PitcherAgent(nn.Module):
    """투수 에이전트: Policy + Value 네트워크를 통합합니다."""

    def __init__(self, obs_dim: int = 6, action_dim: int = 5):
        super().__init__()
        self.policy = PitcherPolicy(obs_dim, action_dim)
        self.value = ValueNetwork(obs_dim)

    def get_action_and_value(
        self,
        obs: torch.Tensor,
        deterministic: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """액션 샘플링 + 가치 추정.

        Returns:
            (action, log_prob, entropy, value)
        """
        action, log_prob, entropy = self.policy.get_action(obs, deterministic)
        value = self.value(obs)
        return action, log_prob, entropy, value.squeeze(-1)

    def evaluate(
        self,
        obs: torch.Tensor,
        actions: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """저장된 경험의 액션을 재평가.

        Returns:
            (log_prob, entropy, value)
        """
        log_prob, entropy = self.policy.evaluate_actions(obs, actions)
        value = self.value(obs)
        return log_prob, entropy, value.squeeze(-1)


class BatterAgent(nn.Module):
    """타자 에이전트: Policy(LSTM) + Value 네트워크를 통합합니다."""

    def __init__(self, obs_dim: int = 13, action_dim: int = 4):
        super().__init__()
        self.policy = BatterPolicy(obs_dim, action_dim)
        self.value = ValueNetwork(obs_dim)

    def get_action_and_value(
        self,
        obs: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        deterministic: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, Tuple]:
        """액션 샘플링 + 가치 추정.

        Returns:
            (action, log_prob, entropy, value, hidden)
        """
        action, log_prob, entropy, hidden = self.policy.get_action(
            obs, hidden, deterministic
        )
        # Value는 마지막 관찰의 단일 프레임으로 추정
        if obs.dim() == 3:
            value_input = obs[:, -1, :]
        else:
            value_input = obs
        value = self.value(value_input)
        return action, log_prob, entropy, value.squeeze(-1), hidden

    def evaluate(
        self,
        obs: torch.Tensor,
        actions: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """저장된 경험의 액션을 재평가.

        Returns:
            (log_prob, entropy, value)
        """
        log_prob, entropy = self.policy.evaluate_actions(obs, actions, hidden)
        if obs.dim() == 3:
            value_input = obs[:, -1, :]
        else:
            value_input = obs
        value = self.value(value_input)
        return log_prob, entropy, value.squeeze(-1)
