# baseball/scripts/patches/fix_mat.py

원본: [scripts/patches/fix_mat.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/fix_mat.py)

SHA256: `4c29f7615a59f7c001774e54acfa696e6af1fb91dd0d0944ccf6b141ae043248`

전체 16행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_fielder.xml")
    4 | root = tree.getroot()
    5 | 
    6 | asset = root.find("asset")
    7 | mats = asset.findall("material")
    8 | seen = set()
    9 | for m in mats:
   10 |     name = m.get("name")
   11 |     if name in seen:
   12 |         asset.remove(m)
   13 |     else:
   14 |         seen.add(name)
   15 | 
   16 | tree.write("shared_assets/h1_fielder.xml")
````
