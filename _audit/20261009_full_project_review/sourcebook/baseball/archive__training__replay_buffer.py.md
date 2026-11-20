# baseball/archive/training/replay_buffer.py

원본: [archive/training/replay_buffer.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/replay_buffer.py)

SHA256: `43c37fd026e815c92abfb7445c187172b6f4f41d4c5d173bfc9d739fc0bbedc5`

전체 311행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `SumTree` | ClassDef | 22 | 86 |
| `__init__` | FunctionDef | 29 | 33 |
| `total` | FunctionDef | 35 | 37 |
| `add` | FunctionDef | 39 | 49 |
| `update` | FunctionDef | 51 | 59 |
| `get` | FunctionDef | 61 | 86 |
| `Transition` | ClassDef | 94 | 106 |
| `PrioritizedReplayBuffer` | ClassDef | 113 | 275 |
| `__init__` | FunctionDef | 128 | 156 |
| `beta` | FunctionDef | 159 | 162 |
| `fill_ratio` | FunctionDef | 165 | 167 |
| `add` | FunctionDef | 169 | 200 |
| `sample` | FunctionDef | 202 | 248 |
| `update_priorities` | FunctionDef | 250 | 260 |
| `get_stats` | FunctionDef | 262 | 275 |
| `transitions_to_batch` | FunctionDef | 282 | 311 |

## 전체 원문

