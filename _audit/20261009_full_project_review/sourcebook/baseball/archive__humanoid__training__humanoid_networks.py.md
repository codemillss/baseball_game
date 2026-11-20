# baseball/archive/humanoid/training/humanoid_networks.py

원본: [archive/humanoid/training/humanoid_networks.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/humanoid/training/humanoid_networks.py)

SHA256: `0e3ed6f0ceaa68a9ab51d74b4a9cd3c0fe9258c8eb6396babc12e6c76a826b0a`

전체 207행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `get_device` | FunctionDef | 14 | 19 |
| `MultimodalEncoder` | ClassDef | 22 | 66 |
| `__init__` | FunctionDef | 25 | 58 |
| `forward` | FunctionDef | 60 | 66 |
| `MultimodalBatterPolicy` | ClassDef | 69 | 183 |
| `__init__` | FunctionDef | 72 | 95 |
| `init_hidden` | FunctionDef | 97 | 101 |
| `forward` | FunctionDef | 103 | 133 |
| `get_action` | FunctionDef | 135 | 151 |
| `evaluate_actions` | FunctionDef | 153 | 174 |
| `predict_next_vision` | FunctionDef | 176 | 183 |
| `MultimodalValueNetwork` | ClassDef | 186 | 207 |
| `__init__` | FunctionDef | 189 | 192 |
| `forward` | FunctionDef | 194 | 207 |

## 전체 원문

