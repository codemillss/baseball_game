# baseball/archive/legacy_scripts/build_humanoid_stadium.py

원본: [archive/legacy_scripts/build_humanoid_stadium.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_scripts/build_humanoid_stadium.py)

SHA256: `ce549aabc6a7a10a13faf5080c8d9ca00e645272c2c57fdfb83e8054f0d9bab5`

전체 99행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | stadium_tree = ET.parse('assets/stadium_3d.xml')
    4 | stadium_root = stadium_tree.getroot()
    5 | 
    6 | humanoid_tree = ET.parse('humanoid_tmp.xml')
    7 | humanoid_root = humanoid_tree.getroot()
    8 | 
    9 | # 1. Add humanoid defaults
   10 | stadium_default = stadium_root.find('default')
   11 | humanoid_default = humanoid_root.find('default')
   12 | if humanoid_default is not None:
   13 |     for child in humanoid_default:
   14 |         stadium_default.append(child)
   15 | 
   16 | # 2. Add humanoid assets
   17 | stadium_asset = stadium_root.find('asset')
   18 | humanoid_asset = humanoid_root.find('asset')
   19 | if humanoid_asset is not None:
   20 |     for child in humanoid_asset:
   21 |         # Avoid duplicate grid texture
   22 |         if child.get('name') != 'grid':
   23 |             stadium_asset.append(child)
   24 | 
   25 | # 3. Add humanoid torso to stadium worldbody
   26 | stadium_worldbody = stadium_root.find('worldbody')
   27 | # Remove old custom batter_torso
   28 | for body in stadium_worldbody.findall('body'):
   29 |     if body.get('name') == 'batter_torso':
   30 |         stadium_worldbody.remove(body)
   31 | 
   32 | humanoid_torso = humanoid_root.find(".//body[@name='torso']")
   33 | 
   34 | # Pelvis Pinning: Replace freejoint with nothing or fixed joint.
   35 | # To pin it in mid-air at home plate, we set torso pos. Home plate is at 0 0 0.
   36 | # Let's place the batter at x=0.6, y=-0.1, z=1.2
   37 | humanoid_torso.set('pos', '0.6 -0.1 1.2')
   38 | freejoint = humanoid_torso.find('freejoint')
   39 | if freejoint is not None:
   40 |     humanoid_torso.remove(freejoint) # Pin the pelvis!
   41 | 
   42 | # Find the right hand and attach the bat
   43 | right_hand = humanoid_torso.find(".//body[@name='hand_right']")
   44 | # We need to add the bat bodies to the right hand
   45 | bat_xml = """
   46 | <body name="bat" pos="0.1 0 0" euler="0 90 0">
   47 |   <geom name="bat_knob" type="cylinder" size="0.025 0.015" pos="0 0.015 0" euler="90 0 0" material="wood" mass="0.05"/>
   48 |   <geom name="bat_handle" type="cylinder" size="0.014 0.2" pos="0 0.2 0" euler="90 0 0" material="wood" mass="0.25"/>
   49 |   <geom name="bat_taper" type="capsule" size="0.024 0.1" pos="0 0.45 0" euler="90 0 0" material="wood" mass="0.2"/>
   50 |   <geom name="bat_barrel" type="cylinder" size="0.034 0.25" pos="0 0.675 0" euler="90 0 0" material="wood" mass="0.5" condim="3" friction="0.6 0.1 0.1" solref="0.015 1"/>
   51 | </body>
   52 | """
   53 | bat_elem = ET.fromstring(bat_xml)
   54 | right_hand.append(bat_elem)
   55 | 
   56 | # Add camera to the head
   57 | head = humanoid_torso.find(".//body[@name='head']")
   58 | cam_xml = '<camera name="batter_cam" pos="0.1 0 0" euler="90 0 90" fovy="75"/>'
   59 | cam_elem = ET.fromstring(cam_xml)
   60 | # Remove egocentric cam if exists
   61 | for old_cam in head.findall('camera'):
   62 |     head.remove(old_cam)
   63 | head.append(cam_elem)
   64 | 
   65 | stadium_worldbody.append(humanoid_torso)
   66 | 
   67 | # Also update ball physics for bounciness
   68 | for geom in stadium_worldbody.findall(".//geom[@name='ball_geom']"):
   69 |     geom.set('solref', '0.015 1')
   70 | 
   71 | # 4. Add contact, tendon
   72 | stadium_contact = ET.SubElement(stadium_root, 'contact')
   73 | for exclude in humanoid_root.find('contact'):
   74 |     stadium_contact.append(exclude)
   75 | 
   76 | stadium_tendon = ET.SubElement(stadium_root, 'tendon')
   77 | for tendon in humanoid_root.find('tendon'):
   78 |     stadium_tendon.append(tendon)
   79 | 
   80 | # 5. Actuators
   81 | stadium_actuator = stadium_root.find('actuator')
   82 | # Remove old batter actuators
   83 | for motor in stadium_actuator.findall('motor'):
   84 |     joint_name = motor.get('joint')
   85 |     if joint_name in ['shoulder_yaw', 'shoulder_pitch', 'shoulder_roll', 'elbow_flex', 'wrist_yaw', 'wrist_pitch', 'wrist_roll', 'head_yaw', 'head_pitch']:
   86 |         stadium_actuator.remove(motor)
   87 | 
   88 | for motor in humanoid_root.find('actuator'):
   89 |     stadium_actuator.append(motor)
   90 | 
   91 | # Fix existing cameras that might have been removed (Wait, they were added to worldbody directly in stadium_3d.xml, they won't be deleted)
   92 | # But we should remove the old batter_cam if it was at the root
   93 | for cam in stadium_worldbody.findall('camera'):
   94 |     if cam.get('name') == 'batter_cam':
   95 |         stadium_worldbody.remove(cam)
   96 | 
   97 | ET.indent(stadium_tree, space="  ")
   98 | stadium_tree.write('humanoid/assets/stadium_3d_humanoid.xml', encoding='utf-8')
   99 | print("Successfully created humanoid/assets/stadium_3d_humanoid.xml")
````
