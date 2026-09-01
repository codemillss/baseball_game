import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_catcher.xml")
worldbody = tree.getroot().find("worldbody")

ball = ET.SubElement(worldbody, "body", name="baseball", pos="0 18.4 1.5")
ET.SubElement(ball, "joint", name="ball_joint", type="free")
ET.SubElement(ball, "geom", name="ball_geom", type="sphere", size="0.036", rgba="1 1 1 1", mass="0.145")

tree.write("shared_assets/h1_catcher.xml")
