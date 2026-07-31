"""
world_model.py — Baseball RSSM World Model (DreamerV3 경량화)

아키텍처:
    잠재 상태 s_t = (h_t, z_t)
      h_t : 결정론적(Deterministic) GRU 은닉 벡터  → 과거 정보 요약
      z_t : 확률론적(Stochastic) Categorical 벡터  → 불확실성 표현

학습 손실:
    L_WM = L_pred (재구성 + 보상 + continue 예측)
         + L_dyn  (Prior KL — dynamics 개선)
         + L_rep  (Posterior KL — representation 개선)

사용법:
    rssm = BaseballRSSM()
    h, z = rssm.initial_state(batch_size, device)

    # 실제 관찰이 있을 때 (학습 단계)
    h, z, post_logits = rssm.observe(obs_dict, action, h, z)

    # 상상 롤아웃 (정책 학습 단계)
    h, z, prior_logits = rssm.imagine(action, h, z)

    # 예측
    obs_recon  = rssm.decode_state(h, z)   # 관찰 재구성
    reward_hat = rssm.predict_reward(h, z)  # 보상 예측
    continue_p = rssm.predict_continue(h,z) # 에피소드 계속 여부
"""

import math
import numpy as np
from typing import Dict, Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import OneHotCategorical


# ──────────────────────────────────────────────────────────────
#  MultimodalEncoder (multimodal_networks.py 버전 재정의)
#  — LayerNorm + SiLU 적용된 버전으로 독립 유지
# ──────────────────────────────────────────────────────────────

class MultimodalEncoderWM(nn.Module):
    """World Model용 멀티모달 관찰 인코더.

    Input:
        vision       (4D)  : [azimuth, elevation, distance, rel_vel]
        proprioception(18D): [qpos(9), qvel(9)]
        context       (6D) : [balls, strikes, outs, r1, r2, r3]

    Output:
        fused feature (hidden_dim)
    """

    def __init__(self, hidden_dim: int = 256):
        super().__init__()

        self.vision_net = nn.Sequential(
            nn.Linear(4, 64),   nn.LayerNorm(64),  nn.SiLU(),
            nn.Linear(64, 64),  nn.LayerNorm(64),  nn.SiLU(),
        )
        self.prop_net = nn.Sequential(
            nn.Linear(18, 128), nn.LayerNorm(128), nn.SiLU(),
            nn.Linear(128, 128),nn.LayerNorm(128), nn.SiLU(),
        )
        self.context_net = nn.Sequential(
            nn.Linear(6, 32),   nn.LayerNorm(32),  nn.SiLU(),
            nn.Linear(32, 64),  nn.LayerNorm(64),  nn.SiLU(),
        )
        # 64 + 128 + 64 = 256 → hidden_dim
        self.fusion = nn.Sequential(
            nn.Linear(256, hidden_dim), nn.LayerNorm(hidden_dim), nn.SiLU(),
        )

    def forward(self, obs: Dict[str, torch.Tensor]) -> torch.Tensor:
        v = self.vision_net(obs["vision"])
        p = self.prop_net(obs["proprioception"])
        c = self.context_net(obs["context"])
        return self.fusion(torch.cat([v, p, c], dim=-1))


# ──────────────────────────────────────────────────────────────
#  SymLog / SymExp (DreamerV3 수치 안정화 기법)
# ──────────────────────────────────────────────────────────────

def symlog(x: torch.Tensor) -> torch.Tensor:
    """SymLog: 부호 보존 로그 변환. 큰 보상값의 스케일을 압축."""
    return torch.sign(x) * torch.log1p(x.abs())


def symexp(x: torch.Tensor) -> torch.Tensor:
    """SymExp: SymLog의 역변환."""
    return torch.sign(x) * (torch.exp(x.abs()) - 1)


# ──────────────────────────────────────────────────────────────
#  Baseball RSSM (Recurrent State Space Model)
# ──────────────────────────────────────────────────────────────

