import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_fielder.xml")
root = tree.getroot()

actuator = root.find("actuator")

# Add left arm actuators
ET.SubElement(actuator, "motor", name="left_shoulder_pitch", joint="left_shoulder_pitch", ctrlrange="-100 100")
ET.SubElement(actuator, "motor", name="left_shoulder_roll", joint="left_shoulder_roll", ctrlrange="-100 100")
ET.SubElement(actuator, "motor", name="left_shoulder_yaw", joint="left_shoulder_yaw", ctrlrange="-50 50")
ET.SubElement(actuator, "motor", name="left_elbow", joint="left_elbow", ctrlrange="-50 50")

tree.write("shared_assets/h1_fielder.xml")
