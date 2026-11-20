# 문서·실험 이력 독립 조사 노트

검사 기준: 로컬 `main`, `f63dc977` 계열 HEAD. 이 노트의 저장소 상대경로는 모두 `/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/` 아래다. 원본·체크포인트·기존 로그를 수정하지 않고 문서, 코드, Git 이력과 기존 로그를 읽었다. 정책의 신규 실행 성능은 이 노트에서 측정하지 않았다. 원본 스크립트는 실행하지 않았다.

## 1. 먼저 구분해야 할 결론

- **200만 스텝 규모 학습의 실행 기록은 존재한다.** `train_mega_architecture.py`의 설정만 있는 것이 아니라, 로컬 TensorBoard의 마지막 기록 step이 투수 2,015,232 / 타자 2,031,616이다. 이를 '학습하지 않았다'고 말할 근거는 없다.
- **기존 성공률을 현재 전체 시스템의 성능으로 묶어 말할 수 없다.** 티볼, 소프트토스, 피칭 머신, 구버전 투수, MoCap 이름 투수, mega 투수는 서로 다른 경로이고 최신 데모가 mega 가중치를 쓰지 않는다. 대부분 수치는 원래 평가 케이스·시드·소스 해시와 연결되지 않는다.
- **문서와 현재 코드 사이에 명시적인 불일치가 있다.** 티볼 행동 차원(문서 2D, 현재 1D 자동 스윙), 동일 영상의 태스크 분류(피칭 머신 타자 vs 휴머노이드 투수), LSTM 표기(실제 MlpPolicy), 투수 학습률(문서 5e-4, 코드·로그 3e-4), 완전한 야구 규칙 주장(FOUL이 볼카운트를 초기화) 등이 해당한다.
- **발 들림 감소를 달성했다는 수치 주장은 현재 조사 범위에서 찾지 못했다.** 이를 사용자 예시로부터 만들어 프로젝트 주장으로 기재하면 안 된다. `docs/index.html:1151`에는 별개의 '이족 균형/ZMP에 90% 이상 연산량 낭비' 주장이 있으나 그 측정 자료를 찾지 못했다.
- **기존 자료만으로 당시 개발자의 의도·이해 수준이나 모든 실험 과정의 타당성을 확정할 수 없다.** 반복 실험 로그와 패치 이력은 존재하지만 통제 실험의 인과 비교는 대부분 재구성 불가능하다.

## 2. 현재·과거 경로 및 주장 대응

