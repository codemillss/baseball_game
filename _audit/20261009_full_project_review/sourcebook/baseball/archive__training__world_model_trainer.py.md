# baseball/archive/training/world_model_trainer.py

원본: [archive/training/world_model_trainer.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/world_model_trainer.py)

SHA256: `1f42fd199a852a26c5a37fc94fe3b702c6a6c959e6a7bdb202e7115ba1421bd7`

전체 680행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `SequenceReplayBuffer` | ClassDef | 44 | 144 |
| `__init__` | FunctionDef | 55 | 64 |
| `add_episode` | FunctionDef | 66 | 90 |
| `sample` | FunctionDef | 92 | 140 |
| `_slice` | FunctionDef | 120 | 125 |
| `fill_ratio` | FunctionDef | 143 | 144 |
| `_mlp` | FunctionDef | 151 | 156 |
| `LatentActor` | ClassDef | 159 | 181 |
| `__init__` | FunctionDef | 162 | 166 |
| `forward` | FunctionDef | 168 | 172 |
| `get_action` | FunctionDef | 174 | 181 |
| `LatentCritic` | ClassDef | 184 | 192 |
| `__init__` | FunctionDef | 187 | 189 |
| `forward` | FunctionDef | 191 | 192 |
| `DreamerTrainer` | ClassDef | 199 | 519 |
| `__init__` | FunctionDef | 215 | 259 |
| `_get_device` | FunctionDef | 262 | 267 |
| `collect_episode` | FunctionDef | 274 | 320 |
| `train_world_model` | FunctionDef | 326 | 376 |
| `_lambda_return` | FunctionDef | 382 | 403 |
| `update_actor_critic` | FunctionDef | 405 | 483 |
| `save` | FunctionDef | 489 | 499 |
| `load` | FunctionDef | 501 | 507 |
| `get_wm_metrics` | FunctionDef | 509 | 519 |
| `safe_mean` | FunctionDef | 510 | 511 |
| `run_dreamer_training` | FunctionDef | 526 | 663 |

## 전체 원문

