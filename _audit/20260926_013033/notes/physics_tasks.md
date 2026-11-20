# 물리·개별 태스크 하위 감사

작성 범위: `main` / `f63dc977`의 로컬 코드(원본 변경 없음). 모든 경로는 저장소 루트(`/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball`) 기준이다. 최종 정확한 전체 commit·초기 상태·checksum은 부모 감사 manifest를 사용한다. 이 노트는 전체 보고서의 근거 자료이며 현재 핵심 `PitcherEnv`·`BaseballMatchEnv`는 다른 작업에서 검사했다.

## 1. 요약

- 개별 타격 환경은 전신 토크 정책이 아니라, 사람이 쓴 5개 keyframe의 높이·타이밍·몸통 회전 등을 정책이 선택하고 매 물리 substep `qpos`를 직접 대입하는 태스크다. `h1_baseball.xml`은 골반이 world에 고정되어 있다. 이는 제한된 태스크의 추상화로 사용할 수 있으나 이족 균형 학습을 증명하지 않는다.
- `FielderEnv` 체크포인트는 5회 모두 `catch=True`였지만 **정상적인 플라이볼 포구의 5/5가 아니다.** 초기 공이 장식용 `origin_pole` 안에 있고 손과 공을 묶는 `ball_weld`도 활성이다. 각 실행에서 QACC 수치 발산 경고가 났다. 상세 추적은 자동 상태 reset 후 손 부근으로 제약된 공에 가까워지는 결과를 확인했다. 이 파이프라인의 catch 성공률은 수정 전 포구 성능으로 사용할 수 없다.
- `CatcherEnv`는 존재하지 않는 `glove_box`를 조회하여 ID가 `-1`이다. 실제 공–글러브 접촉을 합성했어도 `catch=False`였다. 관측의 base도 실제로 공 좌표다. 12개 action 중 5개는 무시된다.
- `RunnerEnv`는 공의 `qpos[:3]`를 주자 위치로 해석해 초기화·관측·목표 거리·성공 판정에 사용한다. 실제 주자는 `[27.4,27.4,.4]`인데 관측은 공 위치 `[19.4,19.4,2.35]`다. 공만 목표로 설정한 판정 단위검사에서 주자가 멀리 있어도 +1000/종료가 발생했다.
- 기존 가중치를 실제 로드한 소규모 비교: Tee 3/5, Catcher 0/5, Runner 0/5, Fielder 코드상 5/5(위 결함 때문에 의미 제한). 이 소표본은 보편적 성능 추정이 아니다. Tee 고정 action 0도 4/5여서 이 표본은 RL 우월성을 보여주지 않는다.
- `CognitiveBaseballEnv` 원본 실행은 CoreGraphics 렌더 초기화 오류로 막혔다. 렌더 의존성만 감사 인스턴스에서 stub한 별도 검사에서는 존재하지 않는 `root_y`가 `ball_joint`로 잘못 매핑되어 공 x와 vx를 0으로 덮어쓰는 로직 결함을 확인했다. stub 영상을 실제 관측 검증으로 취급하지 않았다.

## 2. 전체 읽기/검색 범위

전체 읽기: `cognitive_ai/envs/{cognitive_baseball_env,teeball_env,soft_toss_env,pitching_machine_env,breaking_ball_env,fielder_env,catcher_env,runner_env}.py`, `shared_assets/{h1_baseball,h1_fielder,h1_catcher,h1_runner}.xml`(공통 파일 비교 포함), `cognitive_ai/training/{train_cognitive,train_teeball,train_fielder,train_catcher,train_runner}.py`, `cognitive_ai/evaluation/{evaluate_fielder,evaluate_base_stealing}.py`, `archive/humanoid/envs/{atlas_baseball_env,humanoid_baseball_env}.py`, `docs/EXPERIMENT_LOG.md`.

관련 부분 읽기: `archive/humanoid/assets/stadium_3d_atlas.xml`, `archive/humanoid/training/atlas_trainer.py`, `README.md`, `docs/PAPER.md`, `docs/VIDEO_CATALOG.md`.

검색: tracked `.py/.md/.json`의 balance/foot/ankle/발 들림/균형 관련 코드·주장. **발 들림 감소 수치나 발 높이 평가 코드는 발견하지 못했다.** 사용자의 예시를 프로젝트의 주장으로 만들면 안 된다. 과거 Atlas의 pelvis 높이 보상은 존재하지만 발 들림이나 지지다각형/ZMP 측정이 아니다. 문서 `docs/PAPER.md:157`의 H1 다리 복원/이족 균형은 향후 계획이다.

## 3. 실제 태스크 계약