| 기능·주장 | 실제 진입점 / 연결 | 사용 상태 | 확인 근거와 해석 |
|---|---|---|---|
| README 기본 중계 데모 | `run_demo.sh:6` → `cognitive_ai/evaluation/simulate_full_match.py:10,15-28` → `train_mlb_batter.BatterMatchTrainingEnv`, `mocap_pitcher_best`, `mocap_batter_best`와 각 VecNormalize | 기본 데모 | 현재 README는 mega/FrameStack을 대표 특징으로 소개하지만 기본 데모 가중치는 mocap 계열이다. |
| 9이닝 | `run_demo.sh:12` → `simulate_9_innings.py:5,14-27` → `BaseballGameState` | 별도 텍스트 시연 | 랜덤 결과를 입력하며 MuJoCo/PPO 정책과 연결되지 않는다. `runs/sim_9_inning.log:1102-1105`에는 Top10 도달 및 140-160 최종 점수 기록이 있어, 상태 머신이 종료까지 실행된 과거 기록은 있다. |
| 도루 | `run_demo.sh:9` → `evaluate_base_stealing.py` | 기본 데모의 별도 단계 | 9이닝 게임·투타 중계와 같은 환경으로 통합된 경기라는 뜻은 아니다. 세부 물리·정책 경로는 주 감사자 조사와 결합할 것. |
| 200만 mega 훈련 | `train_mega_architecture.py:43-102` | 독립 훈련 진입점 | 16 환경, `VecFrameStack(n_stack=4)` 타자, MlpPolicy 두 역할. 2M 규모 TensorBoard 기록 실제 존재. 기본 중계 경로가 이를 로드하지 않음. |
| 적대적 자기대전 | `adversarial_match_env.py:9-68` | 미완성 구조 | `:42` 자체 주석이 stub, `:46-50` 타자 action zero와 `pass`; `rg`로 조사한 cognitive_ai Python에서 이 클래스의 외부 사용처 없음. `docs/index.html:1193`은 '초석 마련'이라고 한정하므로 완료된 self-play 실험을 주장했다고 일괄 해석하면 안 된다. 도입부 `:688`의 광범위한 서술과 구분 필요. |
| 티볼 90% | `video_evaluator.py:35-126` → `TeeBallEnv`, `teeball_best_model` | 과거 개별 실험 | 문서 `EXPERIMENT_LOG.md:9-11`, `VIDEO_CATALOG.md:7`. evaluator 기본 3회, main은 5회(:135), 90%의 분모·별도 실행 명령은 미확인. |
| 소프트토스 70% | `eval_normalized.py:13-30,46-108` → `SoftTossEnv`, `soft_toss_best_model`, normalize | 과거 개별 실험 | 기본 10회, `ep_rew>50` 또는 step reward>50으로 hit 판정. 문서 70%를 곧 7/10 실제 로그라고 확정하지 말 것(기본값과 실제 실행은 다름). |
| 피칭 머신 60% | `eval_pitching_machine.py:11,13-34,100-109` → `PitchingMachineEnv` | 과거 개별 실험 | 기본 10회, 속도별 checkpoint와 normalize. 문서상의 가중치 별칭 `fast_pitching_best`와 실제 경로가 다르다. |
| 변화구 66.7% | `eval_breaking_ball.py:13-30,41-65,100-105` → `BreakingBallEnv` | 과거 개별 실험 | `EXPERIMENT_LOG.md:26`에 **10/15** 분모·분자 명시. 코드 기본15. 시드·케이스별 판정 원로그 연결은 미확인. |
| 투수 100%, 84.4km/h | `eval_pitcher.py:13-30,77-104` → `PitcherEnv`, `pitcher_best`, normalize | 과거 개별 실험 | `EXPERIMENT_LOG.md:33`은 15회라고 명시. 성공 조건은 `reached_plate && min_dist<=0.20`(:81-82), 평균 구속은 모든 15회 final_speed 평균(:88,100-104). 현재 PitcherEnv/가중치 계약은 주 감사자 실행과 결합 필요. |
| 외야 포구 5/5 | `evaluate_fielder.py:14-19,33-56,72` → `FielderEnv` | 개별 수비 평가 | 코드 기본5회이며 `info.catch` 카운트. FielderEnv:125-139의 catch는 glove-ball site 거리<0.25m이며, 공을 붙잡아 유지하는 물리적 포구 성공 기준은 아니다. |
| 밸런싱 보상 | `archive/humanoid/envs/atlas_baseball_env.py:163-176` | archive Atlas 실험 | pelvis world-z가0.95m에 가까울수록 보상. 발 높이·접촉·동적 회복 지표가 아니며 현재 H1 데모와 연결 없음. |

## 3. 프로젝트에 실제 존재하는 주장과 증거

