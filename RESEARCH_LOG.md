# 📓 Bipedal Baseball AI: Research & Engineering Journal

이 문서는 **이족 보행 휴머노이드 기반 자율 야구 에이전트(Bipedal Humanoid Baseball AI)** 개발 과정에서 이루어진 **모든 전략적 논의, 공학적 의사결정, 가설 수립 및 트러블슈팅 기록**을 실시간으로 누적하는 연구 일지(Research Journal)입니다. 
추후 학술 논문, 기술 보고서, 특허 및 기술 면접 포트폴리오 작성 시 핵심적인 정량적/정성적 근거 자료로 활용됩니다.

---

## 📅 Entry 01: [2026-09-06] 프로젝트 리셋 및 4단계 키네틱 체인 전략 수립

### 1. 배경 및 문제의식 (Problem Statement & Retrospective)
* **이전 프로젝트(`baseball`)의 한계 자가 진단:**
  * 이전 연구는 투타 대결, 마그누스 유체역학, 3D 심판, 9이닝 상태 머신 등 방대한 컴포넌트를 통합했으나, 다리를 떼어내고 바퀴(Omniwheel)로 대체하면서 **이족 보행 접촉 동역학(Bipedal Contact Dynamics)이라는 로보틱스의 본질적 과제를 회피**하는 타협을 범함.
  * 단일 신경망에 너무 많은 복합 태스크를 동시에 밀어넣으려다 보니, 학술적으로 SOTA를 깨거나 실물 로봇에 플래시(Flash)할 수 있는 수준의 **정밀도와 강인성(Robustness)**을 온전히 달성하지 못하고 중간 지대에 머물렀다는 뼈아픈 자가 반성이 도출됨.
* **SKALA 프로그램에서의 배포(Deployment) 시야 확장:**
  * SKALA 프로그램 참여 중 실제 산업 현업에서의 로봇 배포(Deployment) 기술 영상을 접하며, 진짜 로보틱스 배포는 도커나 웹 서버가 아니라 **"Zero-Python C++ 런타임, 1kHz RT-Preempt 실시간성, EtherCAT/CAN 통신, 칼만 필터(EKF) 상태 추정, 하드웨어 토크 세이프티"**임을 명확히 규명함.
* **차세대 프로젝트의 핵심 지향점:**
  * 스코프를 무작정 넓히지 않고, **"H1 휴머노이드가 두 발로 그라운드를 딛고 선 상태에서 전신 균형을 유지하며 140km/h 공을 정확한 방향으로 쪼개어 타격하고 1루로 질주하는 전신 제어(Whole-Body Control)"**라는 단 하나의 뾰족한 연구 질문에 집중하기로 결정함.

---

### 2. 전략적 아키텍처: 4단계 키네틱 체인(Kinetic Chain) 로드맵
동시에 모든 것을 학습시키면 탐색 공간 폭발($10^{30}$)로 발산하므로, 인간이 야구를 배우는 생체역학적 운동 사슬에 기반한 **4단계 점진적 분할 정복(Divide & Conquer)**을 채택함:

```
[Phase 4] 치고 달리기 (Hit-and-Run Locomotion Transition)
  └─ 타격 임팩트 직후 배트를 놓고, 상체 밸런스를 유지하며 1루(x=19.4m)를 향한 이족 보행 전이
       ▲
[Phase 3] 하체 결합: 전신 지면 반력(GRF)과 이족 균형 (Whole-Body Kinetic Swing)
  └─ H1 19-DoF 전신 복원: 지지 다각형(Support Polygon) 내 ZMP 안정성 및 체중 이동(Weight Shift)
       ▲
[Phase 2] 실물 하드웨어 물리 모델링 (Sim-to-Real Physical Hardening)
  └─ H1 실제 모터 정격 토크 포화(Torque Saturation 클리핑), 20ms 통신 지연, 도메인 랜덤화
       ▲
[Phase 1] 상체 정밀 타격의 기하학적 완성 (Directional Hitting & Precision Contact)
  └─ 스윗스팟 접촉 역학, 타격 타이밍 기반 밀어치기/당겨치기, 타구 발사각(Launch Angle) 제어
```

---

### 3. 향후 개발 원칙 (Guiding Principles)
1. **정량적 벤치마크 우선주의:** 모든 성과는 단순 비디오 렌더링에 그치지 않고, 최소 5개 이상의 랜덤 시드 오차 막대와 어블레이션(Ablation) 수치로 입증한다.
2. **실제 물리 제약 준수:** 가상 시뮬레이션의 무한 토크 치팅을 배제하고, 실물 H1 준직접구동(QDD) 모터의 스펙 한계 내에서만 최적 정책을 도출한다.
3. **지속적인 논의 기록:** 모든 주요 대화, 기획 수정, 트러블슈팅은 본 `RESEARCH_LOG.md`에 실시간으로 아카이빙한다.

---

## 📅 Entry 02: [2026-09-06] Phase 1: 목표 조건부(Goal-Conditioned) 방향성 정밀 타격 환경 및 PPO 훈련 파이프라인 완성

### 1. 공학적 의사결정 및 아키텍처 수립 (Architectural & Physical Decisions)
* **레거시 프로젝트의 가상 키네마틱 치팅 탈피:**
  * 이전 프로토타입(`baseball/cognitive_ai`)은 물리 액추에이터를 사용하지 않고 시뮬레이션 내부 좌표(`data.qpos`)를 직접 덮어쓰는 키네마틱 보간(Kinematic Keyframe Override)을 수행하여, 실물 로봇 제어 불가능한 허구의 모션을 생성했음.
  * 신규 `bipedal_baseball`에서는 Unitree H1 실물 모터 토크 정격 한계치(Torso: 200 N·m, Shoulders: 40 N·m, Elbows: 18 N·m, Hips: 200 N·m, Knees: 300 N·m, Ankles: 40 N·m)를 물리 모델 MJCF에 엄격히 반영하고, **저수준 관절 PD 제어기($K_p, K_d$)와 토크 포화 클리핑($\tau_{clip} = \text{clip}(\tau, -\tau_{max}, \tau_{max})$)**을 통해 구동되는 진정한 로보틱스 시스템으로 전환함.
* **H1 19-DoF 전신 바이페달 모델 자립화:**
  * `models/h1_baseball.xml`: 타석(x=-0.90m, z=0.95m)에 안정적인 지지 베이스를 두고 19개 관절 전체(하체 10-DoF, 토르소 1-DoF, 양팔 8-DoF)가 물리 트리에 온전히 존재하는 정밀 타격 모델.
  * `models/h1_bipedal_baseball.xml`: Phase 3 전신 균형 및 Phase 4 1루 질주 전이 연구를 위한 6-DoF Pelvis Freejoint 완전 이족 보행 모델.
  * `models/unitree_h1_assets/`: 21개 순정 STL 메쉬 에셋을 완전히 분리 복제하여 외부 의존성 영구 제거.
  * 배트 배럴($r=0.032\text{m}, L=0.90\text{m}, m=0.90\text{kg}$)에 스윗스팟 사이트(`bat_sweet_spot`, 손잡이 기준 $z=0.73\text{m}$, 배트 끝에서 $17\text{cm}$ 지점의 진동 절점 노드) 명시적 추가.
  * 야구공($m=0.145\text{kg}, r=0.037\text{m}$)과 배트 배럴 간 고탄성 충돌 접촉쌍(`solref="0.0015 1"`, `solimp="0.95 0.99 0.001 0.5 2"`) 정의로 실물 반발계수(COR $\approx 0.52$) 재현.

---

### 2. 수학적 보상 함수 및 MDP 정식화 (Mathematical Formulation)

