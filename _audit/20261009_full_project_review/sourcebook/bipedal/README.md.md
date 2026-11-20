# bipedal/README.md

원본: [README.md](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/README.md)

SHA256: `e47b62582c9f662a8f0270c0fb0fda2ba38455dba5f080f7a501fe159facfb01`

전체 15행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | # 🤖 Bipedal Baseball AI: Whole-Body Kinetic Strike & Locomotion
    2 | 
    3 | Unitree H1 휴머노이드 로봇 기반의 **이족 보행 전신 타격(Whole-Body Bipedal Batting) 및 질주(Locomotion Transition)** 차세대 심층 강화학습 프로젝트.
    4 | 
    5 | ## 📌 Core Research Question
    6 | > *"휴머노이드 로봇이 두 발로 그라운드를 딛고 서서(Bipedal Stance), 140km/h 타격 회전 토크를 지면 반력(GRF)과 ZMP 밸런스로 버텨내며 원하는 방향으로 공을 쪼개고, 타격 직후 1루로 전력 질주하는 전신 제어(Whole-Body Control)를 어떻게 달성할 것인가?"*
    7 | 
    8 | ## 📚 Ongoing Research Journal
    9 | * 프로젝트의 모든 기획 회의, 기술 의사결정, 가설 및 트러블슈팅은 [**`RESEARCH_LOG.md`**](RESEARCH_LOG.md)에 실시간으로 누적 기록됩니다.
   10 | 
   11 | ## 🏛 4-Stage Progressive Curriculum
   12 | 1. **Phase 1: Directional Hitting & Precision Contact** (밀어치기/당겨치기, 발사각 제어)
   13 | 2. **Phase 2: Sim-to-Real Physical Hardening** (H1 실물 모터 토크 클리핑, 통신 지연, 도메인 랜덤화)
   14 | 3. **Phase 3: Whole-Body Kinetic Chain Swing** (H1 19-DoF 전신 복원, 체중 이동 및 ZMP 지면 반력 균형)
   15 | 4. **Phase 4: Hit-and-Run Locomotion Transition** (타격 후 배트 릴리스 및 1루 전력 질주 보행 위상 전이)
````
