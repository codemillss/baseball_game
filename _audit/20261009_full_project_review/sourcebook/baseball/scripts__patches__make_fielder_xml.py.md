# baseball/scripts/patches/make_fielder_xml.py

원본: [scripts/patches/make_fielder_xml.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/make_fielder_xml.py)

SHA256: `45f930f4cfcef001a0b5db6f4d8cfc2c0bd0c5f204a3ab22dc7c89c7966993fc`

전체 62행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import xml.etree.ElementTree as ET
    2 | 
    3 | tree = ET.parse("shared_assets/h1_pitcher.xml")
    4 | root = tree.getroot()
    5 | 
    6 | root.set("model", "h1_fielder")
    7 | worldbody = root.find("worldbody")
    8 | 
    9 | pelvis = worldbody.find("body[@name='pelvis']")
   10 | worldbody.remove(pelvis)
   11 | 
   12 | base = ET.Element("body", name="fielder_base", pos="0 30 0.4")
   13 | ET.SubElement(base, "joint", name="base_x", type="slide", axis="1 0 0", damping="200")
   14 | ET.SubElement(base, "joint", name="base_y", type="slide", axis="0 1 0", damping="200")
   15 | ET.SubElement(base, "joint", name="base_yaw", type="hinge", axis="0 0 1", damping="100")
   16 | ET.SubElement(base, "geom", type="cylinder", size="0.3 0.1", pos="0 0 0", rgba="0.2 0.2 0.2 1", mass="30.0")
   17 | 
   18 | pelvis.set("name", "fielder_pelvis")
   19 | pelvis.set("pos", "0 0 0.4")
   20 | pelvis.set("quat", "1 0 0 0") # Reset quat to face normally
   21 | 
   22 | legs_to_remove = ["left_hip_yaw_link", "right_hip_yaw_link"]
   23 | for leg_name in legs_to_remove:
   24 |     leg = pelvis.find(f"body[@name='{leg_name}']")
   25 |     if leg is not None:
   26 |         pelvis.remove(leg)
   27 | 
   28 | torso = pelvis.find("body[@name='torso_link']")
   29 | l_shoulder_pitch = torso.find("body[@name='left_shoulder_pitch_link']")
   30 | l_shoulder_roll = l_shoulder_pitch.find("body[@name='left_shoulder_roll_link']")
   31 | l_shoulder_yaw = l_shoulder_roll.find("body[@name='left_shoulder_yaw_link']")
   32 | l_elbow = l_shoulder_yaw.find("body[@name='left_elbow_link']")
   33 | 
   34 | glove = ET.SubElement(l_elbow, "body", name="glove", pos="0.05 0 -0.3")
   35 | ET.SubElement(glove, "geom", name="glove_geom", type="box", size="0.15 0.15 0.1", rgba="0.6 0.3 0.1 1", mass="0.5", friction="2 0.005 0.0001")
   36 | ET.SubElement(glove, "site", name="glove_site", pos="0 0 -0.1", size="0.02", rgba="1 0 0 1")
   37 | 
   38 | base.append(pelvis)
   39 | worldbody.append(base)
   40 | 
   41 | for geom in root.iter("geom"):
   42 |     if geom.get("material") == "pitcher_mat":
   43 |         geom.set("material", "fielder_mat")
   44 | 
   45 | asset = root.find("asset")
   46 | ET.SubElement(asset, "material", name="fielder_mat", rgba="0.2 0.8 0.2 1")
   47 | ET.SubElement(asset, "material", name="ball_mat", rgba="1 1 1 1")
   48 | 
   49 | # Ensure cameras are decent for fielding
   50 | # Remove old cameras
   51 | for cam in worldbody.findall("camera"):
   52 |     worldbody.remove(cam)
   53 | 
   54 | ET.SubElement(worldbody, "camera", name="field_cam", pos="0 0 5.0", xyaxes="1 0 0 0 1 0", fovy="60") # Top down or behind
   55 | ET.SubElement(worldbody, "camera", name="glove_cam", pos="0 -5 2", xyaxes="-1 0 0 0 0.2 0.98", fovy="60") # dynamic cam?
   56 | 
   57 | ball = ET.SubElement(worldbody, "body", name="baseball", pos="0 0 1")
   58 | ET.SubElement(ball, "joint", name="ball_joint", type="free")
   59 | ET.SubElement(ball, "geom", name="ball_geom", type="sphere", size="0.036", mass="0.145", material="ball_mat")
   60 | ET.SubElement(ball, "site", name="ball_site", size="0.036", rgba="1 0 0 0") # Invisible site
   61 | 
   62 | tree.write("shared_assets/h1_fielder.xml")
````
