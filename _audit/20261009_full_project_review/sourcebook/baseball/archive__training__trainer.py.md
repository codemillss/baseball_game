# baseball/archive/training/trainer.py

원본: [archive/training/trainer.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/trainer.py)

SHA256: `baca9f1f52c708b3ea67b577413a1719ef44e00feb560eb2b73cd549daf5c783`

전체 748행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `TrainingConfig` | ClassDef | 40 | 70 |
| `ScriptedPitcherBot` | ClassDef | 77 | 110 |
| `__init__` | FunctionDef | 83 | 88 |
| `get_action` | FunctionDef | 90 | 110 |
| `ScriptedBatterBot` | ClassDef | 113 | 155 |
| `__init__` | FunctionDef | 119 | 120 |
| `get_action` | FunctionDef | 122 | 155 |
| `PPOUpdater` | ClassDef | 162 | 291 |
| `__init__` | FunctionDef | 165 | 167 |
| `compute_gae` | FunctionDef | 169 | 202 |
| `ppo_update` | FunctionDef | 204 | 291 |
| `SelfPlayTrainer` | ClassDef | 298 | 717 |
| `__init__` | FunctionDef | 305 | 352 |
| `_get_opponent_action` | FunctionDef | 354 | 413 |
| `_snapshot_agent` | FunctionDef | 415 | 426 |
| `_collect_episode` | FunctionDef | 428 | 558 |
| `_update_agent` | FunctionDef | 560 | 608 |
| `train` | FunctionDef | 610 | 645 |
| `_log_progress` | FunctionDef | 647 | 692 |
| `_save_checkpoint` | FunctionDef | 694 | 706 |
| `load_checkpoint` | FunctionDef | 708 | 717 |
| `main` | FunctionDef | 724 | 744 |

## 전체 원문

