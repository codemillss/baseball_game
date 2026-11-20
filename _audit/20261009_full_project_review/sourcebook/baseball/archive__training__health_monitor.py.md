# baseball/archive/training/health_monitor.py

원본: [archive/training/health_monitor.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/health_monitor.py)

SHA256: `5b975955d75465b080edf71af13535ffe457fa360ae9a5b91c748e7a5ae5c6d4`

전체 165행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `TrainingHealthMonitor` | ClassDef | 13 | 165 |
| `__init__` | FunctionDef | 20 | 33 |
| `record` | FunctionDef | 35 | 62 |
| `check_health` | FunctionDef | 64 | 132 |
| `get_summary` | FunctionDef | 134 | 148 |
| `safe_mean` | FunctionDef | 136 | 137 |
| `get_status_str` | FunctionDef | 150 | 165 |

## 전체 원문

````text
    1 | """
    2 | health_monitor.py — 학습 안정성 자동 감시 및 조기 경보 시스템
    3 | 
    4 | Policy Entropy, KL Divergence, Value Loss, Contact Rate, Win Rate 등의
    5 | 핵심 메트릭을 실시간 추적하고, 붕괴 징후를 조기에 감지합니다.
    6 | """
    7 | 
    8 | from collections import deque
    9 | from typing import Dict, List, Optional
   10 | import numpy as np
   11 | 
   12 | 
   13 | class TrainingHealthMonitor:
   14 |     """학습 상태 자동 감시 및 조기 경보.
   15 | 
   16 |     Args:
   17 |         window_size: 이동 평균 윈도우 크기
   18 |     """
   19 | 
   20 |     def __init__(self, window_size: int = 50):
   21 |         self.window_size = window_size
   22 | 
   23 |         # 메트릭 히스토리 (슬라이딩 윈도우)
   24 |         self.entropy_history = deque(maxlen=window_size)
   25 |         self.kl_history = deque(maxlen=window_size)
   26 |         self.value_loss_history = deque(maxlen=window_size)
   27 |         self.policy_loss_history = deque(maxlen=window_size)
   28 |         self.contact_rate_history = deque(maxlen=window_size)
   29 |         self.reward_history = deque(maxlen=window_size)
   30 |         self.grad_norm_history = deque(maxlen=window_size)
   31 | 
   32 |         # 알림 로그
   33 |         self.alerts: List[Dict] = []
   34 | 
   35 |     def record(self, metrics: Dict[str, float]):
   36 |         """학습 메트릭을 기록합니다.
   37 | 
   38 |         Args:
   39 |             metrics: {
   40 |                 'entropy': float,
   41 |                 'kl_divergence': float,
   42 |                 'value_loss': float,
   43 |                 'policy_loss': float,
   44 |                 'contact_rate': float,
   45 |                 'reward': float,
   46 |                 'grad_norm': float,  (optional)
   47 |             }
   48 |         """
   49 |         if "entropy" in metrics:
   50 |             self.entropy_history.append(metrics["entropy"])
   51 |         if "kl_divergence" in metrics:
   52 |             self.kl_history.append(metrics["kl_divergence"])
   53 |         if "value_loss" in metrics:
   54 |             self.value_loss_history.append(metrics["value_loss"])
   55 |         if "policy_loss" in metrics:
   56 |             self.policy_loss_history.append(metrics["policy_loss"])
   57 |         if "contact_rate" in metrics:
   58 |             self.contact_rate_history.append(metrics["contact_rate"])
   59 |         if "reward" in metrics:
   60 |             self.reward_history.append(metrics["reward"])
   61 |         if "grad_norm" in metrics:
   62 |             self.grad_norm_history.append(metrics["grad_norm"])
   63 | 
   64 |     def check_health(self) -> List[str]:
   65 |         """학습 상태를 검사하고 경보 메시지를 반환합니다.
   66 | 
   67 |         Returns:
   68 |             경보 메시지 리스트 (비어있으면 정상)
   69 |         """
   70 |         alerts = []
   71 | 
   72 |         # 1. Mode Collapse 감지: 엔트로피 급락
   73 |         if len(self.entropy_history) >= 10:
   74 |             recent_entropy = np.mean(list(self.entropy_history)[-10:])
   75 |             if recent_entropy < 0.01:
   76 |                 alerts.append(
   77 |                     "🚨 MODE COLLAPSE: 정책 엔트로피 극소 "
   78 |                     f"({recent_entropy:.4f}) → 정책 다양성 상실. "
   79 |                     "엔트로피 보너스 계수 증가 권장."
   80 |                 )
   81 | 
   82 |         # 2. KL Divergence 폭주: 정책 급변
   83 |         if len(self.kl_history) >= 5:
   84 |             recent_kl = np.mean(list(self.kl_history)[-5:])
   85 |             if recent_kl > 0.1:
   86 |                 alerts.append(
   87 |                     f"⚠️ KL SPIKE: 정책 급변 (KL={recent_kl:.4f} > 0.1). "
   88 |                     "학습률 자동 감소 또는 PPO clip 범위 축소 권장."
   89 |                 )
   90 | 
   91 |         # 3. Value Loss 발산
   92 |         if len(self.value_loss_history) >= 10:
   93 |             recent_vloss = np.mean(list(self.value_loss_history)[-10:])
   94 |             if recent_vloss > 100.0:
   95 |                 alerts.append(
   96 |                     f"🚨 CRITIC 발산: Value Loss 폭증 ({recent_vloss:.1f}). "
   97 |                     "학습 일시 중단 또는 학습률 감소 권장."
   98 |                 )
   99 | 
  100 |         # 4. Contact Rate 정체: 학습 신호 없음
  101 |         if len(self.contact_rate_history) >= 30:
  102 |             recent_cr = np.mean(list(self.contact_rate_history)[-30:])
  103 |             if recent_cr < 0.01:
  104 |                 alerts.append(
  105 |                     "⚠️ 학습 신호 없음: Contact Rate 0%에 수렴. "
  106 |                     "커리큘럼 난이도 하향 또는 Distance Shaping 활성화 권장."
  107 |                 )
  108 | 
  109 |         # 5. Gradient Norm 폭발
  110 |         if len(self.grad_norm_history) >= 5:
  111 |             recent_gn = np.mean(list(self.grad_norm_history)[-5:])
  112 |             if recent_gn > 10.0:
  113 |                 alerts.append(
  114 |                     f"⚠️ GRADIENT 폭발: Grad Norm={recent_gn:.1f}. "
  115 |                     "Gradient Clipping 강화 권장."
  116 |                 )
  117 | 
  118 |         # 6. 보상 급격한 하락 (최근 vs 과거 비교)
  119 |         if len(self.reward_history) >= 40:
  120 |             early = np.mean(list(self.reward_history)[:20])
  121 |             late = np.mean(list(self.reward_history)[-20:])
  122 |             if late < early - 5.0:
  123 |                 alerts.append(
  124 |                     f"⚠️ 보상 급락: {early:.2f} → {late:.2f}. "
  125 |                     "정책 붕괴 또는 과적합 가능성."
  126 |                 )
  127 | 
  128 |         # 알림 저장
  129 |         for alert in alerts:
  130 |             self.alerts.append({"message": alert})
  131 | 
  132 |         return alerts
  133 | 
  134 |     def get_summary(self) -> Dict[str, float]:
  135 |         """현재 모니터링 요약을 반환합니다."""
  136 |         def safe_mean(d):
  137 |             return float(np.mean(list(d))) if len(d) > 0 else 0.0
  138 | 
  139 |         return {
  140 |             "avg_entropy": safe_mean(self.entropy_history),
  141 |             "avg_kl": safe_mean(self.kl_history),
  142 |             "avg_value_loss": safe_mean(self.value_loss_history),
  143 |             "avg_policy_loss": safe_mean(self.policy_loss_history),
  144 |             "avg_contact_rate": safe_mean(self.contact_rate_history),
  145 |             "avg_reward": safe_mean(self.reward_history),
  146 |             "avg_grad_norm": safe_mean(self.grad_norm_history),
  147 |             "total_alerts": len(self.alerts),
  148 |         }
  149 | 
  150 |     def get_status_str(self) -> str:
  151 |         """현재 상태를 사람이 읽을 수 있는 문자열로 반환합니다."""
  152 |         s = self.get_summary()
  153 |         status = "✅ HEALTHY"
  154 |         recent_alerts = self.check_health()
  155 |         if recent_alerts:
  156 |             status = "⚠️ ALERT"
  157 | 
  158 |         return (
  159 |             f"[{status}] "
  160 |             f"Entropy={s['avg_entropy']:.3f} | "
  161 |             f"KL={s['avg_kl']:.4f} | "
  162 |             f"VLoss={s['avg_value_loss']:.2f} | "
  163 |             f"CR={s['avg_contact_rate']:.1%} | "
  164 |             f"Reward={s['avg_reward']:+.2f}"
  165 |         )
````
