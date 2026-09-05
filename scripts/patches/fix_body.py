import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_fielder.xml")
root = tree.getroot()

worldbody = root.find("worldbody")
bodies = worldbody.findall("body")
seen = set()
for b in bodies:
    name = b.get("name")
    if name in seen:
        worldbody.remove(b)
    else:
        seen.add(name)

tree.write("shared_assets/h1_fielder.xml")
