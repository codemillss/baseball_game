import mujoco
from mujoco import viewer
import time
import numpy as np

def test_humanoid():
    model = mujoco.MjModel.from_xml_path('shared_assets/humanoid_stadium.xml')
    data = mujoco.MjData(model)
    
    print("Testing Humanoid Baseball Environment...")
    
    with viewer.launch_passive(model, data) as v:
        t = 0
        while v.is_running():
            # Slowly rotate spine and move right arm to simulate a swing
            spine_twist = np.sin(t * 2) * 1.5
            r_shoulder_y = np.cos(t * 2) * 1.5 - 1.0 # Lift arm up/down
            
            # Find actuator addresses
            spine_adr = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "a_spine_twist")
            rsy_adr = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "a_r_shoulder_y")
            
            data.ctrl[spine_adr] = spine_twist
            data.ctrl[rsy_adr] = r_shoulder_y
            
            mujoco.mj_step(model, data)
            v.sync()
            time.sleep(0.01)
            t += 0.01

if __name__ == "__main__":
    test_humanoid()