공통: 아래 H1 XML의 시간 간격은 `.005 s`이고 중력은 `[0,0,-9.81]`이다(`h1_baseball.xml:3`, 나머지 XML:3). 바디/공 상태는 시뮬레이터 정확 상태를 사용한다. 이것만으로 데이터 누수라고 하지 않으며 실제 센서 기반 추정 구현을 증명하는 것은 아니다.

| 환경 / 근거 | 초기화·관측 | 행동·상태 변화 | 보상·성공·실패·종료 | 정책 주기 |
|---|---|---|---|---|
| `CognitiveBaseballEnv` / :11–58,60–84,86–166 | 공 y=15,z=1.6, fastball 또는 curveball·global RNG. 64×64 RGB 렌더 관측 | 3D trigger/height/speed; 5 keyframe 직접 qpos, qvel=0. `root_y` 없는 관절 오류 있음. drag+Magnus를 xfrc_applied에 설정 | 배트–공 MuJoCo contact +10. 공 y<−2 또는 z<.1 종료, 놓친 공 최종 좌표로 −1 또는 +.5. 명시 max_steps/truncated 없음 | 4×.005=.02 s |
| `TeeBallEnv` / :19–45,54–81,83–166 | 공 `[0,.4,z]`, z∈[.65,.95], 질량1e−6. obs3 공 xyz. 시작부터 swing_active | action1=높이; trigger 없음. shoulder contact/follow-through keyframe 매 step 변경, robot qpos 직접 대입. 공 hit 전 매 substep 직선속도0 | contact +100 및 종료+100; miss −50×min_dist². 접촉 또는 스윙 끝 종료; 40step 시간 제한 | 2×.005=.01 s, swing 약.125 s |
| `SoftTossEnv` / :20–46,56–88,90–191 | 공 `[0,4,1]`; vy∈[−8.2,−7.8], vz∈[1.55,2.05], vx∈[−.04,.04]. obs8=xyz/vxyz/시간/물리식 예상높이 | action2 trigger+height. trigger 순간 높이만 저장, 고정24 substep keyframe. 그 뒤 높이 action은 운동에 미반영 | contact +100 +150+min(speed×10,50). miss 거리+트리거 y=1.20 근접 페널티; 미스윙−30. contact/통과/지면/스윙끝 종료,45step 제한 | .02 s |
| `PitchingMachineEnv` / :23–46,63–117,119–220 | 3 속도구간과 y=4/10/15m. 목표높이[.68,.95]를 맞추도록 초기 vz 계산. obs8 마지막은 pred_z 자체가 아니라 정규화 z_zone | action2; t_remain≤.25일 때 trigger; 높이 저장; 24substep qpos keyframe. 매 step action은 trigger 뒤 운동에 영향 없음 | contact 200+min(speed×10,50). miss 거리, t=.12 timing, 높이오차; 미스윙−60. contact/통과/지면/스윙끝 종료,55step 제한 | .02 s |
| `BreakingBallEnv` / :19–42,57–125,127–247 | 직구40%/슬라이더35%/커브25%, y=12m; x/z 목표와 extra_acc에 맞춰 초기 속도 설정. obs9=xyz/vxyz/t/z_zone/x_zone | action3 trigger+height+yaw; trigger 뒤 keyframe 고정. 매 substep `qvel += extra_acc * .005`로 변화구 가속도 직접 주입(162–164), 물리적 스핀으로 유도한 양력은 아님 | contact 200+속도상한; miss 거리/t=.10/height/yaw alignment; 미스윙−50. common terminal+60step 제한 | .02 s |
| `FielderEnv` / :10–42,44–101,103–150 | 공 `[0,0,1]`, v=[uniform(−10,10),uniform(15,30),uniform(10,25)]. 포물선 착지 근방으로 base slide qpos를 설정하지만 XML world y=30 오프셋 미반영. obs30=공6/base6/upper18 | action12; base3→motor ctrl×5, upper9→각 actuator ctrlrange. MuJoCo motor 동역학. 2D slide+heading base이고 실제 바퀴/다리 보행 동역학은 없음 | −.1×glove site–ball site 거리. 거리<.25이면+1000 catch; 실제 접촉/보유 필요 없음. ball site z<.2면−50 실패;200step 제한 | .02 s |
| `CatcherEnv` / :8–38,40–96 | 공 y18.4→약.4s 도착 설정. obs30의 base/arm slices가 XML 순서와 다름 | action12이나 실효7(base3/left arm4). ctrl=action 직접(상체 전체 torque 범위로 재스케일하지 않음). 10 substep | −.1×잘못 조회한 geom까지 거리. ID−1인 glove contact 요구 때문에 성공 불가. y<−2 또는 z<.1 실패−50;150step 제한 | .05 s |
| `RunnerEnv` / :8–83 | 의도1루→2루. 실제 reset 공을 [19.4,19.4,2.35]로 변경; 주자는 XML [27.4,27.4,.4]에 남음. obs8=공xyz/공vxyz/target−공xy | action3→runner slide/heading motors. actual base는 움직이나 성공은 공을 보고 계산. 공은 active weld로 주자 오른손에 연결 | −.05×공의 목표거리 + .1×공의 목표방향 속도. 공거리<1이면+1000 종료;300step 제한. 태그아웃/포수 송구/도루타이밍 없음 | .05 s |

