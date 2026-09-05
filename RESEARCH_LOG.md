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
