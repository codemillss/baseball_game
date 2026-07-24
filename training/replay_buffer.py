"""
replay_buffer.py — Prioritized Experience Replay (PER) 버퍼

SumTree 자료구조 기반 O(log n) 우선순위 샘플링.
희귀 이벤트(홈런, Sweet Spot 정타)에 priority 부스트를 적용합니다.

설정:
    α = 0.6 (우선순위 지수)
    β = 0.4 → 1.0 (중요도 샘플링 가중치 어닐링)
    capacity = 100,000
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass, field


# ──────────────────────────────────────────────────────────────
#  SumTree
# ──────────────────────────────────────────────────────────────

class SumTree:
    """SumTree 자료구조.

    리프 노드에 priority를 저장하고, 부모 노드에 자식 합을 유지합니다.
    O(log n) 삽입/샘플링을 지원합니다.
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.tree = np.zeros(2 * capacity - 1, dtype=np.float64)
        self.data_pointer = 0
        self.n_entries = 0

    def total(self) -> float:
        """전체 priority 합."""
        return float(self.tree[0])

    def add(self, priority: float, data_index: int):
        """새 데이터의 priority를 추가합니다.

        Args:
            priority: 우선순위 값
            data_index: 데이터 배열 인덱스 (외부 관리)
        """
        tree_index = self.data_pointer + self.capacity - 1
        self.update(tree_index, priority)
        self.data_pointer = (self.data_pointer + 1) % self.capacity
        self.n_entries = min(self.n_entries + 1, self.capacity)

    def update(self, tree_index: int, priority: float):
        """특정 인덱스의 priority를 업데이트합니다."""
        change = priority - self.tree[tree_index]
        self.tree[tree_index] = priority

        # 부모 노드 업데이트 (루트까지)
        while tree_index != 0:
            tree_index = (tree_index - 1) // 2
            self.tree[tree_index] += change

    def get(self, s: float) -> Tuple[int, float, int]:
        """누적 확률 s에 해당하는 리프 노드를 찾습니다.

        Args:
            s: [0, total) 범위의 누적 확률값

        Returns:
            (tree_index, priority, data_index)
        """
        parent_index = 0

        while True:
            left = 2 * parent_index + 1
            right = left + 1

            if left >= len(self.tree):
                break

            if s <= self.tree[left] or right >= len(self.tree):
                parent_index = left
            else:
                s -= self.tree[left]
                parent_index = right

        data_index = parent_index - self.capacity + 1
        return parent_index, self.tree[parent_index], data_index


# ──────────────────────────────────────────────────────────────
#  Transition 데이터 구조
# ──────────────────────────────────────────────────────────────

@dataclass
class Transition:
    """하나의 경험 전이(Transition)를 저장합니다."""

    pitcher_obs: np.ndarray          # 투수 관찰 (6,)
    pitcher_action: np.ndarray       # 투수 액션 (5,)
    batter_obs: np.ndarray           # 타자 관찰 (13,) 또는 (seq, 13)
    batter_action: np.ndarray        # 타자 액션 (4,)
    pitcher_reward: float            # 투수 보상
    batter_reward: float             # 타자 보상
    next_pitcher_obs: np.ndarray     # 다음 투수 관찰
    next_batter_obs: np.ndarray      # 다음 타자 관찰
    done: bool                       # 에피소드 종료 여부
    info: Dict[str, Any] = field(default_factory=dict)  # 추가 정보


# ──────────────────────────────────────────────────────────────
#  PER 버퍼
# ──────────────────────────────────────────────────────────────

