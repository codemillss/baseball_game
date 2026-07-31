"""
stage_gate.py — 학습 단계별 통과 기준(Stage Gate) 정의

각 Phase 별 성공 기준(Success Criteria)을 정의합니다.
AutoGameBuilder가 현재 모델 성능(Metrics)을 평가하여
다음 단계로 넘어갈지, 혹은 파라미터를 조정할지 결정하는 기준이 됩니다.
"""

from typing import Dict, Any, Tuple


class StageGate:
    """단일 Stage의 통과/정체 상태를 평가하는 클래스."""

    def __init__(self, name: str, phase_id: int):
        self.name = name
        self.phase_id = phase_id

    def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
        """
        메트릭을 평가하여 상태를 반환합니다.
        Returns:
            passed (bool): 통과 여부 (다음 단계로 진행)
            stuck (bool): 정체 여부 (파라미터 조정 필요)
            reason (str): 판단 이유
        """
        raise NotImplementedError


class Phase1Gate(StageGate):
    def __init__(self):
        super().__init__("Phase 1: Motor Primitives", 1)

    def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
        """
        성공 기준:
          [투수] 투구 동작 완료율 > 80% (release 됨)
          [타자] 스윙 완료율 > 80% (bat tip speed > 60km/h)
        """
        pitch_completion = metrics.get('pitch_completion_rate', 0.0)
        swing_completion = metrics.get('swing_completion_rate', 0.0)
        bat_speed = metrics.get('avg_bat_speed_kmh', 0.0)

        passed = pitch_completion > 0.8 and swing_completion > 0.8 and bat_speed > 60.0
        
        # 1000 에피소드 이상 진행되었는데도 통과하지 못한 경우
        episodes = metrics.get('episodes', 0)
        stuck = not passed and episodes > 1000

        if passed:
            return True, False, "투수/타자 기본 모션 완료"
        elif stuck:
            return False, True, f"모션 학습 정체 (Pitch:{pitch_completion:.1f}, Swing:{swing_completion:.1f}, Spd:{bat_speed:.1f})"
        else:
            return False, False, "모션 학습 진행 중"


class Phase2Gate(StageGate):
    def __init__(self):
        super().__init__("Phase 2: Ball Tracking", 2)

    def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
        """
        성공 기준:
          시야 유지율 > 90% (공이 박스 통과할 때까지)
        """
        tracking_rate = metrics.get('visual_tracking_rate', 0.0)
        
        passed = tracking_rate > 0.90
        episodes = metrics.get('episodes_in_phase', 0)
        stuck = not passed and episodes > 2000

        if passed:
            return True, False, "시선 추적 안정화"
        elif stuck:
            return False, True, f"시선 추적 정체 (Tracking:{tracking_rate:.1%})"
        else:
            return False, False, "시선 추적 학습 중"


class Phase3Gate(StageGate):
    def __init__(self):
        super().__init__("Phase 3: First Contact", 3)

    def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
        """
        성공 기준:
          Contact Rate > 20%
        """
        contact_rate = metrics.get('contact_rate', 0.0)
        
        passed = contact_rate > 0.20
        episodes = metrics.get('episodes_in_phase', 0)
        stuck = contact_rate < 0.05 and episodes > 3000

        if passed:
            return True, False, "초기 컨택 확보"
        elif stuck:
            return False, True, f"컨택 실패 정체 (Contact:{contact_rate:.1%})"
        else:
            return False, False, "컨택 학습 중"


class Phase4Gate(StageGate):
    def __init__(self):
        super().__init__("Phase 4: Quality Contact", 4)

    def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
        """
        성공 기준:
          Contact Rate > 50%
          Avg Exit Velocity > 80 km/h
          Sweet Spot Rate > 30%
        """
        contact_rate = metrics.get('contact_rate', 0.0)
        ev = metrics.get('avg_exit_velocity_kmh', 0.0)
        ss_rate = metrics.get('sweet_spot_rate', 0.0)
        
        passed = contact_rate > 0.50 and ev > 80.0 and ss_rate > 0.30
        episodes = metrics.get('episodes_in_phase', 0)
        stuck = (contact_rate < 0.20 or ev < 40.0) and episodes > 5000

        if passed:
            return True, False, "양질의 타구 확보"
        elif stuck:
            return False, True, f"타구 품질 정체 (CR:{contact_rate:.1%}, EV:{ev:.1f}, SS:{ss_rate:.1%})"
        else:
            return False, False, "타격 품질 개선 중"


