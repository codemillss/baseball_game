# baseball/scripts/patches/fix_ground.py

원본: [scripts/patches/fix_ground.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/fix_ground.py)

SHA256: `eafeada8df606a7ac82bccfb8b154190fef174bd48a44a9c68ec84faefba4dd8`

전체 24행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_fielder.xml")
    4 | root = tree.getroot()
    5 | 
    6 | asset = root.find("asset")
    7 | ET.SubElement(asset, "texture", type="2d", name="grid", builtin="checker", rgb1="0.1 0.5 0.1", rgb2="0.2 0.6 0.2", width="300", height="300")
    8 | ET.SubElement(asset, "material", name="grid_mat", texture="grid", texrepeat="50 50", texuniform="true")
    9 | 
   10 | worldbody = root.find("worldbody")
   11 | for geom in worldbody.findall("geom"):
   12 |     if geom.get("name") == "grass":
   13 |         geom.set("material", "grid_mat")
   14 |         # Remove rgba since material overrides it
   15 |         if "rgba" in geom.attrib:
   16 |             del geom.attrib["rgba"]
   17 | 
   18 | # Also let's add a static reference pole at the origin so we can see the robot moving away from it
   19 | ET.SubElement(worldbody, "geom", name="origin_pole", type="cylinder", size="0.2 5.0", pos="0 0 5", rgba="1 0 0 1")
   20 | 
   21 | # And another one at y=20
   22 | ET.SubElement(worldbody, "geom", name="marker_20", type="cylinder", size="0.2 5.0", pos="0 20 5", rgba="1 1 0 1")
   23 | 
   24 | tree.write("shared_assets/h1_fielder.xml")
````
