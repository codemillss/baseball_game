import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_catcher.xml")
worldbody = tree.getroot().find("worldbody")

balls = worldbody.findall("body[@name='baseball']")
if len(balls) > 1:
    worldbody.remove(balls[-1])

tree.write("shared_assets/h1_catcher.xml")
