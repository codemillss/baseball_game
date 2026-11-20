# bipedal/scripts/build_duel_match_xml.py

원본: [scripts/build_duel_match_xml.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/build_duel_match_xml.py)

SHA256: `a7976d4ee8e58dafd8d812a8e016312b869e1a0cc0dbc978559a2e89bce15f90`

전체 173행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `prefix_elements` | FunctionDef | 13 | 43 |
| `main` | FunctionDef | 46 | 170 |

## 전체 원문

````text
    1 | """
    2 | Builds the Unified Pitcher vs Batter Duel Arena XML (models/h1_duel_match.xml).
    3 | Places H1 Pitcher on the mound (y=10.0m) and H1 Batter at home plate (x=-0.90m, y=0.0m)
    4 | with distinct joint and actuator namespaces (p_ and b_).
    5 | """
    6 | 
    7 | import os
    8 | import xml.etree.ElementTree as ET
    9 | import mujoco
   10 | 
   11 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   12 | 
   13 | def prefix_elements(elem, prefix):
   14 |     # Prefix name
   15 |     if 'name' in elem.attrib:
   16 |         name = elem.attrib['name']
   17 |         if not name.startswith(('ground', 'home_plate', 'pitcher_mound', 'pitcher_rubber', 
   18 |                                 'strike_zone', 'pitch_target', 'target_', 'broadcast_cam',
   19 |                                 'side_cam', 'behind_', 'catcher_cam', 'overhead_cam',
   20 |                                 'baseball', 'ball_', 'left_box', 'right_box', 'bat_')):
   21 |             elem.attrib['name'] = f"{prefix}_{name}"
   22 | 
   23 |     # Prefix joint references in actuators
   24 |     if 'joint' in elem.attrib:
   25 |         jname = elem.attrib['joint']
   26 |         elem.attrib['joint'] = f"{prefix}_{jname}"
   27 | 
   28 |     # Prefix body references in contacts / exclusions
   29 |     for b_attr in ['body1', 'body2']:
   30 |         if b_attr in elem.attrib:
   31 |             bname = elem.attrib[b_attr]
   32 |             if bname not in ['baseball', 'ground']:
   33 |                 elem.attrib[b_attr] = f"{prefix}_{bname}"
   34 | 
   35 |     # Prefix site references
   36 |     for s_attr in ['site1', 'site2']:
   37 |         if s_attr in elem.attrib:
   38 |             sname = elem.attrib[s_attr]
   39 |             if not sname.startswith(('ball_', 'bat_')):
   40 |                 elem.attrib[s_attr] = f"{prefix}_{sname}"
   41 | 
   42 |     for child in elem:
   43 |         prefix_elements(child, prefix)
   44 | 
   45 | 
   46 | def main():
   47 |     p_tree = ET.parse(os.path.join(BASE_DIR, 'models', 'h1_pitcher.xml'))
   48 |     b_tree = ET.parse(os.path.join(BASE_DIR, 'models', 'h1_baseball.xml'))
   49 | 
   50 |     p_root = p_tree.getroot()
   51 |     b_root = b_tree.getroot()
   52 | 
   53 |     p_world = p_root.find('worldbody')
   54 |     b_world = b_root.find('worldbody')
   55 | 
   56 |     # Pitcher pelvis
   57 |     p_pelvis = p_world.find(".//body[@name='pelvis']")
   58 |     prefix_elements(p_pelvis, 'p')
   59 | 
   60 |     # Batter pelvis
   61 |     b_pelvis = b_world.find(".//body[@name='pelvis']")
   62 |     b_pelvis.attrib['pos'] = "-0.90 0.00 0.95"
   63 |     prefix_elements(b_pelvis, 'b')
   64 | 
   65 |     # Create root for duel match
   66 |     duel_root = ET.Element('mujoco', attrib={'model': 'h1_duel_match'})
   67 |     
   68 |     # Compiler
   69 |     ET.SubElement(duel_root, 'compiler', attrib={
   70 |         'angle': 'radian',
   71 |         'meshdir': 'unitree_h1_assets',
   72 |         'autolimits': 'true'
   73 |     })
   74 |     
   75 |     # Option
   76 |     ET.SubElement(duel_root, 'option', attrib={
   77 |         'timestep': '0.002',
   78 |         'gravity': '0 0 -9.81'
   79 |     })
   80 | 
   81 |     # Defaults and Assets from pitcher XML
   82 |     duel_root.append(p_root.find('default'))
   83 |     asset = p_root.find('asset')
   84 |     for mat in b_root.find('asset').findall('material'):
   85 |         if mat.attrib.get('name') not in [m.attrib.get('name') for m in asset.findall('material')]:
   86 |             asset.append(mat)
   87 |     duel_root.append(asset)
   88 | 
   89 |     # Worldbody
   90 |     wb = ET.SubElement(duel_root, 'worldbody')
   91 |     
   92 |     # Copy lights, ground, markers from pitcher worldbody
   93 |     for item in p_world:
   94 |         if item.tag in ['light', 'geom', 'site'] and 'pelvis' not in item.attrib.get('name', ''):
   95 |             wb.append(item)
   96 | 
   97 |     # Cameras
   98 |     wb.append(ET.Element('camera', attrib={
   99 |         'name': 'duel_broadcast_cam',
  100 |         'pos': '-5.5 4.5 2.6',
  101 |         'xyaxes': '0.85 -0.52 0 0.18 0.30 0.94',
  102 |         'fovy': '52'
  103 |     }))
  104 |     wb.append(ET.Element('camera', attrib={
  105 |         'name': 'side_cam',
  106 |         'pos': '-3.5 0.5 1.4',
  107 |         'xyaxes': '0 -1 0 0.15 0 0.98',
  108 |         'fovy': '48'
  109 |     }))
  110 |     wb.append(ET.Element('camera', attrib={
  111 |         'name': 'pitcher_cam',
  112 |         'pos': '0 11.5 1.8',
  113 |         'xyaxes': '1 0 0 0 -0.2 0.98',
  114 |         'fovy': '55'
  115 |     }))
  116 |     wb.append(ET.Element('camera', attrib={
  117 |         'name': 'catcher_cam',
  118 |         'mode': 'targetbody',
  119 |         'target': 'p_pelvis',
  120 |         'pos': '0 -1.5 1.0',
  121 |         'fovy': '45'
  122 |     }))
  123 | 
  124 |     # Add Pitcher and Batter Pelvis bodies
  125 |     wb.append(p_pelvis)
  126 |     wb.append(b_pelvis)
  127 | 
  128 |     # Add Baseball
  129 |     ball_body = p_world.find(".//body[@name='baseball']")
  130 |     wb.append(ball_body)
  131 | 
  132 |     # Contacts
  133 |     contact = ET.SubElement(duel_root, 'contact')
  134 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'p_torso_link', 'body2': 'p_right_shoulder_roll_link'})
  135 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'b_torso_link', 'body2': 'b_right_shoulder_roll_link'})
  136 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'p_right_elbow_link'})
  137 |     ET.SubElement(contact, 'pair', attrib={
  138 |         'geom1': 'bat_barrel',
  139 |         'geom2': 'ball_geom',
  140 |         'solref': '0.0015 1',
  141 |         'solimp': '0.95 0.99 0.001 0.5 2',
  142 |         'friction': '0.4 0.01 0.001'
  143 |     })
  144 | 
  145 |     # Actuators
  146 |     actuators = ET.SubElement(duel_root, 'actuator')
  147 |     p_act = p_root.find('actuator')
  148 |     prefix_elements(p_act, 'p')
  149 |     for a in p_act:
  150 |         actuators.append(a)
  151 | 
  152 |     b_act = b_root.find('actuator')
  153 |     prefix_elements(b_act, 'b')
  154 |     for a in b_act:
  155 |         actuators.append(a)
  156 | 
  157 |     # Equality
  158 |     equality = ET.SubElement(duel_root, 'equality')
  159 |     ET.SubElement(equality, 'weld', attrib={
  160 |         'name': 'p_ball_weld',
  161 |         'site1': 'p_pitcher_hand_site',
  162 |         'site2': 'ball_site'
  163 |     })
  164 | 
  165 |     # Write output
  166 |     out_path = os.path.join(BASE_DIR, 'models', 'h1_duel_match.xml')
  167 |     tree = ET.ElementTree(duel_root)
  168 |     ET.indent(tree, space="  ")
  169 |     tree.write(out_path, encoding='utf-8', xml_declaration=True)
  170 |     print(f"Generated {out_path} successfully!")
  171 | 
  172 | if __name__ == '__main__':
  173 |     main()
````
