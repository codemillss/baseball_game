# baseball/archive/render_angles.py

원본: [archive/render_angles.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/render_angles.py)

SHA256: `2b019ff5e5dbad71b21c13ae33ea587e898b2b88b76422022897b6494c6de66d`

전체 32행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | import cv2
    3 | import os
    4 | 
    5 | model = mujoco.MjModel.from_xml_path('assets/stadium_3d.xml')
    6 | data = mujoco.MjData(model)
    7 | mujoco.mj_forward(model, data)
    8 | 
    9 | renderer = mujoco.Renderer(model, height=480, width=640)
   10 | 
   11 | cameras = ["pitcher_cam", "catcher_cam", "broadcaster_cam", "top_down_cam"]
   12 | out_dir = "/Users/jmjeon/.gemini/antigravity-ide/brain/4bdec9f3-e0a2-4d05-aab9-6d6fb58bd3c2"
   13 | 
   14 | for i, cam_name in enumerate(cameras):
   15 |     renderer.update_scene(data, camera=cam_name)
   16 |     img = renderer.render()
   17 |     img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
   18 |     cv2.imwrite(os.path.join(out_dir, f"stance_{cam_name}.png"), img_bgr)
   19 |     print(f"Saved {cam_name}")
   20 | 
   21 | # Custom close-up camera on the batter
   22 | custom_cam = mujoco.MjvCamera()
   23 | custom_cam.type = mujoco.mjtCamera.mjCAMERA_FREE
   24 | custom_cam.lookat[:] = [-0.85, 0, 1.3] # Look at batter chest
   25 | custom_cam.distance = 2.5
   26 | custom_cam.azimuth = 120 # Side view
   27 | custom_cam.elevation = -15
   28 | renderer.update_scene(data, camera=custom_cam)
   29 | img = renderer.render()
   30 | img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
   31 | cv2.imwrite(os.path.join(out_dir, f"stance_closeup.png"), img_bgr)
   32 | print(f"Saved stance_closeup.png")
````