class BaseballRSSM(nn.Module):
    """야구 환경을 위한 RSSM World Model.

    Args:
        hidden_dim      : GRU 은닉 상태 크기 (h_t 차원)
        latent_classes  : Categorical 잠재 변수 개수
        latent_dim      : 각 Categorical 변수의 클래스 수
        obs_dim         : 관찰 차원 (vision4 + prop18 + context6 = 28)
        action_dim      : 액션 차원 (9-DOF)
    """

    def __init__(
        self,
        hidden_dim:     int = 256,
        latent_classes: int = 32,   # Categorical 변수 개수
        latent_dim:     int = 32,   # 각 Categorical 클래스 수
        obs_dim:        int = 28,   # 재구성 대상 총 차원
        action_dim:     int = 9,
    ):
        super().__init__()
        self.hidden_dim     = hidden_dim
        self.latent_classes = latent_classes
        self.latent_dim     = latent_dim
        self.z_dim          = latent_classes * latent_dim  # 펼친 잠재 벡터 크기
        self.obs_dim        = obs_dim
        self.action_dim     = action_dim

        # ── 1. 관찰 인코더 ──
        self.encoder = MultimodalEncoderWM(hidden_dim)

        # ── 2. Dynamics: (z_{t-1}, a_{t-1}) → GRU → h_t ──
        self.dynamics_gru = nn.GRUCell(
            input_size=self.z_dim + action_dim,
            hidden_size=hidden_dim,
        )

        # ── 3. Posterior: (h_t, obs_feat) → z_t (실제 관찰 이용) ──
        self.posterior_net = nn.Sequential(
            nn.Linear(hidden_dim + hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim), nn.SiLU(),
            nn.Linear(hidden_dim, latent_classes * latent_dim),
        )

        # ── 4. Prior: h_t → z_t 예측 (관찰 없이 상상) ──
        self.prior_net = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim), nn.SiLU(),
            nn.Linear(hidden_dim, latent_classes * latent_dim),
        )

        # ── 5. Decoder: (h_t, z_t) → 관찰 재구성 ──
        state_dim = hidden_dim + self.z_dim
        self.decoder = nn.Sequential(
            nn.Linear(state_dim, 256), nn.LayerNorm(256), nn.SiLU(),
            nn.Linear(256, 128),       nn.LayerNorm(128), nn.SiLU(),
            nn.Linear(128, obs_dim),
        )

        # ── 6. Reward Head: (h_t, z_t) → SymLog(r_t) ──
        self.reward_head = nn.Sequential(
            nn.Linear(state_dim, 256), nn.LayerNorm(256), nn.SiLU(),
            nn.Linear(256, 128),       nn.LayerNorm(128), nn.SiLU(),
            nn.Linear(128, 1),
        )

        # ── 7. Continue Head: (h_t, z_t) → P(episode continues) ──
        self.continue_head = nn.Sequential(
            nn.Linear(state_dim, 128), nn.LayerNorm(128), nn.SiLU(),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    # ──────────────────────────────────────────────────────────
    #  상태 유틸리티
    # ──────────────────────────────────────────────────────────

    def initial_state(
        self, batch_size: int, device: torch.device
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """초기 (h_0, z_0) 반환. 모두 0으로 초기화."""
        h = torch.zeros(batch_size, self.hidden_dim, device=device)
        z = torch.zeros(batch_size, self.latent_classes, self.latent_dim, device=device)
        return h, z

    def get_state(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        """(h, z) → 결합 상태 벡터 s (Actor/Critic 입력용)."""
        return torch.cat([h, z.flatten(1)], dim=-1)  # (B, hidden + z_dim)

    @property
    def state_dim(self) -> int:
        return self.hidden_dim + self.z_dim

    # ──────────────────────────────────────────────────────────
    #  핵심 전이 함수
    # ──────────────────────────────────────────────────────────

    def _gru_step(
        self,
        z: torch.Tensor,
        action: torch.Tensor,
        h: torch.Tensor,
    ) -> torch.Tensor:
        """GRU 단일 스텝: (z, a) → h'."""
        gru_input = torch.cat([z.flatten(1), action], dim=-1)
        return self.dynamics_gru(gru_input, h)

    def _sample_straight_through(self, logits: torch.Tensor) -> torch.Tensor:
        """Straight-Through Gumbel Softmax로 이산 잠재 변수 샘플링.

        Args:
            logits: (B, latent_classes, latent_dim)
        Returns:
            z:      (B, latent_classes, latent_dim) — 원핫 (forward)
        """
        b = logits.shape[0]
        flat = logits.view(b * self.latent_classes, self.latent_dim)
        # Straight-Through: forward=hard, backward=soft
        z_flat = F.gumbel_softmax(flat, tau=1.0, hard=True)
        return z_flat.view(b, self.latent_classes, self.latent_dim)

    def observe(
        self,
        obs_dict:  Dict[str, torch.Tensor],
        action:    torch.Tensor,
        h:         torch.Tensor,
        z:         torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """실제 관찰이 있을 때 Posterior z_t 계산 (학습 단계).

        Args:
            obs_dict: 현재 관찰 딕셔너리
            action:   이전 스텝의 액션 (B, action_dim)
            h:        이전 GRU 은닉 상태 (B, hidden_dim)
            z:        이전 잠재 상태 (B, latent_classes, latent_dim)

        Returns:
            h_new:          새 GRU 은닉 상태 (B, hidden_dim)
            z_new:          새 잠재 상태 샘플 (B, latent_classes, latent_dim)
            posterior_logits: (B, latent_classes, latent_dim)
        """
        # 1. GRU 전이
        h_new = self._gru_step(z, action, h)

        # 2. 관찰 인코딩
        obs_feat = self.encoder(obs_dict)  # (B, hidden_dim)

        # 3. Posterior: obs + h 모두 사용
        post_logits = self.posterior_net(
            torch.cat([obs_feat, h_new], dim=-1)
        ).view(-1, self.latent_classes, self.latent_dim)

        z_new = self._sample_straight_through(post_logits)
        return h_new, z_new, post_logits

    def imagine(
        self,
        action: torch.Tensor,
        h:      torch.Tensor,
        z:      torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """관찰 없이 Prior로 다음 상태를 상상 (상상 롤아웃 단계).

        Args:
            action: 현재 액션 (B, action_dim)
            h:      현재 GRU 은닉 상태
            z:      현재 잠재 상태

        Returns:
            h_new:        새 GRU 은닉 상태
            z_new:        Prior에서 샘플된 잠재 상태
            prior_logits: (B, latent_classes, latent_dim)
        """
        h_new = self._gru_step(z, action, h)

        prior_logits = self.prior_net(h_new).view(
            -1, self.latent_classes, self.latent_dim
        )
        z_new = self._sample_straight_through(prior_logits)
        return h_new, z_new, prior_logits

    # ──────────────────────────────────────────────────────────
    #  예측 헤드
    # ──────────────────────────────────────────────────────────

    def decode_state(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        """잠재 상태 → 관찰 재구성 (vision + prop + context 통합)."""
        s = self.get_state(h, z)
        return self.decoder(s)  # (B, obs_dim)

    def predict_reward(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        """잠재 상태 → SymLog 보상 예측."""
        s = self.get_state(h, z)
        return self.reward_head(s).squeeze(-1)  # (B,)

    def predict_continue(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        """잠재 상태 → 에피소드 계속 확률 (0~1)."""
        s = self.get_state(h, z)
        return self.continue_head(s).squeeze(-1)  # (B,)

    # ──────────────────────────────────────────────────────────
    #  시퀀스 단위 관찰 처리 (학습 배치용)
    # ──────────────────────────────────────────────────────────

    def observe_sequence(
        self,
        obs_seq:    Dict[str, torch.Tensor],
        action_seq: torch.Tensor,
        h0:         Optional[torch.Tensor] = None,
        z0:         Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """시퀀스 전체를 처리하여 Posterior 잠재 상태 시퀀스를 계산.

        Args:
            obs_seq:    각 키가 (B, T, dim) 형태인 관찰 딕셔너리
            action_seq: (B, T, action_dim)
            h0:         초기 은닉 상태 (없으면 0으로 초기화)
            z0:         초기 잠재 상태 (없으면 0으로 초기화)

        Returns:
            h_seq:         (B, T, hidden_dim) — 은닉 상태 시퀀스
            z_seq:         (B, T, latent_classes, latent_dim)
            post_logits_seq: (B, T, latent_classes, latent_dim)
            prior_logits_seq: (B, T, latent_classes, latent_dim)
        """
        B, T = action_seq.shape[:2]
        device = action_seq.device

        h = h0 if h0 is not None else torch.zeros(B, self.hidden_dim, device=device)
        z = z0 if z0 is not None else torch.zeros(B, self.latent_classes, self.latent_dim, device=device)

        h_list, z_list, post_list, prior_list = [], [], [], []

        for t in range(T):
            obs_t = {k: v[:, t] for k, v in obs_seq.items()}
            a_t   = action_seq[:, t]

            # Prior (obs 없이)
            h_pred = self._gru_step(z, a_t, h)
            prior_logits = self.prior_net(h_pred).view(B, self.latent_classes, self.latent_dim)

            # Posterior (obs 있음)
            obs_feat = self.encoder(obs_t)
            post_logits = self.posterior_net(
                torch.cat([obs_feat, h_pred], dim=-1)
            ).view(B, self.latent_classes, self.latent_dim)
            z_new = self._sample_straight_through(post_logits)

            h, z = h_pred, z_new

            h_list.append(h)
            z_list.append(z)
            post_list.append(post_logits)
            prior_list.append(prior_logits)

        h_seq    = torch.stack(h_list, dim=1)        # (B, T, hidden)
        z_seq    = torch.stack(z_list, dim=1)        # (B, T, C, D)
        post_seq = torch.stack(post_list, dim=1)     # (B, T, C, D)
        prior_seq= torch.stack(prior_list, dim=1)    # (B, T, C, D)

        return h_seq, z_seq, post_seq, prior_seq


# ──────────────────────────────────────────────────────────────
#  World Model 손실 함수
# ──────────────────────────────────────────────────────────────

def compute_world_model_loss(
    rssm:         BaseballRSSM,
    h_seq:        torch.Tensor,           # (B, T, hidden)
    z_seq:        torch.Tensor,           # (B, T, C, D)
    post_logits:  torch.Tensor,           # (B, T, C, D)
    prior_logits: torch.Tensor,           # (B, T, C, D)
    obs_target:   torch.Tensor,           # (B, T, obs_dim)
    reward_target:torch.Tensor,           # (B, T)
    continue_target: torch.Tensor,        # (B, T) — 0/1
    kl_scale:     float = 0.1,
    kl_balance:   float = 0.8,            # DreamerV3: 80% Prior / 20% Post
) -> Dict[str, torch.Tensor]:
    """World Model 전체 손실 계산.

    L_WM = L_pred + β * L_kl

    Args:
        kl_balance: Prior loss 비중 (DreamerV3 권장 0.8)

    Returns:
        손실 딕셔너리 (total, pred, kl, reward, continue, recon)
    """
    B, T = h_seq.shape[:2]
    flat_h = h_seq.reshape(B * T, -1)
    flat_z = z_seq.reshape(B * T, rssm.latent_classes, rssm.latent_dim)

    # ── 재구성 손실 (Decoder) ──
    recon = rssm.decode_state(flat_h, flat_z)
    recon_loss = F.mse_loss(recon, obs_target.reshape(B * T, -1))

    # ── 보상 예측 손실 (SymLog 공간에서 MSE) ──
    reward_pred = rssm.predict_reward(flat_h, flat_z)
    reward_true = symlog(reward_target.reshape(B * T))
    reward_loss = F.mse_loss(reward_pred, reward_true)

    # ── Continue 예측 손실 (BCE) ──
    cont_pred = rssm.predict_continue(flat_h, flat_z)
    cont_true = continue_target.reshape(B * T)
    continue_loss = F.binary_cross_entropy(cont_pred, cont_true)

    # ── KL Divergence 손실 (DreamerV3 Balanced KL) ──
    # posterior → prior 방향의 KL
    post_dist  = OneHotCategorical(logits=post_logits.reshape(B * T, rssm.latent_classes, rssm.latent_dim))
    prior_dist = OneHotCategorical(logits=prior_logits.reshape(B * T, rssm.latent_classes, rssm.latent_dim))

    # KL(posterior || prior): dynamics 학습 신호 (stop-grad posterior)
    kl_dynamics = torch.distributions.kl_divergence(
        OneHotCategorical(logits=post_logits.reshape(B*T, rssm.latent_classes, rssm.latent_dim).detach()),
        prior_dist,
    ).sum(-1).mean()

    # KL(posterior || prior): representation 학습 신호 (stop-grad prior)
    kl_rep = torch.distributions.kl_divergence(
        post_dist,
        OneHotCategorical(logits=prior_logits.reshape(B*T, rssm.latent_classes, rssm.latent_dim).detach()),
    ).sum(-1).mean()

    # Balanced KL
    kl_loss = kl_balance * kl_dynamics + (1 - kl_balance) * kl_rep

    # ── 총 손실 ──
    pred_loss = recon_loss + reward_loss + continue_loss
    total = pred_loss + kl_scale * kl_loss

    return {
        "total":    total,
        "pred":     pred_loss,
        "recon":    recon_loss,
        "reward":   reward_loss,
        "continue": continue_loss,
        "kl":       kl_loss,
        "kl_dyn":   kl_dynamics,
        "kl_rep":   kl_rep,
    }
