# 학습·평가·경기 연결 감사 메모

검사 기준: 로컬 `main` / `f63dc977` (루트 감사에서 제공한 식별 정보; 이 하위 작업은 원본 수정·신규 학습을 하지 않음). 아래 소스 위치는 저장소 루트 `/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/`에 대한 정확한 상대 경로이다. 줄 번호는 이번 검사 시점 원본 기준.

## 가장 중요한 결론

1. 학습된 정책 파일은 실제로 존재한다. ZIP의 JSON 메타데이터를 읽어 mega 타자 48차원(12×4), 투수 16차원, 16개 환경 및 각각 1,920,000 / 1,600,000 step에 저장된 best 정책을 확인했다. 이것은 학습 산출물과 저장 상태를 뒷받침하지만 컨택률, 스핀 추론 능력, 인과적 개선을 증명하지 않는다.
2. 기본 데모는 mega 정책을 사용하지 않는다. `run_demo.sh → simulate_full_match.py → BatterMatchTrainingEnv → BaseballMatchEnv`이고, 정책은 mocap pitcher/batter, 타자 관측은 12차원 단일 프레임이다. `train_mega_architecture.py`는 별도 학습 경로이며 이를 연결한 평가/데모 진입점은 현재 Python 검색에서 발견되지 않았다.
3. 투수 단독 학습 관측과 경기 관측은 모두 16차원이지만 열 순서가 다르다. 경기 타자 학습·평가에 연결된 투수 정책은 의미가 뒤섞인 관측을 받는다. shape 검사만으로 드러나지 않는 실제 계약 결함이다.
4. 특정 평가에는 정규화 생략, terminal 상태 대신 reset 상태 판정, 존재하지 않는 컨택/스윙 필드 참조가 있다. 문서의 기존 성능을 현재 평가기로 확인했다고 볼 수 없다.
5. 9이닝은 무작위 이벤트를 입력하는 별도 텍스트 상태 머신이고, 도루 데모는 포수와 경쟁하지 않는 주자의 목표 도달이다. 제한된 구성요소로 사용할 수 있으나 통합 정책 경기 완료의 증거는 아니다.

## 실제 연결표

| 기능 또는 주장 | 실제 진입점 | 연결된 환경·정책·통계 | 사용 상태 | 확인 근거 |
|---|---|---|---|---|
| 기본 중계 데모 | `run_demo.sh:6` → `evaluation/simulate_full_match.py:13` | `BatterMatchTrainingEnv` + `BaseballMatchEnv(is_eval_mode=True)`; mocap pitcher + mocap batter, 각각 VecNormalize | 현재 기본 데모 | `run_demo.sh:5-12`, `simulate_full_match.py:15-32` |
| MoCap 별도 5회 평가 | `evaluation/evaluate_mocap_match.py:13` | 동일 정책이나 b_norm 생성 후 raw b_vec를 사용 | 별도 과거/병행 평가; 기본 데모에서 호출 안 됨 | `evaluate_mocap_match.py:18-40,53,61-66` |
| MLB 15회 맞대결 | `evaluation/simulate_mlb_match.py:15` | mlb pitcher/batter + VecNormalize 수동 적용; `BaseballMatchEnv()` 기본 짧은 모드 | 별도 과거/병행 경로 | `simulate_mlb_match.py:16-20,47,64-74` |
| 현재 타자 학습 wrapper | `training/train_mlb_batter.py:14` | 경기 환경 + `PitcherEnv`용 통계/고정 투수 정책; 타자 12D→3D | mocap·mega·데모에서 재사용 | 각 import와 `train_mlb_batter.py:18-46` |
| MoCap 미세학습 | `training/train_mocap_pitcher.py`, `train_mocap_batter.py` | mlb 정책·통계에서 재개; 각 60k 명령 | 기본 데모 정책 생성 코드 | 두 파일의 load/learn/save |
| mega 타자 | `training/train_mega_architecture.py:43` | 16×BatterMatchTrainingEnv, VecNormalize→VecFrameStack(4), PPO MlpPolicy | 별도 학습; 기본 데모 미연결 | `:48-73`; ZIP obs48 |
| mega 투수 | 같은 파일 `:76` | 16×PitcherEnv, VecNormalize, PPO MlpPolicy | 별도 학습; 기본 데모 미연결 | `:81-101`; ZIP obs16 |
| 주자 목표 도달(도루 명명) | `run_demo.sh:9` → `evaluate_base_stealing.py` | RunnerEnv와 runner 정책만 step; CatcherEnv/정책은 로드 후 미사용 | 기본 데모의 독립 시연 | `evaluate_base_stealing.py:15-34,46-66` |
| 9이닝 | `run_demo.sh:12` → `simulate_9_innings.py` | BaseballGameState + Python random; MuJoCo/PPO 호출 없음 | 텍스트 규칙 데모, 기본 스크립트는 head 25줄로 절단 | `simulate_9_innings.py:14-30` |
| adversarial 투수 | `envs/adversarial_match_env.py` | BaseballMatchEnv, 선택적 타자 경로이나 predict는 pass | 현재 import/호출 검색에서는 미연결 stub | `:42,47-53`; 다른 파일 참조 검색 |
| 옛 match 타자 | `training/train_match_batter.py` | 9D 선언/현재 Match는12D, 구 pitch checkpoint | 현재 핵심 경로에서 import 안 된 옛 코드 | `:23,37-39`; 현재 get_observations |
| 독립 수비 | `train_fielder.py` → `evaluate_fielder.py` | FielderEnv; fielder/best_model과 통계 | 별도 구성요소, full match에 미연결 | training/evaluation import, full match 전체 호출 추적 |

