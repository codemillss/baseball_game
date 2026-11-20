# baseball/shared_assets/humanoid_stadium.xml

원본: [shared_assets/humanoid_stadium.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/shared_assets/humanoid_stadium.xml)

SHA256: `e8c8131eeb58464a8116ae313bcb91b53651fbc14bd3697a429685de3ea42969`

전체 195행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <mujoco model="stadium_3d_humanoid">
    2 |   <compiler angle="radian" coordinate="local"/>
    3 |   <option gravity="0 0 -9.81" timestep="0.005"/>
    4 |   <size nconmax="500" njmax="1000"/>
    5 | 
    6 |   <asset>
    7 |     <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="512"/>
    8 |     <texture name="texplane" type="2d" builtin="checker" rgb1="0.2 0.3 0.4" rgb2="0.1 0.15 0.2" width="512" height="512"/>
    9 |     <material name="matplane" reflectance="0.3" texture="texplane" texrepeat="1 1" texuniform="true"/>
   10 |     <material name="infield_dirt_mat" rgba="0.6 0.4 0.2 1" reflectance="0.1"/>
   11 |     <material name="home_plate_mat" rgba="0.9 0.9 0.9 1" reflectance="0.2"/>
   12 |     <material name="ball_mat" rgba="0.98 0.98 0.95 1" reflectance="0.4"/>
   13 |     <material name="bat_mat" rgba="0.8 0.6 0.3 1" reflectance="0.3"/>
   14 |     <material name="human_mat" rgba="0.8 0.6 0.5 1"/>
   15 |   </asset>
   16 | 
   17 |   <default>
   18 |     <!-- Basic defaults for joints and geoms -->
   19 |     <joint limited="true" damping="0.5" armature="0.1"/>
   20 |     <geom friction="0.8 0.1 0.1" margin="0.001" condim="3"/>
   21 |     
   22 |     <!-- Humanoid geom defaults -->
   23 |     <default class="humanoid">
   24 |       <geom type="capsule" material="human_mat"/>
   25 |     </default>
   26 |   </default>
   27 | 
   28 |   <worldbody>
   29 |     <light directional="true" diffuse="0.8 0.8 0.8" specular="0.2 0.2 0.2" pos="0 0 10" dir="0 0 -1"/>
   30 |     
   31 |     <!-- Ground and field markings -->
   32 |     <geom name="ground" type="plane" size="30 30 0.1" material="matplane"/>
   33 |     <geom name="home_plate" type="box" size="0.22 0.22 0.005" pos="0 0 0.005" material="home_plate_mat"/>
   34 |     <geom name="pitcher_mound" type="box" size="0.3 0.1 0.005" pos="0 18.44 0.005" material="home_plate_mat"/>
   35 |     
   36 |     <!-- Cameras -->
   37 |     <camera name="pitcher_cam" pos="0 20.0 2.0" xyaxes="-1 0 0 0 0 1" fovy="60"/>
   38 |     <camera name="catcher_cam" pos="0 -2.0 1.2" xyaxes="1 0 0 0 0 1" fovy="60"/>
   39 |     <camera name="top_down_cam" pos="0 9.0 25.0" euler="0 0 0" fovy="70"/>
   40 |     
   41 |     <!-- Baseball -->
   42 |     <body name="baseball" pos="0 15 1.5">
   43 |       <freejoint name="ball_joint"/>
   44 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat"/>
   45 |     </body>
   46 | 
   47 |     <!-- Full-body Humanoid Batter -->
   48 |     <!-- Positioned on the right side of home plate for a RHB -->
   49 |     <body name="pelvis" pos="-0.85 0 1.0">
   50 |       <!-- 6-DOF Root to allow striding and hip rotation without falling over (for kinematic control) -->
   51 |       <joint name="root_x" type="slide" axis="1 0 0" limited="false"/>
   52 |       <joint name="root_y" type="slide" axis="0 1 0" limited="false"/>
   53 |       <joint name="root_z" type="slide" axis="0 0 1" limited="false"/>
   54 |       <joint name="root_rx" type="hinge" axis="1 0 0" limited="false"/>
   55 |       <joint name="root_ry" type="hinge" axis="0 1 0" limited="false"/>
   56 |       <joint name="root_rz" type="hinge" axis="0 0 1" limited="false"/>
   57 |       
   58 |       <geom name="pelvis_geom" class="humanoid" size="0.1 0.15" pos="0 0 0" euler="1.57 0 0"/>
   59 |       
   60 |       <!-- Right Leg -->
   61 |       <body name="r_thigh" pos="0 -0.15 -0.1">
   62 |         <joint name="r_hip_x" type="hinge" axis="1 0 0" range="-1.5 1.5"/>
   63 |         <joint name="r_hip_y" type="hinge" axis="0 1 0" range="-1.5 1.5"/>
   64 |         <joint name="r_hip_z" type="hinge" axis="0 0 1" range="-1.5 1.5"/>
   65 |         <geom name="r_thigh_geom" class="humanoid" size="0.08 0.20" pos="0 0 -0.20"/>
   66 |         <body name="r_shin" pos="0 0 -0.40">
   67 |           <joint name="r_knee" type="hinge" axis="0 1 0" range="-2.5 0"/>
   68 |           <geom name="r_shin_geom" class="humanoid" size="0.07 0.18" pos="0 0 -0.18"/>
   69 |           <body name="r_foot" pos="0 0 -0.36">
   70 |             <joint name="r_ankle_x" type="hinge" axis="1 0 0" range="-0.5 0.5"/>
   71 |             <joint name="r_ankle_y" type="hinge" axis="0 1 0" range="-0.5 0.5"/>
   72 |             <geom name="r_foot_geom" type="box" size="0.12 0.06 0.02" pos="0.06 0 -0.02" material="human_mat"/>
   73 |           </body>
   74 |         </body>
   75 |       </body>
   76 |       
   77 |       <!-- Left Leg -->
   78 |       <body name="l_thigh" pos="0 0.15 -0.1">
   79 |         <joint name="l_hip_x" type="hinge" axis="1 0 0" range="-1.5 1.5"/>
   80 |         <joint name="l_hip_y" type="hinge" axis="0 1 0" range="-1.5 1.5"/>
   81 |         <joint name="l_hip_z" type="hinge" axis="0 0 1" range="-1.5 1.5"/>
   82 |         <geom name="l_thigh_geom" class="humanoid" size="0.08 0.20" pos="0 0 -0.20"/>
   83 |         <body name="l_shin" pos="0 0 -0.40">
   84 |           <joint name="l_knee" type="hinge" axis="0 1 0" range="-2.5 0"/>
   85 |           <geom name="l_shin_geom" class="humanoid" size="0.07 0.18" pos="0 0 -0.18"/>
   86 |           <body name="l_foot" pos="0 0 -0.36">
   87 |             <joint name="l_ankle_x" type="hinge" axis="1 0 0" range="-0.5 0.5"/>
   88 |             <joint name="l_ankle_y" type="hinge" axis="0 1 0" range="-0.5 0.5"/>
   89 |             <geom name="l_foot_geom" type="box" size="0.12 0.06 0.02" pos="0.06 0 -0.02" material="human_mat"/>
   90 |           </body>
   91 |         </body>
   92 |       </body>
   93 | 
   94 |       
   95 |       <!-- Spine (Twist) -->
   96 |       <body name="torso" pos="0 0 0.2">
   97 |         <joint name="spine_twist" type="hinge" axis="0 0 1" range="-1.5 1.5"/>
   98 |         <geom name="torso_geom" class="humanoid" size="0.12 0.25" pos="0 0 0.2"/>
   99 |         
  100 |         <!-- Head -->
  101 |         <body name="head" pos="0 0 0.6">
  102 |           <joint name="neck_pitch" type="hinge" axis="1 0 0" range="-0.5 0.5"/>
  103 |           <geom name="head_geom" class="humanoid" type="sphere" size="0.12" pos="0 0 0"/>
  104 |           <camera name="batter_cam" pos="0 0 0" xyaxes="1 0 0 0 0 1" fovy="90"/>
  105 |         </body>
  106 |         
  107 |         <!-- Right Arm (Back arm for RHB) -->
  108 |         <body name="r_upper_arm" pos="-0.15 0 0.4">
  109 |           <joint name="r_shoulder_z" type="hinge" axis="0 0 1" range="-1.5 1.5"/>
  110 |           <joint name="r_shoulder_y" type="hinge" axis="0 1 0" range="-1.5 1.5"/>
  111 |           <joint name="r_shoulder_x" type="hinge" axis="1 0 0" range="-1.5 1.5"/>
  112 |           <geom name="r_ua_geom" class="humanoid" size="0.04 0.15" pos="0 0 -0.15"/>
  113 |           
  114 |           <body name="r_lower_arm" pos="0 0 -0.3">
  115 |             <joint name="r_elbow" type="hinge" axis="0 1 0" range="0 2.5"/>
  116 |             <geom name="r_la_geom" class="humanoid" size="0.03 0.15" pos="0 0 -0.15"/>
  117 |             
  118 |             <body name="r_hand" pos="0 0 -0.3">
  119 |               <joint name="r_wrist_x" type="hinge" axis="1 0 0" range="-0.5 0.5"/>
  120 |               <joint name="r_wrist_y" type="hinge" axis="0 1 0" range="-0.5 0.5"/>
  121 |               <geom name="r_hand_geom" type="sphere" size="0.04" material="human_mat"/>
  122 |               
  123 |               <!-- Bat attached to Right Hand -->
  124 |               <body name="bat" pos="0 0 -0.1">
  125 |                 <!-- No joints relative to hand, fixed to hand -->
  126 |                 <!-- The bat points downwards slightly in neutral pose -->
  127 |                 <geom name="bat_barrel" type="cylinder" size="0.03 0.45" pos="0 0 -0.45" material="bat_mat" mass="0.9"/>
  128 |                 <!-- Site for the left hand to grab onto -->
  129 |                 <site name="bat_grip_left" pos="0 0 0.05" size="0.01"/>
  130 |               </body>
  131 |             </body>
  132 |           </body>
  133 |         </body>
  134 |         
  135 |         <!-- Left Arm (Front arm for RHB) -->
  136 |         <body name="l_upper_arm" pos="0.15 0 0.4">
  137 |           <joint name="l_shoulder_z" type="hinge" axis="0 0 1" range="-1.5 1.5"/>
  138 |           <joint name="l_shoulder_y" type="hinge" axis="0 1 0" range="-1.5 1.5"/>
  139 |           <joint name="l_shoulder_x" type="hinge" axis="1 0 0" range="-1.5 1.5"/>
  140 |           <geom name="l_ua_geom" class="humanoid" size="0.04 0.15" pos="0 0 -0.15"/>
  141 |           
  142 |           <body name="l_lower_arm" pos="0 0 -0.3">
  143 |             <joint name="l_elbow" type="hinge" axis="0 1 0" range="0 2.5"/>
  144 |             <geom name="l_la_geom" class="humanoid" size="0.03 0.15" pos="0 0 -0.15"/>
  145 |             
  146 |             <body name="l_hand" pos="0 0 -0.3">
  147 |               <!-- Site to connect to the bat -->
  148 |               <site name="l_hand_grip" pos="0 0 0" size="0.01"/>
  149 |               <geom name="l_hand_geom" type="sphere" size="0.04" material="human_mat"/>
  150 |             </body>
  151 |           </body>
  152 |         </body>
  153 |         
  154 |       </body>
  155 |     </body>
  156 |   </worldbody>
  157 |   
  158 |   <equality>
  159 |     <!-- Connect left hand to the bat to form a closed kinematic chain (2-handed grip) -->
  160 |     <!-- The constraint brings l_hand_grip to bat_grip_left -->
  161 |     <connect name="left_hand_to_bat" site1="l_hand_grip" site2="bat_grip_left"/>
  162 |   </equality>
  163 |   
  164 |   <actuator>
  165 |     <!-- Add basic position actuators for kinematic control -->
  166 |     <position name="a_spine_twist" joint="spine_twist" kp="500"/>
  167 |     <position name="a_r_shoulder_z" joint="r_shoulder_z" kp="500"/>
  168 |     <position name="a_r_shoulder_y" joint="r_shoulder_y" kp="500"/>
  169 |     <position name="a_r_shoulder_x" joint="r_shoulder_x" kp="500"/>
  170 |     <position name="a_r_elbow" joint="r_elbow" kp="500"/>
  171 |     <position name="a_r_wrist_x" joint="r_wrist_x" kp="500"/>
  172 |     <position name="a_r_wrist_y" joint="r_wrist_y" kp="500"/>
  173 |     
  174 |     <!-- Left arm actuators REMOVED so the equality constraint can naturally pull the arm to the bat -->
  175 | 
  176 |     
  177 |     <!-- Leg actuators -->
  178 |     <position name="a_root_x" joint="root_x" kp="1000"/>
  179 |     <position name="a_root_y" joint="root_y" kp="1000"/>
  180 |     <position name="a_root_z" joint="root_z" kp="1000"/>
  181 |     <position name="a_root_rx" joint="root_rx" kp="1000"/>
  182 |     <position name="a_root_ry" joint="root_ry" kp="1000"/>
  183 |     <position name="a_root_rz" joint="root_rz" kp="1000"/>
  184 |     
  185 |     <position name="a_r_hip_x" joint="r_hip_x" kp="500"/>
  186 |     <position name="a_r_hip_y" joint="r_hip_y" kp="500"/>
  187 |     <position name="a_r_hip_z" joint="r_hip_z" kp="500"/>
  188 |     <position name="a_r_knee" joint="r_knee" kp="500"/>
  189 |     <position name="a_l_hip_x" joint="l_hip_x" kp="500"/>
  190 |     <position name="a_l_hip_y" joint="l_hip_y" kp="500"/>
  191 |     <position name="a_l_hip_z" joint="l_hip_z" kp="500"/>
  192 |     <position name="a_l_knee" joint="l_knee" kp="500"/>
  193 |   </actuator>
  194 |   
  195 | </mujoco>
````
