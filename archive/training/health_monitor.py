"""
health_monitor.py — 학습 안정성 자동 감시 및 조기 경보 시스템

Policy Entropy, KL Divergence, Value Loss, Contact Rate, Win Rate 등의
핵심 메트릭을 실시간 추적하고, 붕괴 징후를 조기에 감지합니다.
"""

from collections import deque
from typing import Dict, List, Optional
import numpy as np


class TrainingHealthMonitor:
    """학습 상태 자동 감시 및 조기 경보.

    Args:
        window_size: 이동 평균 윈도우 크기
    """

    def __init__(self, window_size: int = 50):
        self.window_size = window_size

        # 메트릭 히스토리 (슬라이딩 윈도우)
        self.entropy_history = deque(maxlen=window_size)
        self.kl_history = deque(maxlen=window_size)
        self.value_loss_history = deque(maxlen=window_size)
        self.policy_loss_history = deque(maxlen=window_size)
        self.contact_rate_history = deque(maxlen=window_size)
        self.reward_history = deque(maxlen=window_size)
        self.grad_norm_history = deque(maxlen=window_size)

        # 알림 로그
        self.alerts: List[Dict] = []

    def record(self, metrics: Dict[str, float]):
        """학습 메트릭을 기록합니다.

        Args:
            metrics: {
                'entropy': float,
                'kl_divergence': float,
                'value_loss': float,
                'policy_loss': float,
                'contact_rate': float,
                'reward': float,
                'grad_norm': float,  (optional)
            }
        """
        if "entropy" in metrics:
            self.entropy_history.append(metrics["entropy"])
        if "kl_divergence" in metrics:
            self.kl_history.append(metrics["kl_divergence"])
        if "value_loss" in metrics:
            self.value_loss_history.append(metrics["value_loss"])
        if "policy_loss" in metrics:
            self.policy_loss_history.append(metrics["policy_loss"])
        if "contact_rate" in metrics:
            self.contact_rate_history.append(metrics["contact_rate"])
        if "reward" in metrics:
            self.reward_history.append(metrics["reward"])
        if "grad_norm" in metrics:
            self.grad_norm_history.append(metrics["grad_norm"])

    def check_health(self) -> List[str]:
        """학습 상태를 검사하고 경보 메시지를 반환합니다.

        Returns:
            경보 메시지 리스트 (비어있으면 정상)
        """
        alerts = []

        # 1. Mode Collapse 감지: 엔트로피 급락
        if len(self.entropy_history) >= 10:
            recent_entropy = np.mean(list(self.entropy_history)[-10:])
            if recent_entropy < 0.01:
                alerts.append(
                    "🚨 MODE COLLAPSE: 정책 엔트로피 극소 "
                    f"({recent_entropy:.4f}) → 정책 다양성 상실. "
                    "엔트로피 보너스 계수 증가 권장."
                )

        # 2. KL Divergence 폭주: 정책 급변
        if len(self.kl_history) >= 5:
            recent_kl = np.mean(list(self.kl_history)[-5:])
            if recent_kl > 0.1:
                alerts.append(
                    f"⚠️ KL SPIKE: 정책 급변 (KL={recent_kl:.4f} > 0.1). "
                    "학습률 자동 감소 또는 PPO clip 범위 축소 권장."
                )

        # 3. Value Loss 발산
        if len(self.value_loss_history) >= 10:
            recent_vloss = np.mean(list(self.value_loss_history)[-10:])
            if recent_vloss > 100.0:
                alerts.append(
                    f"🚨 CRITIC 발산: Value Loss 폭증 ({recent_vloss:.1f}). "
                    "학습 일시 중단 또는 학습률 감소 권장."
                )

        # 4. Contact Rate 정체: 학습 신호 없음
        if len(self.contact_rate_history) >= 30:
            recent_cr = np.mean(list(self.contact_rate_history)[-30:])
            if recent_cr < 0.01:
                alerts.append(
                    "⚠️ 학습 신호 없음: Contact Rate 0%에 수렴. "
                    "커리큘럼 난이도 하향 또는 Distance Shaping 활성화 권장."
                )

        # 5. Gradient Norm 폭발
        if len(self.grad_norm_history) >= 5:
            recent_gn = np.mean(list(self.grad_norm_history)[-5:])
            if recent_gn > 10.0:
                alerts.append(
                    f"⚠️ GRADIENT 폭발: Grad Norm={recent_gn:.1f}. "
                    "Gradient Clipping 강화 권장."
                )

        # 6. 보상 급격한 하락 (최근 vs 과거 비교)
        if len(self.reward_history) >= 40:
            early = np.mean(list(self.reward_history)[:20])
            late = np.mean(list(self.reward_history)[-20:])
            if late < early - 5.0:
                alerts.append(
                    f"⚠️ 보상 급락: {early:.2f} → {late:.2f}. "
                    "정책 붕괴 또는 과적합 가능성."
                )

        # 알림 저장
        for alert in alerts:
            self.alerts.append({"message": alert})

        return alerts

    def get_summary(self) -> Dict[str, float]:
        """현재 모니터링 요약을 반환합니다."""
        def safe_mean(d):
            return float(np.mean(list(d))) if len(d) > 0 else 0.0

        return {
            "avg_entropy": safe_mean(self.entropy_history),
            "avg_kl": safe_mean(self.kl_history),
            "avg_value_loss": safe_mean(self.value_loss_history),
            "avg_policy_loss": safe_mean(self.policy_loss_history),
            "avg_contact_rate": safe_mean(self.contact_rate_history),
            "avg_reward": safe_mean(self.reward_history),
            "avg_grad_norm": safe_mean(self.grad_norm_history),
            "total_alerts": len(self.alerts),
        }

    def get_status_str(self) -> str:
        """현재 상태를 사람이 읽을 수 있는 문자열로 반환합니다."""
        s = self.get_summary()
        status = "✅ HEALTHY"
        recent_alerts = self.check_health()
        if recent_alerts:
            status = "⚠️ ALERT"

        return (
            f"[{status}] "
            f"Entropy={s['avg_entropy']:.3f} | "
            f"KL={s['avg_kl']:.4f} | "
            f"VLoss={s['avg_value_loss']:.2f} | "
            f"CR={s['avg_contact_rate']:.1%} | "
            f"Reward={s['avg_reward']:+.2f}"
        )
