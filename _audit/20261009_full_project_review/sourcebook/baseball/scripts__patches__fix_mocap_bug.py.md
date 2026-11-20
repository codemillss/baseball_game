# baseball/scripts/patches/fix_mocap_bug.py

원본: [scripts/patches/fix_mocap_bug.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/fix_mocap_bug.py)

SHA256: `7b1b7770327c366d0db08a1b641f8e375f5186338df25545084b0e69d2320feb`

전체 5행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | 
    3 | model = mujoco.MjModel.from_xml_path("shared_assets/h1_baseball_match.xml")
    4 | for i in range(model.njnt):
    5 |     print(mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i))
````
