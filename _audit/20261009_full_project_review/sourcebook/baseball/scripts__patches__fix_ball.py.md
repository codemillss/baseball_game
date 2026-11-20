# baseball/scripts/patches/fix_ball.py

원본: [scripts/patches/fix_ball.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/fix_ball.py)

SHA256: `707d3eee5ab464afaeaf4a178964170dcd98e4e68d2986b7a56edfeaaf8228f7`

전체 13행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_fielder.xml")
    4 | root = tree.getroot()
    5 | 
    6 | worldbody = root.find("worldbody")
    7 | 
    8 | # Find the first freejoint
    9 | for fj in worldbody.findall("freejoint"):
   10 |     if fj.get("name") == "ball_joint":
   11 |         worldbody.remove(fj)
   12 | 
   13 | tree.write("shared_assets/h1_fielder.xml")
````