| 주장 위치 | 실제 주장 | 확인 상태 / 설명 가능한 범위 | 더 필요한 것 |
|---|---|---|---|
| `README.md:5` | fully automated, physics-accurate match, MoCap, 9이닝 | 다수 하위 기능 구현과 별도 데모는 존재. 통합된 물리 기반9이닝 실험으로 확인되지 않음 | 경기 이벤트를 실제 환경에서 상태 머신으로 전달하는 경로, 모든 이닝의 실행 기록 |
| `README.md:25` | 수백만 스텝 PPO, FrameStack으로 가속도·스핀 추적, 투수 LR annealing | 2M 학습 기록·stack·schedule은 확인. 스핀을 내부 추론한다는 메커니즘·성능 효과는 미검증 | 같은 조건의1/2/4 frame 재학습 비교·held-out 구종/케이스 |
| `docs/PAPER.md:46` | FrameStack(4) LSTM | 현재 mega는 PPO MlpPolicy(`train_mega_architecture.py:66,94`). 코드 계약과 표기 불일치 | LSTM 표기 수정 또는 실제 recurrent 구현·실험 근거 |
| `docs/PAPER.md:104`, `docs/index.html:1192` | 투수 LR 5e-4부터0 | 코드 :96=3e-4; 기존TB도3e-4 계열. 문서와 불일치 | 역할별 설정값 명시 |
| `docs/PAPER.md:131` | 2M 후 중심 오차0.22m 이내 | 기존 mega 투수 내부 성공로그 확인; npz에는 raw 좌표·오차 없음. 현재 기준은0.20m이므로0.22m 수치 직접 대응 미확인 | 좌표·거리·통과시각 raw기록, 통계 산식·분모 |
| `docs/PAPER.md:132` | FrameStack 도입 후 헛스윙률 대폭 감소 | 신규 구조와 학습기록만 확인, ablation 없음. 문서 :192도비교를 향후 과제로 명시 | 단일 요소를 바꾼 재학습 비교 |
| `docs/index.html:1419` | 직구80% 이상, 변화구 헛스윙90% 이상 | 문서 수치만 확인. 평가 cases·분모·source/checkpoint 연결 미확인 | 원 실험 기록 또는 새 독립 검증 |
| `docs/index.html:1122` | 실제 오타니3D 광학식 MoCap 데이터를19관절에 retarget | 현재는 하드코딩6개 pose (`pitcher_env.py:57-67`, patch:16-27). 광학식 원자료·capture 출처·retarget pipeline 없음 | 데이터 출처·허가·raw motion과 변환 코드. 당시 데이터가 전혀 없었다는 단정은 불가 |
| `docs/index.html:1151` | 이족 균형/ZMP 유지에90% 이상 연산량 낭비 | 프로파일링 근거, 당시 ZMP 코드·하드웨어·비교분모 미확인 | 프로파일 trace, 측정 구간/대상 |
| `docs/index.html:1269` | 1.35배 적용으로 MLB 평균140~160km/h, 120m 이상 | 문서·패치 문자열에는 있으나 현행 실행 경로에 적용 없음. `scripts/patches/patch_physics_full.py:47`의 문자열 수정안에만 `*=1.35`가 있으며 현재 `BaseballMatchEnv`의 접촉 분기 `:268-272`는 flag와 속도만 기록한다. 주 감사자의 `logs/source_history_contracts.json`에서도 검사한 과거 세 snapshot에 적용 코드가 없었다. | 구현 존재 여부부터 정정하고, 비거리 수치를 주장하려면 해당 실행 버전·입력·출력과 접촉 모델 검증 기록 연결 |
| `docs/PAPER.md:133` | 외야5/5 포구·주자30m 이동 | 평가 루프·판정 기준 존재.5/5 표본은 넓은 분포의100% 일반화 근거가 아님 | 케이스별 raw거리·capture/retention 정의·시드 |
| `docs/PAPER.md:134` | run_demo 단일명령으로세단계 결함 없이 동작 | script는실패해도최종완료문구 출력; 현재 실행 여부는주 감사자 검증과 결합 | stage returncode 검증·독립로컬실행 |
| `docs/index.html:1549` | 9이닝이야구규칙에따라오차없이완결 | 기존완주로그는있으나FOUL count실제오류의기록도같이있음 | 아래CH-04 재현과회귀검증 |
| `docs/VIDEO_CATALOG.md:9` vs `docs/index.html:1610-1614` | 동일phase_2_2_pitching_80kmh.mp4를각각피칭머신타자60% / 휴머노이드투수제구93.3%로분류 | 확정문서내부불일치. rename_videos.py:13 원명pitching_80kmh_eval→현재명; eval_pitching_machine importsPitchingMachineEnv:11 | 영상-실험-가중치일대일manifest |
| `docs/PAPER.md:145-147` | 전문가3인평가8.5/7.5/7.0 | 개인신원·검토일·원문등독립검토근거없음.저자가실제로검토받지않았다고단정할수없으나외부검증자료로사용불가 | 검토출처또는자가검토/가상관점명시 |

