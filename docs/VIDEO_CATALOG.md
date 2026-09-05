# 🎬 Unitree H1 Baseball AI - Video Catalog

본 문서는 프로젝트의 각 Phase별 학습 결과와 실증 시뮬레이션 비디오(mp4)를 메타데이터와 함께 표준화된 형식으로 기록한 카탈로그입니다.

| Phase | 파일명 | 학습 모델 / 체크포인트 | 평가 지표 (Metric) | 설명 및 특징 |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1-A** | `teeball_evaluation.mp4` | `teeball_best` | 타격률 90.0% | 정지된 티볼(Tee-ball) 타격 훈련. 5단계 키네틱 체인 모션 검증. |
| **Phase 1-B** | `phase_1_1_soft_toss_initial.mp4` | `soft_toss_best` | 타격률 70.0% | 28km/h의 느린 소프트토스 타격. 낙하 궤적 및 도달 시간(`t_remain`) 인지. |
| **Phase 1-C** | `phase_2_2_pitching_80kmh.mp4` | `fast_pitching_best` | 타격률 60.0% | 15m 거리에서 날아오는 50~80km/h 피칭머신 직구 타격 및 타이밍 훈련. |
| **Phase 1-D** | `phase_1_4_breaking_ball.mp4` | `breaking_ball_best` | 타격률 66.7% | 직구, 슬라이더, 커브볼 3대 구종 및 좌우/상하 무작위 코스 대응 스윙. |
| **Phase 2** | `phase_2_3_pitcher_final.mp4` | `pitcher_best` | 100% 제구 / 84.4km/h | H1 로봇이 마운드에서 직접 와인드업 투구를 수행하여 스트라이크 존을 찌르는 실증 비디오. |
| **Phase 3** | `phase_3_1_match_duel.mp4` | `pitcher_best` vs `match_batter` | 15타석 투타 맞대결 | 투수와 타자 로봇이 동일 물리 공간에서 84.4km/h로 대결. 방송 HUD 스코어보드 오버레이 적용. |
| **Phase 4** | `phase_4_1_mlb_match.mp4` | `mlb_pitcher` vs `mlb_batter` | 178km/h / 볼넷 3회 | 메이저리그급 초강속구(178km/h) 및 매그너스 궤적(슬라이더/커브) 구사. 타자의 선구안(Walk) 확인. |
| **Phase 5** | `phase_5_1_stadium_match.mp4` | `mlb_pitcher` vs `mlb_batter` | 137.7km/h 타구속도 | 바람(Wind)과 공기 저항(Drag)이 적용된 초고해상도 3D 잔디구장에서의 대결 시뮬레이션. |

---
*모든 비디오 파일은 `.gemini/antigravity/brain/` 내부의 아티팩트 저장소 및 `data/eval_videos/` 디렉토리에 보존되어 있습니다.*

| `phase_6_2_mocap_match.mp4` | 3b74... | Phase 6: Pro MoCap Imitation | **하이-레그킥 투구 및 파워 어퍼스윙 타격 폼**이 적용된 극한의 실감형 로봇 대결 영상 | `mocap_pitcher_best`, `mocap_batter_best` |
| `phase_7_1_wheeled_fielder.mp4` | 3b74... | Phase 7: Wheeled Fielder | 다리 대신 바퀴를 달고 왼손에 글러브를 장착한 수비수가 뜬공을 추적하여 캐치하는 AI | `fielder_best` |