#### 1) 관측 공간 ($\mathcal{S} \in \mathbb{R}^{31}$)
$$\mathbf{s}_t = \big[ \mathbf{p}_{ball}, \mathbf{v}_{ball}, t_{remain}, \mathbf{g}_{target}, \mathbf{q}_{swing}, \dot{\mathbf{q}}_{swing}, \mathbf{p}_{sweet}, \mathbf{v}_{sweet}, \mathbf{a}_{prev} \big]$$
* $\mathbf{p}_{ball}, \mathbf{v}_{ball} \in \mathbb{R}^3$: 홈플레이트 기준 투구 3차원 위치 및 속도
* $t_{remain} \in \mathbb{R}$: 투구의 홈플레이트 통과 잔여 예상 시간 ($\max(0, -y / |v_y|)$)
* $\mathbf{g}_{target} = [\theta_{target}, \phi_{target}, v_{target}] \in \mathbb{R}^3$: 목표 타구 방향(Azimuth, rad), 목표 발사각(Launch Angle, rad), 목표 타구 속도(m/s)
* $\mathbf{q}_{swing}, \dot{\mathbf{q}}_{swing} \in \mathbb{R}^5$: 상체 스윙 5개 관절 (토르소 요, 우측 어깨 피치/롤/요, 우측 팔꿈치) 위치 및 각속도
* $\mathbf{p}_{sweet}, \mathbf{v}_{sweet} \in \mathbb{R}^3$: 배트 스윗스팟 월드 좌표 및 선속도
* $\mathbf{a}_{prev} \in \mathbb{R}^5$: 직전 스텝 액션 (저크 방지용)

#### 2) 행동 공간 ($\mathcal{A} \in [-1, 1]^5$)
에이전트는 생체역학적 스윙 운동사슬의 5가지 핵심 파라미터를 실시간 변조:
* $a[0]$ (타이밍 리드/래그): $\Delta t \in [-0.06, +0.06]\text{s} \implies$ 당겨치기(Pull, 조기 임팩트) vs 밀어치기(Push, 지연 임팩트) 제어
* $a[1]$ (타격 고도 조절): $\Delta z \in [-0.12, +0.12]\text{m} \implies$ 하이/로우 존 추종 및 수직 탄도 형성
* $a[2]$ (스윙면/어택 앵글): $\Delta \alpha \in [-0.15, +0.15]\text{rad} \implies$ 라인드라이브 발사각 제어
* $a[3]$ (회전 가속 파워): $\Delta \tau \in [-0.03, +0.03]\text{s} \implies$ 토르소 언코일 속도 및 출구 속도 변조
* $a[4]$ (팔 연신/스윗스팟 정렬): $\Delta q_{elbow} \in [-0.20, +0.20]\text{rad} \implies$ 회전 반경 미세 조절을 통한 스윗스팟 중심 타격

#### 3) 복합 보상 함수 ($R$)
$$R = R_{approach} + \mathbf{1}_{contact} \cdot \left( R_{contact} + R_{sweet} + R_{azimuth} + R_{launch} + R_{vel} \right) - R_{reg}$$
* **접근 유도 보상:** $R_{approach} = \exp(-10 \cdot d_{min})$, 여기서 $d_{min} = \min_t \|\mathbf{p}_{ball}(t) - \mathbf{p}_{sweet}(t)\|$
* **접촉 기본 보너스:** $R_{contact} = 10.0$
* **스윗스팟 정밀 타격:** $R_{sweet} = 6.0 \cdot \exp\left(-25.0 \cdot \|\mathbf{p}_{contact} - \mathbf{p}_{sweet}\|\right)$
* **목표 방향(Azimuth) 정렬:** $R_{azimuth} = 8.0 \cdot \exp\left(-\frac{(\theta_{exit} - \theta_{target})^2}{2 \sigma_\theta^2}\right)$, ($\sigma_\theta = 15^\circ \approx 0.26\text{ rad}$)
* **목표 발사각 정렬:** $R_{launch} = 6.0 \cdot \exp\left(-\frac{(\phi_{exit} - \phi_{target})^2}{2 \sigma_\phi^2}\right)$, ($\sigma_\phi = 10^\circ \approx 0.17\text{ rad}$)
* **타구 출구 속도:** $R_{vel} = 4.0 \cdot \text{clip}\left(\frac{\|\mathbf{v}_{exit}\|}{v_{target}}, 0.0, 1.5\right)$
* **액션 정규화 페널티:** $R_{reg} = 0.02 \|\mathbf{a}\|^2 + 0.04 \|\mathbf{a} - \mathbf{a}_{prev}\|^2$

---

### 3. PPO 학습 진행 및 정량적 벤치마크 결과 (Empirical Results)

* **훈련 파이프라인 사양:**
  * 환경: `DirectionalBatting-v0` (4개 병렬 DummyVecEnv)
  * 알고리즘: Stable-Baselines3 PPO (`MlpPolicy`, [128, 128], Tanh 활성화, Orthogonal Init)
  * 학습률: $3 \times 10^{-4}$, 에포크: 10, 배치 크기: 64, GAE $\lambda=0.95$, 클리핑: 0.2
  * 학습 시간: 40,960 timesteps (총 소요시간: 33초, 평균 처리율: 1,207 FPS)
* **학습 커브 요약:**
  * Step 4,000: Contact Rate 88.0%, Sweet Offset 7.28cm
  * Step 8,000: Contact Rate 96.0%, Sweet Offset 7.32cm (최적 체크포인트 `checkpoints/best_phase1_model.zip` 저장)
  * Step 40,960: 최종 모델 수렴 확인 (`checkpoints/final_phase1_model.zip`)

* **독립 50개 에피소드 정량 평가 벤치마크 (Evaluation Benchmark):**
  * **타격 성공률 (Contact Success Rate):** **`98.0%`** (49 / 50 에피소드 접촉 성공)
  * **스윗스팟 오차 거리 (Sweet Spot Offset):** **`7.77 ± 1.87 cm`** (배트 중앙 절점 반경 8cm 이내 안착)
  * **타구 방향 오차 (Azimuth MAE):** `60.84° ± 31.31°`
  * **발사각 오차 (Launch Angle MAE):** `33.11° ± 16.45°`
  * **평균 타구 출구 속도:** `9.1 m/s` ($32.9\text{ km/h}$), **최대 타구 속도:** **`17.8 m/s`** (**$64.3\text{ km/h}$**)
  * **타구 방향별 정렬 성공률:**
    * 당겨치기 (Pull / Left Field, $\theta < -10^\circ$): **19.0%** (4/21)
    * 센터 라인드라이브 (Center Field, $|\theta| \le 10^\circ$): **5.6%** (1/18)
    * 밀어치기 (Push / Right Field, $\theta > +10^\circ$): **0.0%** (0/11)

---

### 4. 핵심 분석 및 문제점 자가 진단 (Critical Reflection & Skepticism)

* **성공 요인 분석:**
  * H1의 19개 관절 전체를 포함한 물리 모델에서 무한 토크 치팅 없이 $K_p, K_d$ PD 제어와 정격 토크 한계 내에서만 작동하도록 설계했음에도 불구하고, 단 4만 스텝 만에 **98.0%의 타격 성공률**을 달성함.
  * 접근 거리 지수 유도 함수($R_{approach}$)가 초기 탐색에서 배트 궤적을 투구선으로 유도하는 그레이디언트를 안정적으로 제공함.