## 관측·평가 계약

투수의 동일 차원 내 순서 차이:

| 0-based index | PitcherEnv 학습 관측 | BaseballMatchEnv 경기 관측 |
|---|---|---|
| 0–2 | target_x, target_z, released | 동일 |
| 3 | ball_x | throw_progress |
| 4–5 | ball_y, ball_z | ball_x, ball_y |
| 6–8 | ball_vx, ball_vy, ball_vz | ball_z, ball_vx, ball_vy |
| 9–11 | hand_x, hand_y, hand_z | ball_vz, hand_x, hand_y |
| 12 | throw_progress | hand_z |
| 13–15 | pitch-type one-hot | 동일 |

`train_mlb_batter.py:43-44`는 경기 관측을 재배열하지 않고 단독 투수 통계에 넣는다. 투수는 `deterministic=False`로 추론하므로 타자를 deterministic 평가해도 상대 투수의 샘플링은 남는다. 정책 파라미터 업데이트는 이 wrapper에서 하지 않으며 `p_norm.training=False`, `norm_reward=False`는 올바르게 설정했다. 동결과 결정론은 별개다.

타자 관측 `BaseballMatchEnv:397-406`: ball_pos(3), ball_vel(3), 중력 포물선으로 계산한 도달 시간/정규화된 예상 z/x(3), 구종 one-hot(3). 미래 위치 특징은 학습된 예측 모델의 결과가 아니다. 시뮬레이터 상태 기반 특징을 허용하는 태스크로는 가능하나, 스핀을 관측 시퀀스에서 스스로 발견한다는 주장과 구분해야 한다. mega는 이 이미 가공된 12D 관측을 4개 연결한 MLP이며 `docs/PAPER.md:46`의 LSTM 표기는 구현과 불일치한다.

학습/평가 차이: `BatterMatchTrainingEnv` 학습 기본 `is_eval_mode=False`, 실제 중계 `True`; Match `:279-287`에서 접촉 뒤 제한 20→350 step, 총 제한70→450. Wrapper 보상은 `has_contacted`가 참인 매 step 반복 지급(`train_mlb_batter.py:50-52`)하므로 동일 접촉이라도 모드별 누적 보상/거리 관찰 구간이 다르다. 평가 시 단순 reward 비교를 공정한 정책 성능 비교로 쓰면 안 된다. timeout은 wrapper `:67`에서 항상 terminated=done, truncated=False로 전달한다.

