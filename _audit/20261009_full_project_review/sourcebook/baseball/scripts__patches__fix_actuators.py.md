# baseball/scripts/patches/fix_actuators.py

원본: [scripts/patches/fix_actuators.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/fix_actuators.py)

SHA256: `e942613199a343d45053867380e47769a2a80c86ba7b6385e9987a8d153c22cf`

전체 21행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `fix_xml` | FunctionDef | 3 | 18 |

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | def fix_xml(filename, prefix):
    4 |     tree = ET.parse(filename)
    5 |     root = tree.getroot()
    6 |     actuator = root.find("actuator")
    7 |     for motor in actuator.findall("motor"):
    8 |         joint = motor.get("joint")
    9 |         if joint == "base_x": motor.set("joint", f"{prefix}_x")
   10 |         elif joint == "base_y": motor.set("joint", f"{prefix}_y")
   11 |         elif joint == "base_yaw": motor.set("joint", f"{prefix}_yaw")
   12 |         
   13 |         name = motor.get("name")
   14 |         if name == "base_x": motor.set("name", f"{prefix}_x")
   15 |         elif name == "base_y": motor.set("name", f"{prefix}_y")
   16 |         elif name == "base_yaw": motor.set("name", f"{prefix}_yaw")
   17 | 
   18 |     tree.write(filename)
   19 | 
   20 | fix_xml("shared_assets/h1_catcher.xml", "catcher")
   21 | fix_xml("shared_assets/h1_runner.xml", "runner")
````