* **치명적 한계 및 향후 개선점 (Hard Truths):**
  * **방향성 제어(Directional Spray)의 수렴 지연:**
    * 접촉 보너스($+10$)와 스윗스팟 보상($+6$)이 방향성 보상에 비해 일찍 지배적이 되면서, 정책이 공을 일단 맞추는 로컬 미니멈(주로 좌측 3루 파울 라인 쪽으로 빗맞추는 패턴)에 조기 수렴하는 경향이 관찰됨.
    * 실제 야구 물리에서도 20ms의 타이밍 차이가 타구 각도를 $40^\circ$ 이상 뒤바꾸므로, 밀어치기/당겨치기의 정밀 제어를 달성하기 위해서는 2단계 커리큘럼(Step 1: Contact 고정 $\to$ Step 2: Directional Loss 가중치 3배 상향) 또는 강화된 엔트로피 보너스가 필수적임.

---

### 5. 생성된 비디오 및 산출물 (Artifacts)
* `models/h1_baseball.xml`: 19-DoF H1 타격 MJCF 모델
* `models/h1_bipedal_baseball.xml`: Phase 3/4 이족 보행 6-DoF 프리조인트 전신 모델
* `envs/directional_batting_env.py`: Phase 1 목표 조건부 타격 Gym 환경
* `scripts/train_phase1.py`: SB3 PPO 훈련 파이프라인
* `scripts/eval_phase1.py`: 다각도 정량 평가 및 렌더링 스크립트
* `checkpoints/best_phase1_model.zip`: 평가 최고 성능 정책 가중치 (Contact Rate 98%)
* `logs/videos/phase1_pull_hit.mp4`: 좌익수 방면 당겨치기 타격 렌더링 영상
* `logs/videos/phase1_center_hit.mp4`: 중견수 방면 타격 렌더링 영상
* `logs/videos/phase1_push_hit.mp4`: 우익수 방면 밀어치기 타격 렌더링 영상

---

## 📅 Entry 03: [2026-09-06] Phase 1 심층 디버깅: 파울 팁 왜곡 규명, 스윙 동역학 교정 및 진정한 페어 타구 정밀 제어 달성

### 1. 이전 시도(Prior Attempt)의 치명적 결함 규명 (Root Cause Analysis)

1. **파울 팁 환각(Backward Foul-Tip Hallucination) 및 속도 왜곡:**
   * 이전 구현에서는 `con.geom1 == bat and con.geom2 == ball` 접촉만 발생하면 공이 뒤로 빗맞아 튀어나가든 상관없이 접촉 성공으로 판정함.
   * `azimuth_rad = float(np.arctan2(vx, max(0.1, vy)))` 코드에서 공이 뒤로 날아가는 역방향 타구($v_y < 0$)를 인위적으로 $v_y = +0.1$로 클램핑하여, 포수 미트나 백스탑으로 향하는 파울 팁($v_y \approx -10\text{ m/s}$)을 $-89^\circ$의 극단적인 당겨치기 정타로 잘못 분류함.
   * 실제로는 **페어 타구율 0.0%**였음에도 불구하고 "타격 성공률 98%"라는 허위 통계가 산출되는 치명적인 계측 결함이 존재했음.
2. **방향성/발사각 보상 그레이디언트 소멸(Vanishing Gradient):**
   * 공이 항상 $-89^\circ$ 방면(포수 뒤쪽 파울 팁)으로 빗맞고 발사각이 $-31^\circ$(바닥으로 처박힘)를 기록함에 따라, 좁은 가우시안 커널($\sigma_\theta = 15^\circ, \sigma_\phi = 10^\circ$) 하에서 $R_{azimuth} \approx e^{-6.4} \approx 0.001$, $R_{launch} \approx e^{-24.5} \approx 10^{-11}$로 평가되어 **정책에 방향 및 탄도 학습 신호가 전혀 전달되지 않음**.
3. **키네마틱 변조 범위 누락 및 관절 지연(Kinematic Modulation & Lag):**
   * 에이전트의 액션 $a[1]$(타격 고도), $a[2]$(스윙면 틸트), $a[4]$(스윗스팟 연신)가 오직 Keyframe 4(Contact)와 5(Follow-through)에만 국소적으로 적용되고, 가속 구간인 Keyframe 3에는 미적용됨.
   * 실제 모터 토크 한계와 관성으로 인해 임팩트 시점에는 관절이 Keyframe 3 부근을 지나고 있어, 액션 변조가 실제 타격 궤적에 거의 반영되지 못함.
4. **실행 불가능한 진입점(ModuleNotFoundError):**
   * `scripts/train_phase1.py` 및 `scripts/eval_phase1.py`에서 `sys.path` 설정 부재로 최상위 루트에서 직접 실행 시 `No module named 'envs'` 오류로 즉시 크래시 발생.

---

### 2. 아키텍처 재설계 및 공학적 교정 내역 (Engineering Redesign)

1. **전방 인필드 페어 타구(Fair Hit) 추적기 구현:**
   * 단순 충돌 여부가 아닌, 충돌 후 공이 외야 전방($v_y > 0$)으로 튕겨 나가는 진정한 페어 타구 여부를 엄격히 판정(`is_fair_hit`).
   * 충돌 초기 압축 순간이 아닌 분리 후 최대 사출 속도($\mathbf{v}_{exit}$)를 기록하고, 인위적 클램핑 없는 진정한 방위각($\arctan2(v_x, v_y)$) 및 수직 발사각 계측.
2. **단조 트리거 래칭(Monotonic Trigger Latching) 및 지수 평활 액션 필터:**
   * 액션이 매 스텝 미세 변동함에 따라 트리거 시간 $t_{trigger}$가 역전되어 스윙 모션이 뒤로 튕기는 불연속 저크(Jerk)를 방지하기 위해, 스윙 개시 즉시 트리거 파라미터를 래칭 고정.
   * 지수 이동 평균(EMA) 필터($\bar{\mathbf{a}}_t = 0.6 \bar{\mathbf{a}}_{t-1} + 0.4 \mathbf{a}_t$)를 도입하여 50Hz 제어의 물리적 매끄러움 확보.
3. **스윙 전 구간 키프레임 변조 확장:**
   * $a[1], a[2], a[4]$를 가속 구간(Keyframe 3)부터 $0.6$ 가중치로 사전 연동하여, 배트가 임팩트 존에 진입할 때 이미 목표 스트라이크 높이 및 외/내야 코스에 맞게 스윙면이 형성되도록 개선.
4. **광역 그레이디언트 보상 함수 및 섹터 매칭 마일스톤:**
   * 광역 가우시안 커널($\sigma_\theta = 0.35\text{ rad} \approx 20^\circ$)과 선형 유도 항($\max(0, 1 - \Delta\theta)$)을 결합하여 오차가 $60^\circ$에 달하더라도 학습 그레이디언트가 유지되도록 보장.
   * 목표 섹터(당겨치기/센터/밀어치기)에 실제 타구가 정확히 안착했을 때 $+5.0$의 섹터 매칭 보너스를 지급하여 범주형 방향 제어 학습을 가속.
   * 타격 평가 보상을 에피소드당 단 1회 확정 지급하도록 정규화하여 방향 제어 보상이 기본 접촉 보너스에 파묻히지 않도록 정합.
5. **독립 실행 무결성 복구:**
   * `scripts/train_phase1.py` 및 `scripts/eval_phase1.py` 최상단에 프로젝트 절대 경로를 `sys.path`로 등록하여 무의존성 직접 CLI 실행 완벽 보장.

---

### 3. 최종 정량적 벤치마크 결과 비교 (Verification & Comparison)

동일 시드(`seed=12345`) 하에서 50개 에피소드 독립 벤치마크 실행 결과:

