# baseball/archive/auto_builder/auto_game_builder.py

원본: [archive/auto_builder/auto_game_builder.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/auto_builder/auto_game_builder.py)

SHA256: `eff375cb4c09c4e53e7364d2c28331077f4dee1f13106c63f8f74f2fe432c1be`

전체 125행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `AutoGameBuilder` | ClassDef | 18 | 120 |
| `__init__` | FunctionDef | 19 | 37 |
| `_log_event` | FunctionDef | 39 | 48 |
| `_train_cycle` | FunctionDef | 50 | 75 |
| `run` | FunctionDef | 77 | 120 |

## 전체 원문

````text
    1 | """
    2 | auto_game_builder.py — 완전 자동화 파이프라인의 오케스트레이터
    3 | 
    4 | 이 스크립트는 야구 게임 환경 구축을 위한 전체 과정을 통제합니다.
    5 | 각 Phase(학습 단계)를 실행하고, 평가(StageGate)하고, 막히면 진단(Diagnostician)하여
    6 | 파라미터를 자동 조정(Plan Adjuster)합니다.
    7 | """
    8 | 
    9 | import time
   10 | import json
   11 | from pathlib import Path
   12 | from typing import Dict, Any
   13 | 
   14 | from auto_builder.stage_gate import GateKeeper
   15 | from auto_builder.diagnostician import Diagnostician
   16 | 
   17 | 
   18 | class AutoGameBuilder:
   19 |     def __init__(self, log_dir: str = "logs"):
   20 |         self.gate_keeper = GateKeeper()
   21 |         self.diagnostician = Diagnostician()
   22 |         
   23 |         self.current_phase = 1
   24 |         self.max_phase = 7
   25 |         self.env_params = {
   26 |             "pitch_speed_max": 30.0,
   27 |             "release_distance": 18.44,
   28 |             "action_penalty_weight": 1.0,
   29 |             "swing_bonus": 1.0,
   30 |             "sweet_spot_bonus_weight": 1.0,
   31 |             "power_bonus_weight": 1.0,
   32 |         }
   33 |         
   34 |         self.log_dir = Path(log_dir)
   35 |         self.log_dir.mkdir(parents=True, exist_ok=True)
   36 |         self.history_file = self.log_dir / "auto_builder_history.json"
   37 |         self.history = []
   38 | 
   39 |     def _log_event(self, event_type: str, details: Dict[str, Any]):
   40 |         event = {
   41 |             "time": time.time(),
   42 |             "phase": self.current_phase,
   43 |             "type": event_type,
   44 |             "details": details
   45 |         }
   46 |         self.history.append(event)
   47 |         with open(self.history_file, 'w') as f:
   48 |             json.dump(self.history, f, indent=2)
   49 | 
   50 |     def _train_cycle(self) -> Dict[str, Any]:
   51 |         """
   52 |         현재 설정(env_params)으로 N 에피소드만큼 훈련을 수행하고 메트릭을 반환합니다.
   53 |         (실제 환경 학습 루프 모킹 - 이후 curriculum_trainer 등과 연동)
   54 |         """
   55 |         print(f"\n[실행] Phase {self.current_phase} 학습 사이클 가동 중...")
   56 |         print(f"       현재 파라미터: {self.env_params}")
   57 |         
   58 |         # TODO: 실제 RL Trainer 연동
   59 |         # trainer = MultiAgentTrainer(phase=self.current_phase, **self.env_params)
   60 |         # metrics = trainer.train(episodes=100)
   61 |         
   62 |         # 임시 모의 메트릭 반환
   63 |         time.sleep(1)
   64 |         return {
   65 |             "episodes": 1500,
   66 |             "episodes_in_phase": 1500,
   67 |             "pitch_completion_rate": 0.85,
   68 |             "swing_completion_rate": 0.82,
   69 |             "avg_bat_speed_kmh": 65.0,
   70 |             "visual_tracking_rate": 0.95,
   71 |             "contact_rate": 0.25,
   72 |             "avg_exit_velocity_kmh": 85.0,
   73 |             "sweet_spot_rate": 0.35,
   74 |             "current_release_distance": self.env_params["release_distance"],
   75 |         }
   76 | 
   77 |     def run(self):
   78 |         print("=" * 60)
   79 |         print(" 🤖 AutoGameBuilder: 야구 게임 완전 자동화 구축 시작")
   80 |         print("=" * 60)
   81 | 
   82 |         while self.current_phase <= self.max_phase:
   83 |             print(f"\n=== [Phase {self.current_phase}] 시작 ===")
   84 |             
   85 |             # 1. 실행 및 성능 측정
   86 |             metrics = self._train_cycle()
   87 |             self._log_event("train_cycle", metrics)
   88 |             
   89 |             # 2. Gate 평가
   90 |             passed, stuck, reason = self.gate_keeper.evaluate(self.current_phase, metrics)
   91 |             print(f"[평가] {reason}")
   92 |             
   93 |             if passed:
   94 |                 print(f"🎉 Phase {self.current_phase} 통과! 다음 단계로 진입합니다.")
   95 |                 self._log_event("phase_passed", {"reason": reason})
   96 |                 self.current_phase += 1
   97 |                 
   98 |                 # Phase 통과 시 파라미터 초기화/승격 로직 등
   99 |                 if self.current_phase == 5:
  100 |                     print("🚀 Phase 5: 투수 에이전트 본격 학습 개시!")
  101 |             
  102 |             elif stuck:
  103 |                 print(f"⚠️ 정체 감지 (Stuck). 진단 및 파라미터 조정을 시작합니다.")
  104 |                 plan = self.diagnostician.diagnose(self.current_phase, metrics)
  105 |                 
  106 |                 if not plan:
  107 |                     print("❌ 진단기가 해결책을 찾지 못했습니다. 수동 개입이 필요합니다.")
  108 |                     break
  109 |                     
  110 |                 print(f"[조정] 적용되는 파라미터 변경: {plan}")
  111 |                 self.env_params.update(plan)
  112 |                 self._log_event("plan_adjusted", plan)
  113 |             
  114 |             else:
  115 |                 print(f"⏳ 학습 진행 중... (목표치 미달, 계속 훈련)")
  116 |                 
  117 |             # 무한루프 방지 (실제 환경에서는 제외)
  118 |             break
  119 | 
  120 |         print("\n✅ AutoGameBuilder 루프 종료.")
  121 | 
  122 | 
  123 | if __name__ == "__main__":
  124 |     builder = AutoGameBuilder()
  125 |     builder.run()
````
