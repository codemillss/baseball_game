"""
Builds the Phase 7 Arena XML: models/h1_infield_defense.xml
Integrates 3 simultaneous Unitree H1 humanoids:
1. Pitcher (p_): on 10m mound (y=10.0m)
2. Batter-Runner (b_): at home plate (x=-0.75m, y=0.0m), 6-DoF floating pelvis, cardinal hip roll links, held/dropped bat prop handover
3. 1st Baseman Infielder (f_): in 1st base infield (x=5.0m, y=5.0m), 6-DoF floating pelvis, cardinal hip roll links, fielding glove (r=0.12m) on left hand
Also includes 1st base pad at (6.5, 6.5, 0.03m), non-colliding chalk markers, broadcast cameras.
"""

import os
import xml.etree.ElementTree as ET
import mujoco

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def prefix_tree(elem, prefix):
    # Prefix name
    if 'name' in elem.attrib:
        name = elem.attrib['name']
        if not name.startswith(('ground', 'home_plate', 'pitcher_mound', 'pitcher_rubber',
                                'first_base', 'baseline_', 'strike_zone', 'pitch_target',
                                'left_box', 'right_box', 'baseball', 'ball_',
                                'dropped_bat', 'infield_', 'first_base_cam', 'run_tracking_')):
            elem.attrib['name'] = f"{prefix}_{name}"

    # Prefix joint in actuators
    if 'joint' in elem.attrib:
        elem.attrib['joint'] = f"{prefix}_{elem.attrib['joint']}"

    # Prefix body in contacts
    for b_attr in ['body1', 'body2']:
        if b_attr in elem.attrib:
            bname = elem.attrib[b_attr]
            if bname not in ['baseball', 'ground', 'dropped_bat', 'first_base']:
                elem.attrib[b_attr] = f"{prefix}_{bname}"

    # Prefix site references
    for s_attr in ['site1', 'site2']:
        if s_attr in elem.attrib:
            sname = elem.attrib[s_attr]
            if not sname.startswith(('ball_', 'first_base_')):
                elem.attrib[s_attr] = f"{prefix}_{sname}"

    for child in elem:
        prefix_tree(child, prefix)


