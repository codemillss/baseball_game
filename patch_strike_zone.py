import xml.etree.ElementTree as ET

tree = ET.parse("shared_assets/h1_baseball_match.xml")
root = tree.getroot()
worldbody = root.find("worldbody")

# Add Strike Zone as a transparent site/geom for detection
# site is great for sensors, but geom is good for visual if rgba has low alpha
sz = ET.Element("site", name="strike_zone", type="box", size="0.215 0.215 0.3", pos="-0.3 0 0.8", rgba="0 1 0 0.2")
# Wait, home plate is at -0.3, 0? No, let's check where the batter is.
# Batter pelvis is at x=-0.7, y=-0.45.
# Usually home plate is at 0,0. Let's see where the home plate is in the stadium!
# Actually, baseball rules: Home plate is at 0,0,0. Pitcher is at 0, 18.4, 0 (y=18.4m).
# In our XML, pitcher is at y=10. Batter is at x=-0.7, y=-0.45 (right-handed batter box).
# So home plate is effectively around x=0, y=0!
sz.set("pos", "0 0 0.8")
worldbody.append(sz)

# Add Foul Lines (1st base line, 3rd base line)
# From home plate (0,0) to 1st base (x=27.4, y=27.4) and 3rd base (x=-27.4, y=27.4)
# We can just draw them using cylinders.
# 1st base line: 45 degrees to the right. 3rd base line: 45 degrees to the left.
line1 = ET.Element("geom", name="foul_line_1b", type="cylinder", size="0.05 40", pos="28.28 28.28 0.01", xyaxes="0.707 -0.707 0 0 0 1", rgba="1 1 1 1")
line3 = ET.Element("geom", name="foul_line_3b", type="cylinder", size="0.05 40", pos="-28.28 28.28 0.01", xyaxes="0.707 0.707 0 0 0 1", rgba="1 1 1 1")
# Wait, cylinders point along Z-axis by default.
# To make them lie on the ground pointing at 45 degrees:
# xyaxes specifies X and Y axes.
# We want Z-axis to be along (1, 1, 0).
# Let X-axis be (-1, 1, 0) and Y-axis be (0, 0, 1).
# Then Z = X x Y = (-1, 1, 0) x (0, 0, 1) = (1, 1, 0).
line1.set("xyaxes", "-0.707 0.707 0 0 0 1")
line3.set("xyaxes", "0.707 0.707 0 0 0 1")
worldbody.append(line1)
worldbody.append(line3)

tree.write("shared_assets/h1_baseball_match.xml")