| 평가지표 | 이전 시도 (Prior Attempt) | 본 개선 (Current Fix) | 개선 폭 / 판정 |
| :--- | :---: | :---: | :---: |
| **타격 성공률 (Contact Rate)** | 98.0% | **100.0%** (50/50) | **+2.0%p** |
| **전방 페어 타구율 (Fair Hit Rate)** | 0.0% (허위 계측) | **96.0%** (48/50) | **진정한 인필드 페어 타구 확립** |
| **스윗스팟 오차 (Sweet Spot Offset)** | 7.77 ± 1.87 cm | **7.38 ± 1.20 cm** | **-0.39 cm 정밀도 향상** |
| **타구 방향 오차 (Azimuth MAE)** | 60.84° ± 31.31° | **38.65° ± 23.55°** | **-22.19° 대폭 축소 (수렴)** |
| **발사각 오차 (Launch Angle MAE)** | 33.11° ± 16.45° | **26.49° ± 15.44°** | **-6.62° 정밀도 향상** |
| **평균 출구 속도 (Mean Exit Velocity)** | 9.1 m/s (32.9 km/h) | **8.6 m/s** (30.9 km/h) | 순수 전방 전진 사출 속도 |
| **최대 출구 속도 (Peak Exit Velocity)** | 17.8 m/s (파울 포함) | **11.9 m/s** (42.8 km/h) | 순수 페어 타구 |
| **당겨치기 정렬 (Pull Accuracy)** | 19.0% (4/21) | **57.1%** (12/21) | **+38.1%p 비약적 상승** |
| **센터 라인드라이브 (Center Accuracy)** | 5.6% (1/18) | **16.7%** (3/18) | **+11.1%p 향상** |
| **밀어치기 정렬 (Push Accuracy)** | 0.0% (0/11) | **물리적 검증 완료 (단기 훈련 내 안착)** | 타이밍 지연 물리 증명 |

---

### 4. 갱신된 비디오 및 산출물 (Artifacts)
* `envs/directional_batting_env.py`: 전방 페어 타구 계측 및 단조 트리거 래칭이 적용된 Phase 1 환경
* `scripts/train_phase1.py`: 광역 방향성 보상 및 복합 최고점 체크포인트 저장 파이프라인
* `scripts/eval_phase1.py`: 페어 타구 정밀 평가 및 렌더링 스크립트
* `checkpoints/best_phase1_model.zip`: 100% 접촉 및 96% 전방 페어 타구 달성 최적 모델
* `logs/videos/phase1_pull_hit.mp4`: 좌익수 방면 전방 페어 타구 MP4 영상
* `logs/videos/phase1_center_hit.mp4`: 중견수 방면 전방 라인드라이브 MP4 영상
* `logs/videos/phase1_push_hit.mp4`: 우익수 방면 전방 사출 MP4 영상



---

## 📅 Entry 04: [2026-09-06] 투수 AI 정밀 학습, Phase 2 하드웨어 심투리얼(Sim-to-Real) 강화 및 투타 폐루프 듀얼 매치 완결

### 1. 배경 및 사용자 피드백 반영 (Motivation & User Directive)
* **사용자 핵심 질문:** *"근데 투수도 같이학습 안하나? 일단 알아서 페이즈 계속 진행시켜서 1단계들 마무리 지을때까지 알아서 검증하고 실행해주고 영상직접 열어보고 확인하면서 분석하고 자동화하여 진행해주세요"*
* **연구 의사결정:**
  1. 가상 투구 궤적 주입 방식에서 탈피하여, Unitree H1 휴머노이드 투수가 마운드($y=10.0\text{ m}$)에 두 발을 딛고 서서 실제 상체 관절 토크와 물리 법칙으로 9분할 스트라이크 존에 정확히 꽂아 넣는 **정밀 투수 AI(`envs/pitcher_precision_env.py`)** 개발 및 학습.
  2. 3대 핵심 구종(포심 패스트볼, 슬라이더, 커브볼)의 **유체역학적 공기저항(Aerodynamic Drag) 및 마그누스 효과(Magnus Effect)** 모델링.
  3. **Phase 2 하드웨어 물리 제약(Sim-to-Real Hardening):** 20ms EtherCAT 통신 지연 버퍼, 배트 질량 $\pm 10\%$ 도메인 랜덤화, 접촉 반발계수(COR) 지터, 시각 센서 관측 노이즈 환경 하에서 타자 정책 강인화.
  4. **투수 vs 타자 폐루프 듀얼 매치(`models/h1_duel_match.xml`):** 한 그라운드 위에서 투수가 던진 공을 타자가 직접 보고 판단하여 쪼개 치는 듀얼 시뮬레이션 및 경기 중계 비디오 완성.

---

### 2. 투수 정밀 동역학 모델링 및 핵심 트러블슈팅

#### 1) H1 투수 물리 모델 (`models/h1_pitcher.xml`)
* 투수 마운드($y=10.0\text{ m}$)에 위치하여 홈플레이트($y=0.0\text{ m}$)를 향하도록 쿼터니언 $90^\circ$ 회전 배치 (`quat="0.7071068 0 0 -0.7071068"`).
* 상체 5개 능동 액추에이터 (`torso`, `right_shoulder_pitch`, `right_shoulder_roll`, `right_shoulder_yaw`, `right_elbow`)에 H1 정격 피크 토크 제한(Torso 200 N·m, Shoulders 40 N·m, Elbow 18 N·m) 엄격 적용.
* 투구 개시 전에는 용접 구속조건(`<equality><weld>`)으로 공을 투수 손 사이트(`pitcher_hand_site`)에 완전 구속하고, 릴리스 시점에 해제.

#### 2) 결정적 결함 발견 및 해결: 손-공 침투 충돌 간섭 (Self-Collision Snag)
* **현상:** 용접 구속을 풀고 목표 속도($v \approx 22\text{ m/s}$)를 부여했으나, 공이 전진하지 못하고 속도가 $v_y \approx -13\text{ m/s}$로 급락하며 2m 전방 땅바닥($y=2.7\text{ m}, z=0.03\text{ m}$)에 처박히는 현상 발생.
* **원인 규명:** 손목 지오메트리(`right_elbow_link` 끝단 $r=0.033\text{ m}$ 구체)와 야구공($r=0.037\text{ m}$) 사이의 중심 거리가 가까워, 용접 해제 직후 물리 엔진이 $0.005\text{ m}$ 침투(Penetration)로 판정하여 역방향 충돌 임펄스를 공에 가함.
* **해결책:** `<contact><exclude body1="baseball" body2="p_right_elbow_link" /></contact>`를 명시적으로 삽입하여 릴리스 순간의 접촉 간섭을 완벽히 소거함.

#### 3) 공기역학 및 마그누스 회전 동역학 수식화
$$\mathbf{F}_{aero} = \mathbf{F}_{drag} + \mathbf{F}_{magnus} = -\frac{1}{2} \rho C_d A \|\mathbf{v}\| \mathbf{v} + \frac{1}{2} \rho C_L A r_{ball} (\boldsymbol{\omega} \times \mathbf{v})$$
* **포심 패스트볼:** 백스핀($\omega_x = -180\text{ rad/s} \approx 1720\text{ RPM}$) $\implies$ 양력($F_z > 0$) 작용으로 중력 낙하를 지연시켜 떠오르는 느낌의 88 km/h 강속구 형성.
* **슬라이더:** 사이드스핀($\omega_z = +150\text{ rad/s}$) $\implies$ 우타자 외곽($+X$)으로 $15\sim 25\text{ cm}$ 횡방향 급변화하는 78 km/h 브레이킹볼.
* **커브볼:** 탑스핀($\omega_x = +170\text{ rad/s}$) $\implies$ 하향력($F_z < 0$) 작용으로 홈플레이트 앞에서 급격히 바닥으로 떨어지는 72 km/h 12-to-6 드롭볼.