### 균형·발 들림에 대한 조사 범위

`cognitive_ai`, `archive`의 Python과현재문서를 `foot`, `feet`, `foot_height`, `foot_lift`, `balance`, `균형`, `발.?들림` 등으로검색했다. 현재H1 경로에서발높이감소율·균형회복성공률을측정·보고하는파일은확인하지못했다. 문서의 균형관련 기술은 (a)이족수비에대한계산부담주장, (b)향후ZMP/Centroidal계획, (c)초기전신비전에대한회고다. **사용자가 예시로 든 발 들림 성과를 프로젝트가 주장했다고 적으면 안 된다.**

## 4. 기존 결과 로그를 실제로 읽은 결과

읽기 전용 파서 실행환경: 기존 `.venv/bin/python`, Python3.11.5, NumPy2.4.6, 설치된TensorBoard EventAccumulator. `np.load(..., allow_pickle=False)`로배열만읽었다. 이는정책을새로실행한결과가아니다.

### 4.1 mega 기록

`checkpoints/mega_pitcher/logs/evaluations.npz`:

| 학습 step | 평가 ep | success 수 | 저장 평균 reward | ep lengths |
|---:|---:|---:|---:|---|
|320000|5|3|5.6825727701|28,28,24,31,28|
|640000|5|3|5.8341233134|28,25,26,26,31|
|960000|5|4|6.3797015548|31,31,26,26,31|
|1280000|5|4|5.8586770058|31,31,26,26,31|
|1600000|5|5|7.2036953926|31,31,26,27,31|
|1920000|5|5|6.6084367752|31,31,27,31,31|

`checkpoints/mega_batter/logs/evaluations.npz`:

| 학습 step | 평가 ep | 저장 평균 reward | ep lengths |
|---:|---:|---:|---|
|320000|5|3.7060584545|40,34,64,45,36|
|640000|5|5.0637403488|53,33,51,32,42|
|960000|5|5.1430633545|48,32,31,39,60|
|1280000|5|3.0059762955|42,64,38,70,39|
|1600000|5|3.0894288063|70,44,70,47,52|
|1920000|5|5.2736100197|43,70,32,70,42|

타자npz에는success/contact/outcome이없다. reward만으로hit/walk/miss분해불가. 투수의후반5/5는검사한내부평가5회에대한기록이고, 문서의15회84.4km/h실험과다른실험이다. 여러checkpoint평가를합쳐단일최종정책성공률로보고하면안된다.

TensorBoard:

- `checkpoints/mega_pitcher/tb_logs/PPO_1/events.out.tfevents.1788274612.man-ui-MacBookPro.local.80228.0`: 마지막학습태그step2,015,232. LR 첫기록step32,768에서0.0002975424, 마지막1.728e-7. `eval/success_rate` 태그존재.
- `checkpoints/mega_batter/tb_logs/PPO_1/events.out.tfevents.1788274863.man-ui-MacBookPro.local.80228.1`: 마지막학습태그step2,031,616. LR 첫기록step65,536에서0.00049180799, 마지막2.88e-7. success/contact태그없음.
- 두evalnpz의평가간격320,000은 `EvalCallback(eval_freq=20000)` ×16환경과대응한다(`train_mega_architecture.py:48-64,81-92`).
- 해당평가환경은 `VecNormalize(... norm_reward=True)`로생성하며 `training=False` 설정이없다(:55-57,:85-86). Monitor도없다. 따라서평가reward는물리적원보상과동일하지않고평가중통계가갱신되는설정이다. best는이평균reward로선택된다. 시점별reward크기를실제태스크성과로직접비교하지말아야한다.
- 기록이source해시·XML해시·seed목록·checkpoint해시를내장하지않아, 이훈련이현재와완전히동일한환경에서이루어졌는지는확정할수없다. 체크포인트메타데이터는주감사자별도조사.

