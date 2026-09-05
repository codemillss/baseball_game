import xml.etree.ElementTree as ET

def fix_xml(filename, prefix):
    tree = ET.parse(filename)
    root = tree.getroot()
    actuator = root.find("actuator")
    for motor in actuator.findall("motor"):
        joint = motor.get("joint")
        if joint == "base_x": motor.set("joint", f"{prefix}_x")
        elif joint == "base_y": motor.set("joint", f"{prefix}_y")
        elif joint == "base_yaw": motor.set("joint", f"{prefix}_yaw")
        
        name = motor.get("name")
        if name == "base_x": motor.set("name", f"{prefix}_x")
        elif name == "base_y": motor.set("name", f"{prefix}_y")
        elif name == "base_yaw": motor.set("name", f"{prefix}_yaw")

    tree.write(filename)

fix_xml("shared_assets/h1_catcher.xml", "catcher")
fix_xml("shared_assets/h1_runner.xml", "runner")
