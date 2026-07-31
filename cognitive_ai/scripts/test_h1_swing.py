import mujoco
from mujoco import viewer
import time
import numpy as np

def test_h1_swing():
    model = mujoco.MjModel.from_xml_path('shared_assets/h1_baseball.xml')
    data = mujoco.MjData(model)
    
    # We will override these joints kinematically
    j_names = ["root_y", "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"]
    j_adrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in j_names]
    
    # Dummy keyframes [root_y, torso, rs_p, rs_r, rs_y, r_elbow]
    # Stance -> Load -> Stride -> Contact -> Follow-through
    # root_y is kept 0 to prevent the robot from flying (No-stride swing)
    keyframes = np.array([
        [0.0, -0.5, -1.0, 0.0, 0.5, 1.5],   # Stance
        [0.0, -1.0, -1.2, 0.0, 0.8, 2.0],   # Load
        [0.0, 0.0, -0.5, 0.0, 0.0, 1.0],    # Stride (Hip turn only)
        [0.0, 1.5, 0.5, 0.0, -0.5, 0.0],    # Contact
        [0.0, 2.0, 1.0, 0.0, -1.0, 1.5]     # Follow-through
    ])
    
    print("Testing H1 Humanoid Baseball Environment...")
    
    with viewer.launch_passive(model, data) as v:
        # Give it a second to settle equality constraints
        for _ in range(100):
            mujoco.mj_step(model, data)
            
        t = 0
        while v.is_running():
            # Oscillate progress 0 -> 1 -> 0
            progress = (np.sin(t) + 1) / 2
            
            num_kfs = len(keyframes)
            scaled = progress * (num_kfs - 1)
            idx1 = int(np.floor(scaled))
            idx2 = min(idx1 + 1, num_kfs - 1)
            alpha = scaled - idx1
            
            current = (1-alpha)*keyframes[idx1] + alpha*keyframes[idx2]
            
            for i, adr in enumerate(j_adrs):
                data.qpos[adr] = current[i]
                jnt_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, j_names[i])
                vel_adr = model.jnt_dofadr[jnt_id]
                data.qvel[vel_adr] = 0.0
                
            mujoco.mj_step(model, data)
            v.sync()
            time.sleep(0.01)
            t += 0.02

if __name__ == "__main__":
    test_h1_swing()