## 중요한 발견

### TE-01. 투수 정책의 단독 환경→경기 환경 관측 순서 불일치

- 분류: 확인된 문제
- 우선순위: 진행 차단 — 연결 정책의 의미 있는 평가와 현재 wrapper를 이용한 후속 타자 학습을 막음. import/shape 실행 자체를 막지는 않음.
- 근거 수준: 정적 확인 (루트 감사에서 동적 수치 확인 추가 가능)
- 위치: `cognitive_ai/envs/pitcher_env.py:238-250`, `cognitive_ai/envs/baseball_match_env.py:374-395`, `cognitive_ai/training/train_mlb_batter.py:43-44`
- 관찰한 사실: 모두16D지만 index3–12의 의미가 다름. 같은 통계·정책에 그대로 전달.
- 문제가 되는 이유: 정책이 학습한 ball_x 위치에 throw_progress가 들어가며, 평균/분산도 잘못 대응한다.
- 영향을 받는 결과·주장: 실시간 학습 투수와 타자의 정상 연결, mocap/mlb/mega batter 및 기본 데모의 상대 투수 행동.
- 최소 재현 방법: 두 get_obs에 동일 target/ball/hand/progress 값을 대입해 열별 비교. 16이라는 shape 검사만 하지 말 것.
- 구체적인 보완 행동: 하나의 named schema를 기준으로 경기 관측을 순서에 맞게 변환. 기존 파일은 감사에서 수정하지 않음.
- 보완 후 통과 기준: 동일 semantic state의 관측 벡터와 정규화 값이 열별 일치; 각 가중치 입력 계약을 manifest로 저장. 기존 타자 checkpoint는 잘못 연결된 상대에 학습했을 수 있어 고친 환경에서 먼저 재평가.
- 아직 모르는 부분: 저장 가중치별 실제 학습 코드 버전과 과거 순서, 잘못된 관측이 기존 타자 성능에 미친 크기.

### TE-02. MoCap 평가에서 로드한 타자 정규화를 우회

- 분류: 확인된 문제
- 우선순위: 진행 차단 — `evaluate_mocap_match.py`를 통한 정책 평가 해석을 막음.
- 근거 수준: 정적 확인
- 위치: `cognitive_ai/evaluation/evaluate_mocap_match.py:36-40,61-66,80-88`
- 관찰한 사실: b_norm을 로드하고 PPO에 연결하지만 실제 reset/step은 내부 raw `b_vec`. predict는 전달된 관측을 내부적으로 VecNormalize하지 않음. `p_model`은 로드만 하고 wrapper 내부 투수가 별도로 행동.
- 문제가 되는 이유: 학습 때 정규화 입력을 사용한 정책에 raw 입력 제공. 또한 done 후 pitch_type은 reset된 새 에피소드, speed는 존재하지 않는 `pitch_speed` info 키 fallback으로 reset 상태의0을 읽음(실제 키는 pitch_speed_kmh).
- 영향을 받는 결과·주장: MoCap 5회 box score, 영상 HUD 구속/구종 및 학습-평가 대응.
- 최소 재현 방법: 같은 obs에 `b_vec.reset()` 대 `b_norm.reset()` 경로와 normalize_obs 결과 비교. terminal info에서 pitch_speed_kmh를 읽는지 추적.
- 구체적인 보완 행동: reset/step을 b_norm으로 통일, 모든 terminal 메타데이터를 info에 보존하고 그 값으로 기록.
- 보완 후 통과 기준: 정책 입력이 training transform과 같고 eval 중 통계가 고정됨. terminal 구속·구종이 마지막 전이 상태와 일치.
- 아직 모르는 부분: 과거 영상이 이 현재 코드 버전으로 생성되었는지, 정규화 우회가 성공률에 미친 크기.

### TE-03. 기본 중계의 컨택 감지·종료 판정이 실제 환경 상태 계약과 불일치

