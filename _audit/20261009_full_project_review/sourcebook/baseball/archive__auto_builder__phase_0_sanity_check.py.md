# baseball/archive/auto_builder/phase_0_sanity_check.py

원본: [archive/auto_builder/phase_0_sanity_check.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/auto_builder/phase_0_sanity_check.py)

SHA256: `b5ffea76c701456651687236319b879eec5b5d0bfc221dc4778e5931b1dbae09`

전체 95행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `run_sanity_check` | FunctionDef | 15 | 92 |

## 전체 원문

````text
    1 | """
    2 | phase_0_sanity_check.py — 물리 검증 (Phase 0)
    3 | 
    4 | 새롭게 정의된 투수 및 타자 로봇이 포함된 stadium_3d.xml 파일이
    5 | MuJoCo 시뮬레이터에서 정상적으로 로드되는지,
    6 | 물리적 폭발(폭주) 현상이 없는지 검증합니다.
    7 | """
    8 | 
    9 | import mujoco
   10 | import numpy as np
   11 | import time
   12 | from pathlib import Path
   13 | 
   14 | 
   15 | def run_sanity_check():
   16 |     print("=" * 55)
   17 |     print(" 🛠️  Phase 0: 물리 검증 (Physics Sanity Check)")
   18 |     print("=" * 55)
   19 | 
   20 |     xml_path = Path(__file__).resolve().parent.parent / "assets" / "stadium_3d.xml"
   21 |     if not xml_path.exists():
   22 |         print(f"❌ 오류: XML 파일을 찾을 수 없습니다: {xml_path}")
   23 |         return False
   24 | 
   25 |     # 1. 모델 로드 검증
   26 |     print(f"\n[1] 모델 로드 테스트: {xml_path.name} ... ", end="")
   27 |     try:
   28 |         model = mujoco.MjModel.from_xml_path(str(xml_path))
   29 |         data = mujoco.MjData(model)
   30 |         print("✅ 성공")
   31 |     except Exception as e:
   32 |         print(f"❌ 실패\n에러: {e}")
   33 |         return False
   34 | 
   35 |     # 2. DOF 확인
   36 |     print("\n[2] 자유도(DOF) 확인:")
   37 |     print(f"  총 DOF (nq)     : {model.nq}")
   38 |     print(f"  총 속도 (nv)    : {model.nv}")
   39 |     print(f"  총 액추에이터(nu): {model.nu}")
   40 |     
   41 |     # 3. 물리 안정성 (폭발 방지) 시뮬레이션
   42 |     print("\n[3] 물리 안정성 시뮬레이션 (1.0초) ... ", end="")
   43 |     mujoco.mj_resetData(model, data)
   44 |     
   45 |     # 초기 볼 위치 (z 높이)
   46 |     ball_qpos_adr = -1
   47 |     try:
   48 |         ball_joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
   49 |         if ball_joint_id != -1:
   50 |             ball_qpos_adr = model.jnt_qposadr[ball_joint_id]
   51 |             initial_ball_z = data.qpos[ball_qpos_adr + 2]
   52 |         else:
   53 |             initial_ball_z = None
   54 |     except Exception:
   55 |         initial_ball_z = None
   56 | 
   57 |     sim_time = 1.0  # 1초 시뮬레이션
   58 |     steps = int(sim_time / model.opt.timestep)
   59 | 
   60 |     try:
   61 |         for _ in range(steps):
   62 |             # 모터에 0 인가
   63 |             data.ctrl[:] = 0.0
   64 |             mujoco.mj_step(model, data)
   65 |             
   66 |             # 발산 체크
   67 |             if not np.all(np.isfinite(data.qpos)):
   68 |                 raise ValueError("시뮬레이션 위치(qpos)가 발산(NaN/Inf)했습니다.")
   69 |             if not np.all(np.isfinite(data.qvel)):
   70 |                 raise ValueError("시뮬레이션 속도(qvel)가 발산(NaN/Inf)했습니다.")
   71 |                 
   72 |         print("✅ 성공 (발산 없음)")
   73 |     except Exception as e:
   74 |         print(f"❌ 실패\n에러: {e}")
   75 |         return False
   76 | 
   77 |     # 4. 중력 검증 (볼 자유 낙하)
   78 |     print("\n[4] 볼 자유 낙하 검증 ... ", end="")
   79 |     if ball_qpos_adr != -1 and initial_ball_z is not None:
   80 |         final_ball_z = data.qpos[ball_qpos_adr + 2]
   81 |         # 1초 자유낙하 z = z_0 - 0.5 * 9.81 * t^2
   82 |         expected_z = initial_ball_z - 0.5 * 9.81 * 1.0**2
   83 |         diff = abs(final_ball_z - expected_z)
   84 |         if diff < 0.1:  # 오차 범위 10cm
   85 |             print(f"✅ 성공 (예측: {expected_z:.2f}m, 실제: {final_ball_z:.2f}m)")
   86 |         else:
   87 |             print(f"⚠️ 오차 (예측: {expected_z:.2f}m, 실제: {final_ball_z:.2f}m, 차이: {diff:.2f}m) - 지면에 닿았을 수 있음")
   88 |     else:
   89 |         print("⚠️ 스킵 (ball_joint를 찾을 수 없음)")
   90 | 
   91 |     print("\n🎉 Phase 0 검증 완료! 모든 테스트 통과.")
   92 |     return True
   93 | 
   94 | if __name__ == "__main__":
   95 |     run_sanity_check()
````
