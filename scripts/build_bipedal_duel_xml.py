"""
Builds the Unified Full-Stadium Whole-Body Bipedal Duel Arena XML (models/h1_bipedal_duel.xml).
Combines:
- 10m Mound H1 Pitcher (aerodynamic release, 19 actuators, anchored on mound at y=10.0m)
- Full 19-DoF H1 Whole-Body Bipedal Batter on 6-DoF Floating Base Pelvis (at home plate y=0.0m)
- Unified 10m Stadium Arena with strike zone, mound, cameras, and aerodynamic contact dynamics.
"""

import os
import xml.etree.ElementTree as ET
import mujoco

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def prefix_elements(elem, prefix):
    # Prefix name
    if 'name' in elem.attrib:
        name = elem.attrib['name']
        if not name.startswith(('ground', 'home_plate', 'pitcher_mound', 'pitcher_rubber', 
                                'strike_zone', 'pitch_target', 'target_', 'broadcast_cam',
                                'side_cam', 'behind_', 'catcher_cam', 'overhead_cam',
                                'baseball', 'ball_', 'left_box', 'right_box', 'bat_')):
            elem.attrib['name'] = f"{prefix}_{name}"

    # Prefix joint references in actuators
    if 'joint' in elem.attrib:
        jname = elem.attrib['joint']
        elem.attrib['joint'] = f"{prefix}_{jname}"

    # Prefix body references in contacts / exclusions
    for b_attr in ['body1', 'body2']:
        if b_attr in elem.attrib:
            bname = elem.attrib[b_attr]
            if bname not in ['baseball', 'ground']:
                elem.attrib[b_attr] = f"{prefix}_{bname}"

    # Prefix site references
    for s_attr in ['site1', 'site2']:
        if s_attr in elem.attrib:
            sname = elem.attrib[s_attr]
            if not sname.startswith(('ball_', 'bat_')):
                elem.attrib[s_attr] = f"{prefix}_{sname}"

    for child in elem:
        prefix_elements(child, prefix)