### 4.2 티볼·소프트토스 기록

- `runs/teeball_eval/evaluations.npz`: timestep2k~50k의25회×5ep, reward모두-10.0, episode length모두100. 그러나 `runs/teeball_tensorboard/PPO_1/...65853.0`에는마지막평가평균reward100.0/length53.2가기록되어있고, `PPO_2/...66220.0`는모든evalreward-10이다. 서로다른실행기록이있다. 현재TeeBallEnv의max_steps=40(:55)와저장length100도다르다. **현재npz만보고과거90%가거짓이라고결론낼수없고, 기존원로그가현재환경·정책과동일하다고볼수도없다.**
- `train_teeball.py:32-35`가eval출력경로를고정하므로반복실행시동일npz/best경로가사용된다. 매run의TB는PPO_1/PPO_2로분리되지만npz는한경로만남는구조다.
- `runs/soft_toss_eval/evaluations.npz`:2k~60k의30회×20ep, reward범위-56.108765~243.085393, length18~26. best평균reward는34k에서139.5249072, 마지막60k=113.10398945. `runs/soft_toss_tensorboard/PPO_1...PPO_5` 총5개실행기록이있다. npz의평균배열은PPO_5와대응한다. 초기PPO_1,PPO_2에서는평가reward가마지막0까지개선되었고, PPO_4에서는다른학습률5e-4와80k실행기록이있다.
- 이것은반복실험을실제로진행한증거다. 각run의전체설정·소스차이·통제변수가남아있지않아이개선이정규화한요소때문인지, 동작/보상/환경수정때문인지분리할수없다.

### 4.3 기록의버전관리·범위

- `.gitignore:16-20`은tb_logs/logs/data/runs/MUJOCO_LOG를제외하지만이미tracked인파일에는소급적용되지않는다. **`git ls-files`로확인한결과runs의tee/soft_toss npz·TensorBoard·sim_9_inning.log는tracked이다.** mega npz/TB, data/pitch_log.json, MUJOCO_LOG.TXT는같은확인에서tracked로반환되지않았다. 일반`rg --files`에안보인다는이유로파일이없다고하면안된다.
- `data/pitch_log.json`:23records, outcomes swinging_strike13/ball10. 소비코드는 `archive/legacy_scripts/simulator/dashboard.py:33`의경로참조. 현재H1성과와직접연결되지않는다.
- `MUJOCO_LOG.TXT`:읽을당시WARNING13,937건. 예시:1-29에2026-09-01 QACC NaN/Inf/huge경고. 어떤실행/버전/태스크의문제인지묶는식별정보없어현재정책에13,937건오류가난다고보고하면안된다. '이전불안정성이있었다'는회고와일치하는기록일뿐이다.
- `VIDEO_CATALOG.md:17`과 `scripts/patches/rename_videos.py:4-5`는외부 `.gemini/antigravity/brain/...`와옛절대프로젝트경로를참조한다. 외부아티팩트저장소내용은이하위조사에서열지않았다. 로컬repository내data/final_videos/frames는존재한다.

## 5. 우선순위별 발견 형식

### CH-01. 이전 실험·현재 환경·문서 수치를 연결하는 식별 정보 부족

