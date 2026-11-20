# baseball/archive/legacy_scripts/build_atlas_stadium.py

원본: [archive/legacy_scripts/build_atlas_stadium.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_scripts/build_atlas_stadium.py)

SHA256: `47d0e5642c81df3a8f50ab1bf1b0f0e4062dd5bd7eeeaca6e994406146682f54`

전체 96행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `build_atlas_stadium` | FunctionDef | 4 | 93 |

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | import os
    3 | 
    4 | def build_atlas_stadium():
    5 |     stadium_path = 'assets/stadium_3d.xml'
    6 |     atlas_path = 'humanoid/assets/atlas_repo/model/atlas_minimal_contact.xml'
    7 |     output_path = 'humanoid/assets/stadium_3d_atlas.xml'
    8 | 
    9 |     stadium_tree = ET.parse(stadium_path)
   10 |     stadium_root = stadium_tree.getroot()
   11 | 
   12 |     atlas_tree = ET.parse(atlas_path)
   13 |     atlas_root = atlas_tree.getroot()
   14 | 
   15 |     # 1. Update compiler meshdir
   16 |     compiler = stadium_root.find('compiler')
   17 |     if compiler is not None:
   18 |         compiler.set('meshdir', 'atlas_repo/model/meshes/')
   19 | 
   20 |     # 2. Add Atlas defaults and materials/assets
   21 |     stadium_default = stadium_root.find('default')
   22 |     atlas_default = atlas_root.find('default')
   23 |     if atlas_default is not None:
   24 |         for child in atlas_default:
   25 |             stadium_default.append(child)
   26 | 
   27 |     stadium_asset = stadium_root.find('asset')
   28 |     atlas_asset = atlas_root.find('asset')
   29 |     if atlas_asset is not None:
   30 |         for child in atlas_asset:
   31 |             stadium_asset.append(child)
   32 | 
   33 |     # 3. Process Atlas pelvis body and attach to stadium worldbody
   34 |     stadium_worldbody = stadium_root.find('worldbody')
   35 |     
   36 |     # Remove old custom batter bodies
   37 |     for body in stadium_worldbody.findall('body'):
   38 |         if body.get('name') in ['batter_torso', 'torso', 'pelvis']:
   39 |             stadium_worldbody.remove(body)
   40 | 
   41 |     atlas_pelvis = atlas_root.find(".//body[@name='pelvis']")
   42 |     
   43 |     # Position Atlas in the right-handed batter's box (x=0.5, y=-0.2, z=0.95)
   44 |     atlas_pelvis.set('pos', '0.5 -0.2 0.95')
   45 |     atlas_pelvis.set('euler', '0 0 90') # Face towards the pitcher (along +Y axis)
   46 | 
   47 |     # Attach Bat to r_hand body
   48 |     r_hand = atlas_pelvis.find(".//body[@name='r_hand']")
   49 |     if r_hand is not None:
   50 |         bat_xml = """
   51 |         <body name="bat" pos="0.0 -0.15 0.0" euler="0 90 0">
   52 |           <geom name="bat_knob" type="cylinder" size="0.025 0.015" pos="0 0.015 0" euler="90 0 0" material="wood" mass="0.05"/>
   53 |           <geom name="bat_handle" type="cylinder" size="0.014 0.2" pos="0 0.2 0" euler="90 0 0" material="wood" mass="0.25"/>
   54 |           <geom name="bat_taper" type="capsule" size="0.024 0.1" pos="0 0.45 0" euler="90 0 0" material="wood" mass="0.2"/>
   55 |           <geom name="bat_barrel" type="cylinder" size="0.034 0.25" pos="0 0.675 0" euler="90 0 0" material="wood" mass="0.5" condim="3" friction="0.6 0.1 0.1" solref="0.015 1"/>
   56 |         </body>
   57 |         """
   58 |         bat_elem = ET.fromstring(bat_xml)
   59 |         r_hand.append(bat_elem)
   60 | 
   61 |     # Attach 1st person Camera to Head body
   62 |     head = atlas_pelvis.find(".//body[@name='head']")
   63 |     if head is not None:
   64 |         cam_xml = '<camera name="batter_cam" pos="0.15 0 0.1" euler="90 0 90" fovy="75"/>'
   65 |         cam_elem = ET.fromstring(cam_xml)
   66 |         head.append(cam_elem)
   67 | 
   68 |     stadium_worldbody.append(atlas_pelvis)
   69 | 
   70 |     # Update ball physics for crisp contact
   71 |     for geom in stadium_worldbody.findall(".//geom[@name='ball_geom']"):
   72 |         geom.set('solref', '0.015 1')
   73 | 
   74 |     # Remove old batter_cam at root if exists
   75 |     for cam in stadium_worldbody.findall('camera'):
   76 |         if cam.get('name') == 'batter_cam':
   77 |             stadium_worldbody.remove(cam)
   78 | 
   79 |     # 4. Actuators
   80 |     stadium_actuator = stadium_root.find('actuator')
   81 |     if stadium_actuator is None:
   82 |         stadium_actuator = ET.SubElement(stadium_root, 'actuator')
   83 |     else:
   84 |         stadium_actuator.clear() # Reset old actuators
   85 | 
   86 |     atlas_actuator = atlas_root.find('actuator')
   87 |     if atlas_actuator is not None:
   88 |         for motor in atlas_actuator:
   89 |             stadium_actuator.append(motor)
   90 | 
   91 |     ET.indent(stadium_tree, space="  ")
   92 |     stadium_tree.write(output_path, encoding='utf-8')
   93 |     print(f"Successfully generated {output_path}")
   94 | 
   95 | if __name__ == '__main__':
   96 |     build_atlas_stadium()
````
