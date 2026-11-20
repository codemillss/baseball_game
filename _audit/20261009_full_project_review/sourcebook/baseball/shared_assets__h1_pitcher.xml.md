# baseball/shared_assets/h1_pitcher.xml

원본: [shared_assets/h1_pitcher.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/shared_assets/h1_pitcher.xml)

SHA256: `1b49eabe291c344fa69031c3cfd2d08457766e469307b2a68a2c97f6d0f22c54`

전체 249행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <mujoco model="h1_pitcher">
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
   63 |   </asset>
   64 | 
   65 |   <worldbody>
   66 |     <!-- Pitcher robot standing on mound (y = 10.0m facing towards home plate at y = 0) -->
   67 |     <!-- quat="0.7071068 0 0 -0.7071068" rotates +90 deg around Z to face -Y -->
   68 |     <body name="pelvis" pos="0 10.0 0.82" quat="0.7071068 0 0 -0.7071068" childclass="h1">
   69 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
   70 |       <geom class="visual" mesh="pelvis" />
   71 |       
   72 |       <body name="left_hip_yaw_link" pos="0 0.0875 -0.1742">
   73 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
   74 |         <joint name="left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
   75 |         <geom class="visual" mesh="left_hip_yaw_link" />
   76 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
   77 |         <body name="left_hip_roll_link" pos="0.039468 0 0">
   78 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
   79 |           <joint name="left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
   80 |           <geom class="visual" mesh="left_hip_roll_link" />
   81 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
   82 |           <body name="left_hip_pitch_link" pos="0 0.11536 0">
   83 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
   84 |             <joint name="left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
   85 |             <geom class="visual" mesh="left_hip_pitch_link" />
   86 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
   87 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
   88 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
   89 |             <body name="left_knee_link" pos="0 0 -0.4">
   90 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
   91 |               <joint name="left_knee" axis="0 1 0" range="-0.26 2.05" />
   92 |               <geom class="visual" mesh="left_knee_link" />
   93 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
   94 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
   95 |               <body name="left_ankle_link" pos="0 0 -0.4">
   96 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
   97 |                 <joint name="left_ankle" axis="0 1 0" range="-0.87 0.52" />
   98 |                 <geom class="visual" mesh="left_ankle_link" />
   99 |                 <geom class="foot1" />
  100 |                 <geom class="foot2" />
  101 |                 <geom class="foot3" />
  102 |               </body>
  103 |             </body>
  104 |           </body>
  105 |         </body>
  106 |       </body>
  107 | 
  108 |       <body name="right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  109 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  110 |         <joint name="right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  111 |         <geom class="visual" mesh="right_hip_yaw_link" />
  112 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  113 |         <body name="right_hip_roll_link" pos="0.039468 0 0">
  114 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0438242 0.70721 0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  115 |           <joint name="right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  116 |           <geom class="visual" mesh="right_hip_roll_link" />
  117 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  118 |           <body name="right_hip_pitch_link" pos="0 -0.11536 0">
  119 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  120 |             <joint name="right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  121 |             <geom class="visual" mesh="right_hip_pitch_link" />
  122 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  123 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  124 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  125 |             <body name="right_knee_link" pos="0 0 -0.4">
  126 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  127 |               <joint name="right_knee" axis="0 1 0" range="-0.26 2.05" />
  128 |               <geom class="visual" mesh="right_knee_link" />
  129 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  130 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  131 |               <body name="right_ankle_link" pos="0 0 -0.4">
  132 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  133 |                 <joint name="right_ankle" axis="0 1 0" range="-0.87 0.52" />
  134 |                 <geom class="visual" mesh="right_ankle_link" />
  135 |                 <geom class="foot1" />
  136 |                 <geom class="foot2" />
  137 |                 <geom class="foot3" />
  138 |               </body>
  139 |             </body>
  140 |           </body>
  141 |         </body>
  142 |       </body>
  143 | 
  144 |       <body name="torso_link">
  145 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00130808 -0.00282289 -0.00349105" mass="17.789" diaginertia="0.487315 0.409628 0.127837" />
  146 |         <joint name="torso" axis="0 0 1" range="-2.35 2.35" />
  147 |         <geom class="visual" mesh="torso_link" />
  148 |         <geom class="visual" material="white" mesh="logo_link" />
  149 |         <geom name="head" class="collision" type="capsule" size="0.06" fromto="0.05 0 0.68 0.05 0 0.6" />
  150 |         <geom name="helmet" class="collision" type="sphere" size="0.073" pos="0.045 0 0.68" />
  151 |         <geom name="torso" class="collision" type="box" size="0.07 0.1 0.22" pos="0 0 0.25" />
  152 |         <geom name="hip" class="collision" type="capsule" size="0.05" fromto="0 -0.1 -0.05 0 0.1 -0.05" />
  153 |         <site name="imu" pos="-0.04452 -0.01891 0.27756" />
  154 | 
  155 |         <body name="left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  156 |           <inertial pos="0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 -0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  157 |           <joint name="left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  158 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  159 |           <body name="left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  160 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  161 |             <joint name="left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  162 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  163 |             <geom name="left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  164 |             <body name="left_shoulder_yaw_link" pos="0 0 -0.1343">
  165 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  166 |               <joint name="left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  167 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  168 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  169 |               <body name="left_elbow_link" pos="0.0185 0 -0.198">
  170 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  171 |                 <joint name="left_elbow" axis="0 1 0" range="-1.25 2.61" />
  172 |                 <geom class="visual" mesh="left_elbow_link" />
  173 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  174 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  175 |               </body>
  176 |             </body>
  177 |           </body>
  178 |         </body>
  179 | 
  180 |         <!-- Pitching Right Arm -->
  181 |         <body name="right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  182 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  183 |           <joint name="right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  184 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  185 |           <body name="right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  186 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  187 |             <joint name="right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  188 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  189 |             <geom name="right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  190 |             <body name="right_shoulder_yaw_link" pos="0 0 -0.1343">
  191 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  192 |               <joint name="right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  193 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  194 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  195 |               <body name="right_elbow_link" pos="0.0185 0 -0.198">
  196 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  197 |                 <joint name="right_elbow" axis="0 1 0" range="-1.25 2.61" />
  198 |                 <geom class="visual" mesh="right_elbow_link" />
  199 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  200 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  201 |                 <!-- Attachment site for the baseball in pitcher hand -->
  202 |                 <site name="pitcher_hand_site" pos="0.30 0 -0.015" size="0.01" />
  203 |               </body>
  204 |             </body>
  205 |           </body>
  206 |         </body>
  207 |       </body>
  208 |     </body>
  209 | 
  210 |     <!-- Field and Markers -->
  211 |     <light directional="true" diffuse="0.8 0.8 0.8" specular="0.2 0.2 0.2" pos="0 5 10" dir="0 0 -1" />
  212 |     <geom name="ground" type="plane" size="30 30 0.1" material="matplane" />
  213 |     <geom name="home_plate" type="box" size="0.22 0.22 0.005" pos="0 0 0.005" material="home_plate_mat" />
  214 |     <geom name="pitcher_mound" type="cylinder" size="1.2 0.02" pos="0 10.0 0.01" material="home_plate_mat" />
  215 |     
  216 |     <!-- Target Strike Zone visualizer at Home Plate (Y = 0.0m) -->
  217 |     <site name="strike_zone_target" type="box" size="0.20 0.02 0.30" pos="0 0.0 0.815" material="target_zone_mat" />
  218 | 
  219 |     <!-- Cameras -->
  220 |     <camera name="side_cam" pos="-4.0 5.0 2.0" xyaxes="0.9 -0.4 0 0.2 0.4 0.9" fovy="50" />
  221 |     <camera name="pitcher_cam" pos="1.5 12.5 2.0" xyaxes="-0.8 -0.6 0 0.3 -0.4 0.9" fovy="50" />
  222 |     <camera name="behind_pitcher_cam" pos="0 12.5 2.0" xyaxes="1 0 0 0 -0.4 0.9" fovy="50" />
  223 |     <camera name="catcher_cam" pos="0 -2.0 1.2" xyaxes="-1 0 0 0 0.2 0.98" fovy="50" />
  224 | 
  225 |     <!-- Baseball with Weld Constraint to Hand -->
  226 |     <body name="baseball" pos="0 10.0 1.2">
  227 |       <freejoint name="ball_joint" />
  228 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" />
  229 |       <site name="ball_site" pos="0 0 0" size="0.01" />
  230 |     </body>
  231 |   </worldbody>
  232 | 
  233 |   <contact>
  234 |     <exclude body1="torso_link" body2="left_shoulder_roll_link" />
  235 |     <exclude body1="torso_link" body2="right_shoulder_roll_link" />
  236 |   </contact>
  237 | 
  238 |   <actuator>
  239 |     <motor class="h1" name="torso" joint="torso" ctrlrange="-200 200" />
  240 |     <motor class="h1" name="right_shoulder_pitch" joint="right_shoulder_pitch" ctrlrange="-100 100" />
  241 |     <motor class="h1" name="right_shoulder_roll" joint="right_shoulder_roll" ctrlrange="-100 100" />
  242 |     <motor class="h1" name="right_shoulder_yaw" joint="right_shoulder_yaw" ctrlrange="-50 50" />
  243 |     <motor class="h1" name="right_elbow" joint="right_elbow" ctrlrange="-50 50" />
  244 |   </actuator>
  245 | 
  246 |   <equality>
  247 |     <weld name="ball_weld" site1="pitcher_hand_site" site2="ball_site" />
  248 |   </equality>
  249 | </mujoco>
````
