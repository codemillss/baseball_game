"""
auto_game_builder.py — 완전 자동화 파이프라인의 오케스트레이터

이 스크립트는 야구 게임 환경 구축을 위한 전체 과정을 통제합니다.
각 Phase(학습 단계)를 실행하고, 평가(StageGate)하고, 막히면 진단(Diagnostician)하여
파라미터를 자동 조정(Plan Adjuster)합니다.
"""

import time
import json
from pathlib import Path
from typing import Dict, Any

from auto_builder.stage_gate import GateKeeper
from auto_builder.diagnostician import Diagnostician


class AutoGameBuilder:
    def __init__(self, log_dir: str = "logs"):
        self.gate_keeper = GateKeeper()
        self.diagnostician = Diagnostician()
        
        self.current_phase = 1
        self.max_phase = 7
        self.env_params = {
            "pitch_speed_max": 30.0,
            "release_distance": 18.44,
            "action_penalty_weight": 1.0,
            "swing_bonus": 1.0,
            "sweet_spot_bonus_weight": 1.0,
            "power_bonus_weight": 1.0,
        }
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.log_dir / "auto_builder_history.json"
        self.history = []

    def _log_event(self, event_type: str, details: Dict[str, Any]):
        event = {
            "time": time.time(),
            "phase": self.current_phase,
            "type": event_type,
            "details": details
        }
        self.history.append(event)
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def _train_cycle(self) -> Dict[str, Any]:
        """
        현재 설정(env_params)으로 N 에피소드만큼 훈련을 수행하고 메트릭을 반환합니다.
        (실제 환경 학습 루프 모킹 - 이후 curriculum_trainer 등과 연동)
        """
        print(f"\n[실행] Phase {self.current_phase} 학습 사이클 가동 중...")
        print(f"       현재 파라미터: {self.env_params}")
        
        # TODO: 실제 RL Trainer 연동
        # trainer = MultiAgentTrainer(phase=self.current_phase, **self.env_params)
        # metrics = trainer.train(episodes=100)
        
        # 임시 모의 메트릭 반환
        time.sleep(1)
        return {
            "episodes": 1500,
            "episodes_in_phase": 1500,
            "pitch_completion_rate": 0.85,
            "swing_completion_rate": 0.82,
            "avg_bat_speed_kmh": 65.0,
            "visual_tracking_rate": 0.95,
            "contact_rate": 0.25,
            "avg_exit_velocity_kmh": 85.0,
            "sweet_spot_rate": 0.35,
            "current_release_distance": self.env_params["release_distance"],
        }

    def run(self):
        print("=" * 60)
        print(" 🤖 AutoGameBuilder: 야구 게임 완전 자동화 구축 시작")
        print("=" * 60)

        while self.current_phase <= self.max_phase:
            print(f"\n=== [Phase {self.current_phase}] 시작 ===")
            
            # 1. 실행 및 성능 측정
            metrics = self._train_cycle()
            self._log_event("train_cycle", metrics)
            
            # 2. Gate 평가
            passed, stuck, reason = self.gate_keeper.evaluate(self.current_phase, metrics)
            print(f"[평가] {reason}")
            
            if passed:
                print(f"🎉 Phase {self.current_phase} 통과! 다음 단계로 진입합니다.")
                self._log_event("phase_passed", {"reason": reason})
                self.current_phase += 1
                
                # Phase 통과 시 파라미터 초기화/승격 로직 등
                if self.current_phase == 5:
                    print("🚀 Phase 5: 투수 에이전트 본격 학습 개시!")
            
            elif stuck:
                print(f"⚠️ 정체 감지 (Stuck). 진단 및 파라미터 조정을 시작합니다.")
                plan = self.diagnostician.diagnose(self.current_phase, metrics)
                
                if not plan:
                    print("❌ 진단기가 해결책을 찾지 못했습니다. 수동 개입이 필요합니다.")
                    break
                    
                print(f"[조정] 적용되는 파라미터 변경: {plan}")
                self.env_params.update(plan)
                self._log_event("plan_adjusted", plan)
            
            else:
                print(f"⏳ 학습 진행 중... (목표치 미달, 계속 훈련)")
                
            # 무한루프 방지 (실제 환경에서는 제외)
            break

        print("\n✅ AutoGameBuilder 루프 종료.")


if __name__ == "__main__":
    builder = AutoGameBuilder()
    builder.run()
