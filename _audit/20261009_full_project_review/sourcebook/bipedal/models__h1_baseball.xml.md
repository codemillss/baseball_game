# bipedal/models/h1_baseball.xml

원본: [models/h1_baseball.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/models/h1_baseball.xml)

SHA256: `25af198c993e26db456317bca1b6c25d6ac2d7dbbaa556849dc614baaa3dd116`

전체 303행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <mujoco model="h1_baseball">
    2 |   <compiler angle="radian" meshdir="unitree_h1_assets" autolimits="true" />
    3 |   <option timestep="0.002" gravity="0 0 -9.81" />
    4 | 
    5 |   <statistic meansize="0.05" />
    6 | 
    7 |   <default>
    8 |     <default class="h1">
    9 |       <joint damping="1.5" armature="0.1" />
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
   35 |     <material name="matplane" reflectance="0.2" texture="texplane" texrepeat="1 1" texuniform="true" />
   36 |     <material name="home_plate_mat" rgba="0.95 0.95 0.95 1" reflectance="0.2" />
   37 |     <material name="ball_mat" rgba="0.98 0.98 0.95 1" reflectance="0.4" />
   38 |     <material name="bat_mat" rgba="0.82 0.55 0.28 1" reflectance="0.3" />
   39 |     <material name="strike_zone_mat" rgba="0.2 0.8 0.3 0.25" />
   40 |     <material name="sweet_spot_mat" rgba="0.9 0.1 0.1 0.7" />
   41 |     <material name="foul_line_mat" rgba="0.9 0.9 0.9 0.8" />
   42 | 
   43 |     <mesh file="pelvis.stl" />
   44 |     <mesh file="left_hip_yaw_link.stl" />
   45 |     <mesh file="left_hip_roll_link.stl" />
   46 |     <mesh file="left_hip_pitch_link.stl" />
   47 |     <mesh file="left_knee_link.stl" />
   48 |     <mesh file="left_ankle_link.stl" />
   49 |     <mesh file="right_hip_yaw_link.stl" />
   50 |     <mesh file="right_hip_roll_link.stl" />
   51 |     <mesh file="right_hip_pitch_link.stl" />
   52 |     <mesh file="right_knee_link.stl" />
   53 |     <mesh file="right_ankle_link.stl" />
   54 |     <mesh file="torso_link.stl" />
   55 |     <mesh file="left_shoulder_pitch_link.stl" />
   56 |     <mesh file="left_shoulder_roll_link.stl" />
   57 |     <mesh file="left_shoulder_yaw_link.stl" />
   58 |     <mesh file="left_elbow_link.stl" />
   59 |     <mesh file="right_shoulder_pitch_link.stl" />
   60 |     <mesh file="right_shoulder_roll_link.stl" />
   61 |     <mesh file="right_shoulder_yaw_link.stl" />
   62 |     <mesh file="right_elbow_link.stl" />
   63 |     <mesh file="logo_link.stl" />
   64 | 
   65 |     <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="512" />
   66 |     <texture name="texplane" type="2d" builtin="checker" rgb1="0.15 0.45 0.15" rgb2="0.12 0.38 0.12" width="512" height="512" />
   67 |   </asset>
   68 | 
   69 |   <worldbody>
   70 |     <!-- Lighting -->
   71 |     <light directional="true" diffuse="0.85 0.85 0.85" specular="0.25 0.25 0.25" pos="0 5 12" dir="0 0 -1" />
   72 |     <light directional="true" diffuse="0.4 0.4 0.4" pos="-5 -5 10" dir="1 1 -1" />
   73 | 
   74 |     <!-- Ground & Field Markers -->
   75 |     <geom name="ground" type="plane" size="40 40 0.1" material="matplane" />
   76 |     <geom name="home_plate" type="box" size="0.216 0.216 0.005" pos="0 0 0.005" material="home_plate_mat" />
   77 |     <geom name="pitcher_mound" type="cylinder" size="1.2 0.01" pos="0 10.0 0.005" material="home_plate_mat" />
   78 |     <geom name="pitcher_rubber" type="box" size="0.30 0.07 0.006" pos="0 10.0 0.015" material="home_plate_mat" />
   79 | 
   80 |     <!-- Strike Zone Visualizer at Home Plate -->
   81 |     <site name="strike_zone" type="box" size="0.216 0.02 0.25" pos="0 0 0.80" material="strike_zone_mat" />
   82 | 
   83 |     <!-- Left & Right Batter Box visual markers -->
   84 |     <geom name="left_box" type="box" size="0.45 0.9 0.002" pos="-0.75 0 0.002" rgba="0.8 0.8 0.8 0.3" />
   85 |     <geom name="right_box" type="box" size="0.45 0.9 0.002" pos="0.75 0 0.002" rgba="0.8 0.8 0.8 0.3" />
   86 | 
   87 |     <!-- Target Field Visual Markers (Left / Center / Right Field) -->
   88 |     <site name="target_left_field" type="cylinder" size="1.5 0.01" pos="-8.0 16.0 0.02" rgba="1.0 0.3 0.3 0.4" />
   89 |     <site name="target_center_field" type="cylinder" size="1.5 0.01" pos="0.0 20.0 0.02" rgba="0.3 1.0 0.3 0.4" />
   90 |     <site name="target_right_field" type="cylinder" size="1.5 0.01" pos="8.0 16.0 0.02" rgba="0.3 0.3 1.0 0.4" />
   91 | 
   92 |     <!-- Cameras -->
   93 |     <camera name="broadcast_cam" pos="-2.8 -2.0 1.8" xyaxes="0.75 -0.66 0 0.25 0.28 0.93" fovy="48" />
   94 |     <camera name="side_cam" pos="-3.0 0.2 1.3" xyaxes="0 -1 0 0.2 0 0.98" fovy="50" />
   95 |     <camera name="pitcher_cam" pos="0 10.5 1.5" xyaxes="-1 0 0 0 -0.15 0.99" fovy="55" />
   96 |     <camera name="catcher_cam" pos="0 -2.5 1.2" xyaxes="1 0 0 0 0.2 0.98" fovy="55" />
   97 |     <camera name="overhead_cam" pos="0 6.0 14.0" xyaxes="1 0 0 0 1 0" fovy="60" />
   98 | 
   99 |     <!-- Baseball with 6-DoF Freejoint -->
  100 |     <body name="baseball" pos="0 10.0 1.2">
  101 |       <freejoint name="ball_joint" />
  102 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat"
  103 |             solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" />
  104 |       <site name="ball_center" pos="0 0 0" size="0.005" />
  105 |     </body>
  106 | 
  107 |     <!-- H1 Humanoid Batter (Positioned in Right-Handed Batter Box, x=-0.75m) -->
  108 |     <body name="pelvis" pos="-0.75 0 0.82" childclass="h1">
  109 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
  110 |       <geom class="visual" mesh="pelvis" />
  111 |       
  112 |       <!-- Left Leg (1: Hip Yaw, 2: Hip Roll, 3: Hip Pitch, 4: Knee, 5: Ankle) -->
  113 |       <body name="left_hip_yaw_link" pos="0 0.0875 -0.1742">
  114 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  115 |         <joint name="left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  116 |         <geom class="visual" mesh="left_hip_yaw_link" />
  117 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  118 |         <body name="left_hip_roll_link" pos="0.039468 0 0">
  119 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  120 |           <joint name="left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  121 |           <geom class="visual" mesh="left_hip_roll_link" />
  122 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  123 |           <body name="left_hip_pitch_link" pos="0 0.11536 0">
  124 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  125 |             <joint name="left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  126 |             <geom class="visual" mesh="left_hip_pitch_link" />
  127 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  128 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  129 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  130 |             <body name="left_knee_link" pos="0 0 -0.4">
  131 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  132 |               <joint name="left_knee" axis="0 1 0" range="-0.26 2.05" />
  133 |               <geom class="visual" mesh="left_knee_link" />
  134 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  135 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  136 |               <body name="left_ankle_link" pos="0 0 -0.4">
  137 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  138 |                 <joint name="left_ankle" axis="0 1 0" range="-0.87 0.52" />
  139 |                 <geom class="visual" mesh="left_ankle_link" />
  140 |                 <geom class="foot1" />
  141 |                 <geom class="foot2" />
  142 |                 <geom class="foot3" />
  143 |               </body>
  144 |             </body>
  145 |           </body>
  146 |         </body>
  147 |       </body>
  148 | 
  149 |       <!-- Right Leg (6: Hip Yaw, 7: Hip Roll, 8: Hip Pitch, 9: Knee, 10: Ankle) -->
  150 |       <body name="right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  151 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  152 |         <joint name="right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  153 |         <geom class="visual" mesh="right_hip_yaw_link" />
  154 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  155 |         <body name="right_hip_roll_link" pos="0.039468 0 0">
  156 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0438242 0.70721 0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  157 |           <joint name="right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  158 |           <geom class="visual" mesh="right_hip_roll_link" />
  159 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  160 |           <body name="right_hip_pitch_link" pos="0 -0.11536 0">
  161 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  162 |             <joint name="right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  163 |             <geom class="visual" mesh="right_hip_pitch_link" />
  164 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  165 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  166 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  167 |             <body name="right_knee_link" pos="0 0 -0.4">
  168 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  169 |               <joint name="right_knee" axis="0 1 0" range="-0.26 2.05" />
  170 |               <geom class="visual" mesh="right_knee_link" />
  171 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  172 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  173 |               <body name="right_ankle_link" pos="0 0 -0.4">
  174 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  175 |                 <joint name="right_ankle" axis="0 1 0" range="-0.87 0.52" />
  176 |                 <geom class="visual" mesh="right_ankle_link" />
  177 |                 <geom class="foot1" />
  178 |                 <geom class="foot2" />
  179 |                 <geom class="foot3" />
  180 |               </body>
  181 |             </body>
  182 |           </body>
  183 |         </body>
  184 |       </body>
  185 | 
  186 |       <!-- Torso (11: Torso Yaw) -->
  187 |       <body name="torso_link">
  188 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00130808 -0.00282289 -0.00349105" mass="17.789" diaginertia="0.487315 0.409628 0.127837" />
  189 |         <joint name="torso" axis="0 0 1" range="-2.35 2.35" />
  190 |         <geom class="visual" mesh="torso_link" />
  191 |         <geom class="visual" material="white" mesh="logo_link" />
  192 |         <geom name="head" class="collision" type="capsule" size="0.06" fromto="0.05 0 0.68 0.05 0 0.6" />
  193 |         <geom name="helmet" class="collision" type="sphere" size="0.073" pos="0.045 0 0.68" />
  194 |         <geom name="torso" class="collision" type="box" size="0.07 0.1 0.22" pos="0 0 0.25" />
  195 |         <geom name="hip" class="collision" type="capsule" size="0.05" fromto="0 -0.1 -0.05 0 0.1 -0.05" />
  196 |         <site name="imu" pos="-0.04452 -0.01891 0.27756" />
  197 | 
  198 |         <!-- Left Arm (12: Pitch, 13: Roll, 14: Yaw, 15: Elbow) -->
  199 |         <body name="left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  200 |           <inertial pos="0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 -0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  201 |           <joint name="left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  202 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  203 |           <body name="left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  204 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  205 |             <joint name="left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  206 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  207 |             <geom name="left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  208 |             <body name="left_shoulder_yaw_link" pos="0 0 -0.1343">
  209 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  210 |               <joint name="left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  211 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  212 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  213 |               <body name="left_elbow_link" pos="0.0185 0 -0.198">
  214 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  215 |                 <joint name="left_elbow" axis="0 1 0" range="-1.25 2.61" />
  216 |                 <geom class="visual" mesh="left_elbow_link" />
  217 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  218 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  219 |                 <site name="l_hand_grip" pos="0.30 0 0" size="0.01" />
  220 |               </body>
  221 |             </body>
  222 |           </body>
  223 |         </body>
  224 | 
  225 |         <!-- Right Arm (16: Pitch, 17: Roll, 18: Yaw, 19: Elbow) + Bat -->
  226 |         <body name="right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  227 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  228 |           <joint name="right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  229 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  230 |           <body name="right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  231 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  232 |             <joint name="right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  233 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  234 |             <geom name="right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  235 |             <body name="right_shoulder_yaw_link" pos="0 0 -0.1343">
  236 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  237 |               <joint name="right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  238 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  239 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  240 |               <body name="right_elbow_link" pos="0.0185 0 -0.198">
  241 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  242 |                 <joint name="right_elbow" axis="0 1 0" range="-1.25 2.61" />
  243 |                 <geom class="visual" mesh="right_elbow_link" />
  244 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  245 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  246 | 
  247 |                 <!-- Bat attached to Right Forearm / Hand -->
  248 |                 <body name="bat" pos="0.30 0 0" quat="0.7071068 0 0.7071068 0">
  249 |                   <geom name="bat_barrel" type="cylinder" size="0.032 0.45" pos="0 0 0.45" material="bat_mat" mass="0.90"
  250 |                         solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" />
  251 |                   <!-- Bat Key Sites -->
  252 |                   <site name="bat_knob" pos="0 0 0.02" size="0.01" />
  253 |                   <site name="bat_grip_left" pos="0 0 0.08" size="0.01" />
  254 |                   <site name="bat_sweet_spot" pos="0 0 0.73" size="0.015" material="sweet_spot_mat" />
  255 |                   <site name="bat_tip" pos="0 0 0.90" size="0.01" />
  256 |                 </body>
  257 |               </body>
  258 |             </body>
  259 |           </body>
  260 |         </body>
  261 |       </body>
  262 |     </body>
  263 |   </worldbody>
  264 | 
  265 |   <contact>
  266 |     <exclude body1="torso_link" body2="left_shoulder_roll_link" />
  267 |     <exclude body1="torso_link" body2="right_shoulder_roll_link" />
  268 |     <pair geom1="bat_barrel" geom2="ball_geom" solref="0.0015 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.4 0.01 0.001" />
  269 |   </contact>
  270 | 
  271 |   <actuator>
  272 |     <!-- 10 Leg Motors (ctrlrange = H1 rated peak torque in N*m) -->
  273 |     <motor class="h1" name="left_hip_yaw" joint="left_hip_yaw" ctrlrange="-200 200" />
  274 |     <motor class="h1" name="left_hip_roll" joint="left_hip_roll" ctrlrange="-200 200" />
  275 |     <motor class="h1" name="left_hip_pitch" joint="left_hip_pitch" ctrlrange="-200 200" />
  276 |     <motor class="h1" name="left_knee" joint="left_knee" ctrlrange="-300 300" />
  277 |     <motor class="h1" name="left_ankle" joint="left_ankle" ctrlrange="-40 40" />
  278 |     <motor class="h1" name="right_hip_yaw" joint="right_hip_yaw" ctrlrange="-200 200" />
  279 |     <motor class="h1" name="right_hip_roll" joint="right_hip_roll" ctrlrange="-200 200" />
  280 |     <motor class="h1" name="right_hip_pitch" joint="right_hip_pitch" ctrlrange="-200 200" />
  281 |     <motor class="h1" name="right_knee" joint="right_knee" ctrlrange="-300 300" />
  282 |     <motor class="h1" name="right_ankle" joint="right_ankle" ctrlrange="-40 40" />
  283 | 
  284 |     <!-- 1 Torso Motor -->
  285 |     <motor class="h1" name="torso" joint="torso" ctrlrange="-200 200" />
  286 | 
  287 |     <!-- 4 Left Arm Motors -->
  288 |     <motor class="h1" name="left_shoulder_pitch" joint="left_shoulder_pitch" ctrlrange="-40 40" />
  289 |     <motor class="h1" name="left_shoulder_roll" joint="left_shoulder_roll" ctrlrange="-40 40" />
  290 |     <motor class="h1" name="left_shoulder_yaw" joint="left_shoulder_yaw" ctrlrange="-18 18" />
  291 |     <motor class="h1" name="left_elbow" joint="left_elbow" ctrlrange="-18 18" />
  292 | 
  293 |     <!-- 4 Right Arm Motors -->
  294 |     <motor class="h1" name="right_shoulder_pitch" joint="right_shoulder_pitch" ctrlrange="-40 40" />
  295 |     <motor class="h1" name="right_shoulder_roll" joint="right_shoulder_roll" ctrlrange="-40 40" />
  296 |     <motor class="h1" name="right_shoulder_yaw" joint="right_shoulder_yaw" ctrlrange="-18 18" />
  297 |     <motor class="h1" name="right_elbow" joint="right_elbow" ctrlrange="-18 18" />
  298 |   </actuator>
  299 | 
  300 |   <equality>
  301 |     <connect name="left_hand_to_bat" site1="l_hand_grip" site2="bat_grip_left" />
  302 |   </equality>
  303 | </mujoco>
````
