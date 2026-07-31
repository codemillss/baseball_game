"""
diagnostician.py — 정체 구간 원인 분석 및 파라미터 조정(Plan Adjuster)

학습이 정체(Stuck)되었을 때, 메트릭을 분석하여 환경 또는 학습 파라미터를 
어떻게 조정할지(Action Plan)를 결정합니다.
"""

from typing import Dict, Any, List


class Diagnostician:
    def __init__(self):
        pass

    def diagnose(self, phase_id: int, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        메트릭을 분석하여 조정 계획(Action Plan)을 반환합니다.
        
        Returns:
            Dict: 조정할 파라미터 딕셔너리
                예) {'env.pitch_speed': 30.0, 'reward.contact_bonus': 5.0}
        """
        if phase_id == 1:
            return self._diagnose_phase_1(metrics)
        elif phase_id == 2:
            return self._diagnose_phase_2(metrics)
        elif phase_id == 3:
            return self._diagnose_phase_3(metrics)
        elif phase_id == 4:
            return self._diagnose_phase_4(metrics)
        else:
            return {}

    def _diagnose_phase_1(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1 (모션) 진단"""
        plan = {}
        # 타자 스윙이 안 되면 토크 상한을 더 풀어주거나 보상 셰이핑 조정
        if metrics.get('swing_completion_rate', 0.0) < 0.5:
            plan['action_penalty_weight'] = 0.5  # 액션 페널티 감소 (움직임 장려)
            plan['swing_bonus'] = 2.0            # 스윙 보너스 증가
        return plan

    def _diagnose_phase_2(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2 (시선 추적) 진단"""
        plan = {}
        if metrics.get('visual_tracking_rate', 0.0) < 0.5:
            plan['pitch_speed_max'] = 40.0       # 공 속도를 늦춰서 보기 쉽게 만듦
        return plan

    def _diagnose_phase_3(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3 (첫 컨택) 진단"""
        plan = {}
        contact_rate = metrics.get('contact_rate', 0.0)
        swing_rate = metrics.get('swing_completion_rate', 0.0)
        
        if swing_rate < 0.5:
            # 아예 스윙을 안해서 못 치는 경우
            plan['swing_bonus'] = 3.0
        elif contact_rate < 0.05:
            # 스윙은 하는데 안 맞는 경우 -> 거리를 좁히거나 (release_distance 감소) 공을 더 크게 만듦
            plan['release_distance'] = max(2.0, metrics.get('current_release_distance', 18.44) * 0.8)
            plan['pitch_speed_max'] = 35.0
            
        return plan

    def _diagnose_phase_4(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4 (양질의 컨택) 진단"""
        plan = {}
        ev = metrics.get('avg_exit_velocity_kmh', 0.0)
        ss = metrics.get('sweet_spot_rate', 0.0)
        
        if ev < 50.0:
            # 빗맞음 -> 스윗 스팟 보상 강화
            plan['sweet_spot_bonus_weight'] = 2.0
            plan['power_bonus_weight'] = 1.5
            
        return plan
