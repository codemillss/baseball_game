# baseball/archive/test_arm.py

원본: [archive/test_arm.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/test_arm.py)

SHA256: `db64c9ad02acb295d544e7711ff8f6aef434c2b559cc14203c49ce933f1d9cd4`

전체 63행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import mujoco
    2 | import numpy as np
    3 | import cv2
    4 | 
    5 | xml_arm = """
    6 | <mujoco>
    7 |   <option gravity="0 0 -9.81"/>
    8 |   <worldbody>
    9 |     <light pos="0 0 10"/>
   10 |     <geom type="plane" size="5 5 0.1" rgba=".9 .9 .9 1"/>
   11 |     
   12 |     <body name="batter_torso" pos="-0.85 -0.1 0">
   13 |       <geom name="torso_geom" type="capsule" size="0.15 0.3" pos="0 0 1.1" rgba="0 0 1 1"/>
   14 |       
   15 |       <!-- Shoulder (3 DOF) -->
   16 |       <body name="shoulder" pos="0 -0.2 1.3">
   17 |         <joint name="shoulder_yaw" type="hinge" axis="0 0 1" range="-90 120"/>
   18 |         <joint name="shoulder_pitch" type="hinge" axis="1 0 0" range="-90 90"/>
   19 |         <joint name="shoulder_roll" type="hinge" axis="0 1 0" range="-90 90"/>
   20 |         <geom name="shoulder_geom" type="sphere" size="0.1" rgba="1 0 0 1"/>
   21 |         <geom name="upper_arm_geom" type="capsule" size="0.06" fromto="0 0 0  0 -0.1 -0.3" rgba="1 1 1 1"/>
   22 |         
   23 |         <!-- Elbow (1 DOF) -->
   24 |         <body name="elbow" pos="0 -0.1 -0.3">
   25 |           <joint name="elbow_flex" type="hinge" axis="0.53 -0.80 0.27" range="-150 150"/>
   26 |           <geom name="elbow_geom" type="sphere" size="0.08" rgba="1 0 0 1"/>
   27 |           <geom name="forearm_geom" type="capsule" size="0.05" fromto="0 0 0  0.3 0.3 0.3" rgba="1 1 1 1"/>
   28 |           
   29 |           <!-- Wrist (3 DOF) -->
   30 |           <body name="wrist" pos="0.3 0.3 0.3">
   31 |             <joint name="wrist_yaw" type="hinge" axis="0 0 1" range="-90 90"/>
   32 |             <joint name="wrist_pitch" type="hinge" axis="1 0 0" range="-90 90"/>
   33 |             <joint name="wrist_roll" type="hinge" axis="0 1 0" range="-90 90"/>
   34 |             <geom name="wrist_geom" type="sphere" size="0.06" rgba="1 0 0 1"/>
   35 |             
   36 |             <!-- Bat (Points UP and BACK) -->
   37 |             <body name="bat" pos="0 0 0" euler="-45 0 0">
   38 |               <geom name="bat_handle" type="cylinder" size="0.014 0.2" pos="0 0 0.2" rgba="0.8 0.6 0.4 1"/>
   39 |               <geom name="bat_barrel" type="cylinder" size="0.034 0.25" pos="0 0 0.675" rgba="0.8 0.6 0.4 1"/>
   40 |             </body>
   41 |           </body>
   42 |         </body>
   43 |       </body>
   44 |     </body>
   45 |     
   46 |     <!-- Home Plate reference -->
   47 |     <geom name="home_plate" type="box" size="0.2 0.2 0.01" pos="0 0 0.005" rgba="1 1 1 1"/>
   48 |   </worldbody>
   49 | </mujoco>
   50 | """
   51 | 
   52 | with open("test_arm.xml", "w") as f:
   53 |     f.write(xml_arm)
   54 | 
   55 | model = mujoco.MjModel.from_xml_path('test_arm.xml')
   56 | data = mujoco.MjData(model)
   57 | mujoco.mj_forward(model, data)
   58 | 
   59 | renderer = mujoco.Renderer(model, height=480, width=640)
   60 | renderer.update_scene(data, camera=-1) # Free camera
   61 | img = renderer.render()
   62 | cv2.imwrite("arm_test.png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
   63 | print("Saved arm_test.png")
````
