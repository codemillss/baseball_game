# bipedal/models/h1_battery_pitch_catch.xml

원본: [models/h1_battery_pitch_catch.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/models/h1_battery_pitch_catch.xml)

SHA256: `a59f7243b01adf63e262b7d79c96eaf01235e8d101fc8e9939bc440bcb313e4e`

전체 412행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <?xml version='1.0' encoding='utf-8'?>
    2 | <mujoco model="h1_infield_defense">
    3 |   <compiler angle="radian" meshdir="unitree_h1_assets" autolimits="true" />
    4 |   <option timestep="0.002" gravity="0 0 -9.81" />
    5 |   <default>
    6 |     <default class="h1">
    7 |       <joint damping="1.5" armature="0.1" />
    8 |       <default class="visual">
    9 |         <geom type="mesh" contype="0" conaffinity="0" group="2" material="black" />
   10 |       </default>
   11 |       <default class="collision">
   12 |         <geom group="3" mass="0" density="0" />
   13 |         <default class="foot">
   14 |           <geom type="capsule" size=".014" friction="1.2 0.01 0.001" />
   15 |           <default class="foot1">
   16 |             <geom fromto="-.035 0 -0.056 .02 0 -0.045" />
   17 |           </default>
   18 |           <default class="foot2">
   19 |             <geom fromto=".02 0 -0.045 .115 0 -0.056" />
   20 |           </default>
   21 |           <default class="foot3">
   22 |             <geom fromto=".14 -.03 -0.056 .14 .03 -0.056" />
   23 |           </default>
   24 |         </default>
   25 |       </default>
   26 |       <site size="0.001" rgba="0.5 0.5 0.5 0.3" group="4" />
   27 |     </default>
   28 |   </default>
   29 |   <asset>
   30 |     <material name="black" rgba="0.1 0.1 0.1 1" />
   31 |     <material name="white" rgba="1 1 1 1" />
   32 |     <material name="matplane" reflectance="0.2" texture="texplane" texrepeat="1 1" texuniform="true" />
   33 |     <material name="home_plate_mat" rgba="0.95 0.95 0.95 1" reflectance="0.2" />
   34 |     <material name="base_pad_mat" rgba="0.98 0.98 0.90 1" reflectance="0.3" />
   35 |     <material name="ball_mat" rgba="0.98 0.98 0.95 1" reflectance="0.4" />
   36 |     <material name="bat_mat" rgba="0.82 0.55 0.28 1" reflectance="0.3" />
   37 |     <material name="strike_zone_mat" rgba="0.2 0.8 0.3 0.25" />
   38 |     <material name="sweet_spot_mat" rgba="0.9 0.1 0.1 0.7" />
   39 |     <mesh file="pelvis.stl" />
   40 |     <mesh file="left_hip_yaw_link.stl" />
   41 |     <mesh file="left_hip_roll_link.stl" />
   42 |     <mesh file="left_hip_pitch_link.stl" />
   43 |     <mesh file="left_knee_link.stl" />
   44 |     <mesh file="left_ankle_link.stl" />
   45 |     <mesh file="right_hip_yaw_link.stl" />
   46 |     <mesh file="right_hip_roll_link.stl" />
   47 |     <mesh file="right_hip_pitch_link.stl" />
   48 |     <mesh file="right_knee_link.stl" />
   49 |     <mesh file="right_ankle_link.stl" />
   50 |     <mesh file="torso_link.stl" />
   51 |     <mesh file="left_shoulder_pitch_link.stl" />
   52 |     <mesh file="left_shoulder_roll_link.stl" />
   53 |     <mesh file="left_shoulder_yaw_link.stl" />
   54 |     <mesh file="left_elbow_link.stl" />
   55 |     <mesh file="right_shoulder_pitch_link.stl" />
   56 |     <mesh file="right_shoulder_roll_link.stl" />
   57 |     <mesh file="right_shoulder_yaw_link.stl" />
   58 |     <mesh file="right_elbow_link.stl" />
   59 |     <mesh file="logo_link.stl" />
   60 |     <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="512" />
   61 |     <texture name="texplane" type="2d" builtin="checker" rgb1="0.15 0.45 0.15" rgb2="0.12 0.38 0.12" width="512" height="512" />
   62 |     <material name="glove_mat" rgba="0.55 0.32 0.16 1.0" reflectance="0.2" />
   63 |   </asset>
   64 |   
   65 |   <worldbody>
   66 |     <light directional="true" diffuse="0.85 0.85 0.85" specular="0.25 0.25 0.25" pos="2 5 14" dir="0 0 -1" />
   67 |     <light directional="true" diffuse="0.45 0.45 0.45" pos="-5 -5 10" dir="1 1 -1" />
   68 |     <geom name="ground" type="plane" size="50 50 0.1" material="matplane" />
   69 |     <geom name="home_plate" type="box" size="0.216 0.216 0.005" pos="0 0 0.005" material="home_plate_mat" contype="0" conaffinity="0" />
   70 |     <geom name="pitcher_mound" type="cylinder" size="1.2 0.01" pos="0 10.0 0.005" material="home_plate_mat" contype="0" conaffinity="0" />
   71 |     <geom name="pitcher_rubber" type="box" size="0.30 0.07 0.008" pos="0 10.0 0.015" material="home_plate_mat" contype="0" conaffinity="0" />
   72 |     <geom name="catcher_box" type="box" size="0.50 0.60 0.002" pos="0 -0.95 0.002" rgba="0.8 0.8 0.8 0.25" contype="0" conaffinity="0" />
   73 |     <site name="strike_zone" type="box" size="0.216 0.02 0.20" pos="0 0 0.85" material="strike_zone_mat" />
   74 |     <site name="pitch_target_point" type="sphere" size="0.04" pos="0 0.0 0.85" rgba="0.9 0.2 0.2 0.4" />
   75 | 
   76 |     <camera name="battery_broadcast_cam" pos="-6.5 4.5 3.2" xyaxes="0.0000 -1.0000 0.0000 0.3464 0.0000 0.9381" fovy="64" />
   77 |     <camera name="umpire_cam" pos="0.0 -2.4 1.4" xyaxes="1 0 0 0 0.35 0.94" fovy="48" />
   78 |     <camera name="pitcher_cam" pos="0.0 11.5 1.8" xyaxes="-1 0 0 0 -0.22 0.97" fovy="50" />
   79 |     <camera name="catcher_closeup" pos="-1.5 -0.5 1.2" xyaxes="0.7071 -0.7071 0 0.35 0.35 0.87" fovy="45" />
   80 | 
   81 |     <body name="baseball" pos="0 10.0 1.48">
   82 |       <freejoint name="ball_joint" />
   83 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.4 0.02 0.001" />
   84 |       <site name="ball_site" pos="0 0 0" size="0.01" />
   85 |     </body>
   86 | 
   87 | <body name="p_pelvis" pos="0 10.0 0.82" quat="0.7071068 0 0 -0.7071068" childclass="h1">
   88 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
   89 |       <geom class="visual" mesh="pelvis" />
   90 |       <body name="p_left_hip_yaw_link" pos="0 0.0875 -0.1742">
   91 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
   92 |         <joint name="p_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
   93 |         <geom class="visual" mesh="left_hip_yaw_link" />
   94 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
   95 |         <body name="p_left_hip_roll_link" pos="0.039468 0 0">
   96 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
   97 |           <joint name="p_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
   98 |           <geom class="visual" mesh="left_hip_roll_link" />
   99 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  100 |           <body name="p_left_hip_pitch_link" pos="0 0.11536 0">
  101 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  102 |             <joint name="p_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  103 |             <geom class="visual" mesh="left_hip_pitch_link" />
  104 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  105 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  106 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  107 |             <body name="p_left_knee_link" pos="0 0 -0.4">
  108 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  109 |               <joint name="p_left_knee" axis="0 1 0" range="-0.26 2.05" />
  110 |               <geom class="visual" mesh="left_knee_link" />
  111 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  112 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  113 |               <body name="p_left_ankle_link" pos="0 0 -0.4">
  114 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  115 |                 <joint name="p_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  116 |                 <geom class="visual" mesh="left_ankle_link" />
  117 |                 <geom class="foot1" />
  118 |                 <geom class="foot2" />
  119 |                 <geom class="foot3" />
  120 |               </body>
  121 |             </body>
  122 |           </body>
  123 |         </body>
  124 |       </body>
  125 |       <body name="p_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  126 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  127 |         <joint name="p_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  128 |         <geom class="visual" mesh="right_hip_yaw_link" />
  129 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  130 |         <body name="p_right_hip_roll_link" pos="0.039468 0 0">
  131 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0729075 0.701867 0.0438242 0.70721" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  132 |           <joint name="p_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  133 |           <geom class="visual" mesh="right_hip_roll_link" />
  134 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  135 |           <body name="p_right_hip_pitch_link" pos="0 -0.11536 0">
  136 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  137 |             <joint name="p_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  138 |             <geom class="visual" mesh="right_hip_pitch_link" />
  139 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  140 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  141 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  142 |             <body name="p_right_knee_link" pos="0 0 -0.4">
  143 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  144 |               <joint name="p_right_knee" axis="0 1 0" range="-0.26 2.05" />
  145 |               <geom class="visual" mesh="right_knee_link" />
  146 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  147 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  148 |               <body name="p_right_ankle_link" pos="0 0 -0.4">
  149 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  150 |                 <joint name="p_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  151 |                 <geom class="visual" mesh="right_ankle_link" />
  152 |                 <geom class="foot1" />
  153 |                 <geom class="foot2" />
  154 |                 <geom class="foot3" />
  155 |               </body>
  156 |             </body>
  157 |           </body>
  158 |         </body>
  159 |       </body>
  160 |       <body name="p_torso_link" pos="0 0 0">
  161 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00127082 -0.0043492 0.00149972" mass="17.789" diaginertia="0.487014 0.409608 0.127815" />
  162 |         <joint name="p_torso" axis="0 0 1" range="-2.35 2.35" />
  163 |         <geom class="visual" mesh="torso_link" />
  164 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.15 0.04 0 0.15" />
  165 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.25 0.04 0 0.25" />
  166 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.35 0.04 0 0.35" />
  167 |         <geom class="visual" mesh="logo_link" />
  168 |         <body name="p_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  169 |           <inertial pos="-0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  170 |           <joint name="p_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  171 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  172 |           <body name="p_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  173 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  174 |             <joint name="p_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  175 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  176 |             <geom name="p_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.07 -0.02 0 0.01 0.008" />
  177 |             <body name="p_left_shoulder_yaw_link" pos="0 0 -0.1343">
  178 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  179 |               <joint name="p_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  180 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  181 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  182 |               <body name="p_left_elbow_link" pos="0.0185 0 -0.198">
  183 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.684102 -0.0853116 -0.0765232 0.720327" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  184 |                 <joint name="p_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  185 |                 <geom class="visual" mesh="left_elbow_link" />
  186 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  187 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  188 |               </body>
  189 |             </body>
  190 |           </body>
  191 |         </body>
  192 |         <body name="p_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  193 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  194 |           <joint name="p_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  195 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  196 |           <body name="p_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  197 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  198 |             <joint name="p_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  199 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  200 |             <geom name="p_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  201 |             <body name="p_right_shoulder_yaw_link" pos="0 0 -0.1343">
  202 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  203 |               <joint name="p_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  204 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  205 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  206 |               <body name="p_right_elbow_link" pos="0.0185 0 -0.198">
  207 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  208 |                 <joint name="p_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  209 |                 <geom class="visual" mesh="right_elbow_link" />
  210 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  211 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  212 |                 <site name="p_pitcher_hand_site" pos="0.30 0 -0.015" size="0.01" />
  213 |               </body>
  214 |             </body>
  215 |           </body>
  216 |         </body>
  217 |       </body>
  218 |     </body>
  219 |     
  220 | <body name="c_pelvis" pos="0.0 -0.95 0.52" quat="0.7071068 0 0 0.7071068" childclass="h1">
  221 |       <freejoint name="c_pelvis_joint" />
  222 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
  223 |       <geom class="visual" mesh="pelvis" />
  224 |       <body name="c_left_hip_yaw_link" pos="0 0.0875 -0.1742">
  225 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  226 |         <joint name="c_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  227 |         <geom class="visual" mesh="left_hip_yaw_link" />
  228 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  229 |         <body name="c_left_hip_roll_link" pos="0.039468 0 0">
  230 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  231 |           <joint name="c_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  232 |           <geom class="visual" mesh="left_hip_roll_link" />
  233 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  234 |           <body name="c_left_hip_pitch_link" pos="0 0.11536 0">
  235 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  236 |             <joint name="c_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  237 |             <geom class="visual" mesh="left_hip_pitch_link" />
  238 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  239 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  240 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  241 |             <body name="c_left_knee_link" pos="0 0 -0.4">
  242 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  243 |               <joint name="c_left_knee" axis="0 1 0" range="-0.26 2.05" />
  244 |               <geom class="visual" mesh="left_knee_link" />
  245 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  246 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  247 |               <body name="c_left_ankle_link" pos="0 0 -0.4">
  248 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  249 |                 <joint name="c_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  250 |                 <geom class="visual" mesh="left_ankle_link" />
  251 |                 <geom class="foot1" />
  252 |                 <geom class="foot2" />
  253 |                 <geom class="foot3" />
  254 |               </body>
  255 |             </body>
  256 |           </body>
  257 |         </body>
  258 |       </body>
  259 |       <body name="c_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  260 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  261 |         <joint name="c_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  262 |         <geom class="visual" mesh="right_hip_yaw_link" />
  263 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  264 |         <body name="c_right_hip_roll_link" pos="0.039468 0 0">
  265 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0438242 0.70721 0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  266 |           <joint name="c_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  267 |           <geom class="visual" mesh="right_hip_roll_link" />
  268 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  269 |           <body name="c_right_hip_pitch_link" pos="0 -0.11536 0">
  270 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  271 |             <joint name="c_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  272 |             <geom class="visual" mesh="right_hip_pitch_link" />
  273 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  274 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  275 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  276 |             <body name="c_right_knee_link" pos="0 0 -0.4">
  277 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  278 |               <joint name="c_right_knee" axis="0 1 0" range="-0.26 2.05" />
  279 |               <geom class="visual" mesh="right_knee_link" />
  280 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  281 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  282 |               <body name="c_right_ankle_link" pos="0 0 -0.4">
  283 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  284 |                 <joint name="c_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  285 |                 <geom class="visual" mesh="right_ankle_link" />
  286 |                 <geom class="foot1" />
  287 |                 <geom class="foot2" />
  288 |                 <geom class="foot3" />
  289 |               </body>
  290 |             </body>
  291 |           </body>
  292 |         </body>
  293 |       </body>
  294 |       <body name="c_torso_link" pos="0 0 0">
  295 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00127082 -0.00434747 0.00162814" mass="17.789" diaginertia="0.487405 0.409312 0.127837" />
  296 |         <joint name="c_torso" axis="0 0 1" range="-2.35 2.35" />
  297 |         <geom class="visual" mesh="torso_link" />
  298 |         <geom class="visual" mesh="logo_link" />
  299 |         <geom class="collision" type="capsule" size="0.08" fromto="-0.03 0 0.05 -0.03 0 0.45" />
  300 |         <body name="c_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  301 |           <inertial pos="-0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  302 |           <joint name="c_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  303 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  304 |           <body name="c_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  305 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  306 |             <joint name="c_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  307 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  308 |             <geom name="c_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  309 |             <body name="c_left_shoulder_yaw_link" pos="0 0 -0.1343">
  310 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  311 |               <joint name="c_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  312 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  313 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  314 |               <body name="c_left_elbow_link" pos="0.0185 0 -0.198">
  315 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  316 |                 <joint name="c_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  317 |                 <geom class="visual" mesh="left_elbow_link" />
  318 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  319 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  320 |                 <site name="c_l_hand_grip" pos="0.30 0 0" size="0.01" />
  321 |               
  322 |         <body name="c_mitt" pos="0.22 0 0" quat="0.7071068 0 0.7071068 0">
  323 |           <geom name="c_mitt_geom" type="cylinder" size="0.14 0.04" pos="0 0 0" material="glove_mat" mass="0.45" contype="0" conaffinity="0" />
  324 |           <site name="c_mitt_site" type="sphere" size="0.05" pos="0 0 0" rgba="0.9 0.4 0.1 0.6" />
  325 |         </body>
  326 | </body>
  327 |             </body>
  328 |           </body>
  329 |         </body>
  330 |         <body name="c_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  331 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  332 |           <joint name="c_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  333 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  334 |           <body name="c_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  335 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  336 |             <joint name="c_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  337 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  338 |             <geom name="c_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  339 |             <body name="c_right_shoulder_yaw_link" pos="0 0 -0.1343">
  340 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  341 |               <joint name="c_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  342 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  343 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  344 |               <body name="c_right_elbow_link" pos="0.0185 0 -0.198">
  345 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  346 |                 <joint name="c_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  347 |                 <geom class="visual" mesh="right_elbow_link" />
  348 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  349 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  350 |                 
  351 |               </body>
  352 |             </body>
  353 |           </body>
  354 |         </body>
  355 |       </body>
  356 |     </body>
  357 |     
  358 |   </worldbody>
  359 |   <contact>
  360 |         <exclude body1="p_torso_link" body2="p_right_shoulder_roll_link" />
  361 |         <exclude body1="p_torso_link" body2="p_left_shoulder_roll_link" />
  362 |         <exclude body1="c_torso_link" body2="c_right_shoulder_roll_link" />
  363 |         <exclude body1="c_torso_link" body2="c_left_shoulder_roll_link" />
  364 |         <exclude body1="baseball" body2="p_right_elbow_link" />
  365 |         <exclude body1="baseball" body2="c_right_elbow_link" />
  366 |         <exclude body1="baseball" body2="c_left_elbow_link" />
  367 |     <pair geom1="c_mitt_geom" geom2="ball_geom" solref="0.005 1" solimp="0.80 0.90 0.001 0.5 2" friction="0.8 0.02 0.001" />
  368 |   </contact>
  369 |   <equality>
  370 |     <weld name="pitch_weld" body1="baseball" body2="p_right_elbow_link" relpose="0.25 0 0 1 0 0 0" active="false" />
  371 |   </equality>
  372 | <actuator>
  373 |     <motor class="h1" name="p_left_hip_yaw" joint="p_left_hip_yaw" ctrlrange="-200 200" />
  374 |     <motor class="h1" name="p_left_hip_roll" joint="p_left_hip_roll" ctrlrange="-200 200" />
  375 |     <motor class="h1" name="p_left_hip_pitch" joint="p_left_hip_pitch" ctrlrange="-200 200" />
  376 |     <motor class="h1" name="p_left_knee" joint="p_left_knee" ctrlrange="-300 300" />
  377 |     <motor class="h1" name="p_left_ankle" joint="p_left_ankle" ctrlrange="-40 40" />
  378 |     <motor class="h1" name="p_right_hip_yaw" joint="p_right_hip_yaw" ctrlrange="-200 200" />
  379 |     <motor class="h1" name="p_right_hip_roll" joint="p_right_hip_roll" ctrlrange="-200 200" />
  380 |     <motor class="h1" name="p_right_hip_pitch" joint="p_right_hip_pitch" ctrlrange="-200 200" />
  381 |     <motor class="h1" name="p_right_knee" joint="p_right_knee" ctrlrange="-300 300" />
  382 |     <motor class="h1" name="p_right_ankle" joint="p_right_ankle" ctrlrange="-40 40" />
  383 |     <motor class="h1" name="p_torso" joint="p_torso" ctrlrange="-200 200" />
  384 |     <motor class="h1" name="p_left_shoulder_pitch" joint="p_left_shoulder_pitch" ctrlrange="-40 40" />
  385 |     <motor class="h1" name="p_left_shoulder_roll" joint="p_left_shoulder_roll" ctrlrange="-40 40" />
  386 |     <motor class="h1" name="p_left_shoulder_yaw" joint="p_left_shoulder_yaw" ctrlrange="-18 18" />
  387 |     <motor class="h1" name="p_left_elbow" joint="p_left_elbow" ctrlrange="-18 18" />
  388 |     <motor class="h1" name="p_right_shoulder_pitch" joint="p_right_shoulder_pitch" ctrlrange="-40 40" />
  389 |     <motor class="h1" name="p_right_shoulder_roll" joint="p_right_shoulder_roll" ctrlrange="-40 40" />
  390 |     <motor class="h1" name="p_right_shoulder_yaw" joint="p_right_shoulder_yaw" ctrlrange="-18 18" />
  391 |     <motor class="h1" name="p_right_elbow" joint="p_right_elbow" ctrlrange="-18 18" />
  392 |     <motor class="h1" name="c_left_hip_yaw" joint="c_left_hip_yaw" ctrlrange="-200 200" />
  393 |     <motor class="h1" name="c_left_hip_roll" joint="c_left_hip_roll" ctrlrange="-200 200" />
  394 |     <motor class="h1" name="c_left_hip_pitch" joint="c_left_hip_pitch" ctrlrange="-200 200" />
  395 |     <motor class="h1" name="c_left_knee" joint="c_left_knee" ctrlrange="-300 300" />
  396 |     <motor class="h1" name="c_left_ankle" joint="c_left_ankle" ctrlrange="-40 40" />
  397 |     <motor class="h1" name="c_right_hip_yaw" joint="c_right_hip_yaw" ctrlrange="-200 200" />
  398 |     <motor class="h1" name="c_right_hip_roll" joint="c_right_hip_roll" ctrlrange="-200 200" />
  399 |     <motor class="h1" name="c_right_hip_pitch" joint="c_right_hip_pitch" ctrlrange="-200 200" />
  400 |     <motor class="h1" name="c_right_knee" joint="c_right_knee" ctrlrange="-300 300" />
  401 |     <motor class="h1" name="c_right_ankle" joint="c_right_ankle" ctrlrange="-40 40" />
  402 |     <motor class="h1" name="c_torso" joint="c_torso" ctrlrange="-200 200" />
  403 |     <motor class="h1" name="c_left_shoulder_pitch" joint="c_left_shoulder_pitch" ctrlrange="-40 40" />
  404 |     <motor class="h1" name="c_left_shoulder_roll" joint="c_left_shoulder_roll" ctrlrange="-40 40" />
  405 |     <motor class="h1" name="c_left_shoulder_yaw" joint="c_left_shoulder_yaw" ctrlrange="-18 18" />
  406 |     <motor class="h1" name="c_left_elbow" joint="c_left_elbow" ctrlrange="-18 18" />
  407 |     <motor class="h1" name="c_right_shoulder_pitch" joint="c_right_shoulder_pitch" ctrlrange="-40 40" />
  408 |     <motor class="h1" name="c_right_shoulder_roll" joint="c_right_shoulder_roll" ctrlrange="-40 40" />
  409 |     <motor class="h1" name="c_right_shoulder_yaw" joint="c_right_shoulder_yaw" ctrlrange="-18 18" />
  410 |     <motor class="h1" name="c_right_elbow" joint="c_right_elbow" ctrlrange="-18 18" />
  411 |   </actuator>
  412 | </mujoco>
````