### 물리 모델과 수동 설계의 범위

- `shared_assets/h1_baseball.xml:60–63`의 `pelvis`에는 freejoint나 root slide가 없다. XML상의 전체 로봇 골반은 world에 고정이며 다리 qpos를 변경해도 로봇의 중심 위치/방향을 외력에 따라 자유롭게 유지·회복하는 태스크가 아니다.
- `h1_baseball.xml:200–216` motor 토크 제한은 존재하지만 Tee/Soft/Machine/Breaking의 정책 행동 적용 경로는 `ctrl`이 아닌 `qpos`/`qvel` 직접 대입이다. 이 제한의 존재를 이 스윙이 물리적 토크 제한을 만족한다는 근거로 쓸 수 없다. XML217의 왼손–배트 connect도 보조 제약이다.
- Fielder/Catcher/Runner는 다리가 없는 cylinder base에 x/y slide 및 yaw 관절을 두었다(XML81). 바퀴 슬립·구동륜 역학/비홀로노믹 제약을 구현한 wheeled robot은 아니며 평면 이동 추상화다. 문서가 이를 추상화라고 소개하는 부분과 함께 판단해야 한다.
- 타격 관측의 time_to_plate/pred_z/x_zone은 물리식으로 계산한 특징이다(Soft185–188, Machine212–219, Breaking238–246). 신경망이 미래 궤적을 추정한 값이 아니다. Breaking 관측식은 extra_acc를 생략하지만 trigger reward 목표식(143–144)에는 포함한다. 근사 특징으로 의도했을 가능성이 있어 이것만으로 bug라고 하지 않는다. 관측식의 오차와 허용 정보 범위를 명시할 필요가 있다.
- `_check_contact`는 MuJoCo contact를 순회한다. 따라서 Tee/Soft/Machine/Breaking의 컨택 판정 자체는 단순 거리 임계값이 아니지만 움직임은 직접 상태 설정이므로 물리적 관절 동력/배트 속도가 일관된 타격이라는 별도 검증이 필요하다.

### 연결 경로와 사용 상태

| 기능 | 실제 진입점 | 연결 자산·가중치 | 상태·근거 |
|---|---|---|---|
| 초기 Cognitive | `training/train_cognitive.py:11` | CognitiveBaseballEnv / h1_baseball.xml, neural checkpoint 없음 | 초기 개념 코드. state를 직접 읽는 heuristic threshold update(18–20,28–39,51–60), WM_Loss는 mock(63). 현재 메인 PPO 경로와 구분 |
| Tee | `training/train_teeball.py:12` / `scripts/test_trained_teeball.py` | TeeBallEnv/h1_baseball.xml/teeball_final_model.zip | 과거 Phase1 태스크; 실제 local weight 로드 성공 |
| Fielder | `training/train_fielder.py:11` / `evaluation/evaluate_fielder.py:13` | h1_fielder.xml / fielder/best_model.zip + vec_normalize.pkl | 독립 Phase7 환경. eval5회, norm 학습동결(:16–17) |
| Catcher | `training/train_catcher.py:12` | h1_catcher.xml / catcher/best_model.zip + vec_normalize.pkl | 독립 학습 코드. base_stealing 평가에서 로드하지만 step하지 않음 |
| Runner | `training/train_runner.py:12` / `evaluation/evaluate_base_stealing.py:13` | h1_runner.xml / runner/best_model.zip + vec_normalize.pkl | 단독 1회 runner 영상. catcher 모델 생성·로드는 있으나 실제 루프는 r_vec만 step(46–53) |
| 과거 Atlas 균형 | `archive/humanoid/training/atlas_trainer.py` | archive/humanoid/envs/atlas_baseball_env.py / stadium_3d_atlas.xml | 별도 과거 Atlas 모델. H1 현재 태스크 성과로 합치면 안 됨 |

## 4. 우선순위별 발견

### PHY-01. Fielder의 높은 catch 수치가 원래 투구 조건의 포구를 의미하지 않음