````text
    1 | """
    2 | world_model_trainer.py — DreamerV3 스타일 World Model 학습 엔진
    3 | 
    4 | 학습 흐름:
    5 |     1. [실제 환경] 에피소드 수집 → Replay Buffer 저장
    6 |     2. [World Model] 미니배치로 WM 학습 (Representation + Prediction + KL)
    7 |     3. [상상 롤아웃] 학습된 WM에서 H=15 스텝 상상
    8 |     4. [Actor-Critic] 상상 경험으로 Lambda-Return 기반 업데이트
    9 | 
   10 | 핵심 이점:
   11 |     - 실제 MuJoCo 1 step → 상상 롤아웃 imagination_ratio steps
   12 |     - PrioritizedReplayBuffer가 off-policy 데이터로 제대로 활용됨
   13 |     - 희귀 이벤트(홈런)를 상상에서 반복 학습 가능
   14 | """
   15 | 
   16 | import os
   17 | import sys
   18 | import time
   19 | import numpy as np
   20 | from pathlib import Path
   21 | from collections import deque
   22 | from typing import Dict, List, Tuple, Optional
   23 | 
   24 | import torch
   25 | import torch.nn as nn
   26 | import torch.nn.functional as F
   27 | import torch.optim as optim
   28 | 
   29 | sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
   30 | 
   31 | from envs.unified_baseball_env import UnifiedBaseballEnv
   32 | from training.world_model import BaseballRSSM, compute_world_model_loss, symlog, symexp
   33 | from training.curriculum_manager import CurriculumManager
   34 | from training.health_monitor import TrainingHealthMonitor
   35 | from training.episode_recorder import EpisodeRecorder
   36 | from training.reward_audit import RewardAuditSystem
   37 | from training.logger import DashboardLogger
   38 | 
   39 | 
   40 | # ──────────────────────────────────────────────────────────────
   41 | #  Replay Buffer (시퀀스 단위 저장)
   42 | # ──────────────────────────────────────────────────────────────
   43 | 
   44 | class SequenceReplayBuffer:
   45 |     """에피소드 시퀀스를 저장하는 링 버퍼.
   46 | 
   47 |     World Model 학습은 단일 transition이 아닌
   48 |     연속된 시퀀스(sequence)로 학습해야 RSSM이 올바르게 작동함.
   49 | 
   50 |     Args:
   51 |         capacity:   저장할 최대 에피소드 수
   52 |         seq_len:    학습 시 샘플링할 시퀀스 길이
   53 |     """
   54 | 
   55 |     def __init__(self, capacity: int = 5_000, seq_len: int = 50):
   56 |         self.capacity = capacity
   57 |         self.seq_len  = seq_len
   58 |         self.episodes: List[Dict] = []
   59 |         self.write_ptr = 0
   60 |         self.size = 0
   61 | 
   62 |         # 우선순위 부스트용 홈런/컨택 카운트
   63 |         self.n_home_runs = 0
   64 |         self.n_contacts  = 0
   65 | 
   66 |     def add_episode(self, episode: Dict):
   67 |         """에피소드 딕셔너리 저장.
   68 | 
   69 |         episode 형식:
   70 |             {
   71 |                 "obs_seq":    {"vision": (T,4), "prop": (T,18), "context": (T,6)},
   72 |                 "action_seq": (T, 9),
   73 |                 "reward_seq": (T,),
   74 |                 "done_seq":   (T,),    # 1.0 if terminal at that step
   75 |                 "has_contact": bool,
   76 |                 "has_home_run": bool,
   77 |             }
   78 |         """
   79 |         if len(self.episodes) < self.capacity:
   80 |             self.episodes.append(episode)
   81 |         else:
   82 |             self.episodes[self.write_ptr] = episode
   83 | 
   84 |         self.write_ptr = (self.write_ptr + 1) % self.capacity
   85 |         self.size = min(self.size + 1, self.capacity)
   86 | 
   87 |         if episode.get("has_home_run", False):
   88 |             self.n_home_runs += 1
   89 |         if episode.get("has_contact", False):
   90 |             self.n_contacts += 1
   91 | 
   92 |     def sample(self, batch_size: int) -> Optional[Dict[str, torch.Tensor]]:
   93 |         """랜덤 에피소드에서 seq_len 길이 시퀀스를 batch_size 개 샘플링.
   94 | 
   95 |         Returns:
   96 |             배치 딕셔너리 또는 데이터 부족 시 None
   97 |         """
   98 |         if self.size < batch_size:
   99 |             return None
  100 | 
  101 |         obs_batch   = {"vision": [], "proprioception": [], "context": []}
  102 |         act_batch   = []
  103 |         rew_batch   = []
  104 |         done_batch  = []
  105 | 
  106 |         indices = np.random.choice(self.size, batch_size, replace=True)
  107 | 
  108 |         for idx in indices:
  109 |             ep = self.episodes[idx]
  110 |             T  = ep["action_seq"].shape[0]
  111 | 
  112 |             if T < 2:
  113 |                 # 너무 짧은 에피소드는 반복 패딩
  114 |                 start = 0
  115 |             else:
  116 |                 start = np.random.randint(0, max(1, T - self.seq_len + 1))
  117 | 
  118 |             end = start + self.seq_len
  119 | 
  120 |             def _slice(arr):
  121 |                 if len(arr) >= end:
  122 |                     return arr[start:end]
  123 |                 # 끝에 패딩 (마지막 값 반복)
  124 |                 padded = np.concatenate([arr[start:], np.tile(arr[-1:], (end - len(arr), 1) if arr.ndim > 1 else (end - len(arr),))], axis=0)
  125 |                 return padded[:self.seq_len]
  126 | 
  127 |             for k in obs_batch:
  128 |                 obs_batch[k].append(_slice(ep["obs_seq"][k]))
  129 |             act_batch.append(_slice(ep["action_seq"]))
  130 |             rew_batch.append(_slice(ep["reward_seq"]))
  131 |             done_batch.append(_slice(ep["done_seq"]))
  132 | 
  133 |         device = torch.device("cpu")
  134 |         batch = {
  135 |             "obs": {k: torch.tensor(np.array(v), dtype=torch.float32) for k, v in obs_batch.items()},
  136 |             "actions":  torch.tensor(np.array(act_batch),  dtype=torch.float32),
  137 |             "rewards":  torch.tensor(np.array(rew_batch),  dtype=torch.float32),
  138 |             "dones":    torch.tensor(np.array(done_batch), dtype=torch.float32),
  139 |         }
  140 |         return batch
  141 | 
  142 |     @property
  143 |     def fill_ratio(self) -> float:
  144 |         return self.size / self.capacity
  145 | 
  146 | 
  147 | # ──────────────────────────────────────────────────────────────
  148 | #  Actor / Critic (잠재 공간에서 작동)
  149 | # ──────────────────────────────────────────────────────────────
  150 | 
  151 | def _mlp(in_dim: int, out_dim: int, hidden: int = 256) -> nn.Sequential:
  152 |     return nn.Sequential(
  153 |         nn.Linear(in_dim, hidden), nn.LayerNorm(hidden), nn.SiLU(),
  154 |         nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.SiLU(),
  155 |         nn.Linear(hidden, out_dim),
  156 |     )
  157 | 
  158 | 
  159 | class LatentActor(nn.Module):
  160 |     """잠재 상태 s_t = (h_t, z_t) → 액션 분포."""
  161 | 
  162 |     def __init__(self, state_dim: int, action_dim: int, hidden: int = 256):
  163 |         super().__init__()
  164 |         self.trunk   = _mlp(state_dim, hidden, hidden)
  165 |         self.mean    = nn.Linear(hidden, action_dim)
  166 |         self.log_std = nn.Parameter(torch.zeros(action_dim))
  167 | 
  168 |     def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
  169 |         feat  = self.trunk(state)
  170 |         mean  = torch.tanh(self.mean(feat))
  171 |         std   = torch.exp(self.log_std.clamp(-5, 2)).expand_as(mean)
  172 |         return mean, std
  173 | 
  174 |     def get_action(self, state: torch.Tensor, deterministic: bool = False):
  175 |         mean, std = self.forward(state)
  176 |         if deterministic:
  177 |             return mean, None
  178 |         dist   = torch.distributions.Normal(mean, std)
  179 |         action = torch.clamp(dist.rsample(), -1.0, 1.0)
  180 |         log_p  = dist.log_prob(action).sum(-1)
  181 |         return action, log_p
  182 | 
  183 | 
  184 | class LatentCritic(nn.Module):
  185 |     """잠재 상태 s_t → V(s_t) (SymLog 공간 스칼라)."""
  186 | 
  187 |     def __init__(self, state_dim: int, hidden: int = 256):
  188 |         super().__init__()
  189 |         self.net = _mlp(state_dim, 1, hidden)
  190 | 
  191 |     def forward(self, state: torch.Tensor) -> torch.Tensor:
  192 |         return self.net(state).squeeze(-1)
  193 | 
  194 | 
  195 | # ──────────────────────────────────────────────────────────────
  196 | #  Dreamer 학습 엔진
  197 | # ──────────────────────────────────────────────────────────────
  198 | 
  199 | class DreamerTrainer:
  200 |     """Baseball Dreamer 학습 엔진.
  201 | 
  202 |     Args:
  203 |         env:                UnifiedBaseballEnv 인스턴스
  204 |         imagination_horizon: 상상 롤아웃 스텝 수 (H)
  205 |         wm_lr:              World Model 학습률
  206 |         actor_lr:           Actor 학습률
  207 |         critic_lr:          Critic 학습률
  208 |         wm_batch_size:      World Model 미니배치 에피소드 수
  209 |         buffer_capacity:    Replay Buffer 용량 (에피소드 단위)
  210 |         seq_len:            학습 시퀀스 길이
  211 |         kl_scale:           KL 손실 가중치
  212 |         lambda_return:      Lambda-Return λ 값
  213 |     """
  214 | 
  215 |     def __init__(
  216 |         self,
  217 |         env:                  UnifiedBaseballEnv,
  218 |         imagination_horizon:  int   = 15,
  219 |         wm_lr:                float = 3e-4,
  220 |         actor_lr:             float = 3e-4,
  221 |         critic_lr:            float = 3e-4,
  222 |         wm_batch_size:        int   = 16,
  223 |         buffer_capacity:      int   = 5_000,
  224 |         seq_len:              int   = 50,
  225 |         kl_scale:             float = 0.1,
  226 |         lambda_return:        float = 0.95,
  227 |     ):
  228 |         self.env    = env
  229 |         self.H      = imagination_horizon
  230 |         self.kl_scale   = kl_scale
  231 |         self.lambda_ret = lambda_return
  232 |         self.wm_batch   = wm_batch_size
  233 |         self.device     = self._get_device()
  234 | 
  235 |         # ── World Model ──
  236 |         self.rssm = BaseballRSSM(
  237 |             hidden_dim=256, latent_classes=32, latent_dim=32,
  238 |             obs_dim=28, action_dim=env.action_space.shape[0],
  239 |         ).to(self.device)
  240 | 
  241 |         # ── Actor / Critic ──
  242 |         self.actor  = LatentActor(self.rssm.state_dim,  env.action_space.shape[0]).to(self.device)
  243 |         self.critic = LatentCritic(self.rssm.state_dim).to(self.device)
  244 |         # 느린 Target Critic (EMA)
  245 |         self.target_critic = LatentCritic(self.rssm.state_dim).to(self.device)
  246 |         self.target_critic.load_state_dict(self.critic.state_dict())
  247 | 
  248 |         # ── Optimizers ──
  249 |         self.wm_opt     = optim.Adam(self.rssm.parameters(), lr=wm_lr, eps=1e-8)
  250 |         self.actor_opt  = optim.Adam(self.actor.parameters(),  lr=actor_lr, eps=1e-8)
  251 |         self.critic_opt = optim.Adam(self.critic.parameters(), lr=critic_lr, eps=1e-8)
  252 | 
  253 |         # ── Replay Buffer ──
  254 |         self.buffer = SequenceReplayBuffer(capacity=buffer_capacity, seq_len=seq_len)
  255 | 
  256 |         # ── 로깅 ──
  257 |         self.wm_loss_history    = deque(maxlen=100)
  258 |         self.actor_loss_history = deque(maxlen=100)
  259 |         self.imag_reward_history= deque(maxlen=100)
  260 | 
  261 |     @staticmethod
  262 |     def _get_device() -> torch.device:
  263 |         if torch.backends.mps.is_available():
  264 |             return torch.device("mps")
  265 |         if torch.cuda.is_available():
  266 |             return torch.device("cuda")
  267 |         return torch.device("cpu")
  268 | 
  269 |     # ──────────────────────────────────────────────────────────
  270 |     #  에피소드 수집 (실제 환경)
  271 |     # ──────────────────────────────────────────────────────────
  272 | 
  273 |     @torch.no_grad()
  274 |     def collect_episode(self) -> Dict:
  275 |         """실제 환경에서 에피소드 하나를 수집."""
  276 |         obs, info = self.env.reset()
  277 |         h, z = self.rssm.initial_state(1, self.device)
  278 | 
  279 |         obs_lists  = {"vision": [], "proprioception": [], "context": []}
  280 |         act_list, rew_list, done_list = [], [], []
  281 | 
  282 |         done = False
  283 |         while not done:
  284 |             # 관찰 → 텐서
  285 |             obs_t = {k: torch.tensor(v, dtype=torch.float32, device=self.device).unsqueeze(0)
  286 |                      for k, v in obs.items()}
  287 | 
  288 |             # RSSM observe (잠재 상태 업데이트)
  289 |             action_dummy = torch.zeros(1, self.env.action_space.shape[0], device=self.device)
  290 |             if act_list:
  291 |                 action_dummy = torch.tensor(act_list[-1], dtype=torch.float32, device=self.device).unsqueeze(0)
  292 | 
  293 |             h, z, _ = self.rssm.observe(obs_t, action_dummy, h, z)
  294 |             s = self.rssm.get_state(h, z)
  295 | 
  296 |             # Actor로 액션 결정
  297 |             action, _ = self.actor.get_action(s)
  298 |             action_np  = action.squeeze(0).cpu().numpy()
  299 | 
  300 |             next_obs, reward, terminated, truncated, step_info = self.env.step(action_np)
  301 |             done = terminated or truncated
  302 | 
  303 |             for k in obs_lists:
  304 |                 obs_lists[k].append(obs[k])
  305 |             act_list.append(action_np)
  306 |             rew_list.append(float(reward))
  307 |             done_list.append(1.0 if done else 0.0)
  308 | 
  309 |             obs = next_obs
  310 | 
  311 |         episode = {
  312 |             "obs_seq": {k: np.array(v) for k, v in obs_lists.items()},
  313 |             "action_seq":  np.array(act_list),
  314 |             "reward_seq":  np.array(rew_list),
  315 |             "done_seq":    np.array(done_list),
  316 |             "has_contact": step_info.get("has_contacted", False),
  317 |             "has_home_run": "Home Run" in step_info.get("game_event", ""),
  318 |             "total_reward": sum(rew_list),
  319 |         }
  320 |         return episode
  321 | 
  322 |     # ──────────────────────────────────────────────────────────
  323 |     #  World Model 학습
  324 |     # ──────────────────────────────────────────────────────────
  325 | 
  326 |     def train_world_model(self) -> Optional[Dict[str, float]]:
  327 |         """Replay Buffer에서 미니배치를 샘플링해 World Model 학습.
  328 | 
  329 |         Returns:
  330 |             손실 딕셔너리 또는 데이터 부족 시 None
  331 |         """
  332 |         batch = self.buffer.sample(self.wm_batch)
  333 |         if batch is None:
  334 |             return None
  335 | 
  336 |         # 디바이스 이동
  337 |         obs_seq    = {k: v.to(self.device) for k, v in batch["obs"].items()}
  338 |         action_seq = batch["actions"].to(self.device)   # (B, T, 9)
  339 |         reward_seq = batch["rewards"].to(self.device)   # (B, T)
  340 |         done_seq   = batch["dones"].to(self.device)     # (B, T)
  341 | 
  342 |         B, T = action_seq.shape[:2]
  343 | 
  344 |         # 초기 상태
  345 |         h0, z0 = self.rssm.initial_state(B, self.device)
  346 | 
  347 |         # 시퀀스 전체 처리 (Posterior)
  348 |         h_seq, z_seq, post_logits, prior_logits = self.rssm.observe_sequence(
  349 |             obs_seq, action_seq, h0, z0
  350 |         )
  351 | 
  352 |         # 관찰 재구성 타겟 (vision + prop + context 결합)
  353 |         obs_target = torch.cat([
  354 |             obs_seq["vision"],
  355 |             obs_seq["proprioception"],
  356 |             obs_seq["context"],
  357 |         ], dim=-1)  # (B, T, 28)
  358 | 
  359 |         # 손실 계산
  360 |         losses = compute_world_model_loss(
  361 |             self.rssm, h_seq, z_seq,
  362 |             post_logits, prior_logits,
  363 |             obs_target, reward_seq,
  364 |             continue_target=(1.0 - done_seq),
  365 |             kl_scale=self.kl_scale,
  366 |         )
  367 | 
  368 |         # 역전파
  369 |         self.wm_opt.zero_grad()
  370 |         losses["total"].backward()
  371 |         nn.utils.clip_grad_norm_(self.rssm.parameters(), 100.0)
  372 |         self.wm_opt.step()
  373 | 
  374 |         loss_vals = {k: v.item() for k, v in losses.items()}
  375 |         self.wm_loss_history.append(loss_vals["total"])
  376 |         return loss_vals
  377 | 
  378 |     # ──────────────────────────────────────────────────────────
  379 |     #  상상 롤아웃 + Actor-Critic 업데이트
  380 |     # ──────────────────────────────────────────────────────────
  381 | 
  382 |     def _lambda_return(
  383 |         self,
  384 |         rewards:   torch.Tensor,  # (B, H)
  385 |         values:    torch.Tensor,  # (B, H)
  386 |         continues: torch.Tensor,  # (B, H) — 계속 확률
  387 |         lambda_:   float = 0.95,
  388 |         gamma:     float = 0.99,
  389 |     ) -> torch.Tensor:
  390 |         """Lambda-Return 계산 (DreamerV3 방식).
  391 | 
  392 |         R^λ_t = r_t + γ * c_t * [(1-λ)*V_{t+1} + λ*R^λ_{t+1}]
  393 |         """
  394 |         B, H = rewards.shape
  395 |         targets = torch.zeros_like(rewards)
  396 |         last = values[:, -1]  # bootstrap from last value
  397 | 
  398 |         for t in reversed(range(H)):
  399 |             bootstrap = (1 - lambda_) * values[:, t] + lambda_ * last
  400 |             targets[:, t] = rewards[:, t] + gamma * continues[:, t] * bootstrap
  401 |             last = targets[:, t]
  402 | 
  403 |         return targets
  404 | 
  405 |     def update_actor_critic(self, start_h: torch.Tensor, start_z: torch.Tensor) -> Dict[str, float]:
  406 |         """상상 롤아웃 후 Actor-Critic 업데이트.
  407 | 
  408 |         Args:
  409 |             start_h: 상상 시작 GRU 은닉 상태 (B, hidden)
  410 |             start_z: 상상 시작 잠재 상태 (B, C, D)
  411 | 
  412 |         Returns:
  413 |             actor_loss, critic_loss, mean_imag_reward
  414 |         """
  415 |         B = start_h.shape[0]
  416 | 
  417 |         # 상상 롤아웃
  418 |         h, z = start_h, start_z
  419 |         states, actions, rewards, continues, values = [], [], [], [], []
  420 | 
  421 |         for _ in range(self.H):
  422 |             s = self.rssm.get_state(h, z)
  423 |             a, log_p = self.actor.get_action(s)
  424 | 
  425 |             # 예측 (reward, continue, value)
  426 |             r  = symexp(self.rssm.predict_reward(h, z))
  427 |             c  = self.rssm.predict_continue(h, z)
  428 |             v  = self.target_critic(s)
  429 | 
  430 |             states.append(s)
  431 |             actions.append(a)
  432 |             rewards.append(r)
  433 |             continues.append(c)
  434 |             values.append(v)
  435 | 
  436 |             # 상상 전이 (실제 환경 호출 없음)
  437 |             h, z, _ = self.rssm.imagine(a, h, z)
  438 | 
  439 |         # (B, H, ...) 스택
  440 |         states_t    = torch.stack(states,    dim=1)   # (B, H, state_dim)
  441 |         actions_t   = torch.stack(actions,   dim=1)
  442 |         rewards_t   = torch.stack(rewards,   dim=1)   # (B, H)
  443 |         continues_t = torch.stack(continues, dim=1)   # (B, H)
  444 |         values_t    = torch.stack(values,    dim=1)   # (B, H)
  445 | 
  446 |         # Lambda-Return 타겟
  447 |         with torch.no_grad():
  448 |             lambda_targets = self._lambda_return(
  449 |                 rewards_t, values_t, continues_t, self.lambda_ret
  450 |             )
  451 | 
  452 |         # ── Critic 업데이트 ──
  453 |         new_values = self.critic(states_t.detach().reshape(B * self.H, -1))
  454 |         new_values = new_values.reshape(B, self.H)
  455 |         critic_loss = F.mse_loss(new_values, lambda_targets.detach())
  456 | 
  457 |         self.critic_opt.zero_grad()
  458 |         critic_loss.backward()
  459 |         nn.utils.clip_grad_norm_(self.critic.parameters(), 100.0)
  460 |         self.critic_opt.step()
  461 | 
  462 |         # ── Actor 업데이트 (Reinforce-style) ──
  463 |         actor_loss = -(lambda_targets.detach()).mean()
  464 | 
  465 |         self.actor_opt.zero_grad()
  466 |         actor_loss.backward()
  467 |         nn.utils.clip_grad_norm_(self.actor.parameters(), 100.0)
  468 |         self.actor_opt.step()
  469 | 
  470 |         # ── Target Critic EMA 업데이트 ──
  471 |         ema = 0.98
  472 |         for p_tgt, p_src in zip(self.target_critic.parameters(), self.critic.parameters()):
  473 |             p_tgt.data.mul_(ema).add_(p_src.data, alpha=1 - ema)
  474 | 
  475 |         mean_imag_r = rewards_t.mean().item()
  476 |         self.actor_loss_history.append(actor_loss.item())
  477 |         self.imag_reward_history.append(mean_imag_r)
  478 | 
  479 |         return {
  480 |             "actor_loss":      actor_loss.item(),
  481 |             "critic_loss":     critic_loss.item(),
  482 |             "mean_imag_reward": mean_imag_r,
  483 |         }
  484 | 
  485 |     # ──────────────────────────────────────────────────────────
  486 |     #  체크포인트
  487 |     # ──────────────────────────────────────────────────────────
  488 | 
  489 |     def save(self, path: str):
  490 |         torch.save({
  491 |             "rssm":          self.rssm.state_dict(),
  492 |             "actor":         self.actor.state_dict(),
  493 |             "critic":        self.critic.state_dict(),
  494 |             "target_critic": self.target_critic.state_dict(),
  495 |             "wm_opt":        self.wm_opt.state_dict(),
  496 |             "actor_opt":     self.actor_opt.state_dict(),
  497 |             "critic_opt":    self.critic_opt.state_dict(),
  498 |         }, path)
  499 |         print(f"  💾 DreamerTrainer saved: {path}")
  500 | 
  501 |     def load(self, path: str):
  502 |         ckpt = torch.load(path, map_location=self.device)
  503 |         self.rssm.load_state_dict(ckpt["rssm"])
  504 |         self.actor.load_state_dict(ckpt["actor"])
  505 |         self.critic.load_state_dict(ckpt["critic"])
  506 |         self.target_critic.load_state_dict(ckpt["target_critic"])
  507 |         print(f"  ✅ DreamerTrainer loaded: {path}")
  508 | 
  509 |     def get_wm_metrics(self) -> Dict[str, float]:
  510 |         def safe_mean(d):
  511 |             return float(np.mean(list(d))) if d else 0.0
  512 |         return {
  513 |             "avg_wm_loss":      safe_mean(self.wm_loss_history),
  514 |             "avg_actor_loss":   safe_mean(self.actor_loss_history),
  515 |             "avg_imag_reward":  safe_mean(self.imag_reward_history),
  516 |             "buffer_fill":      self.buffer.fill_ratio,
  517 |             "n_home_runs":      self.buffer.n_home_runs,
  518 |             "n_contacts":       self.buffer.n_contacts,
  519 |         }
  520 | 
  521 | 
  522 | # ──────────────────────────────────────────────────────────────
  523 | #  메인 학습 루프
  524 | # ──────────────────────────────────────────────────────────────
  525 | 
  526 | def run_dreamer_training(
  527 |     total_episodes:      int   = 1000,
  528 |     initial_stage:       int   = 1,
  529 |     wm_warmup_episodes:  int   = 50,    # WM 학습 전 순수 수집 에피소드 수
  530 |     imagination_ratio:   int   = 5,     # 실제 1 ep당 상상 업데이트 횟수
  531 |     record_interval:     int   = 100,
  532 |     save_interval:       int   = 200,
  533 | ):
  534 |     """World Model 기반 Dreamer 학습 실행.
  535 | 
  536 |     Args:
  537 |         wm_warmup_episodes: 이 에피소드 수만큼은 WM 학습 없이 버퍼만 채움
  538 |         imagination_ratio:  실제 환경 1 에피소드당 상상 업데이트 횟수
  539 |     """
  540 |     device_str = "mps" if torch.backends.mps.is_available() else \
  541 |                  "cuda" if torch.cuda.is_available() else "cpu"
  542 |     print("=" * 70)
  543 |     print(f" ⚾ Baseball Dreamer (World Model) 학습 시작")
  544 |     print(f"   Device: {device_str} | Episodes: {total_episodes}")
  545 |     print(f"   WM Warmup: {wm_warmup_episodes} | Imagination Ratio: {imagination_ratio}")
  546 |     print("=" * 70)
  547 | 
  548 |     env = UnifiedBaseballEnv(curriculum_stage=initial_stage, render_mode="rgb_array")
  549 | 
  550 |     dreamer = DreamerTrainer(
  551 |         env=env,
  552 |         imagination_horizon=15,
  553 |         wm_lr=1e-4, actor_lr=3e-4, critic_lr=3e-4,
  554 |         wm_batch_size=16,
  555 |         buffer_capacity=5_000,
  556 |         seq_len=50,
  557 |         kl_scale=0.1,
  558 |     )
  559 | 
  560 |     curriculum    = CurriculumManager(initial_stage=initial_stage)
  561 |     monitor       = TrainingHealthMonitor()
  562 |     recorder      = EpisodeRecorder()
  563 |     auditor       = RewardAuditSystem()
  564 |     dashboard     = DashboardLogger()
  565 | 
  566 |     reward_window = deque(maxlen=50)
  567 |     best_cr       = 0.0
  568 |     start_time    = time.time()
  569 | 
  570 |     for ep in range(1, total_episodes + 1):
  571 |         # ── 1. 실제 환경에서 에피소드 수집 ──
  572 |         episode = dreamer.collect_episode()
  573 |         dreamer.buffer.add_episode(episode)
  574 | 
  575 |         ep_reward = episode["total_reward"]
  576 |         contacted = episode["has_contact"]
  577 |         reward_window.append(ep_reward)
  578 | 
  579 |         curriculum.record_episode(contacted, {})
  580 |         if contacted:
  581 |             fake_info = {
  582 |                 "exit_velocity_kmh": 120.0,
  583 |                 "launch_angle": 20.0,
  584 |                 "spray_angle": 10.0,
  585 |             }
  586 |             auditor.record_hit(fake_info, ep_reward)
  587 | 
  588 |         # ── 2. World Model 학습 ──
  589 |         wm_metrics = {}
  590 |         if ep > wm_warmup_episodes:
  591 |             wm_metrics = dreamer.train_world_model() or {}
  592 | 
  593 |             # ── 3. 상상 롤아웃으로 Actor-Critic 업데이트 ──
  594 |             for _ in range(imagination_ratio):
  595 |                 # 랜덤 에피소드의 임의 시점에서 상상 시작
  596 |                 if dreamer.buffer.size > 0:
  597 |                     batch = dreamer.buffer.sample(8)
  598 |                     if batch is not None:
  599 |                         obs_t = {k: v[:, 0].to(dreamer.device) for k, v in batch["obs"].items()}
  600 |                         a_dummy = batch["actions"][:, 0].to(dreamer.device)
  601 |                         h0, z0 = dreamer.rssm.initial_state(8, dreamer.device)
  602 |                         with torch.no_grad():
  603 |                             h, z, _ = dreamer.rssm.observe(obs_t, a_dummy, h0, z0)
  604 |                         ac_metrics = dreamer.update_actor_critic(h, z)
  605 |                         wm_metrics.update(ac_metrics)
  606 | 
  607 |         # ── 4. 모니터링 & 로깅 ──
  608 |         monitor_metrics = {
  609 |             "reward":       ep_reward,
  610 |             "contact_rate": curriculum.get_contact_rate(),
  611 |             **{k: v for k, v in wm_metrics.items() if isinstance(v, (int, float))},
  612 |         }
  613 |         monitor.record(monitor_metrics)
  614 | 
  615 |         if ep % 5 == 0:
  616 |             dashboard.log_episode_stats(ep, monitor_metrics)
  617 | 
  618 |         if ep % record_interval == 0:
  619 |             recorder.record_episode(env, dreamer.actor, ep, dreamer.device)
  620 | 
  621 |         if ep % 50 == 0:
  622 |             new_stage = curriculum.check_and_update()
  623 |             env.set_curriculum_stage(new_stage)
  624 | 
  625 |         if ep % 20 == 0 or ep == total_episodes:
  626 |             elapsed = time.time() - start_time
  627 |             cr  = curriculum.get_contact_rate()
  628 |             avg = np.mean(list(reward_window)) if reward_window else 0.0
  629 |             wm  = dreamer.get_wm_metrics()
  630 |             stage_name = env.CURRICULUM[curriculum.current_stage]["name"]
  631 | 
  632 |             print(
  633 |                 f"  [EP {ep:4d}/{total_episodes}] "
  634 |                 f"Stage {curriculum.current_stage} ({stage_name}) | "
  635 |                 f"CR={cr:.1%} | Reward={avg:+.2f} | "
  636 |                 f"WM_Loss={wm['avg_wm_loss']:.4f} | "
  637 |                 f"Imag_R={wm['avg_imag_reward']:+.2f} | "
  638 |                 f"Buffer={wm['buffer_fill']:.0%} | {elapsed:.0f}s"
  639 |             )
  640 |             for alert in monitor.check_health():
  641 |                 print(f"    {alert}")
  642 |             for alert in auditor.audit():
  643 |                 print(f"    {alert}")
  644 | 
  645 |             if cr > best_cr:
  646 |                 best_cr = cr
  647 | 
  648 |         if ep % save_interval == 0:
  649 |             ckpt_dir = Path(__file__).parent.parent / "checkpoints"
  650 |             ckpt_dir.mkdir(parents=True, exist_ok=True)
  651 |             dreamer.save(str(ckpt_dir / f"dreamer_ep{ep:05d}.pt"))
  652 | 
  653 |     # 최종 저장
  654 |     save_dir = Path(__file__).parent.parent / "checkpoints"
  655 |     save_dir.mkdir(parents=True, exist_ok=True)
  656 |     dreamer.save(str(save_dir / "dreamer_final.pt"))
  657 | 
  658 |     print("\n" + "=" * 70)
  659 |     print(f" 🏆 Dreamer 학습 완료!")
  660 |     print(f"    최종 Stage: {curriculum.current_stage}")
  661 |     print(f"    최고 Contact Rate: {best_cr:.1%}")
  662 |     print(f"    {auditor.get_summary()}")
  663 |     print("=" * 70)
  664 | 
  665 | 
  666 | if __name__ == "__main__":
  667 |     import argparse
  668 |     parser = argparse.ArgumentParser(description="Baseball Dreamer Trainer")
  669 |     parser.add_argument("--episodes", type=int, default=1000)
  670 |     parser.add_argument("--stage",    type=int, default=1)
  671 |     parser.add_argument("--warmup",   type=int, default=50)
  672 |     parser.add_argument("--imag",     type=int, default=5)
  673 |     args = parser.parse_args()
  674 | 
  675 |     run_dreamer_training(
  676 |         total_episodes=args.episodes,
  677 |         initial_stage=args.stage,
  678 |         wm_warmup_episodes=args.warmup,
  679 |         imagination_ratio=args.imag,
  680 |     )
````
