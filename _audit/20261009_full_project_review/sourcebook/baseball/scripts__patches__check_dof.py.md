# baseball/scripts/patches/check_dof.py

원본: [scripts/patches/check_dof.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/check_dof.py)

SHA256: `a63ffc6bd60f439c0c58845756da79d1d64c25f85c76dfbf845719fbb1cb2f7f`

전체 4행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | model = mujoco.MjModel.from_xml_path("shared_assets/h1_baseball_match.xml")
    3 | for i in range(model.nv):
    4 |     print(f"DOF {i}: {mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, model.dof_jntid[i])}")
````