- 분류: 확인된 문제.
- 우선순위: 진행 차단 — Fielder 포구 성공률 주장과 이 환경의 후속 학습을 차단. 프로젝트 전체 import 실행을 막는다는 뜻은 아님.
- 근거 수준: 정적 확인 + 실행 확인.
- 위치: `cognitive_ai/envs/fielder_env.py:50–74,118–139`; `shared_assets/h1_fielder.xml:76–81,152,167–169`.
- 관찰: 공의 초기 위치는 origin_pole 내부(contact distance −.237m)이고 `ball_weld`는 active=True. seed21 첫 .005s에서 공 velocity가 [−9.03,19.34,20.81]→[−559.15,1151.71,14.65] m/s. trained seed0의 첫 env.step .02s 기대와 달리 time=.01s, warning.number[5]=1(lastinfo=DOF3), 초기 fielder base_y≈99.113 qpos가 ≈−.001386으로 reset. 이후 step7/time=.13s, 공 site [0.25119,29.64899,.81568]와 glove site [.38640,29.76095,.88352] 거리 .1881979로 catch. qpos/qvel은 그 시점 finite였음.
- 이유: 단순 finite 체크만으로 수치 발산 후 자동 reset을 못 찾는다. 반환된 catch가 원래 랜덤 fly-ball 조건의 난도를 반영하지 않는다. 또한 base_y qpos는 displacement인데 착지 world y처럼 초기화/관측하여 실제 world y가 +30m 어긋남.
- 영향: 독립 Fielder 성능/영상, 이를 근거로 통합 수비 지능을 주장하는 표현. 실제 main match에 같은 환경이 연결되는지는 별도 계약 검토 필요.
- 최소 재현: `physics_probe.py --task fielder` 및 `fielder_trace.py`, seed0 trained. 정상·random/zero도 로그 보존.
- 구체적 보완: 새로운 환경 버전에서 투구 중 ball_weld 비활성/제거, marker pole의 collision mask0 또는 launch 변경, named joint/world 좌표 일치, 경고 또는 simtime 단조성 위반 시 invalid episode 표시. 정상 fly ball에서 공–글러브 접촉 및 포유시간을 측정할지 태스크 명시.
- 통과 기준: 동일 고정 seed마다 expected dt만큼 시간 증가, 경고0, 공 초기 궤적 reference와 지정 오차 이내, desired/actual base world 오차 허용치 이내, 원래 초기조건 provenance가 유지된 catch만 평가. 수정 환경에는 기존 policy를 그대로 공정비교했다고 하지 않고 필요 재학습 후 baseline 비교.
- 아직 모름: 기존 300k 학습 시점의 MuJoCo 버전 및 당시 XML에 같은 제약이 있었는지, 당시 성공 로그와 현재 weight/XML 정확 대응.

### PHY-02. Catcher의 실제 글러브 접촉을 성공으로 판정할 수 없음

- 분류: 확인된 문제.
- 우선순위: 진행 차단 — Catcher 성공률 평가와 다음 학습.
- 근거 수준: 정적+실행 확인.
- 위치: `cognitive_ai/envs/catcher_env.py:16–25,28–38,61–87`; `shared_assets/h1_catcher.xml:76–81,116,165,168`.
- 관찰: `glove_box` ID −1, 실제 `glove_geom` ID22. MuJoCo contact geom ID는 비음수라 조건상 성공 불가. eq를 audit instance에서 끄고 실제 공–glove 접촉 (5,22)을 생성하고 물리를 동결해 판정만 호출했을 때 catch=False. negative numpy index 때문에 거리계산은 다른 마지막 geom을 사용한다. obs[:3]도 catcher base가 아닌 공 `[0,18.4,1.5]`; 실제 base `[0,−1.5,.4]`. 액션7–11은 존재하지 않는 ID/루프 truncation으로 모두 무시되고 변화시켜도 ctrl/obs/qpos 동일.
- 이유: 목표 판정·reward 거리·관측·행동 계약이 서로 어긋난다. active ball_weld까지 남아 정상적인 incoming pitch가 아니다.
- 영향: 포구 학습과 베이스스틸 통합을 주장할 근거. 단독 weight가 로드된다는 사실은 목표를 배운 증거가 아님.
- 최소 재현: `physics_probe.py --task catcher`와 `physics_contracts.py`.
- 보완: named geom 조회와 assert ID≥0, named joint 주소로 obs, action dimension 계약 일치, free pitch 시 weld inactive. 포구를 한 번 접촉으로 할지 일정 시간 보유로 할지 명시.
- 통과 기준: 실제 glove contact synthetic case 성공, non-glove contact 실패, 12차원 유지 시 모든 action 효과 설명 또는7D 재정의, 실제 base obs 일치. 수정 후 기존 weight/normalizer 호환 판단과 재학습·평가 분리.
- 아직 모름: 당시 학습 환경이 같은 버전이었는지. 문서의 Catcher를 실제 어떤 시연에서 사용했는지 전부 검증하지 않음.

### PHY-03. Runner의 목표 거리는 주자가 아니라 공으로 계산됨

