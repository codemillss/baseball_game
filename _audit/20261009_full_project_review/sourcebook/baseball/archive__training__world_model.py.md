# baseball/archive/training/world_model.py

원본: [archive/training/world_model.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/world_model.py)

SHA256: `efc332b4c19ec60f11ec321635714735384ff2727ae649ee742b231d1b6bba31`

전체 441행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `MultimodalEncoderWM` | ClassDef | 45 | 81 |
| `__init__` | FunctionDef | 57 | 75 |
| `forward` | FunctionDef | 77 | 81 |
| `symlog` | FunctionDef | 88 | 90 |
| `symexp` | FunctionDef | 93 | 95 |
| `BaseballRSSM` | ClassDef | 102 | 361 |
| `__init__` | FunctionDef | 113 | 172 |
| `initial_state` | FunctionDef | 178 | 184 |
| `get_state` | FunctionDef | 186 | 188 |
| `state_dim` | FunctionDef | 191 | 192 |
| `_gru_step` | FunctionDef | 198 | 206 |
| `_sample_straight_through` | FunctionDef | 208 | 220 |
| `observe` | FunctionDef | 222 | 254 |
| `imagine` | FunctionDef | 256 | 280 |
| `decode_state` | FunctionDef | 286 | 289 |
| `predict_reward` | FunctionDef | 291 | 294 |
| `predict_continue` | FunctionDef | 296 | 299 |
| `observe_sequence` | FunctionDef | 305 | 361 |
| `compute_world_model_loss` | FunctionDef | 368 | 441 |

## 전체 원문