- 분류: 확인된 문제
- 우선순위: 진행 차단 — 기본 중계의 타구/심판 결과 및 동적 카메라 주장을 막음. 정책 step 실행과는 별개.
- 근거 수준: 정적 확인 + 실제 실행 확인(SB3 synthetic autoreset 계약)
- 위치: `cognitive_ai/evaluation/simulate_full_match.py:60-87`, `cognitive_ai/envs/baseball_match_env.py:118-123,268-272,293-299,302-306`; 설치 SB3 `common/vec_env/dummy_vec_env.py:68-72`
- 관찰한 사실: actual flag는 has_contacted인데 스크립트는 has_hit을 읽는다. 대안 batted_distance는 종료 때만 설정되고, DummyVecEnv는 그 step 내부에서 reset하므로 읽을 때0이다. terminal ball_pos 역시 다음 에피소드 위치. swing/info key와 has_swung도 실제 b_swing_active와 다름.
- 문제가 되는 이유: 실제 컨택이 있어도 hit_detected가 False로 남고 타구 카메라/타구 판정 경로를 타지 못한다. terminal 장면·판정이 원래 공 상태가 아니다.
- 영향을 받는 결과·주장: README:28-29의 정밀 심판·자동 카메라, PAPER:134의 결함 없는 run_demo 파이프라인.
- 최소 재현 방법: `_audit/20260926_013033/scripts/vecenv_contract_probe.py`로 종료 raw 상태가 reset됨 확인. 실제 컨택 사례에서는 infos[0]['has_contacted']와 hit_detected를 함께 기록.
- 구체적인 보완 행동: info에 terminal ball_pos, trajectory crossing, contact, swing, pitch_type을 저장하고 evaluator는 오직 같은 전이 info로 판정. 카메라는 info.has_contacted를 사용. 영상 terminal frame은 reset 전 캡처 가능한 경로로 별도 처리.
- 보완 후 통과 기준: 통제된 contact/no-contact/swing 세 사례에서 info, 카메라, 심판 결과가 같은 에피소드와 일치; 종료 직전·직후 관측을 구분.
- 아직 모르는 부분: 과거 생성 영상에 별도 패치가 적용되었는지. 이번 synthetic 실행은 학습 정책 성공 사례가 아니다.

### TE-04. 파울 처리 시 볼·스트라이크 카운트가 잘못 초기화됨

- 분류: 확인된 문제
- 우선순위: 이번 단계 보완 — 표준 카운트/9이닝 규칙 주장을 막지만 정책 물리 검증에는 독립적.
- 근거 수준: 실제 실행 확인 + 정적 확인
- 위치: `cognitive_ai/envs/baseball_game_state.py:27-31`
- 관찰한 사실: handle_hit이 FOUL 분기 전에 reset_count를 호출. 합성 1S2B foul→1S0B, 2S3B foul→1S0B. 초기 0S0B foul은1S0B로 우연히 정상.
- 문제가 되는 이유: 일반 파울은 볼 카운트를 유지하고 2스트라이크 이후 스트라이크도 유지해야 하는데 구현은 초기화. 후속 삼진/볼넷 및 이닝 분포를 바꿈.
- 영향을 받는 결과·주장: README:30 완전한 표준 경기 카운트 추적, PAPER:123-124.
- 최소 재현 방법: `rules_and_checkpoint_probe.py`의 ordinary_foul 3개 사례.
- 구체적인 보완 행동: FOUL을 별도 분기로 처리하고 실제 타석 종료 때만 reset_count. 범위가 단순 규칙 모델임을 설명.
- 보완 후 통과 기준: 0S0B→1S0B, 1S2B→2S2B, 2S3B→2S3B; 이어지는 3번째 strike/4번째 ball와 3아웃 교대 검증.
- 아직 모르는 부분: 이 코드 외 경기 규칙 구현의 존재 여부; 현재 기본 경로에서 더 완전한 규칙은 발견하지 못함. walk-off, 9회말 생략, 연장 등은 구현 안 된 제한 범위로 표시할 수 있으며 이 제한을 자동으로 태스크 오류라고 보지는 않음.

