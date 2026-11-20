# baseball/cognitive_ai/scripts/test_cameras.py

원본: [cognitive_ai/scripts/test_cameras.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/test_cameras.py)

SHA256: `a87503ba6e2cffa7526f7bd829665da2f9d293a02cb1a1b08e0f951b6fcf2fb6`

전체 19행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | import cv2
    3 | 
    4 | model = mujoco.MjModel.from_xml_path("shared_assets/h1_baseball.xml")
    5 | data = mujoco.MjData(model)
    6 | mujoco.mj_forward(model, data)
    7 | 
    8 | renderer = mujoco.Renderer(model, height=480, width=640)
    9 | 
   10 | # Check all cameras
   11 | for cam_name in ["pitcher_cam", "batter_cam", "side_cam", "front_cam"]:
   12 |     try:
   13 |         renderer.update_scene(data, camera=cam_name)
   14 |         img = renderer.render()
   15 |         bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
   16 |         cv2.imwrite(f"data/{cam_name}.png", bgr)
   17 |         print(f"Rendered {cam_name}")
   18 |     except Exception as e:
   19 |         print(f"Error {cam_name}: {e}")
````
