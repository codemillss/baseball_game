import mujoco
import numpy as np
import cv2

model = mujoco.MjModel.from_xml_path('assets/stadium_3d.xml')
data = mujoco.MjData(model)
mujoco.mj_forward(model, data)

renderer = mujoco.Renderer(model, height=480, width=640)
# Use a custom camera to see the batter clearly
renderer.update_scene(data, camera="batter_cam")
img_batter = renderer.render()

# Or use catcher cam
renderer.update_scene(data, camera="catcher_cam")
img_catcher = renderer.render()

cv2.imwrite("batter_posture_batter_cam.png", cv2.cvtColor(img_batter, cv2.COLOR_RGB2BGR))
cv2.imwrite("batter_posture_catcher_cam.png", cv2.cvtColor(img_catcher, cv2.COLOR_RGB2BGR))
print("Saved posture images.")
