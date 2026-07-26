# ⚾ Baseball RL Simulator & Game 실행 가이드 (EXECUTION_GUIDE.md)

본 가이드는 **Baseball RL 시뮬레이터 프로젝트**의 다양한 실행 모드(인터랙티브 게임, 실시간 3D 대시보드, 강화학습 트레이너) 사용법을 안내합니다.

---

## ⚙️ 1. 사전 준비 (가상환경 활성화)

터미널을 열고 프로젝트 디렉토리로 이동한 뒤 가상환경을 활성화합니다.

```bash
# 디렉토리 이동
cd /Users/jmjeon/Desktop/baseball

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 의존성 패키지 설치 (필요시)
pip install -r requirements.txt
```

---

## ⚾ 2. 인터랙티브 야구 게임 (`game.py`)

AI 에이전트 간의 관전 대결 또는 유저가 투수/타자로 직접 조작할 수 있는 터미널 기반 게임 엔진입니다.

### 2.1 주요 실행 명령어

#### ① AI vs AI 관전 모드 (기본)
```bash
python game.py --role spectator
```
- AI 투수와 AI 타자의 대결을 터미널 그래픽으로 관전합니다.

#### ② 유저 타자 모드 (직접 스윙 조작)
```bash
python game.py --role batter
```
- 투구가 도착할 때 스윙 여부, 타격 방향(당기기/밀어치기), 배트 각도, 높이를 입력합니다.

#### ③ 유저 투수 모드 (직접 구종/코스 조작)
```bash
python game.py --role pitcher
```
- 투구 속도, 좌우/상하 코스, 스핀량, 회전축을 직접 지정하여 투구합니다.

#### ④ 학습된 체크포인트(모델)로 게임 실행
```bash
python game.py --checkpoint checkpoints/checkpoint_ep20.pt
```

---

### 2.2 주요 옵션 (Arguments)

| 옵션 | 설명 | 기본값 | 예시 |
| :--- | :--- | :--- | :--- |
| `--role` | 실행 역할 지정 (`spectator`, `pitcher`, `batter`) | `spectator` | `--role batter` |
| `--at-bats` | 진행할 총 타석 수 | `9` | `--at-bats 5` |
| `--delay` | AI 행동 간 딜레이 초 (관전 모드 속도 조절) | `1.0` | `--delay 0.3` |
| `--checkpoint` | 로드할 PyTorch 모델 체크포인트 파일 경로 | `None` (랜덤 가중치) | `--checkpoint checkpoints/checkpoint_ep20.pt` |

---

## 🌐 3. 실시간 3D 대시보드 (`simulator/dashboard.py`)

Dash + Plotly 기반 실시간 모니터링 웹 대시보드입니다.

### 3.1 실행 방법

```bash
python -m simulator.dashboard
```
또는
```bash
python simulator/dashboard.py
```

### 3.2 브라우저 접속
서버 실행 후 웹 브라우저에서 아래 주소로 접속합니다:
👉 **[http://127.0.0.1:8050](http://127.0.0.1:8050)**

### 3.3 대시보드 화면 구성
1. **3D Trajectory Viewer**: 공의 3D 궤적, 마그누스 힘 벡터, 배트 스윙 궤면 관찰 (마우스로 360도 회전 및 확대/축소 가능)
2. **Exit Dynamics Dashboard**: 타구 속도(Exit Velocity), 발사각(Launch Angle), 스프레이 각도 분석
3. **Strike Zone Heatmap**: 투구 위치 분배 및 안타/삼진/홈런 스트라이크존 오버레이
4. **Learning Progress Monitor**: 투수 vs 타자 승률, 보상(Reward) 변화 그래프

---

## 🤖 4. Self-Play 강화학습 트레이너 (`training/trainer.py`)

투수 에이전트와 타자 에이전트가 교대 학습을 진행하며 서로 성장하는 Self-Play PPO 학습 엔진입니다.

### 4.1 주요 실행 명령어

#### ① 새로 학습 시작 (기본 1000 에피소드)
```bash
python -m training.trainer --episodes 1000
```

#### ② 빠른 학습 테스트 (100 에피소드, Warmup 20 에피소드)
```bash
python -m training.trainer --episodes 100 --warmup 20
```

#### ③ 이전 체크포인트에서 학습 이어하기
```bash
python -m training.trainer --resume checkpoints/checkpoint_ep20.pt --episodes 500
```

---

### 4.2 주요 옵션 (Arguments)

| 옵션 | 설명 | 기본값 | 예시 |
| :--- | :--- | :--- | :--- |
| `--episodes` | 총 학습할 에피소드 수 | `1000` | `--episodes 500` |
| `--warmup` | 기초 봇 상대 초기 학습 에피소드 수 | `100` | `--warmup 50` |
| `--lr` | Learning Rate (학습률) | `0.0003` | `--lr 0.0001` |
| `--resume` | 이어받아 학습할 체크포인트 경로 | `None` | `--resume checkpoints/checkpoint_ep20.pt` |

---

## 📁 5. 파일 및 데이터 구조 안내

- **`checkpoints/`**: 학습된 모델 가중치 파일 (`checkpoint_ep20.pt` 등)이 저장됩니다.
- **`data/`**:
  - `pitch_log.json`: 최근 투구 궤적 및 결과 데이터 (대시보드와 공유)
  - `training_metrics.json`: 학습 에피소드별 승률/보상 데이터 (대시보드와 공유)
- **`envs/`**: 물리 시뮬레이션 환경 (공 궤적, 마그누스 효과, 타격 메커니즘)
- **`training/`**: PPO 신경망 네트워크(`networks.py`), 리플레이 버퍼(`replay_buffer.py`), 트레이너(`trainer.py`)
