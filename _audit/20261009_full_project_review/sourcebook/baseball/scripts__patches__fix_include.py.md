# baseball/scripts/patches/fix_include.py

원본: [scripts/patches/fix_include.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/fix_include.py)

SHA256: `4ba0d529a53127f6f625df674d67a6884a87c2dbafac973aa8ba10f03e489f2e`

전체 15행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_fielder.xml")
    4 | root = tree.getroot()
    5 | 
    6 | # Remove include
    7 | for inc in root.findall("include"):
    8 |     root.remove(inc)
    9 | 
   10 | worldbody = root.find("worldbody")
   11 | 
   12 | # Add a nice green grass plane
   13 | ET.SubElement(worldbody, "geom", name="grass", type="plane", size="50 50 0.1", rgba="0.1 0.5 0.1 1")
   14 | 
   15 | tree.write("shared_assets/h1_fielder.xml")
````