- 분류: 확인된 문제.
- 우선순위: 진행 차단 — 도루/베이스 도달 성능 주장과 후속 Runner 학습.
- 근거 수준: 정적+실행 확인.
- 위치: `cognitive_ai/envs/runner_env.py:29–38,46–49,64–78`; `shared_assets/h1_runner.xml:76–81,168`.
- 관찰: ball freejoint가 XML 첫 관절(qposadr0)이고 runner_x/y/yaw는 각각 qposadr7/8/9. reset이 공만 [19.4,19.4,2.35]로 놓고 runner는 [27.4,27.4,.4]. 합성 테스트에서 공 xy만 target `[0,38.8]`로 두고 물리를 동결하니 실제 runner가 약29.67m 떨어져 있어도 reward1000/terminated=True.
- 이유: 현재 정책은 평면이동 motor를 제어하지만 reward/obs는 weld된 공으로 받는다. 본래 베이스 도달이 아닌 잘못된 proxy 최적화다. yaw라고 쓰는 obs[2]는 공 높이다.
- 영향: `evaluate_base_stealing.py:63–64`의 SAFE/도루 성공 판정. 이 평가에서는 포수를 실제 step하지 않아 송구와 시간 경쟁도 검증하지 않음(:32–34,46–53).
- 최소 재현: `physics_probe.py --task runner`.
- 보완: 모든 state/reward/reset을 runner joint 및 base body world pose로 교체; XML body origin과 slide displacement 처리; 불필요 공/weld 제거 또는 경기 역할 분리; 독립 달리기와 도루 경쟁 태스크를 구분.
- 통과 기준: 공만 움직이면 runner obs/거리/성공 불변; runner base만 목표에 도달하면 성공. 실제 world initial xy가 선언된1루와 일치. 도루 주장에는 포수 송구/태그/주자 시간조건을 통합 평가.
- 아직 모름: 기존 weight가 이 잘못된 proxy에서 어떤 일반화된 전략을 배웠는지. 이번5개 seed는 Runner reset이 deterministic이므로 독립5개 초기조건이 아닌 같은 조건 반복임.

### PHY-04. Cognitive의 없는 관절 이름이 공의 상태를 덮어씀

- 분류: 확인된 문제.
- 우선순위: 이번 단계 보완 — 해당 과거 경로의 타격 결과를 해석하기 전 수정; 현재 Match 경로 전체를 차단한다고 하지 않음.
- 근거 수준: 정적 + renderer 의존성만 대체한 실행 확인. 원본 RGB pipeline은 실행 제약으로 확인 불가.
- 위치: `cognitive_ai/envs/cognitive_baseball_env.py:28–32,141–154`; `shared_assets/h1_baseball.xml:60–63,193`.
- 관찰: XML에 root_y 없음→mj_name2id −1→model.jnt_qposadr[−1]=19=ball_qposadr. `qpos[19]`와 공 vx를 swing keyframe의 root값0으로 덮어쓴다. synthetic 값을 x=.123,vx=.456으로 두고 원본 메서드 호출 후 둘 다0.
- 이유: 정책으로 조절한 로봇 자세가 투구의 횡방향 궤적을 직접 바꾸는 우발적 결합.
- 영향: 이 환경을 사용한 초기 heuristic/vision demo. 현재 다른 환경에 같은 오류가 있다고 일반화하지 않음.
- 최소 재현: `physics_contracts.py`의 SyntheticRenderer scope; 실제 image output은 의도적으로0이고 검증 대상이 아님.
- 보완: 이름 조회마다 음수 ID 예외, 모델과 joint list 계약 맞추기.
- 통과 기준: 로봇 keyframe 업데이트 전후 free-ball qpos/qvel이 불변; 관절별 주소가 중복/ball과 겹치지 않음.
- 아직 모름: 원본 visual 환경의 실제 RGB quality/renderer 수명/장기 실행. 원본 렌더러는 `invalid CoreGraphics connection`으로 생성 실패.

### PHY-05. reset(seed=...)가 다수 환경의 난수를 제어하지 않음

