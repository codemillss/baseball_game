import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_fielder.xml")
root = tree.getroot()

asset = root.find("asset")
ET.SubElement(asset, "texture", type="2d", name="grid", builtin="checker", rgb1="0.1 0.5 0.1", rgb2="0.2 0.6 0.2", width="300", height="300")
ET.SubElement(asset, "material", name="grid_mat", texture="grid", texrepeat="50 50", texuniform="true")

worldbody = root.find("worldbody")
for geom in worldbody.findall("geom"):
    if geom.get("name") == "grass":
        geom.set("material", "grid_mat")
        # Remove rgba since material overrides it
        if "rgba" in geom.attrib:
            del geom.attrib["rgba"]

# Also let's add a static reference pole at the origin so we can see the robot moving away from it
ET.SubElement(worldbody, "geom", name="origin_pole", type="cylinder", size="0.2 5.0", pos="0 0 5", rgba="1 0 0 1")

# And another one at y=20
ET.SubElement(worldbody, "geom", name="marker_20", type="cylinder", size="0.2 5.0", pos="0 20 5", rgba="1 1 0 1")

tree.write("shared_assets/h1_fielder.xml")