````text
    1 | """
    2 | world_model.py — Baseball RSSM World Model (DreamerV3 경량화)
    3 | 
    4 | 아키텍처:
    5 |     잠재 상태 s_t = (h_t, z_t)
    6 |       h_t : 결정론적(Deterministic) GRU 은닉 벡터  → 과거 정보 요약
    7 |       z_t : 확률론적(Stochastic) Categorical 벡터  → 불확실성 표현
    8 | 
    9 | 학습 손실:
   10 |     L_WM = L_pred (재구성 + 보상 + continue 예측)
   11 |          + L_dyn  (Prior KL — dynamics 개선)
   12 |          + L_rep  (Posterior KL — representation 개선)
   13 | 
   14 | 사용법:
   15 |     rssm = BaseballRSSM()
   16 |     h, z = rssm.initial_state(batch_size, device)
   17 | 
   18 |     # 실제 관찰이 있을 때 (학습 단계)
   19 |     h, z, post_logits = rssm.observe(obs_dict, action, h, z)
   20 | 
   21 |     # 상상 롤아웃 (정책 학습 단계)
   22 |     h, z, prior_logits = rssm.imagine(action, h, z)
   23 | 
   24 |     # 예측
   25 |     obs_recon  = rssm.decode_state(h, z)   # 관찰 재구성
   26 |     reward_hat = rssm.predict_reward(h, z)  # 보상 예측
   27 |     continue_p = rssm.predict_continue(h,z) # 에피소드 계속 여부
   28 | """
   29 | 
   30 | import math
   31 | import numpy as np
   32 | from typing import Dict, Tuple, Optional
   33 | 
   34 | import torch
   35 | import torch.nn as nn
   36 | import torch.nn.functional as F
   37 | from torch.distributions import OneHotCategorical
   38 | 
   39 | 
   40 | # ──────────────────────────────────────────────────────────────
   41 | #  MultimodalEncoder (multimodal_networks.py 버전 재정의)
   42 | #  — LayerNorm + SiLU 적용된 버전으로 독립 유지
   43 | # ──────────────────────────────────────────────────────────────
   44 | 
   45 | class MultimodalEncoderWM(nn.Module):
   46 |     """World Model용 멀티모달 관찰 인코더.
   47 | 
   48 |     Input:
   49 |         vision       (4D)  : [azimuth, elevation, distance, rel_vel]
   50 |         proprioception(18D): [qpos(9), qvel(9)]
   51 |         context       (6D) : [balls, strikes, outs, r1, r2, r3]
   52 | 
   53 |     Output:
   54 |         fused feature (hidden_dim)
   55 |     """
   56 | 
   57 |     def __init__(self, hidden_dim: int = 256):
   58 |         super().__init__()
   59 | 
   60 |         self.vision_net = nn.Sequential(
   61 |             nn.Linear(4, 64),   nn.LayerNorm(64),  nn.SiLU(),
   62 |             nn.Linear(64, 64),  nn.LayerNorm(64),  nn.SiLU(),
   63 |         )
   64 |         self.prop_net = nn.Sequential(
   65 |             nn.Linear(18, 128), nn.LayerNorm(128), nn.SiLU(),
   66 |             nn.Linear(128, 128),nn.LayerNorm(128), nn.SiLU(),
   67 |         )
   68 |         self.context_net = nn.Sequential(
   69 |             nn.Linear(6, 32),   nn.LayerNorm(32),  nn.SiLU(),
   70 |             nn.Linear(32, 64),  nn.LayerNorm(64),  nn.SiLU(),
   71 |         )
   72 |         # 64 + 128 + 64 = 256 → hidden_dim
   73 |         self.fusion = nn.Sequential(
   74 |             nn.Linear(256, hidden_dim), nn.LayerNorm(hidden_dim), nn.SiLU(),
   75 |         )
   76 | 
   77 |     def forward(self, obs: Dict[str, torch.Tensor]) -> torch.Tensor:
   78 |         v = self.vision_net(obs["vision"])
   79 |         p = self.prop_net(obs["proprioception"])
   80 |         c = self.context_net(obs["context"])
   81 |         return self.fusion(torch.cat([v, p, c], dim=-1))
   82 | 
   83 | 
   84 | # ──────────────────────────────────────────────────────────────
   85 | #  SymLog / SymExp (DreamerV3 수치 안정화 기법)
   86 | # ──────────────────────────────────────────────────────────────
   87 | 
   88 | def symlog(x: torch.Tensor) -> torch.Tensor:
   89 |     """SymLog: 부호 보존 로그 변환. 큰 보상값의 스케일을 압축."""
   90 |     return torch.sign(x) * torch.log1p(x.abs())
   91 | 
   92 | 
   93 | def symexp(x: torch.Tensor) -> torch.Tensor:
   94 |     """SymExp: SymLog의 역변환."""
   95 |     return torch.sign(x) * (torch.exp(x.abs()) - 1)
   96 | 
   97 | 
   98 | # ──────────────────────────────────────────────────────────────
   99 | #  Baseball RSSM (Recurrent State Space Model)
  100 | # ──────────────────────────────────────────────────────────────
  101 | 
  102 | class BaseballRSSM(nn.Module):
  103 |     """야구 환경을 위한 RSSM World Model.
  104 | 
  105 |     Args:
  106 |         hidden_dim      : GRU 은닉 상태 크기 (h_t 차원)
  107 |         latent_classes  : Categorical 잠재 변수 개수
  108 |         latent_dim      : 각 Categorical 변수의 클래스 수
  109 |         obs_dim         : 관찰 차원 (vision4 + prop18 + context6 = 28)
  110 |         action_dim      : 액션 차원 (9-DOF)
  111 |     """
  112 | 
  113 |     def __init__(
  114 |         self,
  115 |         hidden_dim:     int = 256,
  116 |         latent_classes: int = 32,   # Categorical 변수 개수
  117 |         latent_dim:     int = 32,   # 각 Categorical 클래스 수
  118 |         obs_dim:        int = 28,   # 재구성 대상 총 차원
  119 |         action_dim:     int = 9,
  120 |     ):
  121 |         super().__init__()
  122 |         self.hidden_dim     = hidden_dim
  123 |         self.latent_classes = latent_classes
  124 |         self.latent_dim     = latent_dim
  125 |         self.z_dim          = latent_classes * latent_dim  # 펼친 잠재 벡터 크기
  126 |         self.obs_dim        = obs_dim
  127 |         self.action_dim     = action_dim
  128 | 
  129 |         # ── 1. 관찰 인코더 ──
  130 |         self.encoder = MultimodalEncoderWM(hidden_dim)
  131 | 
  132 |         # ── 2. Dynamics: (z_{t-1}, a_{t-1}) → GRU → h_t ──
  133 |         self.dynamics_gru = nn.GRUCell(
  134 |             input_size=self.z_dim + action_dim,
  135 |             hidden_size=hidden_dim,
  136 |         )
  137 | 
  138 |         # ── 3. Posterior: (h_t, obs_feat) → z_t (실제 관찰 이용) ──
  139 |         self.posterior_net = nn.Sequential(
  140 |             nn.Linear(hidden_dim + hidden_dim, hidden_dim),
  141 |             nn.LayerNorm(hidden_dim), nn.SiLU(),
  142 |             nn.Linear(hidden_dim, latent_classes * latent_dim),
  143 |         )
  144 | 
  145 |         # ── 4. Prior: h_t → z_t 예측 (관찰 없이 상상) ──
  146 |         self.prior_net = nn.Sequential(
  147 |             nn.Linear(hidden_dim, hidden_dim),
  148 |             nn.LayerNorm(hidden_dim), nn.SiLU(),
  149 |             nn.Linear(hidden_dim, latent_classes * latent_dim),
  150 |         )
  151 | 
  152 |         # ── 5. Decoder: (h_t, z_t) → 관찰 재구성 ──
  153 |         state_dim = hidden_dim + self.z_dim
  154 |         self.decoder = nn.Sequential(
  155 |             nn.Linear(state_dim, 256), nn.LayerNorm(256), nn.SiLU(),
  156 |             nn.Linear(256, 128),       nn.LayerNorm(128), nn.SiLU(),
  157 |             nn.Linear(128, obs_dim),
  158 |         )
  159 | 
  160 |         # ── 6. Reward Head: (h_t, z_t) → SymLog(r_t) ──
  161 |         self.reward_head = nn.Sequential(
  162 |             nn.Linear(state_dim, 256), nn.LayerNorm(256), nn.SiLU(),
  163 |             nn.Linear(256, 128),       nn.LayerNorm(128), nn.SiLU(),
  164 |             nn.Linear(128, 1),
  165 |         )
  166 | 
  167 |         # ── 7. Continue Head: (h_t, z_t) → P(episode continues) ──
  168 |         self.continue_head = nn.Sequential(
  169 |             nn.Linear(state_dim, 128), nn.LayerNorm(128), nn.SiLU(),
  170 |             nn.Linear(128, 1),
  171 |             nn.Sigmoid(),
  172 |         )
  173 | 
  174 |     # ──────────────────────────────────────────────────────────
  175 |     #  상태 유틸리티
  176 |     # ──────────────────────────────────────────────────────────
  177 | 
  178 |     def initial_state(
  179 |         self, batch_size: int, device: torch.device
  180 |     ) -> Tuple[torch.Tensor, torch.Tensor]:
  181 |         """초기 (h_0, z_0) 반환. 모두 0으로 초기화."""
  182 |         h = torch.zeros(batch_size, self.hidden_dim, device=device)
  183 |         z = torch.zeros(batch_size, self.latent_classes, self.latent_dim, device=device)
  184 |         return h, z
  185 | 
  186 |     def get_state(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
  187 |         """(h, z) → 결합 상태 벡터 s (Actor/Critic 입력용)."""
  188 |         return torch.cat([h, z.flatten(1)], dim=-1)  # (B, hidden + z_dim)
  189 | 
  190 |     @property
  191 |     def state_dim(self) -> int:
  192 |         return self.hidden_dim + self.z_dim
  193 | 
  194 |     # ──────────────────────────────────────────────────────────
  195 |     #  핵심 전이 함수
  196 |     # ──────────────────────────────────────────────────────────
  197 | 
  198 |     def _gru_step(
  199 |         self,
  200 |         z: torch.Tensor,
  201 |         action: torch.Tensor,
  202 |         h: torch.Tensor,
  203 |     ) -> torch.Tensor:
  204 |         """GRU 단일 스텝: (z, a) → h'."""
  205 |         gru_input = torch.cat([z.flatten(1), action], dim=-1)
  206 |         return self.dynamics_gru(gru_input, h)
  207 | 
  208 |     def _sample_straight_through(self, logits: torch.Tensor) -> torch.Tensor:
  209 |         """Straight-Through Gumbel Softmax로 이산 잠재 변수 샘플링.
  210 | 
  211 |         Args:
  212 |             logits: (B, latent_classes, latent_dim)
  213 |         Returns:
  214 |             z:      (B, latent_classes, latent_dim) — 원핫 (forward)
  215 |         """
  216 |         b = logits.shape[0]
  217 |         flat = logits.view(b * self.latent_classes, self.latent_dim)
  218 |         # Straight-Through: forward=hard, backward=soft
  219 |         z_flat = F.gumbel_softmax(flat, tau=1.0, hard=True)
  220 |         return z_flat.view(b, self.latent_classes, self.latent_dim)
  221 | 
  222 |     def observe(
  223 |         self,
  224 |         obs_dict:  Dict[str, torch.Tensor],
  225 |         action:    torch.Tensor,
  226 |         h:         torch.Tensor,
  227 |         z:         torch.Tensor,
  228 |     ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
  229 |         """실제 관찰이 있을 때 Posterior z_t 계산 (학습 단계).
  230 | 
  231 |         Args:
  232 |             obs_dict: 현재 관찰 딕셔너리
  233 |             action:   이전 스텝의 액션 (B, action_dim)
  234 |             h:        이전 GRU 은닉 상태 (B, hidden_dim)
  235 |             z:        이전 잠재 상태 (B, latent_classes, latent_dim)
  236 | 
  237 |         Returns:
  238 |             h_new:          새 GRU 은닉 상태 (B, hidden_dim)
  239 |             z_new:          새 잠재 상태 샘플 (B, latent_classes, latent_dim)
  240 |             posterior_logits: (B, latent_classes, latent_dim)
  241 |         """
  242 |         # 1. GRU 전이
  243 |         h_new = self._gru_step(z, action, h)
  244 | 
  245 |         # 2. 관찰 인코딩
  246 |         obs_feat = self.encoder(obs_dict)  # (B, hidden_dim)
  247 | 
  248 |         # 3. Posterior: obs + h 모두 사용
  249 |         post_logits = self.posterior_net(
  250 |             torch.cat([obs_feat, h_new], dim=-1)
  251 |         ).view(-1, self.latent_classes, self.latent_dim)
  252 | 
  253 |         z_new = self._sample_straight_through(post_logits)
  254 |         return h_new, z_new, post_logits
  255 | 
  256 |     def imagine(
  257 |         self,
  258 |         action: torch.Tensor,
  259 |         h:      torch.Tensor,
  260 |         z:      torch.Tensor,
  261 |     ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
  262 |         """관찰 없이 Prior로 다음 상태를 상상 (상상 롤아웃 단계).
  263 | 
  264 |         Args:
  265 |             action: 현재 액션 (B, action_dim)
  266 |             h:      현재 GRU 은닉 상태
  267 |             z:      현재 잠재 상태
  268 | 
  269 |         Returns:
  270 |             h_new:        새 GRU 은닉 상태
  271 |             z_new:        Prior에서 샘플된 잠재 상태
  272 |             prior_logits: (B, latent_classes, latent_dim)
  273 |         """
  274 |         h_new = self._gru_step(z, action, h)
  275 | 
  276 |         prior_logits = self.prior_net(h_new).view(
  277 |             -1, self.latent_classes, self.latent_dim
  278 |         )
  279 |         z_new = self._sample_straight_through(prior_logits)
  280 |         return h_new, z_new, prior_logits
  281 | 
  282 |     # ──────────────────────────────────────────────────────────
  283 |     #  예측 헤드
  284 |     # ──────────────────────────────────────────────────────────
  285 | 
  286 |     def decode_state(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
  287 |         """잠재 상태 → 관찰 재구성 (vision + prop + context 통합)."""
  288 |         s = self.get_state(h, z)
  289 |         return self.decoder(s)  # (B, obs_dim)
  290 | 
  291 |     def predict_reward(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
  292 |         """잠재 상태 → SymLog 보상 예측."""
  293 |         s = self.get_state(h, z)
  294 |         return self.reward_head(s).squeeze(-1)  # (B,)
  295 | 
  296 |     def predict_continue(self, h: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
  297 |         """잠재 상태 → 에피소드 계속 확률 (0~1)."""
  298 |         s = self.get_state(h, z)
  299 |         return self.continue_head(s).squeeze(-1)  # (B,)
  300 | 
  301 |     # ──────────────────────────────────────────────────────────
  302 |     #  시퀀스 단위 관찰 처리 (학습 배치용)
  303 |     # ──────────────────────────────────────────────────────────
  304 | 
  305 |     def observe_sequence(
  306 |         self,
  307 |         obs_seq:    Dict[str, torch.Tensor],
  308 |         action_seq: torch.Tensor,
  309 |         h0:         Optional[torch.Tensor] = None,
  310 |         z0:         Optional[torch.Tensor] = None,
  311 |     ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
  312 |         """시퀀스 전체를 처리하여 Posterior 잠재 상태 시퀀스를 계산.
  313 | 
  314 |         Args:
  315 |             obs_seq:    각 키가 (B, T, dim) 형태인 관찰 딕셔너리
  316 |             action_seq: (B, T, action_dim)
  317 |             h0:         초기 은닉 상태 (없으면 0으로 초기화)
  318 |             z0:         초기 잠재 상태 (없으면 0으로 초기화)
  319 | 
  320 |         Returns:
  321 |             h_seq:         (B, T, hidden_dim) — 은닉 상태 시퀀스
  322 |             z_seq:         (B, T, latent_classes, latent_dim)
  323 |             post_logits_seq: (B, T, latent_classes, latent_dim)
  324 |             prior_logits_seq: (B, T, latent_classes, latent_dim)
  325 |         """
  326 |         B, T = action_seq.shape[:2]
  327 |         device = action_seq.device
  328 | 
  329 |         h = h0 if h0 is not None else torch.zeros(B, self.hidden_dim, device=device)
  330 |         z = z0 if z0 is not None else torch.zeros(B, self.latent_classes, self.latent_dim, device=device)
  331 | 
  332 |         h_list, z_list, post_list, prior_list = [], [], [], []
  333 | 
  334 |         for t in range(T):
  335 |             obs_t = {k: v[:, t] for k, v in obs_seq.items()}
  336 |             a_t   = action_seq[:, t]
  337 | 
  338 |             # Prior (obs 없이)
  339 |             h_pred = self._gru_step(z, a_t, h)
  340 |             prior_logits = self.prior_net(h_pred).view(B, self.latent_classes, self.latent_dim)
  341 | 
  342 |             # Posterior (obs 있음)
  343 |             obs_feat = self.encoder(obs_t)
  344 |             post_logits = self.posterior_net(
  345 |                 torch.cat([obs_feat, h_pred], dim=-1)
  346 |             ).view(B, self.latent_classes, self.latent_dim)
  347 |             z_new = self._sample_straight_through(post_logits)
  348 | 
  349 |             h, z = h_pred, z_new
  350 | 
  351 |             h_list.append(h)
  352 |             z_list.append(z)
  353 |             post_list.append(post_logits)
  354 |             prior_list.append(prior_logits)
  355 | 
  356 |         h_seq    = torch.stack(h_list, dim=1)        # (B, T, hidden)
  357 |         z_seq    = torch.stack(z_list, dim=1)        # (B, T, C, D)
  358 |         post_seq = torch.stack(post_list, dim=1)     # (B, T, C, D)
  359 |         prior_seq= torch.stack(prior_list, dim=1)    # (B, T, C, D)
  360 | 
  361 |         return h_seq, z_seq, post_seq, prior_seq
  362 | 
  363 | 
  364 | # ──────────────────────────────────────────────────────────────
  365 | #  World Model 손실 함수
  366 | # ──────────────────────────────────────────────────────────────
  367 | 
  368 | def compute_world_model_loss(
  369 |     rssm:         BaseballRSSM,
  370 |     h_seq:        torch.Tensor,           # (B, T, hidden)
  371 |     z_seq:        torch.Tensor,           # (B, T, C, D)
  372 |     post_logits:  torch.Tensor,           # (B, T, C, D)
  373 |     prior_logits: torch.Tensor,           # (B, T, C, D)
  374 |     obs_target:   torch.Tensor,           # (B, T, obs_dim)
  375 |     reward_target:torch.Tensor,           # (B, T)
  376 |     continue_target: torch.Tensor,        # (B, T) — 0/1
  377 |     kl_scale:     float = 0.1,
  378 |     kl_balance:   float = 0.8,            # DreamerV3: 80% Prior / 20% Post
  379 | ) -> Dict[str, torch.Tensor]:
  380 |     """World Model 전체 손실 계산.
  381 | 
  382 |     L_WM = L_pred + β * L_kl
  383 | 
  384 |     Args:
  385 |         kl_balance: Prior loss 비중 (DreamerV3 권장 0.8)
  386 | 
  387 |     Returns:
  388 |         손실 딕셔너리 (total, pred, kl, reward, continue, recon)
  389 |     """
  390 |     B, T = h_seq.shape[:2]
  391 |     flat_h = h_seq.reshape(B * T, -1)
  392 |     flat_z = z_seq.reshape(B * T, rssm.latent_classes, rssm.latent_dim)
  393 | 
  394 |     # ── 재구성 손실 (Decoder) ──
  395 |     recon = rssm.decode_state(flat_h, flat_z)
  396 |     recon_loss = F.mse_loss(recon, obs_target.reshape(B * T, -1))
  397 | 
  398 |     # ── 보상 예측 손실 (SymLog 공간에서 MSE) ──
  399 |     reward_pred = rssm.predict_reward(flat_h, flat_z)
  400 |     reward_true = symlog(reward_target.reshape(B * T))
  401 |     reward_loss = F.mse_loss(reward_pred, reward_true)
  402 | 
  403 |     # ── Continue 예측 손실 (BCE) ──
  404 |     cont_pred = rssm.predict_continue(flat_h, flat_z)
  405 |     cont_true = continue_target.reshape(B * T)
  406 |     continue_loss = F.binary_cross_entropy(cont_pred, cont_true)
  407 | 
  408 |     # ── KL Divergence 손실 (DreamerV3 Balanced KL) ──
  409 |     # posterior → prior 방향의 KL
  410 |     post_dist  = OneHotCategorical(logits=post_logits.reshape(B * T, rssm.latent_classes, rssm.latent_dim))
  411 |     prior_dist = OneHotCategorical(logits=prior_logits.reshape(B * T, rssm.latent_classes, rssm.latent_dim))
  412 | 
  413 |     # KL(posterior || prior): dynamics 학습 신호 (stop-grad posterior)
  414 |     kl_dynamics = torch.distributions.kl_divergence(
  415 |         OneHotCategorical(logits=post_logits.reshape(B*T, rssm.latent_classes, rssm.latent_dim).detach()),
  416 |         prior_dist,
  417 |     ).sum(-1).mean()
  418 | 
  419 |     # KL(posterior || prior): representation 학습 신호 (stop-grad prior)
  420 |     kl_rep = torch.distributions.kl_divergence(
  421 |         post_dist,
  422 |         OneHotCategorical(logits=prior_logits.reshape(B*T, rssm.latent_classes, rssm.latent_dim).detach()),
  423 |     ).sum(-1).mean()
  424 | 
  425 |     # Balanced KL
  426 |     kl_loss = kl_balance * kl_dynamics + (1 - kl_balance) * kl_rep
  427 | 
  428 |     # ── 총 손실 ──
  429 |     pred_loss = recon_loss + reward_loss + continue_loss
  430 |     total = pred_loss + kl_scale * kl_loss
  431 | 
  432 |     return {
  433 |         "total":    total,
  434 |         "pred":     pred_loss,
  435 |         "recon":    recon_loss,
  436 |         "reward":   reward_loss,
  437 |         "continue": continue_loss,
  438 |         "kl":       kl_loss,
  439 |         "kl_dyn":   kl_dynamics,
  440 |         "kl_rep":   kl_rep,
  441 |     }
````