- 분류: 확인된 문제.
- 우선순위: 이번 단계 보완 — 재현 가능한 평가 프로토콜.
- 근거 수준: 정적+Tee/Catcher 실행. Soft/Machine/Breaking/Cognitive는 정적(부모 실행 근거 추가 가능).
- 위치: Tee reset59/71, Soft61/77–80, Machine64/85–109, Breaking58/76–117, Catcher41/48–49, Cognitive61/73–80.
- 관찰: Gym `super().reset(seed)` 호출 후 `self.np_random` 대신 전역 `np.random` 사용. Tee seed42를 연속 reset했는데 z=.925062→.826563. Catcher도 같은 seed의 다른 투구. Fielder는 직접 np.random.seed로 seed를 지키지만 프로세스 전역 RNG를 바꿈(:44–46). Runner는 난수가 없어서 같은 seed가 동일하나 다양한 초기조건을 의미하지 않음.
- 이유: 학습/평가 seed 로그만으로 동일 pitch를 재현하지 못한다. 병렬환경에서 전역 seed의 상호작용도 명시해야 한다.
- 영향: 문서 타격률 재현과 paired baseline 비교.
- 최소 재현: `physics_probe.py` reset_seed_contract. 기준선 비교는 이를 우회해 매 episode np.random.seed(seed)를 명시해 동일 초기 qpos를 확인했다.
- 보완: 환경별 self.np_random로 난수 통일, 초기조건 JSON 저장/로드 경로 추가.
- 통과 기준: 동일 seed/reset 두 번의 최초 observation 및 초기 qpos/qvel 동일, 다른 seed 변화, 서로 다른 env를 reset해도 상대 env RNG 불변.
- 아직 모름: 원래 실험에서 global numpy seed를 별도로 고정했는지; 현재 문서만으로는 없음.

### PHY-06. 트리거 후 실행되지 않은 action이 종료 reward에 반영됨

- 분류: 확인된 문제(정적); 성능 영향 크기는 미검증.
- 우선순위: 이번 단계 보완.
- 근거 수준: 정적 확인. 부모 감사에서 최소 실행 추가 권장.
- 위치: `pitching_machine_env.py:127–137,173–179`; `breaking_ball_env.py:137–157,197–205`.
- 관찰: 스윙 높이/yaw는 trigger step에서만 keyframe에 고정하지만 miss 높이/yaw penalty는 마지막 step의 `target_z_delta`/`target_x_yaw` 로컬 변수를 쓴다.
- 이유: 이미 실행한 동일 스윙에서, 물리 궤적을 바꾸지 않는 마지막 action으로 reward를 바꿀 수 있다. 이 shaping을 행동의 정확도라 해석할 수 없다.
- 영향: reward 개선과 실제 높이/방향 정확도의 연결.
- 최소 재현: 동일 seed·trigger/action으로 두 인스턴스 실행 후 final step 높이/yaw만 바꿔 qpos/contact/거리 동일 및 reward 차이 확인.
- 보완: trigger action을 별도 저장하고 penalty에 저장값을 사용하거나 실행 후 action이 없는 option형 API로 재정의.
- 통과 기준: 이미 고정된 스윙 뒤 action을 바꾸면 trajectory와 reward 모두 불변(별도 합법 제어동작으로 정의하지 않는 한).
- 아직 모름: 학습 정책이 실제 이 경로를 이용했는지. 이를 exploit했다고 단정하지 않음.

### PHY-07. Tee 문서의 action·질량 설명과 현 구현 차이

- 분류: 확인된 불일치. 결과90% 재현 여부는 별도 확인 불가.
- 우선순위: 이번 단계 보완.
- 근거 수준: 정적+실행, 결과90%는 문서 주장.
- 위치: `docs/EXPERIMENT_LOG.md:8–11`; `teeball_env.py:22–24,62–76,110–116`.
- 관찰: 문서는 action2 trigger+height, 질량.001kg 중력상쇄라고 쓰지만 실제 action1 높이, 자동스윙, 질량1e−6이고 공 hit전 속도0. 질량 감소 자체가 중력가속도를 상쇄하는 것은 아니다.
- 이유: 다른 태스크/물리 조건 수치를 같은 결과로 비교하기 어렵다. 현재 checkpoint도 action1 로드된다.
- 영향: Phase1 90% 결과의 조건 설명과 전신/RL 학습 내용.
- 최소 재현: Tee metadata/weight space 기록 및 코드 줄 비교. 이번 seed0–4 trained3/5가 기존90%를 통계적으로 반증하는 것은 아님.
- 보완: 당시 코드 commit/weight/hash/평가초기조건을 매핑하고 현재문서에 버전별 실제1D 추상화 설명. 정지공 의도는 명시적 kinematic/중력보상 모델로 정의.
- 통과 기준: 실행 관측·행동·질량·hold 방식과 문서가 정확히 일치, 기존90% 분모/seed/weight를 식별.
- 아직 모름: 문서가 설명한2D 이전 환경이 따로 있었는지 및 당시 평가자료.

### PHY-08. 초기 Cognitive 경로의 WM_Loss는 실제 학습 손실이 아님

