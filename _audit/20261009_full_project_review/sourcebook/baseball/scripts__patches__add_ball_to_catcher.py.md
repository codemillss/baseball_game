# baseball/scripts/patches/add_ball_to_catcher.py

원본: [scripts/patches/add_ball_to_catcher.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/add_ball_to_catcher.py)

SHA256: `6d7fab8af1ab6084f045b7f72ad83d485c948170b22d11c6d50a61e267e1e583`

전체 10행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_catcher.xml")
    4 | worldbody = tree.getroot().find("worldbody")
    5 | 
    6 | ball = ET.SubElement(worldbody, "body", name="baseball", pos="0 18.4 1.5")
    7 | ET.SubElement(ball, "joint", name="ball_joint", type="free")
    8 | ET.SubElement(ball, "geom", name="ball_geom", type="sphere", size="0.036", rgba="1 1 1 1", mass="0.145")
    9 | 
   10 | tree.write("shared_assets/h1_catcher.xml")
````
