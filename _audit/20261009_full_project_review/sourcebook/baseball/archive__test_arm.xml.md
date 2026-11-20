# baseball/archive/test_arm.xml

원본: [archive/test_arm.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/test_arm.xml)

SHA256: `ebc00c6b9ea6b15d39dbecf35a3b92c6d91385aec5c89baf94bb7a302d59db76`

전체 45행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | 
    2 | <mujoco>
    3 |   <option gravity="0 0 -9.81"/>
    4 |   <worldbody>
    5 |     <light pos="0 0 10"/>
    6 |     <geom type="plane" size="5 5 0.1" rgba=".9 .9 .9 1"/>
    7 |     
    8 |     <body name="batter_torso" pos="-0.85 -0.1 0">
    9 |       <geom name="torso_geom" type="capsule" size="0.15 0.3" pos="0 0 1.1" rgba="0 0 1 1"/>
   10 |       
   11 |       <!-- Shoulder (3 DOF) -->
   12 |       <body name="shoulder" pos="0 -0.2 1.3">
   13 |         <joint name="shoulder_yaw" type="hinge" axis="0 0 1" range="-90 120"/>
   14 |         <joint name="shoulder_pitch" type="hinge" axis="1 0 0" range="-90 90"/>
   15 |         <joint name="shoulder_roll" type="hinge" axis="0 1 0" range="-90 90"/>
   16 |         <geom name="shoulder_geom" type="sphere" size="0.1" rgba="1 0 0 1"/>
   17 |         <geom name="upper_arm_geom" type="capsule" size="0.06" fromto="0 0 0  0 -0.1 -0.3" rgba="1 1 1 1"/>
   18 |         
   19 |         <!-- Elbow (1 DOF) -->
   20 |         <body name="elbow" pos="0 -0.1 -0.3">
   21 |           <joint name="elbow_flex" type="hinge" axis="0.53 -0.80 0.27" range="-150 150"/>
   22 |           <geom name="elbow_geom" type="sphere" size="0.08" rgba="1 0 0 1"/>
   23 |           <geom name="forearm_geom" type="capsule" size="0.05" fromto="0 0 0  0.3 0.3 0.3" rgba="1 1 1 1"/>
   24 |           
   25 |           <!-- Wrist (3 DOF) -->
   26 |           <body name="wrist" pos="0.3 0.3 0.3">
   27 |             <joint name="wrist_yaw" type="hinge" axis="0 0 1" range="-90 90"/>
   28 |             <joint name="wrist_pitch" type="hinge" axis="1 0 0" range="-90 90"/>
   29 |             <joint name="wrist_roll" type="hinge" axis="0 1 0" range="-90 90"/>
   30 |             <geom name="wrist_geom" type="sphere" size="0.06" rgba="1 0 0 1"/>
   31 |             
   32 |             <!-- Bat (Points UP and BACK) -->
   33 |             <body name="bat" pos="0 0 0" euler="-45 0 0">
   34 |               <geom name="bat_handle" type="cylinder" size="0.014 0.2" pos="0 0 0.2" rgba="0.8 0.6 0.4 1"/>
   35 |               <geom name="bat_barrel" type="cylinder" size="0.034 0.25" pos="0 0 0.675" rgba="0.8 0.6 0.4 1"/>
   36 |             </body>
   37 |           </body>
   38 |         </body>
   39 |       </body>
   40 |     </body>
   41 |     
   42 |     <!-- Home Plate reference -->
   43 |     <geom name="home_plate" type="box" size="0.2 0.2 0.01" pos="0 0 0.005" rgba="1 1 1 1"/>
   44 |   </worldbody>
   45 | </mujoco>
````
