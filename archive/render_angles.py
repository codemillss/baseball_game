import mujoco
import cv2
import os

model = mujoco.MjModel.from_xml_path('assets/stadium_3d.xml')
data = mujoco.MjData(model)
mujoco.mj_forward(model, data)

renderer = mujoco.Renderer(model, height=480, width=640)

cameras = ["pitcher_cam", "catcher_cam", "broadcaster_cam", "top_down_cam"]
out_dir = "/Users/jmjeon/.gemini/antigravity-ide/brain/4bdec9f3-e0a2-4d05-aab9-6d6fb58bd3c2"

for i, cam_name in enumerate(cameras):
    renderer.update_scene(data, camera=cam_name)
    img = renderer.render()
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(os.path.join(out_dir, f"stance_{cam_name}.png"), img_bgr)
    print(f"Saved {cam_name}")

# Custom close-up camera on the batter
custom_cam = mujoco.MjvCamera()
custom_cam.type = mujoco.mjtCamera.mjCAMERA_FREE
custom_cam.lookat[:] = [-0.85, 0, 1.3] # Look at batter chest
custom_cam.distance = 2.5
custom_cam.azimuth = 120 # Side view
custom_cam.elevation = -15
renderer.update_scene(data, camera=custom_cam)
img = renderer.render()
img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
cv2.imwrite(os.path.join(out_dir, f"stance_closeup.png"), img_bgr)
print(f"Saved stance_closeup.png")
