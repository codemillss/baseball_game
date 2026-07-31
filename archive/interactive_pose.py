import mujoco
from mujoco import viewer
import time
import numpy as np

model = mujoco.MjModel.from_xml_path('assets/stadium_3d.xml')
data = mujoco.MjData(model)

def key_callback(keycode):
    # Print joint angles when 'P' is pressed
    if chr(keycode).lower() == 'p':
        print("\n--- Current Joint Angles (qpos) ---")
        for i in range(model.nq):
            # Try to get joint name based on qpos adr mapping
            for j in range(model.njnt):
                if model.jnt_qposadr[j] == i:
                    joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, j)
                    print(f"{joint_name}: {data.qpos[i]:.4f}")
        print("-----------------------------------")

with viewer.launch_passive(model, data, key_callback=key_callback) as v:
    print("Interactive Viewer Launched!")
    print("1. Physics is intentionally PAUSED so you can pose the robot.")
    print("2. Open the 'Joints' panel on the right side.")
    print("3. Adjust the sliders. The robot will move immediately.")
    print("4. Press 'P' on your keyboard to print the current joint angles!")
    
    while v.is_running():
        # Update geometry based on user's GUI slider changes
        mujoco.mj_forward(model, data)
        v.sync()
        time.sleep(0.01)
