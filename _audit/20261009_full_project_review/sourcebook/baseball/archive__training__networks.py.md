# baseball/archive/training/networks.py

원본: [archive/training/networks.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/networks.py)

SHA256: `81ffac836c401738a00b32333e0a1923fc9ea2fd7b684b1a24633865c071c5c4`

전체 430행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `get_device` | FunctionDef | 26 | 32 |
| `layer_init` | FunctionDef | 35 | 39 |
| `PitcherPolicy` | ClassDef | 46 | 142 |
| `__init__` | FunctionDef | 56 | 73 |
| `forward` | FunctionDef | 75 | 87 |
| `get_action` | FunctionDef | 89 | 117 |
| `evaluate_actions` | FunctionDef | 119 | 142 |
| `BatterPolicy` | ClassDef | 149 | 300 |
| `__init__` | FunctionDef | 159 | 195 |
| `init_hidden` | FunctionDef | 197 | 203 |
| `forward` | FunctionDef | 205 | 243 |
| `get_action` | FunctionDef | 245 | 275 |
| `evaluate_actions` | FunctionDef | 277 | 300 |
| `ValueNetwork` | ClassDef | 307 | 339 |
| `__init__` | FunctionDef | 317 | 328 |
| `forward` | FunctionDef | 330 | 339 |
| `PitcherAgent` | ClassDef | 346 | 380 |
| `__init__` | FunctionDef | 349 | 352 |
| `get_action_and_value` | FunctionDef | 354 | 366 |
| `evaluate` | FunctionDef | 368 | 380 |
| `BatterAgent` | ClassDef | 383 | 430 |
| `__init__` | FunctionDef | 386 | 389 |
| `get_action_and_value` | FunctionDef | 391 | 411 |
| `evaluate` | FunctionDef | 413 | 430 |

## 전체 원문

