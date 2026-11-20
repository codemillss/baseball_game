# bipedal/scripts/build_infield_defense_xml.py

원본: [scripts/build_infield_defense_xml.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/build_infield_defense_xml.py)

SHA256: `22ef069eceb48a633b1b81e095a39968c243283f1a150c32c8abc4e28b132555`

전체 340행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `prefix_tree` | FunctionDef | 17 | 46 |
| `build_infield_defense_xml` | FunctionDef | 49 | 336 |

## 전체 원문

````text
    1 | """
    2 | Builds the Phase 7 Arena XML: models/h1_infield_defense.xml
    3 | Integrates 3 simultaneous Unitree H1 humanoids:
    4 | 1. Pitcher (p_): on 10m mound (y=10.0m)
    5 | 2. Batter-Runner (b_): at home plate (x=-0.75m, y=0.0m), 6-DoF floating pelvis, cardinal hip roll links, held/dropped bat prop handover
    6 | 3. 1st Baseman Infielder (f_): in 1st base infield (x=5.0m, y=5.0m), 6-DoF floating pelvis, cardinal hip roll links, fielding glove (r=0.12m) on left hand
    7 | Also includes 1st base pad at (6.5, 6.5, 0.03m), non-colliding chalk markers, broadcast cameras.
    8 | """
    9 | 
   10 | import os
   11 | import xml.etree.ElementTree as ET
   12 | import mujoco
   13 | 
   14 | BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   15 | 
   16 | 
   17 | def prefix_tree(elem, prefix):
   18 |     # Prefix name
   19 |     if 'name' in elem.attrib:
   20 |         name = elem.attrib['name']
   21 |         if not name.startswith(('ground', 'home_plate', 'pitcher_mound', 'pitcher_rubber',
   22 |                                 'first_base', 'baseline_', 'strike_zone', 'pitch_target',
   23 |                                 'left_box', 'right_box', 'baseball', 'ball_',
   24 |                                 'dropped_bat', 'infield_', 'first_base_cam', 'run_tracking_')):
   25 |             elem.attrib['name'] = f"{prefix}_{name}"
   26 | 
   27 |     # Prefix joint in actuators
   28 |     if 'joint' in elem.attrib:
   29 |         elem.attrib['joint'] = f"{prefix}_{elem.attrib['joint']}"
   30 | 
   31 |     # Prefix body in contacts
   32 |     for b_attr in ['body1', 'body2']:
   33 |         if b_attr in elem.attrib:
   34 |             bname = elem.attrib[b_attr]
   35 |             if bname not in ['baseball', 'ground', 'dropped_bat', 'first_base']:
   36 |                 elem.attrib[b_attr] = f"{prefix}_{bname}"
   37 | 
   38 |     # Prefix site references
   39 |     for s_attr in ['site1', 'site2']:
   40 |         if s_attr in elem.attrib:
   41 |             sname = elem.attrib[s_attr]
   42 |             if not sname.startswith(('ball_', 'first_base_')):
   43 |                 elem.attrib[s_attr] = f"{prefix}_{sname}"
   44 | 
   45 |     for child in elem:
   46 |         prefix_tree(child, prefix)
   47 | 
   48 | 
   49 | def build_infield_defense_xml():
   50 |     # Load pitcher and bipedal sprint template
   51 |     pitcher_xml = os.path.join(BASE_DIR, 'models', 'h1_pitcher.xml')
   52 |     sprint_xml = os.path.join(BASE_DIR, 'models', 'h1_bipedal_sprint.xml')
   53 | 
   54 |     p_tree = ET.parse(pitcher_xml)
   55 |     s_tree = ET.parse(sprint_xml)
   56 | 
   57 |     p_root = p_tree.getroot()
   58 |     s_root = s_tree.getroot()
   59 | 
   60 |     # Root XML
   61 |     root = ET.Element('mujoco', attrib={'model': 'h1_infield_defense'})
   62 |     ET.SubElement(root, 'compiler', attrib={
   63 |         'angle': 'radian',
   64 |         'meshdir': 'unitree_h1_assets',
   65 |         'autolimits': 'true'
   66 |     })
   67 |     ET.SubElement(root, 'option', attrib={
   68 |         'timestep': '0.002',
   69 |         'gravity': '0 0 -9.81'
   70 |     })
   71 | 
   72 |     # Default
   73 |     root.append(s_root.find('default'))
   74 | 
   75 |     # Asset
   76 |     asset = s_root.find('asset')
   77 |     # Add glove material
   78 |     glove_mat = ET.Element('material', attrib={
   79 |         'name': 'glove_mat',
   80 |         'rgba': '0.55 0.32 0.16 1.0',
   81 |         'reflectance': '0.2'
   82 |     })
   83 |     asset.append(glove_mat)
   84 |     root.append(asset)
   85 | 
   86 |     # Worldbody
   87 |     wb = ET.SubElement(root, 'worldbody')
   88 | 
   89 |     # Lights
   90 |     wb.append(ET.Element('light', attrib={
   91 |         'directional': 'true', 'diffuse': '0.85 0.85 0.85', 'specular': '0.25 0.25 0.25',
   92 |         'pos': '2 5 14', 'dir': '0 0 -1'
   93 |     }))
   94 |     wb.append(ET.Element('light', attrib={
   95 |         'directional': 'true', 'diffuse': '0.45 0.45 0.45',
   96 |         'pos': '-5 -5 10', 'dir': '1 1 -1'
   97 |     }))
   98 | 
   99 |     # Ground
  100 |     wb.append(ET.Element('geom', attrib={
  101 |         'name': 'ground', 'type': 'plane', 'size': '50 50 0.1', 'material': 'matplane'
  102 |     }))
  103 | 
  104 |     # Home plate & Pitcher mound (Non-colliding markers)
  105 |     wb.append(ET.Element('geom', attrib={
  106 |         'name': 'home_plate', 'type': 'box', 'size': '0.216 0.216 0.005', 'pos': '0 0 0.005',
  107 |         'material': 'home_plate_mat', 'contype': '0', 'conaffinity': '0'
  108 |     }))
  109 |     wb.append(ET.Element('geom', attrib={
  110 |         'name': 'pitcher_mound', 'type': 'cylinder', 'size': '1.2 0.01', 'pos': '0 10.0 0.005',
  111 |         'material': 'home_plate_mat', 'contype': '0', 'conaffinity': '0'
  112 |     }))
  113 |     wb.append(ET.Element('geom', attrib={
  114 |         'name': 'pitcher_rubber', 'type': 'box', 'size': '0.30 0.07 0.008', 'pos': '0 10.0 0.015',
  115 |         'material': 'home_plate_mat', 'contype': '0', 'conaffinity': '0'
  116 |     }))
  117 | 
  118 |     # 1st Base Pad at (6.5, 6.5, 0.03) and Baseline Chalk
  119 |     wb.append(ET.Element('geom', attrib={
  120 |         'name': 'first_base', 'type': 'box', 'size': '0.22 0.22 0.03', 'pos': '6.5 6.5 0.03',
  121 |         'material': 'base_pad_mat'
  122 |     }))
  123 |     wb.append(ET.Element('site', attrib={
  124 |         'name': 'first_base_site', 'type': 'sphere', 'size': '0.25', 'pos': '6.5 6.5 0.03',
  125 |         'rgba': '1 1 0 0.4'
  126 |     }))
  127 |     wb.append(ET.Element('geom', attrib={
  128 |         'name': 'baseline_1b', 'type': 'box', 'size': '0.05 4.6 0.002', 'pos': '3.25 3.35 0.002',
  129 |         'quat': '0.92388 0 0 0.38268', 'rgba': '1 1 1 0.6', 'contype': '0', 'conaffinity': '0'
  130 |     }))
  131 |     wb.append(ET.Element('geom', attrib={
  132 |         'name': 'baseline_3b', 'type': 'box', 'size': '0.05 4.6 0.002', 'pos': '-3.25 3.35 0.002',
  133 |         'quat': '0.92388 0 0 -0.38268', 'rgba': '1 1 1 0.6', 'contype': '0', 'conaffinity': '0'
  134 |     }))
  135 | 
  136 |     # Visual Batter's box & Strike Zone
  137 |     wb.append(ET.Element('site', attrib={
  138 |         'name': 'strike_zone', 'type': 'box', 'size': '0.216 0.02 0.25', 'pos': '0 0 0.80',
  139 |         'material': 'strike_zone_mat'
  140 |     }))
  141 |     wb.append(ET.Element('site', attrib={
  142 |         'name': 'pitch_target_point', 'type': 'sphere', 'size': '0.04', 'pos': '0 0.0 0.80',
  143 |         'rgba': '0.9 0.2 0.2 0.4'
  144 |     }))
  145 |     wb.append(ET.Element('geom', attrib={
  146 |         'name': 'left_box', 'type': 'box', 'size': '0.45 0.9 0.002', 'pos': '-0.75 0 0.002',
  147 |         'rgba': '0.8 0.8 0.8 0.3', 'contype': '0', 'conaffinity': '0'
  148 |     }))
  149 | 
  150 |     # Broadcast Cameras
  151 |     # Infield Broadcast Cam: elevated wide angle showing plate, mound, 1B, and fielding territory
  152 |     wb.append(ET.Element('camera', attrib={
  153 |         'name': 'infield_broadcast_cam',
  154 |         'pos': '-4.2 -2.2 4.2',
  155 |         'xyaxes': '0.78 -0.62 0 0.28 0.35 0.89',
  156 |         'fovy': '64'
  157 |     }))
  158 |     # 1st Base Camera: zoomed on 1B bag and runner/fielder intercept play
  159 |     wb.append(ET.Element('camera', attrib={
  160 |         'name': 'first_base_cam',
  161 |         'pos': '8.5 8.5 1.6',
  162 |         'xyaxes': '-0.7071 0.7071 0 -0.22 -0.22 0.95',
  163 |         'fovy': '50'
  164 |     }))
  165 |     # Runner tracking cam
  166 |     wb.append(ET.Element('camera', attrib={
  167 |         'name': 'run_tracking_cam',
  168 |         'mode': 'targetbody',
  169 |         'target': 'b_pelvis',
  170 |         'pos': '-3.0 -2.6 2.2',
  171 |         'fovy': '52'
  172 |     }))
  173 |     # Wide stadium cam
  174 |     wb.append(ET.Element('camera', attrib={
  175 |         'name': 'stadium_wide',
  176 |         'pos': '-6.5 4.5 5.2',
  177 |         'xyaxes': '0.75 -0.66 0 0.35 0.40 0.85',
  178 |         'fovy': '65'
  179 |     }))
  180 | 
  181 |     # Baseball with 6-DoF freejoint
  182 |     ball_body = ET.Element('body', attrib={'name': 'baseball', 'pos': '0 10.0 1.2'})
  183 |     ET.SubElement(ball_body, 'freejoint', attrib={'name': 'ball_joint'})
  184 |     ET.SubElement(ball_body, 'geom', attrib={
  185 |         'name': 'ball_geom', 'type': 'sphere', 'size': '0.037', 'mass': '0.145',
  186 |         'material': 'ball_mat', 'solref': '0.002 1', 'solimp': '0.95 0.99 0.001 0.5 2',
  187 |         'friction': '0.4 0.02 0.001'
  188 |     })
  189 |     ET.SubElement(ball_body, 'site', attrib={'name': 'ball_site', 'pos': '0 0 0', 'size': '0.01'})
  190 |     wb.append(ball_body)
  191 | 
  192 |     # Dropped bat in sky (z=50m) with freejoint
  193 |     drop_body = ET.Element('body', attrib={'name': 'dropped_bat', 'pos': '0 0 50'})
  194 |     ET.SubElement(drop_body, 'freejoint', attrib={'name': 'dropped_bat_joint'})
  195 |     ET.SubElement(drop_body, 'geom', attrib={
  196 |         'name': 'dropped_bat_barrel', 'type': 'capsule', 'size': '0.032 0.40', 'pos': '0 0 0.45',
  197 |         'material': 'bat_mat', 'mass': '0.90', 'solref': '0.005 1', 'solimp': '0.90 0.95 0.001 0.5 2',
  198 |         'friction': '0.8 0.02 0.001'
  199 |     })
  200 |     wb.append(drop_body)
  201 | 
  202 |     # 1. Pitcher Robot (p_) - anchored at mound (0, 10.0, 0.82)
  203 |     p_pelvis = ET.fromstring(ET.tostring(p_root.find(".//worldbody/body[@name='pelvis']")))
  204 |     prefix_tree(p_pelvis, 'p')
  205 |     p_pelvis.attrib['pos'] = '0 10.0 0.82'
  206 |     p_pelvis.attrib['quat'] = '0.7071068 0 0 -0.7071068'
  207 |     wb.append(p_pelvis)
  208 | 
  209 |     # 2. Batter-Runner Robot (b_) - at home plate (-0.75, 0.0, 0.92) with freejoint
  210 |     b_pelvis = ET.fromstring(ET.tostring(s_root.find(".//worldbody/body[@name='pelvis']")))
  211 |     prefix_tree(b_pelvis, 'b')
  212 |     b_pelvis.attrib['pos'] = '-0.75 0.0 0.92'
  213 |     # Ensure freejoint is named b_pelvis_joint
  214 |     fj = b_pelvis.find('freejoint')
  215 |     if fj is not None:
  216 |         fj.attrib['name'] = 'b_pelvis_joint'
  217 |     wb.append(b_pelvis)
  218 | 
  219 |     # 3. 1st Baseman Infielder Robot (f_) - at 1st base infield (5.0, 5.0, 0.92)
  220 |     # Using H1 bipedal template from sprint (which has cardinal-aligned hip rolls!)
  221 |     f_pelvis = ET.fromstring(ET.tostring(s_root.find(".//worldbody/body[@name='pelvis']")))
  222 |     # Remove held bat from infielder right arm
  223 |     right_elbow = f_pelvis.find(".//body[@name='right_elbow_link']")
  224 |     if right_elbow is not None:
  225 |         for ch in list(right_elbow):
  226 |             if 'bat' in ch.attrib.get('name', ''):
  227 |                 right_elbow.remove(ch)
  228 | 
  229 |     # Attach fielding glove to left arm (left_elbow_link)
  230 |     left_elbow = f_pelvis.find(".//body[@name='left_elbow_link']")
  231 |     if left_elbow is not None:
  232 |         # Add f_glove geom (sphere r=0.12m)
  233 |         left_elbow.append(ET.Element('geom', attrib={
  234 |             'name': 'glove',
  235 |             'type': 'sphere',
  236 |             'size': '0.12',
  237 |             'pos': '0.30 0 0',
  238 |             'material': 'glove_mat',
  239 |             'friction': '0.8 0.02 0.001',
  240 |             'solref': '0.005 1',
  241 |             'solimp': '0.92 0.98 0.001 0.5 2'
  242 |         }))
  243 |         left_elbow.append(ET.Element('site', attrib={
  244 |             'name': 'glove_site',
  245 |             'type': 'sphere',
  246 |             'size': '0.12',
  247 |             'pos': '0.30 0 0',
  248 |             'rgba': '0.7 0.35 0.15 0.6'
  249 |         }))
  250 | 
  251 |     prefix_tree(f_pelvis, 'f')
  252 |     f_pelvis.attrib['pos'] = '5.0 5.0 0.92'
  253 |     # Yaw towards home plate / ball approach (-135 deg)
  254 |     f_pelvis.attrib['quat'] = '0.3826834 0 0 -0.9238795'
  255 |     fj_f = f_pelvis.find('freejoint')
  256 |     if fj_f is not None:
  257 |         fj_f.attrib['name'] = 'f_pelvis_joint'
  258 |     wb.append(f_pelvis)
  259 | 
  260 |     # Contacts Section
  261 |     contact = ET.SubElement(root, 'contact')
  262 |     for pfx in ['p', 'b', 'f']:
  263 |         ET.SubElement(contact, 'exclude', attrib={'body1': f'{pfx}_torso_link', 'body2': f'{pfx}_right_shoulder_roll_link'})
  264 |         ET.SubElement(contact, 'exclude', attrib={'body1': f'{pfx}_torso_link', 'body2': f'{pfx}_left_shoulder_roll_link'})
  265 | 
  266 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'p_right_elbow_link'})
  267 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'b_right_elbow_link'})
  268 |     ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'b_left_elbow_link'})
  269 | 
  270 |     # Batted ball collision pairs
  271 |     ET.SubElement(contact, 'pair', attrib={
  272 |         'geom1': 'b_held_bat_barrel', 'geom2': 'ball_geom',
  273 |         'solref': '0.0015 1', 'solimp': '0.95 0.99 0.001 0.5 2', 'friction': '0.4 0.01 0.001'
  274 |     })
  275 |     ET.SubElement(contact, 'pair', attrib={
  276 |         'geom1': 'f_glove', 'geom2': 'ball_geom',
  277 |         'solref': '0.005 1', 'solimp': '0.92 0.98 0.001 0.5 2', 'friction': '0.8 0.02 0.001'
  278 |     })
  279 |     ET.SubElement(contact, 'pair', attrib={
  280 |         'geom1': 'ground', 'geom2': 'ball_geom',
  281 |         'solref': '0.002 1', 'solimp': '0.95 0.99 0.001 0.5 2', 'friction': '0.4 0.02 0.001'
  282 |     })
  283 | 
  284 |     # Actuator Section
  285 |     actuators = ET.SubElement(root, 'actuator')
  286 | 
  287 |     # Pitcher actuators
  288 |     p_act = p_root.find('actuator')
  289 |     prefix_tree(p_act, 'p')
  290 |     for a in p_act:
  291 |         actuators.append(a)
  292 | 
  293 |     # Batter actuators
  294 |     b_act = ET.fromstring(ET.tostring(s_root.find('actuator')))
  295 |     prefix_tree(b_act, 'b')
  296 |     for a in b_act:
  297 |         actuators.append(a)
  298 | 
  299 |     # Infielder actuators
  300 |     f_act = ET.fromstring(ET.tostring(s_root.find('actuator')))
  301 |     prefix_tree(f_act, 'f')
  302 |     for a in f_act:
  303 |         actuators.append(a)
  304 | 
  305 |     # Equality Section
  306 |     equality = ET.SubElement(root, 'equality')
  307 |     ET.SubElement(equality, 'weld', attrib={
  308 |         'name': 'p_ball_weld',
  309 |         'site1': 'p_pitcher_hand_site',
  310 |         'site2': 'ball_site'
  311 |     })
  312 | 
  313 |     # Save to models/h1_infield_defense.xml
  314 |     out_path = os.path.join(BASE_DIR, 'models', 'h1_infield_defense.xml')
  315 |     tree = ET.ElementTree(root)
  316 |     ET.indent(tree, space="  ")
  317 |     tree.write(out_path, encoding='utf-8', xml_declaration=True)
  318 |     print(f"Generated {out_path} successfully!")
  319 | 
  320 |     # Verify loading with MuJoCo
  321 |     m = mujoco.MjModel.from_xml_path(out_path)
  322 |     d = mujoco.MjData(m)
  323 |     mujoco.mj_forward(m, d)
  324 |     print(f"MuJoCo Verification: Successfully loaded {out_path}")
  325 |     print(f"  Total bodies: {m.nbody}")
  326 |     print(f"  Total joints: {m.njnt}")
  327 |     print(f"  Total actuators: {m.nu}")
  328 |     print(f"  Total geoms: {m.ngeom}")
  329 |     print(f"  Pitcher pelvis: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'p_pelvis')}")
  330 |     print(f"  Batter pelvis: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'b_pelvis')}")
  331 |     print(f"  Infielder pelvis: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'f_pelvis')}")
  332 |     print(f"  Fielding glove geom: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, 'f_glove')}")
  333 |     print(f"  Fielding glove site: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, 'f_glove_site')}")
  334 |     print(f"  1st base geom: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, 'first_base')}")
  335 |     print(f"  Infield broadcast cam: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_CAMERA, 'infield_broadcast_cam')}")
  336 |     print(f"  First base cam: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_CAMERA, 'first_base_cam')}")
  337 | 
  338 | 
  339 | if __name__ == '__main__':
  340 |     build_infield_defense_xml()
````
