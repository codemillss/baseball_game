import mujoco
import cv2

model = mujoco.MjModel.from_xml_path("shared_assets/h1_baseball.xml")
data = mujoco.MjData(model)
mujoco.mj_forward(model, data)

renderer = mujoco.Renderer(model, height=480, width=640)

# Check all cameras
for cam_name in ["pitcher_cam", "batter_cam", "side_cam", "front_cam"]:
    try:
        renderer.update_scene(data, camera=cam_name)
        img = renderer.render()
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(f"data/{cam_name}.png", bgr)
        print(f"Rendered {cam_name}")
    except Exception as e:
        print(f"Error {cam_name}: {e}")