- 분류: 확인 불가(성과재현) + 확인된문서내부불일치.
- 우선순위: **이번 단계 보완**. 특정성공률·현재코드의일반성능주장을막으며, 모든개발진행자체를막는것은아님.
- 근거 수준: 정적확인, 기존로그읽기, 문서주장.
- 위치: `docs/EXPERIMENT_LOG.md:9-33`; `docs/VIDEO_CATALOG.md:7-14`; `docs/index.html:1603-1621`; `train_teeball.py:32-35`; `train_soft_toss.py:19-24`; `TeeBallEnv:24,55,62,76`.
- 관찰한 사실: 티볼문서2D/0.001kg와현재1D/1e-6kg가다름. 옛npz episode100과현재limit40이다. 동일80kmh영상은문서마다타자와투수로분류됨. 반복train이같은best/log이름을사용한다.
- 문제가 되는 이유: 각성과가무엇을학습하고어떤조건에서측정됐는지한눈에확정되지않음. 과거성과와현재시스템수준을혼합할위험.
- 영향을 받는 결과·주장: 티볼90%, soft70%, pitching60%/93.3%, pitcher100%, 단계별개선.
- 최소 재현 방법: 위파일줄비교, `np.load(allow_pickle=False)`의shapes/lengths, git로그와rename_videos mapping확인.
- 구체적인 보완 행동: 문서수치별로원runID/소스commit/XML해시/checkpoint·normalize해시/시드·케이스집합/성공산식/분모를일대일표로복원. 못찾은수치는과거기록으로명시하고새평가와분리.
- 보완 후 통과 기준: 보고할모든수치가하나의재실행명령과immutable artifact세트에연결됨. 복원불가항목은재현미확인표기.
- 아직 모르는 부분: 원영상촬영당시명령·checkpoint버전, 일부이전소스상태.

### CH-02. 실제 광학식 MoCap·LSTM·전신 제어 설명의 근거 수준 혼재

- 분류: 확인된불일치(LSTM/키프레임폐기설명), 확인불가(원MoCap출처).
- 우선순위: **이번 단계 보완**. 광학식데이터retarget·학습한전신동작이라는포트폴리오주장을막음.
- 근거 수준: 정적확인 / 문서주장.
- 위치: `docs/index.html:1122`; `docs/PAPER.md:46,59-60,137-139`; `pitcher_env.py:57-67`; `scripts/patches/inject_mocap_pitcher.py:16-27`; `train_mega_architecture.py:53,66,94`.
- 관찰한 사실: 현재6개19관절pose상수가있고보간한다. raw광학식motion파일(.bvh/.c3d/.trc등)이나retarget단계를repository에서찾지못함. FrameStack정책은MlpPolicy.
- 문제가 되는 이유: 사람이다룬폼·정책이선택한파라미터·학습한모방행동을구별하기어려움.
- 영향을 받는 결과·주장: 오타니MoCap모방학습실효성, LSTM시간추론, 미시적관절제어RL.
- 최소 재현 방법: source의base_keyframes와PPO생성자확인,모션파일/loader검색.
- 구체적인 보완 행동: 원motion출처·변환과정이있으면자료를연결. 없으면'선수폼을참고한수작업키프레임+저차원PPO'로사실범위수정. LSTM표기정정.
- 보완 후 통과 기준: 학습된요소와설계된요소가코드·도식·문서에서동일하게설명됨.
- 아직 모르는 부분: 개발자가원자료를repository밖에서참고/처리했는지여부. 코드만으로부정하지않음.

### CH-03. mega 평가 reward가 정규화된 값이며 평가 통계 갱신이 켜져 있음

- 분류: 확인된평가설정문제.
- 우선순위: **이번 단계 보완**. rawreward곡선에기반한시점간성과비교·best선정해석을막음.
- 근거 수준: 정적확인,기존npz/TB파싱.
- 위치: `train_mega_architecture.py:55-64,85-92`; `checkpoints/mega_{pitcher,batter}/logs/evaluations.npz`.
- 관찰한 사실: 평가VecNormalize에training=False/norm_reward=False가없고Monitor도없다. 평가저장reward약3~7은원태스크보상과동일단위가아니다. best정책은해당평균으로선택한다.
- 문제가 되는 이유: 평가중변하는통계/보상스케일이점수에영향. 타자reward에는히트수와볼회피수가분리되어있지않다.
- 영향을 받는 결과·주장: mega최적모델·개선량·타자성공률해석.2M학습수행사실자체는여전히뒷받침됨.
- 최소 재현 방법: 생성자설정·실제eval npz값확인. 주감사자SB3버전내EvalCallback/VecNormalize동작확인과결합.
- 구체적인 보완 행동: 별도eval환경통계고정·원보상집계·task success/outcome저장. best시점normalize를같이저장. 기존모델을다시학습하지않고우선고정평가셋에서각checkpoint비교.
- 보완 후 통과 기준: 평가전후obs_rms/ret_rms불변, success와rawreward기록, 동일input/output계약의checkpoint-통계쌍.
- 아직 모르는 부분: 당시사용한SB3버전과현재작업공간코드동일성,기존best선정이실제성공률을얼마나바꿨는지.

