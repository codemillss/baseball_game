# bipedal/models/h1_pitcher.xml

원본: [models/h1_pitcher.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/models/h1_pitcher.xml)

SHA256: `44c93a2d7713ed04c1fd0a1e7b254849ca29bbf39bbc4f5444e99e1f64c6c046`

전체 280행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <mujoco model="h1_pitcher">
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
   38 |     <material name="target_zone_mat" rgba="0.2 0.8 0.3 0.35" />
   39 |     <material name="strike_zone_target_mat" rgba="0.9 0.2 0.2 0.4" />
   40 | 
   41 |     <mesh file="pelvis.stl" />
   42 |     <mesh file="left_hip_yaw_link.stl" />
   43 |     <mesh file="left_hip_roll_link.stl" />
   44 |     <mesh file="left_hip_pitch_link.stl" />
   45 |     <mesh file="left_knee_link.stl" />
   46 |     <mesh file="left_ankle_link.stl" />
   47 |     <mesh file="right_hip_yaw_link.stl" />
   48 |     <mesh file="right_hip_roll_link.stl" />
   49 |     <mesh file="right_hip_pitch_link.stl" />
   50 |     <mesh file="right_knee_link.stl" />
   51 |     <mesh file="right_ankle_link.stl" />
   52 |     <mesh file="torso_link.stl" />
   53 |     <mesh file="left_shoulder_pitch_link.stl" />
   54 |     <mesh file="left_shoulder_roll_link.stl" />
   55 |     <mesh file="left_shoulder_yaw_link.stl" />
   56 |     <mesh file="left_elbow_link.stl" />
   57 |     <mesh file="right_shoulder_pitch_link.stl" />
   58 |     <mesh file="right_shoulder_roll_link.stl" />
   59 |     <mesh file="right_shoulder_yaw_link.stl" />
   60 |     <mesh file="right_elbow_link.stl" />
   61 |     <mesh file="logo_link.stl" />
   62 | 
   63 |     <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="512" />
   64 |     <texture name="texplane" type="2d" builtin="checker" rgb1="0.15 0.45 0.15" rgb2="0.12 0.38 0.12" width="512" height="512" />
   65 |   </asset>
   66 | 
   67 |   <worldbody>
   68 |     <!-- Lighting -->
   69 |     <light directional="true" diffuse="0.85 0.85 0.85" specular="0.25 0.25 0.25" pos="0 5 12" dir="0 0 -1" />
   70 |     <light directional="true" diffuse="0.4 0.4 0.4" pos="-5 -5 10" dir="1 1 -1" />
   71 | 
   72 |     <!-- Ground & Field Markers -->
   73 |     <geom name="ground" type="plane" size="40 40 0.1" material="matplane" />
   74 |     <geom name="home_plate" type="box" size="0.216 0.216 0.005" pos="0 0 0.005" material="home_plate_mat" />
   75 |     <geom name="pitcher_mound" type="cylinder" size="1.2 0.02" pos="0 10.0 0.01" material="home_plate_mat" />
   76 |     <geom name="pitcher_rubber" type="box" size="0.30 0.07 0.008" pos="0 10.0 0.025" material="home_plate_mat" />
   77 | 
   78 |     <!-- Target Strike Zone visualizer at Home Plate (y = 0.0m) -->
   79 |     <site name="strike_zone_target" type="box" size="0.216 0.02 0.22" pos="0 0.0 0.80" material="target_zone_mat" />
   80 |     <site name="pitch_target_point" type="sphere" size="0.04" pos="0 0.0 0.80" material="strike_zone_target_mat" />
   81 | 
   82 |     <!-- Cameras -->
   83 |     <camera name="broadcast_cam" pos="-4.0 5.0 2.2" xyaxes="0.9 -0.4 0 0.15 0.35 0.92" fovy="48" />
   84 |     <camera name="behind_pitcher_cam" pos="0 12.5 1.8" xyaxes="1 0 0 0 -0.3 0.95" fovy="50" />
   85 |     <camera name="pitcher_side_cam" pos="-3.5 10.0 1.5" xyaxes="0 1 0 0.1 0 0.99" fovy="48" />
   86 |     <camera name="catcher_cam" mode="targetbody" target="pelvis" pos="0 -1.0 1.0" fovy="45" />
   87 | 
   88 |     <!-- Pitcher robot standing on mound (y = 10.0m facing towards home plate at y = 0) -->
   89 |     <body name="pelvis" pos="0 10.0 0.82" quat="0.7071068 0 0 -0.7071068" childclass="h1">
   90 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
   91 |       <geom class="visual" mesh="pelvis" />
   92 |       
   93 |       <!-- Left Leg (Pitcher stride / pivot leg) -->
   94 |       <body name="left_hip_yaw_link" pos="0 0.0875 -0.1742">
   95 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
   96 |         <joint name="left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
   97 |         <geom class="visual" mesh="left_hip_yaw_link" />
   98 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
   99 |         <body name="left_hip_roll_link" pos="0.039468 0 0">
  100 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  101 |           <joint name="left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  102 |           <geom class="visual" mesh="left_hip_roll_link" />
  103 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  104 |           <body name="left_hip_pitch_link" pos="0 0.11536 0">
  105 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  106 |             <joint name="left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  107 |             <geom class="visual" mesh="left_hip_pitch_link" />
  108 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  109 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  110 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  111 |             <body name="left_knee_link" pos="0 0 -0.4">
  112 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  113 |               <joint name="left_knee" axis="0 1 0" range="-0.26 2.05" />
  114 |               <geom class="visual" mesh="left_knee_link" />
  115 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  116 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  117 |               <body name="left_ankle_link" pos="0 0 -0.4">
  118 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  119 |                 <joint name="left_ankle" axis="0 1 0" range="-0.87 0.52" />
  120 |                 <geom class="visual" mesh="left_ankle_link" />
  121 |                 <geom class="foot1" />
  122 |                 <geom class="foot2" />
  123 |                 <geom class="foot3" />
  124 |               </body>
  125 |             </body>
  126 |           </body>
  127 |         </body>
  128 |       </body>
  129 | 
  130 |       <!-- Right Leg -->
  131 |       <body name="right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  132 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  133 |         <joint name="right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  134 |         <geom class="visual" mesh="right_hip_yaw_link" />
  135 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  136 |         <body name="right_hip_roll_link" pos="0.039468 0 0">
  137 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0729075 0.701867 0.0438242 0.70721" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  138 |           <joint name="right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  139 |           <geom class="visual" mesh="right_hip_roll_link" />
  140 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  141 |           <body name="right_hip_pitch_link" pos="0 -0.11536 0">
  142 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  143 |             <joint name="right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  144 |             <geom class="visual" mesh="right_hip_pitch_link" />
  145 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  146 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  147 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  148 |             <body name="right_knee_link" pos="0 0 -0.4">
  149 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  150 |               <joint name="right_knee" axis="0 1 0" range="-0.26 2.05" />
  151 |               <geom class="visual" mesh="right_knee_link" />
  152 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  153 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  154 |               <body name="right_ankle_link" pos="0 0 -0.4">
  155 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  156 |                 <joint name="right_ankle" axis="0 1 0" range="-0.87 0.52" />
  157 |                 <geom class="visual" mesh="right_ankle_link" />
  158 |                 <geom class="foot1" />
  159 |                 <geom class="foot2" />
  160 |                 <geom class="foot3" />
  161 |               </body>
  162 |             </body>
  163 |           </body>
  164 |         </body>
  165 |       </body>
  166 | 
  167 |       <!-- Torso -->
  168 |       <body name="torso_link" pos="0 0 0">
  169 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00127082 -0.0043492 0.00149972" mass="17.789" diaginertia="0.487014 0.409608 0.127815" />
  170 |         <joint name="torso" axis="0 0 1" range="-2.35 2.35" />
  171 |         <geom class="visual" mesh="torso_link" />
  172 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.15 0.04 0 0.15" />
  173 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.25 0.04 0 0.25" />
  174 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.35 0.04 0 0.35" />
  175 |         <geom class="visual" mesh="logo_link" />
  176 | 
  177 |         <!-- Left Arm (Glove / Balance arm) -->
  178 |         <body name="left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  179 |           <inertial pos="-0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  180 |           <joint name="left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  181 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  182 |           <body name="left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  183 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  184 |             <joint name="left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  185 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  186 |             <geom name="left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.07 -0.02 0 0.01 0.008" />
  187 |             <body name="left_shoulder_yaw_link" pos="0 0 -0.1343">
  188 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  189 |               <joint name="left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  190 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  191 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  192 |               <body name="left_elbow_link" pos="0.0185 0 -0.198">
  193 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.684102 -0.0853116 -0.0765232 0.720327" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  194 |                 <joint name="left_elbow" axis="0 1 0" range="-1.25 2.61" />
  195 |                 <geom class="visual" mesh="left_elbow_link" />
  196 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  197 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  198 |               </body>
  199 |             </body>
  200 |           </body>
  201 |         </body>
  202 | 
  203 |         <!-- Right Arm: Dynamic Pitching Arm -->
  204 |         <body name="right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  205 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  206 |           <joint name="right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  207 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  208 |           <body name="right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  209 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  210 |             <joint name="right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  211 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  212 |             <geom name="right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  213 |             <body name="right_shoulder_yaw_link" pos="0 0 -0.1343">
  214 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  215 |               <joint name="right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  216 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  217 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  218 |               <body name="right_elbow_link" pos="0.0185 0 -0.198">
  219 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  220 |                 <joint name="right_elbow" axis="0 1 0" range="-1.25 2.61" />
  221 |                 <geom class="visual" mesh="right_elbow_link" />
  222 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  223 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  224 |                 <!-- Pitcher Hand Site: Ball grip and release point -->
  225 |                 <site name="pitcher_hand_site" pos="0.30 0 -0.015" size="0.01" />
  226 |               </body>
  227 |             </body>
  228 |           </body>
  229 |         </body>
  230 |       </body>
  231 |     </body>
  232 | 
  233 |     <!-- Baseball with Freejoint and Site for Weld -->
  234 |     <body name="baseball" pos="0 10.0 1.2">
  235 |       <freejoint name="ball_joint" />
  236 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat"
  237 |             solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" />
  238 |       <site name="ball_site" pos="0 0 0" size="0.01" />
  239 |     </body>
  240 |   </worldbody>
  241 | 
  242 |   <contact>
  243 |     <exclude body1="torso_link" body2="left_shoulder_roll_link" />
  244 |     <exclude body1="torso_link" body2="right_shoulder_roll_link" />
  245 |     <exclude body1="baseball" body2="right_elbow_link" />
  246 |   </contact>
  247 | 
  248 |   <actuator>
  249 |     <!-- 10 Leg Motors (Stance stability) -->
  250 |     <motor class="h1" name="left_hip_yaw" joint="left_hip_yaw" ctrlrange="-200 200" />
  251 |     <motor class="h1" name="left_hip_roll" joint="left_hip_roll" ctrlrange="-200 200" />
  252 |     <motor class="h1" name="left_hip_pitch" joint="left_hip_pitch" ctrlrange="-200 200" />
  253 |     <motor class="h1" name="left_knee" joint="left_knee" ctrlrange="-300 300" />
  254 |     <motor class="h1" name="left_ankle" joint="left_ankle" ctrlrange="-40 40" />
  255 |     <motor class="h1" name="right_hip_yaw" joint="right_hip_yaw" ctrlrange="-200 200" />
  256 |     <motor class="h1" name="right_hip_roll" joint="right_hip_roll" ctrlrange="-200 200" />
  257 |     <motor class="h1" name="right_hip_pitch" joint="right_hip_pitch" ctrlrange="-200 200" />
  258 |     <motor class="h1" name="right_knee" joint="right_knee" ctrlrange="-300 300" />
  259 |     <motor class="h1" name="right_ankle" joint="right_ankle" ctrlrange="-40 40" />
  260 | 
  261 |     <!-- 1 Torso Motor -->
  262 |     <motor class="h1" name="torso" joint="torso" ctrlrange="-200 200" />
  263 | 
  264 |     <!-- 4 Left Arm Motors -->
  265 |     <motor class="h1" name="left_shoulder_pitch" joint="left_shoulder_pitch" ctrlrange="-40 40" />
  266 |     <motor class="h1" name="left_shoulder_roll" joint="left_shoulder_roll" ctrlrange="-40 40" />
  267 |     <motor class="h1" name="left_shoulder_yaw" joint="left_shoulder_yaw" ctrlrange="-18 18" />
  268 |     <motor class="h1" name="left_elbow" joint="left_elbow" ctrlrange="-18 18" />
  269 | 
  270 |     <!-- 4 Right Arm Pitching Motors -->
  271 |     <motor class="h1" name="right_shoulder_pitch" joint="right_shoulder_pitch" ctrlrange="-40 40" />
  272 |     <motor class="h1" name="right_shoulder_roll" joint="right_shoulder_roll" ctrlrange="-40 40" />
  273 |     <motor class="h1" name="right_shoulder_yaw" joint="right_shoulder_yaw" ctrlrange="-18 18" />
  274 |     <motor class="h1" name="right_elbow" joint="right_elbow" ctrlrange="-18 18" />
  275 |   </actuator>
  276 | 
  277 |   <equality>
  278 |     <weld name="ball_weld" site1="pitcher_hand_site" site2="ball_site" />
  279 |   </equality>
  280 | </mujoco>
````
