# baseball/scripts/patches/fix_camera.py

원본: [scripts/patches/fix_camera.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/fix_camera.py)

SHA256: `ca27673c7eb3d9e93980ea2e8ffbaae1c7c5808dcd086e70c7ea8d9e94b04afa`

전체 29행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_fielder.xml")
    4 | root = tree.getroot()
    5 | worldbody = root.find("worldbody")
    6 | 
    7 | # Remove old field_cam and glove_cam
    8 | for cam in worldbody.findall("camera"):
    9 |     worldbody.remove(cam)
   10 | 
   11 | # Add a camera that covers the outfield.
   12 | # The ball lands around y=15 to 30.
   13 | # Camera at y=40, z=10, looking back towards y=20.
   14 | # xyaxes: x is right (1 0 0), y is up-ish (0 -1 1) -> z is forward-ish (0 -1 -1)
   15 | # Actually, let's just use a simple pos and let mujoco's free camera look at it? No, xml cameras are easier.
   16 | # Camera at pos="10 40 10" looking at "0 20 0".
   17 | # direction dir = (0-10, 20-40, 0-10) = (-10, -20, -10). Normalize.
   18 | # Let's just use Euler angles or quat! Or just standard xyaxes.
   19 | # If camera is at (0, 45, 10), looking down at (0, 25, 0).
   20 | # x-axis = (1, 0, 0).
   21 | # y-axis (up on screen) = (0, 10, 20) -> (0, 0.44, 0.89)
   22 | # Let's just set pos="0 40 5" xyaxes="1 0 0 0 0.5 0.866" (looks towards -y, slightly down).
   23 | ET.SubElement(worldbody, "camera", name="field_cam", pos="0 45 8", xyaxes="1 0 0 0 0.5 0.866", fovy="60")
   24 | 
   25 | # Or better yet, attach a camera to the fielder_base so it perfectly tracks the robot!
   26 | base = worldbody.find("body[@name='fielder_base']")
   27 | ET.SubElement(base, "camera", name="tracking_cam", pos="0 -5 3", xyaxes="1 0 0 0 0.5 0.866", fovy="60")
   28 | 
   29 | tree.write("shared_assets/h1_fielder.xml")
````
