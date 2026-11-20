# bipedal/scripts/build_bipedal_duel_xml.py

원본: [scripts/build_bipedal_duel_xml.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/build_bipedal_duel_xml.py)

SHA256: `5c006a9922db3433665976e82f01c8ebb1128896dfd225f65e085c76a6f6cc2a`

전체 215행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `prefix_elements` | FunctionDef | 16 | 46 |
| `build_bipedal_duel_xml` | FunctionDef | 49 | 211 |

## 전체 원문

````text
    1 | """
    2 | Builds the Unified Full-Stadium Whole-Body Bipedal Duel Arena XML (models/h1_bipedal_duel.xml).
    3 | Combines:
    4 | - 10m Mound H1 Pitcher (aerodynamic release, 19 actuators, anchored on mound at y=10.0m)
    5 | - Full 19-DoF H1 Whole-Body Bipedal Batter on 6-DoF Floating Base Pelvis (at home plate y=0.0m)
    6 | - Unified 10m Stadium Arena with strike zone, mound, cameras, and aerodynamic contact dynamics.
    7 | """
    8 | 
    9 | import os
   10 | import xml.etree.ElementTree as ET
   11 | import mujoco
   12 | 
   13 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   14 | 
   15 | 
   16 | def prefix_elements(elem, prefix):
   17 |     # Prefix name
   18 |     if 'name' in elem.attrib:
   19 |         name = elem.attrib['name']
   20 |         if not name.startswith(('ground', 'home_plate', 'pitcher_mound', 'pitcher_rubber', 
   21 |                                 'strike_zone', 'pitch_target', 'target_', 'broadcast_cam',
   22 |                                 'side_cam', 'behind_', 'catcher_cam', 'overhead_cam',
   23 |                                 'baseball', 'ball_', 'left_box', 'right_box', 'bat_')):
   24 |             elem.attrib['name'] = f"{prefix}_{name}"
   25 | 
   26 |     # Prefix joint references in actuators
   27 |     if 'joint' in elem.attrib:
   28 |         jname = elem.attrib['joint']
   29 |         elem.attrib['joint'] = f"{prefix}_{jname}"
   30 | 
   31 |     # Prefix body references in contacts / exclusions
   32 |     for b_attr in ['body1', 'body2']:
   33 |         if b_attr in elem.attrib:
   34 |             bname = elem.attrib[b_attr]
   35 |             if bname not in ['baseball', 'ground']:
   36 |                 elem.attrib[b_attr] = f"{prefix}_{bname}"
   37 | 
   38 |     # Prefix site references
   39 |     for s_attr in ['site1', 'site2']:
   40 |         if s_attr in elem.attrib:
   41 |             sname = elem.attrib[s_attr]
   42 |             if not sname.startswith(('ball_', 'bat_')):
   43 |                 elem.attrib[s_attr] = f"{prefix}_{sname}"
   44 | 
   45 |     for child in elem:
   46 |         prefix_elements(child, prefix)
   47 | 
   48 | 
   49 | def build_bipedal_duel_xml():
   50 |     p_tree = ET.parse(os.path.join(BASE_DIR, 'models', 'h1_pitcher.xml'))
   51 |     b_tree = ET.parse(os.path.join(BASE_DIR, 'models', 'h1_bipedal_baseball.xml'))
   52 | 
   53 |     p_root = p_tree.getroot()
   54 |     b_root = b_tree.getroot()
   55 | 
   56 |     p_world = p_root.find('worldbody')
   57 |     b_world = b_root.find('worldbody')
   58 | 
   59 |     # Pitcher pelvis (anchored at y=10.0m)
   60 |     p_pelvis = p_world.find(".//body[@name='pelvis']")
   61 |     prefix_elements(p_pelvis, 'p')
   62 | 
   63 |     # Batter pelvis (with 6-DoF freejoint, pos="-0.85 0.00 0.88")
   64 |     b_pelvis = b_world.find(".//body[@name='pelvis']")
   65 |     b_pelvis.attrib['pos'] = "-0.85 0.00 0.88"
   66 |     prefix_elements(b_pelvis, 'b')
   67 | 
   68 |     # Verify b_pelvis has freejoint
   69 |     fj = b_pelvis.find('freejoint')
   70 |     if fj is not None:
   71 |         fj.attrib['name'] = 'b_pelvis_joint'
   72 | 
   73 |     # Create root for bipedal duel
   74 |     duel_root = ET.Element('mujoco', attrib={'model': 'h1_bipedal_duel'})
   75 |     
   76 |     # Compiler
   77 |     ET.SubElement(duel_root, 'compiler', attrib={
   78 |         'angle': 'radian',
   79 |         'meshdir': 'unitree_h1_assets',
   80 |         'autolimits': 'true'
   81 |     })
   82 |     
   83 |     # Option
   84 |     ET.SubElement(duel_root, 'option', attrib={
   85 |         'timestep': '0.002',
   86 |         'gravity': '0 0 -9.81'
   87 |     })
   88 | 
   89 |     # Defaults and Assets from pitcher XML + batter XML
   90 |     duel_root.append(p_root.find('default'))
   91 |     asset = p_root.find('asset')
   92 |     for mat in b_root.find('asset').findall('material'):
   93 |         if mat.attrib.get('name') not in [m.attrib.get('name') for m in asset.findall('material')]:
   94 |             asset.append(mat)
   95 |     duel_root.append(asset)
   96 | 
   97 |     # Worldbody
   98 |     wb = ET.SubElement(duel_root, 'worldbody')
   99 |     
  100 |     # Copy lights, ground, markers from pitcher worldbody
  101 |     for item in p_world:
  102 |         if item.tag in ['light', 'geom', 'site'] and 'pelvis' not in item.attrib.get('name', ''):
  103 |             wb.append(item)
  104 | 
  105 |     # Visual Batter's box
  106 |     wb.append(ET.Element('geom', attrib={
  107 |         'name': 'left_box',
  108 |         'type': 'box',
  109 |         'size': '0.45 0.9 0.002',
  110 |         'pos': '-0.85 0 0.002',
  111 |         'rgba': '0.8 0.8 0.8 0.3'
  112 |     }))
  113 | 
  114 |     # Cameras
  115 |     wb.append(ET.Element('camera', attrib={
  116 |         'name': 'duel_broadcast_cam',
  117 |         'pos': '-9.0 5.0 3.6',
  118 |         'xyaxes': '0 -1 0 0.35 0 0.94',
  119 |         'fovy': '68'
  120 |     }))
  121 |     wb.append(ET.Element('camera', attrib={
  122 |         'name': 'side_cam',
  123 |         'pos': '-3.5 0.5 1.4',
  124 |         'xyaxes': '0 -1 0 0.15 0 0.98',
  125 |         'fovy': '48'
  126 |     }))
  127 |     wb.append(ET.Element('camera', attrib={
  128 |         'name': 'pitcher_cam',
  129 |         'pos': '0 11.5 1.8',
  130 |         'xyaxes': '1 0 0 0 -0.2 0.98',
  131 |         'fovy': '55'
  132 |     }))
  133 |     wb.append(ET.Element('camera', attrib={
  134 |         'name': 'catcher_cam',
  135 |         'mode': 'targetbody',
  136 |         'target': 'p_pelvis',
  137 |         'pos': '0 -1.5 1.0',
  138 |         'fovy': '45'
  139 |     }))
  140 |     wb.append(ET.Element('camera', attrib={
  141 |         'name': 'batter_cam',
  142 |         'pos': '-2.8 -2.0 1.8',
  143 |         'xyaxes': '0.75 -0.66 0 0.25 0.28 0.93',
  144 |         'fovy': '48'
  145 |     }))
  146 | 
  147 |     # Add Pitcher and Batter Pelvis bodies
  148 |     wb.append(p_pelvis)
  149 |     wb.append(b_pelvis)
  150 | 
  151 |     # Add Baseball
  152 |     ball_body = p_world.find(".//body[@name='baseball']")
  153 |     wb.append(ball_body)
  154 | 
  155 |     # Contacts
  156 |     contact = ET.SubElement(duel_root, 'contact')
  157 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'p_torso_link', 'body2': 'p_right_shoulder_roll_link'})
  158 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'p_torso_link', 'body2': 'p_left_shoulder_roll_link'})
  159 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'b_torso_link', 'body2': 'b_right_shoulder_roll_link'})
  160 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'b_torso_link', 'body2': 'b_left_shoulder_roll_link'})
  161 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'p_right_elbow_link'})
  162 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'b_right_elbow_link'})
  163 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'b_left_elbow_link'})
  164 |     ET.SubElement(contact, 'pair', attrib={
  165 |         'geom1': 'bat_barrel',
  166 |         'geom2': 'ball_geom',
  167 |         'solref': '0.0015 1',
  168 |         'solimp': '0.95 0.99 0.001 0.5 2',
  169 |         'friction': '0.4 0.01 0.001'
  170 |     })
  171 | 
  172 |     # Actuators
  173 |     actuators = ET.SubElement(duel_root, 'actuator')
  174 |     p_act = p_root.find('actuator')
  175 |     prefix_elements(p_act, 'p')
  176 |     for a in p_act:
  177 |         actuators.append(a)
  178 | 
  179 |     b_act = b_root.find('actuator')
  180 |     prefix_elements(b_act, 'b')
  181 |     for a in b_act:
  182 |         actuators.append(a)
  183 | 
  184 |     # Equality
  185 |     equality = ET.SubElement(duel_root, 'equality')
  186 |     ET.SubElement(equality, 'weld', attrib={
  187 |         'name': 'p_ball_weld',
  188 |         'site1': 'p_pitcher_hand_site',
  189 |         'site2': 'ball_site'
  190 |     })
  191 | 
  192 |     # Write output
  193 |     out_path = os.path.join(BASE_DIR, 'models', 'h1_bipedal_duel.xml')
  194 |     tree = ET.ElementTree(duel_root)
  195 |     ET.indent(tree, space="  ")
  196 |     tree.write(out_path, encoding='utf-8', xml_declaration=True)
  197 |     print(f"Generated {out_path} successfully!")
  198 | 
  199 |     # Verify loading with MuJoCo
  200 |     m = mujoco.MjModel.from_xml_path(out_path)
  201 |     d = mujoco.MjData(m)
  202 |     mujoco.mj_forward(m, d)
  203 |     print(f"MuJoCo Verification: Successfully loaded {out_path}")
  204 |     print(f"  Total bodies: {m.nbody}")
  205 |     print(f"  Total joints: {m.njnt}")
  206 |     print(f"  Total actuators: {m.nu}")
  207 |     print(f"  Total geoms: {m.ngeom}")
  208 |     print(f"  Pitcher pelvis: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'p_pelvis')}")
  209 |     print(f"  Batter pelvis: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'b_pelvis')}")
  210 |     print(f"  Batter pelvis freejoint: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, 'b_pelvis_joint')}")
  211 |     print(f"  Baseball freejoint: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, 'ball_joint')}")
  212 | 
  213 | 
  214 | if __name__ == '__main__':
  215 |     build_bipedal_duel_xml()
````