def build_bipedal_duel_xml():
    p_tree = ET.parse(os.path.join(BASE_DIR, 'models', 'h1_pitcher.xml'))
    b_tree = ET.parse(os.path.join(BASE_DIR, 'models', 'h1_bipedal_baseball.xml'))

    p_root = p_tree.getroot()
    b_root = b_tree.getroot()

    p_world = p_root.find('worldbody')
    b_world = b_root.find('worldbody')

    # Pitcher pelvis (anchored at y=10.0m)
    p_pelvis = p_world.find(".//body[@name='pelvis']")
    prefix_elements(p_pelvis, 'p')

    # Batter pelvis (with 6-DoF freejoint, pos="-0.85 0.00 0.88")
    b_pelvis = b_world.find(".//body[@name='pelvis']")
    b_pelvis.attrib['pos'] = "-0.85 0.00 0.88"
    prefix_elements(b_pelvis, 'b')

    # Verify b_pelvis has freejoint
    fj = b_pelvis.find('freejoint')
    if fj is not None:
        fj.attrib['name'] = 'b_pelvis_joint'

    # Create root for bipedal duel
    duel_root = ET.Element('mujoco', attrib={'model': 'h1_bipedal_duel'})
    
    # Compiler
    ET.SubElement(duel_root, 'compiler', attrib={
        'angle': 'radian',
        'meshdir': 'unitree_h1_assets',
        'autolimits': 'true'
    })
    
    # Option
    ET.SubElement(duel_root, 'option', attrib={
        'timestep': '0.002',
        'gravity': '0 0 -9.81'
    })

    # Defaults and Assets from pitcher XML + batter XML
    duel_root.append(p_root.find('default'))
    asset = p_root.find('asset')
    for mat in b_root.find('asset').findall('material'):
        if mat.attrib.get('name') not in [m.attrib.get('name') for m in asset.findall('material')]:
            asset.append(mat)
    duel_root.append(asset)

    # Worldbody
    wb = ET.SubElement(duel_root, 'worldbody')
    
    # Copy lights, ground, markers from pitcher worldbody
    for item in p_world:
        if item.tag in ['light', 'geom', 'site'] and 'pelvis' not in item.attrib.get('name', ''):
            wb.append(item)

    # Visual Batter's box
    wb.append(ET.Element('geom', attrib={
        'name': 'left_box',
        'type': 'box',
        'size': '0.45 0.9 0.002',
        'pos': '-0.85 0 0.002',
        'rgba': '0.8 0.8 0.8 0.3'
    }))

    # Cameras
    wb.append(ET.Element('camera', attrib={
        'name': 'duel_broadcast_cam',
        'pos': '-9.0 5.0 3.6',
        'xyaxes': '0 -1 0 0.35 0 0.94',
        'fovy': '68'
    }))
    wb.append(ET.Element('camera', attrib={
        'name': 'side_cam',
        'pos': '-3.5 0.5 1.4',
        'xyaxes': '0 -1 0 0.15 0 0.98',
        'fovy': '48'
    }))
    wb.append(ET.Element('camera', attrib={
        'name': 'pitcher_cam',
        'pos': '0 11.5 1.8',
        'xyaxes': '1 0 0 0 -0.2 0.98',
        'fovy': '55'
    }))
    wb.append(ET.Element('camera', attrib={
        'name': 'catcher_cam',
        'mode': 'targetbody',
        'target': 'p_pelvis',
        'pos': '0 -1.5 1.0',
        'fovy': '45'
    }))
    wb.append(ET.Element('camera', attrib={
        'name': 'batter_cam',
        'pos': '-2.8 -2.0 1.8',
        'xyaxes': '0.75 -0.66 0 0.25 0.28 0.93',
        'fovy': '48'
    }))

    # Add Pitcher and Batter Pelvis bodies
    wb.append(p_pelvis)
    wb.append(b_pelvis)

    # Add Baseball
    ball_body = p_world.find(".//body[@name='baseball']")
    wb.append(ball_body)

    # Contacts
    contact = ET.SubElement(duel_root, 'contact')
    ET.SubElement(contact, 'exclude', attrib={'body1': 'p_torso_link', 'body2': 'p_right_shoulder_roll_link'})
    ET.SubElement(contact, 'exclude', attrib={'body1': 'p_torso_link', 'body2': 'p_left_shoulder_roll_link'})
    ET.SubElement(contact, 'exclude', attrib={'body1': 'b_torso_link', 'body2': 'b_right_shoulder_roll_link'})
    ET.SubElement(contact, 'exclude', attrib={'body1': 'b_torso_link', 'body2': 'b_left_shoulder_roll_link'})
    ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'p_right_elbow_link'})
    ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'b_right_elbow_link'})
    ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'b_left_elbow_link'})
    ET.SubElement(contact, 'pair', attrib={
        'geom1': 'bat_barrel',
        'geom2': 'ball_geom',
        'solref': '0.0015 1',
        'solimp': '0.95 0.99 0.001 0.5 2',
        'friction': '0.4 0.01 0.001'
    })

    # Actuators
    actuators = ET.SubElement(duel_root, 'actuator')
    p_act = p_root.find('actuator')
    prefix_elements(p_act, 'p')
    for a in p_act:
        actuators.append(a)

    b_act = b_root.find('actuator')
    prefix_elements(b_act, 'b')
    for a in b_act:
        actuators.append(a)

    # Equality
    equality = ET.SubElement(duel_root, 'equality')
    ET.SubElement(equality, 'weld', attrib={
        'name': 'p_ball_weld',
        'site1': 'p_pitcher_hand_site',
        'site2': 'ball_site'
    })

    # Write output
    out_path = os.path.join(BASE_DIR, 'models', 'h1_bipedal_duel.xml')
    tree = ET.ElementTree(duel_root)
    ET.indent(tree, space="  ")
    tree.write(out_path, encoding='utf-8', xml_declaration=True)
    print(f"Generated {out_path} successfully!")

    # Verify loading with MuJoCo
    m = mujoco.MjModel.from_xml_path(out_path)
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    print(f"MuJoCo Verification: Successfully loaded {out_path}")
    print(f"  Total bodies: {m.nbody}")
    print(f"  Total joints: {m.njnt}")
    print(f"  Total actuators: {m.nu}")
    print(f"  Total geoms: {m.ngeom}")
    print(f"  Pitcher pelvis: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'p_pelvis')}")
    print(f"  Batter pelvis: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'b_pelvis')}")
    print(f"  Batter pelvis freejoint: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, 'b_pelvis_joint')}")
    print(f"  Baseball freejoint: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, 'ball_joint')}")


if __name__ == '__main__':
    build_bipedal_duel_xml()
