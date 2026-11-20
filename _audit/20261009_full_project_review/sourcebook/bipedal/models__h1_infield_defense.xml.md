# bipedal/models/h1_infield_defense.xml

원본: [models/h1_infield_defense.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/models/h1_infield_defense.xml)

SHA256: `2ddbfda1b081ca706714a6087eed71069bdcafc686afcf1b5a209064c255c76a`

전체 569행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

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
   64 |   <worldbody>
   65 |     <light directional="true" diffuse="0.85 0.85 0.85" specular="0.25 0.25 0.25" pos="2 5 14" dir="0 0 -1" />
   66 |     <light directional="true" diffuse="0.45 0.45 0.45" pos="-5 -5 10" dir="1 1 -1" />
   67 |     <geom name="ground" type="plane" size="50 50 0.1" material="matplane" />
   68 |     <geom name="home_plate" type="box" size="0.216 0.216 0.005" pos="0 0 0.005" material="home_plate_mat" contype="0" conaffinity="0" />
   69 |     <geom name="pitcher_mound" type="cylinder" size="1.2 0.01" pos="0 10.0 0.005" material="home_plate_mat" contype="0" conaffinity="0" />
   70 |     <geom name="pitcher_rubber" type="box" size="0.30 0.07 0.008" pos="0 10.0 0.015" material="home_plate_mat" contype="0" conaffinity="0" />
   71 |     <geom name="first_base" type="box" size="0.22 0.22 0.03" pos="6.5 6.5 0.03" material="base_pad_mat" />
   72 |     <site name="first_base_site" type="sphere" size="0.25" pos="6.5 6.5 0.03" rgba="1 1 0 0.4" />
   73 |     <geom name="baseline_1b" type="box" size="0.05 4.6 0.002" pos="3.25 3.35 0.002" quat="0.92388 0 0 0.38268" rgba="1 1 1 0.6" contype="0" conaffinity="0" />
   74 |     <geom name="baseline_3b" type="box" size="0.05 4.6 0.002" pos="-3.25 3.35 0.002" quat="0.92388 0 0 -0.38268" rgba="1 1 1 0.6" contype="0" conaffinity="0" />
   75 |     <site name="strike_zone" type="box" size="0.216 0.02 0.25" pos="0 0 0.80" material="strike_zone_mat" />
   76 |     <site name="pitch_target_point" type="sphere" size="0.04" pos="0 0.0 0.80" rgba="0.9 0.2 0.2 0.4" />
   77 |     <geom name="left_box" type="box" size="0.45 0.9 0.002" pos="-0.75 0 0.002" rgba="0.8 0.8 0.8 0.3" contype="0" conaffinity="0" />
   78 |     <camera name="infield_broadcast_cam" pos="-4.2 -2.2 4.2" xyaxes="0.78 -0.62 0 0.28 0.35 0.89" fovy="64" />
   79 |     <camera name="first_base_cam" pos="8.5 8.5 1.6" xyaxes="-0.7071 0.7071 0 -0.22 -0.22 0.95" fovy="50" />
   80 |     <camera name="run_tracking_cam" mode="targetbody" target="b_pelvis" pos="-3.0 -2.6 2.2" fovy="52" />
   81 |     <camera name="stadium_wide" pos="-6.5 4.5 5.2" xyaxes="0.75 -0.66 0 0.35 0.40 0.85" fovy="65" />
   82 |     <body name="baseball" pos="0 10.0 1.2">
   83 |       <freejoint name="ball_joint" />
   84 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.4 0.02 0.001" />
   85 |       <site name="ball_site" pos="0 0 0" size="0.01" />
   86 |     </body>
   87 |     <body name="dropped_bat" pos="0 0 50">
   88 |       <freejoint name="dropped_bat_joint" />
   89 |       <geom name="dropped_bat_barrel" type="capsule" size="0.032 0.40" pos="0 0 0.45" material="bat_mat" mass="0.90" solref="0.005 1" solimp="0.90 0.95 0.001 0.5 2" friction="0.8 0.02 0.001" />
   90 |     </body>
   91 |     <body name="p_pelvis" pos="0 10.0 0.82" quat="0.7071068 0 0 -0.7071068" childclass="h1">
   92 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
   93 |       <geom class="visual" mesh="pelvis" />
   94 |       <body name="p_left_hip_yaw_link" pos="0 0.0875 -0.1742">
   95 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
   96 |         <joint name="p_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
   97 |         <geom class="visual" mesh="left_hip_yaw_link" />
   98 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
   99 |         <body name="p_left_hip_roll_link" pos="0.039468 0 0">
  100 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  101 |           <joint name="p_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  102 |           <geom class="visual" mesh="left_hip_roll_link" />
  103 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  104 |           <body name="p_left_hip_pitch_link" pos="0 0.11536 0">
  105 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  106 |             <joint name="p_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  107 |             <geom class="visual" mesh="left_hip_pitch_link" />
  108 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  109 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  110 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  111 |             <body name="p_left_knee_link" pos="0 0 -0.4">
  112 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  113 |               <joint name="p_left_knee" axis="0 1 0" range="-0.26 2.05" />
  114 |               <geom class="visual" mesh="left_knee_link" />
  115 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  116 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  117 |               <body name="p_left_ankle_link" pos="0 0 -0.4">
  118 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  119 |                 <joint name="p_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  120 |                 <geom class="visual" mesh="left_ankle_link" />
  121 |                 <geom class="foot1" />
  122 |                 <geom class="foot2" />
  123 |                 <geom class="foot3" />
  124 |               </body>
  125 |             </body>
  126 |           </body>
  127 |         </body>
  128 |       </body>
  129 |       <body name="p_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  130 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  131 |         <joint name="p_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  132 |         <geom class="visual" mesh="right_hip_yaw_link" />
  133 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  134 |         <body name="p_right_hip_roll_link" pos="0.039468 0 0">
  135 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0729075 0.701867 0.0438242 0.70721" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  136 |           <joint name="p_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  137 |           <geom class="visual" mesh="right_hip_roll_link" />
  138 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  139 |           <body name="p_right_hip_pitch_link" pos="0 -0.11536 0">
  140 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  141 |             <joint name="p_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  142 |             <geom class="visual" mesh="right_hip_pitch_link" />
  143 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  144 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  145 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  146 |             <body name="p_right_knee_link" pos="0 0 -0.4">
  147 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  148 |               <joint name="p_right_knee" axis="0 1 0" range="-0.26 2.05" />
  149 |               <geom class="visual" mesh="right_knee_link" />
  150 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  151 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  152 |               <body name="p_right_ankle_link" pos="0 0 -0.4">
  153 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  154 |                 <joint name="p_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  155 |                 <geom class="visual" mesh="right_ankle_link" />
  156 |                 <geom class="foot1" />
  157 |                 <geom class="foot2" />
  158 |                 <geom class="foot3" />
  159 |               </body>
  160 |             </body>
  161 |           </body>
  162 |         </body>
  163 |       </body>
  164 |       <body name="p_torso_link" pos="0 0 0">
  165 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00127082 -0.0043492 0.00149972" mass="17.789" diaginertia="0.487014 0.409608 0.127815" />
  166 |         <joint name="p_torso" axis="0 0 1" range="-2.35 2.35" />
  167 |         <geom class="visual" mesh="torso_link" />
  168 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.15 0.04 0 0.15" />
  169 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.25 0.04 0 0.25" />
  170 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.35 0.04 0 0.35" />
  171 |         <geom class="visual" mesh="logo_link" />
  172 |         <body name="p_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  173 |           <inertial pos="-0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  174 |           <joint name="p_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  175 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  176 |           <body name="p_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  177 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  178 |             <joint name="p_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  179 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  180 |             <geom name="p_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.07 -0.02 0 0.01 0.008" />
  181 |             <body name="p_left_shoulder_yaw_link" pos="0 0 -0.1343">
  182 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  183 |               <joint name="p_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  184 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  185 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  186 |               <body name="p_left_elbow_link" pos="0.0185 0 -0.198">
  187 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.684102 -0.0853116 -0.0765232 0.720327" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  188 |                 <joint name="p_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  189 |                 <geom class="visual" mesh="left_elbow_link" />
  190 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  191 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  192 |               </body>
  193 |             </body>
  194 |           </body>
  195 |         </body>
  196 |         <body name="p_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  197 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  198 |           <joint name="p_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  199 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  200 |           <body name="p_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  201 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  202 |             <joint name="p_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  203 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  204 |             <geom name="p_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  205 |             <body name="p_right_shoulder_yaw_link" pos="0 0 -0.1343">
  206 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  207 |               <joint name="p_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  208 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  209 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  210 |               <body name="p_right_elbow_link" pos="0.0185 0 -0.198">
  211 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  212 |                 <joint name="p_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  213 |                 <geom class="visual" mesh="right_elbow_link" />
  214 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  215 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  216 |                 <site name="p_pitcher_hand_site" pos="0.30 0 -0.015" size="0.01" />
  217 |               </body>
  218 |             </body>
  219 |           </body>
  220 |         </body>
  221 |       </body>
  222 |     </body>
  223 |     <body name="b_pelvis" pos="-0.75 0.0 0.92" childclass="h1">
  224 |       <freejoint name="b_pelvis_joint" />
  225 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
  226 |       <geom class="visual" mesh="pelvis" />
  227 |       <body name="b_left_hip_yaw_link" pos="0 0.0875 -0.1742">
  228 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  229 |         <joint name="b_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  230 |         <geom class="visual" mesh="left_hip_yaw_link" />
  231 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  232 |         <body name="b_left_hip_roll_link" pos="0.039468 0 0">
  233 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  234 |           <joint name="b_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  235 |           <geom class="visual" mesh="left_hip_roll_link" />
  236 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  237 |           <body name="b_left_hip_pitch_link" pos="0 0.11536 0">
  238 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  239 |             <joint name="b_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  240 |             <geom class="visual" mesh="left_hip_pitch_link" />
  241 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  242 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  243 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  244 |             <body name="b_left_knee_link" pos="0 0 -0.4">
  245 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  246 |               <joint name="b_left_knee" axis="0 1 0" range="-0.26 2.05" />
  247 |               <geom class="visual" mesh="left_knee_link" />
  248 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  249 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  250 |               <body name="b_left_ankle_link" pos="0 0 -0.4">
  251 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  252 |                 <joint name="b_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  253 |                 <geom class="visual" mesh="left_ankle_link" />
  254 |                 <geom class="foot1" />
  255 |                 <geom class="foot2" />
  256 |                 <geom class="foot3" />
  257 |               </body>
  258 |             </body>
  259 |           </body>
  260 |         </body>
  261 |       </body>
  262 |       <body name="b_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  263 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  264 |         <joint name="b_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  265 |         <geom class="visual" mesh="right_hip_yaw_link" />
  266 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  267 |         <body name="b_right_hip_roll_link" pos="0.039468 0 0">
  268 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0438242 0.70721 0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  269 |           <joint name="b_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  270 |           <geom class="visual" mesh="right_hip_roll_link" />
  271 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  272 |           <body name="b_right_hip_pitch_link" pos="0 -0.11536 0">
  273 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  274 |             <joint name="b_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  275 |             <geom class="visual" mesh="right_hip_pitch_link" />
  276 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  277 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  278 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  279 |             <body name="b_right_knee_link" pos="0 0 -0.4">
  280 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  281 |               <joint name="b_right_knee" axis="0 1 0" range="-0.26 2.05" />
  282 |               <geom class="visual" mesh="right_knee_link" />
  283 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  284 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  285 |               <body name="b_right_ankle_link" pos="0 0 -0.4">
  286 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  287 |                 <joint name="b_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  288 |                 <geom class="visual" mesh="right_ankle_link" />
  289 |                 <geom class="foot1" />
  290 |                 <geom class="foot2" />
  291 |                 <geom class="foot3" />
  292 |               </body>
  293 |             </body>
  294 |           </body>
  295 |         </body>
  296 |       </body>
  297 |       <body name="b_torso_link" pos="0 0 0">
  298 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00127082 -0.00434747 0.00162814" mass="17.789" diaginertia="0.487405 0.409312 0.127837" />
  299 |         <joint name="b_torso" axis="0 0 1" range="-2.35 2.35" />
  300 |         <geom class="visual" mesh="torso_link" />
  301 |         <geom class="visual" mesh="logo_link" />
  302 |         <geom class="collision" type="capsule" size="0.08" fromto="-0.03 0 0.05 -0.03 0 0.45" />
  303 |         <body name="b_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  304 |           <inertial pos="-0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  305 |           <joint name="b_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  306 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  307 |           <body name="b_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  308 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  309 |             <joint name="b_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  310 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  311 |             <geom name="b_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  312 |             <body name="b_left_shoulder_yaw_link" pos="0 0 -0.1343">
  313 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  314 |               <joint name="b_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  315 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  316 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  317 |               <body name="b_left_elbow_link" pos="0.0185 0 -0.198">
  318 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  319 |                 <joint name="b_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  320 |                 <geom class="visual" mesh="left_elbow_link" />
  321 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  322 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  323 |                 <site name="b_l_hand_grip" pos="0.30 0 0" size="0.01" />
  324 |               </body>
  325 |             </body>
  326 |           </body>
  327 |         </body>
  328 |         <body name="b_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  329 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  330 |           <joint name="b_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  331 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  332 |           <body name="b_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  333 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  334 |             <joint name="b_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  335 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  336 |             <geom name="b_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  337 |             <body name="b_right_shoulder_yaw_link" pos="0 0 -0.1343">
  338 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  339 |               <joint name="b_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  340 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  341 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  342 |               <body name="b_right_elbow_link" pos="0.0185 0 -0.198">
  343 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  344 |                 <joint name="b_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  345 |                 <geom class="visual" mesh="right_elbow_link" />
  346 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  347 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  348 |                 <body name="b_held_bat" pos="0.30 0 0" quat="0.7071068 0 0.7071068 0">
  349 |                   <geom name="b_held_bat_barrel" type="cylinder" size="0.032 0.45" pos="0 0 0.45" material="bat_mat" mass="0.90" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" />
  350 |                   <site name="b_bat_knob" pos="0 0 0.02" size="0.01" />
  351 |                   <site name="b_bat_sweet_spot" pos="0 0 0.73" size="0.015" material="sweet_spot_mat" />
  352 |                   <site name="b_bat_tip" pos="0 0 0.90" size="0.01" />
  353 |                 </body>
  354 |               </body>
  355 |             </body>
  356 |           </body>
  357 |         </body>
  358 |       </body>
  359 |     </body>
  360 |     <body name="f_pelvis" pos="5.0 5.0 0.92" childclass="h1" quat="0.3826834 0 0 -0.9238795">
  361 |       <freejoint name="f_pelvis_joint" />
  362 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
  363 |       <geom class="visual" mesh="pelvis" />
  364 |       <body name="f_left_hip_yaw_link" pos="0 0.0875 -0.1742">
  365 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  366 |         <joint name="f_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  367 |         <geom class="visual" mesh="left_hip_yaw_link" />
  368 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  369 |         <body name="f_left_hip_roll_link" pos="0.039468 0 0">
  370 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  371 |           <joint name="f_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  372 |           <geom class="visual" mesh="left_hip_roll_link" />
  373 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  374 |           <body name="f_left_hip_pitch_link" pos="0 0.11536 0">
  375 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  376 |             <joint name="f_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  377 |             <geom class="visual" mesh="left_hip_pitch_link" />
  378 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  379 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  380 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  381 |             <body name="f_left_knee_link" pos="0 0 -0.4">
  382 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  383 |               <joint name="f_left_knee" axis="0 1 0" range="-0.26 2.05" />
  384 |               <geom class="visual" mesh="left_knee_link" />
  385 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  386 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  387 |               <body name="f_left_ankle_link" pos="0 0 -0.4">
  388 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  389 |                 <joint name="f_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  390 |                 <geom class="visual" mesh="left_ankle_link" />
  391 |                 <geom class="foot1" />
  392 |                 <geom class="foot2" />
  393 |                 <geom class="foot3" />
  394 |               </body>
  395 |             </body>
  396 |           </body>
  397 |         </body>
  398 |       </body>
  399 |       <body name="f_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  400 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  401 |         <joint name="f_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  402 |         <geom class="visual" mesh="right_hip_yaw_link" />
  403 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  404 |         <body name="f_right_hip_roll_link" pos="0.039468 0 0">
  405 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0438242 0.70721 0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  406 |           <joint name="f_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  407 |           <geom class="visual" mesh="right_hip_roll_link" />
  408 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  409 |           <body name="f_right_hip_pitch_link" pos="0 -0.11536 0">
  410 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  411 |             <joint name="f_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  412 |             <geom class="visual" mesh="right_hip_pitch_link" />
  413 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  414 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  415 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  416 |             <body name="f_right_knee_link" pos="0 0 -0.4">
  417 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  418 |               <joint name="f_right_knee" axis="0 1 0" range="-0.26 2.05" />
  419 |               <geom class="visual" mesh="right_knee_link" />
  420 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  421 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  422 |               <body name="f_right_ankle_link" pos="0 0 -0.4">
  423 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  424 |                 <joint name="f_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  425 |                 <geom class="visual" mesh="right_ankle_link" />
  426 |                 <geom class="foot1" />
  427 |                 <geom class="foot2" />
  428 |                 <geom class="foot3" />
  429 |               </body>
  430 |             </body>
  431 |           </body>
  432 |         </body>
  433 |       </body>
  434 |       <body name="f_torso_link" pos="0 0 0">
  435 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00127082 -0.00434747 0.00162814" mass="17.789" diaginertia="0.487405 0.409312 0.127837" />
  436 |         <joint name="f_torso" axis="0 0 1" range="-2.35 2.35" />
  437 |         <geom class="visual" mesh="torso_link" />
  438 |         <geom class="visual" mesh="logo_link" />
  439 |         <geom class="collision" type="capsule" size="0.08" fromto="-0.03 0 0.05 -0.03 0 0.45" />
  440 |         <body name="f_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  441 |           <inertial pos="-0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  442 |           <joint name="f_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  443 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  444 |           <body name="f_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  445 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  446 |             <joint name="f_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  447 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  448 |             <geom name="f_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  449 |             <body name="f_left_shoulder_yaw_link" pos="0 0 -0.1343">
  450 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  451 |               <joint name="f_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  452 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  453 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  454 |               <body name="f_left_elbow_link" pos="0.0185 0 -0.198">
  455 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  456 |                 <joint name="f_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  457 |                 <geom class="visual" mesh="left_elbow_link" />
  458 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  459 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  460 |                 <site name="f_l_hand_grip" pos="0.30 0 0" size="0.01" />
  461 |                 <geom name="f_glove" type="sphere" size="0.12" pos="0.30 0 0" material="glove_mat" contype="0" conaffinity="0" />
  462 |                 <site name="f_glove_site" type="sphere" size="0.12" pos="0.30 0 0" rgba="0.7 0.35 0.15 0.6" />
  463 |               </body>
  464 |             </body>
  465 |           </body>
  466 |         </body>
  467 |         <body name="f_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  468 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  469 |           <joint name="f_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  470 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  471 |           <body name="f_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  472 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  473 |             <joint name="f_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  474 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  475 |             <geom name="f_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  476 |             <body name="f_right_shoulder_yaw_link" pos="0 0 -0.1343">
  477 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  478 |               <joint name="f_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  479 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  480 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  481 |               <body name="f_right_elbow_link" pos="0.0185 0 -0.198">
  482 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  483 |                 <joint name="f_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  484 |                 <geom class="visual" mesh="right_elbow_link" />
  485 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  486 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  487 |               </body>
  488 |             </body>
  489 |           </body>
  490 |         </body>
  491 |       </body>
  492 |     </body>
  493 |   </worldbody>
  494 |   <contact>
  495 |     <exclude body1="p_torso_link" body2="p_right_shoulder_roll_link" />
  496 |     <exclude body1="p_torso_link" body2="p_left_shoulder_roll_link" />
  497 |     <exclude body1="b_torso_link" body2="b_right_shoulder_roll_link" />
  498 |     <exclude body1="b_torso_link" body2="b_left_shoulder_roll_link" />
  499 |     <exclude body1="f_torso_link" body2="f_right_shoulder_roll_link" />
  500 |     <exclude body1="f_torso_link" body2="f_left_shoulder_roll_link" />
  501 |     <exclude body1="baseball" body2="p_right_elbow_link" />
  502 |     <exclude body1="baseball" body2="b_right_elbow_link" />
  503 |     <exclude body1="baseball" body2="b_left_elbow_link" />
  504 |     <pair geom1="b_held_bat_barrel" geom2="ball_geom" solref="0.0015 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.4 0.01 0.001" />
  505 |     <pair geom1="ground" geom2="ball_geom" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.4 0.02 0.001" />
  506 |   </contact>
  507 |   <actuator>
  508 |     <motor class="h1" name="p_left_hip_yaw" joint="p_left_hip_yaw" ctrlrange="-200 200" />
  509 |     <motor class="h1" name="p_left_hip_roll" joint="p_left_hip_roll" ctrlrange="-200 200" />
  510 |     <motor class="h1" name="p_left_hip_pitch" joint="p_left_hip_pitch" ctrlrange="-200 200" />
  511 |     <motor class="h1" name="p_left_knee" joint="p_left_knee" ctrlrange="-300 300" />
  512 |     <motor class="h1" name="p_left_ankle" joint="p_left_ankle" ctrlrange="-40 40" />
  513 |     <motor class="h1" name="p_right_hip_yaw" joint="p_right_hip_yaw" ctrlrange="-200 200" />
  514 |     <motor class="h1" name="p_right_hip_roll" joint="p_right_hip_roll" ctrlrange="-200 200" />
  515 |     <motor class="h1" name="p_right_hip_pitch" joint="p_right_hip_pitch" ctrlrange="-200 200" />
  516 |     <motor class="h1" name="p_right_knee" joint="p_right_knee" ctrlrange="-300 300" />
  517 |     <motor class="h1" name="p_right_ankle" joint="p_right_ankle" ctrlrange="-40 40" />
  518 |     <motor class="h1" name="p_torso" joint="p_torso" ctrlrange="-200 200" />
  519 |     <motor class="h1" name="p_left_shoulder_pitch" joint="p_left_shoulder_pitch" ctrlrange="-40 40" />
  520 |     <motor class="h1" name="p_left_shoulder_roll" joint="p_left_shoulder_roll" ctrlrange="-40 40" />
  521 |     <motor class="h1" name="p_left_shoulder_yaw" joint="p_left_shoulder_yaw" ctrlrange="-18 18" />
  522 |     <motor class="h1" name="p_left_elbow" joint="p_left_elbow" ctrlrange="-18 18" />
  523 |     <motor class="h1" name="p_right_shoulder_pitch" joint="p_right_shoulder_pitch" ctrlrange="-40 40" />
  524 |     <motor class="h1" name="p_right_shoulder_roll" joint="p_right_shoulder_roll" ctrlrange="-40 40" />
  525 |     <motor class="h1" name="p_right_shoulder_yaw" joint="p_right_shoulder_yaw" ctrlrange="-18 18" />
  526 |     <motor class="h1" name="p_right_elbow" joint="p_right_elbow" ctrlrange="-18 18" />
  527 |     <motor class="h1" name="b_left_hip_yaw" joint="b_left_hip_yaw" ctrlrange="-200 200" />
  528 |     <motor class="h1" name="b_left_hip_roll" joint="b_left_hip_roll" ctrlrange="-200 200" />
  529 |     <motor class="h1" name="b_left_hip_pitch" joint="b_left_hip_pitch" ctrlrange="-200 200" />
  530 |     <motor class="h1" name="b_left_knee" joint="b_left_knee" ctrlrange="-300 300" />
  531 |     <motor class="h1" name="b_left_ankle" joint="b_left_ankle" ctrlrange="-40 40" />
  532 |     <motor class="h1" name="b_right_hip_yaw" joint="b_right_hip_yaw" ctrlrange="-200 200" />
  533 |     <motor class="h1" name="b_right_hip_roll" joint="b_right_hip_roll" ctrlrange="-200 200" />
  534 |     <motor class="h1" name="b_right_hip_pitch" joint="b_right_hip_pitch" ctrlrange="-200 200" />
  535 |     <motor class="h1" name="b_right_knee" joint="b_right_knee" ctrlrange="-300 300" />
  536 |     <motor class="h1" name="b_right_ankle" joint="b_right_ankle" ctrlrange="-40 40" />
  537 |     <motor class="h1" name="b_torso" joint="b_torso" ctrlrange="-200 200" />
  538 |     <motor class="h1" name="b_left_shoulder_pitch" joint="b_left_shoulder_pitch" ctrlrange="-40 40" />
  539 |     <motor class="h1" name="b_left_shoulder_roll" joint="b_left_shoulder_roll" ctrlrange="-40 40" />
  540 |     <motor class="h1" name="b_left_shoulder_yaw" joint="b_left_shoulder_yaw" ctrlrange="-18 18" />
  541 |     <motor class="h1" name="b_left_elbow" joint="b_left_elbow" ctrlrange="-18 18" />
  542 |     <motor class="h1" name="b_right_shoulder_pitch" joint="b_right_shoulder_pitch" ctrlrange="-40 40" />
  543 |     <motor class="h1" name="b_right_shoulder_roll" joint="b_right_shoulder_roll" ctrlrange="-40 40" />
  544 |     <motor class="h1" name="b_right_shoulder_yaw" joint="b_right_shoulder_yaw" ctrlrange="-18 18" />
  545 |     <motor class="h1" name="b_right_elbow" joint="b_right_elbow" ctrlrange="-18 18" />
  546 |     <motor class="h1" name="f_left_hip_yaw" joint="f_left_hip_yaw" ctrlrange="-200 200" />
  547 |     <motor class="h1" name="f_left_hip_roll" joint="f_left_hip_roll" ctrlrange="-200 200" />
  548 |     <motor class="h1" name="f_left_hip_pitch" joint="f_left_hip_pitch" ctrlrange="-200 200" />
  549 |     <motor class="h1" name="f_left_knee" joint="f_left_knee" ctrlrange="-300 300" />
  550 |     <motor class="h1" name="f_left_ankle" joint="f_left_ankle" ctrlrange="-40 40" />
  551 |     <motor class="h1" name="f_right_hip_yaw" joint="f_right_hip_yaw" ctrlrange="-200 200" />
  552 |     <motor class="h1" name="f_right_hip_roll" joint="f_right_hip_roll" ctrlrange="-200 200" />
  553 |     <motor class="h1" name="f_right_hip_pitch" joint="f_right_hip_pitch" ctrlrange="-200 200" />
  554 |     <motor class="h1" name="f_right_knee" joint="f_right_knee" ctrlrange="-300 300" />
  555 |     <motor class="h1" name="f_right_ankle" joint="f_right_ankle" ctrlrange="-40 40" />
  556 |     <motor class="h1" name="f_torso" joint="f_torso" ctrlrange="-200 200" />
  557 |     <motor class="h1" name="f_left_shoulder_pitch" joint="f_left_shoulder_pitch" ctrlrange="-40 40" />
  558 |     <motor class="h1" name="f_left_shoulder_roll" joint="f_left_shoulder_roll" ctrlrange="-40 40" />
  559 |     <motor class="h1" name="f_left_shoulder_yaw" joint="f_left_shoulder_yaw" ctrlrange="-18 18" />
  560 |     <motor class="h1" name="f_left_elbow" joint="f_left_elbow" ctrlrange="-18 18" />
  561 |     <motor class="h1" name="f_right_shoulder_pitch" joint="f_right_shoulder_pitch" ctrlrange="-40 40" />
  562 |     <motor class="h1" name="f_right_shoulder_roll" joint="f_right_shoulder_roll" ctrlrange="-40 40" />
  563 |     <motor class="h1" name="f_right_shoulder_yaw" joint="f_right_shoulder_yaw" ctrlrange="-18 18" />
  564 |     <motor class="h1" name="f_right_elbow" joint="f_right_elbow" ctrlrange="-18 18" />
  565 |   </actuator>
  566 |   <equality>
  567 |     <weld name="p_ball_weld" site1="p_pitcher_hand_site" site2="ball_site" />
  568 |   </equality>
  569 | </mujoco>
````
