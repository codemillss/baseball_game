import xml.etree.ElementTree as ET

stadium_tree = ET.parse('assets/stadium_3d.xml')
stadium_root = stadium_tree.getroot()

humanoid_tree = ET.parse('humanoid_tmp.xml')
humanoid_root = humanoid_tree.getroot()

# 1. Add humanoid defaults
stadium_default = stadium_root.find('default')
humanoid_default = humanoid_root.find('default')
if humanoid_default is not None:
    for child in humanoid_default:
        stadium_default.append(child)

# 2. Add humanoid assets
stadium_asset = stadium_root.find('asset')
humanoid_asset = humanoid_root.find('asset')
if humanoid_asset is not None:
    for child in humanoid_asset:
        # Avoid duplicate grid texture
        if child.get('name') != 'grid':
            stadium_asset.append(child)

# 3. Add humanoid torso to stadium worldbody
stadium_worldbody = stadium_root.find('worldbody')
# Remove old custom batter_torso
for body in stadium_worldbody.findall('body'):
    if body.get('name') == 'batter_torso':
        stadium_worldbody.remove(body)

humanoid_torso = humanoid_root.find(".//body[@name='torso']")

# Pelvis Pinning: Replace freejoint with nothing or fixed joint.
# To pin it in mid-air at home plate, we set torso pos. Home plate is at 0 0 0.
# Let's place the batter at x=0.6, y=-0.1, z=1.2
humanoid_torso.set('pos', '0.6 -0.1 1.2')
freejoint = humanoid_torso.find('freejoint')
if freejoint is not None:
    humanoid_torso.remove(freejoint) # Pin the pelvis!

# Find the right hand and attach the bat
right_hand = humanoid_torso.find(".//body[@name='hand_right']")
# We need to add the bat bodies to the right hand
bat_xml = """
<body name="bat" pos="0.1 0 0" euler="0 90 0">
  <geom name="bat_knob" type="cylinder" size="0.025 0.015" pos="0 0.015 0" euler="90 0 0" material="wood" mass="0.05"/>
  <geom name="bat_handle" type="cylinder" size="0.014 0.2" pos="0 0.2 0" euler="90 0 0" material="wood" mass="0.25"/>
  <geom name="bat_taper" type="capsule" size="0.024 0.1" pos="0 0.45 0" euler="90 0 0" material="wood" mass="0.2"/>
  <geom name="bat_barrel" type="cylinder" size="0.034 0.25" pos="0 0.675 0" euler="90 0 0" material="wood" mass="0.5" condim="3" friction="0.6 0.1 0.1" solref="0.015 1"/>
</body>
"""
bat_elem = ET.fromstring(bat_xml)
right_hand.append(bat_elem)

# Add camera to the head
head = humanoid_torso.find(".//body[@name='head']")
cam_xml = '<camera name="batter_cam" pos="0.1 0 0" euler="90 0 90" fovy="75"/>'
cam_elem = ET.fromstring(cam_xml)
# Remove egocentric cam if exists
for old_cam in head.findall('camera'):
    head.remove(old_cam)
head.append(cam_elem)

stadium_worldbody.append(humanoid_torso)

# Also update ball physics for bounciness
for geom in stadium_worldbody.findall(".//geom[@name='ball_geom']"):
    geom.set('solref', '0.015 1')

# 4. Add contact, tendon
stadium_contact = ET.SubElement(stadium_root, 'contact')
for exclude in humanoid_root.find('contact'):
    stadium_contact.append(exclude)

stadium_tendon = ET.SubElement(stadium_root, 'tendon')
for tendon in humanoid_root.find('tendon'):
    stadium_tendon.append(tendon)

# 5. Actuators
stadium_actuator = stadium_root.find('actuator')
# Remove old batter actuators
for motor in stadium_actuator.findall('motor'):
    joint_name = motor.get('joint')
    if joint_name in ['shoulder_yaw', 'shoulder_pitch', 'shoulder_roll', 'elbow_flex', 'wrist_yaw', 'wrist_pitch', 'wrist_roll', 'head_yaw', 'head_pitch']:
        stadium_actuator.remove(motor)

for motor in humanoid_root.find('actuator'):
    stadium_actuator.append(motor)

# Fix existing cameras that might have been removed (Wait, they were added to worldbody directly in stadium_3d.xml, they won't be deleted)
# But we should remove the old batter_cam if it was at the root
for cam in stadium_worldbody.findall('camera'):
    if cam.get('name') == 'batter_cam':
        stadium_worldbody.remove(cam)

ET.indent(stadium_tree, space="  ")
stadium_tree.write('humanoid/assets/stadium_3d_humanoid.xml', encoding='utf-8')
print("Successfully created humanoid/assets/stadium_3d_humanoid.xml")
