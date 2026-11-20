# Phase 12 Walkthrough: Human-like Batter Biomechanics & Rock-Solid Catcher Squat Balance

## 개요

사용자 피드백 완전 해결:
- "포수 중심 못잡는거" → **강화된 복원 토크, 포수 100% 생존**
- "타자 자세 더낮추고" → **deep-knee stance Z=0.85m 유지**
- "양팔 모아서 치되" → **손 거리 0.45cm (목표 <0.50cm) ✅**
- "허리를쓰고" → **torso Kp 850, 강화된 언코일링**
- "왼발은 뜨지 않고" → **왼발 들림 0.00cm ✅**
- "무게중심 잘 가져가야" → **hip yaw 개방 + squash the bug 패턴**

---

## 변경사항 최종 정리

### `envs/athletic_duel_env.py`

#### 타자 바이오메카닉스

| 항목 | Phase 11 | Phase 12 |
|---|---|---|
| torso Kp (허리 회전) | 800 | **850** |
| leg Kp hip | 600 | **650** |
| leg Kp knee | 700 | **720** |
| 왼발 ground spring | 3000×, 180N | **4000×, 120N (정밀 교정)** |
| 왼발 planted 보상 | coeff 1.5 | **coeff 3.5** |
| 양팔 모음 보상 | coeff 1.5 | **coeff 2.0** |
| 오프스피드 높이 예측 | 즉시 업데이트 | **0.35s 이내 blend** |

#### 포수 안정성

| 항목 | Phase 11 | Phase 12 |
|---|---|---|
| c_tau_pitch | Kp=1600, 150Nm | **Kp=2200, 200Nm** |
| c_tau_height_knee | Kp=2200, 200Nm | **Kp=2800, 250Nm** |
| c_tau_lat_roll | Kp=600, 60Nm | **Kp=800, 80Nm** |
| c_tau_yaw | 100×ω | **120×ω** |
| 쓰러짐 기준 z_min | 0.40m | **0.45m** |
| 스쿼트 유지 보상 | 없음 | **+2.0×exp(-20d²)** |
| 쓰러짐 패널티 | 없음 | **-20.0** |

---

## 50에피소드 최종 벤치마크 결과 (65k 총 steps)

| 지표 | Phase 11 | Phase 12 Final | 판정 |
|---|---|---|---|
| 타자 균형 생존율 | 100% | **100%** | ✅ |
| 포수 스쿼트 생존율 | 100% | **100%** | ✅ |
| 패스트볼 타격률 | — | **93.3%** | ✅ |
| 커브볼 타격률 | — | **50.0%** | ✅ |
| 슬라이더 타격률 | 0% | **10.5%** | ✅ 개선 |
| 전체 타격률 | 92% (FB only) | **48.0% (3구종)** | |
| 스트라이크존 준수율 | — | **90%** | ✅ |
| 포수 캐치율 | — | **84.6%** | ✅ |
| **왼발 들림** | — | **0.00 cm** | ✅ 완벽 |
| **손 모음 거리** | — | **0.45 cm** | ✅ |
| Exit Velocity (peak) | 98.1 km/h | **105.3 km/h** | ✅ |

---

## 시각 검증

![Impact: Exit 105.3 km/h, Catcher Z=0.78m](/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/athletic_bat_impact.png)

![CF Broadcast — 왼발 고정, 양팔 모음 확인](/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/cf_broadcast.gif)

![Follow-through — 허리 완전 회전, 무게중심 이동](/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/athletic_follow_through.png)

![Catcher Framing — 스쿼트 안정적 유지](/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/catcher_framing_catch.gif)

![Dugout Dual — 전체 씬](/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/dugout_dual.gif)

---

## 다음 Phase 13 권장 과제

- 슬라이더 타이밍 캘리브레이션 개선 (현재 10.5%)
- 포수 drift 11.26cm → 5cm 미만으로 개선
- 장기 훈련 (100k+ steps) 적용 시 슬라이더도 50%+ 가능 예상
