import xml.etree.ElementTree as ET
import shutil

# Make Catcher XML (Similar to Fielder, but placed behind home plate)
shutil.copy("shared_assets/h1_fielder.xml", "shared_assets/h1_catcher.xml")
tree = ET.parse("shared_assets/h1_catcher.xml")
root = tree.getroot()
worldbody = root.find("worldbody")

# Catcher base starts behind home plate (y = -1.5)
base = worldbody.find("body[@name='fielder_base']")
base.set("name", "catcher_base")
base.set("pos", "0 -1.5 0.4")

# Update joint names
for joint in base.findall("joint"):
    if joint.get("name") == "base_x": joint.set("name", "catcher_x")
    elif joint.get("name") == "base_y": joint.set("name", "catcher_y")
    elif joint.get("name") == "base_yaw": joint.set("name", "catcher_yaw")

tree.write("shared_assets/h1_catcher.xml")

# Make Runner XML (Wheeled base, placed at 1st base)
shutil.copy("shared_assets/h1_fielder.xml", "shared_assets/h1_runner.xml")
tree = ET.parse("shared_assets/h1_runner.xml")
root = tree.getroot()
worldbody = root.find("worldbody")

base = worldbody.find("body[@name='fielder_base']")
base.set("name", "runner_base")
# 1st base is at x=27.4, y=27.4
base.set("pos", "27.4 27.4 0.4")

for joint in base.findall("joint"):
    if joint.get("name") == "base_x": joint.set("name", "runner_x")
    elif joint.get("name") == "base_y": joint.set("name", "runner_y")
    elif joint.get("name") == "base_yaw": joint.set("name", "runner_yaw")

tree.write("shared_assets/h1_runner.xml")