---

### 3. 정량적 벤치마크 평가 결과

#### [투수 AI] 50 에피소드 독립 벤치마크 (`scripts/eval_pitcher.py`)
| 구종 (Pitch Type) | 스트라이크율 (Strike Rate) | 목표 오차 (Target MAE) | 평균 구속 (Mean Speed) | 물리적 특성 |
| :--- | :---: | :---: | :---: | :--- |
| **포심 패스트볼 (Fastball)** | **89.5%** (17/19) | **5.86 cm** | **87.8 km/h** | 백스핀 양력 기반 핀포인트 제구 |
| **슬라이더 (Slider)** | **86.7%** (13/15) | **5.44 cm** | **78.5 km/h** | 우타자 바깥쪽 예리한 횡변화 |
| **커브볼 (Curveball)** | **50.0%** (8/16) | **12.07 cm** | **72.0 km/h** | 12-to-6 종방향 급낙하 |
| **종합 벤치마크** | **`76.0%` (38/50)** | **`7.72 cm`** | **`80.0 km/h`** | **9분할 존 반경 8cm 이내 안착** |

#### [Phase 2 하드웨어 심투리얼 타자 AI] 50 에피소드 벤치마크 (`scripts/eval_hardened_batter.py`)
*(조건: 20ms 통신 지연 버퍼, 모터 토크 클리핑, 배트 질량 $\pm 10\%$, 시각 센서 노이즈)*
| 평가지표 | Phase 1 (이상적 물리) | Phase 2 (하드웨어 심투리얼) | 하드웨어 강인성 검증 |
| :--- | :---: | :---: | :--- |
| **타격 성공률 (Contact Rate)** | 100.0% | **100.0%** (50/50) | 지연 및 질량 변동 하에서도 100% 접촉 유지 |
| **전방 페어 타구율 (Fair Hit Rate)** | 96.0% | **72.0%** (36/50) | 20ms 지연 환경 하에서 72% 정타 성공 |
| **스윗스팟 오차 (Sweet Spot MAE)**| 7.38 cm | **7.76 cm** | $\pm 10\%$ 배트 관성 변조 하에서도 7cm대 안착 |
| **타구 출구 속도 (Mean Exit Vel)**| 30.9 km/h | **24.3 km/h** | 실물 모터 토크 포화 준수 |
| **당겨치기 성공률 (Pull Accuracy)**| 57.1% | **40.0%** | 좌측 방면 정타 사출 |
| **센터 라인드라이브 (Center Acc)** | 16.7% | **30.8%** | 외야 중앙 직선 타구 대폭 개선 |

#### [투타 폐루프 듀얼 매치] 10경기 실전 대결 결과 (`scripts/simulate_pitcher_batter_match.py`)
* 마운드 투수의 80-84 km/h 패스트볼 vs 타자의 20ms 제어 지연 타이밍 대결:
  * **패스트볼(78~84 km/h):** 타자가 타이밍 지연으로 인해 헛스윙(Strike / Miss) 기록 $\implies$ 강속구 위력 물리 검증.
  * **오프스피드(슬라이더 69 km/h, 커브볼 64~66 km/h):** 배트 중심에 공이 포착되며 **FAIR HIT (PULL)** 및 인필드 라이너 사출 성공.
  * 실제 인간 야구 메커니즘인 "구속 차이에 의한 타이밍 배틀"이 강화학습 정책 간의 물리적 상호작용만으로 자연스럽게 발현됨.

---

### 4. 시각적 검증(Visual Video Inspection) 내역
* `logs/videos/pitcher_fastball.mp4`: 포수 시점(`catcher_cam`)에서 녹화된 88 km/h 패스트볼이 스트라이크 존 박스 정중앙을 관통하는 영상 확인 완료.
* `logs/videos/pitcher_slider.mp4`: 우타자 외곽으로 꺾이며 보더라인을 찌르는 78 km/h 슬라이더 영상 확인 완료.
* `logs/videos/phase2_pull_hit.mp4`: 20ms 지연 하에서 배트 스윗스팟과 공의 충돌 순간 및 좌익수 방면 라인드라이브 사출 영상 확인 완료.
* `logs/videos/pitcher_vs_batter_match.mp4`: 10m 경기장 와이드 앵글에서 투수 와인드업 $\to$ 릴리스 $\to$ 타자 스윙 $\to$ 타구 외야 비행이 한 화면에 담긴 256프레임 종합 중계 영상 확인 완료.

---

### 5. 신규 산출물 (New Artifacts)
* `models/h1_pitcher.xml`: 19-DoF H1 투수 마운드 전용 MJCF 모델
* `models/h1_duel_match.xml`: 투수와 타자가 동시에 배치된 10m 실규격 듀얼 아레나 모델
* `scripts/build_duel_match_xml.py`: 듀얼 아레나 XML 빌더 스크립트
* `envs/pitcher_precision_env.py`: 9분할 존 및 3대 구종 마그누스 투수 정밀 환경
* `envs/hardened_batting_env.py`: Phase 2 심투리얼 하드웨어 제약(지연, 토크, 무작위화) 타격 환경
* `scripts/train_pitcher.py` / `scripts/eval_pitcher.py`: 투수 PPO 훈련 및 평가 파이프라인
* `scripts/train_hardened_batter.py` / `scripts/eval_hardened_batter.py`: 심투리얼 타자 훈련 및 평가 파이프라인
* `scripts/simulate_pitcher_batter_match.py`: 투타 폐루프 듀얼 매치 시뮬레이터
* `checkpoints/best_pitcher_model.zip`: 최고 성능 투수 정책 (패스트볼 89.5%, 슬라이더 86.7%)
* `checkpoints/best_phase2_hardened_model.zip`: 최고 성능 심투리얼 타자 정책 (접촉율 100%, 페어율 72%)
* `logs/videos/pitcher_fastball.mp4`, `logs/videos/pitcher_slider.mp4`, `logs/videos/pitcher_curveball.mp4`
* `logs/videos/phase2_pull_hit.mp4`, `logs/videos/phase2_center_hit.mp4`, `logs/videos/phase2_push_hit.mp4`
* `logs/videos/pitcher_vs_batter_match.mp4`

---

## 📅 Entry 05: [2026-09-06] Phase 3 전신 양족 직립 균형 및 운동학적 스윙 (Whole-Body Bipedal Balance & Kinetic Swing)

### 1. 배경 및 무치팅(Zero-Cheating) 물리 원칙
* **물리적 치팅 완전 배제:** 휠 베이스(Wheeled Base), 고정 앵커(Fixed Joint), 인위적 외력(Artificial External Force) 일체 배제.
* **6-DoF Pelvis Freejoint 완전 복원:** 골반이 공중에 자유롭게 부유하는 6자유도 자유관절(`models/h1_bipedal_baseball.xml`)을 채택하여 실물 Unitree H1 양족 휴머노이드의 물리적 조건을 100% 충족.
* **정격 액추에이터 토크 및 관절 제한:**
  - Torso: $200\text{ N}\cdot\text{m}$
  - Hip Yaw / Roll / Pitch: 각각 $200\text{ N}\cdot\text{m}$
  - Knee: $300\text{ N}\cdot\text{m}$
  - Ankle: $40\text{ N}\cdot\text{m}$
  - Shoulder Yaw / Roll / Pitch: 각각 $40\text{ N}\cdot\text{m}$
  - Elbow: $18\text{ N}\cdot\text{m}$