````text
    1 | """
    2 | multimodal_networks.py — 멀티모달(Vision, Proprioception, Context) 신경망
    3 | 
    4 | Phase 2의 Dict 관찰 공간을 처리하는 정책(Policy) 및 가치(Value) 네트워크.
    5 | 각 모달리티를 개별적으로 인코딩(Embedding)한 후 융합(Fusion)하여 결과를 출력합니다.
    6 | """
    7 | 
    8 | import torch
    9 | import torch.nn as nn
   10 | from torch.distributions import Normal
   11 | from typing import Dict, Tuple, Optional
   12 | 
   13 | 
   14 | def get_device() -> torch.device:
   15 |     if torch.backends.mps.is_available():
   16 |         return torch.device("mps")
   17 |     if torch.cuda.is_available():
   18 |         return torch.device("cuda")
   19 |     return torch.device("cpu")
   20 | 
   21 | 
   22 | class MultimodalEncoder(nn.Module):
   23 |     """3가지 입력(Vision, Proprioception, Context)을 인코딩 및 융합하는 모듈"""
   24 |     
   25 |     def __init__(self, hidden_dim: int = 256, vision_dim: int = 4, proprio_dim: int = 42, context_dim: int = 8):
   26 |         super().__init__()
   27 |         
   28 |         # Vision: [azimuth, elevation, distance, rel_vel]
   29 |         self.vision_net = nn.Sequential(
   30 |             nn.Linear(vision_dim, 64),
   31 |             nn.ReLU(),
   32 |             nn.Linear(64, 64),
   33 |             nn.ReLU()
   34 |         )
   35 |         
   36 |         # Proprioception: 21 joints (qpos+qvel = 42)
   37 |         self.proprio_net = nn.Sequential(
   38 |             nn.Linear(proprio_dim, 128),
   39 |             nn.ReLU(),
   40 |             nn.Linear(128, 128),
   41 |             nn.ReLU()
   42 |         )
   43 |         
   44 |         # Context
   45 |         self.context_net = nn.Sequential(
   46 |             nn.Linear(context_dim, 32),
   47 |             nn.ReLU(),
   48 |             nn.Linear(32, 32),
   49 |             nn.ReLU()
   50 |         )
   51 |         
   52 |         # Fusion
   53 |         self.fusion = nn.Sequential(
   54 |             nn.Linear(64 + 128 + 32, hidden_dim),
   55 |             nn.ReLU(),
   56 |             nn.Linear(hidden_dim, hidden_dim),
   57 |             nn.LayerNorm(hidden_dim)
   58 |         )
   59 | 
   60 |     def forward(self, obs_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
   61 |         v = self.vision_net(obs_dict["vision"])
   62 |         p = self.proprio_net(obs_dict["proprio"])
   63 |         c = self.context_net(obs_dict["context"])
   64 |         
   65 |         fused = torch.cat([v, p, c], dim=-1)
   66 |         return self.fusion(fused)
   67 | 
   68 | 
   69 | class MultimodalBatterPolicy(nn.Module):
   70 |     """LSTM을 포함한 멀티모달 타자 정책 네트워크"""
   71 |     
   72 |     def __init__(self, action_dim: int = 21, hidden_dim: int = 256, num_layers: int = 1, vision_dim: int = 4, proprio_dim: int = 42, context_dim: int = 8):
   73 |         super().__init__()
   74 |         self.action_dim = action_dim
   75 |         self.hidden_dim = hidden_dim
   76 |         self.num_layers = num_layers
   77 |         
   78 |         self.encoder = MultimodalEncoder(hidden_dim, vision_dim, proprio_dim, context_dim)
   79 |         
   80 |         self.lstm = nn.LSTM(
   81 |             input_size=hidden_dim,
   82 |             hidden_size=hidden_dim,
   83 |             num_layers=num_layers,
   84 |             batch_first=True
   85 |         )
   86 |         
   87 |         self.mean_head = nn.Linear(hidden_dim, action_dim)
   88 |         self.log_std = nn.Parameter(torch.zeros(1, action_dim))
   89 |         
   90 |         # Auxiliary Forward Predictive Task: Predicts next vision (4D) from (hidden + action)
   91 |         self.predictive_head = nn.Sequential(
   92 |             nn.Linear(hidden_dim + action_dim, 128),
   93 |             nn.ReLU(),
   94 |             nn.Linear(128, vision_dim)
   95 |         )
   96 | 
   97 |     def init_hidden(self, batch_size: int, device: torch.device):
   98 |         return (
   99 |             torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device),
  100 |             torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
  101 |         )
  102 | 
  103 |     def forward(
  104 |         self, 
  105 |         obs_dict: Dict[str, torch.Tensor],
  106 |         hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
  107 |     ):
  108 |         # Flattened sequence processing
  109 |         # 입력이 (batch, seq, dim)인지 (batch, dim)인지 확인
  110 |         is_seq = obs_dict["vision"].dim() == 3
  111 |         
  112 |         if is_seq:
  113 |             b, s = obs_dict["vision"].shape[:2]
  114 |             flat_obs = {
  115 |                 k: v.view(b * s, -1) for k, v in obs_dict.items()
  116 |             }
  117 |             features = self.encoder(flat_obs)
  118 |             features = features.view(b, s, -1)
  119 |         else:
  120 |             b = obs_dict["vision"].shape[0]
  121 |             features = self.encoder(obs_dict)
  122 |             features = features.unsqueeze(1) # (batch, 1, hidden)
  123 | 
  124 |         if hidden is None:
  125 |             hidden = self.init_hidden(b, obs_dict["vision"].device)
  126 |             
  127 |         lstm_out, hidden = self.lstm(features, hidden)
  128 |         last_out = lstm_out[:, -1, :]
  129 |         
  130 |         mean = torch.tanh(self.mean_head(last_out))
  131 |         log_std = self.log_std.expand_as(mean)
  132 |         
  133 |         return mean, log_std, hidden
  134 | 
  135 |     def get_action(
  136 |         self,
  137 |         obs_dict: Dict[str, torch.Tensor],
  138 |         hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
  139 |         deterministic: bool = False
  140 |     ):
  141 |         mean, log_std, next_hidden = self.forward(obs_dict, hidden)
  142 |         std = torch.exp(log_std.clamp(-20, 2))
  143 |         dist = Normal(loc=mean, scale=std)
  144 |         
  145 |         if deterministic:
  146 |             action = mean
  147 |         else:
  148 |             action = dist.sample()
  149 |             
  150 |         log_prob = dist.log_prob(action).sum(dim=-1, keepdim=True)
  151 |         return action, log_prob, mean, next_hidden
  152 | 
  153 |     def evaluate_actions(
  154 |         self,
  155 |         obs_dict: Dict[str, torch.Tensor],
  156 |         actions: torch.Tensor
  157 |     ):
  158 |         # 배치(에피소드 통째로) 처리
  159 |         # PPO 업데이트 시에는 보통 hidden 상태를 초기화하고 처음부터 흘려보냄
  160 |         b = obs_dict["vision"].shape[0]
  161 |         hidden = self.init_hidden(b, obs_dict["vision"].device)
  162 |         
  163 |         mean, log_std, hidden_out = self.forward(obs_dict, hidden)
  164 |         std = torch.exp(log_std.clamp(-20, 2))
  165 |         dist = Normal(loc=mean, scale=std)
  166 |         
  167 |         log_probs = dist.log_prob(actions).sum(dim=-1, keepdim=True)
  168 |         entropy = dist.entropy().sum(dim=-1, keepdim=True)
  169 |         
  170 |         # Extract last_out from hidden_out (h_n, c_n). h_n shape: (num_layers, batch, hidden_dim)
  171 |         last_out = hidden_out[0][-1]
  172 |         
  173 |         # Return last_out (lstm hidden state) to compute prediction loss
  174 |         return log_probs, entropy, last_out
  175 | 
  176 |     def predict_next_vision(self, lstm_out: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
  177 |         """
  178 |         Predict the next vision state given the current LSTM hidden state and action.
  179 |         lstm_out shape: (batch, seq, hidden) or (batch, hidden)
  180 |         actions shape: (batch, seq, action_dim) or (batch, action_dim)
  181 |         """
  182 |         fused = torch.cat([lstm_out, actions], dim=-1)
  183 |         return self.predictive_head(fused)
  184 | 
  185 | 
  186 | class MultimodalValueNetwork(nn.Module):
  187 |     """멀티모달 가치(Value) 네트워크"""
  188 |     
  189 |     def __init__(self, hidden_dim: int = 256, vision_dim: int = 4, proprio_dim: int = 42, context_dim: int = 8):
  190 |         super().__init__()
  191 |         self.encoder = MultimodalEncoder(hidden_dim, vision_dim, proprio_dim, context_dim)
  192 |         self.value_head = nn.Linear(hidden_dim, 1)
  193 | 
  194 |     def forward(self, obs_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
  195 |         # LSTM 제외, 단순 MLP 구조 (안정성 목적)
  196 |         is_seq = obs_dict["vision"].dim() == 3
  197 |         if is_seq:
  198 |             b, s = obs_dict["vision"].shape[:2]
  199 |             flat_obs = {
  200 |                 k: v.view(b * s, -1) for k, v in obs_dict.items()
  201 |             }
  202 |             features = self.encoder(flat_obs)
  203 |             val = self.value_head(features)
  204 |             return val.view(b, s, 1)
  205 |         else:
  206 |             features = self.encoder(obs_dict)
  207 |             return self.value_head(features)
````
