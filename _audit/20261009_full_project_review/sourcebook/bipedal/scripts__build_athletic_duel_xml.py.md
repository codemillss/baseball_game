# bipedal/scripts/build_athletic_duel_xml.py

원본: [scripts/build_athletic_duel_xml.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/build_athletic_duel_xml.py)

SHA256: `6e298105c0dcfbad21f1c1d370a8d67894bb20ec515f433b9acda0a9303753e6`

전체 100행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `build_athletic_duel_xml` | FunctionDef | 7 | 97 |

## 전체 원문

````text
    1 | import os
    2 | import xml.etree.ElementTree as ET
    3 | import mujoco
    4 | 
    5 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    6 | 
    7 | def build_athletic_duel_xml():
    8 |     battery_xml = os.path.join(BASE_DIR, 'models', 'h1_battery_pitch_catch.xml')
    9 |     duel_xml = os.path.join(BASE_DIR, 'models', 'h1_bipedal_duel.xml')
   10 | 
   11 |     b_tree = ET.parse(battery_xml)
   12 |     d_tree = ET.parse(duel_xml)
   13 | 
   14 |     b_root = b_tree.getroot()
   15 |     d_root = d_tree.getroot()
   16 | 
   17 |     # Find b_pelvis in duel_xml
   18 |     d_wb = d_root.find('worldbody')
   19 |     b_pelvis = None
   20 |     for child in d_wb:
   21 |         if child.attrib.get('name') == 'b_pelvis':
   22 |             b_pelvis = child
   23 |             break
   24 | 
   25 |     # Adjust b_pelvis initial position to athletic deep stance:
   26 |     # x = -0.75m, y = 0.00m, z = 0.86m
   27 |     b_pelvis.attrib['pos'] = "-0.75 0.00 0.86"
   28 | 
   29 |     # Add b_pelvis to b_root worldbody
   30 |     b_wb = b_root.find('worldbody')
   31 |     # Place b_pelvis before baseball
   32 |     b_wb.append(b_pelvis)
   33 | 
   34 |     # Add batter actuators from duel_xml to b_root actuator
   35 |     b_actuator = b_root.find('actuator')
   36 |     d_actuator = d_root.find('actuator')
   37 |     for act in d_actuator:
   38 |         aname = act.attrib.get('name', '')
   39 |         if aname.startswith('b_'):
   40 |             b_actuator.append(act)
   41 | 
   42 |     # Add cameras: duel_broadcast_cam, umpire_cam, side_cam
   43 |     # Remove existing cameras and add unified set
   44 |     for cam in b_wb.findall('camera'):
   45 |         b_wb.remove(cam)
   46 | 
   47 |     b_wb.append(ET.Element('camera', attrib={
   48 |         'name': 'duel_broadcast_cam',
   49 |         'pos': '-3.8 -4.2 2.6',
   50 |         'xyaxes': '0.74 -0.67 0 0.28 0.31 0.91'
   51 |     }))
   52 |     b_wb.append(ET.Element('camera', attrib={
   53 |         'name': 'umpire_cam',
   54 |         'pos': '0.0 -2.4 1.4',
   55 |         'xyaxes': '1 0 0 0 0.45 0.89'
   56 |     }))
   57 |     b_wb.append(ET.Element('camera', attrib={
   58 |         'name': 'batter_side_cam',
   59 |         'pos': '-3.2 0.0 1.2',
   60 |         'xyaxes': '0 1 0 0 0 1'
   61 |     }))
   62 |     b_wb.append(ET.Element('camera', attrib={
   63 |         'name': 'cf_broadcast_cam',
   64 |         'pos': '0.0 6.0 2.0',
   65 |         'xyaxes': '-1 0 0 0 -0.22 0.975',
   66 |         'fovy': '45'
   67 |     }))
   68 |     b_wb.append(ET.Element('camera', attrib={
   69 |         'name': 'catcher_framing_cam',
   70 |         'pos': '-1.5 -2.2 1.1',
   71 |         'xyaxes': '0.85 -0.53 0 0.18 0.29 0.94',
   72 |         'fovy': '42'
   73 |     }))
   74 | 
   75 |     # Add two_hand_grip connect equality
   76 |     equality = b_root.find('equality')
   77 |     if equality is None:
   78 |         equality = ET.SubElement(b_root, 'equality')
   79 |     if equality.find(".//connect[@name='two_hand_grip']") is None:
   80 |         equality.append(ET.Element('connect', attrib={
   81 |             'name': 'two_hand_grip',
   82 |             'site1': 'b_l_hand_grip',
   83 |             'site2': 'bat_grip_left',
   84 |             'solref': '0.005 1',
   85 |             'solimp': '0.95 0.99 0.001',
   86 |             'active': 'true'
   87 |         }))
   88 | 
   89 |     out_path = os.path.join(BASE_DIR, 'models', 'h1_athletic_duel.xml')
   90 |     b_tree.write(out_path, encoding='utf-8', xml_declaration=True)
   91 |     print(f"Successfully generated {out_path}")
   92 | 
   93 |     # Verify loading in mujoco
   94 |     model = mujoco.MjModel.from_xml_path(out_path)
   95 |     data = mujoco.MjData(model)
   96 |     mujoco.mj_forward(model, data)
   97 |     print(f"MuJoCo verification passed! Bodies: {model.nbody}, Joints: {model.njnt}, Actuators: {model.nu}")
   98 | 
   99 | if __name__ == '__main__':
  100 |     build_athletic_duel_xml()
````