### TE-05. full match·9이닝·도루가 하나의 경쟁 경기로 연결되지 않음

- 분류: 확인된 문제(통합 주장과 현재 연결 범위 차이); 제한된 개별 시연 자체는 유효
- 우선순위: 이번 단계 보완 — 포트폴리오·문서의 통합 완성 주장 범위를 정정. 새 물리 학습의 선행 필수는 아님.
- 근거 수준: 정적 확인 + checkpoint metadata 실제 읽기
- 위치: `run_demo.sh:5-12`, `cognitive_ai/evaluation/simulate_9_innings.py:14-27`, `evaluate_base_stealing.py:15-34,46-66`, `simulate_full_match.py:15-18,43-48`; 주장 `README.md:5,25,30,43,49`, `docs/PAPER.md:60,123-134`
- 관찰한 사실: 셸이 세 독립 프로세스를 순서 실행. 9이닝 random 사건; 도루는 runner target distance<1로SAFE, catcher 모델 미사용. full match는3개 단일 투구 시도이며 counts/bases가 없다. 기본 데모는12D mocap 타자, mega는48D 별도 저장 정책.
- 문제가 되는 이유: 경기 통합·대응 전략·9이닝 정책 운용·4프레임 개선이 같은 데모로 입증되지 않는다. `run_demo.sh`는 9이닝 stdout을 head25로 자르며 성공 exit 검사를 하지 않는다.
- 영향을 받는 결과·주장: fully integrated broadcast, Frame Stacking의 현재 데모 사용, 도루 상대 경쟁, 자율 9이닝 경기.
- 최소 재현 방법: 위 import/call graph와 사용된 checkpoint 경로·shape 기록; 도루 스크립트에서 c_model.predict/c_vec.step 호출이 없는지 확인.
- 구체적인 보완 행동: 우선 설명을 독립 구성요소 데모로 수정. 실제 통합이 목적이면 동일 게임 state와 pitch event 계약을 정의하고 catcher throw/runner 도달 시간 경쟁을 별도 태스크로 설계. mega 비교는 별도 평가 진입점을 추가하고 frame stack reset을 동일 적용.
- 보완 후 통과 기준: 통합 주장 시 각 pitch result가 game counts/bases에 실제 전달됨을 event log로 추적, 유효 종결까지 실행; 도루 SAFE/OUT이 수비행동 변화에 반응. 제한된 프로젝트를 선택하면 위 통합 주장을 제거하는 것으로 통과 가능.
- 아직 모르는 부분: 다른 외부 구현/과거 실험 존재 여부. 현재 문서가 9이닝을 독립 텍스트 시연이라 명시한 부분(PAPER:134)은 그 범위에서는 사실과 맞음.

### TE-06. mega best 선택의 평가 통계 갱신과 checkpoint/normalizer 저장 시점 분리

