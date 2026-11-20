# baseball/archive/test_posture.py

원본: [archive/test_posture.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/test_posture.py)

SHA256: `8d07fac3f0bebbe466f515a8f3f2bc61d4a05fdcdc4ebe3007b8561bfbbdfed6`

전체 20행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | import numpy as np
    3 | import cv2
    4 | 
    5 | model = mujoco.MjModel.from_xml_path('assets/stadium_3d.xml')
    6 | data = mujoco.MjData(model)
    7 | mujoco.mj_forward(model, data)
    8 | 
    9 | renderer = mujoco.Renderer(model, height=480, width=640)
   10 | # Use a custom camera to see the batter clearly
   11 | renderer.update_scene(data, camera="batter_cam")
   12 | img_batter = renderer.render()
   13 | 
   14 | # Or use catcher cam
   15 | renderer.update_scene(data, camera="catcher_cam")
   16 | img_catcher = renderer.render()
   17 | 
   18 | cv2.imwrite("batter_posture_batter_cam.png", cv2.cvtColor(img_batter, cv2.COLOR_RGB2BGR))
   19 | cv2.imwrite("batter_posture_catcher_cam.png", cv2.cvtColor(img_catcher, cv2.COLOR_RGB2BGR))
   20 | print("Saved posture images.")
````
