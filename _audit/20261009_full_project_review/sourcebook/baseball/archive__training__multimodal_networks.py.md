# baseball/archive/training/multimodal_networks.py

원본: [archive/training/multimodal_networks.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/multimodal_networks.py)

SHA256: `8f853f29cbad22340c1fc1ff40a736a9d6d70c377ce7bb73547f9340073dfff8`

전체 215행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `get_device` | FunctionDef | 14 | 19 |
| `MultimodalEncoder` | ClassDef | 22 | 74 |
| `__init__` | FunctionDef | 25 | 66 |
| `forward` | FunctionDef | 68 | 74 |
| `MultimodalBatterPolicy` | ClassDef | 77 | 191 |
| `__init__` | FunctionDef | 80 | 103 |
| `init_hidden` | FunctionDef | 105 | 109 |
| `forward` | FunctionDef | 111 | 141 |
| `get_action` | FunctionDef | 143 | 159 |
| `evaluate_actions` | FunctionDef | 161 | 182 |
| `predict_next_vision` | FunctionDef | 184 | 191 |
| `MultimodalValueNetwork` | ClassDef | 194 | 215 |
| `__init__` | FunctionDef | 197 | 200 |
| `forward` | FunctionDef | 202 | 215 |

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
   25 |     def __init__(self, hidden_dim: int = 256):
   26 |         super().__init__()
   27 |         
   28 |         # Vision: [azimuth, elevation, distance, rel_vel] (4D)
   29 |         self.vision_net = nn.Sequential(
   30 |             nn.Linear(4, 64),
   31 |             nn.LayerNorm(64),
   32 |             nn.SiLU(),
   33 |             nn.Linear(64, 64),
   34 |             nn.LayerNorm(64),
   35 |             nn.SiLU(),
   36 |         )
   37 |         
   38 |         # Proprioception: 9-DOF 관절 상태 (18D)
   39 |         self.prop_net = nn.Sequential(
   40 |             nn.Linear(18, 128),
   41 |             nn.LayerNorm(128),
   42 |             nn.SiLU(),
   43 |             nn.Linear(128, 128),
   44 |             nn.LayerNorm(128),
   45 |             nn.SiLU(),
   46 |         )
   47 |         
   48 |         # Context: [balls, strikes, outs, r1, r2, r3] (6D)
   49 |         self.context_net = nn.Sequential(
   50 |             nn.Linear(6, 32),
   51 |             nn.LayerNorm(32),
   52 |             nn.SiLU(),
   53 |             nn.Linear(32, 64),
   54 |             nn.LayerNorm(64),
   55 |             nn.SiLU(),
   56 |         )
   57 |         
   58 |         # Fusion (64 + 128 + 64 = 256)
   59 |         self.fusion_net = nn.Sequential(
   60 |             nn.Linear(256, hidden_dim),
   61 |             nn.LayerNorm(hidden_dim),
   62 |             nn.SiLU(),
   63 |             nn.Linear(hidden_dim, hidden_dim),
   64 |             nn.LayerNorm(hidden_dim),
   65 |             nn.SiLU(),
   66 |         )
   67 | 
   68 |     def forward(self, obs_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
   69 |         vis_feat = self.vision_net(obs_dict["vision"])
   70 |         prop_feat = self.prop_net(obs_dict["proprioception"])
   71 |         ctx_feat = self.context_net(obs_dict["context"])
   72 |         
   73 |         fused = torch.cat([vis_feat, prop_feat, ctx_feat], dim=-1)
   74 |         return self.fusion_net(fused)
   75 | 
   76 | 
   77 | class MultimodalBatterPolicy(nn.Module):
   78 |     """LSTM을 포함한 멀티모달 타자 정책 네트워크"""
   79 |     
   80 |     def __init__(self, action_dim: int = 9, hidden_dim: int = 256, num_layers: int = 1):
   81 |         super().__init__()
   82 |         self.action_dim = action_dim
   83 |         self.hidden_dim = hidden_dim
   84 |         self.num_layers = num_layers
   85 |         
   86 |         self.encoder = MultimodalEncoder(hidden_dim)
   87 |         
   88 |         self.lstm = nn.LSTM(
   89 |             input_size=hidden_dim,
   90 |             hidden_size=hidden_dim,
   91 |             num_layers=num_layers,
   92 |             batch_first=True
   93 |         )
   94 |         
   95 |         self.mean_head = nn.Linear(hidden_dim, action_dim)
   96 |         self.log_std = nn.Parameter(torch.zeros(1, action_dim))
   97 |         
   98 |         # Auxiliary Forward Predictive Task: Predicts next vision (4D) from (hidden + action)
   99 |         self.predictive_head = nn.Sequential(
  100 |             nn.Linear(hidden_dim + action_dim, 128),
  101 |             nn.ReLU(),
  102 |             nn.Linear(128, 4) # Vision output dimension is 4
  103 |         )
  104 | 
  105 |     def init_hidden(self, batch_size: int, device: torch.device):
  106 |         return (
  107 |             torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device),
  108 |             torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
  109 |         )
  110 | 
  111 |     def forward(
  112 |         self, 
  113 |         obs_dict: Dict[str, torch.Tensor],
  114 |         hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
  115 |     ):
  116 |         # Flattened sequence processing
  117 |         # 입력이 (batch, seq, dim)인지 (batch, dim)인지 확인
  118 |         is_seq = obs_dict["vision"].dim() == 3
  119 |         
  120 |         if is_seq:
  121 |             b, s = obs_dict["vision"].shape[:2]
  122 |             flat_obs = {
  123 |                 k: v.view(b * s, -1) for k, v in obs_dict.items()
  124 |             }
  125 |             features = self.encoder(flat_obs)
  126 |             features = features.view(b, s, -1)
  127 |         else:
  128 |             b = obs_dict["vision"].shape[0]
  129 |             features = self.encoder(obs_dict)
  130 |             features = features.unsqueeze(1) # (batch, 1, hidden)
  131 | 
  132 |         if hidden is None:
  133 |             hidden = self.init_hidden(b, obs_dict["vision"].device)
  134 |             
  135 |         lstm_out, hidden = self.lstm(features, hidden)
  136 |         last_out = lstm_out[:, -1, :]
  137 |         
  138 |         mean = torch.tanh(self.mean_head(last_out))
  139 |         log_std = self.log_std.expand_as(mean)
  140 |         
  141 |         return mean, log_std, hidden
  142 | 
  143 |     def get_action(
  144 |         self,
  145 |         obs_dict: Dict[str, torch.Tensor],
  146 |         hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
  147 |         deterministic: bool = False
  148 |     ):
  149 |         mean, log_std, next_hidden = self.forward(obs_dict, hidden)
  150 |         std = torch.exp(log_std.clamp(-20, 2))
  151 |         dist = Normal(loc=mean, scale=std)
  152 |         
  153 |         if deterministic:
  154 |             action = mean
  155 |         else:
  156 |             action = dist.sample()
  157 |             
  158 |         log_prob = dist.log_prob(action).sum(dim=-1, keepdim=True)
  159 |         return action, log_prob, mean, next_hidden
  160 | 
  161 |     def evaluate_actions(
  162 |         self,
  163 |         obs_dict: Dict[str, torch.Tensor],
  164 |         actions: torch.Tensor
  165 |     ):
  166 |         # 배치(에피소드 통째로) 처리
  167 |         # PPO 업데이트 시에는 보통 hidden 상태를 초기화하고 처음부터 흘려보냄
  168 |         b = obs_dict["vision"].shape[0]
  169 |         hidden = self.init_hidden(b, obs_dict["vision"].device)
  170 |         
  171 |         mean, log_std, hidden_out = self.forward(obs_dict, hidden)
  172 |         std = torch.exp(log_std.clamp(-20, 2))
  173 |         dist = Normal(loc=mean, scale=std)
  174 |         
  175 |         log_probs = dist.log_prob(actions).sum(dim=-1, keepdim=True)
  176 |         entropy = dist.entropy().sum(dim=-1, keepdim=True)
  177 |         
  178 |         # Extract last_out from hidden_out (h_n, c_n). h_n shape: (num_layers, batch, hidden_dim)
  179 |         last_out = hidden_out[0][-1]
  180 |         
  181 |         # Return last_out (lstm hidden state) to compute prediction loss
  182 |         return log_probs, entropy, last_out
  183 | 
  184 |     def predict_next_vision(self, lstm_out: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
  185 |         """
  186 |         Predict the next vision state given the current LSTM hidden state and action.
  187 |         lstm_out shape: (batch, seq, hidden) or (batch, hidden)
  188 |         actions shape: (batch, seq, action_dim) or (batch, action_dim)
  189 |         """
  190 |         fused = torch.cat([lstm_out, actions], dim=-1)
  191 |         return self.predictive_head(fused)
  192 | 
  193 | 
  194 | class MultimodalValueNetwork(nn.Module):
  195 |     """멀티모달 가치(Value) 네트워크"""
  196 |     
  197 |     def __init__(self, hidden_dim: int = 256):
  198 |         super().__init__()
  199 |         self.encoder = MultimodalEncoder(hidden_dim)
  200 |         self.value_head = nn.Linear(hidden_dim, 1)
  201 | 
  202 |     def forward(self, obs_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
  203 |         # LSTM 제외, 단순 MLP 구조 (안정성 목적)
  204 |         is_seq = obs_dict["vision"].dim() == 3
  205 |         if is_seq:
  206 |             b, s = obs_dict["vision"].shape[:2]
  207 |             flat_obs = {
  208 |                 k: v.view(b * s, -1) for k, v in obs_dict.items()
  209 |             }
  210 |             features = self.encoder(flat_obs)
  211 |             val = self.value_head(features)
  212 |             return val.view(b, s, 1)
  213 |         else:
  214 |             features = self.encoder(obs_dict)
  215 |             return self.value_head(features)
````