class PrioritizedReplayBuffer:
    """Prioritized Experience Replay 버퍼.

    TD-Error 기반 우선순위 샘플링으로 학습 효율을 높입니다.
    홈런/Sweet Spot 정타에 priority 부스트를 적용합니다.

    Args:
        capacity: 최대 저장 용량
        alpha: 우선순위 지수 (0=균등, 1=완전 우선순위)
        beta_start: IS 가중치 초기값
        beta_end: IS 가중치 최종값
        beta_frames: 어닐링 완료 프레임 수
        special_boost: 희귀 이벤트 priority 부스트 배수
    """

    def __init__(
        self,
        capacity: int = 100_000,
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_end: float = 1.0,
        beta_frames: int = 100_000,
        special_boost: float = 2.0,
    ):
        self.capacity = capacity
        self.alpha = alpha
        self.beta_start = beta_start
        self.beta_end = beta_end
        self.beta_frames = beta_frames
        self.special_boost = special_boost

        self.tree = SumTree(capacity)
        self.data = [None] * capacity
        self.write_pointer = 0
        self.size = 0
        self.frame = 0

        self.max_priority = 1.0
        self.min_priority = 1e-6

        # 통계
        self.n_home_runs = 0
        self.n_sweet_spots = 0
        self.total_added = 0

    @property
    def beta(self) -> float:
        """현재 IS 가중치 β (어닐링)."""
        frac = min(self.frame / max(self.beta_frames, 1), 1.0)
        return self.beta_start + frac * (self.beta_end - self.beta_start)

    @property
    def fill_ratio(self) -> float:
        """버퍼 채움 비율."""
        return self.size / self.capacity

    def add(self, transition: Transition, td_error: Optional[float] = None):
        """경험을 버퍼에 추가합니다.

        Args:
            transition: Transition 객체
            td_error: TD-Error (None이면 max_priority 사용)
        """
        # Priority 계산
        if td_error is not None:
            priority = (abs(td_error) + self.min_priority) ** self.alpha
        else:
            priority = self.max_priority

        # 희귀 이벤트 부스트
        outcome = transition.info.get('outcome', '')
        if outcome == 'home_run':
            priority *= self.special_boost
            self.n_home_runs += 1
        elif transition.info.get('sweet_spot_factor', 0) > 0.9:
            priority *= self.special_boost * 0.8
            self.n_sweet_spots += 1

        # 저장
        self.data[self.write_pointer] = transition
        self.tree.add(priority, self.write_pointer)

        self.write_pointer = (self.write_pointer + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)
        self.total_added += 1
        self.frame += 1

        self.max_priority = max(self.max_priority, priority)

    def sample(self, batch_size: int) -> Tuple[list, np.ndarray, np.ndarray]:
        """우선순위 기반 배치 샘플링.

        Args:
            batch_size: 샘플 크기

        Returns:
            (transitions, indices, is_weights)
            transitions: Transition 리스트
            indices: SumTree 인덱스 (priority 업데이트용)
            is_weights: 중요도 샘플링 가중치
        """
        batch_size = min(batch_size, self.size)
        transitions = []
        indices = np.zeros(batch_size, dtype=np.int64)
        priorities = np.zeros(batch_size, dtype=np.float64)

        # 구간 분할 (stratified sampling)
        segment = self.tree.total() / batch_size

        for i in range(batch_size):
            low = segment * i
            high = segment * (i + 1)
            s = np.random.uniform(low, high)

            tree_idx, priority, data_idx = self.tree.get(s)

            # 유효성 검사
            data_idx = data_idx % self.capacity
            if self.data[data_idx] is None:
                # 빈 슬롯이면 랜덤 유효 데이터 선택
                valid_indices = [j for j in range(self.size) if self.data[j] is not None]
                if valid_indices:
                    data_idx = np.random.choice(valid_indices)
                    tree_idx = data_idx + self.capacity - 1
                    priority = self.tree.tree[tree_idx]

            indices[i] = tree_idx
            priorities[i] = max(priority, self.min_priority)
            transitions.append(self.data[data_idx])

        # IS 가중치 계산
        sampling_probs = priorities / (self.tree.total() + 1e-10)
        is_weights = (self.size * sampling_probs) ** (-self.beta)
        is_weights = is_weights / (is_weights.max() + 1e-10)  # 정규화

        return transitions, indices, is_weights.astype(np.float32)

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """샘플된 경험의 priority를 TD-Error 기반으로 업데이트합니다.

        Args:
            indices: SumTree 인덱스
            td_errors: 새로운 TD-Error 값
        """
        for idx, td_error in zip(indices, td_errors):
            priority = (abs(td_error) + self.min_priority) ** self.alpha
            self.tree.update(int(idx), priority)
            self.max_priority = max(self.max_priority, priority)

    def get_stats(self) -> dict:
        """버퍼 통계를 반환합니다."""
        return {
            'size': self.size,
            'capacity': self.capacity,
            'fill_ratio': self.fill_ratio,
            'total_added': self.total_added,
            'n_home_runs': self.n_home_runs,
            'n_sweet_spots': self.n_sweet_spots,
            'home_run_ratio': self.n_home_runs / max(self.total_added, 1),
            'sweet_spot_ratio': self.n_sweet_spots / max(self.total_added, 1),
            'max_priority': self.max_priority,
            'beta': self.beta,
        }


# ──────────────────────────────────────────────────────────────
#  배치 변환 유틸리티
# ──────────────────────────────────────────────────────────────

def transitions_to_batch(transitions: list) -> dict:
    """Transition 리스트를 학습용 배치 딕셔너리로 변환합니다.

    Args:
        transitions: Transition 객체 리스트

    Returns:
        dict of numpy arrays:
            'pitcher_obs': (batch, 6)
            'pitcher_actions': (batch, 5)
            'batter_obs': (batch, 13)
            'batter_actions': (batch, 4)
            'pitcher_rewards': (batch,)
            'batter_rewards': (batch,)
            'next_pitcher_obs': (batch, 6)
            'next_batter_obs': (batch, 13)
            'dones': (batch,)
    """
    batch = {
        'pitcher_obs': np.array([t.pitcher_obs for t in transitions]),
        'pitcher_actions': np.array([t.pitcher_action for t in transitions]),
        'batter_obs': np.array([t.batter_obs for t in transitions]),
        'batter_actions': np.array([t.batter_action for t in transitions]),
        'pitcher_rewards': np.array([t.pitcher_reward for t in transitions]),
        'batter_rewards': np.array([t.batter_reward for t in transitions]),
        'next_pitcher_obs': np.array([t.next_pitcher_obs for t in transitions]),
        'next_batter_obs': np.array([t.next_batter_obs for t in transitions]),
        'dones': np.array([float(t.done) for t in transitions]),
    }
    return batch
