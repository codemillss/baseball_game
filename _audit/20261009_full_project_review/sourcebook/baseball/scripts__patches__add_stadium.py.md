# baseball/scripts/patches/add_stadium.py

원본: [scripts/patches/add_stadium.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/add_stadium.py)

SHA256: `2f82f8e2d045b5e4eb331e01f0711485c9679121439a3171a6186a3279416a14`

전체 17행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_fielder.xml")
    4 | root = tree.getroot()
    5 | worldbody = root.find("worldbody")
    6 | 
    7 | # Remove the default checkered floor geom if it exists
    8 | for geom in worldbody.findall("geom"):
    9 |     if geom.get("name") == "floor" or geom.get("type") == "plane":
   10 |         worldbody.remove(geom)
   11 | 
   12 | # Add stadium include before worldbody
   13 | # Wait, include is usually at the top level
   14 | include = ET.Element("include", file="stadium.xml")
   15 | root.insert(0, include)
   16 | 
   17 | tree.write("shared_assets/h1_fielder.xml")
````
