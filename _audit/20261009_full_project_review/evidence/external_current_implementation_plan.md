# [Implementation Plan] Bipedal Catcher Squat Stance, Pitch Framing & Strike Zone Constraint Learning

## 1. 개요 및 배경 (Executive Overview)

사용자 피드백을 통해 기존 시뮬레이션의 핵심 결함이 규명되었습니다:
1. **투구 높이 불일치:** 바퀴/단일 상체 시절의 저타점($z=0.53\sim 0.58\text{m}$, 정강이 높이)이 전신 다리가 생긴 180cm H1 로봇에게 그대로 적용되어, 타자가 무릎 아래로 공을 억지로 찍어내리는 기괴한 폼이 양산됨.
2. **배터리(투수-포수) 기저 부재:** 타석 뒤에 포수가 없어 투수가 물리적 타겟(포수 미트) 없이 가상의 저좌표를 조준하고 있었음.

이에 따라, **"홈플레이트 뒤에 2족 보행 포수를 실제 야구처럼 안정적으로 쪼그려 앉히고(Catcher Squat), 포수 미트 프레이밍 및 포구 학습을 먼저 안정화한 뒤, 규격 스트라이크 존($z \in [0.65, 1.05]\text{m}$) 및 구종별 제약을 적용하는 배터리 기반 단계적 학습 전략"**을 수립합니다.

---

## 2. 세부 기술 아키텍처 (Technical Architecture)

```
[1단계: 포수 스쿼트 & 미트 구축]
  └─ models/h1_battery_pitch_catch.xml
  └─ 6-DoF 부유 골반 저중심 딥 스쿼트 (z_pelvis ≈ 0.52m, knee=1.85rad)
  └─ 왼손 포수 미트(c_mitt, r=0.14m) 및 오른손 안전 파지
       ▼
[2단계: 배터리 투포수 폐루프 훈련]
  └─ envs/battery_pitch_catch_env.py
  └─ 10m 마운드 투구(패스트볼/슬라이더/커브) 릴리스 (z_release ≈ 1.48m)
  └─ 포수 스쿼트 균형 유지 및 실시간 미트 이동 포구(Catch & Framing)
       ▼
[3단계: 규격 스트라이크 존 및 구종 제약 고정]
  └─ 홈플레이트 17인치 폭(x ∈ [-0.22, +0.22]m), 무릎~가슴(z ∈ [0.65, 1.05]m)
  └─ 구종별 마그누스 비행 궤적 및 존 관통 표준화
       ▼
[4단계: 타자 & 인필드 수비 재결합]
  └─ 양손 그립 애슬레틱 타격 폼(Ready → Load → Belt Impact → High Finish)
  └─ 포수-타자-투수-1루수가 완전 통합된 진짜 야구 폼 완성
```

---

## 3. 세부 구현 파일 및 변경 사항 (Proposed Changes)

### 3.1 [NEW] `models/h1_battery_pitch_catch.xml`
- **투수 (Pitcher `p_` on 10m Mound):**
  - 마운드 고도 $0.82\text{m}$, 오버핸드/스리쿼터 릴리스 암슬롯($z \approx 1.45 \sim 1.55\text{m}$).
- **포수 (Catcher `c_` behind Home Plate, $x=0.0\text{m}, y=-0.95\text{m}$):**
  - 6-DoF Pelvis Freejoint 완전 부유 골반 (인공 핀 관절 없음).
  - 딥 스쿼트 기본 관절각 (`hip_pitch = -1.10`, `knee = 1.85`, `ankle = -0.75`, `hip_roll = ±0.18`).
  - 골반 높이 $z_{pelvis} \approx 0.52\text{m}$로 지면에 낮게 밀착된 안정적 기저면.
  - 왼손 포수 미트 (`c_mitt`, $r = 0.14\text{m}$, 두께 $0.05\text{m}$, 고감쇠 완충 재질).
  - 오른손은 우측 허벅지 뒤로 보호 파지.
- **카메라 뷰:**
  - `umpire_cam`: 포수 뒤쪽 상단에서 투수와 스트라이크 존을 바라보는 방송 뷰.
  - `battery_side_cam`: 투수-홈플레이트-포수의 투구 궤적과 미트 안착을 측면에서 포착하는 뷰.

