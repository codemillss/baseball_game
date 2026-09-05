"""
Builds the Unified Pitcher vs Batter Duel Arena XML (models/h1_duel_match.xml).
Places H1 Pitcher on the mound (y=10.0m) and H1 Batter at home plate (x=-0.90m, y=0.0m)
with distinct joint and actuator namespaces (p_ and b_).
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


def main():
    p_tree = ET.parse(os.path.join(BASE_DIR, 'models', 'h1_pitcher.xml'))
    b_tree = ET.parse(os.path.join(BASE_DIR, 'models', 'h1_baseball.xml'))

    p_root = p_tree.getroot()
    b_root = b_tree.getroot()

    p_world = p_root.find('worldbody')
    b_world = b_root.find('worldbody')

    # Pitcher pelvis
    p_pelvis = p_world.find(".//body[@name='pelvis']")
    prefix_elements(p_pelvis, 'p')

    # Batter pelvis
    b_pelvis = b_world.find(".//body[@name='pelvis']")
    b_pelvis.attrib['pos'] = "-0.90 0.00 0.95"
    prefix_elements(b_pelvis, 'b')

    # Create root for duel match
    duel_root = ET.Element('mujoco', attrib={'model': 'h1_duel_match'})
    
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

    # Defaults and Assets from pitcher XML
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

    # Cameras
    wb.append(ET.Element('camera', attrib={
        'name': 'duel_broadcast_cam',
        'pos': '-5.5 4.5 2.6',
        'xyaxes': '0.85 -0.52 0 0.18 0.30 0.94',
        'fovy': '52'
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

    # Add Pitcher and Batter Pelvis bodies
    wb.append(p_pelvis)
    wb.append(b_pelvis)

    # Add Baseball
    ball_body = p_world.find(".//body[@name='baseball']")
    wb.append(ball_body)

    # Contacts
    contact = ET.SubElement(duel_root, 'contact')
    ET.SubElement(contact, 'exclude', attrib={'body1': 'p_torso_link', 'body2': 'p_right_shoulder_roll_link'})
    ET.SubElement(contact, 'exclude', attrib={'body1': 'b_torso_link', 'body2': 'b_right_shoulder_roll_link'})
    ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'p_right_elbow_link'})
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
    out_path = os.path.join(BASE_DIR, 'models', 'h1_duel_match.xml')
    tree = ET.ElementTree(duel_root)
    ET.indent(tree, space="  ")
    tree.write(out_path, encoding='utf-8', xml_declaration=True)
    print(f"Generated {out_path} successfully!")

if __name__ == '__main__':
    main()
