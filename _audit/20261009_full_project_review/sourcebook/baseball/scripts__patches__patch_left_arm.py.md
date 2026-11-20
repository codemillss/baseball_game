# baseball/scripts/patches/patch_left_arm.py

원본: [scripts/patches/patch_left_arm.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/patch_left_arm.py)

SHA256: `9823e9e1e55a89b50bfae0f8fec48eba3b973f6da2c2dabde07396b3977581c9`

전체 14행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_fielder.xml")
    4 | root = tree.getroot()
    5 | 
    6 | actuator = root.find("actuator")
    7 | 
    8 | # Add left arm actuators
    9 | ET.SubElement(actuator, "motor", name="left_shoulder_pitch", joint="left_shoulder_pitch", ctrlrange="-100 100")
   10 | ET.SubElement(actuator, "motor", name="left_shoulder_roll", joint="left_shoulder_roll", ctrlrange="-100 100")
   11 | ET.SubElement(actuator, "motor", name="left_shoulder_yaw", joint="left_shoulder_yaw", ctrlrange="-50 50")
   12 | ET.SubElement(actuator, "motor", name="left_elbow", joint="left_elbow", ctrlrange="-50 50")
   13 | 
   14 | tree.write("shared_assets/h1_fielder.xml")
````
