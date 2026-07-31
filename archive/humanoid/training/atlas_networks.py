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
    """Atlas 30-DOF 멀티모달 인코더 (Vision 4D, Proprio 60D, Context 8D)"""
    
    def __init__(self, hidden_dim: int = 256, vision_dim: int = 4, proprio_dim: int = 60, context_dim: int = 8):
        super().__init__()
        
        self.vision_net = nn.Sequential(
            nn.Linear(vision_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU()
        )
        
        self.proprio_net = nn.Sequential(
            nn.Linear(proprio_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )
        
        self.context_net = nn.Sequential(
            nn.Linear(context_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU()
        )
        
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

class AtlasBatterPolicy(nn.Module):
    """Atlas 30-DOF 액션 정책 네트워크 (PPO + LSTM)"""
    
    def __init__(self, action_dim: int = 30, hidden_dim: int = 256, num_layers: int = 1, vision_dim: int = 4, proprio_dim: int = 60, context_dim: int = 8):
        super().__init__()
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        self.encoder = MultimodalEncoder(hidden_dim, vision_dim, proprio_dim, context_dim)
        self.lstm = nn.LSTM(input_size=hidden_dim, hidden_size=hidden_dim, num_layers=num_layers, batch_first=True)
        
        self.mean_head = nn.Linear(hidden_dim, action_dim)
        self.log_std = nn.Parameter(torch.zeros(action_dim) - 0.5)

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

    def forward(self, obs_dict: Dict[str, torch.Tensor], hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None):
        features = self.encoder(obs_dict)
        if features.dim() == 2:
            features = features.unsqueeze(1)
        
        if hidden is None:
            batch_size = features.size(0)
            hidden = self.init_hidden(batch_size, features.device)
            
        lstm_out, next_hidden = self.lstm(features, hidden)
        lstm_out = lstm_out.squeeze(1)
        
        mean = torch.tanh(self.mean_head(lstm_out))
        log_std = self.log_std.expand_as(mean)
        return mean, log_std, next_hidden

    def get_action(self, obs_dict: Dict[str, torch.Tensor], hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None, deterministic: bool = False):
        mean, log_std, next_hidden = self.forward(obs_dict, hidden)
        if deterministic:
            action = mean
            log_prob = torch.zeros(mean.size(0), device=mean.device)
            entropy = torch.zeros(mean.size(0), device=mean.device)
        else:
            std = torch.exp(log_std)
            dist = Normal(mean, std)
            action = dist.sample()
            log_prob = dist.log_prob(action).sum(dim=-1)
            entropy = dist.entropy().sum(dim=-1)

        action_clipped = torch.clamp(action, -1.0, 1.0)
        return action_clipped, log_prob, entropy, next_hidden

    def evaluate_actions(self, obs_dict: Dict[str, torch.Tensor], actions: torch.Tensor):
        mean, log_std, _ = self.forward(obs_dict)
        std = torch.exp(log_std)
        dist = Normal(mean, std)
        
        log_prob = dist.log_prob(actions).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)
        features = self.encoder(obs_dict)
        return log_prob, entropy, features

    def predict_next_vision(self, lstm_out: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        fused = torch.cat([lstm_out, actions], dim=-1)
        return self.predictive_head(fused)

class AtlasValueNetwork(nn.Module):
    """Atlas Value Network"""
    def __init__(self, hidden_dim: int = 256, vision_dim: int = 4, proprio_dim: int = 60, context_dim: int = 8):
        super().__init__()
        self.encoder = MultimodalEncoder(hidden_dim, vision_dim, proprio_dim, context_dim)
        self.value_head = nn.Linear(hidden_dim, 1)

    def forward(self, obs_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
        features = self.encoder(obs_dict)
        return self.value_head(features)