- 분류: 확인된 문제(평가 통계 갱신); 확인 불가(best 시점 통계와 저장 통계의 수치적 차이/성능 영향)
- 우선순위: 진행 차단 — 동일 조건 best 선정 및 기존 best 수치의 정확한 재현 주장을 막음. 학습 실행 자체는 가능.
- 근거 수준: 정적 확인 + 실제 실행 확인(SB3 synthetic wrapper default); checkpoint ZIP metadata
- 위치: `cognitive_ai/training/train_mega_architecture.py:50-73,83-101`; `train_mocap_batter.py:31-47`; `train_mocap_pitcher.py:28-45`; 설치 SB3 `common/callbacks.py:450-454,465-498,518-526`
- 관찰한 사실: mega eval VecNormalize에 training=False/norm_reward=False가 없어 default True/True. 동일한 초기 통계를 EvalCallback이 평가 직전에 sync하는 동작은 존재한다(따라서 '통계 미동기화'라고 주장하면 틀림). 그 뒤 평가 reset/step이 통계를 다시 갱신하고 normalized return으로 best를 선택한다. best model은 callback 시점, normalization은 learn 종료 후에만 저장. mocap도 best 모델과 종료 통계를 분리 저장한다.
- 문제가 되는 이유: 평가 정책 입력 transform이 평가 에피소드에 따라 변하고 reward scale도 변함. early best weight와 final observation statistics가 같음을 보장하지 못함.
- 영향을 받는 결과·주장: mega 개선, best 성능, reproducible inference pairing.
- 최소 재현 방법: `vecenv_contract_probe.py`에서 mega와 동일 생성 인자 사용. obs count0.0001→2.0001, return count0.0001→1.0001, raw reward5→returned10 확인. 이는 합성 예시 값이며 프로젝트 보상 변화량이 아님.
- 구체적인 보완 행동: 평가 training=False,norm_reward=False; new-best callback에서 model+normalizer+config+평가 seed목록을 함께 저장. 최종 holdout 평가와 checkpoint 선택 평가 분리.
- 보완 후 통과 기준: 평가 전후 obs_rms/ret_rms 불변, 동일 checkpoint bundle 재실행 시 동일 입력 변환, raw return과 task metrics 기록. best 시점의 통계가 없으면 기존 짝의 정확 재현 불가를 명시.
- 아직 모르는 부분: pkl의 실제 통계별 생성 step, 기존 best와 통계가 우연히 거의 같은지, 독립 holdout 존재 여부. 본 하위 작업은 기존 로그 해석을 제외하며, 실제로 확인된 mega NPZ/TensorBoard 및 runs NPZ 해석은 `claims_history` 검토와 종합 보고서를 참조한다. best 시점별 정규화 통계 원본의 대응이 확인되지 않아 저장 시점 차이의 실제 성능 영향은 미확인이다.

### TE-07. adversarial wrapper는 현재 Match API와 맞지 않는 미연결 stub

- 분류: 확인된 문제(구현 API); 통합 self-play 성과 주장 여부는 현재 주요 문서에서 별도로 확인하지 못함
- 우선순위: 이후 개선 — 이 파일로 학습을 시작할 때는 실행 차단. 기본 데모에는 영향 없음.
- 근거 수준: 정적 확인
- 위치: `cognitive_ai/envs/adversarial_match_env.py:20-22,31-42,44-60`
- 관찰한 사실: reset을 (obs,info)로 해체하지만 실제 dict 2개 키를 해체하여 문자열을 받음. action12/obs26은 실제 투수4/16과 다름. 타자 inference는pass. step은5개 return을 기대하지만 actual3개. ball_trajectory attribute와 has_hit도 현재 Match에 없음.
- 문제가 되는 이유: 해당 파일의 docstring처럼 frozen 타자와 경쟁하는 학습을 수행하지 못함. 하지만 불러오지 않는 stub의 결함을 현재 기본 데모 실패로 확장하면 안 됨.
- 영향을 받는 결과·주장: 이 wrapper를 향후 재사용하는 계획과 adversarial 학습 기능.
- 최소 재현 방법: 현재 Match.reset/step 반환 계약과 각 호출을 대조. 무작정 학습을 실행할 필요 없음.
- 구체적인 보완 행동: 연구 질문을 먼저 정하고 current Match 계약에 맞춘 작고 별도 adapter를 작성; frozen opponent predict와 frame stack 계약 검증.
- 보완 후 통과 기준: reset16D, action4D, step Gym 5-return; opponent action이 실제 결과에 영향; opponent weight와 통계 불변.
- 아직 모르는 부분: 이 stub의 당시 개발 의도/이해 수준, 과거 다른 Match API에서 실행되었는지.

### TE-08. 심판의 점 샘플 검사와 '밀리초 단위 체적 교차' 표현 차이

