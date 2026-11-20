# baseball/archive/training/multi_agent_world_model.py

원본: [archive/training/multi_agent_world_model.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/multi_agent_world_model.py)

SHA256: `62835f8f4bb2ec23fd2ebf172468fc2afc6538f38c61350838cb6aa521f2fc85`

전체 307행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `symlog` | FunctionDef | 19 | 20 |
| `symexp` | FunctionDef | 22 | 23 |
| `VisionEncoder` | ClassDef | 26 | 42 |
| `__init__` | FunctionDef | 28 | 38 |
| `forward` | FunctionDef | 40 | 42 |
| `VisionDecoder` | ClassDef | 45 | 67 |
| `__init__` | FunctionDef | 47 | 58 |
| `forward` | FunctionDef | 60 | 67 |
| `MultimodalEncoderWM` | ClassDef | 70 | 90 |
| `__init__` | FunctionDef | 71 | 79 |
| `forward` | FunctionDef | 81 | 90 |
| `BaseballVisionRSSM` | ClassDef | 93 | 227 |
| `__init__` | FunctionDef | 94 | 147 |
| `initial_state` | FunctionDef | 149 | 152 |
| `get_state` | FunctionDef | 154 | 155 |
| `state_dim` | FunctionDef | 158 | 159 |
| `_gru_step` | FunctionDef | 161 | 163 |
| `_sample_straight_through` | FunctionDef | 165 | 184 |
| `observe` | FunctionDef | 186 | 191 |
| `imagine` | FunctionDef | 193 | 197 |
| `observe_sequence` | FunctionDef | 199 | 221 |
| `predict_reward` | FunctionDef | 223 | 224 |
| `predict_continue` | FunctionDef | 226 | 227 |
| `compute_vision_world_model_loss` | FunctionDef | 230 | 307 |

## 전체 원문

