"""
reward_audit.py — 보상 악용(Reward Hacking) 자동 감시 및 분석

Exit Velocity, Spray Angle 등의 분포를 추적하여,
정상적인 야구 타격이 아닌 편법(예: 배트 밀어넣기, 연속 파울)으로
보상을 수확하는 징후를 감지합니다.
"""

import numpy as np
from collections import deque
from typing import Dict, List, Optional


class RewardAuditSystem:
    """보상 악용 및 이상 타격 패턴 자동 감시 시스템."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        
        # 타격 성공 시의 메트릭만 추적
        self.exit_velocities = deque(maxlen=window_size)
        self.launch_angles = deque(maxlen=window_size)
        self.spray_angles = deque(maxlen=window_size)
        self.rewards = deque(maxlen=window_size)
        
        self.alerts: List[Dict] = []

    def record_hit(self, info: Dict, reward: float):
        """타격이 발생한 에피소드의 데이터를 기록합니다."""
        if "exit_velocity_kmh" in info:
            self.exit_velocities.append(info["exit_velocity_kmh"])
        if "launch_angle" in info:
            self.launch_angles.append(info["launch_angle"])
        if "spray_angle" in info:
            self.spray_angles.append(info["spray_angle"])
            
        self.rewards.append(reward)

    def audit(self) -> List[str]:
        """현재 타격 분포를 분석하여 이상 징후를 보고합니다."""
        alerts = []
        n_hits = len(self.exit_velocities)
        
        if n_hits < 20:
            return alerts  # 분석하기에 데이터 부족

        # 1. "배트 밀어넣기" (Bunting/Pushing) 감지
        # 보상은 받는데 타구 속도가 비정상적으로 낮은 경우
        avg_exit_velo = np.mean(list(self.exit_velocities))
        if avg_exit_velo < 40.0:
            alerts.append(
                f"🚨 [보상 악용 의심] 타구 속도 비정상 낮음 (평균 {avg_exit_velo:.1f}km/h). "
                "배트를 휘두르지 않고 공 궤적에 밀어넣는 편법 가능성 높음."
            )

        # 2. "연속 파울" (Foul Spamming) 감지
        # 파울 페널티가 너무 작을 때, 파울만 쳐서 에피소드를 끝내려는 징후
        foul_count = sum(1 for sa in self.spray_angles if abs(sa) > 45.0)
        foul_rate = foul_count / n_hits
        if foul_rate > 0.8:
            alerts.append(
                f"⚠️ [보상 악용 의심] 파울 비율 극단적 높음 ({foul_rate:.1%}). "
                "파울 페널티(현재 -0.5)를 강화하거나 페어존 보너스를 높여야 함."
            )

        # 3. 타구 다양성 상실 (Mode Collapse)
        # 모든 타구가 동일한 각도/속도로 날아가는 경우 (표준편차 극소)
        if len(self.launch_angles) > 50:
            la_std = np.std(list(self.launch_angles))
            sa_std = np.std(list(self.spray_angles))
            if la_std < 2.0 and sa_std < 2.0:
                alerts.append(
                    f"⚠️ [다양성 상실] 타구 각도 분포가 극도로 편중됨 (LA Std={la_std:.1f}, SA Std={sa_std:.1f})."
                )
                
        # 알림 저장
        for alert in alerts:
            self.alerts.append({"message": alert})

        return alerts

    def get_summary(self) -> str:
        """현재 감사 요약을 문자열로 반환합니다."""
        n_hits = len(self.exit_velocities)
        if n_hits == 0:
            return "No hits recorded."
            
        avg_ev = np.mean(list(self.exit_velocities))
        max_ev = np.max(list(self.exit_velocities))
        foul_count = sum(1 for sa in self.spray_angles if abs(sa) > 45.0)
        
        return (
            f"[Audit] Hits: {n_hits} | "
            f"Avg EV: {avg_ev:.1f} km/h (Max: {max_ev:.1f}) | "
            f"Foul Rate: {foul_count/n_hits:.1%}"
        )