- 분류: 확인된 문제(연속 궤적 교차 주장과 구현 차이); 실제 정책에서 오판 빈도는 미검증 가정
- 우선순위: 이번 단계 보완 — 엄밀한 strike 판정 주장 보완.
- 근거 수준: 정적 확인 + 합성 실제 실행
- 위치: `cognitive_ai/envs/baseball_rules.py:13-28`, `cognitive_ai/evaluation/simulate_full_match.py:60-65`; `docs/PAPER.md:118`
- 관찰한 사실: 받은 좌표점 중 하나라도 box 내부면STRIKE. 선분 교차는 검사 안 함. Match timestep0.005×frame_skip2=외부 step0.01초이고 evaluator는 그때만 좌표 수집. 합성 y=+0.30→-0.30, x0/z0.8의 box 관통 선분을BALL 처리.
- 문제가 되는 이유: 충분히 빠른 공/샘플 간격에서 존을 건너뛰어도 누락 가능. 구 반지름도 고려하지 않는 공 중심 point-box 모델이다.
- 영향을 받는 결과·주장: AI umpire의 정확성. 현재 broadcaster의 terminal-state 결함을 고쳐도 이 샘플링 한계가 남음.
- 최소 재현 방법: `rules_and_checkpoint_probe.py` sampled_segment_crosses_zone.
- 구체적인 보완 행동: 연속 구간-존 교차 또는 physics substep crossing 이벤트 기록; ball-radius 포함 여부를 태스크 정의에 명시.
- 보완 후 통과 기준: 직선 관통/경계/비관통 및 빠른 통과 사례의 기대값 일치. 정책 episode에서 빈도 별도 측정.
- 아직 모르는 부분: 현재 checkpoint 투구의 실제 누락 빈도. 합성 사례를 정책 오판률로 보고하지 않음.

## 추가 확인·해석 주의

- seed: `PitcherEnv.reset:88-105`, `BaseballMatchEnv.reset:108-137`, `CatcherEnv.reset:40-49`는 super.reset(seed=seed)를 호출하지만 실제 난수는 전역 np.random. mega make_env에서 reset(seed+rank)하더라도 그것만으로 이 난수를 고정하지 않는다. PPO 생성 seed도 없고 ZIP seed도null. 루트가 동적 반복 seed 검사 담당. FielderEnv는 np.random.seed를 직접 사용해 전역 상태를 변경하므로 독립 환경간 격리와 별개다.
- best라는 파일명만으로 best selection을 의미하지 않는다. MLB batter(:90-92), catcher/runner(:21-25), fielder(:32-35)는 마지막 학습 상태를 best_model로 저장한다. `train_mlb_pitcher.py:44`는 일반 pitcher와 같은 `pitcher_final_model` 경로에 저장하므로 사용자가 순서대로 재실행하면 기존 final 파일을 덮는다(이번 감사에서는 실행하지 않음).
- `simulate_mlb_match.py:141`: 타율 산식 HITS/(num_at_bats-WALKS). 단일 pitch BALL을 WALK로, 단일 called strike를 strikeout로 세는 :120-123이므로 실제 경기 타율/삼진률이 아니다. `DOUBLE`은 HITS 분기에 없어 OUTS로 집계(:115-125). 고정15회 수치라도 분모/사건 정의를 먼저 바꿔야 한다.
- `BaseballUmpire.check_hit_outcome:55`은120m 초과HR, `BaseballMatchEnv._evaluate_outcome:313`은60m와높이>2.5HR. 서로 다른 단순 판정 기준이다. 어느 규칙을 authoritative로 쓰는지 정하지 않으면 동일 타구도 라벨이 다를 수 있다.
- 문서 Phase 기록은 환경/보상/관측/물리 조건 변화를 일부 추적할 수 있게 한다. 다만 같은 조건의 대조군, 시드목록, 정확한 코드·정규화 hash, best 선정자료가 없어서 관측 정규화·프레임스택·학습량 각각의 인과적 개선은 분리되지 않는다. 당시 의도를 단정하지 않는다.

## 이 하위 작업의 실행 기록