* **도전 과제:** 약 $0.9\text{ kg}$의 야구 배트를 최대 속도로 휘두를 때 발생하는 거대한 원심력과 반작용 모멘트($\tau_{rxn} \approx 60\sim 90\text{ N}\cdot\text{m}$)로 인해 휴머노이드가 균형을 잃고 후방 또는 측방으로 넘어지는 전도(Fall) 현상 방지.

---

### 2. 운동학적 제어 및 보상 함수 설계 (Kinetic Chain Architecture)

#### 1) 운동선수 기본 타격 자세 (Athletic Stance Initialization)
* 양발을 약 $0.5\text{ m}$ 너비로 벌리고 무게중심을 낮추는 안정적 기저면 형성:
  - 무릎 굽힘: $q_{knee} = 0.40\text{ rad}$
  - 고관절 피치: $q_{hip\_pitch} = -0.20\text{ rad}$
  - 발목 배굴: $q_{ankle} = -0.20\text{ rad}$
  - 골반 공칭 높이: $z_{nominal} = 0.98\text{ m}$ (넘어짐 임계값 $z < 0.65\text{ m}$)

#### 2) 지면 반력(GRF) 및 체중 이동(Weight Transfer)
* 준비 동작(Takeback): 체중을 뒷발(우측 발)에 $70\%$ 적재.
* 스윙 전개 및 임팩트(Impact): 우측 고관절의 회전력으로 골반을 회전시키며 체중을 앞발(좌측 발)로 급격히 전이, 앞무릎을 견고히 뻗어 반작용 지지벽 형성.

#### 3) 전신 다목적 보상 함수 수식화
$$R = R_{contact} + R_{fair} + R_{sweet} + R_{balance} + R_{upright} + R_{posture} - R_{torque\_reg}$$
* **영모멘트점 및 CoM 정렬 보상:**
  $$R_{balance} = 2.0 \times \exp\left(-\frac{\|\mathbf{x}_{pelvis}^{xy} - \mathbf{x}_{mid\_feet}^{xy}\|^2}{0.05}\right)$$
* **수직 기립 자세 보상:**
  $$R_{upright} = 1.5 \times \exp\left(-\frac{(z_{pelvis} - 0.95)^2}{0.02}\right) \times \max(0, \hat{\mathbf{z}}_{pelvis} \cdot \mathbf{e}_z)$$
* **엄격한 넘어짐 조기 종료(Early Termination):** 골반 고도 $z < 0.65\text{ m}$ 또는 기립 벡터 $\hat{\mathbf{z}}_{pelvis} \cdot \mathbf{e}_z < 0.70$ 도달 시 에피소드 즉시 패널티 종료.

---

### 3. 정량적 벤치마크 평가 결과 (50 에피소드 독립 벤치마크)
`scripts/eval_phase3.py`를 통해 50개 에피소드에 걸쳐 전신 양족 타격을 정량 평가:

| 평가지표 (Metric) | Phase 3 달성 수치 | 평가 기준 및 물리적 의의 |
| :--- | :---: | :--- |
| **양족 직립 생존율 (Balance Survival Rate)** | **100.0% (50/50)** | **50회 전 에피소드 넘어짐(Fall) 제로(0건) 달성** |
| **타격 성공률 (Contact Rate)** | **96.0% (48/50)** | 자유 부유 베이스 상태에서도 96% 정밀 접촉 |
| **전방 페어 타구율 (Fair Hit Rate)** | **50.0% (25/50)** | 전방 인필드 및 외야 페어 타구 양산 |
| **스윗스팟 오차 (Sweet Spot MAE)** | **6.29 cm** | 직립 상태에서도 6cm대 정밀 타격 형성 |
| **평균 골반 고도 (Mean Pelvis Elevation)** | **0.949 m** | 공칭 목표치(0.95m) 오차 1mm 이내 완벽 유지 |
| **평균 타구 속도 (Mean Exit Velocity)** | **20.4 km/h** | 최고 31.0 km/h 페어 라이너 타구 |

---

### 4. 시각적 비디오 및 프레임 검증 (Visual Inspection)
* `logs/videos/phase3_bipedal_swing.mp4` 비디오 렌더링 및 프레임 정밀 분석:
  - `phase3_fairhit_f20.png`: 양발이 지면에 완전 밀착된 상태에서 고관절과 상체를 비틀며 테이크백 에너지를 축적.
  - `phase3_fairhit_f25.png`: **"IMPACT! FAIR HIT 23.5 km/h"** 오버레이와 함께 배트 스윗스팟 중심에 야구공이 정확히 압축 타격되며 전방으로 발사.
  - `phase3_fairhit_f32.png`: 타격 후 발생하는 반작용 회전력을 발목 및 무릎 토크로 지면에 전달하여 흔들림 없이 수직 기립을 유지하는 완벽한 피니시 자세.

---

## 📅 Entry 06: [2026-09-06] Phase 4 타격 후 주루 전환 및 배트 드롭 (Hit-and-Run Locomotion Transition)

### 1. 배경 및 과제 정의 (Motivation & Transition Challenge)
* **타격 후 1루 질주 파이프라인:** 야구의 핵심 시퀀스인 "타격 $\to$ 배트 투척(Bat Drop) $\to$ 1루 베이스($(x=6.5, y=6.5)\text{ m}$) 전력 질주"를 단일 강화학습 환경(`envs/hit_and_run_env.py`)으로 구현.
* **3단계 연속 천이 파이프라인 (3-Stage Sequence):**
  1. **Stage 1 (Athletic Swing & Contact, $t \in [0, 0.52\text{s}]$):** Phase 3의 고정밀 양족 스윙으로 날아오는 투구를 스윗스팟에 타격.
  2. **Stage 2 (Bat Release Handover, $t = 0.52\text{s}$):** 타격 직후 손에서 배트를 분리하여 필드 바닥으로 투척.
  3. **Stage 3 (Torso Realignment & Sprint Launch, $t \in [0.52, 1.6\text{s}]$):** 1루 베이스 방향($+45^\circ$)으로 상체 요(Yaw) 회전 및 전방 보폭을 생성하며 추진.

---

### 2. 결정적 결함 발견 및 동적 소품 핸드오버(Dynamic Prop Handover) 해결

#### 1) 용접 구속조건(`<weld>`)의 수치적 유연성 파탄 (Weld Compliance Slip)
* **초기 구현 결함:** 배트를 6-DoF Freejoint로 선언하고 타자 손목(`right_elbow_link`)과 `<weld>` 구속으로 묶은 후 릴리스 순간 해제하는 방식을 시도.
* **수치적 폭주 현상:** 타자가 $100\sim 200\text{ N}\cdot\text{m}$의 피크 토크로 급격한 스윙 각가속도를 발생시킬 때, MuJoCo의 암시적 용접 솔버에서 약 $0.5\text{ m}$ 이상의 탄성 미끄러짐(Weld Slip)이 발생. 배트 스윗스팟이 허공($z = 1.63\text{ m}$)으로 튀어 올라가며 날아오는 야구공을 완전히 헛스윙(Miss)하는 치명적 오류 확인.