````text
    1 | """
    2 | multi_agent_world_model.py — Multi-Agent 환경을 위한 Vision 기반 RSSM
    3 | 
    4 | 기존 4D 벡터 대신 64x64 RGB 이미지를 입력으로 받는 CNN 인코더와 
    5 | 디코더(Reconstruction)를 포함합니다.
    6 | 투수용/타자용 독립적인 두 개의 모델 인스턴스로 사용됩니다.
    7 | """
    8 | 
    9 | import math
   10 | import numpy as np
   11 | from typing import Dict, Tuple, Optional
   12 | 
   13 | import torch
   14 | import torch.nn as nn
   15 | import torch.nn.functional as F
   16 | from torch.distributions import OneHotCategorical
   17 | 
   18 | 
   19 | def symlog(x: torch.Tensor) -> torch.Tensor:
   20 |     return torch.sign(x) * torch.log1p(x.abs())
   21 | 
   22 | def symexp(x: torch.Tensor) -> torch.Tensor:
   23 |     return torch.sign(x) * (torch.exp(x.abs()) - 1)
   24 | 
   25 | 
   26 | class VisionEncoder(nn.Module):
   27 |     """64x64 RGB Image -> 256D Feature"""
   28 |     def __init__(self):
   29 |         super().__init__()
   30 |         # Input: (B, 3, 64, 64)
   31 |         self.net = nn.Sequential(
   32 |             nn.Conv2d(3, 32, 4, stride=2), nn.ReLU(),      # (B, 32, 31, 31)
   33 |             nn.Conv2d(32, 64, 4, stride=2), nn.ReLU(),     # (B, 64, 14, 14)
   34 |             nn.Conv2d(64, 128, 4, stride=2), nn.ReLU(),    # (B, 128, 6, 6)
   35 |             nn.Conv2d(128, 256, 4, stride=2), nn.ReLU(),   # (B, 256, 2, 2)
   36 |             nn.Flatten(),
   37 |             nn.Linear(256 * 2 * 2, 256), nn.LayerNorm(256), nn.SiLU()
   38 |         )
   39 | 
   40 |     def forward(self, x: torch.Tensor) -> torch.Tensor:
   41 |         # x is assumed to be (B, C, H, W) in [0, 1] range or [-0.5, 0.5]
   42 |         return self.net(x)
   43 | 
   44 | 
   45 | class VisionDecoder(nn.Module):
   46 |     """State(h, z) -> 64x64 RGB Image"""
   47 |     def __init__(self, state_dim: int):
   48 |         super().__init__()
   49 |         self.fc = nn.Sequential(
   50 |             nn.Linear(state_dim, 256 * 2 * 2), nn.SiLU()
   51 |         )
   52 |         self.net = nn.Sequential(
   53 |             nn.ConvTranspose2d(256, 128, 4, stride=2), nn.ReLU(),
   54 |             nn.ConvTranspose2d(128, 64, 4, stride=2), nn.ReLU(),
   55 |             nn.ConvTranspose2d(64, 32, 4, stride=2), nn.ReLU(),
   56 |             nn.ConvTranspose2d(32, 3, 4, stride=2),
   57 |             # 출력 크기가 64x64가 되도록 조절 (보통 stride=2, k=4면 정확히 2배씩 늘어남)
   58 |         )
   59 | 
   60 |     def forward(self, state: torch.Tensor) -> torch.Tensor:
   61 |         x = self.fc(state)
   62 |         x = x.view(-1, 256, 2, 2)
   63 |         x = self.net(x)
   64 |         # 64x64에 맞추기 위해 interpolate 사용 (차이가 날 경우 대비)
   65 |         if x.shape[-1] != 64:
   66 |             x = F.interpolate(x, size=(64, 64))
   67 |         return x  # (B, 3, 64, 64) logits for MSE loss
   68 | 
   69 | 
   70 | class MultimodalEncoderWM(nn.Module):
   71 |     def __init__(self, prop_dim: int, hidden_dim: int = 256):
   72 |         super().__init__()
   73 |         self.vision_enc = VisionEncoder()
   74 |         self.prop_net = nn.Sequential(
   75 |             nn.Linear(prop_dim, 128), nn.LayerNorm(128), nn.SiLU(),
   76 |         )
   77 |         self.fusion = nn.Sequential(
   78 |             nn.Linear(256 + 128, hidden_dim), nn.LayerNorm(hidden_dim), nn.SiLU(),
   79 |         )
   80 | 
   81 |     def forward(self, obs_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
   82 |         vision = obs_dict["vision"] - 0.5
   83 |         vision = torch.nan_to_num(vision, nan=0.0, posinf=1.0, neginf=-1.0)
   84 |         v_feat = self.vision_enc(vision)
   85 |         
   86 |         prop = obs_dict["proprioception"]
   87 |         prop = torch.nan_to_num(prop, nan=0.0, posinf=100.0, neginf=-100.0)
   88 |         p_feat = self.prop_net(prop)
   89 |         
   90 |         return self.fusion(torch.cat([v_feat, p_feat], dim=-1))
   91 | 
   92 | 
   93 | class BaseballVisionRSSM(nn.Module):
   94 |     def __init__(
   95 |         self,
   96 |         prop_dim:       int,
   97 |         action_dim:     int,
   98 |         hidden_dim:     int = 256,
   99 |         latent_classes: int = 32,
  100 |         latent_dim:     int = 32,
  101 |     ):
  102 |         super().__init__()
  103 |         self.hidden_dim     = hidden_dim
  104 |         self.latent_classes = latent_classes
  105 |         self.latent_dim     = latent_dim
  106 |         self.z_dim          = latent_classes * latent_dim
  107 |         self.prop_dim       = prop_dim
  108 |         self.action_dim     = action_dim
  109 | 
  110 |         self.encoder = MultimodalEncoderWM(prop_dim, hidden_dim)
  111 | 
  112 |         self.dynamics_gru = nn.GRUCell(
  113 |             input_size=self.z_dim + action_dim,
  114 |             hidden_size=hidden_dim,
  115 |         )
  116 | 
  117 |         self.posterior_net = nn.Sequential(
  118 |             nn.Linear(hidden_dim + hidden_dim, hidden_dim),
  119 |             nn.LayerNorm(hidden_dim), nn.SiLU(),
  120 |             nn.Linear(hidden_dim, self.z_dim),
  121 |         )
  122 | 
  123 |         self.prior_net = nn.Sequential(
  124 |             nn.Linear(hidden_dim, hidden_dim),
  125 |             nn.LayerNorm(hidden_dim), nn.SiLU(),
  126 |             nn.Linear(hidden_dim, self.z_dim),
  127 |         )
  128 | 
  129 |         state_dim = hidden_dim + self.z_dim
  130 |         
  131 |         # 디코더 분리 (Vision / Proprioception)
  132 |         self.vision_decoder = VisionDecoder(state_dim)
  133 |         self.prop_decoder = nn.Sequential(
  134 |             nn.Linear(state_dim, 128), nn.LayerNorm(128), nn.SiLU(),
  135 |             nn.Linear(128, prop_dim),
  136 |         )
  137 | 
  138 |         self.reward_head = nn.Sequential(
  139 |             nn.Linear(state_dim, 128), nn.LayerNorm(128), nn.SiLU(),
  140 |             nn.Linear(128, 1),
  141 |         )
  142 | 
  143 |         self.continue_head = nn.Sequential(
  144 |             nn.Linear(state_dim, 128), nn.LayerNorm(128), nn.SiLU(),
  145 |             nn.Linear(128, 1),
  146 |             nn.Sigmoid(),
  147 |         )
  148 | 
  149 |     def initial_state(self, batch_size: int, device: torch.device):
  150 |         h = torch.zeros(batch_size, self.hidden_dim, device=device)
  151 |         z = torch.zeros(batch_size, self.latent_classes, self.latent_dim, device=device)
  152 |         return h, z
  153 | 
  154 |     def get_state(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
  155 |         return torch.cat([h, z.flatten(1)], dim=-1)
  156 | 
  157 |     @property
  158 |     def state_dim(self) -> int:
  159 |         return self.hidden_dim + self.z_dim
  160 | 
  161 |     def _gru_step(self, z: torch.Tensor, action: torch.Tensor, h: torch.Tensor) -> torch.Tensor:
  162 |         gru_input = torch.cat([z.flatten(1), action], dim=-1)
  163 |         return self.dynamics_gru(gru_input, h)
  164 | 
  165 |     def _sample_straight_through(self, logits: torch.Tensor) -> torch.Tensor:
  166 |         # Clamp logits to prevent extreme values
  167 |         logits = torch.clamp(logits, -30.0, 30.0)
  168 |         b = logits.shape[0]
  169 |         flat = logits.view(b * self.latent_classes, self.latent_dim)
  170 |         
  171 |         # Manual Gumbel-Softmax to avoid PyTorch MPS backend bug
  172 |         U = torch.rand_like(flat)
  173 |         U = torch.clamp(U, 1e-6, 1.0 - 1e-6) # Prevent exactly 0.0 or 1.0
  174 |         gumbels = -torch.log(-torch.log(U))
  175 |         
  176 |         y = flat + gumbels
  177 |         probs = F.softmax(flat, dim=-1)
  178 |         
  179 |         index = y.argmax(dim=-1, keepdim=True)
  180 |         y_hard = torch.zeros_like(flat).scatter_(-1, index, 1.0)
  181 |         
  182 |         z_flat = y_hard - probs.detach() + probs
  183 |         
  184 |         return z_flat.view(b, self.latent_classes, self.latent_dim)
  185 | 
  186 |     def observe(self, obs_dict: Dict[str, torch.Tensor], action: torch.Tensor, h: torch.Tensor, z: torch.Tensor):
  187 |         h_new = self._gru_step(z, action, h)
  188 |         obs_feat = self.encoder(obs_dict)
  189 |         post_logits = self.posterior_net(torch.cat([obs_feat, h_new], dim=-1)).view(-1, self.latent_classes, self.latent_dim)
  190 |         z_new = self._sample_straight_through(post_logits)
  191 |         return h_new, z_new, post_logits
  192 | 
  193 |     def imagine(self, action: torch.Tensor, h: torch.Tensor, z: torch.Tensor):
  194 |         h_new = self._gru_step(z, action, h)
  195 |         prior_logits = self.prior_net(h_new).view(-1, self.latent_classes, self.latent_dim)
  196 |         z_new = self._sample_straight_through(prior_logits)
  197 |         return h_new, z_new, prior_logits
  198 | 
  199 |     def observe_sequence(self, obs_seq: Dict[str, torch.Tensor], action_seq: torch.Tensor, h0=None, z0=None):
  200 |         B, T = action_seq.shape[:2]
  201 |         device = action_seq.device
  202 |         h = h0 if h0 is not None else torch.zeros(B, self.hidden_dim, device=device)
  203 |         z = z0 if z0 is not None else torch.zeros(B, self.latent_classes, self.latent_dim, device=device)
  204 |         
  205 |         h_list, z_list, post_list, prior_list = [], [], [], []
  206 |         for t in range(T):
  207 |             obs_t = {k: v[:, t] for k, v in obs_seq.items()}
  208 |             a_t   = action_seq[:, t]
  209 | 
  210 |             h_pred = self._gru_step(z, a_t, h)
  211 |             prior_logits = self.prior_net(h_pred).view(B, self.latent_classes, self.latent_dim)
  212 | 
  213 |             obs_feat = self.encoder(obs_t)
  214 |             post_logits = self.posterior_net(torch.cat([obs_feat, h_pred], dim=-1)).view(B, self.latent_classes, self.latent_dim)
  215 |             z_new = self._sample_straight_through(post_logits)
  216 | 
  217 |             h, z = h_pred, z_new
  218 |             h_list.append(h); z_list.append(z); post_list.append(post_logits); prior_list.append(prior_logits)
  219 | 
  220 |         return (torch.stack(h_list, dim=1), torch.stack(z_list, dim=1), 
  221 |                 torch.stack(post_list, dim=1), torch.stack(prior_list, dim=1))
  222 | 
  223 |     def predict_reward(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
  224 |         return self.reward_head(self.get_state(h, z)).squeeze(-1)
  225 | 
  226 |     def predict_continue(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
  227 |         return self.continue_head(self.get_state(h, z)).squeeze(-1)
  228 | 
  229 | 
  230 | def compute_vision_world_model_loss(
  231 |     rssm:         BaseballVisionRSSM,
  232 |     h_seq:        torch.Tensor,
  233 |     z_seq:        torch.Tensor,
  234 |     post_logits:  torch.Tensor,
  235 |     prior_logits: torch.Tensor,
  236 |     obs_target:   Dict[str, torch.Tensor],
  237 |     reward_target:torch.Tensor,
  238 |     continue_target: torch.Tensor,
  239 |     kl_scale:     float = 0.1,
  240 |     kl_balance:   float = 0.8,
  241 | ) -> Dict[str, torch.Tensor]:
  242 |     B, T = h_seq.shape[:2]
  243 |     flat_h = h_seq.reshape(B * T, -1)
  244 |     flat_z = z_seq.reshape(B * T, rssm.latent_classes, rssm.latent_dim)
  245 |     state = rssm.get_state(flat_h, flat_z)
  246 | 
  247 |     # Reconstruction Loss
  248 |     recon_vision = rssm.vision_decoder(state)
  249 |     recon_prop = rssm.prop_decoder(state)
  250 |     
  251 |     # Target Vision is (B, T, C, H, W). We reshape to (B*T, C, H, W)
  252 |     target_vision = obs_target["vision"].reshape(B*T, 3, 64, 64)
  253 |     target_vision = target_vision - 0.5 # Match encoder preprocessing
  254 |     target_vision = torch.nan_to_num(target_vision, nan=0.0, posinf=1.0, neginf=-1.0)
  255 |     
  256 |     target_prop = obs_target["proprioception"].reshape(B*T, -1)
  257 |     target_prop = torch.nan_to_num(target_prop, nan=0.0, posinf=100.0, neginf=-100.0)
  258 | 
  259 |     loss_vision = F.mse_loss(recon_vision, target_vision)
  260 |     loss_prop = F.mse_loss(recon_prop, target_prop)
  261 |     recon_loss = loss_vision + loss_prop
  262 | 
  263 |     # Reward Loss
  264 |     reward_pred = rssm.reward_head(state).squeeze(-1)
  265 |     reward_true = symlog(reward_target.reshape(B * T))
  266 |     reward_true = torch.nan_to_num(reward_true, nan=0.0)
  267 |     reward_loss = F.mse_loss(reward_pred, reward_true)
  268 | 
  269 |     # Continue Loss
  270 |     cont_pred = rssm.continue_head(state).squeeze(-1)
  271 |     cont_true = continue_target.reshape(B * T)
  272 |     cont_true = torch.nan_to_num(cont_true, nan=0.0)
  273 |     continue_loss = F.binary_cross_entropy(cont_pred, cont_true)
  274 | 
  275 |     # Manual KL divergence computation to avoid PyTorch MPS OneHotCategorical scatter bug
  276 |     post_logits = post_logits.reshape(B * T, rssm.latent_classes, rssm.latent_dim)
  277 |     prior_logits = prior_logits.reshape(B * T, rssm.latent_classes, rssm.latent_dim)
  278 |     
  279 |     post_probs = F.softmax(post_logits, dim=-1)
  280 |     post_log_probs = F.log_softmax(post_logits, dim=-1)
  281 |     prior_log_probs = F.log_softmax(prior_logits, dim=-1)
  282 | 
  283 |     # Prevent NaN gradients from 0 * log(0) when backpropagating through post_probs
  284 |     post_probs_safe = post_probs.clamp(min=1e-8, max=1.0)
  285 | 
  286 |     # Dynamics loss: stop gradients on posterior
  287 |     post_probs_detached = post_probs_safe.detach()
  288 |     post_log_probs_detached = post_log_probs.detach()
  289 |     kl_dynamics = (post_probs_detached * (post_log_probs_detached - prior_log_probs)).sum(-1).sum(-1).mean()
  290 | 
  291 |     # Representation loss: stop gradients on prior
  292 |     prior_log_probs_detached = prior_log_probs.detach()
  293 |     kl_rep = (post_probs_safe * (post_log_probs - prior_log_probs_detached)).sum(-1).sum(-1).mean()
  294 | 
  295 |     kl_loss = kl_balance * kl_dynamics + (1 - kl_balance) * kl_rep
  296 | 
  297 |     pred_loss = recon_loss + reward_loss + continue_loss
  298 |     total = pred_loss + kl_scale * kl_loss
  299 | 
  300 |     return {
  301 |         "total":    total,
  302 |         "pred":     pred_loss,
  303 |         "recon":    recon_loss,
  304 |         "reward":   reward_loss,
  305 |         "continue": continue_loss,
  306 |         "kl":       kl_loss,
  307 |     }
````