실행은 기존 파일 덮어쓰기 없이 신규 `_audit/20260926_013033/scripts/`와 `logs/`에 한정. 설치 없음, 네트워크 없음, GPU 없음, 렌더 없음, 정책 학습 없음. 기존 스크립트의 main은 실행하지 않음. import 대상 순수 룰 소스와 SB3 wrapper 구현을 먼저 읽음. `PYTHONDONTWRITEBYTECODE=1`로 소스 폴더 pycache 기록 방지.

| 실행 명령(저장소 루트에서) | 코드·가중치·설정 식별 | 환경 | 기대 결과 | 실제 결과 | 로그/한계 |
|---|---|---|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python _audit/20260926_013033/scripts/rules_and_checkpoint_probe.py > _audit/20260926_013033/logs/rules_and_checkpoint_probe.json` | 현재 두 rules .py, 모든 로컬 checkpoints ZIP data 읽기; 각 ZIP SHA256 출력 | Python3.11.5, macOS27 arm64, NumPy2.4.6; 약0.2초 | foul 카운트·단순54아웃·점샘플 판정과 ZIP metadata 확인 | 일반 foul3사례 중2불일치; 54outs→Top10 정상; box 관통 선분BALL; ZIP metadata 추출 성공 | `logs/rules_and_checkpoint_probe.json`; 합성 입력은 정책 성공률아님, pickle/weight load 안 함 |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python _audit/20260926_013033/scripts/vecenv_contract_probe.py > _audit/20260926_013033/logs/vecenv_contract_probe.json` | 감사 자체 OneStepEnv, 설치 SB3 wrapper; 모델/가중치 없음 | Python3.11.5, SB3 2.9.0, Gymnasium1.3.0, NumPy2.4.6; 약1.2초 | DummyVecEnv autoreset과 VecNormalize eval default 확인 | terminal99, raw/returned reset=-10; trainingTrue, stats counts 증가, reward5→10 | `logs/vecenv_contract_probe.json`; 2개 one-step 합성 에피소드, 실제 정책 성능과 무관 |

ZIP metadata에서 읽은 주요 저장 시점:

| 파일 | 관측/행동 | num_timesteps | total_timesteps | 의미 |
|---|---|---:|---:|---|
| mega_batter/best_model.zip |48/3|1,920,000|2,000,000|4프레임 입력과 대규모 실행에 부합하는 저장 metadata; 성공률 증거는 아님|
| mega_pitcher/best_model.zip |16/4|1,600,000|2,000,000|best가 학습 완료 시점과 다름|
| mocap_batter_best/best_model.zip |12/3|36,000|60,000|기본 데모는 이 정책, 단일 프레임|
| mocap_pitcher_best/best_model.zip |16/4|56,000|60,000|기본 데모 투수; best 통계 동시저장없음|

## 재사용 판단에 기여하는 근거

기존 PPO·VecNormalize·키프레임 매개변수 태스크, XML·카메라·렌더 및 단순 룰 엔진은 선택적으로 재사용 가능하다. 확인된 계약/평가 결함은 위치가 구체적이라 수정 대상으로 한정 가능하며 이 증거만으로 전체 폐기할 근거는 없다. 그러나 목표가 '물리적으로 충실한 전신 학습과 균형'이면 현재 기본 데모의 고수준 매개변수·운동학 경로와 별도 태스크 정의가 필요하다(물리 분석은 루트 감사 범위). 현재 태스크를 명확히 축소하면 B(핵심 계약·평가 수정), 전신 제어가 목표면 C(자산 재사용 후 태스크 재설계)를 비교할 수 있다. D를 바로 택할 근거는 이 검토만으로 부족하다.

작은 결정 실험: 관측 계약과 평가 입력을 감사 adapter에서 수정한 버전, 현행 버전, 유효한 고정/규칙 정책을 동일 seed·target/pitch_type 목록에서 headless 비교한다. 이것은 기존 정책의 조건 변경 민감도 검사이며 기존 정책의 재학습 없는 공정한 ablation으로 표현하지 않는다. 순수 타이밍/aim 매개변수 태스크에서 RL 필요성은 baseline 없이 검증되지 않았지만 RL 사용 자체가 오류는 아니다.
