import xml.etree.ElementTree as ET

def merge_xml():
    tree = ET.parse('archive/mujoco_menagerie/unitree_h1/h1.xml')
    root = tree.getroot()
    
    # 1. Update compiler
    compiler = root.find('compiler')
    if compiler is not None:
        compiler.set('meshdir', 'unitree_h1_assets')
        
    # 2. Add stadium assets
    asset = root.find('asset')
    if asset is None:
        asset = ET.SubElement(root, 'asset')
    
    ET.SubElement(asset, 'texture', type='skybox', builtin='gradient', rgb1='0.3 0.5 0.7', rgb2='0 0 0', width='512', height='512')
    ET.SubElement(asset, 'texture', name='texplane', type='2d', builtin='checker', rgb1='0.2 0.3 0.4', rgb2='0.1 0.15 0.2', width='512', height='512')
    ET.SubElement(asset, 'material', name='matplane', reflectance='0.3', texture='texplane', texrepeat='1 1', texuniform='true')
    ET.SubElement(asset, 'material', name='home_plate_mat', rgba='0.9 0.9 0.9 1', reflectance='0.2')
    ET.SubElement(asset, 'material', name='ball_mat', rgba='0.98 0.98 0.95 1', reflectance='0.4')
    ET.SubElement(asset, 'material', name='bat_mat', rgba='0.8 0.6 0.3 1', reflectance='0.3')

    # 3. Add stadium worldbody elements
    worldbody = root.find('worldbody')
    # Remove existing light
    for light in worldbody.findall('light'):
        worldbody.remove(light)
        
    ET.SubElement(worldbody, 'light', directional='true', diffuse='0.8 0.8 0.8', specular='0.2 0.2 0.2', pos='0 0 10', dir='0 0 -1')
    ET.SubElement(worldbody, 'geom', name='ground', type='plane', size='30 30 0.1', material='matplane')
    ET.SubElement(worldbody, 'geom', name='home_plate', type='box', size='0.22 0.22 0.005', pos='0 0 0.005', material='home_plate_mat')
    ET.SubElement(worldbody, 'geom', name='pitcher_mound', type='box', size='0.3 0.1 0.005', pos='0 18.44 0.005', material='home_plate_mat')
    
    ET.SubElement(worldbody, 'camera', name='pitcher_cam', pos='0 20.0 2.0', xyaxes='-1 0 0 0 0 1', fovy='60')
    ET.SubElement(worldbody, 'camera', name='batter_cam', pos='-0.85 -0.5 1.7', xyaxes='1 0 0 0 0 1', fovy='90')
    
    # Baseball
    ball = ET.SubElement(worldbody, 'body', name='baseball', pos='0 15 1.5')
    ET.SubElement(ball, 'freejoint', name='ball_joint')
    ET.SubElement(ball, 'geom', name='ball_geom', type='sphere', size='0.037', mass='0.145', material='ball_mat')

    # 4. Modify Pelvis
    pelvis = worldbody.find(".//*[@name='pelvis']")
    if pelvis is not None:
        pelvis.set('pos', '-0.85 0 1.05')
        # Remove freejoint
        fj = pelvis.find('freejoint')
        if fj is not None:
            pelvis.remove(fj)
        
        # Add 6-DOF root for kinematic stride control
        ET.SubElement(pelvis, 'joint', name='root_x', type='slide', axis='1 0 0', limited='false')
        ET.SubElement(pelvis, 'joint', name='root_y', type='slide', axis='0 1 0', limited='false')
        ET.SubElement(pelvis, 'joint', name='root_z', type='slide', axis='0 0 1', limited='false')
        ET.SubElement(pelvis, 'joint', name='root_rx', type='hinge', axis='1 0 0', limited='false')
        ET.SubElement(pelvis, 'joint', name='root_ry', type='hinge', axis='0 1 0', limited='false')
        ET.SubElement(pelvis, 'joint', name='root_rz', type='hinge', axis='0 0 1', limited='false')

    # 5. Add Bat to right_elbow_link
    right_elbow = worldbody.find(".//*[@name='right_elbow_link']")
    if right_elbow is not None:
        bat_body = ET.SubElement(right_elbow, 'body', name='bat', pos='0.3 0 0', quat='0.707 0 0.707 0')
        ET.SubElement(bat_body, 'geom', name='bat_barrel', type='cylinder', size='0.03 0.45', pos='0 0 0.45', material='bat_mat', mass='0.9')
        ET.SubElement(bat_body, 'site', name='bat_grip_left', pos='0 0 0.05', size='0.01')
        
    # 6. Add grip site to left_elbow_link
    left_elbow = worldbody.find(".//*[@name='left_elbow_link']")
    if left_elbow is not None:
        ET.SubElement(left_elbow, 'site', name='l_hand_grip', pos='0.3 0 0', size='0.01')
        
    # 7. Add equality constraint
    equality = ET.SubElement(root, 'equality')
    ET.SubElement(equality, 'connect', name='left_hand_to_bat', site1='l_hand_grip', site2='bat_grip_left')

    # Remove left arm actuators so constraint works seamlessly
    actuator = root.find('actuator')
    if actuator is not None:
        for motor in actuator.findall('motor'):
            if motor.get('name', '').startswith('left_shoulder') or motor.get('name') == 'left_elbow':
                actuator.remove(motor)
                
    # Save to shared_assets
    tree.write('shared_assets/h1_baseball.xml')
    print("Successfully generated shared_assets/h1_baseball.xml")

if __name__ == "__main__":
    merge_xml()
