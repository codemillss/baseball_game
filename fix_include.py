import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_fielder.xml")
root = tree.getroot()

# Remove include
for inc in root.findall("include"):
    root.remove(inc)

worldbody = root.find("worldbody")

# Add a nice green grass plane
ET.SubElement(worldbody, "geom", name="grass", type="plane", size="50 50 0.1", rgba="0.1 0.5 0.1 1")

tree.write("shared_assets/h1_fielder.xml")
