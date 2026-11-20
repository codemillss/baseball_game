# baseball/scripts/patches/patch_strike_zone.py

원본: [scripts/patches/patch_strike_zone.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/patch_strike_zone.py)

SHA256: `e6fbd41a5a475fc361b9d36a06977f3fee1017e6b348cb16b7d7482782110659`

전체 36행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_baseball_match.xml")
    4 | root = tree.getroot()
    5 | worldbody = root.find("worldbody")
    6 | 
    7 | # Add Strike Zone as a transparent site/geom for detection
    8 | # site is great for sensors, but geom is good for visual if rgba has low alpha
    9 | sz = ET.Element("site", name="strike_zone", type="box", size="0.215 0.215 0.3", pos="-0.3 0 0.8", rgba="0 1 0 0.2")
   10 | # Wait, home plate is at -0.3, 0? No, let's check where the batter is.
   11 | # Batter pelvis is at x=-0.7, y=-0.45.
   12 | # Usually home plate is at 0,0. Let's see where the home plate is in the stadium!
   13 | # Actually, baseball rules: Home plate is at 0,0,0. Pitcher is at 0, 18.4, 0 (y=18.4m).
   14 | # In our XML, pitcher is at y=10. Batter is at x=-0.7, y=-0.45 (right-handed batter box).
   15 | # So home plate is effectively around x=0, y=0!
   16 | sz.set("pos", "0 0 0.8")
   17 | worldbody.append(sz)
   18 | 
   19 | # Add Foul Lines (1st base line, 3rd base line)
   20 | # From home plate (0,0) to 1st base (x=27.4, y=27.4) and 3rd base (x=-27.4, y=27.4)
   21 | # We can just draw them using cylinders.
   22 | # 1st base line: 45 degrees to the right. 3rd base line: 45 degrees to the left.
   23 | line1 = ET.Element("geom", name="foul_line_1b", type="cylinder", size="0.05 40", pos="28.28 28.28 0.01", xyaxes="0.707 -0.707 0 0 0 1", rgba="1 1 1 1")
   24 | line3 = ET.Element("geom", name="foul_line_3b", type="cylinder", size="0.05 40", pos="-28.28 28.28 0.01", xyaxes="0.707 0.707 0 0 0 1", rgba="1 1 1 1")
   25 | # Wait, cylinders point along Z-axis by default.
   26 | # To make them lie on the ground pointing at 45 degrees:
   27 | # xyaxes specifies X and Y axes.
   28 | # We want Z-axis to be along (1, 1, 0).
   29 | # Let X-axis be (-1, 1, 0) and Y-axis be (0, 0, 1).
   30 | # Then Z = X x Y = (-1, 1, 0) x (0, 0, 1) = (1, 1, 0).
   31 | line1.set("xyaxes", "-0.707 0.707 0 0 0 1")
   32 | line3.set("xyaxes", "0.707 0.707 0 0 0 1")
   33 | worldbody.append(line1)
   34 | worldbody.append(line3)
   35 | 
   36 | tree.write("shared_assets/h1_baseball_match.xml")
````
