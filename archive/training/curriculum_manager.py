"""
curriculum_manager.py — 커리큘럼 학습 자동 관리자

Contact Rate를 실시간 모니터링하여 커리큘럼 Stage를 자동 승격하고,
학습이 불안정할 경우 이전 Stage로 롤백합니다.
"""

from typing import Optional, List, Dict
from collections import deque


class CurriculumManager:
    """커리큘럼 학습 자동 관리자.

    Args:
        initial_stage: 시작 커리큘럼 단계 (1~5)
        window_size: 승격 판단에 사용할 최근 에피소드 수
        promotion_patience: 승격 조건을 연속 N회 충족해야 승격
        max_stage: 최대 커리큘럼 단계
    """

    # 각 Stage별 승격 기준 Contact Rate
    PROMOTION_THRESHOLDS = {
        1: 0.40,  # Stage 1 → 2: Contact Rate > 40%
        2: 0.25,  # Stage 2 → 3: > 25%
        3: 0.15,  # Stage 3 → 4: > 15%
        4: 0.10,  # Stage 4 → 5: > 10%
        5: None,  # 최종 단계
    }

    def __init__(
        self,
        initial_stage: int = 1,
        window_size: int = 50,
        promotion_patience: int = 3,
        max_stage: int = 5,
    ):
        self.current_stage = initial_stage
        self.window_size = window_size
        self.promotion_patience = promotion_patience
        self.max_stage = max_stage

        # 최근 에피소드 결과 슬라이딩 윈도우
        self.contact_history: deque = deque(maxlen=window_size)
        self.consecutive_promotable = 0

        # 로그
        self.stage_history: List[Dict] = []

    def record_episode(self, contacted: bool, info: Optional[Dict] = None):
        """에피소드 결과를 기록합니다.

        Args:
            contacted: 이번 에피소드에서 배트-공 충돌이 발생했는지
            info: 추가 에피소드 정보 (exit_velo, result 등)
        """
        self.contact_history.append(1.0 if contacted else 0.0)

    def get_contact_rate(self) -> float:
        """최근 윈도우의 Contact Rate를 반환합니다."""
        if len(self.contact_history) == 0:
            return 0.0
        return sum(self.contact_history) / len(self.contact_history)

    def should_promote(self) -> bool:
        """현재 Stage에서 다음 Stage로 승격해야 하는지 판단합니다."""
        threshold = self.PROMOTION_THRESHOLDS.get(self.current_stage)
        if threshold is None:
            return False  # 최종 단계

        if len(self.contact_history) < self.window_size // 2:
            return False  # 데이터 부족

        rate = self.get_contact_rate()
        if rate >= threshold:
            self.consecutive_promotable += 1
        else:
            self.consecutive_promotable = 0

        return self.consecutive_promotable >= self.promotion_patience

    def promote(self) -> int:
        """다음 Stage로 승격합니다.

        Returns:
            새로운 Stage 번호
        """
        old_stage = self.current_stage
        # clear() 전에 rate를 먼저 기록해야 올바른 값이 저장됨
        rate_at_promotion = self.get_contact_rate()
        self.current_stage = min(self.current_stage + 1, self.max_stage)
        self.consecutive_promotable = 0
        self.contact_history.clear()

        self.stage_history.append({
            "from_stage": old_stage,
            "to_stage": self.current_stage,
            "contact_rate_at_promotion": rate_at_promotion,
        })

        print(f"  🎓 커리큘럼 승격: Stage {old_stage} → Stage {self.current_stage}")
        return self.current_stage

    def should_demote(self) -> bool:
        """학습이 붕괴되어 이전 Stage로 롤백해야 하는지 판단합니다."""
        if self.current_stage <= 1:
            return False

        if len(self.contact_history) < self.window_size:
            return False

        rate = self.get_contact_rate()
        # 현재 Stage의 이전 Stage 기준보다도 못하면 롤백
        prev_threshold = self.PROMOTION_THRESHOLDS.get(self.current_stage - 1, 0.0)
        if prev_threshold and rate < prev_threshold * 0.3:
            return True

        return False

    def demote(self) -> int:
        """이전 Stage로 롤백합니다."""
        old_stage = self.current_stage
        self.current_stage = max(1, self.current_stage - 1)
        self.consecutive_promotable = 0
        self.contact_history.clear()

        print(f"  ⚠️ 커리큘럼 롤백: Stage {old_stage} → Stage {self.current_stage}")
        return self.current_stage

    def check_and_update(self) -> int:
        """승격/롤백 여부를 확인하고 필요 시 업데이트합니다.

        Returns:
            현재(업데이트 후) Stage 번호
        """
        if self.should_promote():
            return self.promote()
        elif self.should_demote():
            return self.demote()
        return self.current_stage

    def get_status_str(self) -> str:
        """현재 커리큘럼 상태 문자열을 반환합니다."""
        rate = self.get_contact_rate()
        threshold = self.PROMOTION_THRESHOLDS.get(self.current_stage, "N/A")
        return (
            f"Stage {self.current_stage}/5 | "
            f"Contact Rate: {rate:.1%} | "
            f"Promotion Target: {threshold}"
        )
