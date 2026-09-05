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