- 분류: 확인된 구현 사실. 명시적 mock 주석이 있으므로 개발자가 이를 속이려 했다고 추정하지 않음.
- 우선순위: 이번 단계 보완 — 해당 로그를 성과 증거로 제시할 때만 차단.
- 근거 수준: 정적 확인.
- 위치: `training/train_cognitive.py:18–20,28–39,51–64`.
- 관찰: neural world model optimizer 없이 heuristic trigger threshold를 ±.25 바꾸고, loss는 random(.1,.5)×(1−ep/episodes). 영상 픽셀 obs도 정책 결정에서 쓰지 않고 env.data ball_pos를 직접 읽음.
- 이유: WM_Loss 감소나 pixel prediction이 학습됐다고 해석하면 구현과 맞지 않는다. current PPO/MoCap 전체가 fake라는 뜻은 아니다.
- 최소 재현: 위 코드의 loss 식·업데이트 경로 정적 추적(200회 학습 스크립트를 실제 실행할 필요 없음).
- 보완: archived proof-of-concept/heuristic demo 명시, mock 메트릭을 성능표에서 배제.
- 통과 기준: 프로젝트 설명이 실제 사용하는 학습 경로를 식별하고 해당 로그의 성격을 분리.
- 아직 모름: 이 출력이 외부 발표에서 실제 학습손실로 사용됐는지.

## 5. 재현 실행·기준선

환경: Python3.11.5, MuJoCo3.10.0, Gymnasium1.3.0, NumPy2.4.6, SB3 2.9.0, Torch2.13.0, arm64 macOS27.0. 기존 `.venv` 사용, 설치·네트워크·학습 없음. 모든 실행 cwd는 `_audit/20260926_013033`, `PYTHONDONTWRITEBYTECODE=1`, `MPLCONFIGDIR="$PWD/logs/mpl"`. XML은 audit shared_assets symlink 또는 절대경로를 통해 읽음. MuJoCo 오류파일도 audit cwd 안에만 생성됨. 원본 파일·checkpoint 쓰기 없음.

각 명령의 공통 prefix: `PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR="$PWD/logs/mpl" ../../.venv/bin/python -B`.

| 실행명령(prefix 뒤) | 기대 | 실제 | 로그 | 한계 |
|---|---|---|---|---|
| `scripts/physics_probe.py --task tee` | init/reset/step/종료·다음reset/기존 PPO 추론,5 seeds baseline | 성공. obs3/action1, 유한값·space 적합. trained3/5 | `logs/physics_tee.jsonl`, `.stderr.txt` | max45step,20episodes. 첫 실행 후 스크립트에120초 alarm 추가(이 실행은 bounded loop만,1.90초 종료). output 식은 동일 |
| `scripts/physics_probe.py --task catcher` | 동일 + valid name/contact 계약 | PPO 로드·진행; false catch 계약 발견; trained0/5 | `logs/physics_catcher.jsonl`, `.stderr.txt` | max155step/각5seed,15episodes. 합성contact는 정책결과 미집계 |
| `scripts/physics_probe.py --task runner` | 실제 이동/목표거리 일치 | PPO 로드·진행; 잘못된 공 거리 확인; trained0/5 | `logs/physics_runner.jsonl`, `.stderr.txt` | max305step/15episodes. 환경초기조건 난수 없으므로 seed반복 독립사례 아님 |
| `scripts/physics_probe.py --task fielder` | fly-ball 추적 및 valid catch | PPO 코드상5/5, QACC 경고와 자동reset을 동반 | `logs/physics_fielder.jsonl`, `.stderr.txt` | max205step/15episodes. 포구 성능 측정으로 무효 |
| `scripts/physics_probe.py --task cognitive` | 원본 RGB init/reset/3step | 생성에서 CoreGraphics connection 실패(exit1) | `logs/physics_cognitive.jsonl`, `.stderr.txt` | OS 렌더 접근 제약. 모델로직 전체 결함으로 확대하지 않음 |
| `scripts/physics_contracts.py` | 상태주소·미사용action·weld 원인 분리 | missing joint 공덮어쓰기, catcher5D 무시, weld 영향 확인 | `logs/physics_contracts.jsonl`, 이후 initial contacts 추가한 `logs/physics_contracts_contacts.jsonl`, 각각stderr | 모두 합성/기전 검사. renderer는 stub, weld off는 학습비교 아님 |
| `scripts/fielder_trace.py` | 경고/시간/좌표 추적 | seed0 첫step reset 후7step catch 확인 | `logs/fielder_trace.jsonl`, `.stderr.txt` | 별도1episode;5/5와 합산 금지 |

스크립트는120초 signal alarm 및 유한 step cap을 둔다. 기존 source·XML·가중치 식별은 전체 감사 manifest 및 각각 `checkpoint`/`normalization` JSON record의 sha256을 사용. 모든 모델은 CPU deterministic inference, normalizer.training=False/norm_reward=False; 기존 statistics를 수정·저장하지 않았다.

### 소규모 paired 기준선 결과

