# Unitree H1 Baseball 기술 감사

검사일: 2026-09-26 KST. 대상은 **로컬 `main`, `f63dc977f29d53103b0853ac29fbaeddfb95b60e`**다. 이 문서는 원본을 고친 결과가 아니라, 원본을 보존하고 수행한 정적 추적·제한된 실행 검증의 기록이다.

저장소 루트: `/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball`. 아래 소스 위치는 이 루트 기준의 정확한 상대 경로와 1-based 줄 번호다. `logs/`, `scripts/`, `notes/`는 이 보고서가 있는 감사 실행 디렉터리 기준이다.

## 1. 결론 요약

**현재의 주된 구현은, 사람이 만든 키프레임 동작과 공 속도 주입을 바탕으로 PPO가 투구·타격의 소수 매개변수를 선택하는 시뮬레이션이다.** 일부 수비·주루 환경은 액추에이터 힘을 사용하지만, 기본 투타 경로는 토크 기반 전신 제어·균형 회복 태스크가 아니다. 이 제한적 추상화 자체는 유효한 연구 대상이 될 수 있다. 다만 물리적으로 충실한 전신 야구 로봇, 실물 전이, 정책들이 운영하는 통합 9이닝 경기의 증거로 설명할 수는 없다.

믿을 수 있는 범위는 다음과 같다.

- PPO 체크포인트와 정규화 파일이 실제 존재하고 여러 정책의 로드·추론·환경 종료까지 실행된다. 기존 TensorBoard에는 mega 투수 2,015,232 step, 타자 2,031,616 step까지 학습한 기록이 있다. **학습을 하지 않았다는 결론은 근거가 없다.**
- 현재 환경에서 새로 수행한 10개 고정 사례의 단독 mega 투수는 10/10회 코드상 목표 반경 0.20m 이내에 도달했다. 평균 오차 0.1133m, 최대 0.1703m, 주입된 릴리스 속도 평균 152.34km/h였다. 이는 특정 가중치·현재 물리·10개 사례의 결과이며, 문서의 과거 15회/84.4km/h 실험을 재현한 것이 아니다.
- 소프트토스와 피칭 머신에서도 학습 정책에 의한 실제 MuJoCo 배트-공 접촉을 확인했다. 소프트토스 6/10, 50km/h 머신 5/10, 올바른 정규화 파일을 짝지은 80km/h deep 정책 2/10이다. 무스윙은 각각 0/10이었다. 이 정도 표본으로 모집단 성능이나 RL 우월성을 확정할 수 없다.

반대로 지금 성과로 인정하기 어려운 범위는 다음과 같다.

- 단독 투수와 경기 투수의 관측이 모두 16D지만 열의 의미가 다르다. 기본 경기에는 잘못된 순서의 관측을 기존 정책·정규화에 전달하는 확정 결함이 있다.
- 수비수는 5/5 포구로 집계됐지만 **5회 모두 초반 수치 불안정과 MuJoCo 자동 초기화가 동반됐다.** 정상적인 뜬공 포구 100%의 증거로 사용할 수 없다. NaN 여부만 검사하면 이 문제를 놓친다.
- 주루 환경은 공 좌표를 주자 좌표로 사용하고, 포수는 존재하지 않는 glove 이름으로 접촉을 판정한다. 이 둘은 실제 태스크 판정에 영향을 주는 결함이다.
- 기본 중계는 잘못된 컨택 필드와 자동 reset 뒤 상태를 읽는다. 별도 9이닝 코드는 난수 사건을 처리하며, 실제 파울 카운트 오류도 재현됐다.
- FrameStack의 개선 효과, 광학식 MoCap 원자료·리타기팅, 물리 정확성, 전신 균형 및 실물 전이는 현재 증거로 입증되지 않는다. 문서 일부는 기구학적 개입과 향후 전신 제어의 필요성을 이미 인정한다(`docs/PAPER.md:150-160`). 그 한계 설명도 함께 읽어야 한다.

**권고는 B: 핵심 환경·정책 연결·평가를 일부 수정하는 것이다.** 단, 목표를 먼저 ‘설계한 동작 아래 투구/타격 의사결정’으로 제한해야 한다. 지금은 문서만 보강하는 A로 부족하다. 전신 균형·접촉을 통한 투구·실물 전이가 다음 목표라면 **C: 자산만 선별 재사용하고 단일 태스크부터 새로 설계**하는 쪽이 맞다. 이를 기존 가중치의 자연스러운 확장이라고 볼 근거는 없다. 기존 프로젝트 전체를 폐기하고 독립 저장소부터 만드는 D가 필수라는 근거는 이번 감사에서 나오지 않았다.

## 2. 검사한 범위와 검사하지 못한 범위

### 2.1 상태·환경·보존