````text
    1 | """
    2 | networks.py — PyTorch Actor-Critic 신경망
    3 | 
    4 | 투수(MLP)와 타자(LSTM) 정책 네트워크 및 공유 Value 네트워크를 정의합니다.
    5 | 
    6 | Architecture:
    7 |     PitcherPolicy: MLP(6 → 256 → 256 → 128 → 5) + Tanh output
    8 |     BatterPolicy:  LSTM(13 → 128h → 128 → 4) + Tanh output
    9 |     ValueNetwork:  MLP(obs_dim → 256 → 256 → 1)
   10 | """
   11 | 
   12 | import math
   13 | from typing import Tuple, Optional
   14 | 
   15 | import torch
   16 | import torch.nn as nn
   17 | import torch.nn.functional as F
   18 | from torch.distributions import Normal
   19 | import numpy as np
   20 | 
   21 | 
   22 | # ──────────────────────────────────────────────────────────────
   23 | #  공통 유틸리티
   24 | # ──────────────────────────────────────────────────────────────
   25 | 
   26 | def get_device() -> torch.device:
   27 |     """사용 가능한 최적 디바이스를 반환합니다."""
   28 |     if torch.cuda.is_available():
   29 |         return torch.device("cuda")
   30 |     elif getattr(torch.backends, 'mps', None) is not None and torch.backends.mps.is_available():
   31 |         return torch.device("mps")
   32 |     return torch.device("cpu")
   33 | 
   34 | 
   35 | def layer_init(layer: nn.Linear, std: float = math.sqrt(2), bias_const: float = 0.0) -> nn.Linear:
   36 |     """PPO 스타일 직교 초기화."""
   37 |     nn.init.orthogonal_(layer.weight, std)
   38 |     nn.init.constant_(layer.bias, bias_const)
   39 |     return layer
   40 | 
   41 | 
   42 | # ──────────────────────────────────────────────────────────────
   43 | #  투수 정책 네트워크 (MLP)
   44 | # ──────────────────────────────────────────────────────────────
   45 | 
   46 | class PitcherPolicy(nn.Module):
   47 |     """투수 정책 네트워크.
   48 | 
   49 |     MLP 구조: 카운트와 이전 투구 이력으로 결정하므로 순차 구조 불필요.
   50 |     SiLU 활성화 + LayerNorm 적용.
   51 | 
   52 |     Input:  obs_dim (6) = [strikes, balls, prev_result, prev_plate_x, prev_plate_z, stance]
   53 |     Output: action_dim (5) = [v_release, θ_x, θ_z, ω_spin, a_axis]
   54 |     """
   55 | 
   56 |     def __init__(self, obs_dim: int = 6, action_dim: int = 5, hidden_dim: int = 256):
   57 |         super().__init__()
   58 | 
   59 |         self.actor_backbone = nn.Sequential(
   60 |             layer_init(nn.Linear(obs_dim, hidden_dim)),
   61 |             nn.LayerNorm(hidden_dim),
   62 |             nn.SiLU(),
   63 |             layer_init(nn.Linear(hidden_dim, hidden_dim)),
   64 |             nn.LayerNorm(hidden_dim),
   65 |             nn.SiLU(),
   66 |             layer_init(nn.Linear(hidden_dim, hidden_dim // 2)),
   67 |             nn.LayerNorm(hidden_dim // 2),
   68 |             nn.SiLU(),
   69 |         )
   70 | 
   71 |         # 평균과 로그 분산을 분리 출력
   72 |         self.mean_head = layer_init(nn.Linear(hidden_dim // 2, action_dim), std=0.01)
   73 |         self.log_std = nn.Parameter(torch.zeros(action_dim))
   74 | 
   75 |     def forward(self, obs: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
   76 |         """순전파: 관찰 → (평균, 로그 표준편차)
   77 | 
   78 |         Args:
   79 |             obs: (batch, obs_dim) 관찰 텐서
   80 | 
   81 |         Returns:
   82 |             (mean, log_std): 액션 분포의 평균과 로그 표준편차
   83 |         """
   84 |         features = self.actor_backbone(obs)
   85 |         mean = torch.tanh(self.mean_head(features))  # [-1, 1] 범위
   86 |         log_std = self.log_std.expand_as(mean)
   87 |         return mean, log_std
   88 | 
   89 |     def get_action(
   90 |         self,
   91 |         obs: torch.Tensor,
   92 |         deterministic: bool = False,
   93 |     ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
   94 |         """액션 샘플링 및 로그 확률 계산.
   95 | 
   96 |         Args:
   97 |             obs: (batch, obs_dim) 관찰 텐서
   98 |             deterministic: True이면 평균값 반환 (평가 시)
   99 | 
  100 |         Returns:
  101 |             (action, log_prob, entropy)
  102 |         """
  103 |         mean, log_std = self.forward(obs)
  104 |         std = torch.exp(log_std.clamp(-5, 2))
  105 |         dist = Normal(loc=mean, scale=std)
  106 | 
  107 |         if deterministic:
  108 |             action = mean
  109 |         else:
  110 |             action = dist.rsample()  # Reparameterization trick
  111 | 
  112 |         action = torch.clamp(action, -1.0, 1.0)
  113 | 
  114 |         log_prob = dist.log_prob(action).sum(dim=-1)
  115 |         entropy = dist.entropy().sum(dim=-1)
  116 | 
  117 |         return action, log_prob, entropy
  118 | 
  119 |     def evaluate_actions(
  120 |         self,
  121 |         obs: torch.Tensor,
  122 |         actions: torch.Tensor,
  123 |     ) -> Tuple[torch.Tensor, torch.Tensor]:
  124 |         """주어진 액션의 로그 확률과 엔트로피를 평가합니다.
  125 | 
  126 |         PPO 업데이트 시 사용됩니다.
  127 | 
  128 |         Args:
  129 |             obs: (batch, obs_dim) 관찰 텐서
  130 |             actions: (batch, action_dim) 액션 텐서
  131 | 
  132 |         Returns:
  133 |             (log_prob, entropy)
  134 |         """
  135 |         mean, log_std = self.forward(obs)
  136 |         std = torch.exp(log_std.clamp(-5, 2))
  137 |         dist = Normal(loc=mean, scale=std)
  138 | 
  139 |         log_prob = dist.log_prob(actions).sum(dim=-1)
  140 |         entropy = dist.entropy().sum(dim=-1)
  141 | 
  142 |         return log_prob, entropy
  143 | 
  144 | 
  145 | # ──────────────────────────────────────────────────────────────
  146 | #  타자 정책 네트워크 (LSTM)
  147 | # ──────────────────────────────────────────────────────────────
  148 | 
  149 | class BatterPolicy(nn.Module):
  150 |     """타자 정책 네트워크.
  151 | 
  152 |     LSTM 구조: 시시각각 변하는 공 궤적의 시계열 패턴을 포착합니다.
  153 |     공이 날아오는 동안 여러 프레임의 관찰을 순차적으로 처리합니다.
  154 | 
  155 |     Input:  obs_dim (13) = [ball_pos(3), ball_vel(3), bat_pos(3), bat_vel(3), time_to_plate]
  156 |     Output: action_dim (4) = [t_trigger, θ_yaw, θ_pitch, z_height]
  157 |     """
  158 | 
  159 |     def __init__(
  160 |         self,
  161 |         obs_dim: int = 13,
  162 |         action_dim: int = 4,
  163 |         hidden_dim: int = 128,
  164 |         num_layers: int = 2,
  165 |     ):
  166 |         super().__init__()
  167 | 
  168 |         # 입력 임베딩
  169 |         self.input_embed = nn.Sequential(
  170 |             layer_init(nn.Linear(obs_dim, hidden_dim)),
  171 |             nn.LayerNorm(hidden_dim),
  172 |             nn.SiLU(),
  173 |         )
  174 | 
  175 |         # LSTM 코어
  176 |         self.lstm = nn.LSTM(
  177 |             input_size=hidden_dim,
  178 |             hidden_size=hidden_dim,
  179 |             num_layers=num_layers,
  180 |             batch_first=True,
  181 |             dropout=0.1 if num_layers > 1 else 0.0,
  182 |         )
  183 | 
  184 |         # 출력 헤드
  185 |         self.output_net = nn.Sequential(
  186 |             layer_init(nn.Linear(hidden_dim, hidden_dim)),
  187 |             nn.LayerNorm(hidden_dim),
  188 |             nn.SiLU(),
  189 |         )
  190 | 
  191 |         self.mean_head = layer_init(nn.Linear(hidden_dim, action_dim), std=0.01)
  192 |         self.log_std = nn.Parameter(torch.zeros(action_dim))
  193 | 
  194 |         self.hidden_dim = hidden_dim
  195 |         self.num_layers = num_layers
  196 | 
  197 |     def init_hidden(self, batch_size: int = 1, device: Optional[torch.device] = None):
  198 |         """LSTM 은닉 상태를 초기화합니다."""
  199 |         if device is None:
  200 |             device = next(self.parameters()).device
  201 |         h = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
  202 |         c = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
  203 |         return (h, c)
  204 | 
  205 |     def forward(
  206 |         self,
  207 |         obs_seq: torch.Tensor,
  208 |         hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
  209 |     ) -> Tuple[torch.Tensor, torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
  210 |         """순전파: 관찰 시퀀스 → (평균, 로그 표준편차, 은닉 상태)
  211 | 
  212 |         Args:
  213 |             obs_seq: (batch, seq_len, obs_dim) 관찰 시퀀스
  214 |                      또는 (batch, obs_dim) 단일 프레임
  215 |             hidden: LSTM 은닉 상태 (h, c) 또는 None
  216 | 
  217 |         Returns:
  218 |             (mean, log_std, hidden)
  219 |         """
  220 |         if obs_seq.dim() == 2:
  221 |             # 단일 프레임 → 시퀀스 차원 추가
  222 |             obs_seq = obs_seq.unsqueeze(1)
  223 | 
  224 |         batch_size = obs_seq.size(0)
  225 | 
  226 |         # 입력 임베딩
  227 |         embedded = self.input_embed(obs_seq)  # (batch, seq, hidden)
  228 | 
  229 |         # LSTM
  230 |         if hidden is None:
  231 |             hidden = self.init_hidden(batch_size, obs_seq.device)
  232 | 
  233 |         lstm_out, hidden = self.lstm(embedded, hidden)
  234 | 
  235 |         # 마지막 시퀀스의 출력 사용
  236 |         last_out = lstm_out[:, -1, :]  # (batch, hidden)
  237 | 
  238 |         # 출력 네트워크
  239 |         features = self.output_net(last_out)
  240 |         mean = torch.tanh(self.mean_head(features))
  241 |         log_std = self.log_std.expand_as(mean)
  242 | 
  243 |         return mean, log_std, hidden
  244 | 
  245 |     def get_action(
  246 |         self,
  247 |         obs_seq: torch.Tensor,
  248 |         hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
  249 |         deterministic: bool = False,
  250 |     ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
  251 |         """액션 샘플링.
  252 | 
  253 |         Args:
  254 |             obs_seq: 관찰 시퀀스
  255 |             hidden: LSTM 은닉 상태
  256 |             deterministic: True이면 평균값 반환
  257 | 
  258 |         Returns:
  259 |             (action, log_prob, entropy, hidden)
  260 |         """
  261 |         mean, log_std, hidden = self.forward(obs_seq, hidden)
  262 |         std = torch.exp(log_std.clamp(-5, 2))
  263 |         dist = Normal(loc=mean, scale=std)
  264 | 
  265 |         if deterministic:
  266 |             action = mean
  267 |         else:
  268 |             action = dist.rsample()
  269 | 
  270 |         action = torch.clamp(action, -1.0, 1.0)
  271 | 
  272 |         log_prob = dist.log_prob(action).sum(dim=-1)
  273 |         entropy = dist.entropy().sum(dim=-1)
  274 | 
  275 |         return action, log_prob, entropy, hidden
  276 | 
  277 |     def evaluate_actions(
  278 |         self,
  279 |         obs_seq: torch.Tensor,
  280 |         actions: torch.Tensor,
  281 |         hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
  282 |     ) -> Tuple[torch.Tensor, torch.Tensor]:
  283 |         """주어진 액션 평가.
  284 | 
  285 |         Args:
  286 |             obs_seq: 관찰 시퀀스
  287 |             actions: 액션 텐서
  288 |             hidden: LSTM 은닉 상태
  289 | 
  290 |         Returns:
  291 |             (log_prob, entropy)
  292 |         """
  293 |         mean, log_std, _ = self.forward(obs_seq, hidden)
  294 |         std = torch.exp(log_std.clamp(-5, 2))
  295 |         dist = Normal(loc=mean, scale=std)
  296 | 
  297 |         log_prob = dist.log_prob(actions).sum(dim=-1)
  298 |         entropy = dist.entropy().sum(dim=-1)
  299 | 
  300 |         return log_prob, entropy
  301 | 
  302 | 
  303 | # ──────────────────────────────────────────────────────────────
  304 | #  Value 네트워크 (Critic)
  305 | # ──────────────────────────────────────────────────────────────
  306 | 
  307 | class ValueNetwork(nn.Module):
  308 |     """상태 가치 함수 네트워크 (Critic).
  309 | 
  310 |     투수와 타자 각각의 가치 추정에 사용됩니다.
  311 |     MLP(obs_dim → 256 → 256 → 1)
  312 | 
  313 |     Args:
  314 |         obs_dim: 관찰 벡터 차원
  315 |     """
  316 | 
  317 |     def __init__(self, obs_dim: int, hidden_dim: int = 256):
  318 |         super().__init__()
  319 | 
  320 |         self.network = nn.Sequential(
  321 |             layer_init(nn.Linear(obs_dim, hidden_dim)),
  322 |             nn.LayerNorm(hidden_dim),
  323 |             nn.SiLU(),
  324 |             layer_init(nn.Linear(hidden_dim, hidden_dim)),
  325 |             nn.LayerNorm(hidden_dim),
  326 |             nn.SiLU(),
  327 |             layer_init(nn.Linear(hidden_dim, 1), std=1.0),
  328 |         )
  329 | 
  330 |     def forward(self, obs: torch.Tensor) -> torch.Tensor:
  331 |         """상태 가치 추정.
  332 | 
  333 |         Args:
  334 |             obs: (batch, obs_dim) 관찰 텐서
  335 | 
  336 |         Returns:
  337 |             (batch, 1) 가치 추정값
  338 |         """
  339 |         return self.network(obs)
  340 | 
  341 | 
  342 | # ──────────────────────────────────────────────────────────────
  343 | #  통합 에이전트 래퍼
  344 | # ──────────────────────────────────────────────────────────────
  345 | 
  346 | class PitcherAgent(nn.Module):
  347 |     """투수 에이전트: Policy + Value 네트워크를 통합합니다."""
  348 | 
  349 |     def __init__(self, obs_dim: int = 6, action_dim: int = 5):
  350 |         super().__init__()
  351 |         self.policy = PitcherPolicy(obs_dim, action_dim)
  352 |         self.value = ValueNetwork(obs_dim)
  353 | 
  354 |     def get_action_and_value(
  355 |         self,
  356 |         obs: torch.Tensor,
  357 |         deterministic: bool = False,
  358 |     ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
  359 |         """액션 샘플링 + 가치 추정.
  360 | 
  361 |         Returns:
  362 |             (action, log_prob, entropy, value)
  363 |         """
  364 |         action, log_prob, entropy = self.policy.get_action(obs, deterministic)
  365 |         value = self.value(obs)
  366 |         return action, log_prob, entropy, value.squeeze(-1)
  367 | 
  368 |     def evaluate(
  369 |         self,
  370 |         obs: torch.Tensor,
  371 |         actions: torch.Tensor,
  372 |     ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
  373 |         """저장된 경험의 액션을 재평가.
  374 | 
  375 |         Returns:
  376 |             (log_prob, entropy, value)
  377 |         """
  378 |         log_prob, entropy = self.policy.evaluate_actions(obs, actions)
  379 |         value = self.value(obs)
  380 |         return log_prob, entropy, value.squeeze(-1)
  381 | 
  382 | 
  383 | class BatterAgent(nn.Module):
  384 |     """타자 에이전트: Policy(LSTM) + Value 네트워크를 통합합니다."""
  385 | 
  386 |     def __init__(self, obs_dim: int = 13, action_dim: int = 4):
  387 |         super().__init__()
  388 |         self.policy = BatterPolicy(obs_dim, action_dim)
  389 |         self.value = ValueNetwork(obs_dim)
  390 | 
  391 |     def get_action_and_value(
  392 |         self,
  393 |         obs: torch.Tensor,
  394 |         hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
  395 |         deterministic: bool = False,
  396 |     ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
  397 |         """액션 샘플링 + 가치 추정.
  398 | 
  399 |         Returns:
  400 |             (action, log_prob, entropy, value, hidden)
  401 |         """
  402 |         action, log_prob, entropy, hidden = self.policy.get_action(
  403 |             obs, hidden, deterministic
  404 |         )
  405 |         # Value는 마지막 관찰의 단일 프레임으로 추정
  406 |         if obs.dim() == 3:
  407 |             value_input = obs[:, -1, :]
  408 |         else:
  409 |             value_input = obs
  410 |         value = self.value(value_input)
  411 |         return action, log_prob, entropy, value.squeeze(-1), hidden
  412 | 
  413 |     def evaluate(
  414 |         self,
  415 |         obs: torch.Tensor,
  416 |         actions: torch.Tensor,
  417 |         hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
  418 |     ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
  419 |         """저장된 경험의 액션을 재평가.
  420 | 
  421 |         Returns:
  422 |             (log_prob, entropy, value)
  423 |         """
  424 |         log_prob, entropy = self.policy.evaluate_actions(obs, actions, hidden)
  425 |         if obs.dim() == 3:
  426 |             value_input = obs[:, -1, :]
  427 |         else:
  428 |             value_input = obs
  429 |         value = self.value(value_input)
  430 |         return log_prob, entropy, value.squeeze(-1)
````