def build_infield_defense_xml():
    # Load pitcher and bipedal sprint template
    pitcher_xml = os.path.join(BASE_DIR, 'models', 'h1_pitcher.xml')
    sprint_xml = os.path.join(BASE_DIR, 'models', 'h1_bipedal_sprint.xml')

    p_tree = ET.parse(pitcher_xml)
    s_tree = ET.parse(sprint_xml)

    p_root = p_tree.getroot()
    s_root = s_tree.getroot()

    # Root XML
    root = ET.Element('mujoco', attrib={'model': 'h1_infield_defense'})
    ET.SubElement(root, 'compiler', attrib={
        'angle': 'radian',
        'meshdir': 'unitree_h1_assets',
        'autolimits': 'true'
    })
    ET.SubElement(root, 'option', attrib={
        'timestep': '0.002',
        'gravity': '0 0 -9.81'
    })

    # Default
    root.append(s_root.find('default'))

    # Asset
    asset = s_root.find('asset')
    # Add glove material
    glove_mat = ET.Element('material', attrib={
        'name': 'glove_mat',
        'rgba': '0.55 0.32 0.16 1.0',
        'reflectance': '0.2'
    })
    asset.append(glove_mat)
    root.append(asset)

    # Worldbody
    wb = ET.SubElement(root, 'worldbody')

    # Lights
    wb.append(ET.Element('light', attrib={
        'directional': 'true', 'diffuse': '0.85 0.85 0.85', 'specular': '0.25 0.25 0.25',
        'pos': '2 5 14', 'dir': '0 0 -1'
    }))
    wb.append(ET.Element('light', attrib={
        'directional': 'true', 'diffuse': '0.45 0.45 0.45',
        'pos': '-5 -5 10', 'dir': '1 1 -1'
    }))

    # Ground
    wb.append(ET.Element('geom', attrib={
        'name': 'ground', 'type': 'plane', 'size': '50 50 0.1', 'material': 'matplane'
    }))

    # Home plate & Pitcher mound (Non-colliding markers)
    wb.append(ET.Element('geom', attrib={
        'name': 'home_plate', 'type': 'box', 'size': '0.216 0.216 0.005', 'pos': '0 0 0.005',
        'material': 'home_plate_mat', 'contype': '0', 'conaffinity': '0'
    }))
    wb.append(ET.Element('geom', attrib={
        'name': 'pitcher_mound', 'type': 'cylinder', 'size': '1.2 0.01', 'pos': '0 10.0 0.005',
        'material': 'home_plate_mat', 'contype': '0', 'conaffinity': '0'
    }))
    wb.append(ET.Element('geom', attrib={
        'name': 'pitcher_rubber', 'type': 'box', 'size': '0.30 0.07 0.008', 'pos': '0 10.0 0.015',
        'material': 'home_plate_mat', 'contype': '0', 'conaffinity': '0'
    }))

    # 1st Base Pad at (6.5, 6.5, 0.03) and Baseline Chalk
    wb.append(ET.Element('geom', attrib={
        'name': 'first_base', 'type': 'box', 'size': '0.22 0.22 0.03', 'pos': '6.5 6.5 0.03',
        'material': 'base_pad_mat'
    }))
    wb.append(ET.Element('site', attrib={
        'name': 'first_base_site', 'type': 'sphere', 'size': '0.25', 'pos': '6.5 6.5 0.03',
        'rgba': '1 1 0 0.4'
    }))
    wb.append(ET.Element('geom', attrib={
        'name': 'baseline_1b', 'type': 'box', 'size': '0.05 4.6 0.002', 'pos': '3.25 3.35 0.002',
        'quat': '0.92388 0 0 0.38268', 'rgba': '1 1 1 0.6', 'contype': '0', 'conaffinity': '0'
    }))
    wb.append(ET.Element('geom', attrib={
        'name': 'baseline_3b', 'type': 'box', 'size': '0.05 4.6 0.002', 'pos': '-3.25 3.35 0.002',
        'quat': '0.92388 0 0 -0.38268', 'rgba': '1 1 1 0.6', 'contype': '0', 'conaffinity': '0'
    }))

    # Visual Batter's box & Strike Zone
    wb.append(ET.Element('site', attrib={
        'name': 'strike_zone', 'type': 'box', 'size': '0.216 0.02 0.25', 'pos': '0 0 0.80',
        'material': 'strike_zone_mat'
    }))
    wb.append(ET.Element('site', attrib={
        'name': 'pitch_target_point', 'type': 'sphere', 'size': '0.04', 'pos': '0 0.0 0.80',
        'rgba': '0.9 0.2 0.2 0.4'
    }))
    wb.append(ET.Element('geom', attrib={
        'name': 'left_box', 'type': 'box', 'size': '0.45 0.9 0.002', 'pos': '-0.75 0 0.002',
        'rgba': '0.8 0.8 0.8 0.3', 'contype': '0', 'conaffinity': '0'
    }))

    # Broadcast Cameras
    # Infield Broadcast Cam: elevated wide angle showing plate, mound, 1B, and fielding territory
    wb.append(ET.Element('camera', attrib={
        'name': 'infield_broadcast_cam',
        'pos': '-4.2 -2.2 4.2',
        'xyaxes': '0.78 -0.62 0 0.28 0.35 0.89',
        'fovy': '64'
    }))
    # 1st Base Camera: zoomed on 1B bag and runner/fielder intercept play
    wb.append(ET.Element('camera', attrib={
        'name': 'first_base_cam',
        'pos': '8.5 8.5 1.6',
        'xyaxes': '-0.7071 0.7071 0 -0.22 -0.22 0.95',
        'fovy': '50'
    }))
    # Runner tracking cam
    wb.append(ET.Element('camera', attrib={
        'name': 'run_tracking_cam',
        'mode': 'targetbody',
        'target': 'b_pelvis',
        'pos': '-3.0 -2.6 2.2',
        'fovy': '52'
    }))
    # Wide stadium cam
    wb.append(ET.Element('camera', attrib={
        'name': 'stadium_wide',
        'pos': '-6.5 4.5 5.2',
        'xyaxes': '0.75 -0.66 0 0.35 0.40 0.85',
        'fovy': '65'
    }))

    # Baseball with 6-DoF freejoint
    ball_body = ET.Element('body', attrib={'name': 'baseball', 'pos': '0 10.0 1.2'})
    ET.SubElement(ball_body, 'freejoint', attrib={'name': 'ball_joint'})
    ET.SubElement(ball_body, 'geom', attrib={
        'name': 'ball_geom', 'type': 'sphere', 'size': '0.037', 'mass': '0.145',
        'material': 'ball_mat', 'solref': '0.002 1', 'solimp': '0.95 0.99 0.001 0.5 2',
        'friction': '0.4 0.02 0.001'
    })
    ET.SubElement(ball_body, 'site', attrib={'name': 'ball_site', 'pos': '0 0 0', 'size': '0.01'})
    wb.append(ball_body)

    # Dropped bat in sky (z=50m) with freejoint
    drop_body = ET.Element('body', attrib={'name': 'dropped_bat', 'pos': '0 0 50'})
    ET.SubElement(drop_body, 'freejoint', attrib={'name': 'dropped_bat_joint'})
    ET.SubElement(drop_body, 'geom', attrib={
        'name': 'dropped_bat_barrel', 'type': 'capsule', 'size': '0.032 0.40', 'pos': '0 0 0.45',
        'material': 'bat_mat', 'mass': '0.90', 'solref': '0.005 1', 'solimp': '0.90 0.95 0.001 0.5 2',
        'friction': '0.8 0.02 0.001'
    })
    wb.append(drop_body)

    # 1. Pitcher Robot (p_) - anchored at mound (0, 10.0, 0.82)
    p_pelvis = ET.fromstring(ET.tostring(p_root.find(".//worldbody/body[@name='pelvis']")))
    prefix_tree(p_pelvis, 'p')
    p_pelvis.attrib['pos'] = '0 10.0 0.82'
    p_pelvis.attrib['quat'] = '0.7071068 0 0 -0.7071068'
    wb.append(p_pelvis)

    # 2. Batter-Runner Robot (b_) - at home plate (-0.75, 0.0, 0.92) with freejoint
    b_pelvis = ET.fromstring(ET.tostring(s_root.find(".//worldbody/body[@name='pelvis']")))
    prefix_tree(b_pelvis, 'b')
    b_pelvis.attrib['pos'] = '-0.75 0.0 0.92'
    # Ensure freejoint is named b_pelvis_joint
    fj = b_pelvis.find('freejoint')
    if fj is not None:
        fj.attrib['name'] = 'b_pelvis_joint'
    wb.append(b_pelvis)

    # 3. 1st Baseman Infielder Robot (f_) - at 1st base infield (5.0, 5.0, 0.92)
    # Using H1 bipedal template from sprint (which has cardinal-aligned hip rolls!)
    f_pelvis = ET.fromstring(ET.tostring(s_root.find(".//worldbody/body[@name='pelvis']")))
    # Remove held bat from infielder right arm
    right_elbow = f_pelvis.find(".//body[@name='right_elbow_link']")
    if right_elbow is not None:
        for ch in list(right_elbow):
            if 'bat' in ch.attrib.get('name', ''):
                right_elbow.remove(ch)

    # Attach fielding glove to left arm (left_elbow_link)
    left_elbow = f_pelvis.find(".//body[@name='left_elbow_link']")
    if left_elbow is not None:
        # Add f_glove geom (sphere r=0.12m)
        left_elbow.append(ET.Element('geom', attrib={
            'name': 'glove',
            'type': 'sphere',
            'size': '0.12',
            'pos': '0.30 0 0',
            'material': 'glove_mat',
            'friction': '0.8 0.02 0.001',
            'solref': '0.005 1',
            'solimp': '0.92 0.98 0.001 0.5 2'
        }))
        left_elbow.append(ET.Element('site', attrib={
            'name': 'glove_site',
            'type': 'sphere',
            'size': '0.12',
            'pos': '0.30 0 0',
            'rgba': '0.7 0.35 0.15 0.6'
        }))

    prefix_tree(f_pelvis, 'f')
    f_pelvis.attrib['pos'] = '5.0 5.0 0.92'
    # Yaw towards home plate / ball approach (-135 deg)
    f_pelvis.attrib['quat'] = '0.3826834 0 0 -0.9238795'
    fj_f = f_pelvis.find('freejoint')
    if fj_f is not None:
        fj_f.attrib['name'] = 'f_pelvis_joint'
    wb.append(f_pelvis)

    # Contacts Section
    contact = ET.SubElement(root, 'contact')
    for pfx in ['p', 'b', 'f']:
        ET.SubElement(contact, 'exclude', attrib={'body1': f'{pfx}_torso_link', 'body2': f'{pfx}_right_shoulder_roll_link'})
        ET.SubElement(contact, 'exclude', attrib={'body1': f'{pfx}_torso_link', 'body2': f'{pfx}_left_shoulder_roll_link'})

    ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'p_right_elbow_link'})
    ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'b_right_elbow_link'})
    ET.SubElement(contact, 'exclude', attrib={'body1': 'baseball', 'body2': 'b_left_elbow_link'})

    # Batted ball collision pairs
    ET.SubElement(contact, 'pair', attrib={
        'geom1': 'b_held_bat_barrel', 'geom2': 'ball_geom',
        'solref': '0.0015 1', 'solimp': '0.95 0.99 0.001 0.5 2', 'friction': '0.4 0.01 0.001'
    })
    ET.SubElement(contact, 'pair', attrib={
        'geom1': 'f_glove', 'geom2': 'ball_geom',
        'solref': '0.005 1', 'solimp': '0.92 0.98 0.001 0.5 2', 'friction': '0.8 0.02 0.001'
    })
    ET.SubElement(contact, 'pair', attrib={
        'geom1': 'ground', 'geom2': 'ball_geom',
        'solref': '0.002 1', 'solimp': '0.95 0.99 0.001 0.5 2', 'friction': '0.4 0.02 0.001'
    })

    # Actuator Section
    actuators = ET.SubElement(root, 'actuator')

    # Pitcher actuators
    p_act = p_root.find('actuator')
    prefix_tree(p_act, 'p')
    for a in p_act:
        actuators.append(a)

    # Batter actuators
    b_act = ET.fromstring(ET.tostring(s_root.find('actuator')))
    prefix_tree(b_act, 'b')
    for a in b_act:
        actuators.append(a)

    # Infielder actuators
    f_act = ET.fromstring(ET.tostring(s_root.find('actuator')))
    prefix_tree(f_act, 'f')
    for a in f_act:
        actuators.append(a)

    # Equality Section
    equality = ET.SubElement(root, 'equality')
    ET.SubElement(equality, 'weld', attrib={
        'name': 'p_ball_weld',
        'site1': 'p_pitcher_hand_site',
        'site2': 'ball_site'
    })

    # Save to models/h1_infield_defense.xml
    out_path = os.path.join(BASE_DIR, 'models', 'h1_infield_defense.xml')
    tree = ET.ElementTree(root)
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
    print(f"  Infielder pelvis: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'f_pelvis')}")
    print(f"  Fielding glove geom: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, 'f_glove')}")
    print(f"  Fielding glove site: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, 'f_glove_site')}")
    print(f"  1st base geom: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, 'first_base')}")
    print(f"  Infield broadcast cam: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_CAMERA, 'infield_broadcast_cam')}")
    print(f"  First base cam: {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_CAMERA, 'first_base_cam')}")


if __name__ == '__main__':
    build_infield_defense_xml()