| 항목 | 확인 결과 |
|---|---|
| 브랜치 / HEAD | `main` / `f63dc977f29d53103b0853ac29fbaeddfb95b60e` |
| 시작 시 변경 | `git status --short` 출력 없음. 기존 미커밋 변경 없음 |
| 공개 저장소 | [codemillss/baseball_game](https://github.com/codemillss/baseball_game)의 공개 페이지·README 확인. 원격 HEAD API는 도구 접근 실패 및 로컬 DNS 제한으로 SHA 미확인. 공개 HEAD와 로컬 동일성을 단정하지 않음 |
| 이번 실행 하드웨어 | Apple M1 Pro, MacBook Pro, 16GB, arm64. M4에서는 실행하지 않음 |
| 기존 실행 환경 | Python 3.11.5 / MuJoCo 3.10.0 / Gymnasium 1.3.0 / SB3 2.9.0 / PyTorch 2.13.0 / NumPy 2.4.6 / macOS 27.0 |
| 실행 장치 | CPU, Torch thread 1. MPS 가용성 probe False; 이 사실을 Apple 하드웨어 일반 한계로 확대하지 않음 |
| 설치·신규 학습 | 없음. 기존 `.venv` 사용, `pip freeze` 기록. 유료/클라우드/외부 전송/다운로드 없음 |
| 감사 산출물 | 새 `_audit/20260926_013033/`에만 작성. 원본 소스·가중치·기존 결과를 고치지 않음 |
| 파일 식별 | `logs/initial_manifest.json`의 모든 tracked 파일 SHA256, `runtime_results.jsonl`의 가중치·정규화 SHA256, `logs/pip_freeze.txt` |

최초 감사용 작업 디렉터리에서 경기 XML의 상대 텍스처 경로를 찾지 못했다. 로컬 원본의 텍스처를 가리키는 감사용 `data/textures` 링크를 추가한 뒤 같은 모델이 생성됐다. **첫 실패는 감사 실행 경로 문제이며 macOS 물리 실행 실패가 아니다.** 다만 해당 텍스처는 저장소에서 tracked되지 않고 `data/`는 ignore 대상이어서, 공개 checkout의 자족성은 별도 보완 대상이다(F15).

### 2.2 읽은 핵심 범위

- `README.md`, `.agents/AGENTS.md`, `run_demo.sh`, `requirements.txt`, `.gitignore`, `docs/PAPER.md`, `docs/EXPERIMENT_LOG.md`, `docs/VIDEO_CATALOG.md`, `docs/index.html` 관련 기술·결과 항목.
- `cognitive_ai/envs/`의 13개 환경·룰 모듈, `cognitive_ai/training/`의 각 진입점, `cognitive_ai/evaluation/`의 대표 시연 및 개별 평가 경로.
- `shared_assets/h1_baseball.xml`, `h1_pitcher.xml`, `h1_baseball_match.xml`, `h1_fielder.xml`, `h1_catcher.xml`, `h1_runner.xml`과 관련 모델·에셋 참조.
- 체크포인트 ZIP 메타데이터 24개, 정규화 파일 16개, 관련 `runs/` 및 `checkpoints/**/{logs,tb_logs}`의 npz/TensorBoard. `.gitignore`만 보고 파일 부재로 판단하지 않고 실제 로컬·tracked 여부를 확인했다.
- `scripts/patches/` 중 물리/키프레임/영상 이름 변경 관련 스크립트는 내용만 읽었다. 실행하지 않았다. `archive/`는 역사적 경로·Atlas 균형 보상·시각 관측 구조 등 필요한 부분만 확인했다.

### 2.3 실행 범위와 제외

환경 import·생성·reset·bounded step·종료 후 reset, 9종 태스크의 정책/기준선 일부, mega 타자 48D 추론, 판정 함수 합성 입력, 실제 경기 wrapper의 autoreset, Fielder 불안정 추적을 수행했다. 자세한 수·명령은 6절과 로그 참조.

다음은 하지 않았거나 완료하지 못했다.

- 신규·장시간 재학습, 다중 학습 시드 성능 검증, 정책 수정 후 재학습 ablation, 실로봇 실험, M4 교차 실행.
- 원본 `run_demo.sh` 전체 영상 생성: 기존 출력 덮어쓰기를 피하고 headless 검증을 우선했다. 중계·도루는 연결된 환경/정책을 따로 실행했으며 ‘원본 데모 전체 통과’로 보고하지 않는다.
- `CognitiveBaseballEnv` 원형은 생성자에서 renderer를 만들어 CoreGraphics 연결 오류로 실패. 이후 감사 인스턴스에서 renderer만 stub 처리한 검사와 원형 실행 실패를 분리했다.
- PDF 30페이지 전체 시각 검수 및 기존 MP4 15개 전체 프레임 검수. Markdown/HTML/카탈로그와 생성 코드를 근거로 판정했다.
- 외부 `.gemini/...` 원아티팩트, 원 MoCap 데이터, 실제 학습 당시 전체 패키지 lock·케이스 목록. 현재 없어도 당시 작업을 하지 않았다는 뜻은 아니다.

## 3. 실제 시스템 구조와 태스크 정의

### 3.1 실행 경로 표

| 기능 또는 주장 | 실제 진입점 | 연결된 환경·모델·가중치 | 사용 상태 | 확인 근거 |
|---|---|---|---|---|
| 기본 투타 중계 | `run_demo.sh:6` → `evaluation/simulate_full_match.py:10-32` | `training/train_mlb_batter.BatterMatchTrainingEnv` → `BaseballMatchEnv` / `h1_baseball_match.xml`; `mocap_pitcher_best`, `mocap_batter_best`, 각 pkl | 현재 README 기본 데모. 3개 단일 투구 시도 | 셸 호출·import·명시적 checkpoint 경로 |
| mega 타자/투수 | `training/train_mega_architecture.py:43-112` | 타자: MLB wrapper+기본 MLB 상대, 12D×4=48D; 투수: `PitcherEnv` 16D. `mega_*` zip/pkl | 별도 학습 경로, 기본 데모와 다름 | FrameStack·PPO 생성자·저장 메타데이터·TB |
| MoCap 이름 fine-tune | `train_mocap_pitcher.py:10-45`, `train_mocap_batter.py:10-47` | MLB weight/norm에서 계속 학습, 수작업 6키프레임 환경 | 기본 데모 가중치 생성 경로 | 실제 load→learn→save, pose imitation loss 없음 |
| 초기 투수 100% | `evaluation/eval_pitcher.py:13-30` | `PitcherEnv` 현재16D / `pitcher_best` 및 pkl13D | 과거 실험 경로, 현행 짝 로드 실패 | shape assertion 실제 재현 |
| 티볼·소프트토스·머신·변화구 | 각 train/eval 및 `video_evaluator.py` | 각각 독립 환경, `h1_baseball.xml`, 이름별 체크포인트 | 과거 개별 태스크, 현재도 일부 실행 가능 | 평가 import·저장/로드 경로·정책 실행 |
| 수비 | `evaluate_fielder.py:14-19` | `FielderEnv` / `h1_fielder.xml` / `fielder` | 개별 평가, 수치 불안정 확인 | 거리 기반 catch·5회 실제 실행 |
| 도루 | `run_demo.sh:9` → `evaluate_base_stealing.py:15-53` | catcher·runner 각각 로드, 실제 step은 runner만 | 별도 주자 시연. 수비와 경쟁하지 않음 | catcher predict/step 없음 |
| 9이닝 | `run_demo.sh:12` → `simulate_9_innings.py:14-27` | 난수 → `BaseballGameState` | 독립 텍스트 시연. `head -n 25`로 출력 제한 | MuJoCo/PPO 호출 없음; 과거 완주 로그 존재 |
| adversarial | `envs/adversarial_match_env.py:9-68` | 실제 계약과 다른 action12/obs26 stub | 현재 기본 경로 미연결 | reset은 문자열 `pitcher` 반환, opponent predict `pass` |
| 초기 인지/세계모델 | `train_cognitive.py:18-20,51-64` | `CognitiveBaseballEnv`; 수동 trigger threshold, mock WM loss | 별도 프로토타입 | WM_Loss 난수·경사 학습 부재 |
| egocentric vision·Atlas | `archive/` 및 `.agents/AGENTS.md:5-24` | 옛 로봇팔/Atlas/Dreamer 계열 | 과거 별도 아키텍처. 현재 H1 기본 경로 아님 | 현재 import 연결 없음; 전역상태 관측과도 다름 |

위 `training/`, `evaluation/`, `envs/`의 축약 경로는 모두 `cognitive_ai/` 아래다. 루트 `envs`, `simulator`, `training` 디렉터리 이름만으로 사용 경로를 추정하지 않았다. 문서의 `batter_env.py`는 현재 파일명과도 다르다.

### 3.2 누가 무엇을 결정하는가

| 구성 | 정책이 학습하는 부분 | 사람이 설계한 부분 | 실행 중 시뮬레이터에 직접 적용 |
|---|---|---|---|
| 투수 | 4개 연속값: release 진행률, z/x aim, power scale | 6개 자세, 선형 보간, release 공식·구종별 가속도 | 관절 qpos 덮어쓰기; weld 해제; 공 qvel에 계산한 속도 주입 |
| 타자 | 티볼1D 높이, 소프트/머신2D trigger+높이, 변화구/경기3D trigger+높이+yaw | 5/6개 자세, swing duration, 진입 허용 window, 예측 특징 | 관절 qpos 및 qvel=0 설정. 접촉 자체는 MuJoCo contact pair로 검사 |
| 수비/포수/주자 | 모델상 이동·상지 actuator 명령의 일부 | 바퀴 대신 slide 축, 관절 damping·제약, 목표점·보상 | motor ctrl 직접 입력, 현재 공 weld 잔존; 잘못된 body/joint 참조 별도 결함 |
| 심판·중계·경기상태 | 학습된 정책 없음 | 조건문·좌표 영역·확률·카운트 전이 | 카메라 선택·난수 사건 생성 |

투타 XML은 골반에 free joint가 없고 **공만 자유물체**다. 경기 모델의 `nu=0`을 실행으로 확인했다. 단독 투수는 motor5개가 있어도 `step()`은 ctrl을 쓰지 않고 qpos를 설정한다. 따라서 XML ctrlrange의 존재로 모터 제한을 지키는 전신 제어라고 설명할 수 없다. 단독 투수는 qpos만, 경기·타격 계열은 qpos와 해당 qvel을 함께 덮는 차이도 있다.

투수 `action[1:3]`가 단독 환경에서는 키프레임 열0,1,2(왼쪽 hip)에 적용되지만(`pitcher_env.py:123-126`) 경기에서는 열10,15,16(torso/right shoulder)에 적용된다(`baseball_match_env.py:188-191`). 관측 순서를 맞춰도 모델·제어·항력·바람 차이가 남는다. 동일 shape만으로 환경 동등성을 인정하면 안 된다.

### 3.3 핵심 태스크의 계약

모든 길이·속도는 별도 언급 없으면 world 좌표 m, m/s; 관절 각도는 rad다. 단독 타격/투구 관측은 이미지가 아니라 시뮬레이터 수치 상태다. 이는 허용된 state-based 태스크에서는 데이터 누수가 아니다. 현실 센서로 획득·추정했다는 증거도 아니다.

| 태스크 | 초기 상태 / 관측 / 행동 | 전이·보상·성공 | 실패·종료·주기 |
|---|---|---|---|
| TeeBall | 랜덤 높이 공, 3D 공위치, action1D 높이; reset부터 자동 swing | qpos 보간, 접촉 전 공속도0. 접촉 +100 및 종료+100, 실패 -50×최근접거리² | 접촉/swing 완료/40step. dt=.005, skip2 →10ms. 공 질량1e-6kg |
| SoftToss | 공 [0,4,1], vy[-8.2,-7.8], vz[1.55,2.05]; obs8=pos3/vel3/time/pred_z; action2 | trigger>0이면 일회 스윙. 접촉 순간100+종료150+속도항≤50. 실패 최근접거리²·trigger y=1.2와 차이 패널티 | 접촉·y<-.3·z<.1·swing완료, 45step timeout.20ms |
| PitchingMachine | 50계열 거리10m, 80계열15m; 목표z[.68,.95]에 맞춘 초기 탄도; obs8(pred_z 대신 z_zone); action2 | time≤.25에서 trigger. 접촉200+속도항≤50. 실패 거리²/이상 trigger시간.12/높이 오차 | Soft와 같은 종료,55step timeout.20ms |
| BreakingBall | 거리12m, 직구/슬라이더/커브 .40/.35/.25; 가속도 반영 초기 발사; obs9(pos/vel/time/z_zone/x_zone), action3 | 추가 가속도 qvel 주입; time≤.25 trigger. 접촉200+≤50. 실패 거리·이상시간.10·높이/yaw오차 | 접촉/지면/통과/swing완료,60step.20ms |
| Pitcher | 골반고정, 손-공 weld, target x[-.12,.12],z[.70,.93], 균등3구종; obs16 / action4 | pose+직접 ball velocity. y≤.20의 첫 위치에서 목표 XZ거리. d≤.20:1000+( .20-d)×1000+speed×3; miss:-300d; 미도달지면패널티 | plate도달/지면z≤.05/뒤로통과가 terminal,70step timeout.10ms. mound_distance 인자는 저장만 하고 XML 위치를 바꾸지 않음 |
| Match / MLB wrapper | 두 고정골반, 구종/target+wind ±4. pitcher16,batter12; action4/3 | batter에 탄도 time/z_zone/x_zone와 구종정답 onehot 제공. time≤.080+release 조건 아래 swing. 접촉 실제 contact pair. wrapper는 접촉 후 매 step300+속도≤150+거리≤100 | y<-.5·z≤.05·총limit 또는 접촉후limit. train70/접촉후20,eval450/접촉후350.10ms; wrapper는 timeout도 terminated로 반환 |
| Fielder | 공 [0,0,1]에서 랜덤 발사; obs30=공6/base6/상지18, action12 | slide 이동 actuator와 상지제어. -.1×glove-ball 거리, 거리<.25 →+1000 catch | 공높이<.2 실패-50,200step 제한.20ms. 실제 실행은 불안정으로 조기 reset; F02 |
| Catcher | obs30,action12(실효7); 공 y18.4에서 발사+base/상지 관측 의도 | -.1×잘못 조회한 geom까지 거리, glove 접촉 +1000 | 150step/공y<-2·z<.1/포구.50ms. 실제 glove id=-1; F04 |
| Runner | obs8=현재로 간주한pos3/vel3+target와의차이2,action3 slide/heading 힘 | -.05×거리+.1×목표방향속도, 거리<1이면1000 | 300step timeout.50ms. 현재 pos가 공 상태여서 실제 주자 도달 판정 아님; F03 |

전체 상세 추출·줄 근거는 `notes/physics_tasks.md` 및 `notes/training_eval.md`에 남겼다. `BaseballMatchEnv` 자체는 Gymnasium 표준 단일-agent API가 아니라 dict reset / `(obs,done,info)`의 내부 2-agent 시뮬레이터다. 이를 wrapper에서 변환하는 설계 자체가 오류는 아니며, 그 계약을 잘못 소비하는 adversarial stub가 별도 문제다.

### 3.4 문제 정의와 방법·실험 과정 판단

현재 목적에는 ‘맞히기’, ‘빠르게 던지기’, ‘스트라이크/볼 구별’, ‘그럴듯한 폼’, ‘중계’, ‘경기 규칙’이 함께 있지만 각각의 성과를 따로 정의해야 한다. 접촉률은 안타율이 아니고, 한 공을 지켜본 보상은 볼넷/전술 성과가 아니다. ‘MoCap pose reward’는 현재 투수 보상에 존재하지 않는다. 폼 유지의 상당 부분은 학습 목표가 아니라 지정된 자세 재생이다.

RL은 이런 저차원 연속 매개변수의 선택에도 쓸 수 있다. 그러나 고정 타이밍·물리식 규칙·작은 탐색과의 비교가 없으면 **필요성/효과 미검증**이다. 이번 소표본은 규칙도 일부 접촉을 만들고 단독 투수 PPO가 고정값보다 잘한 사례를 보여 주지만, 충분한 최적화 기준선이나 독립 검증집합 비교는 아니다.

반복된 TensorBoard run, 진단/패치 스크립트, git 변경, phase별 문서로 시행착오의 존재는 확인된다. 반면 환경·동작·보상·정규화·학습량이 함께 달라져 어떤 변경이 개선을 일으켰는지 분리하기 어렵다. 예를 들어 tee 이전 로그의 episode length100은 현재 limit40과 맞지 않으며, 소프트토스는 5개 TB run과 하나의 덮어쓰기형 evaluation 경로가 존재한다. **과정 전체가 엉터리라는 결론이 아니라, 통제 비교의 재구성이 불가능한 범위가 크다는 결론**이다.

평가 보상으로 checkpoint를 선택한 사실은 명확하지만, 같은 최종 사례에 반복 튜닝해 과적합했는지는 확인할 수 없다. 고정된 독립 holdout, 명시적 가설→변경1개→동일조건 비교 기록이 없다. FrameStack·항력·스케줄·보상 변경의 개별 효과는 재학습 비교가 필요하다. 학습 조건의 보조를 평가 때 제거해 얻은 성능 저하를 공정한 ablation이라고 해석하지 않는다.

## 4. 프로젝트의 주장과 확인된 증거 비교표

| 실제 주장 / 위치 | 근거 | 검증 상태 | 설명 가능한 범위 | 추가 확인 |
|---|---|---|---|---|
| 수백만 PPO step,4-frame 타자 / README25 | mega 코드,24개 ZIP,TB | 정적+기존로그+추론 확인 | 학습기록·48D 모델 존재. 기본 데모는12D mocap | FrameStack의 독립 효과,heldout |
| 오타니 광학 MoCap retarget / HTML1122 | 현재6개 pose상수,patch 문자열 | 원자료 확인 불가 | 사람 설계 자세를 보간하며 PPO가 조정 | 원motion·출처·변환 코드 |
| LSTM / PAPER46 | `MlpPolicy` 생성·저장 | 확인된 불일치 | MLP+frame concatenation | 도식 정정 |
| 동역학이 지배하는 자율 시뮬레이션·관절 제어 RL / PAPER137-139 | 고정골반,qpos 덮기,ball qvel 주입 | 넓은 표현과 실제 범위 불일치 | 기구학적 동작+저차원 policy. PAPER151도 한계 인정 | 전신 태스크는 새 정의 |
| COR1.35 접촉속도 증폭 / PAPER85-87 | active contact분기에 없음. patch script 문자열에만 존재 | 확인된 불일치 | 현재 MuJoCo contact는 존재하나 명시1.35 증폭 없음 | 실제 적용버전·검증된 충돌 모델 |
| 정밀 Magnus / README26,PAPER78-83 | 구종별 상수가속도+별도 force 경로 | 구현확인/물리정확성 미검증 | 궤적에 인위적 구종효과 있음. 실제 spin vector 미사용 | 단일 힘 모델·기준 궤적·계수 |
| 티볼90%,소프트70%,머신60% / EXP_LOG11,16,21 | 기존로그·가중치·평가코드 | 정확한 과거수치 재현 미확인 | 새 별도 사례는 tee3/5,soft6/10,50머신5/10,80deep2/10 | 원분모·시드·소스·weight/norm 짝 |
| 변화구66.7%=10/15 / EXP_LOG26 | 분모 문서에 명시; 기존정책실행 | 과거10/15 재현 미확인 | 이번에는1/10 contact | 원15사례·구종분포 |
| 투수100%/15회,84.4km/h / EXP_LOG33 | 평가조건 코드 존재,현재13→16D 불일치 | 기존경로 로드실패 확인 | mega 별도10/10,152.34km/h를 대신 과거결과로 쓰면 안 됨 | 당시13D 환경/통계/설정 복원 |
| 200만 후0.22m / PAPER131 | mega 내부평가5회씩,현재 기준.20 | 일부 뒷받침;원수치 산식 미확인 | 현재10개에서는max.1703m, 그 표본에 한함 | 당시 raw오차·분모 |
| FrameStack후 헛스윙 대폭 감소 / PAPER132 | stack구현,타자TB,ablation없음 | 미검증 가정 | 구조변경·학습 수행만 확인 | 동일태스크1/2/4 frame 재학습 |
| 외야5/5 포구 / PAPER133 | 이번에도5/5 flag,모두불안정 | 성공집계는 재현,정상포구 성과는 차단 | 수치 reset 뒤 근접한 것을 catch로 집계 | F02 수정후 정상 물리 평가 |
| 주자30m·도루 / PAPER133 | runner만 step,잘못된공좌표 | 구현 결함 확인 | 경쟁 도루 실증 아님 | F03,수비상대·시간경쟁 |
| 정확한3D심판/자동카메라 / README28-29 | 합성교차BALL,contact flag누락,autoreset | 확인된 결함 | 규칙 기반 프로토타입 | F05/F07 |
| Full9이닝 / README30,PAPER123-134 | 난수→상태머신,기존완주로그 | 독립텍스트 시연 확인;통합경기 아님 | 이닝/점수 전이 프로토타입 | 파울수정·실제이벤트연결 |
| ZMP에90%이상 연산량 / HTML1151 | profiling기록 미발견 | 확인 불가 | 회고의 정량주장 | 당시 profiler/분모/기기 |
| 발 들림 감소·균형회복 성과 | 현재문서/지표 검색에 그런 성과 없음 | 프로젝트 주장으로 채택하지 않음 | 사용자 예시를 사실로 만들지 않음 | 목표로 삼는다면 별도 측정 정의 |

## 5. 우선순위별 발견 사항

발견의 분류는 **① 확인된 문제 / ② 확인 불가 / ③ 미검증 가정 / ④ 선택적 개선**이다. ‘진행 차단’은 아래에서 명시한 주장·실험만 막는다. 모든 개발을 멈추라는 의미가 아니다.

### F01. 같은 16차원 관측의 열 의미가 학습·경기에서 다르다

- 분류: **① 확인된 문제**.
- 우선순위: **진행 차단 — 연결된 경기 정책의 정상 입력·성능 주장과 추가 경기 학습을 막음**. 단독 PitcherEnv 검증은 계속 가능.
- 근거 수준: 정적 확인 + 실제 실행 확인.
- 위치: `cognitive_ai/envs/pitcher_env.py:238-250`; `cognitive_ai/envs/baseball_match_env.py:374-406`; `cognitive_ai/training/train_mlb_batter.py:43-46`.
- 관찰한 사실: 단독은 `[target2,released,ball_pos3,ball_vel3,hand_pos3,progress,onehot3]`, 경기는 `[target2,released,progress,ball_pos3,ball_vel3,hand_pos3,onehot3]`. index3~12 의미가 다르다. 합성 동일 상태에서 progress=.42와 ball_x=.12가 다른 열에 들어감을 재현했다. wrapper는 경기 관측을 그대로 단독 투수 통계에 넣는다.
- 문제가 되는 이유: shape 검사를 통과해도 정책의 입력·평균·분산이 다른 물리량에 적용된다.
- 영향을 받는 결과·주장: MLB/MoCap/mega 타자 상대 투수, 기본 투타 연결.
- 최소 재현 방법: `scripts/runtime_audit.py smoke`의 `synthetic_observation_contract`; 원본 수정 없음.
- 구체적인 보완 행동: 이름·단위·순서를 가진 단일 schema와 adapter를 정의하고 저장 정책의 schema 버전을 기록. 단독/경기의 키프레임 조정 관절·항력 차이도 별도 환경 차이로 다룬다.
- 보완 후 통과 기준: 같은 의미의 상태가 같은 관측·정규화 벡터를 만들고, wrapper에서 학습 때의 계약을 사용함을 열별 검증.
- 아직 모르는 부분: 각 과거 weight의 실제 학습 소스, 이 불일치의 성능 영향 크기. 현재 타자가 잘못 연결된 상대에 적응했을 수도 있어 수정 후 재평가가 필요하다.

### F02. Fielder의 5/5 성공이 수치 불안정 뒤에 발생한다

- 분류: **① 확인된 문제**.
- 우선순위: **진행 차단 — 정상 물리 포구 성과 주장과 이 환경의 추가 학습을 막음**.
- 근거 수준: 실제 실행 확인 + 정적 확인.
- 위치: `cognitive_ai/envs/fielder_env.py:51-85,96-139`; `shared_assets/h1_fielder.xml:76-81,152,168`; `cognitive_ai/evaluation/evaluate_fielder.py:33-56`.
- 관찰한 사실: 저장 정책 5개 seed 모두 catch=True였지만 초반 QACC 불안정 경고와 시뮬레이션 시간 되감김이 있었다. seed0 첫 외부 step은 0.02s가 되어야 하는데 실제0.01s, warning[5].number=1이었다. 이후 7step/t=.13s에서 거리 .1882m를 catch로 집계했다. 공 weld가 활성 상태이고 초기 공이 origin_pole과 겹친 접촉도 확인됐다. 모든 값이 finite여도 이 현상이 발생한다.
- 문제가 되는 이유: 정상 초기 상태부터 이어진 뜬공 궤적을 잡은 실험이 아니다. MuJoCo는 수치값이 비정상/과대일 때 자동 reset할 수 있다([공식 시뮬레이션 문서](https://mujoco.readthedocs.io/en/3.6.0/programming/simulation.html)).
- 영향을 받는 결과·주장: `docs/PAPER.md:133` 외야 5/5 포구. 이번 재현도 성공 flag만 재현한 것이며 정상 성능 증거로 사용 불가.
- 최소 재현 방법: `scripts/physics_probe.py` fielder 모드와 `scripts/fielder_trace.py`; `logs/fielder_trace.jsonl`에서 time/warning/좌표 비교.
- 구체적인 보완 행동: 초기 관절·공 상태를 joint 주소로 설정, 초기 겹침 및 비의도적 weld 제거, warning/시간 연속성 이상을 별도 수치실패로 종료. 근접거리와 유지 가능한 포구를 구분.
- 보완 후 통과 기준: 고정 케이스 모두 물리 시간 단조증가·예상 dt 일치·BADQACC/QPOS/QVEL 경고0, reset 점프0, 정상 비행 후 정의한 접촉/유지 조건 충족.
- 아직 모르는 부분: weld·초기 겹침·제어기 중 각 원인의 기여. 감사의 weld-off 합성 검사는 원인 분리 단서이며 정책 재학습 ablation이 아니다. 과거 5/5 영상도 동일 상태였다고 단정하지 않는다.

### F03. Runner가 공 좌표로 주자 도달을 평가한다

- 분류: **① 확인된 문제**.
- 우선순위: **진행 차단 — 주자 목표 도달·도루 성과 주장과 해당 환경 학습을 막음**.
- 근거 수준: 정적 확인 + 실제 실행 확인.
- 위치: `cognitive_ai/envs/runner_env.py:29-38,46-49,64-78`; `shared_assets/h1_runner.xml:76-81`; `cognitive_ai/evaluation/evaluate_base_stealing.py:46-66`.
- 관찰한 사실: XML에서 첫 joint는 공의 freejoint인데 관측/거리에서 `qpos[:3]`, `qvel[:3]`를 주자 상태로 사용. reset 실제 base [27.4,27.4,.4]와 관측 [19.4,19.4,2.35]가 다르다. 합성 상태에서 주자를 목표 밖에 두고 공만 목표에 놓아도 reward1000/terminated가 된다.
- 문제가 되는 이유: 보상 대상과 실제 조작 대상이 다르며 실제 주자 성공이 아닌 상태로 통과할 수 있다.
- 영향을 받는 결과·주장: 30m 주루·SAFE/OUT. 도루 평가에는 catcher 행동도 연결되지 않는다.
- 최소 재현 방법: `physics_probe.py` runner 모드의 synthetic 판정. 물리를 동결한 함수/주소 검증이며 정책이 exploit했다는 실증은 아님.
- 구체적인 보완 행동: base joint 주소 또는 해당 body의 world position/velocity를 명시적으로 사용하고 목표 좌표계 일치. 도루가 목표면 수비 송구·태그/도착 시간 경쟁을 별도 구현.
- 보완 후 통과 기준: 공만 이동하면 주자 관측·거리·성공은 불변, 주자만 이동하면 그에 맞게 변함. 목표 밖 reward1000 불가.
- 아직 모르는 부분: 기존 정책이 이 결함을 얼마나 이용했는지. 이번 실제 정책5회는 모두 시간초과였다.

### F04. Catcher의 glove 이름 및 관측 주소가 모델과 다르다

- 분류: **① 확인된 문제**.
- 우선순위: **진행 차단 — 포구 판정·포수 학습의 유효성을 막음**.
- 근거 수준: 정적 확인 + 실제 실행 확인.
- 위치: `cognitive_ai/envs/catcher_env.py:16,21-25,29-38,46-49,61-64,76-91`; `shared_assets/h1_catcher.xml:76-81,116`.
- 관찰한 사실: `glove_box` 조회는 -1, 실제 이름은 `glove_geom`. 합성으로 실제 glove와 ball contact pair [5,22]를 만들어도 catch=False. base라고 읽는 첫 qpos/vel도 공 상태이고 일부 action의 actuator 조회는 없어서 적용되지 않는다.
- 문제가 되는 이유: 목표 접촉이 보상/성공으로 이어지지 않고 관측과 행동의 의미도 선언과 달라진다.
- 영향을 받는 결과·주장: 포수 reaction/catch와 결합 도루 기능.
- 최소 재현 방법: `physics_probe.py` catcher 모드의 ID·실제 접촉 합성 검사.
- 구체적인 보완 행동: 모델의 실제 이름과 joint 주소를 사용, 필수 ID>=0 assertion, action 항목→actuator 전체 매핑 표. 쓰지 않는 action 차원은 제거하거나 계약상 명시.
- 보완 후 통과 기준: 올바른 glove contact 양성/다른 geom 음성, 각 허용 action의 적용 경로 확인, 공과 base 관측 분리.
- 아직 모르는 부분: 이름 수정 후의 성능. 체크포인트 재학습 필요 여부는 별도 확인해야 한다.

### F05. 중계가 실제 컨택과 종료 직전 상태를 놓친다

- 분류: **① 확인된 문제**.
- 우선순위: **진행 차단 — 기본 중계의 타구 판정·카메라 전환·최종 위치 해석을 막음**.
- 근거 수준: 정적 확인 + 실제 경기 wrapper의 합성 실행 확인.
- 위치: `cognitive_ai/evaluation/simulate_full_match.py:60-87`; `cognitive_ai/envs/baseball_match_env.py:118-123,268-272,293-306`.
- 관찰한 사실: 환경은 `has_contacted`, 평가기는 `has_hit`을 사용. fallback batted_distance는 종료 때만 계산되고 DummyVecEnv가 바로 reset한다. 합성 종료에서 info.has_contacted=True, terminal ball≈[0,20,3]인데 평가기가 읽는 raw ball=[0,10,1.2], hit_detected=False였다. swing 필드도 실제 `b_swing_active`와 다르다.
- 문제가 되는 이유: 같은 에피소드의 마지막 사건·위치 대신 초기화된 상태로 카메라와 심판을 판단한다. SB3 자동 reset은 정상 API이며 소비 코드의 오류다([공식 VecEnv 문서](https://stable-baselines3.readthedocs.io/en/master/guide/vec_envs.html)).
- 영향을 받는 결과·주장: 동적 카메라·정밀 중계, 결함 없는 demo.
- 최소 재현 방법: `runtime_audit.py followup`의 synthetic_demo_autoreset. contact flag를 강제한 판정 검사이며 실제 정책 접촉으로 세지 않음.
- 구체적인 보완 행동: 마지막 ball/trajectory/contact/swing/pitch_type을 info에 보존; 평가가 그 전이의 info를 사용하도록 통일. 렌더 frame은 reset 전 상태에서 확보.
- 보완 후 통과 기준: 컨택/무접촉/헛스윙 합성 사례에서 info·영상·카메라·심판이 같은 에피소드 사건과 일치.
- 아직 모르는 부분: 과거 영상 생성 시 적용된 코드와 현재 코드의 차이.

### F06. 물리·MoCap·학습 동작의 설명 범위가 실제보다 넓다

- 분류: **① 확인된 주장·구현 불일치**. 원 MoCap 출처 부재는 F13의 확인 불가와 구분.
- 우선순위: **이번 단계 보완 — 전신제어·물리정확성·COR 구현 주장 차단**.
- 근거 수준: 정적 확인 + 모델/합성 힘 실행 확인.
- 위치: `cognitive_ai/envs/pitcher_env.py:57-67,143-172,223-236`; `cognitive_ai/envs/baseball_match_env.py:154-172,238-264,268-272,342-372`; `shared_assets/h1_pitcher.xml:68`; `shared_assets/h1_baseball_match.xml:123,196-198,272-280`; `docs/PAPER.md:85-99,137-139`.
- 관찰한 사실: 고정골반·qpos 재생·공속도 직접주입. 투수 reward에 모방 pose loss 없음. COR1.35는 `scripts/patches/patch_physics_full.py:47`의 미적용 텍스트에만 있고 실제 접촉 분기에는 없음. Match는 추가 가속도/항력을 qvel에 더하고 별도 `_apply_aerodynamics`에서 힘도 준다. spin angular velocity 대신 구종 ID에 따른 규칙으로 방향 결정. v=[0,-30,0] 합성에서는 force/질량 항력31.03m/s²와 별도 직접항력4.86m/s²가 같이 존재한다.
- 문제가 되는 이유: 모델의 목적을 설명하지 않으면 외부에서 지정한 운동을 정책이 동역학적으로 학습한 결과로 오해한다. 이중 물리 경로는 단일 투수와도 다르다.
- 영향을 받는 결과·주장: realistic restitution, precise aerodynamics, MoCap imitation, 전신 동작·실물 전이. 직접 상태 변경 자체가 금지라는 뜻은 아니다.
- 최소 재현 방법: 위 코드 및 `runtime_audit.py smoke`의 nu/freejoint/force 결과. force 값은 합성 단위검사이지 실제 구속 성과가 아님.
- 구체적인 보완 행동: 허용된 기구학 보조·속도 주입을 task spec에 명시. 힘/가속도 단위와 구종 모델을 하나로 통합하고 별도 탄도 검증. 구현하지 않은 COR/pose reward 설명 정정.
- 보완 후 통과 기준: 동일 정의로 학습/평가 궤적 일치, 알려진 초기상태의 수치 궤적을 재현, 정책·보조 각각의 결정 경로가 설명과 동일.
- 아직 모르는 부분: 실제 야구공/배트 측정과의 오차, torque 기반 대체 구현의 비용. 이 감사로 실물 구현 불가능성을 증명한 것은 아님.

### F07. 파울 카운트 결함과 서로 다른 심판 기준

- 분류: **① 확인된 문제**.
- 우선순위: **이번 단계 보완 — 표준 규칙·엄밀한 판정 주장 차단**.
- 근거 수준: 정적 확인 + 합성 실행 확인 + 기존 로그.
- 위치: `cognitive_ai/envs/baseball_game_state.py:27-31`; `cognitive_ai/envs/baseball_rules.py:13-28,54-57`; `cognitive_ai/envs/baseball_match_env.py:302-332`; `runs/sim_9_inning.log:1098-1099`.
- 관찰한 사실: 일반 파울 처리 전 reset_count로 2S3B→1S0B. 기존 로그에서도 비슷한 역행. 심판은 점만 검사해 [0,.3,.8]→[0,-.3,.8]의 box 관통을 BALL로 반환. 투수는 plate 통과 target 반경.20, Match는 종료시 target 반경.22, umpire는 고정 box. HR도 Match60m+높이와 umpire120m가 다르다.
- 문제가 되는 이유: 같은 투구/타구를 학습 성공과 경기 평가에서 다르게 분류할 수 있다. 단순 룰 프로토타입 자체는 허용되나 ‘오차 없는 표준 경기’와 다르다.
- 영향을 받는 결과·주장: strike율·타율·home run·9이닝 카운트.
- 최소 재현 방법: `rules_and_checkpoint_probe.py`, `additional_contracts.py`. 선분 검사는 합성 경계 사례이며 실제 오판 빈도 아님.
- 구체적인 보완 행동: 파울은 count 유지 전이로 수정, authoritative 판정 함수 하나와 plate-crossing event 기록. 공 중심/반지름·파울/담장/종료 범위를 명시.
- 보완 후 통과 기준: 0S0B→1S0B,1S2B→2S2B,2S3B→2S3B; 빠른 관통/비관통; 동일 사건의 학습·평가 라벨 일치.
- 아직 모르는 부분: 현재 정책의 실제 교차 누락 비율, 완전한 야구 규칙 전체 구현 비용.

### F08. 평가 중 정규화 갱신과 best 가중치·통계 저장 시점 분리

- 분류: **① 확인된 평가 설정 문제**.
- 우선순위: **진행 차단 — 고정 조건의 best 선정 및 과거 best 성능 정확 재현 주장 차단**.
- 근거 수준: 정적 확인 + 설치 SB3의 합성 실행 + 가중치/통계 메타데이터.
- 위치: `cognitive_ai/training/train_mega_architecture.py:55-73,85-101`; `cognitive_ai/training/train_mocap_batter.py:31-47`; `cognitive_ai/training/train_mocap_pitcher.py:28-45`.
- 관찰한 사실: mega eval `training=True,norm_reward=True` 기본값, 평가 중 obs/return 통계 갱신을 재현. EvalCallback의 **평가 직전 sync는 존재**하므로 ‘통계 미동기화’가 아니다. best 저장과 learn 종료 pkl 저장이 별개. mega pitcher weight1.6M vs norm count2,015,248, batter weight1.92M vs norm count2,031,632.
- 문제가 되는 이유: 평가 입력과 reward scale이 변하고 early best 당시 통계와 현재 pkl의 동일성을 보장하지 못한다. count는 관측 샘플 누적수이며 weight step과 동일 단위라고 가정하지 않았고, 분리 저장 코드를 함께 근거로 판단했다.
- 영향을 받는 결과·주장: mega 개선곡선, 최선 정책 선택·재현성. 이번 감사에서는 통계를 명시적으로 동결했다.
- 최소 재현 방법: `vecenv_contract_probe.py`; metadata pkl count와 저장 호출 비교.
- 구체적인 보완 행동: eval `training=False,norm_reward=False`, new-best 시 weight/norm/config/seed 함께 저장, 원보상과 contact/strike/수치실패 별도 기록.
- 보완 후 통과 기준: 평가 전후 rms 불변, bundle 재실행 입력변환 동일, 선택평가와 최종 holdout 분리.
- 아직 모르는 부분: 과거 best 통계의 실제 값·성능 영향. mismatch 크기를 임의 수치로 추정하지 않는다.

### F09. 과거 투수 가중치는 현재 환경과 호환되지 않고 별도 MoCap 평가는 정규화를 우회한다

- 분류: **① 확인된 문제**.
- 우선순위: **진행 차단 — 해당 두 평가 경로의 성과 재현/해석 차단**.
- 근거 수준: 정적 확인 + old 투수 로드 실제 실패.
- 위치: `cognitive_ai/evaluation/eval_pitcher.py:14-30`; `cognitive_ai/evaluation/evaluate_mocap_match.py:36-40,61-66,80-88`.
- 관찰한 사실: old pkl13D/current16D로 `spaces must have the same shape: (13,) != (16,)`. 현재 경로의 Git source snapshots를 확인해도13D 당시 상태를 찾지 못했다. 별도 MoCap 평가는 b_norm을 만들고도 raw b_vec.reset/step 결과로 predict하며, pitch_speed 키도 실제 pitch_speed_kmh와 다르다.
- 문제가 되는 이유: 파일이 있다는 것과 대응 환경이 있다는 것은 다르다. 정규화되지 않은 입력은 학습 때와 다른 정책 평가다.
- 영향을 받는 결과·주장: 15회100%/84.4km/h의 정확 재현, MoCap box score. 기본 simulate_full_match는 b_vec 자체를 VecNormalize로 재할당하므로 이 정규화 우회 결함과 구분.
- 최소 재현 방법: `runtime_audit.py followup`의 original_eval_pitcher_pair; MoCap reset/step 사용 변수 추적.
- 구체적인 보완 행동: old13D 버전·설정을 찾으면 감사용 별도 snapshot에 복원, 없으면 재현미확인 표시. MoCap 평가를 b_norm과 terminal info로 통일.
- 보완 후 통과 기준: 계약 검사를 통과한 weight/norm/env 묶음, 정책 입력 수치가 학습 transform과 같음.
- 아직 모르는 부분: 원15개 사례와 당시 source. 임의로 현재 관측3개를 제거한 결과를 원성과 재현으로 보고하면 안 됨.

### F10. 보상·시간제한·성공사건이 목표와 어긋나는 경로

- 분류: **① 확인된 문제**(action attribution/API) 및 태스크 정의의 보완 필요.
- 우선순위: **이번 단계 보완 — 보상개선의 해석 및 추가 학습 전 수정**.
- 근거 수준: 정적 확인 + 실제 통제 실행.
- 위치: `cognitive_ai/envs/pitching_machine_env.py:128-137,178-179`; `cognitive_ai/envs/breaking_ball_env.py:137-157,202-205`; `cognitive_ai/training/train_mlb_batter.py:49-67`; `cognitive_ai/envs/baseball_match_env.py:279-287`.
- 관찰한 사실: 타격 높이/yaw는 trigger 시 한 번만 고정되지만 miss 페널티는 종료 step의 action으로 계산된다. trigger 이후 값을 바꾸면 최종 qpos가 완전히 같아도 두 머신 실행 return=-215.0843/-216.4347, 변화구=-248.6415/-244.6663으로 달랐다. 경기 contact 보상은 한 번이 아니라 contact 이후 매 step 반복되고 eval의 post-contact horizon은20→350. timeout도 wrapper에서 terminated=True로 반환한다.
- 문제가 되는 이유: 행동이 궤적을 바꾸지 않아도 보상을 바꾸는 경로가 있고, 평가길이에 따라 같은 접촉의 누적보상이 달라진다. contact를 안타, 한 공 BALL을 WALK로 부르는 집계도 별도 경기지표가 아니다.
- 영향을 받는 결과·주장: reward 곡선·타격 개선·box score. 실제 정책이 이 경로를 악용했다는 것은 미확인.
- 최소 재현 방법: `runtime_audit.py followup` post_trigger_reward; 보상·horizon 분기 정적 추적.
- 구체적인 보완 행동: trigger에서 사용한 action을 저장해 그 값으로 평가; 접촉 event 보상과 비행/거리 보상 목적을 분리; timeout은 truncated. 안타/볼넷은 실제 타석 사건이 있을 때만 집계.
- 보완 후 통과 기준: 적용되지 않은 종료 action만 바꾸면 궤적과 task 보상 불변, 평가 horizon 변경의 의도된 보상 차이를 명시, terminal/truncation 검사 통과.
- 아직 모르는 부분: 현재 가중치에 미친 영향과 수정 후 재학습 성능.

### F11. seed 계약이 지켜지지 않고 경기 관측이 선언 범위를 벗어난다

- 분류: **① 확인된 문제**.
- 우선순위: **이번 단계 보완 — 사례 재현성과 입력 계약 보완**.
- 근거 수준: 정적 확인 + 실제 실행 확인.
- 위치: `cognitive_ai/envs/pitcher_env.py:88-105`; `cognitive_ai/envs/soft_toss_env.py:60-83`; `cognitive_ai/envs/pitching_machine_env.py:63-110`; `cognitive_ai/envs/breaking_ball_env.py:57-120`; `cognitive_ai/envs/baseball_match_env.py:125-138,398-406`; `cognitive_ai/training/train_mlb_batter.py:23`.
- 관찰한 사실: `super().reset(seed=...)`와 별개 전역 np.random 사용. 네 단독 환경에서 연속 reset(seed=777)이 다른 관측을 반환. 경기 reset에서는 vy=0인데 time=98s, z_zone≈-348942가 생겨 Box±100을 벗어남. 이는 finite이며 저장 통계도 큰 음수 평균을 포함한다. reset은 is_in_strike_zone를 지우지 않아 직전 값 잔존.
- 문제가 되는 이유: seed 인자만으로 사례를 고정할 수 없고, 도달하지 않는 공에 탄도 도달시간 의미가 생긴다. 잘못된 bound는 wrapper 계약과 실제값을 다르게 한다.
- 영향을 받는 결과·주장: 재현성, 관측공간·미래예측 설명. 현재 정규화 후 값이 반드시 ±10 포화라는 뜻은 아님(이번 reset은 약±4대).
- 최소 재현 방법: smoke reset_seed, additional_contracts match_reset_bounds, synthetic_reset_stale.
- 구체적인 보완 행동: self.np_random으로 일원화; release/접근 여부 mask와 유효한 예측값 정의; 모든 episode flag 초기화. 감사 비교는 이를 기다리지 않고 전역 NumPy/Torch seed까지 직접 고정했다.
- 보완 후 통과 기준: 같은 seed/명령→동일 초기상태·궤적, 선언 bounds 또는 무한범위와 실제값 일치, reset 잔존 flag0.
- 아직 모르는 부분: 과거 여러 프로세스 난수 중복/상관 정도. 이번 검사는 M4·다른 버전 간 bitwise 재현 보증 아님.

### F12. 완료되지 않은 인지·adversarial 실험이 현재 경로와 혼재한다

- 분류: **① 확인된 구현 결함**, 상태를 ‘프로토타입’으로 분류.
- 우선순위: **이후 개선 — 이 경로로 새 학습을 시작할 때 차단**, 기본 데모 결함으로 확대하지 않음.
- 근거 수준: 정적 확인 + 부분 실행 확인; renderer 원형은 실행 제약.
- 위치: `cognitive_ai/training/train_cognitive.py:18-20,51-64`; `cognitive_ai/envs/cognitive_baseball_env.py:28-32,141-154`; `cognitive_ai/envs/adversarial_match_env.py:20-22,31-53`.
- 관찰한 사실: cognitive trainer는 threshold를 수동 갱신하고 WM loss는 난수. 존재하지 않는 root_y ID=-1이 마지막 ball joint 주소로 연결되어 공을 덮는 인덱스 결함. adversarial reset은 dict의 key를 해체해 관측 문자열 'pitcher'를 반환하며 타자 inference는 pass, step 반환 개수도 다르다.
- 문제가 되는 이유: 해당 경로를 학습된 세계모델/자기대전의 실행 증거로 쓸 수 없다. 옛 지침 `.agents/AGENTS.md`의 엄격한 egocentric vision도 현재 state-based 주경로와 다르다.
- 영향을 받는 결과·주장: 해당 파일의 재사용·새 학습. 문서가 ‘self-play 초석’으로 한정한 부분까지 완료 주장으로 취급하지 않는다.
- 최소 재현 방법: `additional_contracts.py` adversarial_reset_return; `physics_contracts.py`의 renderer stub 후 ID 추적(`physics_contracts_contacts.jsonl` synthetic_cognitive_lookup). 원형 `physics_probe.py --task cognitive`는 렌더 생성에서 실패했으며 실제 카메라 관측을 검증한 것이 아님.
- 구체적인 보완 행동: prototype/legacy 표시, ID assertion, 실행 가능한 정책 계약이 완성될 때만 학습 명칭 사용. 문맥 파일도 현재 경로와 분리.
- 보완 후 통과 기준: root_y 조회 유효/없는 경우 명시 실패, 공 주소 덮기0, reset/step shape 일치, 실제 loss update·동결 상대 predict 경로 확인.
- 아직 모르는 부분: 외부 세계모델 구현·옛 코드 버전·개발자의 의도.

### F13. 과거 성능 수치와 원자료의 대응을 복원하지 못했다

- 분류: **② 확인 불가**.
- 우선순위: **이번 단계 보완 — 해당 과거 수치·외부 검증·광학 MoCap 주장의 현재 확정 표현 차단**.
- 근거 수준: 문서·기존 로그에 존재하는 주장 + 정적 자료 조사.
- 위치: `docs/EXPERIMENT_LOG.md:9-33`; `docs/PAPER.md:131-147`; `docs/index.html:1122,1151,1419,1610-1614`; `runs/teeball_eval/evaluations.npz`; `checkpoints/mega_*/logs/evaluations.npz`.
- 관찰한 사실: 로그는 있지만 source/XML/weight/norm/case를 묶는 manifest가 없다. 과거 tee length100과 현행40, 같은80km/h 영상의 타자60%/투수93.3% 설명, tee문서2D/현행1D 불일치. 원광학MoCap·90% ZMP profiler·전문가검토 원문은 미확인.
- 확인이 필요한 이유: 현재 보이는 로그만으로 원 주장 전체가 참/거짓인지 정할 수 없고, 다른 단계 수치를 현재 구현 성과로 합치면 안 된다.
- 영향을 받는 결과·주장: 과거70/60/66.7/100%,0.22m·개선 원인·독립 외부 평가.
- 최소 재현 방법: `notes/claims_history.md`의 원로그 표 및 `logs/source_history_contracts.json`; 분모와 소스 식별 가능 여부를 대조.
- 구체적인 보완 행동: 회수 가능한 각 성과의 원사례/명령/asset hash 연결. 못 찾은 것은 ‘과거 보고값·재현미확인’으로 표시하고 새 측정과 분리.
- 보완 후 통과 기준: 각 숫자가 한 번의 명령과 고정 bundle/분모에 연결되거나, 정확히 미확인으로 남음.
- 아직 모르는 부분: 저장소 밖 당시 자료. 부재를 작업 미수행·기만의 증거로 쓰지 않는다.

### F14. RL·FrameStack·보조 구성요소의 독립 효과가 미검증이다

- 분류: **③ 추가 실험이 필요한 가정**.
- 우선순위: **이번 단계 보완 — 방법의 효과/필요성 주장을 하려는 경우**.
- 근거 수준: 문서 주장, 비교자료 미확인, 이번 소표본만 실행.
- 위치: `docs/PAPER.md:23,60,111,132,190-192`; `cognitive_ai/training/train_mega_architecture.py:43-73`.
- 관찰한 사실: 4frame 도입과 학습기록은 있으나 같은 태스크·시드의1/2/4frame 재학습 비교 없음. 구종 onehot 및 물리식 예상도달좌표를 정책에 제공. 규칙 기준선도 이번 일부 사례에서 접촉한다.
- 확인이 필요한 이유: 시계열 기억이 성과 원인인지, 규칙/탐색 대비 개선이 있는지, 이미 제공된 특징이 효과를 설명하는지 분리되지 않는다. 시뮬레이터 상태 사용 자체는 데이터 누수가 아님.
- 영향을 받는 결과·주장: 스핀 ‘추론’ 메커니즘, 헛스윙 감소, 강화학습 필요성.
- 최소 재현 방법: 이번 기준선은 파이프라인 단서. 정식 확인은 동일 예산/분포로 학습한 구조별 정책과 고정된 평가 사례를 비교해야 함.
- 구체적인 보완 행동: 필요한 질문 한 개만 선택해 규칙·작은 매개변수 탐색·PPO, 또는1/4frame을 비교. 제거된 관측/보조의 평가시 민감도와 재학습 ablation을 구분.
- 보완 후 통과 기준: 사전 정의 지표·동일 평가집합·학습시드 반복·개별 케이스 결과와 불확실성 보고.
- 아직 모르는 부분: RL의 실제 순효과, 각 구성의 기여. ‘대안이 가능하므로 RL은 오류’라고 결론내리지 않는다.

### F15. 재현 자산과 실행 식별 정보를 패키징할 필요가 있다

- 분류: **④ 선택적 개선**(배포 재현성 목표에서는 필요한 보완).
- 우선순위: **이후 개선**. 로컬 핵심 물리 검증은 가능.
- 근거 수준: 정적 확인 + 감사 실행 경로 실패/해결 확인.
- 위치: `.gitignore:16-23`; `shared_assets/h1_baseball_match.xml:62-65`; `requirements.txt:1-11`; `run_demo.sh:6-15`.
- 관찰한 사실: 경기 텍스처가 ignored data 경로를 참조하며 파일은 로컬에 존재. 버전은 하한/무핀 지정, 실패에도 셸이 완료 문구를 출력. best 파일명 중 일부는 마지막 저장 모델이다. 원격 URL 설정에는 자격정보가 포함되어 있어 감사 산출물에는 값을 기록하지 않았다.
- 도움이 되는 이유: 다른 Mac/새 checkout에서 필요한 자산과 버전을 빠짐없이 재구성하고 실패를 완료로 오인하지 않게 한다.
- 영향을 받는 결과·주장: out-of-box reproducibility, 단일명령 데모. 로컬 모델 생성 성공 자체와는 별개.
- 최소 재현 방법: `git ls-files data/textures`, XML 경로, `pip_freeze.txt`, 셸 exit 처리 비교. 이번 감사는 공개 clean clone 전체 실행을 하지 않았다.
- 구체적인 보완 행동: 작은 허용 에셋·환경 lock·실행 manifest 포함, 단계별 exit 검사/출력분리. 원격 URL 자격정보는 별도 안전한 인증관리로 옮기고 공유 전 점검.
- 보완 후 통과 기준: 새 격리 checkout에서 명시한 자산·환경만으로 smoke 통과, 실패 단계는 nonzero 종료, 로그/URL에 자격정보 없음.
- 아직 모르는 부분: M4/다른MuJoCo 버전에서 결과 차이, 외부 asset 이용조건. 이번에는 원격설정·의존성·원본을 변경하지 않았다.

## 6. 재현 실험과 기준선 결과

### 6.1 실행 방법·식별·비용

주 실행 명령은 저장소 루트에서 `python3 _audit/20260926_013033/scripts/run_bounded.py MODE [새_로그접미사]`다. 이 실행기는 절대 경로의 기존 `.venv/bin/python -B`로 감사 스크립트를 실행하고 cwd를 감사 디렉터리로 바꾼다. 정확한 명령 argv·cwd·환경변수·소요시간·returncode는 `logs/commands.jsonl`에 있다. 전체 환경은 `pip_freeze.txt`, 원본 식별은 `initial_manifest.json`, 가중치/정규화 hash는 `runtime_results.jsonl` 및 `physics_*.jsonl`이다.

`shared_assets`, `checkpoints`, `data/textures`는 원본을 읽는 감사용 링크이며 원본에 저장하지 않았다. 기존 소스 main·학습 루프는 실행하지 않았다. root 실행기는 각 프로세스180초 timeout, 개별 rollout100/460 step 상한. 보조 물리검사는120초 alarm와 태스크별45/155/305/205 step 상한을 사용했다(tee 첫 실행은 alarm 추가 전 유한 step 상한으로1.90초 종료). 원본 stochastic pitcher는 seed를 고정하되 원래 `deterministic=False` 설정을 유지했다.

**프로세스 returncode0은 모든 검사가 통과했다는 뜻이 아니다.** 감사 스크립트는 한 검사 실패 뒤 독립 검사를 계속하도록 예외를 `kind=error`로 저장한다. 아래 실패 항목과 JSON 원기록이 판정 근거다.

| 실행 명령·검사 | 코드·가중치·설정 | 기대 결과 | 실제 결과 / 로그 | 해석·한계 |
|---|---|---|---|---|
| `run_bounded.py metadata` | 현재24 ZIP/16pkl,기존환경 | 파일identity·version 확인 | 성공,1.47s; `metadata_stdout.txt` | 존재·훈련시점 metadata이지 성능 아님 |
| `run_bounded.py smoke` | 4개 단독환경+Match,0action,합성분기 | 생성/reset/step/종료후reset·finite | 단독성공,Match텍스처경로실패; `smoke_stdout.txt` | audit cwd 경로실패를 보존 |
| `run_bounded.py smoke _assets_resolved` | 텍스처 링크 연결,나머지동일 | 위독립검사/합성contact·관측순서 | 성공,1.80s; `smoke_assets_resolved_stdout.txt` | 원본 수정없음. 합성성공은 정책성과 제외 |
| `run_bounded.py baseline` | soft/machine50/machine80/breaking/mega_pitcher,10cases×4modes | headless비교,가중치추론 | 200rollout,3.75s; `baseline_stdout.txt` | 초기80deep은 잘못된norm짝 사용. 아래정정;실행기록삭제안함 |
| `run_bounded.py match` | demo mocap pair,eval horizon | 30경기시도 | 텍스처 경로실패; `match_stdout.txt` | 재시도전 미완료 |
| `run_bounded.py match _assets_resolved` | 같은mocap pair,wind/target/구종seed100~109 | no-trigger/random/PPO 각10 | 30rollout,2.82s; `match_assets_resolved_stdout.txt` | 정상유한추론,세mode모두contact0.입력계약결함은그대로 |
| `run_bounded.py followup` | 올바른80deep norm,old투수pair,합성보상/종료,mega48D | 짝정정·결함재현·48D추론 | 2.78s; `followup_stdout.txt` | old13Dnorm실패는예상차단,나머지해당기록확인 |
| `../../.venv/bin/python -B scripts/additional_contracts.py` (감사cwd,실제실행기는절대경로) | currentAPI·umpire·mocap norm | 경계·reset입력계약 | 2.13s; `additional_contracts_stdout.txt` | 문자열관측/선분누락/Box범위이탈확인 |
| `../../.venv/bin/python -B scripts/physics_probe.py --task tee` (감사cwd) | tee_final,seed0~4,4modes | 생성/정책/비교 | 20rollout; `physics_tee.jsonl` | action0는자동스윙높이중간값 |
| 같은명령 `--task catcher` | catcher best/norm,3modes | 접촉·이동·종료 | 15rollout; `physics_catcher.jsonl` | 전부성공0;실제접촉합성도실패 |
| 같은명령 `--task runner` | runner best/norm,3modes | 주자목표·종료 | 15rollout; `physics_runner.jsonl` | 모두timeout;초기상태난수없어5독립사례아님 |
| 같은명령 `--task fielder` | fielder best/norm,3modes | 정상비행/포구 | 15rollout; `physics_fielder.jsonl`+stderr | policy5/5이나모두QACC불안정 |
| 같은명령 `--task cognitive` | 원본RGB생성자 | 생성후3step | CoreGraphics오류exit1; `physics_cognitive.stderr.txt` | 환경렌더제약 |
| `physics_contracts.py` / `fielder_trace.py` (같은Python,cwd) | 감사인스턴스/seed21단일substep·seed0추적 | ID·미사용action·시간연속성 | `physics_contracts*.jsonl`, `fielder_trace.jsonl` | renderer stub·weld조건변화·synthetic별도표시 |
| `rules_and_checkpoint_probe.py` / `vecenv_contract_probe.py` | 순수룰/ZIP JSON 및 합성one-step Gym | foul·54outs·SB3계약 | 같은이름JSON;약.2s/1.2s | 54outs→Top10.통합MuJoCo9이닝실행아님 |

위 보조 스크립트들의 전체 환경변수·명령·상한은 `notes/physics_tasks.md` 5절, `notes/training_eval.md` 실행기록에도 있다. 기존 로그의 npz/TB 파싱 명령·수치·원경로는 `notes/claims_history.md`에 보존했다. 단독 XML의 dt=.005s, 실제제어주기와 예산은3절 표와 각model JSON을 따른다.

### 6.2 같은 초기 사례에서의 작은 기준선

root 비교는 seed100~109를 매 episode NumPy/Torch에 고정하고 무작위 action은 별도 generator(seed+9000)를 사용했다. reset(seed)만으로 재현되지 않는 결함을 우회했다. 초기 관측을 episode별 저장했다. 정책은 CPU deterministic 추론, 정규화 training=False/norm_reward=False. Match 상대투수만 원본 stochastic 설정을 유지하며 같은 Torch seed로 난수열을 맞췄다. 고정된 분석용 사례이며 통계적 holdout 또는 훈련독립성이 입증된 사례는 아니다.

| 태스크 / 성공 정의 | 유효 고정 명령 | 무작위 | 미튜닝 규칙 | 기존 PPO | 사례수 |
|---|---:|---:|---:|---:|---|
| SoftToss / contact | trigger=-1:0/10 |0/10|3/10|6/10|각10,동일초기조건|
| Machine50 / contact | trigger=-1:0/10 |0/10|3/10|5/10|각10|
| Machine80 deep / contact | trigger=-1:0/10 |0/10|3/10|**2/10**|각10,deep_norm사용|
| Breaking / contact | trigger=-1:0/10 |0/10|2/10|1/10|각10|
| Pitcher mega / target d≤.20 | midpoint:0/10 |1/10|고정최대power:0/10|10/10|각10,release자동진행|
| Tee / contact | 높이0자동스윙:4/5 |1/5|3/5|3/5|seed0~4,각5|
| Fielder / 환경catch flag | ctrl0:0/5 |1/5|—|5/5 **무효물리포함**|각5,일반포구성공률로사용불가|
| Catcher / catch | ctrl0:0/5 |0/5|—|0/5|각5,판정결함있음|
| Runner / 환경목표 | ctrl0:0/5 |0/5|—|0/5|각5,동일초기조건반복|

규칙은 Soft의time≤.125/높이정규화, Machine time≤.12/z_zone, Breaking time≤.10/z_zone/x_zone를 clip해 사용했다. 정책 전 관측에 이미 제공된 물리식 특징을 그대로 사용했으며 탐색으로 튜닝하지 않았다. Tee는 `clip((z-.8)/.15,-1,1)`. 투수는 정책이 없어도 자동 motion/release하므로 **0 벡터를 무동작으로 세지 않았다**. 수비계열 ctrl0도 중력/제약 아래 자세유지를 뜻하지 않는다.

80km/h 첫 감사 실행은 deep weight와 일반80 norm을 잘못 짝지었고 3/10으로 나왔다. 파일 참조를 재검토하여 `pitching_80kmh_deep_norm.pkl`로 다시 실행했으며 위 표는 **올바른짝2/10**만 사용한다. 최초40rollout은 provenance를 위해 남겼지만 추가 독립표본으로 합산하지 않는다. 이 차이를 정규화의 인과효과 실험으로 주장하지 않는다.

| 실제 사용한 정책 | 정규화 | 저장 num_timesteps / 비고 |
|---|---|---|
| `checkpoints/soft_toss_best_model/best_model.zip` | `soft_toss_vec_normalize.pkl` |70,000|
| `checkpoints/pitching_50kmh_best/best_model.zip` | `pitching_50kmh_vec_normalize.pkl` |50,000|
| `checkpoints/pitching_80kmh_deep_best/best_model.zip` | `pitching_80kmh_deep_norm.pkl` |130,000|
| `checkpoints/breaking_ball_best/best_model.zip` | `breaking_ball_vec_normalize.pkl` |90,000|
| `checkpoints/mega_pitcher/best_model.zip` | `mega_pitcher/vec_normalize.pkl` |1,600,000|
| `checkpoints/mocap_pitcher_best/best_model.zip` | `mocap_pitcher_vec_normalize.pkl` |56,000;경기상대|
| `checkpoints/mocap_batter_best/best_model.zip` | `mocap_batter_vec_normalize.pkl` |36,000;기본경기|
| `checkpoints/mega_batter/best_model.zip` | `mega_batter/vec_normalize.pkl`+FrameStack4 |1,920,000;한step추론만,성과평가아님|
| `checkpoints/teeball_final_model.zip` |없음|50,176;과거best를대신재현한것아님|
| `checkpoints/{fielder,catcher,runner}/best_model.zip` |각동명폴더의pkl|301,056 /106,496 /106,496|

pkl 축약경로는 모두 `checkpoints/` 기준. 정확한SHA256은 metadata/physics 로그에 있다. best라는 파일명만으로 최선선정이 보장되지는 않으며, fielder/catcher/runner와 MLB batter는 trainer가 마지막 상태를 그 이름으로 저장한다.

### 6.3 경기 결과·실패 종류·판정 검사

대표 데모와 같은 mocap pair/정규화/평가 horizon을 사용하되 렌더와 autoreset 없이 실제 끝상태를 기록했다. 이것은 영상평가기의 결과를 그대로 신뢰한 집계가 아니다.

| 타자 명령 | contact | 단일투구 outcome | 평균 원보상 |
|---|---:|---|---:|
| no-trigger |0/10|BALL8,CALLED STRIKE2|90.0|
| random |0/10|swing miss7,BALL3|-15.0|
| PPO |0/10|BALL6,swing miss3,CALLED STRIKE1|50.0|

이 결과는 현재 계약 결함이 있는 경기에서 ‘볼을 지켜보는 보상’만으로 양의 평균보상을 얻을 수 있음을 보여 준다. plate discipline을 보상하려는 설계 자체는 오류가 아니지만 이 보상을 타격성공의 대용으로 쓰면 안 된다. 어떤 정책도 이10사례에서 contact하지 않았다는 사실이 모든가능조건의0% 성능을 의미하지 않는다. 필드명 ‘STRIKE OUT’/‘Walk’는 환경이 한 공에 붙인 라벨이며 실제3strike/4ball 타석을 수행하지 않았다.

단독 mega 투수는10/10 STRIKE, 무작위는 STRIKE1/BALL3/WILD PITCH5/시간초과1, 중간고정값은 BALL6/WILD PITCH4, 최대power고정은 BALL10이다. 타격 환경의 접촉하지 못한 episode는 스윙 완료 또는 공 통과/지면 등의 환경 종료이며 로그의 final ball·steps·terminated/truncated로 구분 범위를 남겼다. 성공하지 못한 모든 원인을 하나의 ‘정책 실패’로 진단한 것은 아니다.

Catcher 기존정책은5회 모두150step(7.5s) timeout, Runner는300step(15s) timeout이며 실제 주자 최종목표거리8.9829m가 기록됐다. Runner5회는 초기상태가 같은 반복이다. Fielder는finite라도 시간 되감김·warning이 있으므로 별도 invalid physical episode로 분류해야 한다.

판정 단위검사에서는 투수 STRIKE/BALL/지면실패/timeout 각각의 branch를 확인했다. 합성 투수 성공은 release_speed=0이어도 목표조건을 만들면 성공 보상이 나오는 것을 확인한 것으로, 자연정책이 이를 달성/악용했다는 뜻이 아니다. 배트와 공을 겹친 contact 생성, catcher 실제glove 접촉, runner 공만목표, foul 카운트, 심판선분, forced contact 종료는 모두 **합성 검사이며 위 정책 성공횟수에 포함하지 않았다**.

### 6.4 기존 결과를 어디까지 재현했는가

- **대규모 학습 수행:** 기존TB/ZIP로 뒷받침. mega 투수 NPZ는320k 간격6평가×각5episode, success수3,3,4,4,5,5. mega 타자는같은6×5 구조이나success/contact필드 없음. 최종정책의30회성공률처럼 합산하면 안 됨.
- **과거70/60/66.7% 및15회100%/84.4km/h:** 정확재현 완료 아님. 현재같은파일이름의정책을새사례에넣어측정한결과는 위 표로 분리. old투수는13D계약 때문에차단,원13D source는확인못함. 다른 태스크도원시드/소스/정규화저장시점 불명.
- **외야5/5:** 환경flag5/5는 새로 관찰했지만 정상물리조건이 무너져 성과증명으로 인정하지 않음.
- **9이닝:** 기존`runs/sim_9_inning.log`에완주가있고순수상태머신54아웃합성검사도Top10으로전환. 통합정책9이닝이나모든야구규칙의정확성을입증하지 않음.
- **수치안정성:** root 소프트/머신/변화구/투수/경기의 저장관측은검사구간finite. Fielder처럼finite인채자동reset이가능하므로finite만으로물리정상판정을하지않았다. 장기안정성은이번범위밖이다.

## 7. 재사용 가능한 자산과 재설계가 필요한 부분

| 선택 | 현재 근거로 판단 | 보존/변경 범위 | 결정을 가르는 최소 검증 |
|---|---|---|---|
| A. 구조유지+평가/문서만 | 부족 | 정직한 설명은 필요하지만 잘못된 관측·판정·수치 reset이 남음 | F01~05를 설명변경만으로 해결할 수 없음 |
| **B. 핵심 환경·제어·평가 일부수정** | **제한된 투타 매개변수 태스크에 우선 권고** | 키프레임·PPO·모델 재사용. 관측계약·단일물리·판정/평가·run bundle 수정. 수비/주루는 별도 결함 처리 전 제외 | 단독투수와 하나의타격태스크를 freeze하고 기준선과 동일사례 평가 |
| C. 자산만 재사용·태스크재설계 | 전신 로봇 제어가 목적이면 타당 | mesh/경기장/일부 유틸 보존. free base,실제 actuator/PD,접촉/보상/관측/실패조건 새설계. 기존정책 직접이식 가정 불가 | 공 없이 균형 또는 고정base 팔 한동작 등 단일역학 태스크 검증 |
| D. 보관후 독립 새프로젝트 | 현재 정보만으로 필수 판단 유보 | provenance를 남긴 보관은 유용. 새repo 자체가 잘못된 문제정의/지표를 고쳐주지는 않음 | B의 명확한제한목표와 사용자의다음목표가 맞지않고 자산재사용 이득도 작을 때 선택 |

재사용할 만한 것은 H1 mesh·모델 조립 경험, 시각적 경기장/카메라 자산, state-based Gym/PPO 실험 뼈대, 키프레임 파라미터화, 학습·로그·영상 생성 도구다. 기존 weight는 버전 고정된 비교대상으로 보존한다. 골반 고정·slide 기반 모델은 그 태스크 범위를 명시하면 재사용할 수 있다. 텍스처·mesh의 원출처/라이선스는 이번 감사에서 법적 검증하지 않았다.

재설계가 필요한 것은 연구질문과 성공사건이다. ‘전신 균형을 학습하는 야구 로봇’이 목표라면 기존 고정골반/qpos주입 구조는 코드정리로 해결되지 않는다. ‘타격 동작이 주어졌을 때 언제·어디를 조정하는가’가 목표라면 현재 구조를 줄이고 계약과 지표를 고쳐 계속할 수 있다. RL 대신 규칙이 비슷하게 작동해도 실패한 프로젝트로 결론낼 필요는 없다. 어떤 조건에서 학습의 이점이 있는지를 실험 질문으로 삼으면 된다.

M1에서 이번 작은 headless 검증은 수초~수십초의 프로세스 단위로 가능했다. 이것을 전신 수백만 step의 시간/비용 추정으로 확장하지 않는다. M4의 속도 향상률이나 학습완료 일정을 측정 없이 제시하지 않는다.

## 8. 포트폴리오에서 현재 가능한 표현과 근거가 부족한 표현

| 현재 가능한 표현 예시 | 붙여야 하는 근거·제한 |
|---|---|
| “MuJoCo에서 H1 형태 모델과 수작업 키프레임을 결합하고, PPO로 투구 릴리스·조준·파워와 타격 타이밍·높이를 선택하는 환경을 구현했다.” | qpos/ball속도 주입,고정골반이라는 제약도 함께 설명 |
| “단독 투수·타자 환경에서 PPO와 정규화를 사용해 학습했고, 4프레임 입력을 갖는 별도 타자 정책까지 실험했다.” | 실제체크포인트/TB. 4프레임의 효과가 검증됐다는 표현은 제외 |
| “현행 mega 투수 체크포인트는 감사의 고정10사례에서 코드상 목표반경0.20m를10회 만족했다.” | 날짜·commit·weight/norm hash·사례seed·물리조건 표시.일반성능100% 주장 금지 |
| “감사를 통해 동일차원 관측순서 불일치와 종료후상태 판정 문제, 수치초기화 후 포구집계를 찾아 최소재현을 남겼다.” | 이번감사 결과. 수정·통과까지 완료했다고 쓰면 안 됨 |
| “투타 시연, 수비/주자 환경, 간단한 규칙·9이닝 상태머신을 각각 구성했다.” | 하나의 정책경기로 완전히연결되었다는 의미는 아님 |

근거가 부족한 예시는 “H1이 전신 균형을 유지하며 투타 동작을 학습했다”, “실제 오타니 광학식 MoCap을 이용한 모방학습을 검증했다”, “FrameStack으로 헛스윙을 크게 줄였다”, “외야 포구100%·도루와9이닝 자율경기를 완성했다”, “실물로 이전가능한 물리정확성과 정격토크를 입증했다”다. 원자료·정상물리·통제비교를 확보하기 전에는 쓰지 않는다. 당시 개인 기여·개발 의도·이해 수준은 이 저장소 감사만으로 평가하지 않았다.

## 9. 다음 행동 최대 3개

1. **가장 먼저: 한 개의 제한된 태스크와 평가 계약을 고정한다.** 지금은 단독 투수·경기·중계의 관측과 성공 조건이 다르다. 선행 조건은 다음 목표가 매개변수 의사결정인지 전신 제어인지 정하는 것이다. 산출물은 `task_spec`(허용 관측·동작·물리 보조·성공·실패), 평가 사례 파일, checkpoint/norm/XML/source 해시 manifest다. 같은 상태가 관련 경로에서 같은 열·단위·사건으로 기록되고, 문서와 코드가 같은 제한 범위를 표현하면 완료다.
2. **선택한 태스크의 차단 결함을 최소 수정하고 동일 사례로 평가한다.** 관측 순서·autoreset·판정 오류가 남아 있으면 학습량을 늘려도 결과를 해석하기 어렵다. 선행 조건은 1번의 계약과 원본 보존이다. 별도 수정 브랜치의 작은 diff, 발견별 재현 검사, 고정·규칙·무작위·PPO 비교 로그를 남긴다. 수치 reset 없음, 정규화 통계 불변, 성공 사건 일치, 정상 종료 및 사례별 원결과 저장이 완료 기준이다. 기존 정책을 고친 환경에 넣는 검사는 우선 조건 변화에 대한 민감도 검사이며, 재학습한 정책의 공정한 효과 비교와 구분한다.
3. **결과를 바탕으로 B와 C를 결정하고 주장·자료를 정리한다.** RL의 추가 가치와 다음에 증명하려는 역량을 구분하기 위해 필요하다. 선행 조건은 1~2번의 완료다. 검증 가능한 결과만 담은 README·실험표, 기존 프로젝트 보관본, 필요하다면 전신 단일 태스크 설계안을 만든다. 모든 숫자에 분모·조건·식별 정보가 있고, 입증하지 않은 성과가 계획 또는 미검증으로 표시되면 완료다. 전신 제어가 목표라면 기존 지표 개선을 계속하기보다 단일 역학 태스크의 통과 조건으로 전환한다.

---

이 보고서는 코드·로그·제한된 재실행에 대한 감사다. 보고서 작성, 체크포인트 로드, 작은 표본의 성공 자체가 프로젝트 전체의 타당성 검증 완료를 뜻하지 않는다.