### CH-04. FOUL 처리에서 기존 스트라이크·볼 카운트가 소실됨

- 분류: 확인된문제.
- 우선순위: **이번 단계 보완**. '표준야구규칙오차없는9이닝'주장을막음.
- 근거 수준: 정적확인 + 기존실행로그. 새synthetic재현은주감사자수행대상.
- 위치: `cognitive_ai/envs/baseball_game_state.py:27-31`; `runs/sim_9_inning.log:1098-1099`; `docs/index.html:1549`.
- 관찰한 사실: handle_hit진입즉시reset_count,그뒤FOUL이면strike+1. 기존로그S2B2→FOUL→S1B0.
- 문제가 되는 이유: 파울로볼카운트가소실되고2strike에서도1strike가됨. 종료확률·득점분포·타석길이가변함.
- 영향을 받는 결과·주장: 9이닝규칙정확성·scoreboard실증. 상태머신이실제로완주했다는것은부정하지않음.
- 최소 재현 방법: game.strikes=2, game.balls=3; game.handle_hit('FOUL'); 실제S1B0,일반파울기대S2B3.
- 구체적인 보완 행동: FOUL분기를reset_count앞으로이동. 0/1/2strike와볼0~3조합표확인. 사용자요청대로이번감사에서는원본수정하지않음.
- 보완 후 통과 기준: 파울은balls유지, strikes0→1/1→2/2→2. 삼진/볼넷/진루분기는기존의도대로분리검증.
- 아직 모르는 부분: 과거어떤데모가다른규칙버전을사용했는지.

### CH-05. 동일 학습환경 인스턴스를 주기 평가에도 재사용

- 분류: 정적확인된공유구조,학습영향크기는추가실험필요.
- 우선순위: **다음 티볼/soft 학습 전 보완**. 해당트레이너의새학습해석을막음.
- 근거 수준: 정적확인.
- 위치: `train_teeball.py:16-22,32-35`; `train_soft_toss.py:16-22,29-31`.
- 관찰한 사실: 같은env가PPO와EvalCallback에넘어간다. 평가reset/step이학습환경상태를변경하는공유구조다.
- 문제가 되는 이유: 평가콜백직후학습collector가보유한관측과실제환경상태의연속성이깨질수있다. 학습이항상실패했다거나과거수치가전부무효라고단정하지않는다.
- 영향을 받는 결과·주장: 해당초기트레이너의학습곡선·학습효과추정.
- 최소 재현 방법: 별도감사용fake statefulenv와실제SB3 EvalCallback으로콜백전후env상태·collector관측을비교(주감사자가필요시).
- 구체적인 보완 행동: 별도env인스턴스및고정평가시드사용. 원코드수정안만제시.
- 보완 후 통과 기준: 평가콜백실행이학습env의state/RNG를바꾸지않음.
- 아직 모르는 부분: 이전실행시점의callback주기·코드가현재와같았는지,실제성능영향.

### CH-06. 방법 선택과 성능 향상의 인과 효과는 별도 검증 필요

- 분류: 미검증가정.
- 우선순위: 이후개선; 'RL/FrameStack이필수/우월'주장전에는이번단계보완.
- 근거 수준: 문서주장 + 기록범위확인.
- 위치: `docs/PAPER.md:111,132,137,189-197`; `docs/index.html:1419-1421`; phase별training/PPO로그.
- 관찰한 사실: 반복실험은존재하나무작위/규칙/고정동작/탐색등동일조건기준선표가없다.1/2/4frame인과비교는문서자체도향후과제로둔다.
- 문제가 되는 이유: 저차원행동에서RL효과와설계된특징·모션효과를분리하지못함. 대안이있다는이유로RL사용을오류라고판정하지않음.
- 영향을 받는 결과·주장: '프레임스택때문에헛스윙대폭감소', 'RL필수성/우월성'.
- 최소 재현 방법: 같은case목록에서유효유지명령·랜덤·간단규칙·기존정책비교. 작은표본은배선/방향성확인만.
- 구체적인 보완 행동: 한개태스크로제한하고metric을고정한다. 성분기여의공정비교에는각조건재학습이필요하며평가때특징삭제만해서ablation이라고부르지않음.
- 보완 후 통과 기준: 태스크성과와실행비용을별도보고하고반복seed/test케이스로확인.
- 아직 모르는 부분: repository외비교실험이있는지.