### 3.2 [NEW] `envs/battery_pitch_catch_env.py`
- **관측 공간 (Observation Space, 42 dims):**
  - 공의 3D 위치 및 속도 ($\mathbf{p}_{ball}, \mathbf{v}_{ball}$), 홈플레이트 도달 잔여 시간($t_{remain}$).
  - 포수 골반 6D 상태 ($\mathbf{p}_{c}, \mathbf{q}_{c}, \mathbf{v}_{c}, \boldsymbol{\omega}_{c}$).
  - 포수 미트 3D 위치 및 선속도 ($\mathbf{p}_{mitt}, \mathbf{v}_{mitt}$).
  - 목표 스트라이크 존 타겟점 ($\mathbf{p}_{target}$).
- **행동 공간 (Action Space, 5 dims):**
  - $a[0 \sim 2]$: 포수 미트 3D 프레이밍 오프셋 ($\Delta x, \Delta y, \Delta z$).
  - $a[3 \sim 4]$: 스쿼트 하체 ZMP 및 골반 피치 밸런스 보정 토크.
- **보상 함수 (Reward Function):**
  $$R = R_{catch} + 2.0 \cdot \exp(-10 \|\mathbf{p}_{ball} - \mathbf{p}_{mitt}\|^2) + R_{squat\_stability} - 0.05 \|\boldsymbol{\tau}\|^2$$
- **종료 조건:**
  - 포구 성공 (공이 미트 반경 $14\text{cm}$ 내 진입 및 감속 정지).
  - 포수 전도 ($z_{pelvis} < 0.35\text{m}$ 또는 $|pitch| > 35^\circ$).
  - 투구 포락 시간 초과 ($t > 0.80\text{s}$).

### 3.3 [NEW] `scripts/train_battery.py` & `scripts/eval_battery.py`
- PPO 알고리즘 기반 포수 미트 트래킹 및 스쿼트 기립 밸런스 훈련 (30,000 steps).
- 50 에피소드 정량 벤치마크:
  - 포수 직립/스쿼트 생존율 ($\ge 98\%$, 낙하 0건 목표).
  - 포구 성공률 (Catch Success Rate, $\ge 85\%$).
  - 미트-볼 정합 오차 (Framing MAE, $< 8\text{cm}$).
  - 스트라이크 존 규격 준수율 ($100\%$).
- 50 FPS 브로드캐스트 비디오 `logs/videos/battery_pitch_catch.mp4` 렌더링.

---

## 4. 검증 계획 (Verification Plan)

### 자동화 평가 및 메트릭
```bash
.venv/bin/python scripts/eval_battery.py --episodes 50
```
- 50회 연속 난수 시드 평가 결과 `logs/battery_benchmark_metrics.csv` 생성.

### 시각적 영상 검증 (Visual-First Standard)
- `battery_pitch_catch.mp4` 비디오 렌더링.
- 3대 핵심 키프레임 추출 및 `view_file`을 통한 사람 눈 수준의 자세 직접 검사:
  1. `battery_pitch_release.png`: 투수 릴리스 및 포수의 단단한 딥 스쿼트 대기 자세.
  2. `battery_pitch_approach.png`: 벨트/가슴 규격 스트라이크 존($z \approx 0.80\text{m}$)으로 비행하는 볼.
  3. `battery_mitt_catch.png`: 포수 미트에 공이 꽂히는 안정적인 포구 및 프레이밍 순간.

---

## 5. 승인 후 연계 작업 (Next Integration)
포수의 스쿼트 및 규격 스트라이크 존($z \in [0.65, 1.05]\text{m}$) 제구가 안정화되면:
1. 타자를 동일 필드 타석에 배치하고, 앞서 프로토타입으로 검증한 **양손 그립 애슬레틱 타격 폼**으로 허리 높이 정타 스윙을 결합.
2. 이후 1루수 내야 수비 및 1루 주루 경합을 다시 얹어 완벽한 비주얼의 야구 경기를 완성.