````text
    1 | """
    2 | trainer.py — Self-Play PPO 학습 엔진
    3 | 
    4 | 투수/타자 에이전트를 Self-Play 방식으로 교대 학습합니다.
    5 | League Training 기반 적대적 학습 + Curriculum 난이도 조절.
    6 | 
    7 | 학습 흐름:
    8 |     1. Warm-up: Scripted Bot 상대로 기초 학습
    9 |     2. Self-Play: 현재 정책 vs 과거 체크포인트
   10 |     3. League: 최강 체크포인트 풀에서 랜덤 상대 선택
   11 | """
   12 | 
   13 | import os
   14 | import json
   15 | import copy
   16 | import time
   17 | import numpy as np
   18 | from pathlib import Path
   19 | from collections import deque
   20 | from typing import Optional, Dict, List, Tuple
   21 | 
   22 | import torch
   23 | import torch.nn as nn
   24 | import torch.optim as optim
   25 | 
   26 | from training.networks import PitcherAgent, BatterAgent, get_device
   27 | from training.replay_buffer import (
   28 |     PrioritizedReplayBuffer,
   29 |     Transition,
   30 |     transitions_to_batch,
   31 | )
   32 | from envs.baseball_game_env import BaseballGameEnv
   33 | from simulator.dashboard import save_pitch_data, save_training_metrics
   34 | 
   35 | 
   36 | # ──────────────────────────────────────────────────────────────
   37 | #  학습 설정
   38 | # ──────────────────────────────────────────────────────────────
   39 | 
   40 | class TrainingConfig:
   41 |     """학습 하이퍼파라미터."""
   42 | 
   43 |     # PPO
   44 |     lr: float = 3e-4
   45 |     gamma: float = 0.99
   46 |     gae_lambda: float = 0.95
   47 |     clip_eps: float = 0.2
   48 |     entropy_coef: float = 0.01
   49 |     value_coef: float = 0.5
   50 |     max_grad_norm: float = 0.5
   51 | 
   52 |     # 배치
   53 |     batch_size: int = 64
   54 |     n_epochs: int = 4           # 미니배치 에폭
   55 |     n_steps_per_update: int = 128  # 업데이트 당 스텝 수
   56 | 
   57 |     # Self-Play
   58 |     opponent_pool_size: int = 10
   59 |     snapshot_interval: int = 50    # 체크포인트 스냅샷 간격 (에피소드)
   60 |     opponent_sample_latest_prob: float = 0.7  # 최신 체크포인트 선택 확률
   61 | 
   62 |     # Curriculum
   63 |     warmup_episodes: int = 100
   64 |     curriculum_phases: int = 3
   65 | 
   66 |     # Logging
   67 |     log_interval: int = 10
   68 |     save_interval: int = 100
   69 |     checkpoint_dir: str = "checkpoints"
   70 |     data_dir: str = "data"
   71 | 
   72 | 
   73 | # ──────────────────────────────────────────────────────────────
   74 | #  Scripted Bot (Warm-up 상대)
   75 | # ──────────────────────────────────────────────────────────────
   76 | 
   77 | class ScriptedPitcherBot:
   78 |     """규칙 기반 투수 봇 (Warm-up 학습용).
   79 | 
   80 |     직구 위주로 스트라이크존 중앙에 던집니다.
   81 |     """
   82 | 
   83 |     def __init__(self, difficulty: float = 0.5):
   84 |         """
   85 |         Args:
   86 |             difficulty: 난이도 (0=쉬움, 1=어려움)
   87 |         """
   88 |         self.difficulty = difficulty
   89 | 
   90 |     def get_action(self, obs: np.ndarray) -> np.ndarray:
   91 |         """규칙 기반 투구 액션을 생성합니다.
   92 | 
   93 |         Args:
   94 |             obs: 투수 관찰 벡터
   95 | 
   96 |         Returns:
   97 |             (5,) 액션 벡터
   98 |         """
   99 |         noise_scale = 0.3 * (1.0 - self.difficulty)
  100 | 
  101 |         # 기본: 중앙 직구
  102 |         v_release = 0.3 + 0.3 * self.difficulty  # 속도
  103 |         target_x = np.random.normal(0.0, noise_scale)  # 좌우
  104 |         target_z = np.random.normal(0.0, noise_scale)  # 상하
  105 |         spin_rate = 0.2  # 중간 스핀
  106 |         spin_axis = np.random.uniform(-0.3, 0.3)  # 약간의 변화
  107 | 
  108 |         action = np.array([v_release, target_x, target_z, spin_rate, spin_axis],
  109 |                          dtype=np.float32)
  110 |         return np.clip(action, -1.0, 1.0)
  111 | 
  112 | 
  113 | class ScriptedBatterBot:
  114 |     """규칙 기반 타자 봇 (Warm-up 학습용).
  115 | 
  116 |     스트라이크존에 오는 공에 대해 단순 스윙합니다.
  117 |     """
  118 | 
  119 |     def __init__(self, difficulty: float = 0.5):
  120 |         self.difficulty = difficulty
  121 | 
  122 |     def get_action(self, obs: np.ndarray) -> np.ndarray:
  123 |         """규칙 기반 스윙 액션을 생성합니다.
  124 | 
  125 |         Args:
  126 |             obs: 타자 관찰 벡터 (13,)
  127 | 
  128 |         Returns:
  129 |             (4,) 액션 벡터
  130 |         """
  131 |         ball_pos = obs[:3]
  132 |         ball_vel = obs[3:6]
  133 |         time_to_plate = obs[12] if len(obs) > 12 else 0.5
  134 | 
  135 |         noise_scale = 0.3 * (1.0 - self.difficulty)
  136 | 
  137 |         # 간단한 판정: 공이 스트라이크존 근처로 향하면 스윙
  138 |         predicted_x = ball_pos[0] + ball_vel[0] * time_to_plate
  139 |         predicted_z = ball_pos[2] + ball_vel[2] * time_to_plate
  140 | 
  141 |         in_zone = (-0.3 <= predicted_x <= 0.3 and 0.3 <= predicted_z <= 1.2)
  142 | 
  143 |         if in_zone:
  144 |             trigger = 0.5 + np.random.normal(0, noise_scale)
  145 |             yaw = np.random.normal(0.3, noise_scale)    # 투수 방향으로 스윙
  146 |             pitch = np.random.normal(0.0, noise_scale)
  147 |             height = predicted_z / 1.3 * 2 - 1  # 높이 매핑
  148 |         else:
  149 |             trigger = -0.5  # 스윙 안 함
  150 |             yaw = 0.0
  151 |             pitch = 0.0
  152 |             height = 0.0
  153 | 
  154 |         action = np.array([trigger, yaw, pitch, height], dtype=np.float32)
  155 |         return np.clip(action, -1.0, 1.0)
  156 | 
  157 | 
  158 | # ──────────────────────────────────────────────────────────────
  159 | #  PPO 업데이트 로직
  160 | # ──────────────────────────────────────────────────────────────
  161 | 
  162 | class PPOUpdater:
  163 |     """PPO 알고리즘 업데이트를 수행합니다."""
  164 | 
  165 |     def __init__(self, config: TrainingConfig, device: torch.device):
  166 |         self.config = config
  167 |         self.device = device
  168 | 
  169 |     def compute_gae(
  170 |         self,
  171 |         rewards: np.ndarray,
  172 |         values: np.ndarray,
  173 |         next_value: float,
  174 |         dones: np.ndarray,
  175 |     ) -> Tuple[np.ndarray, np.ndarray]:
  176 |         """Generalized Advantage Estimation (GAE)를 계산합니다.
  177 | 
  178 |         Args:
  179 |             rewards: (T,) 보상 배열
  180 |             values: (T,) 가치 추정 배열
  181 |             next_value: 마지막 다음 상태의 가치
  182 |             dones: (T,) 종료 플래그
  183 | 
  184 |         Returns:
  185 |             (advantages, returns)
  186 |         """
  187 |         T = len(rewards)
  188 |         advantages = np.zeros(T, dtype=np.float32)
  189 |         gae = 0.0
  190 | 
  191 |         for t in reversed(range(T)):
  192 |             if t == T - 1:
  193 |                 next_val = next_value
  194 |             else:
  195 |                 next_val = values[t + 1]
  196 | 
  197 |             delta = rewards[t] + self.config.gamma * next_val * (1 - dones[t]) - values[t]
  198 |             gae = delta + self.config.gamma * self.config.gae_lambda * (1 - dones[t]) * gae
  199 |             advantages[t] = gae
  200 | 
  201 |         returns = advantages + values
  202 |         return advantages, returns
  203 | 
  204 |     def ppo_update(
  205 |         self,
  206 |         agent: nn.Module,
  207 |         optimizer: optim.Optimizer,
  208 |         obs: torch.Tensor,
  209 |         actions: torch.Tensor,
  210 |         old_log_probs: torch.Tensor,
  211 |         advantages: torch.Tensor,
  212 |         returns: torch.Tensor,
  213 |         is_batter: bool = False,
  214 |     ) -> dict:
  215 |         """PPO Clipped Objective 업데이트를 수행합니다.
  216 | 
  217 |         Args:
  218 |             agent: PitcherAgent 또는 BatterAgent
  219 |             optimizer: Adam 옵티마이저
  220 |             obs: 관찰 텐서
  221 |             actions: 액션 텐서
  222 |             old_log_probs: 이전 로그 확률
  223 |             advantages: GAE 어드밴티지
  224 |             returns: 타겟 리턴
  225 |             is_batter: 타자 에이전트 여부
  226 | 
  227 |         Returns:
  228 |             학습 메트릭 딕셔너리
  229 |         """
  230 |         cfg = self.config
  231 |         total_policy_loss = 0
  232 |         total_value_loss = 0
  233 |         total_entropy = 0
  234 |         n_updates = 0
  235 | 
  236 |         # 어드밴티지 정규화
  237 |         advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
  238 | 
  239 |         dataset_size = obs.size(0)
  240 |         indices = np.arange(dataset_size)
  241 | 
  242 |         for epoch in range(cfg.n_epochs):
  243 |             np.random.shuffle(indices)
  244 | 
  245 |             for start in range(0, dataset_size, cfg.batch_size):
  246 |                 end = min(start + cfg.batch_size, dataset_size)
  247 |                 batch_idx = indices[start:end]
  248 | 
  249 |                 b_obs = obs[batch_idx]
  250 |                 b_actions = actions[batch_idx]
  251 |                 b_old_log_probs = old_log_probs[batch_idx]
  252 |                 b_advantages = advantages[batch_idx]
  253 |                 b_returns = returns[batch_idx]
  254 | 
  255 |                 # 현재 정책으로 재평가
  256 |                 new_log_probs, entropy, values = agent.evaluate(b_obs, b_actions)
  257 | 
  258 |                 # PPO Clipped 목적함수
  259 |                 ratio = torch.exp(new_log_probs - b_old_log_probs)
  260 |                 surr1 = ratio * b_advantages
  261 |                 surr2 = torch.clamp(ratio, 1 - cfg.clip_eps, 1 + cfg.clip_eps) * b_advantages
  262 |                 policy_loss = -torch.min(surr1, surr2).mean()
  263 | 
  264 |                 # Value 손실
  265 |                 value_loss = nn.functional.mse_loss(values, b_returns)
  266 | 
  267 |                 # Entropy 보너스
  268 |                 entropy_loss = -entropy.mean()
  269 | 
  270 |                 # 총 손실
  271 |                 loss = (
  272 |                     policy_loss
  273 |                     + cfg.value_coef * value_loss
  274 |                     + cfg.entropy_coef * entropy_loss
  275 |                 )
  276 | 
  277 |                 optimizer.zero_grad()
  278 |                 loss.backward()
  279 |                 nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)
  280 |                 optimizer.step()
  281 | 
  282 |                 total_policy_loss += policy_loss.item()
  283 |                 total_value_loss += value_loss.item()
  284 |                 total_entropy += (-entropy_loss).item()
  285 |                 n_updates += 1
  286 | 
  287 |         return {
  288 |             'policy_loss': total_policy_loss / max(n_updates, 1),
  289 |             'value_loss': total_value_loss / max(n_updates, 1),
  290 |             'entropy': total_entropy / max(n_updates, 1),
  291 |         }
  292 | 
  293 | 
  294 | # ──────────────────────────────────────────────────────────────
  295 | #  Self-Play 학습 엔진
  296 | # ──────────────────────────────────────────────────────────────
  297 | 
  298 | class SelfPlayTrainer:
  299 |     """Self-Play League Training 엔진.
  300 | 
  301 |     투수/타자 에이전트를 교대로 학습시키며,
  302 |     과거 체크포인트 풀에서 상대를 선택합니다.
  303 |     """
  304 | 
  305 |     def __init__(
  306 |         self,
  307 |         config: Optional[TrainingConfig] = None,
  308 |         max_episodes: int = 10000,
  309 |     ):
  310 |         self.config = config or TrainingConfig()
  311 |         self.max_episodes = max_episodes
  312 |         self.device = get_device()
  313 | 
  314 |         # 에이전트 초기화
  315 |         self.pitcher_agent = PitcherAgent().to(self.device)
  316 |         self.batter_agent = BatterAgent().to(self.device)
  317 | 
  318 |         # 옵티마이저
  319 |         self.pitcher_optimizer = optim.Adam(
  320 |             self.pitcher_agent.parameters(), lr=self.config.lr
  321 |         )
  322 |         self.batter_optimizer = optim.Adam(
  323 |             self.batter_agent.parameters(), lr=self.config.lr
  324 |         )
  325 | 
  326 |         # PPO 업데이터
  327 |         self.updater = PPOUpdater(self.config, self.device)
  328 | 
  329 |         # 상대 풀 (과거 체크포인트)
  330 |         self.pitcher_pool: List[dict] = []
  331 |         self.batter_pool: List[dict] = []
  332 | 
  333 |         # Scripted 봇 (Warm-up)
  334 |         self.scripted_pitcher = ScriptedPitcherBot(difficulty=0.3)
  335 |         self.scripted_batter = ScriptedBatterBot(difficulty=0.3)
  336 | 
  337 |         # 리플레이 버퍼
  338 |         self.replay_buffer = PrioritizedReplayBuffer()
  339 | 
  340 |         # 환경
  341 |         self.env = BaseballGameEnv()
  342 | 
  343 |         # 통계
  344 |         self.episode_stats = deque(maxlen=100)
  345 |         self.pitcher_wins = 0
  346 |         self.batter_wins = 0
  347 | 
  348 |         # 체크포인트 디렉토리
  349 |         self.checkpoint_dir = Path(self.config.checkpoint_dir)
  350 |         self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
  351 |         self.data_dir = Path(self.config.data_dir)
  352 |         self.data_dir.mkdir(parents=True, exist_ok=True)
  353 | 
  354 |     def _get_opponent_action(
  355 |         self,
  356 |         agent_type: str,
  357 |         obs: np.ndarray,
  358 |         episode: int,
  359 |     ) -> np.ndarray:
  360 |         """상대 에이전트의 액션을 생성합니다.
  361 | 
  362 |         Warm-up 단계에서는 Scripted Bot, 이후에는 과거 체크포인트를 사용합니다.
  363 | 
  364 |         Args:
  365 |             agent_type: 'pitcher' 또는 'batter'
  366 |             obs: 관찰 벡터
  367 |             episode: 현재 에피소드 번호
  368 | 
  369 |         Returns:
  370 |             액션 벡터
  371 |         """
  372 |         # Warm-up: Scripted Bot 사용
  373 |         if episode < self.config.warmup_episodes:
  374 |             if agent_type == 'pitcher':
  375 |                 return self.scripted_pitcher.get_action(obs)
  376 |             else:
  377 |                 return self.scripted_batter.get_action(obs)
  378 | 
  379 |         # Self-Play: 과거 체크포인트에서 샘플
  380 |         pool = self.pitcher_pool if agent_type == 'pitcher' else self.batter_pool
  381 | 
  382 |         if not pool:
  383 |             # 풀이 비면 현재 정책 사용
  384 |             if agent_type == 'pitcher':
  385 |                 return self.scripted_pitcher.get_action(obs)
  386 |             else:
  387 |                 return self.scripted_batter.get_action(obs)
  388 | 
  389 |         # 최신 체크포인트 우선 선택
  390 |         if np.random.random() < self.config.opponent_sample_latest_prob:
  391 |             checkpoint = pool[-1]
  392 |         else:
  393 |             checkpoint = pool[np.random.randint(len(pool))]
  394 | 
  395 |         # 체크포인트에서 액션 생성
  396 |         obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
  397 | 
  398 |         if agent_type == 'pitcher':
  399 |             temp_agent = PitcherAgent().to(self.device)
  400 |             temp_agent.load_state_dict(checkpoint)
  401 |             with torch.no_grad():
  402 |                 action, _, _, _ = temp_agent.get_action_and_value(
  403 |                     obs_tensor, deterministic=True
  404 |                 )
  405 |         else:
  406 |             temp_agent = BatterAgent().to(self.device)
  407 |             temp_agent.load_state_dict(checkpoint)
  408 |             with torch.no_grad():
  409 |                 action, _, _, _, _ = temp_agent.get_action_and_value(
  410 |                     obs_tensor, deterministic=True
  411 |                 )
  412 | 
  413 |         return action.cpu().numpy().squeeze()
  414 | 
  415 |     def _snapshot_agent(self, agent_type: str):
  416 |         """현재 에이전트를 체크포인트 풀에 추가합니다."""
  417 |         if agent_type == 'pitcher':
  418 |             state_dict = copy.deepcopy(self.pitcher_agent.state_dict())
  419 |             self.pitcher_pool.append(state_dict)
  420 |             if len(self.pitcher_pool) > self.config.opponent_pool_size:
  421 |                 self.pitcher_pool.pop(0)
  422 |         else:
  423 |             state_dict = copy.deepcopy(self.batter_agent.state_dict())
  424 |             self.batter_pool.append(state_dict)
  425 |             if len(self.batter_pool) > self.config.opponent_pool_size:
  426 |                 self.batter_pool.pop(0)
  427 | 
  428 |     def _collect_episode(self, episode: int) -> dict:
  429 |         """한 에피소드를 실행하고 경험을 수집합니다.
  430 | 
  431 |         Args:
  432 |             episode: 에피소드 번호
  433 | 
  434 |         Returns:
  435 |             에피소드 통계 딕셔너리
  436 |         """
  437 |         obs, info = self.env.reset()
  438 |         pitcher_obs = obs['pitcher']
  439 |         batter_obs = obs['batter']
  440 | 
  441 |         # 수집 버퍼
  442 |         pitcher_buffer = {
  443 |             'obs': [], 'actions': [], 'log_probs': [], 'rewards': [],
  444 |             'values': [], 'dones': [],
  445 |         }
  446 |         batter_buffer = {
  447 |             'obs': [], 'actions': [], 'log_probs': [], 'rewards': [],
  448 |             'values': [], 'dones': [],
  449 |         }
  450 | 
  451 |         episode_reward_pitcher = 0.0
  452 |         episode_reward_batter = 0.0
  453 |         terminated = False
  454 |         truncated = False
  455 |         n_pitches = 0
  456 |         outcomes = []
  457 | 
  458 |         while not terminated and not truncated:
  459 |             # ── 투수 액션 ──
  460 |             p_obs_tensor = torch.FloatTensor(pitcher_obs).unsqueeze(0).to(self.device)
  461 |             with torch.no_grad():
  462 |                 p_action, p_log_prob, _, p_value = \
  463 |                     self.pitcher_agent.get_action_and_value(p_obs_tensor)
  464 | 
  465 |             p_action_np = p_action.cpu().numpy().squeeze()
  466 |             p_log_prob_val = p_log_prob.cpu().item()
  467 |             p_value_val = p_value.cpu().item()
  468 | 
  469 |             # ── 타자 액션 ──
  470 |             b_obs_tensor = torch.FloatTensor(batter_obs).unsqueeze(0).to(self.device)
  471 |             with torch.no_grad():
  472 |                 b_action, b_log_prob, _, b_value, _ = \
  473 |                     self.batter_agent.get_action_and_value(b_obs_tensor)
  474 | 
  475 |             b_action_np = b_action.cpu().numpy().squeeze()
  476 |             b_log_prob_val = b_log_prob.cpu().item()
  477 |             b_value_val = b_value.cpu().item()
  478 | 
  479 |             # ── 환경 스텝 ──
  480 |             combined_action = {
  481 |                 'pitcher': p_action_np,
  482 |                 'batter': b_action_np,
  483 |             }
  484 | 
  485 |             next_obs, rewards, terminated, truncated, info = self.env.step(combined_action)
  486 | 
  487 |             # 버퍼에 저장
  488 |             pitcher_buffer['obs'].append(pitcher_obs)
  489 |             pitcher_buffer['actions'].append(p_action_np)
  490 |             pitcher_buffer['log_probs'].append(p_log_prob_val)
  491 |             pitcher_buffer['rewards'].append(rewards['pitcher'])
  492 |             pitcher_buffer['values'].append(p_value_val)
  493 |             pitcher_buffer['dones'].append(float(terminated or truncated))
  494 | 
  495 |             batter_buffer['obs'].append(batter_obs)
  496 |             batter_buffer['actions'].append(b_action_np)
  497 |             batter_buffer['log_probs'].append(b_log_prob_val)
  498 |             batter_buffer['rewards'].append(rewards['batter'])
  499 |             batter_buffer['values'].append(b_value_val)
  500 |             batter_buffer['dones'].append(float(terminated or truncated))
  501 | 
  502 |             # 리플레이 버퍼에 저장
  503 |             transition = Transition(
  504 |                 pitcher_obs=pitcher_obs,
  505 |                 pitcher_action=p_action_np,
  506 |                 batter_obs=batter_obs,
  507 |                 batter_action=b_action_np,
  508 |                 pitcher_reward=rewards['pitcher'],
  509 |                 batter_reward=rewards['batter'],
  510 |                 next_pitcher_obs=next_obs['pitcher'],
  511 |                 next_batter_obs=next_obs['batter'],
  512 |                 done=terminated or truncated,
  513 |                 info=info.get('pitch_data', {}),
  514 |             )
  515 |             self.replay_buffer.add(transition)
  516 | 
  517 |             # 대시보드 데이터 전송
  518 |             if 'pitch_data' in info:
  519 |                 save_pitch_data(info['pitch_data'])
  520 | 
  521 |             episode_reward_pitcher += rewards['pitcher']
  522 |             episode_reward_batter += rewards['batter']
  523 |             n_pitches += 1
  524 | 
  525 |             outcome = info.get('pitch_outcome', {}).get('reward_key', '')
  526 |             outcomes.append(outcome)
  527 | 
  528 |             # 다음 관찰
  529 |             pitcher_obs = next_obs['pitcher']
  530 |             batter_obs = next_obs['batter']
  531 | 
  532 |         # 승패 판정
  533 |         if episode_reward_pitcher > episode_reward_batter:
  534 |             self.pitcher_wins += 1
  535 |             winner = 'pitcher'
  536 |         else:
  537 |             self.batter_wins += 1
  538 |             winner = 'batter'
  539 | 
  540 |         # 통계
  541 |         stats = {
  542 |             'episode': episode,
  543 |             'pitcher_reward': episode_reward_pitcher,
  544 |             'batter_reward': episode_reward_batter,
  545 |             'n_pitches': n_pitches,
  546 |             'winner': winner,
  547 |             'outcomes': outcomes,
  548 |             'has_home_run': 'home_run' in outcomes,
  549 |             'has_strikeout': outcomes.count('swinging_strike') + \
  550 |                              outcomes.count('called_strike') >= 3,
  551 |         }
  552 |         self.episode_stats.append(stats)
  553 | 
  554 |         return {
  555 |             'stats': stats,
  556 |             'pitcher_buffer': pitcher_buffer,
  557 |             'batter_buffer': batter_buffer,
  558 |         }
  559 | 
  560 |     def _update_agent(
  561 |         self,
  562 |         agent_type: str,
  563 |         buffer: dict,
  564 |     ) -> dict:
  565 |         """수집된 경험으로 에이전트를 업데이트합니다.
  566 | 
  567 |         Args:
  568 |             agent_type: 'pitcher' 또는 'batter'
  569 |             buffer: 경험 버퍼
  570 | 
  571 |         Returns:
  572 |             학습 메트릭
  573 |         """
  574 |         if not buffer['obs']:
  575 |             return {}
  576 | 
  577 |         agent = self.pitcher_agent if agent_type == 'pitcher' else self.batter_agent
  578 |         optimizer = self.pitcher_optimizer if agent_type == 'pitcher' else self.batter_optimizer
  579 | 
  580 |         obs = torch.FloatTensor(np.array(buffer['obs'])).to(self.device)
  581 |         actions = torch.FloatTensor(np.array(buffer['actions'])).to(self.device)
  582 |         old_log_probs = torch.FloatTensor(np.array(buffer['log_probs'])).to(self.device)
  583 |         rewards = np.array(buffer['rewards'])
  584 |         values = np.array(buffer['values'])
  585 |         dones = np.array(buffer['dones'])
  586 | 
  587 |         # GAE 계산
  588 |         with torch.no_grad():
  589 |             if agent_type == 'pitcher':
  590 |                 _, _, _, next_value = agent.get_action_and_value(obs[-1:])
  591 |             else:
  592 |                 _, _, _, next_value, _ = agent.get_action_and_value(obs[-1:])
  593 |             next_value = next_value.cpu().item()
  594 | 
  595 |         advantages, returns = self.updater.compute_gae(
  596 |             rewards, values, next_value, dones
  597 |         )
  598 | 
  599 |         advantages = torch.FloatTensor(advantages).to(self.device)
  600 |         returns = torch.FloatTensor(returns).to(self.device)
  601 | 
  602 |         # PPO 업데이트
  603 |         metrics = self.updater.ppo_update(
  604 |             agent, optimizer, obs, actions, old_log_probs,
  605 |             advantages, returns, is_batter=(agent_type == 'batter'),
  606 |         )
  607 | 
  608 |         return metrics
  609 | 
  610 |     def train(self):
  611 |         """메인 학습 루프를 실행합니다."""
  612 |         print("⚾ Baseball RL Self-Play Training 시작!")
  613 |         print(f"   Device: {self.device}")
  614 |         print(f"   Max Episodes: {self.max_episodes}")
  615 |         print(f"   Warmup: {self.config.warmup_episodes} episodes")
  616 |         print(f"   Checkpoint Dir: {self.checkpoint_dir}")
  617 |         print("-" * 60)
  618 | 
  619 |         start_time = time.time()
  620 | 
  621 |         for episode in range(1, self.max_episodes + 1):
  622 |             # ── 에피소드 수집 ──
  623 |             result = self._collect_episode(episode)
  624 |             stats = result['stats']
  625 | 
  626 |             # ── 에이전트 업데이트 ──
  627 |             p_metrics = self._update_agent('pitcher', result['pitcher_buffer'])
  628 |             b_metrics = self._update_agent('batter', result['batter_buffer'])
  629 | 
  630 |             # ── 체크포인트 스냅샷 ──
  631 |             if episode % self.config.snapshot_interval == 0:
  632 |                 self._snapshot_agent('pitcher')
  633 |                 self._snapshot_agent('batter')
  634 | 
  635 |             # ── 로깅 ──
  636 |             if episode % self.config.log_interval == 0:
  637 |                 self._log_progress(episode, stats, p_metrics, b_metrics, start_time)
  638 | 
  639 |             # ── 모델 저장 ──
  640 |             if episode % self.config.save_interval == 0:
  641 |                 self._save_checkpoint(episode)
  642 | 
  643 |         print("\n" + "=" * 60)
  644 |         print("⚾ 학습 완료!")
  645 |         self._save_checkpoint(self.max_episodes)
  646 | 
  647 |     def _log_progress(
  648 |         self,
  649 |         episode: int,
  650 |         stats: dict,
  651 |         p_metrics: dict,
  652 |         b_metrics: dict,
  653 |         start_time: float,
  654 |     ):
  655 |         """학습 진행 상황을 로깅합니다."""
  656 |         elapsed = time.time() - start_time
  657 |         total_games = self.pitcher_wins + self.batter_wins
  658 |         p_wr = self.pitcher_wins / max(total_games, 1)
  659 |         b_wr = self.batter_wins / max(total_games, 1)
  660 | 
  661 |         # 최근 100 에피소드 통계
  662 |         recent = list(self.episode_stats)
  663 |         avg_p_reward = np.mean([s['pitcher_reward'] for s in recent])
  664 |         avg_b_reward = np.mean([s['batter_reward'] for s in recent])
  665 |         hr_rate = np.mean([s['has_home_run'] for s in recent])
  666 |         k_rate = np.mean([s['has_strikeout'] for s in recent])
  667 | 
  668 |         print(
  669 |             f"[EP {episode:5d}] "
  670 |             f"WR: P={p_wr:.2f}/B={b_wr:.2f} | "
  671 |             f"Reward: P={avg_p_reward:+.2f}/B={avg_b_reward:+.2f} | "
  672 |             f"HR={hr_rate:.1%} K={k_rate:.1%} | "
  673 |             f"Buffer={self.replay_buffer.fill_ratio:.1%} | "
  674 |             f"{elapsed:.0f}s"
  675 |         )
  676 | 
  677 |         # 대시보드 메트릭 전송
  678 |         metrics = {
  679 |             'episode': episode,
  680 |             'pitcher_win_rate': p_wr,
  681 |             'batter_win_rate': b_wr,
  682 |             'pitcher_avg_reward': float(avg_p_reward),
  683 |             'batter_avg_reward': float(avg_b_reward),
  684 |             'home_run_rate': float(hr_rate),
  685 |             'strikeout_rate': float(k_rate),
  686 |             'buffer_fill_ratio': self.replay_buffer.fill_ratio,
  687 |             'pitcher_policy_loss': p_metrics.get('policy_loss', 0),
  688 |             'batter_policy_loss': b_metrics.get('policy_loss', 0),
  689 |             'pitcher_entropy': p_metrics.get('entropy', 0),
  690 |             'batter_entropy': b_metrics.get('entropy', 0),
  691 |         }
  692 |         save_training_metrics(metrics)
  693 | 
  694 |     def _save_checkpoint(self, episode: int):
  695 |         """모델 체크포인트를 저장합니다."""
  696 |         path = self.checkpoint_dir / f"checkpoint_ep{episode}.pt"
  697 |         torch.save({
  698 |             'episode': episode,
  699 |             'pitcher_state_dict': self.pitcher_agent.state_dict(),
  700 |             'batter_state_dict': self.batter_agent.state_dict(),
  701 |             'pitcher_optimizer': self.pitcher_optimizer.state_dict(),
  702 |             'batter_optimizer': self.batter_optimizer.state_dict(),
  703 |             'pitcher_wins': self.pitcher_wins,
  704 |             'batter_wins': self.batter_wins,
  705 |         }, path)
  706 |         print(f"   💾 Checkpoint saved: {path}")
  707 | 
  708 |     def load_checkpoint(self, path: str):
  709 |         """체크포인트에서 모델을 로드합니다."""
  710 |         checkpoint = torch.load(path, map_location=self.device)
  711 |         self.pitcher_agent.load_state_dict(checkpoint['pitcher_state_dict'])
  712 |         self.batter_agent.load_state_dict(checkpoint['batter_state_dict'])
  713 |         self.pitcher_optimizer.load_state_dict(checkpoint['pitcher_optimizer'])
  714 |         self.batter_optimizer.load_state_dict(checkpoint['batter_optimizer'])
  715 |         self.pitcher_wins = checkpoint.get('pitcher_wins', 0)
  716 |         self.batter_wins = checkpoint.get('batter_wins', 0)
  717 |         print(f"   ✅ Checkpoint loaded: {path}")
  718 | 
  719 | 
  720 | # ──────────────────────────────────────────────────────────────
  721 | #  메인 실행
  722 | # ──────────────────────────────────────────────────────────────
  723 | 
  724 | def main():
  725 |     """학습을 시작합니다."""
  726 |     import argparse
  727 | 
  728 |     parser = argparse.ArgumentParser(description='Baseball RL Self-Play Trainer')
  729 |     parser.add_argument('--episodes', type=int, default=1000, help='학습 에피소드 수')
  730 |     parser.add_argument('--lr', type=float, default=3e-4, help='학습률')
  731 |     parser.add_argument('--warmup', type=int, default=100, help='Warm-up 에피소드 수')
  732 |     parser.add_argument('--resume', type=str, default=None, help='체크포인트 경로')
  733 |     args = parser.parse_args()
  734 | 
  735 |     config = TrainingConfig()
  736 |     config.lr = args.lr
  737 |     config.warmup_episodes = args.warmup
  738 | 
  739 |     trainer = SelfPlayTrainer(config=config, max_episodes=args.episodes)
  740 | 
  741 |     if args.resume:
  742 |         trainer.load_checkpoint(args.resume)
  743 | 
  744 |     trainer.train()
  745 | 
  746 | 
  747 | if __name__ == '__main__':
  748 |     main()
````
