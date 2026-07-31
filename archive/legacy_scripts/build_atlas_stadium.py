import xml.etree.ElementTree as ET
import os

def build_atlas_stadium():
    stadium_path = 'assets/stadium_3d.xml'
    atlas_path = 'humanoid/assets/atlas_repo/model/atlas_minimal_contact.xml'
    output_path = 'humanoid/assets/stadium_3d_atlas.xml'

    stadium_tree = ET.parse(stadium_path)
    stadium_root = stadium_tree.getroot()

    atlas_tree = ET.parse(atlas_path)
    atlas_root = atlas_tree.getroot()

    # 1. Update compiler meshdir
    compiler = stadium_root.find('compiler')
    if compiler is not None:
        compiler.set('meshdir', 'atlas_repo/model/meshes/')

    # 2. Add Atlas defaults and materials/assets
    stadium_default = stadium_root.find('default')
    atlas_default = atlas_root.find('default')
    if atlas_default is not None:
        for child in atlas_default:
            stadium_default.append(child)

    stadium_asset = stadium_root.find('asset')
    atlas_asset = atlas_root.find('asset')
    if atlas_asset is not None:
        for child in atlas_asset:
            stadium_asset.append(child)

    # 3. Process Atlas pelvis body and attach to stadium worldbody
    stadium_worldbody = stadium_root.find('worldbody')
    
    # Remove old custom batter bodies
    for body in stadium_worldbody.findall('body'):
        if body.get('name') in ['batter_torso', 'torso', 'pelvis']:
            stadium_worldbody.remove(body)

    atlas_pelvis = atlas_root.find(".//body[@name='pelvis']")
    
    # Position Atlas in the right-handed batter's box (x=0.5, y=-0.2, z=0.95)
    atlas_pelvis.set('pos', '0.5 -0.2 0.95')
    atlas_pelvis.set('euler', '0 0 90') # Face towards the pitcher (along +Y axis)

    # Attach Bat to r_hand body
    r_hand = atlas_pelvis.find(".//body[@name='r_hand']")
    if r_hand is not None:
        bat_xml = """
        <body name="bat" pos="0.0 -0.15 0.0" euler="0 90 0">
          <geom name="bat_knob" type="cylinder" size="0.025 0.015" pos="0 0.015 0" euler="90 0 0" material="wood" mass="0.05"/>
          <geom name="bat_handle" type="cylinder" size="0.014 0.2" pos="0 0.2 0" euler="90 0 0" material="wood" mass="0.25"/>
          <geom name="bat_taper" type="capsule" size="0.024 0.1" pos="0 0.45 0" euler="90 0 0" material="wood" mass="0.2"/>
          <geom name="bat_barrel" type="cylinder" size="0.034 0.25" pos="0 0.675 0" euler="90 0 0" material="wood" mass="0.5" condim="3" friction="0.6 0.1 0.1" solref="0.015 1"/>
        </body>
        """
        bat_elem = ET.fromstring(bat_xml)
        r_hand.append(bat_elem)

    # Attach 1st person Camera to Head body
    head = atlas_pelvis.find(".//body[@name='head']")
    if head is not None:
        cam_xml = '<camera name="batter_cam" pos="0.15 0 0.1" euler="90 0 90" fovy="75"/>'
        cam_elem = ET.fromstring(cam_xml)
        head.append(cam_elem)

    stadium_worldbody.append(atlas_pelvis)

    # Update ball physics for crisp contact
    for geom in stadium_worldbody.findall(".//geom[@name='ball_geom']"):
        geom.set('solref', '0.015 1')

    # Remove old batter_cam at root if exists
    for cam in stadium_worldbody.findall('camera'):
        if cam.get('name') == 'batter_cam':
            stadium_worldbody.remove(cam)

    # 4. Actuators
    stadium_actuator = stadium_root.find('actuator')
    if stadium_actuator is None:
        stadium_actuator = ET.SubElement(stadium_root, 'actuator')
    else:
        stadium_actuator.clear() # Reset old actuators

    atlas_actuator = atlas_root.find('actuator')
    if atlas_actuator is not None:
        for motor in atlas_actuator:
            stadium_actuator.append(motor)

    ET.indent(stadium_tree, space="  ")
    stadium_tree.write(output_path, encoding='utf-8')
    print(f"Successfully generated {output_path}")

if __name__ == '__main__':
    build_atlas_stadium()