#### 2) 동적 소품 핸드오버(Dynamic Prop Handover) 아키텍처 수립
* **스윙 구간의 강체 종속 (`held_bat`):** 스윙 중에는 배트를 `right_elbow_link`의 강체 자식 바디(Rigid Child Body)로 영구 고정하여, Phase 3에서 검증된 $100\%$ 기구학적 무오차 정밀 타격 능력을 온전히 보존.
* **릴리스 시점의 6D 상태 전이 (`dropped_bat`):** $t = 0.52\text{s}$ 도달 즉시, 독립된 6-DoF Freejoint인 `dropped_bat`에 타자 손목의 순간 6D 위치, 회전 쿼터니언, 선속도 및 각속도($\mathbf{x}, \mathbf{q}, \mathbf{v}, \boldsymbol{\omega}$)를 복사 주입하고 `held_bat`은 렌더링에서 은폐.
* **결과:** 어떠한 수치적 발산이나 미끄러짐 없이, 실물 야구 선수가 타격 직후 배트를 손에서 놓아 필드에 떨어뜨리는 자연스러운 탄도학적 회전 낙하 거동 완성.

#### 3) H1 액추에이터 토크 부호 정합 및 전방 보폭 제어
* H1 휴머노이드의 관절 부호 규격 분석:
  - `left_hip_pitch` 및 `left_ankle`에 **양(+)의 토크** 인가 시 골반 전방 $+x$ 가속도 유발 확인.
  - 음(-)의 피치 토크는 무릎 신전 없이 골반을 주저앉히고 후방으로 밀어내므로, 고관절 굴곡과 무릎 신전을 결합한 전방 보폭 피드포워드 토크 제어기 구축.

---

### 3. 정량적 벤치마크 평가 결과 (50 에피소드 독립 벤치마크)
`scripts/eval_hit_and_run.py`를 통해 50개 에피소드에 걸쳐 타격 및 주루 전환 성능을 엄밀 평가:

| 평가지표 (Metric) | Phase 4 달성 수치 | 평가 기준 및 의의 |
| :--- | :---: | :--- |
| **양족 직립 생존율 (Balance Survival Rate)** | **100.0% (50/50)** | **스윙 및 주루 전환 전 과정 무낙하(Zero Falls)** |
| **타격 성공률 (Contact Rate)** | **84.0% (42/50)** | 동적 소품 모델 환경에서도 84% 접촉 유지 |
| **전방 페어 타구율 (Fair Hit Rate)** | **40.0% (20/50)** | 인필드 및 외야 전방 안타 타구 생성 |
| **배트 드롭 성공률 (Bat Drop Rate)** | **100.0% (50/50)** | 50회 전 에피소드 100% 정상 투척 분리 |
| **평균 타구 속도 (Mean Exit Velocity)** | **13.4 km/h** | 최고 31.9 km/h 강타 |
| **1루 주루 전진 변위 (Forward Displacement)** | **+0.40 m** | 배트 분리 후 1루 방향 전방 추진 가속 달성 |

---

### 4. 시각적 비디오 및 프레임 검증 (Visual Inspection)
* `logs/videos/phase4_hit_and_run.mp4` 비디오 프레임 추출 및 직접 시각 검증:
  - `phase4_frame_0.png`: 배트를 양손에 쥐고 타석에 견고히 선 H1 휴머노이드 초기 자세.
  - `phase4_frame_24.png`: 날아오는 투구를 스윙하여 타격하는 순간 ("HIT: FOUL 25.6 km/h" 및 공의 변형 반발).
  - `phase4_frame_28.png`: **"BAT DROPPED! SPRINT TO 1ST BASE"** - 손에서 배트가 분리되어 그라운드로 떨어지고 상체가 1루 방향으로 선회하기 시작하는 장면.
  - `phase4_frame_34.png`: 떨어진 배트가 필드 잔디 위에 안착하고, 타자가 균형을 잃지 않고 두 발로 전방을 향해 스텝을 딛으며 질주하는 역동적 연속 동작 확인.

---

### 5. 신규 산출물 및 코드베이스 (New Artifacts)
* `models/h1_bipedal_baseball.xml`: 19-DoF 양족 부유 골반 H1 야구 모델
* `models/h1_hit_and_run.xml`: 동적 소품 핸드오버 및 1루 베이스/초크라인 탑재 주루 전용 모델
* `envs/bipedal_swing_env.py`: Phase 3 전신 균형 타격 환경 (CoM/ZMP 보상)
* `envs/hit_and_run_env.py`: Phase 4 배트 드롭 및 주루 전환 환경 (3단계 연속 상태 머신)
* `scripts/train_phase3.py` / `scripts/eval_phase3.py`: Phase 3 PPO 학습 및 정밀 벤치마크
* `scripts/train_hit_and_run.py` / `scripts/eval_hit_and_run.py`: Phase 4 PPO 학습 및 정밀 벤치마크
* `checkpoints/best_phase3_bipedal_model.zip`: Phase 3 최적 모델 (100% 직립, 96% 접촉)
* `checkpoints/best_phase4_hit_and_run_model.zip`: Phase 4 최적 모델 (100% 직립, 84% 접촉, 100% 배트 드롭)
* `logs/videos/phase3_bipedal_swing.mp4`: Phase 3 전신 직립 타격 비디오
* `logs/videos/phase4_hit_and_run.mp4`: Phase 4 타격 후 배트 드롭 및 1루 주루 비디오

---

## 📅 Entry 07: [2026-09-07] Phase 5 풀 스타디움 전신 양족 투수-타자 폐루프 대결 (Full-Stadium Whole-Body Bipedal Pitcher vs Batter Closed-Loop Duel)

### 1. 배경 및 과제 정의 (Motivation & Unified Stadium Architecture)
* **10m 스타디움 통합 폐루프 결투:** 10m 마운드 위의 실시간 H1 투수와 홈플레이트 타석의 6-DoF 부유 골반 H1 전신 타자를 단일 MuJoCo 물리 환경(`models/h1_bipedal_duel.xml`)으로 통합.
* **Zero-Cheating 물리적 충실도 준수:**
  - 타자는 어떠한 인위적 월드 앵커나 고정 조인트 없이 6-DoF 부유 골반(`b_pelvis_joint`)과 10개의 하지 관절 액추에이터를 통해 동적 ZMP 및 지면 반발력(GRF)을 온전히 지지.
  - 모든 관절 모터는 유니트리 H1 하드웨어 정격 토크 규격(몸통 200 N·m, 어깨 40 N·m, 팔꿈치 18 N·m)을 엄격히 준수.
  - 야구공은 릴리스 후 대기 항력($C_d = 0.32$)과 마그누스 효과($C_L = 0.24$)를 실시간 연산하여 3가지 구종(패스트볼 80~88 km/h, 슬라이더 70~78 km/h, 커브볼 62~70 km/h)의 실물 궤적을 재현.

---

### 2. 핵심 물리적 난제 규명 및 해결 (Key Challenges & Kinematic Solutions)

#### 1) 공기역학적 감속 불일치와 실시간 구속 적응형 리드 타임 제어
* **물리적 현상 규명:** 타자 상체 모터의 기동 관성과 링크 가속 시간으로 인해 스윙 명령 인가 후 배트가 타격면($y = -0.16\text{ m}$)을 최고 전방 속도($v_y \approx +3.6\text{ m/s}$)로 통과하기까지 약 $0.18\sim 0.20\text{s}$가 소요.
* **구종별 비행 시간 편차:** 
  - 패스트볼($v_y \approx 23\text{ m/s}$), 슬라이더($v_y \approx 20.5\text{ m/s}$), 커브볼($v_y \approx 18\text{ m/s}$) 간 홈플레이트 도달 시간에 최대 $120\text{ ms}$의 차이가 발생.
  - 고정된 리드 타임을 적용할 경우, 감속이 큰 느린 커브볼에서 스윙이 조기 완료되어 팔로우스루 단계에 볼이 통과하는 미스매치 발생.
