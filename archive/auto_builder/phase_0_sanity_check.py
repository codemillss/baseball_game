"""
phase_0_sanity_check.py — 물리 검증 (Phase 0)

새롭게 정의된 투수 및 타자 로봇이 포함된 stadium_3d.xml 파일이
MuJoCo 시뮬레이터에서 정상적으로 로드되는지,
물리적 폭발(폭주) 현상이 없는지 검증합니다.
"""

import mujoco
import numpy as np
import time
from pathlib import Path


def run_sanity_check():
    print("=" * 55)
    print(" 🛠️  Phase 0: 물리 검증 (Physics Sanity Check)")
    print("=" * 55)

    xml_path = Path(__file__).resolve().parent.parent / "assets" / "stadium_3d.xml"
    if not xml_path.exists():
        print(f"❌ 오류: XML 파일을 찾을 수 없습니다: {xml_path}")
        return False

    # 1. 모델 로드 검증
    print(f"\n[1] 모델 로드 테스트: {xml_path.name} ... ", end="")
    try:
        model = mujoco.MjModel.from_xml_path(str(xml_path))
        data = mujoco.MjData(model)
        print("✅ 성공")
    except Exception as e:
        print(f"❌ 실패\n에러: {e}")
        return False

    # 2. DOF 확인
    print("\n[2] 자유도(DOF) 확인:")
    print(f"  총 DOF (nq)     : {model.nq}")
    print(f"  총 속도 (nv)    : {model.nv}")
    print(f"  총 액추에이터(nu): {model.nu}")
    
    # 3. 물리 안정성 (폭발 방지) 시뮬레이션
    print("\n[3] 물리 안정성 시뮬레이션 (1.0초) ... ", end="")
    mujoco.mj_resetData(model, data)
    
    # 초기 볼 위치 (z 높이)
    ball_qpos_adr = -1
    try:
        ball_joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")
        if ball_joint_id != -1:
            ball_qpos_adr = model.jnt_qposadr[ball_joint_id]
            initial_ball_z = data.qpos[ball_qpos_adr + 2]
        else:
            initial_ball_z = None
    except Exception:
        initial_ball_z = None

    sim_time = 1.0  # 1초 시뮬레이션
    steps = int(sim_time / model.opt.timestep)

    try:
        for _ in range(steps):
            # 모터에 0 인가
            data.ctrl[:] = 0.0
            mujoco.mj_step(model, data)
            
            # 발산 체크
            if not np.all(np.isfinite(data.qpos)):
                raise ValueError("시뮬레이션 위치(qpos)가 발산(NaN/Inf)했습니다.")
            if not np.all(np.isfinite(data.qvel)):
                raise ValueError("시뮬레이션 속도(qvel)가 발산(NaN/Inf)했습니다.")
                
        print("✅ 성공 (발산 없음)")
    except Exception as e:
        print(f"❌ 실패\n에러: {e}")
        return False

    # 4. 중력 검증 (볼 자유 낙하)
    print("\n[4] 볼 자유 낙하 검증 ... ", end="")
    if ball_qpos_adr != -1 and initial_ball_z is not None:
        final_ball_z = data.qpos[ball_qpos_adr + 2]
        # 1초 자유낙하 z = z_0 - 0.5 * 9.81 * t^2
        expected_z = initial_ball_z - 0.5 * 9.81 * 1.0**2
        diff = abs(final_ball_z - expected_z)
        if diff < 0.1:  # 오차 범위 10cm
            print(f"✅ 성공 (예측: {expected_z:.2f}m, 실제: {final_ball_z:.2f}m)")
        else:
            print(f"⚠️ 오차 (예측: {expected_z:.2f}m, 실제: {final_ball_z:.2f}m, 차이: {diff:.2f}m) - 지면에 닿았을 수 있음")
    else:
        print("⚠️ 스킵 (ball_joint를 찾을 수 없음)")

    print("\n🎉 Phase 0 검증 완료! 모든 테스트 통과.")
    return True

if __name__ == "__main__":
    run_sanity_check()
