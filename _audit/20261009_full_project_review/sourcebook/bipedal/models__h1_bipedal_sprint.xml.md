# bipedal/models/h1_bipedal_sprint.xml

원본: [models/h1_bipedal_sprint.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/models/h1_bipedal_sprint.xml)

SHA256: `a405cc5e4ec6de41faf9cba69f29514fe966f970b1a06ff9bc13e82d1e1156bc`

전체 290행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <mujoco model="h1_hit_and_run">
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
   16 |           <geom type="capsule" size=".014" friction="1.2 0.01 0.001" />
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
   37 |     <material name="base_pad_mat" rgba="0.98 0.98 0.90 1" reflectance="0.3" />
   38 |     <material name="ball_mat" rgba="0.98 0.98 0.95 1" reflectance="0.4" />
   39 |     <material name="bat_mat" rgba="0.82 0.55 0.28 1" reflectance="0.3" />
   40 |     <material name="strike_zone_mat" rgba="0.2 0.8 0.3 0.25" />
   41 |     <material name="sweet_spot_mat" rgba="0.9 0.1 0.1 0.7" />
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
   70 |     <light directional="true" diffuse="0.85 0.85 0.85" specular="0.25 0.25 0.25" pos="0 5 12" dir="0 0 -1" />
   71 |     <light directional="true" diffuse="0.4 0.4 0.4" pos="-5 -5 10" dir="1 1 -1" />
   72 | 
   73 |     <geom name="ground" type="plane" size="40 40 0.1" material="matplane" />
   74 |     <geom name="home_plate" type="box" size="0.216 0.216 0.005" pos="0 0 0.005" material="home_plate_mat" contype="0" conaffinity="0" />
   75 |     <geom name="pitcher_mound" type="cylinder" size="1.2 0.01" pos="0 10.0 0.005" material="home_plate_mat" contype="0" conaffinity="0" />
   76 | 
   77 |     <!-- 1st Base and Baseline -->
   78 |     <geom name="first_base" type="box" size="0.22 0.22 0.03" pos="6.5 6.5 0.03" material="base_pad_mat" />
   79 |     <site name="first_base_site" type="sphere" size="0.20" pos="6.5 6.5 0.03" rgba="1 1 0 0.4" />
   80 |     <geom name="baseline_1b" type="box" size="0.05 4.6 0.002" pos="3.25 3.35 0.002" quat="0.92388 0 0 0.38268" rgba="1 1 1 0.6" contype="0" conaffinity="0" />
   81 | 
   82 |     <!-- Visual Markers -->
   83 |     <site name="strike_zone" type="box" size="0.216 0.02 0.25" pos="0 0 0.80" material="strike_zone_mat" />
   84 |     <geom name="left_box" type="box" size="0.45 0.9 0.002" pos="-0.75 0 0.002" rgba="0.8 0.8 0.8 0.3" contype="0" conaffinity="0" />
   85 | 
   86 |     <!-- Cameras -->
   87 |     <camera name="broadcast_cam" pos="-2.8 -2.0 1.8" xyaxes="0.75 -0.66 0 0.25 0.28 0.93" fovy="48" />
   88 |     <camera name="run_tracking_cam" mode="targetbody" target="pelvis" pos="-3.0 -2.6 2.2" fovy="52" />
   89 |     <camera name="stadium_wide" pos="-5.5 3.0 4.5" xyaxes="0.75 -0.66 0 0.35 0.40 0.85" fovy="58" />
   90 |     <camera name="first_base_cam" pos="8.2 8.2 1.4" xyaxes="-0.7071 0.7071 0 -0.2 -0.2 0.96" fovy="50" />
   91 | 
   92 |     <!-- Baseball with 6-DoF Freejoint -->
   93 |     <body name="baseball" pos="0 10.0 1.2">
   94 |       <freejoint name="ball_joint" />
   95 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat"
   96 |             solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" />
   97 |       <site name="ball_center" pos="0 0 0" size="0.005" />
   98 |     </body>
   99 | 
  100 |     <!-- Dropped Bat with Freejoint (Spawned/dropped onto turf at release) -->
  101 |     <body name="dropped_bat" pos="0 0 50">
  102 |       <freejoint name="dropped_bat_joint" />
  103 |       <geom name="dropped_bat_barrel" type="cylinder" size="0.032 0.45" pos="0 0 0.45" material="bat_mat" mass="0.90"
  104 |             solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.8 0.01 0.001" />
  105 |     </body>
  106 | 
  107 |     <!-- Full Floating-Base H1 Humanoid (19-DoF) -->
  108 |     <body name="pelvis" pos="-0.75 0 0.98" childclass="h1">
  109 |       <freejoint name="pelvis_joint" />
  110 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
  111 |       <geom class="visual" mesh="pelvis" />
  112 |       
  113 |       <!-- Left Leg -->
  114 |       <body name="left_hip_yaw_link" pos="0 0.0875 -0.1742">
  115 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  116 |         <joint name="left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  117 |         <geom class="visual" mesh="left_hip_yaw_link" />
  118 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  119 |         <body name="left_hip_roll_link" pos="0.039468 0 0">
  120 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  121 |           <joint name="left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  122 |           <geom class="visual" mesh="left_hip_roll_link" />
  123 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  124 |           <body name="left_hip_pitch_link" pos="0 0.11536 0">
  125 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  126 |             <joint name="left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  127 |             <geom class="visual" mesh="left_hip_pitch_link" />
  128 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  129 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  130 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  131 |             <body name="left_knee_link" pos="0 0 -0.4">
  132 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  133 |               <joint name="left_knee" axis="0 1 0" range="-0.26 2.05" />
  134 |               <geom class="visual" mesh="left_knee_link" />
  135 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  136 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  137 |               <body name="left_ankle_link" pos="0 0 -0.4">
  138 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  139 |                 <joint name="left_ankle" axis="0 1 0" range="-0.87 0.52" />
  140 |                 <geom class="visual" mesh="left_ankle_link" />
  141 |                 <geom class="foot1" />
  142 |                 <geom class="foot2" />
  143 |                 <geom class="foot3" />
  144 |               </body>
  145 |             </body>
  146 |           </body>
  147 |         </body>
  148 |       </body>
  149 | 
  150 |       <!-- Right Leg -->
  151 |       <body name="right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  152 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  153 |         <joint name="right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  154 |         <geom class="visual" mesh="right_hip_yaw_link" />
  155 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  156 |         <body name="right_hip_roll_link" pos="0.039468 0 0">
  157 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0438242 0.70721 0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  158 |           <joint name="right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  159 |           <geom class="visual" mesh="right_hip_roll_link" />
  160 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  161 |           <body name="right_hip_pitch_link" pos="0 -0.11536 0">
  162 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  163 |             <joint name="right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  164 |             <geom class="visual" mesh="right_hip_pitch_link" />
  165 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  166 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  167 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  168 |             <body name="right_knee_link" pos="0 0 -0.4">
  169 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  170 |               <joint name="right_knee" axis="0 1 0" range="-0.26 2.05" />
  171 |               <geom class="visual" mesh="right_knee_link" />
  172 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  173 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  174 |               <body name="right_ankle_link" pos="0 0 -0.4">
  175 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  176 |                 <joint name="right_ankle" axis="0 1 0" range="-0.87 0.52" />
  177 |                 <geom class="visual" mesh="right_ankle_link" />
  178 |                 <geom class="foot1" />
  179 |                 <geom class="foot2" />
  180 |                 <geom class="foot3" />
  181 |               </body>
  182 |             </body>
  183 |           </body>
  184 |         </body>
  185 |       </body>
  186 | 
  187 |       <!-- Torso -->
  188 |       <body name="torso_link" pos="0 0 0">
  189 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00127082 -0.00434747 0.00162814" mass="17.789" diaginertia="0.487405 0.409312 0.127837" />
  190 |         <joint name="torso" axis="0 0 1" range="-2.35 2.35" />
  191 |         <geom class="visual" mesh="torso_link" />
  192 |         <geom class="visual" mesh="logo_link" />
  193 |         <geom class="collision" type="capsule" size="0.08" fromto="-0.03 0 0.05 -0.03 0 0.45" />
  194 | 
  195 |         <!-- Left Arm -->
  196 |         <body name="left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  197 |           <inertial pos="-0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  198 |           <joint name="left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  199 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  200 |           <body name="left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  201 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  202 |             <joint name="left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  203 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  204 |             <geom name="left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  205 |             <body name="left_shoulder_yaw_link" pos="0 0 -0.1343">
  206 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  207 |               <joint name="left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  208 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  209 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  210 |               <body name="left_elbow_link" pos="0.0185 0 -0.198">
  211 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  212 |                 <joint name="left_elbow" axis="0 1 0" range="-1.25 2.61" />
  213 |                 <geom class="visual" mesh="left_elbow_link" />
  214 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  215 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  216 |                 <site name="l_hand_grip" pos="0.30 0 0" size="0.01" />
  217 |               </body>
  218 |             </body>
  219 |           </body>
  220 |         </body>
  221 | 
  222 |         <!-- Right Arm + Held Bat -->
  223 |         <body name="right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  224 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  225 |           <joint name="right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  226 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  227 |           <body name="right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  228 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  229 |             <joint name="right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  230 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  231 |             <geom name="right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  232 |             <body name="right_shoulder_yaw_link" pos="0 0 -0.1343">
  233 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  234 |               <joint name="right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  235 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  236 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  237 |               <body name="right_elbow_link" pos="0.0185 0 -0.198">
  238 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  239 |                 <joint name="right_elbow" axis="0 1 0" range="-1.25 2.61" />
  240 |                 <geom class="visual" mesh="right_elbow_link" />
  241 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  242 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  243 | 
  244 |                 <!-- Held Bat attached rigidly during batting -->
  245 |                 <body name="held_bat" pos="0.30 0 0" quat="0.7071068 0 0.7071068 0">
  246 |                   <geom name="held_bat_barrel" type="cylinder" size="0.032 0.45" pos="0 0 0.45" material="bat_mat" mass="0.90"
  247 |                         solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" />
  248 |                   <site name="bat_knob" pos="0 0 0.02" size="0.01" />
  249 |                   <site name="bat_sweet_spot" pos="0 0 0.73" size="0.015" material="sweet_spot_mat" />
  250 |                   <site name="bat_tip" pos="0 0 0.90" size="0.01" />
  251 |                 </body>
  252 |               </body>
  253 |             </body>
  254 |           </body>
  255 |         </body>
  256 |       </body>
  257 |     </body>
  258 |   </worldbody>
  259 | 
  260 |   <contact>
  261 |     <exclude body1="torso_link" body2="left_shoulder_roll_link" />
  262 |     <exclude body1="torso_link" body2="right_shoulder_roll_link" />
  263 |     <pair geom1="held_bat_barrel" geom2="ball_geom" solref="0.0015 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.4 0.01 0.001" />
  264 |   </contact>
  265 | 
  266 |   <actuator>
  267 |     <motor class="h1" name="left_hip_yaw" joint="left_hip_yaw" ctrlrange="-200 200" />
  268 |     <motor class="h1" name="left_hip_roll" joint="left_hip_roll" ctrlrange="-200 200" />
  269 |     <motor class="h1" name="left_hip_pitch" joint="left_hip_pitch" ctrlrange="-200 200" />
  270 |     <motor class="h1" name="left_knee" joint="left_knee" ctrlrange="-300 300" />
  271 |     <motor class="h1" name="left_ankle" joint="left_ankle" ctrlrange="-40 40" />
  272 |     <motor class="h1" name="right_hip_yaw" joint="right_hip_yaw" ctrlrange="-200 200" />
  273 |     <motor class="h1" name="right_hip_roll" joint="right_hip_roll" ctrlrange="-200 200" />
  274 |     <motor class="h1" name="right_hip_pitch" joint="right_hip_pitch" ctrlrange="-200 200" />
  275 |     <motor class="h1" name="right_knee" joint="right_knee" ctrlrange="-300 300" />
  276 |     <motor class="h1" name="right_ankle" joint="right_ankle" ctrlrange="-40 40" />
  277 | 
  278 |     <motor class="h1" name="torso" joint="torso" ctrlrange="-200 200" />
  279 | 
  280 |     <motor class="h1" name="left_shoulder_pitch" joint="left_shoulder_pitch" ctrlrange="-40 40" />
  281 |     <motor class="h1" name="left_shoulder_roll" joint="left_shoulder_roll" ctrlrange="-40 40" />
  282 |     <motor class="h1" name="left_shoulder_yaw" joint="left_shoulder_yaw" ctrlrange="-18 18" />
  283 |     <motor class="h1" name="left_elbow" joint="left_elbow" ctrlrange="-18 18" />
  284 | 
  285 |     <motor class="h1" name="right_shoulder_pitch" joint="right_shoulder_pitch" ctrlrange="-40 40" />
  286 |     <motor class="h1" name="right_shoulder_roll" joint="right_shoulder_roll" ctrlrange="-40 40" />
  287 |     <motor class="h1" name="right_shoulder_yaw" joint="right_shoulder_yaw" ctrlrange="-18 18" />
  288 |     <motor class="h1" name="right_elbow" joint="right_elbow" ctrlrange="-18 18" />
  289 |   </actuator>
  290 | </mujoco>
````
