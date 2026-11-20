# baseball/scripts/patches/fix_body.py

원본: [scripts/patches/fix_body.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/fix_body.py)

SHA256: `6215bc50daec238cc0d464512f9694fabd437a527796bf0e1859b4ce985f2dbf`

전체 16행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_fielder.xml")
    4 | root = tree.getroot()
    5 | 
    6 | worldbody = root.find("worldbody")
    7 | bodies = worldbody.findall("body")
    8 | seen = set()
    9 | for b in bodies:
   10 |     name = b.get("name")
   11 |     if name in seen:
   12 |         worldbody.remove(b)
   13 |     else:
   14 |         seen.add(name)
   15 | 
   16 | tree.write("shared_assets/h1_fielder.xml")
````
