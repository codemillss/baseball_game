import re

# Read h1_infield_defense.xml
with open("models/h1_infield_defense.xml", "r") as f:
    xml = f.read()

# Let's extract:
# 1. header and asset
# 2. worldbody basics (ground, home_plate, pitcher_mound, pitcher_rubber, strike_zone, baseball)
# 3. p_pelvis (pitcher)
# 4. c_pelvis (converted from b_pelvis)
# 5. actuators for p_ and c_
# 6. excludes for p_ and c_

# Let's inspect the bodies in h1_infield_defense.xml
# p_pelvis starts at: <body name="p_pelvis"
# b_pelvis starts at: <body name="b_pelvis"
# f_pelvis starts at: <body name="f_pelvis"

p_start = xml.find('<body name="p_pelvis"')
b_start = xml.find('<body name="b_pelvis"')
f_start = xml.find('<body name="f_pelvis"')

# p_pelvis goes from p_start to b_start
p_body = xml[p_start:b_start]

# b_body goes from b_start to f_start
b_body = xml[b_start:f_start]

# Convert b_body to c_body
c_body = b_body.replace('b_', 'c_')

# In c_body, set initial position to x=0.0, y=-0.95, z=0.52, quat facing pitcher (facing +y)
# quat="0.7071068 0 0 0.7071068" rotates 90 deg CCW around Z axis
c_body = re.sub(
    r'<body name="c_pelvis" pos="[^"]*"[^>]*>',
    '<body name="c_pelvis" pos="0.0 -0.95 0.52" quat="0.7071068 0 0 0.7071068" childclass="h1">',
    c_body
)

# Replace held bat in c_body with c_mitt on left arm!
# Note: in b_body, held_bat was on b_right_elbow_link.
# In baseball, a catcher catches with the LEFT hand!
# So we remove held bat from right arm, and add c_mitt to c_left_elbow_link.

# Remove held bat from right arm:
c_body = re.sub(
    r'<body name="c_held_bat".*?</body>\s*</geom>',
    '</geom>',
    c_body,
    flags=re.DOTALL
)
# If held bat was inside c_right_elbow_link:
c_body = re.sub(
    r'<body name="c_held_bat".*?</body>',
    '',
    c_body,
    flags=re.DOTALL
)

# Add c_mitt to c_left_elbow_link:
mitt_xml = '''
        <body name="c_mitt" pos="0.22 0 0" quat="0.7071068 0 0.7071068 0">
          <geom name="c_mitt_geom" type="cylinder" size="0.14 0.04" pos="0 0 0" material="glove_mat" mass="0.45" contype="0" conaffinity="0" />
          <site name="c_mitt_site" type="sphere" size="0.05" pos="0 0 0" rgba="0.9 0.4 0.1 0.6" />
        </body>
'''

# Insert mitt_xml inside c_left_elbow_link before its closing </body>
# Find c_left_elbow_link
idx = c_body.find('<body name="c_left_elbow_link"')
# Find the next </body> for c_left_elbow_link
idx2 = c_body.find('</body>', idx)
c_body = c_body[:idx2] + mitt_xml + c_body[idx2:]

# Now extract actuators for p_ and b_ (rename b_ -> c_)
act_start = xml.find('<actuator>')
act_end = xml.find('</actuator>') + len('</actuator>')
act_xml = xml[act_start:act_end]

# Filter actuators: keep p_ and b_ (rename b_ -> c_), discard f_
act_lines = []
for line in act_xml.splitlines():
    if 'name="f_' in line or 'joint="f_' in line:
        continue
    act_lines.append(line.replace('name="b_', 'name="c_').replace('joint="b_', 'joint="c_'))
new_act_xml = '\n'.join(act_lines)

# Also ensure left arm motors exist for c_
if 'c_left_elbow' not in new_act_xml:
    left_arm_motors = '''
    <motor class="h1" name="c_left_shoulder_pitch" joint="c_left_shoulder_pitch" ctrlrange="-40 40" />
    <motor class="h1" name="c_left_shoulder_roll" joint="c_left_shoulder_roll" ctrlrange="-40 40" />
    <motor class="h1" name="c_left_shoulder_yaw" joint="c_left_shoulder_yaw" ctrlrange="-18 18" />
    <motor class="h1" name="c_left_elbow" joint="c_left_elbow" ctrlrange="-18 18" />
'''
    new_act_xml = new_act_xml.replace('</actuator>', left_arm_motors + '\n  </actuator>')

