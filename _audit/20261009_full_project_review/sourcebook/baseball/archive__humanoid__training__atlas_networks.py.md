# baseball/archive/humanoid/training/atlas_networks.py

원본: [archive/humanoid/training/atlas_networks.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/humanoid/training/atlas_networks.py)

SHA256: `0bd28982ab67585bb2f14e0ac4a3c60b55ebc11bd08a0ec53669eb7517c7ed4b`

전체 136행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `get_device` | FunctionDef | 6 | 11 |
| `MultimodalEncoder` | ClassDef | 13 | 52 |
| `__init__` | FunctionDef | 16 | 45 |
| `forward` | FunctionDef | 47 | 52 |
| `AtlasBatterPolicy` | ClassDef | 54 | 125 |
| `__init__` | FunctionDef | 57 | 73 |
| `init_hidden` | FunctionDef | 75 | 79 |
| `forward` | FunctionDef | 81 | 95 |
| `get_action` | FunctionDef | 97 | 111 |
| `evaluate_actions` | FunctionDef | 113 | 121 |
| `predict_next_vision` | FunctionDef | 123 | 125 |
| `AtlasValueNetwork` | ClassDef | 127 | 136 |
| `__init__` | FunctionDef | 129 | 132 |
| `forward` | FunctionDef | 134 | 136 |

## 전체 원문

