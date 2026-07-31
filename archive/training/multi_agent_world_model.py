"""
multi_agent_world_model.py — Multi-Agent 환경을 위한 Vision 기반 RSSM

기존 4D 벡터 대신 64x64 RGB 이미지를 입력으로 받는 CNN 인코더와 
디코더(Reconstruction)를 포함합니다.
투수용/타자용 독립적인 두 개의 모델 인스턴스로 사용됩니다.
"""

import math
import numpy as np
from typing import Dict, Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import OneHotCategorical


def symlog(x: torch.Tensor) -> torch.Tensor:
    return torch.sign(x) * torch.log1p(x.abs())

def symexp(x: torch.Tensor) -> torch.Tensor:
    return torch.sign(x) * (torch.exp(x.abs()) - 1)


class VisionEncoder(nn.Module):
    """64x64 RGB Image -> 256D Feature"""
    def __init__(self):
        super().__init__()
        # Input: (B, 3, 64, 64)
        self.net = nn.Sequential(
            nn.Conv2d(3, 32, 4, stride=2), nn.ReLU(),      # (B, 32, 31, 31)
            nn.Conv2d(32, 64, 4, stride=2), nn.ReLU(),     # (B, 64, 14, 14)
            nn.Conv2d(64, 128, 4, stride=2), nn.ReLU(),    # (B, 128, 6, 6)
            nn.Conv2d(128, 256, 4, stride=2), nn.ReLU(),   # (B, 256, 2, 2)
            nn.Flatten(),
            nn.Linear(256 * 2 * 2, 256), nn.LayerNorm(256), nn.SiLU()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x is assumed to be (B, C, H, W) in [0, 1] range or [-0.5, 0.5]
        return self.net(x)


class VisionDecoder(nn.Module):
    """State(h, z) -> 64x64 RGB Image"""
    def __init__(self, state_dim: int):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(state_dim, 256 * 2 * 2), nn.SiLU()
        )
        self.net = nn.Sequential(
            nn.ConvTranspose2d(256, 128, 4, stride=2), nn.ReLU(),
            nn.ConvTranspose2d(128, 64, 4, stride=2), nn.ReLU(),
            nn.ConvTranspose2d(64, 32, 4, stride=2), nn.ReLU(),
            nn.ConvTranspose2d(32, 3, 4, stride=2),
            # 출력 크기가 64x64가 되도록 조절 (보통 stride=2, k=4면 정확히 2배씩 늘어남)
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        x = self.fc(state)
        x = x.view(-1, 256, 2, 2)
        x = self.net(x)
        # 64x64에 맞추기 위해 interpolate 사용 (차이가 날 경우 대비)
        if x.shape[-1] != 64:
            x = F.interpolate(x, size=(64, 64))
        return x  # (B, 3, 64, 64) logits for MSE loss


class MultimodalEncoderWM(nn.Module):
    def __init__(self, prop_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.vision_enc = VisionEncoder()
        self.prop_net = nn.Sequential(
            nn.Linear(prop_dim, 128), nn.LayerNorm(128), nn.SiLU(),
        )
        self.fusion = nn.Sequential(
            nn.Linear(256 + 128, hidden_dim), nn.LayerNorm(hidden_dim), nn.SiLU(),
        )

    def forward(self, obs_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
        vision = obs_dict["vision"] - 0.5
        vision = torch.nan_to_num(vision, nan=0.0, posinf=1.0, neginf=-1.0)
        v_feat = self.vision_enc(vision)
        
        prop = obs_dict["proprioception"]
        prop = torch.nan_to_num(prop, nan=0.0, posinf=100.0, neginf=-100.0)
        p_feat = self.prop_net(prop)
        
        return self.fusion(torch.cat([v_feat, p_feat], dim=-1))


class BaseballVisionRSSM(nn.Module):
    def __init__(
        self,
        prop_dim:       int,
        action_dim:     int,
        hidden_dim:     int = 256,
        latent_classes: int = 32,
        latent_dim:     int = 32,
    ):
        super().__init__()
        self.hidden_dim     = hidden_dim
        self.latent_classes = latent_classes
        self.latent_dim     = latent_dim
        self.z_dim          = latent_classes * latent_dim
        self.prop_dim       = prop_dim
        self.action_dim     = action_dim

        self.encoder = MultimodalEncoderWM(prop_dim, hidden_dim)

        self.dynamics_gru = nn.GRUCell(
            input_size=self.z_dim + action_dim,
            hidden_size=hidden_dim,
        )

        self.posterior_net = nn.Sequential(
            nn.Linear(hidden_dim + hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim), nn.SiLU(),
            nn.Linear(hidden_dim, self.z_dim),
        )

        self.prior_net = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim), nn.SiLU(),
            nn.Linear(hidden_dim, self.z_dim),
        )

        state_dim = hidden_dim + self.z_dim
        
        # 디코더 분리 (Vision / Proprioception)
        self.vision_decoder = VisionDecoder(state_dim)
        self.prop_decoder = nn.Sequential(
            nn.Linear(state_dim, 128), nn.LayerNorm(128), nn.SiLU(),
            nn.Linear(128, prop_dim),
        )

        self.reward_head = nn.Sequential(
            nn.Linear(state_dim, 128), nn.LayerNorm(128), nn.SiLU(),
            nn.Linear(128, 1),
        )

        self.continue_head = nn.Sequential(
            nn.Linear(state_dim, 128), nn.LayerNorm(128), nn.SiLU(),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def initial_state(self, batch_size: int, device: torch.device):
        h = torch.zeros(batch_size, self.hidden_dim, device=device)
        z = torch.zeros(batch_size, self.latent_classes, self.latent_dim, device=device)
        return h, z

    def get_state(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        return torch.cat([h, z.flatten(1)], dim=-1)

    @property
    def state_dim(self) -> int:
        return self.hidden_dim + self.z_dim

    def _gru_step(self, z: torch.Tensor, action: torch.Tensor, h: torch.Tensor) -> torch.Tensor:
        gru_input = torch.cat([z.flatten(1), action], dim=-1)
        return self.dynamics_gru(gru_input, h)

    def _sample_straight_through(self, logits: torch.Tensor) -> torch.Tensor:
        # Clamp logits to prevent extreme values
        logits = torch.clamp(logits, -30.0, 30.0)
        b = logits.shape[0]
        flat = logits.view(b * self.latent_classes, self.latent_dim)
        
        # Manual Gumbel-Softmax to avoid PyTorch MPS backend bug
        U = torch.rand_like(flat)
        U = torch.clamp(U, 1e-6, 1.0 - 1e-6) # Prevent exactly 0.0 or 1.0
        gumbels = -torch.log(-torch.log(U))
        
        y = flat + gumbels
        probs = F.softmax(flat, dim=-1)
        
        index = y.argmax(dim=-1, keepdim=True)
        y_hard = torch.zeros_like(flat).scatter_(-1, index, 1.0)
        
        z_flat = y_hard - probs.detach() + probs
        
        return z_flat.view(b, self.latent_classes, self.latent_dim)

    def observe(self, obs_dict: Dict[str, torch.Tensor], action: torch.Tensor, h: torch.Tensor, z: torch.Tensor):
        h_new = self._gru_step(z, action, h)
        obs_feat = self.encoder(obs_dict)
        post_logits = self.posterior_net(torch.cat([obs_feat, h_new], dim=-1)).view(-1, self.latent_classes, self.latent_dim)
        z_new = self._sample_straight_through(post_logits)
        return h_new, z_new, post_logits

    def imagine(self, action: torch.Tensor, h: torch.Tensor, z: torch.Tensor):
        h_new = self._gru_step(z, action, h)
        prior_logits = self.prior_net(h_new).view(-1, self.latent_classes, self.latent_dim)
        z_new = self._sample_straight_through(prior_logits)
        return h_new, z_new, prior_logits

    def observe_sequence(self, obs_seq: Dict[str, torch.Tensor], action_seq: torch.Tensor, h0=None, z0=None):
        B, T = action_seq.shape[:2]
        device = action_seq.device
        h = h0 if h0 is not None else torch.zeros(B, self.hidden_dim, device=device)
        z = z0 if z0 is not None else torch.zeros(B, self.latent_classes, self.latent_dim, device=device)
        
        h_list, z_list, post_list, prior_list = [], [], [], []
        for t in range(T):
            obs_t = {k: v[:, t] for k, v in obs_seq.items()}
            a_t   = action_seq[:, t]

            h_pred = self._gru_step(z, a_t, h)
            prior_logits = self.prior_net(h_pred).view(B, self.latent_classes, self.latent_dim)

            obs_feat = self.encoder(obs_t)
            post_logits = self.posterior_net(torch.cat([obs_feat, h_pred], dim=-1)).view(B, self.latent_classes, self.latent_dim)
            z_new = self._sample_straight_through(post_logits)

            h, z = h_pred, z_new
            h_list.append(h); z_list.append(z); post_list.append(post_logits); prior_list.append(prior_logits)

        return (torch.stack(h_list, dim=1), torch.stack(z_list, dim=1), 
                torch.stack(post_list, dim=1), torch.stack(prior_list, dim=1))

    def predict_reward(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        return self.reward_head(self.get_state(h, z)).squeeze(-1)

    def predict_continue(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        return self.continue_head(self.get_state(h, z)).squeeze(-1)


def compute_vision_world_model_loss(
    rssm:         BaseballVisionRSSM,
    h_seq:        torch.Tensor,
    z_seq:        torch.Tensor,
    post_logits:  torch.Tensor,
    prior_logits: torch.Tensor,
    obs_target:   Dict[str, torch.Tensor],
    reward_target:torch.Tensor,
    continue_target: torch.Tensor,
    kl_scale:     float = 0.1,
    kl_balance:   float = 0.8,
) -> Dict[str, torch.Tensor]:
    B, T = h_seq.shape[:2]
    flat_h = h_seq.reshape(B * T, -1)
    flat_z = z_seq.reshape(B * T, rssm.latent_classes, rssm.latent_dim)
    state = rssm.get_state(flat_h, flat_z)

    # Reconstruction Loss
    recon_vision = rssm.vision_decoder(state)
    recon_prop = rssm.prop_decoder(state)
    
    # Target Vision is (B, T, C, H, W). We reshape to (B*T, C, H, W)
    target_vision = obs_target["vision"].reshape(B*T, 3, 64, 64)
    target_vision = target_vision - 0.5 # Match encoder preprocessing
    target_vision = torch.nan_to_num(target_vision, nan=0.0, posinf=1.0, neginf=-1.0)
    
    target_prop = obs_target["proprioception"].reshape(B*T, -1)
    target_prop = torch.nan_to_num(target_prop, nan=0.0, posinf=100.0, neginf=-100.0)

    loss_vision = F.mse_loss(recon_vision, target_vision)
    loss_prop = F.mse_loss(recon_prop, target_prop)
    recon_loss = loss_vision + loss_prop

    # Reward Loss
    reward_pred = rssm.reward_head(state).squeeze(-1)
    reward_true = symlog(reward_target.reshape(B * T))
    reward_true = torch.nan_to_num(reward_true, nan=0.0)
    reward_loss = F.mse_loss(reward_pred, reward_true)

    # Continue Loss
    cont_pred = rssm.continue_head(state).squeeze(-1)
    cont_true = continue_target.reshape(B * T)
    cont_true = torch.nan_to_num(cont_true, nan=0.0)
    continue_loss = F.binary_cross_entropy(cont_pred, cont_true)

    # Manual KL divergence computation to avoid PyTorch MPS OneHotCategorical scatter bug
    post_logits = post_logits.reshape(B * T, rssm.latent_classes, rssm.latent_dim)
    prior_logits = prior_logits.reshape(B * T, rssm.latent_classes, rssm.latent_dim)
    
    post_probs = F.softmax(post_logits, dim=-1)
    post_log_probs = F.log_softmax(post_logits, dim=-1)
    prior_log_probs = F.log_softmax(prior_logits, dim=-1)

    # Prevent NaN gradients from 0 * log(0) when backpropagating through post_probs
    post_probs_safe = post_probs.clamp(min=1e-8, max=1.0)

    # Dynamics loss: stop gradients on posterior
    post_probs_detached = post_probs_safe.detach()
    post_log_probs_detached = post_log_probs.detach()
    kl_dynamics = (post_probs_detached * (post_log_probs_detached - prior_log_probs)).sum(-1).sum(-1).mean()

    # Representation loss: stop gradients on prior
    prior_log_probs_detached = prior_log_probs.detach()
    kl_rep = (post_probs_safe * (post_log_probs - prior_log_probs_detached)).sum(-1).sum(-1).mean()

    kl_loss = kl_balance * kl_dynamics + (1 - kl_balance) * kl_rep

    pred_loss = recon_loss + reward_loss + continue_loss
    total = pred_loss + kl_scale * kl_loss

    return {
        "total":    total,
        "pred":     pred_loss,
        "recon":    recon_loss,
        "reward":   reward_loss,
        "continue": continue_loss,
        "kl":       kl_loss,
    }
