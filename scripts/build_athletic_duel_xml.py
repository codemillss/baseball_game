import os
import xml.etree.ElementTree as ET
import mujoco

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def build_athletic_duel_xml():
    battery_xml = os.path.join(BASE_DIR, 'models', 'h1_battery_pitch_catch.xml')
    duel_xml = os.path.join(BASE_DIR, 'models', 'h1_bipedal_duel.xml')

    b_tree = ET.parse(battery_xml)
    d_tree = ET.parse(duel_xml)

    b_root = b_tree.getroot()
    d_root = d_tree.getroot()

    # Find b_pelvis in duel_xml
    d_wb = d_root.find('worldbody')
    b_pelvis = None
    for child in d_wb:
        if child.attrib.get('name') == 'b_pelvis':
            b_pelvis = child
            break

    # Adjust b_pelvis initial position to athletic deep stance:
    # x = -0.75m, y = 0.00m, z = 0.86m
    b_pelvis.attrib['pos'] = "-0.75 0.00 0.86"

    # Add b_pelvis to b_root worldbody
    b_wb = b_root.find('worldbody')
    # Place b_pelvis before baseball
    b_wb.append(b_pelvis)

    # Add batter actuators from duel_xml to b_root actuator
    b_actuator = b_root.find('actuator')
    d_actuator = d_root.find('actuator')
    for act in d_actuator:
        aname = act.attrib.get('name', '')
        if aname.startswith('b_'):
            b_actuator.append(act)

    # Add cameras: duel_broadcast_cam, umpire_cam, side_cam
    # Remove existing cameras and add unified set
    for cam in b_wb.findall('camera'):
        b_wb.remove(cam)

    b_wb.append(ET.Element('camera', attrib={
        'name': 'duel_broadcast_cam',
        'pos': '-3.8 -4.2 2.6',
        'xyaxes': '0.74 -0.67 0 0.28 0.31 0.91'
    }))
    b_wb.append(ET.Element('camera', attrib={
        'name': 'umpire_cam',
        'pos': '0.0 -2.4 1.4',
        'xyaxes': '1 0 0 0 0.45 0.89'
    }))
    b_wb.append(ET.Element('camera', attrib={
        'name': 'batter_side_cam',
        'pos': '-3.2 0.0 1.2',
        'xyaxes': '0 1 0 0 0 1'
    }))

    out_path = os.path.join(BASE_DIR, 'models', 'h1_athletic_duel.xml')
    b_tree.write(out_path, encoding='utf-8', xml_declaration=True)
    print(f"Successfully generated {out_path}")

    # Verify loading in mujoco
    model = mujoco.MjModel.from_xml_path(out_path)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    print(f"MuJoCo verification passed! Bodies: {model.nbody}, Joints: {model.njnt}, Actuators: {model.nu}")

if __name__ == '__main__':
    build_athletic_duel_xml()
