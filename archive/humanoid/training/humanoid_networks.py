"""
multimodal_networks.py — 멀티모달(Vision, Proprioception, Context) 신경망

Phase 2의 Dict 관찰 공간을 처리하는 정책(Policy) 및 가치(Value) 네트워크.
각 모달리티를 개별적으로 인코딩(Embedding)한 후 융합(Fusion)하여 결과를 출력합니다.
"""

import torch
import torch.nn as nn
from torch.distributions import Normal
from typing import Dict, Tuple, Optional


def get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


class MultimodalEncoder(nn.Module):
    """3가지 입력(Vision, Proprioception, Context)을 인코딩 및 융합하는 모듈"""
    
    def __init__(self, hidden_dim: int = 256, vision_dim: int = 4, proprio_dim: int = 42, context_dim: int = 8):
        super().__init__()
        
        # Vision: [azimuth, elevation, distance, rel_vel]
        self.vision_net = nn.Sequential(
            nn.Linear(vision_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU()
        )
        
        # Proprioception: 21 joints (qpos+qvel = 42)
        self.proprio_net = nn.Sequential(
            nn.Linear(proprio_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )
        
        # Context
        self.context_net = nn.Sequential(
            nn.Linear(context_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU()
        )
        
        # Fusion
        self.fusion = nn.Sequential(
            nn.Linear(64 + 128 + 32, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim)
        )

    def forward(self, obs_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
        v = self.vision_net(obs_dict["vision"])
        p = self.proprio_net(obs_dict["proprio"])
        c = self.context_net(obs_dict["context"])
        
        fused = torch.cat([v, p, c], dim=-1)
        return self.fusion(fused)


class MultimodalBatterPolicy(nn.Module):
    """LSTM을 포함한 멀티모달 타자 정책 네트워크"""
    
    def __init__(self, action_dim: int = 21, hidden_dim: int = 256, num_layers: int = 1, vision_dim: int = 4, proprio_dim: int = 42, context_dim: int = 8):
        super().__init__()
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        self.encoder = MultimodalEncoder(hidden_dim, vision_dim, proprio_dim, context_dim)
        
        self.lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True
        )
        
        self.mean_head = nn.Linear(hidden_dim, action_dim)
        self.log_std = nn.Parameter(torch.zeros(1, action_dim))
        
        # Auxiliary Forward Predictive Task: Predicts next vision (4D) from (hidden + action)
        self.predictive_head = nn.Sequential(
            nn.Linear(hidden_dim + action_dim, 128),
            nn.ReLU(),
            nn.Linear(128, vision_dim)
        )

    def init_hidden(self, batch_size: int, device: torch.device):
        return (
            torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device),
            torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
        )

    def forward(
        self, 
        obs_dict: Dict[str, torch.Tensor],
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ):
        # Flattened sequence processing
        # 입력이 (batch, seq, dim)인지 (batch, dim)인지 확인
        is_seq = obs_dict["vision"].dim() == 3
        
        if is_seq:
            b, s = obs_dict["vision"].shape[:2]
            flat_obs = {
                k: v.view(b * s, -1) for k, v in obs_dict.items()
            }
            features = self.encoder(flat_obs)
            features = features.view(b, s, -1)
        else:
            b = obs_dict["vision"].shape[0]
            features = self.encoder(obs_dict)
            features = features.unsqueeze(1) # (batch, 1, hidden)

        if hidden is None:
            hidden = self.init_hidden(b, obs_dict["vision"].device)
            
        lstm_out, hidden = self.lstm(features, hidden)
        last_out = lstm_out[:, -1, :]
        
        mean = torch.tanh(self.mean_head(last_out))
        log_std = self.log_std.expand_as(mean)
        
        return mean, log_std, hidden

    def get_action(
        self,
        obs_dict: Dict[str, torch.Tensor],
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        deterministic: bool = False
    ):
        mean, log_std, next_hidden = self.forward(obs_dict, hidden)
        std = torch.exp(log_std.clamp(-20, 2))
        dist = Normal(loc=mean, scale=std)
        
        if deterministic:
            action = mean
        else:
            action = dist.sample()
            
        log_prob = dist.log_prob(action).sum(dim=-1, keepdim=True)
        return action, log_prob, mean, next_hidden

    def evaluate_actions(
        self,
        obs_dict: Dict[str, torch.Tensor],
        actions: torch.Tensor
    ):
        # 배치(에피소드 통째로) 처리
        # PPO 업데이트 시에는 보통 hidden 상태를 초기화하고 처음부터 흘려보냄
        b = obs_dict["vision"].shape[0]
        hidden = self.init_hidden(b, obs_dict["vision"].device)
        
        mean, log_std, hidden_out = self.forward(obs_dict, hidden)
        std = torch.exp(log_std.clamp(-20, 2))
        dist = Normal(loc=mean, scale=std)
        
        log_probs = dist.log_prob(actions).sum(dim=-1, keepdim=True)
        entropy = dist.entropy().sum(dim=-1, keepdim=True)
        
        # Extract last_out from hidden_out (h_n, c_n). h_n shape: (num_layers, batch, hidden_dim)
        last_out = hidden_out[0][-1]
        
        # Return last_out (lstm hidden state) to compute prediction loss
        return log_probs, entropy, last_out

    def predict_next_vision(self, lstm_out: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        """
        Predict the next vision state given the current LSTM hidden state and action.
        lstm_out shape: (batch, seq, hidden) or (batch, hidden)
        actions shape: (batch, seq, action_dim) or (batch, action_dim)
        """
        fused = torch.cat([lstm_out, actions], dim=-1)
        return self.predictive_head(fused)


class MultimodalValueNetwork(nn.Module):
    """멀티모달 가치(Value) 네트워크"""
    
    def __init__(self, hidden_dim: int = 256, vision_dim: int = 4, proprio_dim: int = 42, context_dim: int = 8):
        super().__init__()
        self.encoder = MultimodalEncoder(hidden_dim, vision_dim, proprio_dim, context_dim)
        self.value_head = nn.Linear(hidden_dim, 1)

    def forward(self, obs_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
        # LSTM 제외, 단순 MLP 구조 (안정성 목적)
        is_seq = obs_dict["vision"].dim() == 3
        if is_seq:
            b, s = obs_dict["vision"].shape[:2]
            flat_obs = {
                k: v.view(b * s, -1) for k, v in obs_dict.items()
            }
            features = self.encoder(flat_obs)
            val = self.value_head(features)
            return val.view(b, s, 1)
        else:
            features = self.encoder(obs_dict)
            return self.value_head(features)
