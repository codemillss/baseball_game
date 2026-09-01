import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_fielder.xml")
root = tree.getroot()

actuator = root.find("actuator")

# Add base actuators
ET.SubElement(actuator, "motor", name="base_x", joint="base_x", gear="500")
ET.SubElement(actuator, "motor", name="base_y", joint="base_y", gear="500")
ET.SubElement(actuator, "motor", name="base_yaw", joint="base_yaw", gear="500")

# The legs are removed, so we should remove their actuators to avoid errors!
leg_joints = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
              "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]
for m in actuator.findall("motor"):
    if m.get("joint") in leg_joints:
        actuator.remove(m)

tree.write("shared_assets/h1_fielder.xml")