## 6. Git 이력이 말해 주는 것과 말하지 않는 것

- `62f112b` (2026-09-01 23:24:37+09)는Phase1~7을108files/5872insertions 규모로한번에추가한다. 티볼·soft·pitcher의현재핵심구현이이때처음이력에등장한다. 세부단계별source snapshot은Git에서자동복원되지않는다.
- `a7227be` (23:42:50)의 commit 제목은 Magnus/COR 변경을 설명한다. 다만 제목과 달리 COR 1.35배가 실제 실행 코드에 반영되었다는 증거는 확인되지 않았다. `d1cfbb5`는9이닝. `58b2a58` (23:57:09)은mega training, FrameStack, LR,adversarial stub와match처리를묶어추가한다. 여러요소가같이바뀌어단일원인실험으로해석할수없다.
- `37cba3b`, `547f58a`, `ec0d5f9`, `92043ab`, `530b6ea`는문서·회고확장. `a64134d`는체크포인트/normalize추가. `48db86d`는docs이동. 현재HEAD `f63dc97`는docs asset디렉터리명변경이다. '최신문서'와'최신정책'은동일한것이아니다.
- 패치파일과실험스크립트존재는시행착오의흔적이다. 정식실험manifest가없다는이유로아무실험도안했거나당시방법을몰랐다고결론내리지않는다.

## 7. 읽기 전용 로그 파싱에 사용한 명령 요지

실행명령은다음구조의 `.venv/bin/python - <<'PY' ... PY` 였다. 파일은읽기만했으며pickle실행을허용하지않았다. 주요stdout수치는위4절에전사했다.

```python
import numpy as np
from pathlib import Path
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

paths = [
    'runs/teeball_eval/evaluations.npz',
    'runs/soft_toss_eval/evaluations.npz',
    'checkpoints/mega_pitcher/logs/evaluations.npz',
    'checkpoints/mega_batter/logs/evaluations.npz',
]
for path in paths:
    data = np.load(path, allow_pickle=False)
    print(path, data.files)
    for key in data.files:
        a = data[key]
        print(key, a.shape, a.min(), a.max())
    for i, step in enumerate(data['timesteps']):
        print(int(step), data['results'][i].mean(), data['ep_lengths'][i])
        if 'successes' in data.files:
            print(data['successes'][i])

events = list(Path('runs').glob('**/events.out.tfevents.*'))
events += list(Path('checkpoints').glob('**/events.out.tfevents.*'))
for path in sorted(events):
    ea = EventAccumulator(str(path), size_guidance={'scalars': 0}).Reload()
    print(path, ea.Tags()['scalars'])
    for key in ea.Tags()['scalars']:
        if key in ['rollout/ep_rew_mean', 'eval/mean_reward',
                   'eval/mean_ep_length', 'train/learning_rate',
                   'rollout/ep_len_mean']:
            values = ea.Scalars(key)
            print(key, len(values), values[0], values[-1])
```

기대결과: 저장된평가분모·reward·success·학습step을읽고문서와대응할수있는지확인.
실제결과: 네npz와현재runs/checkpoints의아홉TB파일읽기성공. 큰학습실행기록은확인,다수핵심수치의원케이스/소스/가중치연결은미확인.
한계: 기존파일의숫자를읽은것이지학습이나성능을새로재현한것은아니다. 상태머신과정책의새실행은주감사자의별도로그를참조해야한다.