````text
    1 | import torch
    2 | import torch.nn as nn
    3 | from torch.distributions import Normal
    4 | from typing import Dict, Tuple, Optional
    5 | 
    6 | def get_device() -> torch.device:
    7 |     if torch.backends.mps.is_available():
    8 |         return torch.device("mps")
    9 |     if torch.cuda.is_available():
   10 |         return torch.device("cuda")
   11 |     return torch.device("cpu")
   12 | 
   13 | class MultimodalEncoder(nn.Module):
   14 |     """Atlas 30-DOF 멀티모달 인코더 (Vision 4D, Proprio 60D, Context 8D)"""
   15 |     
   16 |     def __init__(self, hidden_dim: int = 256, vision_dim: int = 4, proprio_dim: int = 60, context_dim: int = 8):
   17 |         super().__init__()
   18 |         
   19 |         self.vision_net = nn.Sequential(
   20 |             nn.Linear(vision_dim, 64),
   21 |             nn.ReLU(),
   22 |             nn.Linear(64, 64),
   23 |             nn.ReLU()
   24 |         )
   25 |         
   26 |         self.proprio_net = nn.Sequential(
   27 |             nn.Linear(proprio_dim, 128),
   28 |             nn.ReLU(),
   29 |             nn.Linear(128, 128),
   30 |             nn.ReLU()
   31 |         )
   32 |         
   33 |         self.context_net = nn.Sequential(
   34 |             nn.Linear(context_dim, 32),
   35 |             nn.ReLU(),
   36 |             nn.Linear(32, 32),
   37 |             nn.ReLU()
   38 |         )
   39 |         
   40 |         self.fusion = nn.Sequential(
   41 |             nn.Linear(64 + 128 + 32, hidden_dim),
   42 |             nn.ReLU(),
   43 |             nn.Linear(hidden_dim, hidden_dim),
   44 |             nn.LayerNorm(hidden_dim)
   45 |         )
   46 | 
   47 |     def forward(self, obs_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
   48 |         v = self.vision_net(obs_dict["vision"])
   49 |         p = self.proprio_net(obs_dict["proprio"])
   50 |         c = self.context_net(obs_dict["context"])
   51 |         fused = torch.cat([v, p, c], dim=-1)
   52 |         return self.fusion(fused)
   53 | 
   54 | class AtlasBatterPolicy(nn.Module):
   55 |     """Atlas 30-DOF 액션 정책 네트워크 (PPO + LSTM)"""
   56 |     
   57 |     def __init__(self, action_dim: int = 30, hidden_dim: int = 256, num_layers: int = 1, vision_dim: int = 4, proprio_dim: int = 60, context_dim: int = 8):
   58 |         super().__init__()
   59 |         self.action_dim = action_dim
   60 |         self.hidden_dim = hidden_dim
   61 |         self.num_layers = num_layers
   62 |         
   63 |         self.encoder = MultimodalEncoder(hidden_dim, vision_dim, proprio_dim, context_dim)
   64 |         self.lstm = nn.LSTM(input_size=hidden_dim, hidden_size=hidden_dim, num_layers=num_layers, batch_first=True)
   65 |         
   66 |         self.mean_head = nn.Linear(hidden_dim, action_dim)
   67 |         self.log_std = nn.Parameter(torch.zeros(action_dim) - 0.5)
   68 | 
   69 |         self.predictive_head = nn.Sequential(
   70 |             nn.Linear(hidden_dim + action_dim, 128),
   71 |             nn.ReLU(),
   72 |             nn.Linear(128, vision_dim)
   73 |         )
   74 | 
   75 |     def init_hidden(self, batch_size: int, device: torch.device):
   76 |         return (
   77 |             torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device),
   78 |             torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
   79 |         )
   80 | 
   81 |     def forward(self, obs_dict: Dict[str, torch.Tensor], hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None):
   82 |         features = self.encoder(obs_dict)
   83 |         if features.dim() == 2:
   84 |             features = features.unsqueeze(1)
   85 |         
   86 |         if hidden is None:
   87 |             batch_size = features.size(0)
   88 |             hidden = self.init_hidden(batch_size, features.device)
   89 |             
   90 |         lstm_out, next_hidden = self.lstm(features, hidden)
   91 |         lstm_out = lstm_out.squeeze(1)
   92 |         
   93 |         mean = torch.tanh(self.mean_head(lstm_out))
   94 |         log_std = self.log_std.expand_as(mean)
   95 |         return mean, log_std, next_hidden
   96 | 
   97 |     def get_action(self, obs_dict: Dict[str, torch.Tensor], hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None, deterministic: bool = False):
   98 |         mean, log_std, next_hidden = self.forward(obs_dict, hidden)
   99 |         if deterministic:
  100 |             action = mean
  101 |             log_prob = torch.zeros(mean.size(0), device=mean.device)
  102 |             entropy = torch.zeros(mean.size(0), device=mean.device)
  103 |         else:
  104 |             std = torch.exp(log_std)
  105 |             dist = Normal(mean, std)
  106 |             action = dist.sample()
  107 |             log_prob = dist.log_prob(action).sum(dim=-1)
  108 |             entropy = dist.entropy().sum(dim=-1)
  109 | 
  110 |         action_clipped = torch.clamp(action, -1.0, 1.0)
  111 |         return action_clipped, log_prob, entropy, next_hidden
  112 | 
  113 |     def evaluate_actions(self, obs_dict: Dict[str, torch.Tensor], actions: torch.Tensor):
  114 |         mean, log_std, _ = self.forward(obs_dict)
  115 |         std = torch.exp(log_std)
  116 |         dist = Normal(mean, std)
  117 |         
  118 |         log_prob = dist.log_prob(actions).sum(dim=-1)
  119 |         entropy = dist.entropy().sum(dim=-1)
  120 |         features = self.encoder(obs_dict)
  121 |         return log_prob, entropy, features
  122 | 
  123 |     def predict_next_vision(self, lstm_out: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
  124 |         fused = torch.cat([lstm_out, actions], dim=-1)
  125 |         return self.predictive_head(fused)
  126 | 
  127 | class AtlasValueNetwork(nn.Module):
  128 |     """Atlas Value Network"""
  129 |     def __init__(self, hidden_dim: int = 256, vision_dim: int = 4, proprio_dim: int = 60, context_dim: int = 8):
  130 |         super().__init__()
  131 |         self.encoder = MultimodalEncoder(hidden_dim, vision_dim, proprio_dim, context_dim)
  132 |         self.value_head = nn.Linear(hidden_dim, 1)
  133 | 
  134 |     def forward(self, obs_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
  135 |         features = self.encoder(obs_dict)
  136 |         return self.value_head(features)
````