# Now extract contact / equality / exclude
contact_start = xml.find('<contact>')
if contact_start >= 0:
    contact_end = xml.find('</equality>') + len('</equality>') if '</equality>' in xml else xml.find('</contact>') + len('</contact>')
    # Let's clean up pair geoms: keep ball and mitt pair, remove held_bat pair
    contact_xml = '''  <contact>
    <pair geom1="c_mitt_geom" geom2="ball_geom" solref="0.005 1" solimp="0.80 0.90 0.001 0.5 2" friction="0.8 0.02 0.001" />
  </contact>
  <equality>
    <weld name="pitch_weld" body1="baseball" body2="p_right_elbow_link" relpose="0.25 0 0 1 0 0 0" active="false" />
  </equality>'''
else:
    contact_xml = ''

# Excludes: keep p_ and convert b_ -> c_, discard f_
exclude_start = xml.find('<contact>') if xml.find('<contact>') >= 0 else xml.find('<actuator>')
# Actually excludes are inside <contact> or after worldbody
# In h1_infield_defense.xml, let's see where excludes are:
ex_lines = []
for line in xml.splitlines():
    if '<exclude ' in line:
        if 'f_' in line:
            continue
        ex_lines.append(line.replace('b_', 'c_'))

all_excludes = '\n    '.join(ex_lines)

# Cameras for battery duel:
cameras_xml = '''
    <camera name="battery_broadcast_cam" pos="-3.8 4.8 2.6" xyaxes="0.78 -0.62 0 0.28 0.35 0.89" fovy="58" />
    <camera name="umpire_cam" pos="0.0 -2.4 1.4" xyaxes="1 0 0 0 0.35 0.94" fovy="48" />
    <camera name="pitcher_cam" pos="0.0 11.5 1.8" xyaxes="-1 0 0 0 -0.22 0.97" fovy="50" />
    <camera name="catcher_closeup" pos="-1.5 -0.5 1.2" xyaxes="0.7071 -0.7071 0 0.35 0.35 0.87" fovy="45" />
'''

# Strike zone site: center z=0.85m (standard belt-high strike zone, width=0.43m, height=0.40m)
worldbody_prefix = f'''  <worldbody>
    <light directional="true" diffuse="0.85 0.85 0.85" specular="0.25 0.25 0.25" pos="2 5 14" dir="0 0 -1" />
    <light directional="true" diffuse="0.45 0.45 0.45" pos="-5 -5 10" dir="1 1 -1" />
    <geom name="ground" type="plane" size="50 50 0.1" material="matplane" />
    <geom name="home_plate" type="box" size="0.216 0.216 0.005" pos="0 0 0.005" material="home_plate_mat" contype="0" conaffinity="0" />
    <geom name="pitcher_mound" type="cylinder" size="1.2 0.01" pos="0 10.0 0.005" material="home_plate_mat" contype="0" conaffinity="0" />
    <geom name="pitcher_rubber" type="box" size="0.30 0.07 0.008" pos="0 10.0 0.015" material="home_plate_mat" contype="0" conaffinity="0" />
    <geom name="catcher_box" type="box" size="0.50 0.60 0.002" pos="0 -0.95 0.002" rgba="0.8 0.8 0.8 0.25" contype="0" conaffinity="0" />
    <site name="strike_zone" type="box" size="0.216 0.02 0.20" pos="0 0 0.85" material="strike_zone_mat" />
    <site name="pitch_target_point" type="sphere" size="0.04" pos="0 0.0 0.85" rgba="0.9 0.2 0.2 0.4" />
{cameras_xml}
    <body name="baseball" pos="0 10.0 1.48">
      <freejoint name="ball_joint" />
      <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.4 0.02 0.001" />
      <site name="ball_site" pos="0 0 0" size="0.01" />
    </body>
'''

# Assets & Header:
header_and_asset = xml[:xml.find('<worldbody>')]

final_xml = f'''{header_and_asset}
{worldbody_prefix}
{p_body}
{c_body}
  </worldbody>
  <contact>
    {all_excludes}
    <pair geom1="c_mitt_geom" geom2="ball_geom" solref="0.005 1" solimp="0.80 0.90 0.001 0.5 2" friction="0.8 0.02 0.001" />
  </contact>
  <equality>
    <weld name="pitch_weld" body1="baseball" body2="p_right_elbow_link" relpose="0.25 0 0 1 0 0 0" active="false" />
  </equality>
{new_act_xml}
</mujoco>'''

with open("models/h1_battery_pitch_catch.xml", "w") as f:
    f.write(final_xml)

print("Saved models/h1_battery_pitch_catch.xml successfully.")
