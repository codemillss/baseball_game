# baseball/shared_assets/h1_fielder.xml

원본: [shared_assets/h1_fielder.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/shared_assets/h1_fielder.xml)

SHA256: `5b36fb95634e4c5958ab529c93892642714a4ede23d48e0cd54197f40b385ba2`

전체 170행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <mujoco model="h1_fielder">
    2 |   <compiler angle="radian" meshdir="unitree_h1_assets" autolimits="true" />
    3 |   <option timestep="0.005" gravity="0 0 -9.81" />
    4 | 
    5 |   <statistic meansize="0.05" />
    6 | 
    7 |   <default>
    8 |     <default class="h1">
    9 |       <joint damping="1" armature="0.1" />
   10 |       <default class="visual">
   11 |         <geom type="mesh" contype="0" conaffinity="0" group="2" material="black" />
   12 |       </default>
   13 |       <default class="collision">
   14 |         <geom group="3" mass="0" density="0" />
   15 |         <default class="foot">
   16 |           <geom type="capsule" size=".014" />
   17 |           <default class="foot1">
   18 |             <geom fromto="-.035 0 -0.056 .02 0 -0.045" />
   19 |           </default>
   20 |           <default class="foot2">
   21 |             <geom fromto=".02 0 -0.045 .115 0 -0.056" />
   22 |           </default>
   23 |           <default class="foot3">
   24 |             <geom fromto=".14 -.03 -0.056 .14 .03 -0.056" />
   25 |           </default>
   26 |         </default>
   27 |       </default>
   28 |       <site size="0.001" rgba="0.5 0.5 0.5 0.3" group="4" />
   29 |     </default>
   30 |   </default>
   31 | 
   32 |   <asset>
   33 |     <material name="black" rgba="0.1 0.1 0.1 1" />
   34 |     <material name="white" rgba="1 1 1 1" />
   35 | 
   36 |     <mesh file="pelvis.stl" />
   37 |     <mesh file="left_hip_yaw_link.stl" />
   38 |     <mesh file="left_hip_roll_link.stl" />
   39 |     <mesh file="left_hip_pitch_link.stl" />
   40 |     <mesh file="left_knee_link.stl" />
   41 |     <mesh file="left_ankle_link.stl" />
   42 |     <mesh file="right_hip_yaw_link.stl" />
   43 |     <mesh file="right_hip_roll_link.stl" />
   44 |     <mesh file="right_hip_pitch_link.stl" />
   45 |     <mesh file="right_knee_link.stl" />
   46 |     <mesh file="right_ankle_link.stl" />
   47 |     <mesh file="torso_link.stl" />
   48 |     <mesh file="left_shoulder_pitch_link.stl" />
   49 |     <mesh file="left_shoulder_roll_link.stl" />
   50 |     <mesh file="left_shoulder_yaw_link.stl" />
   51 |     <mesh file="left_elbow_link.stl" />
   52 |     <mesh file="right_shoulder_pitch_link.stl" />
   53 |     <mesh file="right_shoulder_roll_link.stl" />
   54 |     <mesh file="right_shoulder_yaw_link.stl" />
   55 |     <mesh file="right_elbow_link.stl" />
   56 |     <mesh file="logo_link.stl" />
   57 |     <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="512" />
   58 |     <texture name="texplane" type="2d" builtin="checker" rgb1="0.2 0.3 0.4" rgb2="0.1 0.15 0.2" width="512" height="512" />
   59 |     <material name="matplane" reflectance="0.3" texture="texplane" texrepeat="1 1" texuniform="true" />
   60 |     <material name="home_plate_mat" rgba="0.9 0.9 0.9 1" reflectance="0.2" />
   61 |     <material name="ball_mat" rgba="0.98 0.98 0.95 1" reflectance="0.4" />
   62 |     <material name="target_zone_mat" rgba="0.2 0.8 0.2 0.4" />
   63 |   <material name="fielder_mat" rgba="0.2 0.8 0.2 1" /><texture type="2d" name="grid" builtin="checker" rgb1="0.1 0.5 0.1" rgb2="0.2 0.6 0.2" width="300" height="300" /><material name="grid_mat" texture="grid" texrepeat="50 50" texuniform="true" /></asset>
   64 | 
   65 |   <worldbody>
   66 |     
   67 |     
   68 |     <light directional="true" diffuse="0.8 0.8 0.8" specular="0.2 0.2 0.2" pos="0 5 10" dir="0 0 -1" />
   69 |     <geom name="home_plate" type="box" size="0.22 0.22 0.005" pos="0 0 0.005" material="home_plate_mat" />
   70 |     <geom name="pitcher_mound" type="cylinder" size="1.2 0.02" pos="0 10.0 0.01" material="home_plate_mat" />
   71 |     
   72 |     
   73 |     <site name="strike_zone_target" type="box" size="0.20 0.02 0.30" pos="0 0.0 0.815" material="target_zone_mat" />
   74 | 
   75 |     
   76 |     <body name="baseball" pos="0 10.0 1.2">
   77 |       <freejoint name="ball_joint" />
   78 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" />
   79 |       <site name="ball_site" pos="0 0 0" size="0.01" />
   80 |     </body>
   81 |   <body name="fielder_base" pos="0 30 0.4"><joint name="base_x" type="slide" axis="1 0 0" damping="200" /><joint name="base_y" type="slide" axis="0 1 0" damping="200" /><joint name="base_yaw" type="hinge" axis="0 0 1" damping="100" /><geom type="cylinder" size="0.3 0.1" pos="0 0 0" rgba="0.2 0.2 0.2 1" mass="30.0" /><body name="fielder_pelvis" pos="0 0 0.4" quat="1 0 0 0" childclass="h1">
   82 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
   83 |       <geom class="visual" mesh="pelvis" />
   84 |       
   85 |       <body name="torso_link">
   86 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00130808 -0.00282289 -0.00349105" mass="17.789" diaginertia="0.487315 0.409628 0.127837" />
   87 |         <joint name="torso" axis="0 0 1" range="-2.35 2.35" />
   88 |         <geom class="visual" mesh="torso_link" />
   89 |         <geom class="visual" material="white" mesh="logo_link" />
   90 |         <geom name="head" class="collision" type="capsule" size="0.06" fromto="0.05 0 0.68 0.05 0 0.6" />
   91 |         <geom name="helmet" class="collision" type="sphere" size="0.073" pos="0.045 0 0.68" />
   92 |         <geom name="torso" class="collision" type="box" size="0.07 0.1 0.22" pos="0 0 0.25" />
   93 |         <geom name="hip" class="collision" type="capsule" size="0.05" fromto="0 -0.1 -0.05 0 0.1 -0.05" />
   94 |         <site name="imu" pos="-0.04452 -0.01891 0.27756" />
   95 | 
   96 |         <body name="left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
   97 |           <inertial pos="0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 -0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
   98 |           <joint name="left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
   99 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  100 |           <body name="left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  101 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  102 |             <joint name="left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  103 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  104 |             <geom name="left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  105 |             <body name="left_shoulder_yaw_link" pos="0 0 -0.1343">
  106 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  107 |               <joint name="left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  108 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  109 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  110 |               <body name="left_elbow_link" pos="0.0185 0 -0.198">
  111 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  112 |                 <joint name="left_elbow" axis="0 1 0" range="-1.25 2.61" />
  113 |                 <geom class="visual" mesh="left_elbow_link" />
  114 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  115 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  116 |               <body name="glove" pos="0.05 0 -0.3"><geom name="glove_geom" type="box" size="0.15 0.15 0.1" rgba="0.6 0.3 0.1 1" mass="0.5" friction="2 0.005 0.0001" /><site name="glove_site" pos="0 0 -0.1" size="0.02" rgba="1 0 0 1" /></body></body>
  117 |             </body>
  118 |           </body>
  119 |         </body>
  120 | 
  121 |         
  122 |         <body name="right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  123 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  124 |           <joint name="right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  125 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  126 |           <body name="right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  127 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  128 |             <joint name="right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  129 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  130 |             <geom name="right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  131 |             <body name="right_shoulder_yaw_link" pos="0 0 -0.1343">
  132 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  133 |               <joint name="right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  134 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  135 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  136 |               <body name="right_elbow_link" pos="0.0185 0 -0.198">
  137 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  138 |                 <joint name="right_elbow" axis="0 1 0" range="-1.25 2.61" />
  139 |                 <geom class="visual" mesh="right_elbow_link" />
  140 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  141 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  142 |                 
  143 |                 <site name="pitcher_hand_site" pos="0.30 0 -0.015" size="0.01" />
  144 |               </body>
  145 |             </body>
  146 |           </body>
  147 |         </body>
  148 |       </body>
  149 |     </body>
  150 | 
  151 |     
  152 |     <camera name="tracking_cam" pos="0 -5 3" xyaxes="1 0 0 0 0.5 0.866" fovy="60" /></body><camera name="field_cam" pos="0 45 8" xyaxes="1 0 0 0 0.5 0.866" fovy="60" /><geom name="grass" type="plane" size="50 50 0.1" material="grid_mat" /><geom name="origin_pole" type="cylinder" size="0.2 5.0" pos="0 0 5" rgba="1 0 0 1" /><geom name="marker_20" type="cylinder" size="0.2 5.0" pos="0 20 5" rgba="1 1 0 1" /></worldbody>
  153 | 
  154 |   <contact>
  155 |     <exclude body1="torso_link" body2="left_shoulder_roll_link" />
  156 |     <exclude body1="torso_link" body2="right_shoulder_roll_link" />
  157 |   </contact>
  158 | 
  159 |   <actuator>
  160 |     <motor class="h1" name="torso" joint="torso" ctrlrange="-200 200" />
  161 |     <motor class="h1" name="right_shoulder_pitch" joint="right_shoulder_pitch" ctrlrange="-100 100" />
  162 |     <motor class="h1" name="right_shoulder_roll" joint="right_shoulder_roll" ctrlrange="-100 100" />
  163 |     <motor class="h1" name="right_shoulder_yaw" joint="right_shoulder_yaw" ctrlrange="-50 50" />
  164 |     <motor class="h1" name="right_elbow" joint="right_elbow" ctrlrange="-50 50" />
  165 |   <motor name="base_x" joint="base_x" gear="500" /><motor name="base_y" joint="base_y" gear="500" /><motor name="base_yaw" joint="base_yaw" gear="500" /><motor name="left_shoulder_pitch" joint="left_shoulder_pitch" ctrlrange="-100 100" /><motor name="left_shoulder_roll" joint="left_shoulder_roll" ctrlrange="-100 100" /><motor name="left_shoulder_yaw" joint="left_shoulder_yaw" ctrlrange="-50 50" /><motor name="left_elbow" joint="left_elbow" ctrlrange="-50 50" /></actuator>
  166 | 
  167 |   <equality>
  168 |     <weld name="ball_weld" site1="pitcher_hand_site" site2="ball_site" />
  169 |   </equality>
  170 | </mujoco>
````
