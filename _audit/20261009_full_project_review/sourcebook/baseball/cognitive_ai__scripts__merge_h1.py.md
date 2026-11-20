# baseball/cognitive_ai/scripts/merge_h1.py

원본: [cognitive_ai/scripts/merge_h1.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/cognitive_ai/scripts/merge_h1.py)

SHA256: `2821b1729d396815486992469198016234a5d3bbac2e1436afb5c3dcf5083477`

전체 88행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `merge_xml` | FunctionDef | 3 | 85 |

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | def merge_xml():
    4 |     tree = ET.parse('archive/mujoco_menagerie/unitree_h1/h1.xml')
    5 |     root = tree.getroot()
    6 |     
    7 |     # 1. Update compiler
    8 |     compiler = root.find('compiler')
    9 |     if compiler is not None:
   10 |         compiler.set('meshdir', 'unitree_h1_assets')
   11 |         
   12 |     # 2. Add stadium assets
   13 |     asset = root.find('asset')
   14 |     if asset is None:
   15 |         asset = ET.SubElement(root, 'asset')
   16 |     
   17 |     ET.SubElement(asset, 'texture', type='skybox', builtin='gradient', rgb1='0.3 0.5 0.7', rgb2='0 0 0', width='512', height='512')
   18 |     ET.SubElement(asset, 'texture', name='texplane', type='2d', builtin='checker', rgb1='0.2 0.3 0.4', rgb2='0.1 0.15 0.2', width='512', height='512')
   19 |     ET.SubElement(asset, 'material', name='matplane', reflectance='0.3', texture='texplane', texrepeat='1 1', texuniform='true')
   20 |     ET.SubElement(asset, 'material', name='home_plate_mat', rgba='0.9 0.9 0.9 1', reflectance='0.2')
   21 |     ET.SubElement(asset, 'material', name='ball_mat', rgba='0.98 0.98 0.95 1', reflectance='0.4')
   22 |     ET.SubElement(asset, 'material', name='bat_mat', rgba='0.8 0.6 0.3 1', reflectance='0.3')
   23 | 
   24 |     # 3. Add stadium worldbody elements
   25 |     worldbody = root.find('worldbody')
   26 |     # Remove existing light
   27 |     for light in worldbody.findall('light'):
   28 |         worldbody.remove(light)
   29 |         
   30 |     ET.SubElement(worldbody, 'light', directional='true', diffuse='0.8 0.8 0.8', specular='0.2 0.2 0.2', pos='0 0 10', dir='0 0 -1')
   31 |     ET.SubElement(worldbody, 'geom', name='ground', type='plane', size='30 30 0.1', material='matplane')
   32 |     ET.SubElement(worldbody, 'geom', name='home_plate', type='box', size='0.22 0.22 0.005', pos='0 0 0.005', material='home_plate_mat')
   33 |     ET.SubElement(worldbody, 'geom', name='pitcher_mound', type='box', size='0.3 0.1 0.005', pos='0 18.44 0.005', material='home_plate_mat')
   34 |     
   35 |     ET.SubElement(worldbody, 'camera', name='pitcher_cam', pos='0 20.0 2.0', xyaxes='-1 0 0 0 0 1', fovy='60')
   36 |     ET.SubElement(worldbody, 'camera', name='batter_cam', pos='-0.85 -0.5 1.7', xyaxes='1 0 0 0 0 1', fovy='90')
   37 |     
   38 |     # Baseball
   39 |     ball = ET.SubElement(worldbody, 'body', name='baseball', pos='0 15 1.5')
   40 |     ET.SubElement(ball, 'freejoint', name='ball_joint')
   41 |     ET.SubElement(ball, 'geom', name='ball_geom', type='sphere', size='0.037', mass='0.145', material='ball_mat')
   42 | 
   43 |     # 4. Modify Pelvis
   44 |     pelvis = worldbody.find(".//*[@name='pelvis']")
   45 |     if pelvis is not None:
   46 |         pelvis.set('pos', '-0.85 0 1.05')
   47 |         # Remove freejoint
   48 |         fj = pelvis.find('freejoint')
   49 |         if fj is not None:
   50 |             pelvis.remove(fj)
   51 |         
   52 |         # Add 6-DOF root for kinematic stride control
   53 |         ET.SubElement(pelvis, 'joint', name='root_x', type='slide', axis='1 0 0', limited='false')
   54 |         ET.SubElement(pelvis, 'joint', name='root_y', type='slide', axis='0 1 0', limited='false')
   55 |         ET.SubElement(pelvis, 'joint', name='root_z', type='slide', axis='0 0 1', limited='false')
   56 |         ET.SubElement(pelvis, 'joint', name='root_rx', type='hinge', axis='1 0 0', limited='false')
   57 |         ET.SubElement(pelvis, 'joint', name='root_ry', type='hinge', axis='0 1 0', limited='false')
   58 |         ET.SubElement(pelvis, 'joint', name='root_rz', type='hinge', axis='0 0 1', limited='false')
   59 | 
   60 |     # 5. Add Bat to right_elbow_link
   61 |     right_elbow = worldbody.find(".//*[@name='right_elbow_link']")
   62 |     if right_elbow is not None:
   63 |         bat_body = ET.SubElement(right_elbow, 'body', name='bat', pos='0.3 0 0', quat='0.707 0 0.707 0')
   64 |         ET.SubElement(bat_body, 'geom', name='bat_barrel', type='cylinder', size='0.03 0.45', pos='0 0 0.45', material='bat_mat', mass='0.9')
   65 |         ET.SubElement(bat_body, 'site', name='bat_grip_left', pos='0 0 0.05', size='0.01')
   66 |         
   67 |     # 6. Add grip site to left_elbow_link
   68 |     left_elbow = worldbody.find(".//*[@name='left_elbow_link']")
   69 |     if left_elbow is not None:
   70 |         ET.SubElement(left_elbow, 'site', name='l_hand_grip', pos='0.3 0 0', size='0.01')
   71 |         
   72 |     # 7. Add equality constraint
   73 |     equality = ET.SubElement(root, 'equality')
   74 |     ET.SubElement(equality, 'connect', name='left_hand_to_bat', site1='l_hand_grip', site2='bat_grip_left')
   75 | 
   76 |     # Remove left arm actuators so constraint works seamlessly
   77 |     actuator = root.find('actuator')
   78 |     if actuator is not None:
   79 |         for motor in actuator.findall('motor'):
   80 |             if motor.get('name', '').startswith('left_shoulder') or motor.get('name') == 'left_elbow':
   81 |                 actuator.remove(motor)
   82 |                 
   83 |     # Save to shared_assets
   84 |     tree.write('shared_assets/h1_baseball.xml')
   85 |     print("Successfully generated shared_assets/h1_baseball.xml")
   86 | 
   87 | if __name__ == "__main__":
   88 |     merge_xml()
````
