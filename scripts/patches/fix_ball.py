import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_fielder.xml")
root = tree.getroot()

worldbody = root.find("worldbody")

# Find the first freejoint
for fj in worldbody.findall("freejoint"):
    if fj.get("name") == "ball_joint":
        worldbody.remove(fj)

tree.write("shared_assets/h1_fielder.xml")
