# baseball/scripts/patches/remove_ball.py

원본: [scripts/patches/remove_ball.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/remove_ball.py)

SHA256: `7f2db932c71f39081f9c5da9a5f7a9ee40e8f1e61042a125900fb8e4ff2108c6`

전체 10행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_catcher.xml")
    4 | worldbody = tree.getroot().find("worldbody")
    5 | 
    6 | balls = worldbody.findall("body[@name='baseball']")
    7 | if len(balls) > 1:
    8 |     worldbody.remove(balls[-1])
    9 | 
   10 | tree.write("shared_assets/h1_catcher.xml")
````
