# baseball/archive/EXECUTION_GUIDE.md

원본: [archive/EXECUTION_GUIDE.md](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/EXECUTION_GUIDE.md)

SHA256: `69387cc292de78fbe4bb2e2cf4970d3fd6236f7e661c0e8b5418c1b84b056b55`

전체 94행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | # ⚾ Baseball RL Simulator & Multi-Agent Game 실행 가이드 (EXECUTION_GUIDE.md)
    2 | 
    3 | 본 가이드는 **3D Baseball Physics & Multi-Agent RL 시뮬레이터 프로젝트**의 다양한 실행 모드(프로 야구장 3D 구장, 3D 관중석/입장통로/광고판, 실시간 3D GUI 팝업 관전, 3D MP4/GIF 비디오 녹화, MuJoCo 3D 물리 환경, IK 전문가 데모 수집, Stage 1 BC 지도학습, Stage 2 PPO 파인튜닝, 실시간 대시보드) 사용법을 안내합니다.
    4 | 
    5 | ---
    6 | 
    7 | ## ⚙️ 1. 사전 준비 (가상환경 활성화)
    8 | 
    9 | 터미널을 열고 프로젝트 디렉토리로 이동한 뒤 가상환경을 활성화합니다.
   10 | 
   11 | ```bash
   12 | # 디렉토리 이동
   13 | cd /Users/jmjeon/Desktop/baseball
   14 | 
   15 | # 가상환경 활성화 (macOS/Linux)
   16 | source venv/bin/activate
   17 | 
   18 | # 의존성 패키지 설치 (필요시)
   19 | pip install -r requirements.txt
   20 | ```
   21 | 
   22 | ---
   23 | 
   24 | ## 🏟️ 2. 프로 야구장 3D 구장 요기 요소 (Pro Stadium 3D Features)
   25 | 
   26 | `assets/stadium_3d.xml`에는 프로 야구장의 디테일한 비주얼 요소가 51개의 3D 객체(Geom)로 구축되어 있습니다:
   27 | - **다층 관중석 (Multi-tiered Seating Stands)**: 1루/3루 및 본루 뒤편 하단/상단 네이비 & 블루 관중석 스탠드
   28 | - **입장 통로 & 터널 (Entry Portals / Tunnels)**: 관중석 스탠드를 관통하는 어두운 콘코스 입장 통로(Concourse Portals)
   29 | - **덕아웃 (1루 & 3루 Dugouts)**: 1루 및 3루 측 선수단 덕아웃 지붕 및 그라운드 구조
   30 | - **외야 스폰서 광고판 (Outfield Sponsor Ads)**: 외야 펜스 상단에 장착된 칼라풀한 스폰서 광고 보드(Samsung, LG, Hyundai, Kakao 등)
   31 | - **대형 점수판 & 배터스 아이 (Jumbo Scoreboard & Batter's Eye)**: 백스탑 중심 높이 14m 대형 전광판 및 타자 시야 보호용 매트 그린 배터스 아이
   32 | - **인내야 다이아몬드 & 3D 파울폴**: 마운드(18.44m), 다이아몬드 베이스 경로, 노란색 12m 3D 파울폴
   33 | 
   34 | ---
   35 | 
   36 | ## 🖥️ 3. 실시간 3D GUI 팝업 윈도우 관전 (`simulator/live_viewer.py`)
   37 | 
   38 | macOS 화면에 **실제 3D OpenGL GUI 팝업 창**이 띄워지며 60FPS로 3D 야구장, 3D 공 궤적, 3D 배트 스윙을 실시간 관전할 수 있습니다. (마우스로 360도 회전/이동/확대 가능)
   39 | 
   40 | ### ① IK Expert Bot 3D 팝업 관전
   41 | ```bash
   42 | PYTHONPATH=. python -m simulator.live_viewer --mode expert --episodes 5
   43 | ```
   44 | 
   45 | ### ② Stage 1 BC 모방학습 모델 3D 팝업 관전
   46 | ```bash
   47 | PYTHONPATH=. python -m simulator.live_viewer --mode bc --checkpoint checkpoints/bc_batter_policy.pt --episodes 5
   48 | ```
   49 | 
   50 | ### ③ Stage 2 PPO 파인튜닝 모델 3D 팝업 관전
   51 | ```bash
   52 | PYTHONPATH=. python -m simulator.live_viewer --mode ppo --checkpoint checkpoints/mujoco_ppo_ep30.pt --episodes 5
   53 | ```
   54 | 
   55 | ---
   56 | 
   57 | ## 🎥 4. 3D 시뮬레이션 MP4 / GIF 비디오 녹화 (`simulator/video_recorder.py`)
   58 | 
   59 | 3D 시뮬레이션 궤적 및 스윙 장면을 60FPS High-Quality MP4 비디오 및 GIF 파일로 자동 추출하여 `videos/` 디렉토리에 저장합니다.
   60 | 
   61 | ```bash
   62 | PYTHONPATH=. python -m simulator.video_recorder
   63 | ```
   64 | - **저장 파일**:
   65 |   - `videos/expert_swing_3d.mp4` (MP4 고화질 비디오)
   66 |   - `videos/expert_swing_3d.gif` (GIF 애니메이션 포트폴리오용)
   67 | 
   68 | ---
   69 | 
   70 | ## 🧱 5. MuJoCo 3D 야구 환경 & 2-Stage 학습 파이프라인
   71 | 
   72 | ### 5.1 Expert Demo 데모 데이터셋 수집 (Analytical IK Solver)
   73 | ```bash
   74 | PYTHONPATH=. python -m expert.demo_collector
   75 | ```
   76 | 
   77 | ### 5.2 Stage 1: Behavioral Cloning (BC) Pre-training
   78 | ```bash
   79 | PYTHONPATH=. python -m training.bc_trainer
   80 | ```
   81 | 
   82 | ### 5.3 Stage 2: MuJoCo 3D PPO Fine-Tuning + Domain Randomization
   83 | ```bash
   84 | PYTHONPATH=. python -m training.mujoco_ppo_trainer
   85 | ```
   86 | 
   87 | ---
   88 | 
   89 | ## 🌐 6. 실시간 3D 대시보드 (`simulator/dashboard.py`)
   90 | 
   91 | ```bash
   92 | PYTHONPATH=. python -m simulator.dashboard
   93 | ```
   94 | 👉 **[http://127.0.0.1:8050](http://127.0.0.1:8050)**
````
