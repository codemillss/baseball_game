import mujoco
import cv2
import os
import numpy as np

model = mujoco.MjModel.from_xml_path('assets/stadium_3d.xml')
data = mujoco.MjData(model)

# 7 DOFs: [shoulder_yaw, shoulder_pitch, shoulder_roll, elbow_flex, wrist_yaw, wrist_pitch, wrist_roll]
keyframes = [
    # 1. Stance (Ready)
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    
    # 2. Load (Cocking back)
    [-0.3, 0.1, -0.1, -0.3, -0.2, 0.0, 0.0],
    
    # 3. Initiation (Dropping bat into zone)
    [0.5, -0.2, 0.2, 0.3, 0.2, 0.5, 0.0],
    
    # 4. Contact (Bat extended forward to hit the ball)
    [1.5, -0.4, 0.3, 1.2, 0.5, 0.8, -0.2],
    
    # 5. Follow-through (Bat wraps around)
    [2.2, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0]
]

out_dir = "/Users/jmjeon/.gemini/antigravity-ide/brain/4bdec9f3-e0a2-4d05-aab9-6d6fb58bd3c2"
renderer = mujoco.Renderer(model, height=480, width=640)

# Custom camera to see the full swing clearly
custom_cam = mujoco.MjvCamera()
custom_cam.type = mujoco.mjtCamera.mjCAMERA_FREE
custom_cam.lookat[:] = [0, 0, 1.0] # Look at home plate
custom_cam.distance = 3.5
custom_cam.azimuth = 135 # Front-side view
custom_cam.elevation = -10

# The first 7 qpos are the arm joints, assuming no other free joints before them.
# Let's find the exact qpos addresses for the 7 joints.
joint_names = ["shoulder_yaw", "shoulder_pitch", "shoulder_roll", "elbow_flex", "wrist_yaw", "wrist_pitch", "wrist_roll"]
qpos_adrs = []
for jname in joint_names:
    jnt_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, jname)
    qpos_adrs.append(model.jnt_qposadr[jnt_id])

for idx, kf in enumerate(keyframes):
    # Set joint angles
    for adr, angle in zip(qpos_adrs, kf):
        data.qpos[adr] = angle
        
    mujoco.mj_forward(model, data)
    
    # Render
    renderer.update_scene(data, camera=custom_cam)
    img = renderer.render()
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    filename = os.path.join(out_dir, f"swing_frame_{idx+1}.png")
    cv2.imwrite(filename, img_bgr)
    print(f"Saved {filename}")
