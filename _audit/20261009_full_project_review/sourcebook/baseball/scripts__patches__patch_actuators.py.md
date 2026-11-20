# baseball/scripts/patches/patch_actuators.py

원본: [scripts/patches/patch_actuators.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/patch_actuators.py)

SHA256: `514260271e70e91ee5954064a83437db88f276fee5b9463df7c399dfd8151465`

전체 20행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_fielder.xml")
    4 | root = tree.getroot()
    5 | 
    6 | actuator = root.find("actuator")
    7 | 
    8 | # Add base actuators
    9 | ET.SubElement(actuator, "motor", name="base_x", joint="base_x", gear="500")
   10 | ET.SubElement(actuator, "motor", name="base_y", joint="base_y", gear="500")
   11 | ET.SubElement(actuator, "motor", name="base_yaw", joint="base_yaw", gear="500")
   12 | 
   13 | # The legs are removed, so we should remove their actuators to avoid errors!
   14 | leg_joints = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
   15 |               "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]
   16 | for m in actuator.findall("motor"):
   17 |     if m.get("joint") in leg_joints:
   18 |         actuator.remove(m)
   19 | 
   20 | tree.write("shared_assets/h1_fielder.xml")
````
