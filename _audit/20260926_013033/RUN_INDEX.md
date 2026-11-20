# 감사 산출물 안내

- `AUDIT_REPORT.md`: 결론, 검사 범위, 태스크, 주장 비교, 15개 발견, 실행·기준선, 재사용 판단.
- `logs/initial_manifest.json`, `final_integrity.json`: 검사 HEAD 및 원본 tracked 파일 보존 확인.
- `logs/runtime_results.jsonl`: 가중치/정규화 식별, root smoke·기준선·경기·합성 검사 원기록.
- `logs/commands.jsonl`: root 실행의 정확한 명령, cwd, 환경변수, timeout 결과와 출력 위치.
- `logs/physics_*.jsonl`, `fielder_trace.jsonl`, 각 stderr: 수비·포수·주자·티볼·인지 경로 검사.
- `logs/rules_and_checkpoint_probe.json`, `vecenv_contract_probe.json`: 룰·SB3 계약 단위검사.
- `logs/pip_freeze.txt`, `hardware.json`: 실제 실행 환경. 설치나 업그레이드는 하지 않음.
- `notes/claims_history.md`, `physics_tasks.md`, `training_eval.md`: 분야별 추적 근거와 추가 명령.

## 재실행

원본 저장소 루트에서 다음과 같이 실행한다. 감사 디렉터리의 읽기용 `shared_assets`, `checkpoints`, `data/textures` 링크가 필요하다. 현재 실행 디렉터리에는 이미 생성되어 있다. 로그 접미사는 기존 파일과 겹치지 않는 이름을 사용한다.

```sh
python3 _audit/20260926_013033/scripts/run_bounded.py smoke _recheck_01
python3 _audit/20260926_013033/scripts/run_bounded.py match _recheck_01
python3 _audit/20260926_013033/scripts/run_bounded.py followup _recheck_01
```

`followup`에는 올바른 80km/h deep 정규화 파일을 사용한 비교가 있다. 최초 `baseline` 모드의 machine80 항목은 감사 당시 잘못 짝지은 norm 경로를 그대로 보존한 기록이다. 해당 3/10은 최종 결과에서 제외했고 올바른 짝으로 얻은 2/10을 보고했다. 최초 실행 오류와 정정 과정을 삭제하지 않았다.

추가 실행은 `runtime_results.jsonl`에 append되므로 최초 감사의 고정 결과와 구분해야 한다. 파일을 완전히 새로 보존하려면 별도 감사 실행 디렉터리에 스크립트·읽기 링크를 복제해 실행한다. 기존 로그에 같은 이름으로 redirect하지 않는다.

보조 검사는 감사 실행 디렉터리에서 기존 Python을 사용한다. 환경별 step cap과 120초 중단 조건이 있다. `cognitive`는 현재 세션의 렌더 연결 제약으로 실패할 수 있으며 이를 물리 로직 전체의 실패로 해석하지 않는다.

```sh
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR="$PWD/logs/mpl" ../../.venv/bin/python -B scripts/physics_probe.py --task fielder
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR="$PWD/logs/mpl" ../../.venv/bin/python -B scripts/physics_contracts.py
```

이 스크립트는 학습하지 않고 원본을 저장하지 않는다. 원본 `run_demo.sh`를 실행하면 기존 영상 경로에 저장할 수 있으므로 이번 감사에서는 호출하지 않았다. 합성 상태·렌더 stub·weld 조건변화 검사는 정책의 실제 성공 횟수에 넣지 않는다.