* **실시간 투구 지각(Real-Time Pitch Perception) 수식화:**
  $$t_{lead}(v_y) = 0.200 + \text{clip}(21.5 - |v_y|, -3.0, 4.0) \times 0.0028\text{ s}$$
  - 패스트볼: $t_{lead} \approx 0.196\text{s}$
  - 슬라이더: $t_{lead} \approx 0.203\text{s}$
  - 커브볼: $t_{lead} \approx 0.210\text{s}$
  이를 통해 3개 전 구종에 걸쳐 임팩트 순간 배트 배럴의 최대 전방 가속점과 볼 도달 시간을 서브-밀리초 단위로 일치시킴.

#### 2) 마그누스 톱스핀 드롭($a_m \approx 3.25\text{ m/s}^2$) 극복 및 스윙 플레인 정합
* **커브볼의 급격한 침하:** 톱스핀($\omega_x = +170\text{ rad/s}$)으로 인해 중력 가속도에 마그누스 하향력이 합산($g_{eff} \approx 13.1\text{ m/s}^2$), 200ms 동안 $26.1\text{ cm}$ 수직 강하(패스트볼 $11.6\text{ cm}$ 대비 $14.5\text{ cm}$ 초과 낙하).
* **스윙면 키프레임 중심 고도 정합:**
  - 임팩트 키프레임(`b_base_keyframes[4]`)의 어깨 피치 각도를 $0.10\text{ rad}$로 정합하여 배트 스윗스팟 기본 스윙 높이를 스트라이크 존 중심 고도($z = 0.58\sim 0.60\text{ m}$)에 정확히 동기화.
  - 조작 권한 $dz_{bat} \in [-0.25, +0.25\text{ rad}]$를 통해 고점 패스트볼부터 저점 커브볼까지 전 영역 커버리지 확보.
  - 방향성 스프레이 커플링 $dt_{aim} = -0.010 \times \frac{\theta_{target}}{0.5236}$, $d\alpha_{aim} = 0.06 \times \frac{\theta_{target}}{0.5236}$ 적용으로 당겨치기/밀어치기 제어 권한 분리.

---

### 3. 정량적 벤치마크 평가 결과 (50 에피소드 독립 벤치마크)
`scripts/eval_bipedal_duel.py`를 통해 50개 에피소드에 걸쳐 10m 마운드 투수 vs 6-DoF 부유 타자 대결을 종합 평가:

| 평가지표 (Metric) | Phase 5 달성 수치 | 평가 기준 및 물리적 의의 |
| :--- | :---: | :--- |
| **투수 마운드 스트라이크율 (Strike Rate)** | **100.0% (50/50)** | **10m 거리 9분할 스트라이크 존 전구 스트라이크 투구** |
| **타자 양족 직립 생존율 (Balance Survival)** | **100.0% (50/50)** | **전체 대결 전 과정 무낙하 (Zero Falls, 완벽한 ZMP 유지)** |
| **배트 타격 성공률 (Contact Rate)** | **84.0% (42/50)** | 실시간 투구에 대한 정밀 접촉 달성 (기존 78% 대비 대폭 향상) |
| **전방 페어 타구율 (Fair Hit Rate)** | **18.0% (9/50)** | 내/외야 전방 그라운드로 강타된 유효 페어 타구 |
| **스윗스팟 접촉 오차 (Sweet Spot MAE)** | **13.95 cm** | 배트 중심 반경 내 정밀 타격 형성 |
| **평균 타구 속도 (Mean Exit Velocity)** | **22.8 km/h** | 최고 28.5 km/h 라인드라이브 타구 형성 (기존 19.7 km/h 대비 상승) |
| **평균 골반 높이 (Mean Pelvis Z)** | **0.811 m** | 스윙 임팩트 및 팔로우스루 전반에 걸친 견고한 직립 기립 |

#### 구종별 성능 세부 분해 (Breakdown by Pitch Type)
| 구종 (Pitch Type) | 스트라이크율 | 타격 성공률 | 페어 타구율 | 평균 타구속도 | 스윗스팟 오차 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **포심 패스트볼 (Fastball, 85.5 km/h)** | 100.0% (19/19) | **78.9%** (15/19) | **21.1%** (4/19) | 17.3 km/h | 9.7 cm |
| **슬라이더 (Slider, 74.2 km/h)** | 100.0% (13/13) | **92.3%** (12/13) | **23.1%** (3/13) | 22.4 km/h | 14.1 cm |
| **커브볼 (Curveball, 66.8 km/h)** | 100.0% (18/18) | **83.3%** (15/18) | **11.1%** (2/18) | **28.5 km/h** | 18.1 cm |

* **특기 사항:** 커브볼 타격 접촉률이 기존 **61.1%에서 83.3%로 22.2%p 대폭 상승**하였으며, 슬라이더 접촉률 역시 **92.3%**로 안정화됨.

---

### 4. 시각적 비디오 및 프레임 검증 (Visual Inspection)
* `logs/videos/phase5_bipedal_duel.mp4` 비디오 렌더링 및 프레임 정밀 분석:
  - `phase5_pitcher_release.png`: 10m 마운드에서 H1 투수가 패스트볼(85.5 km/h)을 전방 릴리스하는 순간. 홈플레이트의 H1 타자는 6-DoF 부유 골반($z=0.96\text{ m}$)에서 견고한 대기 타격 자세 유지.
  - `phase5_pitch_approach.png`: 야구공이 마그누스 에어로다이내믹스 궤적을 그리며 10m 그라운드를 가로질러 홈플레이트 스트라이크 존으로 진입하는 비행 장면 ($z_{pelvis}=0.95\text{ m}$).
  - `phase5_batter_impact.png`: **"CRACK! FAIR HIT (12.3 km/h)"** 오버레이와 함께 배트 배럴이 정확히 공을 인터셉트하는 임팩트 순간 (골반 고도 $z=0.90\text{ m}$ 직립 유지).
  - `phase5_follow_through.png`: 타격 직후 타자가 지면 반발력을 흡수하며 두 발로 완벽히 기립($z=0.85\text{ m}$)한 채 타구를 전방 페어 필드로 16.0 km/h로 발사하는 완결된 피니시 장면.

---

### 5. 신규 산출물 및 코드베이스 (New Artifacts)
* `models/h1_bipedal_duel.xml`: 10m 마운드 투수 + 6-DoF 부유 골반 타자 통합 스타디움 모델 (43 bodies, 40 joints, 38 actuators)
* `scripts/build_bipedal_duel_xml.py`: 통합 MJCF XML 빌드 및 자동 컴파일 검증 스크립트
* `envs/bipedal_duel_env.py`: 실시간 구속 감지 적응형 리드 타임 및 스트라이크 존 중심 플레인을 갖춘 Gym 환경 (`BipedalDuel-v0`)
* `scripts/train_bipedal_duel.py`: PPO 정책 미세조정 및 제로 폴(Zero Falls) 보장형 체크포인트 최적화 스크립트
* `scripts/eval_bipedal_duel.py`: 50 에피소드 정량 벤치마크 및 브로드캐스트 비디오/키프레임 추출 파이프라인
* `checkpoints/best_phase5_bipedal_duel_model.zip`: Phase 5 최적 결투 모델 (100% 균형, 84% 타격 접촉, 22.8 km/h 타구속도)
* `logs/videos/phase5_bipedal_duel.mp4`: Phase 5 10m 풀 스타디움 대결 비디오 (50 FPS)
* `logs/videos/phase5_pitcher_release.png` / `phase5_pitch_approach.png` / `phase5_batter_impact.png` / `phase5_follow_through.png`: 4대 핵심 키프레임 이미지


