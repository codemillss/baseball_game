import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_fielder.xml")
root = tree.getroot()
worldbody = root.find("worldbody")

# Remove the default checkered floor geom if it exists
for geom in worldbody.findall("geom"):
    if geom.get("name") == "floor" or geom.get("type") == "plane":
        worldbody.remove(geom)

# Add stadium include before worldbody
# Wait, include is usually at the top level
include = ET.Element("include", file="stadium.xml")
root.insert(0, include)

tree.write("shared_assets/h1_fielder.xml")
