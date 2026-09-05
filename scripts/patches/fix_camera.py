import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_fielder.xml")
root = tree.getroot()
worldbody = root.find("worldbody")

# Remove old field_cam and glove_cam
for cam in worldbody.findall("camera"):
    worldbody.remove(cam)

# Add a camera that covers the outfield.
# The ball lands around y=15 to 30.
# Camera at y=40, z=10, looking back towards y=20.
# xyaxes: x is right (1 0 0), y is up-ish (0 -1 1) -> z is forward-ish (0 -1 -1)
# Actually, let's just use a simple pos and let mujoco's free camera look at it? No, xml cameras are easier.
# Camera at pos="10 40 10" looking at "0 20 0".
# direction dir = (0-10, 20-40, 0-10) = (-10, -20, -10). Normalize.
# Let's just use Euler angles or quat! Or just standard xyaxes.
# If camera is at (0, 45, 10), looking down at (0, 25, 0).
# x-axis = (1, 0, 0).
# y-axis (up on screen) = (0, 10, 20) -> (0, 0.44, 0.89)
# Let's just set pos="0 40 5" xyaxes="1 0 0 0 0.5 0.866" (looks towards -y, slightly down).
ET.SubElement(worldbody, "camera", name="field_cam", pos="0 45 8", xyaxes="1 0 0 0 0.5 0.866", fovy="60")

# Or better yet, attach a camera to the fielder_base so it perfectly tracks the robot!
base = worldbody.find("body[@name='fielder_base']")
ET.SubElement(base, "camera", name="tracking_cam", pos="0 -5 3", xyaxes="1 0 0 0 0.5 0.866", fovy="60")

tree.write("shared_assets/h1_fielder.xml")