Tee/Fielder/Catcher에서 매 episode global np.random.seed(0…4)를 초기화하여 mode 간 초기 qpos를 맞췄고 random action은 별도 default_rng(seed+1000)를 썼다. 정책 inference는 deterministic이다. **비율의 모집단 추정·통계적 우월성·기존 문서 수치의 확증/반증이 아니다.**

| 환경 | zero action | random | 높이 규칙 | 기존 정책 | 실패/시간 조건 |
|---|---:|---:|---:|---:|---|
| Tee |4/5|1/5|3/5|3/5|hit .08s 또는 miss .13s. zero는 높이 중간값 자동스윙이지 무동작 아님 |
| Catcher |0/5|0/5|—|0/5|zero/policy 모두7.5s timeout. random2회 terminal failure,3회timeout. 성공geom 판정 불가능 |
| Runner |0/5|0/5|—|0/5|모두15s timeout. trained 실제 base 최종거리8.9828779m. reset난수 없음 |
| Fielder |0/5|1/5|—|5/5|policy 모두7step/.125~.13s. 각 실행 QACC 경고 및 초기조건유실. 해당성공률은 해석 제한 |

Tee 단순 규칙은 `clip((ball_z-.8)/.15,-1,1)`이고 학습/탐색 튜닝하지 않았다. zero_action은 각 motor 환경에서 zero ctrl 명령이며 “자세 유지”를 뜻하지 않는다. 로봇 중력·제약에 따라 움직일 수 있다. 훈련 policy보다 zero가4/5로 보인다고 이5사례로 RL이 불필요하다고 결론 내리지 않는다. 다만 정해진 macro task의 baseline 비교가 반드시 필요하다는 근거다.

### Fielder 상세 추적과 diagnostic 조건변경

`fielder_trace.jsonl`에서 warning count는 첫step `[0,0,0,0,0,1,0]`, lastinfo `[0,0,0,0,0,3,0]`. 이후 finite 상태로 catch까지 진행하므로 finite assertion만으로 충분하지 않다. 최초 world base_y=129.113m이었으나 reset 이후 base는 world y≈30m 근방이다. 공은 처음 y=0에서 출발했지만 reset 뒤 y≈12.65m로 바뀌고 active weld에 의해 right hand 부근으로 이동한다.

`physics_contracts_contacts.jsonl`의 seed21, **정책 없이 단 한 substep** weld active/inactive 비교는 기전 진단이다. active vx/vy=[−559.15,1151.71], inactive=[−10.19,18.78]. inactive도 초기 origin_pole 접촉이 남아 정확한 무충돌 포물선과 같지 않다. 이를 weld 제거로 성능이 좋아졌다/나빠졌다는 정책 ablation으로 쓰면 안 된다. 기존 정책에 보조를 제거한 평가에는 분포 변화가 있으므로 공정한 효과 비교에는 태스크수정/재학습/동일기준선이 필요하다.

## 6. archive의 균형 범위와 추가 검증 제안

- `archive/humanoid/envs/atlas_baseball_env.py:152–166`는30개 motor에 clip action을 넣고5 substep 진행 후 pelvis world z만으로 balance reward를 계산한다. `:190–194`는 z<.4 fall. 실제 free pelvis는 `stadium_3d_atlas.xml:139–140`, dt=.002(:3), 따라서 제어주기 .01s. 이 archive는 전신 torque 제어 시도여서 현재 H1 macro-action과 구분해야 한다.
- 측정은 pelvis 높이뿐이고 발 접촉·정상력·지지다각형·CoM margin·회복 실험은 없다. 이 코드의 존재는 시도를 보여주지만 균형을 학습했다는 성공 증거는 아니다. 이번에 Atlas assets/import 경로를 복구하거나 실행하지 않았으므로 성능 판단은 유보.
- Atlas `_get_obs():112–114`의 hardcoded qpos slices는 XML이 baseball freejoint와 cf slide 관절을 pelvis보다 먼저 선언(:125–140)하기 때문에 pelvis30DOF라고 바로 믿기 어렵다. 과거 결과를 재사용하려면 named joint mapping으로 검증해야 한다. 현재 메인환경으로 일반화 금지.
- `archive/humanoid/envs/humanoid_baseball_env.py:73–76`은 context space2인데 `_get_obs():172–174`에서 game6+target2를 합쳐8D 반환한다. 이 archive를 다시 학습에 사용할 때는 observation 계약부터 통과해야 한다. 현재 H1 결과의 결함으로 전가하지 않음.
- 다음 핵심 검증은 원본을 고치지 않은 새 버전으로 Fielder/Catcher/Runner의 named state와 goal predicate부터 바로잡고, 고정 초기조건·경고0·실제 사건 판정이 통과한 뒤 해당 branch용 policy를 재학습하는 것이다. 이 세 독립부품의 결함을 고치는 것만으로 main match 전신성/9이닝 정책연결이 입증되는 것은 아니다.
