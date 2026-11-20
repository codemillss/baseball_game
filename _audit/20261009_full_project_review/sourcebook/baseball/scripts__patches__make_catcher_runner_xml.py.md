# baseball/scripts/patches/make_catcher_runner_xml.py

원본: [scripts/patches/make_catcher_runner_xml.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/make_catcher_runner_xml.py)

SHA256: `00ff0f3840dd2e1e95824dfcecbc2bdce522b042dd48eeb2e94a9bcbc3d2affb`

전체 39행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | import shutil
    3 | 
    4 | # Make Catcher XML (Similar to Fielder, but placed behind home plate)
    5 | shutil.copy("shared_assets/h1_fielder.xml", "shared_assets/h1_catcher.xml")
    6 | tree = ET.parse("shared_assets/h1_catcher.xml")
    7 | root = tree.getroot()
    8 | worldbody = root.find("worldbody")
    9 | 
   10 | # Catcher base starts behind home plate (y = -1.5)
   11 | base = worldbody.find("body[@name='fielder_base']")
   12 | base.set("name", "catcher_base")
   13 | base.set("pos", "0 -1.5 0.4")
   14 | 
   15 | # Update joint names
   16 | for joint in base.findall("joint"):
   17 |     if joint.get("name") == "base_x": joint.set("name", "catcher_x")
   18 |     elif joint.get("name") == "base_y": joint.set("name", "catcher_y")
   19 |     elif joint.get("name") == "base_yaw": joint.set("name", "catcher_yaw")
   20 | 
   21 | tree.write("shared_assets/h1_catcher.xml")
   22 | 
   23 | # Make Runner XML (Wheeled base, placed at 1st base)
   24 | shutil.copy("shared_assets/h1_fielder.xml", "shared_assets/h1_runner.xml")
   25 | tree = ET.parse("shared_assets/h1_runner.xml")
   26 | root = tree.getroot()
   27 | worldbody = root.find("worldbody")
   28 | 
   29 | base = worldbody.find("body[@name='fielder_base']")
   30 | base.set("name", "runner_base")
   31 | # 1st base is at x=27.4, y=27.4
   32 | base.set("pos", "27.4 27.4 0.4")
   33 | 
   34 | for joint in base.findall("joint"):
   35 |     if joint.get("name") == "base_x": joint.set("name", "runner_x")
   36 |     elif joint.get("name") == "base_y": joint.set("name", "runner_y")
   37 |     elif joint.get("name") == "base_yaw": joint.set("name", "runner_yaw")
   38 | 
   39 | tree.write("shared_assets/h1_runner.xml")
````
