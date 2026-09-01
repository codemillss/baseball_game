import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_pitcher.xml")
root = tree.getroot()

root.set("model", "h1_fielder")
worldbody = root.find("worldbody")

pelvis = worldbody.find("body[@name='pelvis']")
worldbody.remove(pelvis)

base = ET.Element("body", name="fielder_base", pos="0 30 0.4")
ET.SubElement(base, "joint", name="base_x", type="slide", axis="1 0 0", damping="200")
ET.SubElement(base, "joint", name="base_y", type="slide", axis="0 1 0", damping="200")
ET.SubElement(base, "joint", name="base_yaw", type="hinge", axis="0 0 1", damping="100")
ET.SubElement(base, "geom", type="cylinder", size="0.3 0.1", pos="0 0 0", rgba="0.2 0.2 0.2 1", mass="30.0")

pelvis.set("name", "fielder_pelvis")
pelvis.set("pos", "0 0 0.4")
pelvis.set("quat", "1 0 0 0") # Reset quat to face normally

legs_to_remove = ["left_hip_yaw_link", "right_hip_yaw_link"]
for leg_name in legs_to_remove:
    leg = pelvis.find(f"body[@name='{leg_name}']")
    if leg is not None:
        pelvis.remove(leg)

torso = pelvis.find("body[@name='torso_link']")
l_shoulder_pitch = torso.find("body[@name='left_shoulder_pitch_link']")
l_shoulder_roll = l_shoulder_pitch.find("body[@name='left_shoulder_roll_link']")
l_shoulder_yaw = l_shoulder_roll.find("body[@name='left_shoulder_yaw_link']")
l_elbow = l_shoulder_yaw.find("body[@name='left_elbow_link']")

glove = ET.SubElement(l_elbow, "body", name="glove", pos="0.05 0 -0.3")
ET.SubElement(glove, "geom", name="glove_geom", type="box", size="0.15 0.15 0.1", rgba="0.6 0.3 0.1 1", mass="0.5", friction="2 0.005 0.0001")
ET.SubElement(glove, "site", name="glove_site", pos="0 0 -0.1", size="0.02", rgba="1 0 0 1")

base.append(pelvis)
worldbody.append(base)

for geom in root.iter("geom"):
    if geom.get("material") == "pitcher_mat":
        geom.set("material", "fielder_mat")

asset = root.find("asset")
ET.SubElement(asset, "material", name="fielder_mat", rgba="0.2 0.8 0.2 1")
ET.SubElement(asset, "material", name="ball_mat", rgba="1 1 1 1")

# Ensure cameras are decent for fielding
# Remove old cameras
for cam in worldbody.findall("camera"):
    worldbody.remove(cam)

ET.SubElement(worldbody, "camera", name="field_cam", pos="0 0 5.0", xyaxes="1 0 0 0 1 0", fovy="60") # Top down or behind
ET.SubElement(worldbody, "camera", name="glove_cam", pos="0 -5 2", xyaxes="-1 0 0 0 0.2 0.98", fovy="60") # dynamic cam?

ball = ET.SubElement(worldbody, "body", name="baseball", pos="0 0 1")
ET.SubElement(ball, "joint", name="ball_joint", type="free")
ET.SubElement(ball, "geom", name="ball_geom", type="sphere", size="0.036", mass="0.145", material="ball_mat")
ET.SubElement(ball, "site", name="ball_site", size="0.036", rgba="1 0 0 0") # Invisible site

tree.write("shared_assets/h1_fielder.xml")
