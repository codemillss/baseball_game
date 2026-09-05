# 🧪 Unitree H1 Baseball AI - Experiment & Physics Log

본 문서는 프로젝트 진행 과정에서 조율된 시뮬레이터 물리 파라미터(Physics Parameter), 상태 관측치(Observation Space), 그리고 각 Phase별 핵심 실험 메트릭을 표준 템플릿에 따라 영구 기록합니다.

---

## 📌 [Phase 1] 지능형 타자 (Batter) 궤적 및 타이밍 학습
### 1-A. 티볼 (Tee-ball)
* **환경 세팅:** `teeball_env.py` (공 질량 `0.001`kg 조정으로 중력 상쇄)
* **Action Space (2D):** `[swing_trigger, target_z_delta]`
* **결과:** 정지 상태의 타겟을 5단계 키네틱 체인으로 90.0% 정타 타격.

### 1-B. 소프트토스 (Soft Toss)
* **물리 파라미터:** 공 초기 속도 `vy = -7.0 ~ -9.0 m/s` (약 25~32 km/h)
* **Observation (8D):** 공 위치(3D), 공 속도(3D), 도달 시간(`t_remain`), 예상 홈플레이트 통과 높이(`pred_z`)
* **결과:** `VecNormalize` 스케일링 도입 후 70.0% 타격 성공률 달성.

### 1-C. 피칭 머신 직구 (Fast Pitching)
* **물리 파라미터:** 투구 거리 `15m`, 구속 `50 ~ 80 km/h`
* **Observation (8D):** 체공 시간이 0.6초로 짧아짐에 따라 스윙 타이밍을 0.05초 단위로 포착하는 훈련 집중.
* **결과:** 60.0% 타격률.

### 1-D. 3차원 변화구 (Breaking Balls)
* **환경 세팅:** `breaking_ball_env.py` (직구 40%, 슬라이더 35%, 커브 25%)
* **물리 파라미터 (Magnus Effect):** 슬라이더(X축 가속도 2.5~4.0), 커브(Z축 중력가속도 +3.5 추가)
* **결과:** 15회 평가 중 10회 컨택 성공 (성공률 66.7%). 몸통 회전(Yaw) 제어 검증.

---

## 📌 [Phase 2] 휴머노이드 투수 (Embodied Pitcher)
* **환경 세팅:** `h1_pitcher.xml` (마운드 `y=10.0m`, 오른손-공 `Weld Equality Constraint`)
* **Action Space (4D):** `[릴리스 타이밍, 숄더 피치(상하), 몸통 요(좌우), 투구 파워]`
* **결과:** 15회 실증 평가에서 **스트라이크 존 제구율 100.0%**, 평균 구속 **84.4 km/h** 달성.

---

## 📌 [Phase 3] 투타 AI 실시간 맞대결 (Full Match)
* **환경 세팅:** `h1_baseball_match.xml` (투수 및 타자 로봇 동시 렌더링)
* **타자 타석 위치 보정:** 헛스윙 방지를 위해 타자 골반 위치를 `pos="-0.70 -0.45 0.82"`로 전방 이동.
* **결과:** 투타 15타석 대결 시뮬레이션 및 HUD 중계. 타자가 84.4km/h 공에 51.6km/h 타구 속도 궤적 생성.

---

## 📌 [Phase 4] 메이저리그(MLB) 수준 투타 지능 고도화
* **환경 세팅:** `train_mlb_pitcher.py`, `train_mlb_batter.py`
* **투수 튜닝:** `vel_scale` 상한을 높여 최대 **178.3 km/h** 릴리스 파워 확보. 구종별 매그너스 힘(직구 상승, 커브 낙하 등) 무작위 부여.
* **타자 튜닝 (Plate Discipline):** 스트라이크 존(거리 오차 0.22 이내) 밖의 공에 스윙하면 `-100`, 스윙을 참으면 `+150` (볼넷) 보상 부여.
---

## 📌 [Phase 5] 3D 스타디움 및 정밀 물리 환경 도입 (Advanced 3D Stadium)
* **환경 세팅:** `h1_baseball_match.xml` (Full Stadium Mode)
* **초고해상도 텍스처(Textures):** 
  - `generate_image`를 통해 **고해상도 천연 잔디(Grass)** 및 **내야 흙(Dirt)** 텍스처 에셋(`grass.png`, `dirt.png`) 동적 생성 및 매핑.
  - 1루/2루/3루 베이스, 홈플레이트, 파울 라인, 그리고 65m 거대한 외야 펜스(Outfield Wall) 3D 구축.
* **환경 역학 엔진 (Aerodynamics & Physics):**
  - **Wind Vector:** 매 타석마다 $X, Y$ 축 각각 $-4.0 \sim +4.0$ m/s의 무작위 바람 팩터 주입.
  - **Drag Coefficient (공기 저항):** 공기 밀도와 항력 계수를 기반으로 계산된 공기 저항($a = -0.0054 |v| v$)을 0.005초 단위로 투구/타구에 역연산 적용.
  - **정교한 야구 규칙 판정:** 파울(Foul), 펜스 직격(Wall-ball Double), 담장 밖(Out of the Park Home Run) 판정 로직 도입 및 시뮬레이션 카메라 트래킹 타임 확장 (볼이 땅에 닿거나 담장을 넘어갈 때까지 추적).
* **결과:** 환경 물리 적용 후 137.7km/h의 강력한 타구 속도가 펜스 밖으로 뻗어나가는 등 AAA급 극사실적 야구 시뮬레이션 환경(stadium_match.mp4)을 완벽히 구축함.