````text
    1 | """
    2 | replay_buffer.py — Prioritized Experience Replay (PER) 버퍼
    3 | 
    4 | SumTree 자료구조 기반 O(log n) 우선순위 샘플링.
    5 | 희귀 이벤트(홈런, Sweet Spot 정타)에 priority 부스트를 적용합니다.
    6 | 
    7 | 설정:
    8 |     α = 0.6 (우선순위 지수)
    9 |     β = 0.4 → 1.0 (중요도 샘플링 가중치 어닐링)
   10 |     capacity = 100,000
   11 | """
   12 | 
   13 | import numpy as np
   14 | from typing import Tuple, Optional, Dict, Any
   15 | from dataclasses import dataclass, field
   16 | 
   17 | 
   18 | # ──────────────────────────────────────────────────────────────
   19 | #  SumTree
   20 | # ──────────────────────────────────────────────────────────────
   21 | 
   22 | class SumTree:
   23 |     """SumTree 자료구조.
   24 | 
   25 |     리프 노드에 priority를 저장하고, 부모 노드에 자식 합을 유지합니다.
   26 |     O(log n) 삽입/샘플링을 지원합니다.
   27 |     """
   28 | 
   29 |     def __init__(self, capacity: int):
   30 |         self.capacity = capacity
   31 |         self.tree = np.zeros(2 * capacity - 1, dtype=np.float64)
   32 |         self.data_pointer = 0
   33 |         self.n_entries = 0
   34 | 
   35 |     def total(self) -> float:
   36 |         """전체 priority 합."""
   37 |         return float(self.tree[0])
   38 | 
   39 |     def add(self, priority: float, data_index: int):
   40 |         """새 데이터의 priority를 추가합니다.
   41 | 
   42 |         Args:
   43 |             priority: 우선순위 값
   44 |             data_index: 데이터 배열 인덱스 (외부 관리)
   45 |         """
   46 |         tree_index = self.data_pointer + self.capacity - 1
   47 |         self.update(tree_index, priority)
   48 |         self.data_pointer = (self.data_pointer + 1) % self.capacity
   49 |         self.n_entries = min(self.n_entries + 1, self.capacity)
   50 | 
   51 |     def update(self, tree_index: int, priority: float):
   52 |         """특정 인덱스의 priority를 업데이트합니다."""
   53 |         change = priority - self.tree[tree_index]
   54 |         self.tree[tree_index] = priority
   55 | 
   56 |         # 부모 노드 업데이트 (루트까지)
   57 |         while tree_index != 0:
   58 |             tree_index = (tree_index - 1) // 2
   59 |             self.tree[tree_index] += change
   60 | 
   61 |     def get(self, s: float) -> Tuple[int, float, int]:
   62 |         """누적 확률 s에 해당하는 리프 노드를 찾습니다.
   63 | 
   64 |         Args:
   65 |             s: [0, total) 범위의 누적 확률값
   66 | 
   67 |         Returns:
   68 |             (tree_index, priority, data_index)
   69 |         """
   70 |         parent_index = 0
   71 | 
   72 |         while True:
   73 |             left = 2 * parent_index + 1
   74 |             right = left + 1
   75 | 
   76 |             if left >= len(self.tree):
   77 |                 break
   78 | 
   79 |             if s <= self.tree[left] or right >= len(self.tree):
   80 |                 parent_index = left
   81 |             else:
   82 |                 s -= self.tree[left]
   83 |                 parent_index = right
   84 | 
   85 |         data_index = parent_index - self.capacity + 1
   86 |         return parent_index, self.tree[parent_index], data_index
   87 | 
   88 | 
   89 | # ──────────────────────────────────────────────────────────────
   90 | #  Transition 데이터 구조
   91 | # ──────────────────────────────────────────────────────────────
   92 | 
   93 | @dataclass
   94 | class Transition:
   95 |     """하나의 경험 전이(Transition)를 저장합니다."""
   96 | 
   97 |     pitcher_obs: np.ndarray          # 투수 관찰 (6,)
   98 |     pitcher_action: np.ndarray       # 투수 액션 (5,)
   99 |     batter_obs: np.ndarray           # 타자 관찰 (13,) 또는 (seq, 13)
  100 |     batter_action: np.ndarray        # 타자 액션 (4,)
  101 |     pitcher_reward: float            # 투수 보상
  102 |     batter_reward: float             # 타자 보상
  103 |     next_pitcher_obs: np.ndarray     # 다음 투수 관찰
  104 |     next_batter_obs: np.ndarray      # 다음 타자 관찰
  105 |     done: bool                       # 에피소드 종료 여부
  106 |     info: Dict[str, Any] = field(default_factory=dict)  # 추가 정보
  107 | 
  108 | 
  109 | # ──────────────────────────────────────────────────────────────
  110 | #  PER 버퍼
  111 | # ──────────────────────────────────────────────────────────────
  112 | 
  113 | class PrioritizedReplayBuffer:
  114 |     """Prioritized Experience Replay 버퍼.
  115 | 
  116 |     TD-Error 기반 우선순위 샘플링으로 학습 효율을 높입니다.
  117 |     홈런/Sweet Spot 정타에 priority 부스트를 적용합니다.
  118 | 
  119 |     Args:
  120 |         capacity: 최대 저장 용량
  121 |         alpha: 우선순위 지수 (0=균등, 1=완전 우선순위)
  122 |         beta_start: IS 가중치 초기값
  123 |         beta_end: IS 가중치 최종값
  124 |         beta_frames: 어닐링 완료 프레임 수
  125 |         special_boost: 희귀 이벤트 priority 부스트 배수
  126 |     """
  127 | 
  128 |     def __init__(
  129 |         self,
  130 |         capacity: int = 100_000,
  131 |         alpha: float = 0.6,
  132 |         beta_start: float = 0.4,
  133 |         beta_end: float = 1.0,
  134 |         beta_frames: int = 100_000,
  135 |         special_boost: float = 2.0,
  136 |     ):
  137 |         self.capacity = capacity
  138 |         self.alpha = alpha
  139 |         self.beta_start = beta_start
  140 |         self.beta_end = beta_end
  141 |         self.beta_frames = beta_frames
  142 |         self.special_boost = special_boost
  143 | 
  144 |         self.tree = SumTree(capacity)
  145 |         self.data = [None] * capacity
  146 |         self.write_pointer = 0
  147 |         self.size = 0
  148 |         self.frame = 0
  149 | 
  150 |         self.max_priority = 1.0
  151 |         self.min_priority = 1e-6
  152 | 
  153 |         # 통계
  154 |         self.n_home_runs = 0
  155 |         self.n_sweet_spots = 0
  156 |         self.total_added = 0
  157 | 
  158 |     @property
  159 |     def beta(self) -> float:
  160 |         """현재 IS 가중치 β (어닐링)."""
  161 |         frac = min(self.frame / max(self.beta_frames, 1), 1.0)
  162 |         return self.beta_start + frac * (self.beta_end - self.beta_start)
  163 | 
  164 |     @property
  165 |     def fill_ratio(self) -> float:
  166 |         """버퍼 채움 비율."""
  167 |         return self.size / self.capacity
  168 | 
  169 |     def add(self, transition: Transition, td_error: Optional[float] = None):
  170 |         """경험을 버퍼에 추가합니다.
  171 | 
  172 |         Args:
  173 |             transition: Transition 객체
  174 |             td_error: TD-Error (None이면 max_priority 사용)
  175 |         """
  176 |         # Priority 계산
  177 |         if td_error is not None:
  178 |             priority = (abs(td_error) + self.min_priority) ** self.alpha
  179 |         else:
  180 |             priority = self.max_priority
  181 | 
  182 |         # 희귀 이벤트 부스트
  183 |         outcome = transition.info.get('outcome', '')
  184 |         if outcome == 'home_run':
  185 |             priority *= self.special_boost
  186 |             self.n_home_runs += 1
  187 |         elif transition.info.get('sweet_spot_factor', 0) > 0.9:
  188 |             priority *= self.special_boost * 0.8
  189 |             self.n_sweet_spots += 1
  190 | 
  191 |         # 저장
  192 |         self.data[self.write_pointer] = transition
  193 |         self.tree.add(priority, self.write_pointer)
  194 | 
  195 |         self.write_pointer = (self.write_pointer + 1) % self.capacity
  196 |         self.size = min(self.size + 1, self.capacity)
  197 |         self.total_added += 1
  198 |         self.frame += 1
  199 | 
  200 |         self.max_priority = max(self.max_priority, priority)
  201 | 
  202 |     def sample(self, batch_size: int) -> Tuple[list, np.ndarray, np.ndarray]:
  203 |         """우선순위 기반 배치 샘플링.
  204 | 
  205 |         Args:
  206 |             batch_size: 샘플 크기
  207 | 
  208 |         Returns:
  209 |             (transitions, indices, is_weights)
  210 |             transitions: Transition 리스트
  211 |             indices: SumTree 인덱스 (priority 업데이트용)
  212 |             is_weights: 중요도 샘플링 가중치
  213 |         """
  214 |         batch_size = min(batch_size, self.size)
  215 |         transitions = []
  216 |         indices = np.zeros(batch_size, dtype=np.int64)
  217 |         priorities = np.zeros(batch_size, dtype=np.float64)
  218 | 
  219 |         # 구간 분할 (stratified sampling)
  220 |         segment = self.tree.total() / batch_size
  221 | 
  222 |         for i in range(batch_size):
  223 |             low = segment * i
  224 |             high = segment * (i + 1)
  225 |             s = np.random.uniform(low, high)
  226 | 
  227 |             tree_idx, priority, data_idx = self.tree.get(s)
  228 | 
  229 |             # 유효성 검사
  230 |             data_idx = data_idx % self.capacity
  231 |             if self.data[data_idx] is None:
  232 |                 # 빈 슬롯이면 랜덤 유효 데이터 선택
  233 |                 valid_indices = [j for j in range(self.size) if self.data[j] is not None]
  234 |                 if valid_indices:
  235 |                     data_idx = np.random.choice(valid_indices)
  236 |                     tree_idx = data_idx + self.capacity - 1
  237 |                     priority = self.tree.tree[tree_idx]
  238 | 
  239 |             indices[i] = tree_idx
  240 |             priorities[i] = max(priority, self.min_priority)
  241 |             transitions.append(self.data[data_idx])
  242 | 
  243 |         # IS 가중치 계산
  244 |         sampling_probs = priorities / (self.tree.total() + 1e-10)
  245 |         is_weights = (self.size * sampling_probs) ** (-self.beta)
  246 |         is_weights = is_weights / (is_weights.max() + 1e-10)  # 정규화
  247 | 
  248 |         return transitions, indices, is_weights.astype(np.float32)
  249 | 
  250 |     def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
  251 |         """샘플된 경험의 priority를 TD-Error 기반으로 업데이트합니다.
  252 | 
  253 |         Args:
  254 |             indices: SumTree 인덱스
  255 |             td_errors: 새로운 TD-Error 값
  256 |         """
  257 |         for idx, td_error in zip(indices, td_errors):
  258 |             priority = (abs(td_error) + self.min_priority) ** self.alpha
  259 |             self.tree.update(int(idx), priority)
  260 |             self.max_priority = max(self.max_priority, priority)
  261 | 
  262 |     def get_stats(self) -> dict:
  263 |         """버퍼 통계를 반환합니다."""
  264 |         return {
  265 |             'size': self.size,
  266 |             'capacity': self.capacity,
  267 |             'fill_ratio': self.fill_ratio,
  268 |             'total_added': self.total_added,
  269 |             'n_home_runs': self.n_home_runs,
  270 |             'n_sweet_spots': self.n_sweet_spots,
  271 |             'home_run_ratio': self.n_home_runs / max(self.total_added, 1),
  272 |             'sweet_spot_ratio': self.n_sweet_spots / max(self.total_added, 1),
  273 |             'max_priority': self.max_priority,
  274 |             'beta': self.beta,
  275 |         }
  276 | 
  277 | 
  278 | # ──────────────────────────────────────────────────────────────
  279 | #  배치 변환 유틸리티
  280 | # ──────────────────────────────────────────────────────────────
  281 | 
  282 | def transitions_to_batch(transitions: list) -> dict:
  283 |     """Transition 리스트를 학습용 배치 딕셔너리로 변환합니다.
  284 | 
  285 |     Args:
  286 |         transitions: Transition 객체 리스트
  287 | 
  288 |     Returns:
  289 |         dict of numpy arrays:
  290 |             'pitcher_obs': (batch, 6)
  291 |             'pitcher_actions': (batch, 5)
  292 |             'batter_obs': (batch, 13)
  293 |             'batter_actions': (batch, 4)
  294 |             'pitcher_rewards': (batch,)
  295 |             'batter_rewards': (batch,)
  296 |             'next_pitcher_obs': (batch, 6)
  297 |             'next_batter_obs': (batch, 13)
  298 |             'dones': (batch,)
  299 |     """
  300 |     batch = {
  301 |         'pitcher_obs': np.array([t.pitcher_obs for t in transitions]),
  302 |         'pitcher_actions': np.array([t.pitcher_action for t in transitions]),
  303 |         'batter_obs': np.array([t.batter_obs for t in transitions]),
  304 |         'batter_actions': np.array([t.batter_action for t in transitions]),
  305 |         'pitcher_rewards': np.array([t.pitcher_reward for t in transitions]),
  306 |         'batter_rewards': np.array([t.batter_reward for t in transitions]),
  307 |         'next_pitcher_obs': np.array([t.next_pitcher_obs for t in transitions]),
  308 |         'next_batter_obs': np.array([t.next_batter_obs for t in transitions]),
  309 |         'dones': np.array([float(t.done) for t in transitions]),
  310 |     }
  311 |     return batch
````