class Phase5Gate(StageGate):
    def __init__(self):
        super().__init__("Phase 5: Self-Play Exploration", 5)

    def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
        """
        성공 기준:
          [투수] 스트라이크존 투구 비율 > 40% (제구력 확보)
          [타자] Contact Rate > 30% (다양한 공에 대한 대처)
        """
        strike_rate = metrics.get('pitcher_strike_rate', 0.0)
        contact_rate = metrics.get('contact_rate', 0.0)
        
        passed = strike_rate > 0.40 and contact_rate > 0.30
        episodes = metrics.get('episodes_in_phase', 0)
        stuck = (strike_rate < 0.10 or contact_rate < 0.10) and episodes > 5000

        if passed:
            return True, False, "기본 제구력 및 타격 대처 확보 (경쟁 준비 완료)"
        elif stuck:
            return False, True, f"Self-Play 탐색 정체 (Strike:{strike_rate:.1%}, Contact:{contact_rate:.1%})"
        else:
            return False, False, "Self-Play 탐색 학습 중"


class Phase6Gate(StageGate):
    def __init__(self):
        super().__init__("Phase 6: Competitive Self-Play", 6)

    def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
        """
        성공 기준:
          양측의 승률(Reward 우위)이 균형을 이루며(40~60%),
          고도화된 지표(Exit Velocity > 100km/h, Pitching Speed > 100km/h) 달성
        """
        batter_win_rate = metrics.get('batter_win_rate', 0.5)
        ev = metrics.get('avg_exit_velocity_kmh', 0.0)
        pitch_speed = metrics.get('avg_pitch_speed_kmh', 0.0)
        
        balance_ok = 0.40 <= batter_win_rate <= 0.60
        quality_ok = ev > 100.0 and pitch_speed > 100.0
        
        passed = balance_ok and quality_ok
        episodes = metrics.get('episodes_in_phase', 0)
        stuck = not passed and episodes > 10000

        if passed:
            return True, False, "고품질 경쟁적 Self-Play 달성 (인간 수준 근접)"
        elif stuck:
            return False, True, f"경쟁 고도화 정체 (WinRate:{batter_win_rate:.1%}, EV:{ev:.0f}, Pitch:{pitch_speed:.0f})"
        else:
            return False, False, "경쟁적 Self-Play 진행 중"


class Phase7Gate(StageGate):
    def __init__(self):
        super().__init__("Phase 7: World Model Mastery", 7)

    def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
        """
        성공 기준:
          World Model의 예측력(Prediction)과 상상 보상(Imagination Reward)이 최고 수준 도달
        """
        wm_loss_p = metrics.get('pitcher_wm_loss', 999.0)
        wm_loss_b = metrics.get('batter_wm_loss', 999.0)
        imag_rew_b = metrics.get('batter_imag_rew', 0.0)
        
        passed = wm_loss_p < 2.0 and wm_loss_b < 2.0 and imag_rew_b > 5.0
        episodes = metrics.get('episodes_in_phase', 0)
        stuck = not passed and episodes > 20000

        if passed:
            return True, False, "World Model 마스터리 달성 (최상위 성능)"
        elif stuck:
            return False, True, f"World Model 수렴 정체 (Loss P:{wm_loss_p:.1f} B:{wm_loss_b:.1f})"
        else:
            return False, False, "World Model 최적화 중"


class GateKeeper:
    """현재 Phase에 맞는 Gate를 관리합니다."""
    
    def __init__(self):
        self.gates = {
            1: Phase1Gate(),
            2: Phase2Gate(),
            3: Phase3Gate(),
            4: Phase4Gate(),
            5: Phase5Gate(),
            6: Phase6Gate(),
            7: Phase7Gate(),
        }
        
    def evaluate(self, phase_id: int, metrics: Dict[str, Any]) -> Tuple[bool, bool, str]:
        if phase_id not in self.gates:
            return False, False, f"Phase {phase_id}에 대한 Gate가 없습니다."
        return self.gates[phase_id].evaluate(metrics)
