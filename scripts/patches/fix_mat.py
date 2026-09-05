import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_fielder.xml")
root = tree.getroot()

asset = root.find("asset")
mats = asset.findall("material")
seen = set()
for m in mats:
    name = m.get("name")
    if name in seen:
        asset.remove(m)
    else:
        seen.add(name)

tree.write("shared_assets/h1_fielder.xml")
