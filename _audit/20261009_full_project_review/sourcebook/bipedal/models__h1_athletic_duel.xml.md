# bipedal/models/h1_athletic_duel.xml

원본: [models/h1_athletic_duel.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/models/h1_athletic_duel.xml)

SHA256: `66b21dbec47b954fac9d822ec1cec5e72014d7da515ff133d316c2407d83a910`

전체 575행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

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
   76 |     <body name="baseball" pos="0 10.0 1.48">
   77 |       <freejoint name="ball_joint" />
   78 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.4 0.02 0.001" />
   79 |       <site name="ball_site" pos="0 0 0" size="0.01" />
   80 |     </body>
   81 | 
   82 | <body name="p_pelvis" pos="0 10.0 0.82" quat="0.7071068 0 0 -0.7071068" childclass="h1">
   83 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
   84 |       <geom class="visual" mesh="pelvis" />
   85 |       <body name="p_left_hip_yaw_link" pos="0 0.0875 -0.1742">
   86 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
   87 |         <joint name="p_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
   88 |         <geom class="visual" mesh="left_hip_yaw_link" />
   89 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
   90 |         <body name="p_left_hip_roll_link" pos="0.039468 0 0">
   91 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
   92 |           <joint name="p_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
   93 |           <geom class="visual" mesh="left_hip_roll_link" />
   94 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
   95 |           <body name="p_left_hip_pitch_link" pos="0 0.11536 0">
   96 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
   97 |             <joint name="p_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
   98 |             <geom class="visual" mesh="left_hip_pitch_link" />
   99 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  100 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  101 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  102 |             <body name="p_left_knee_link" pos="0 0 -0.4">
  103 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  104 |               <joint name="p_left_knee" axis="0 1 0" range="-0.26 2.05" />
  105 |               <geom class="visual" mesh="left_knee_link" />
  106 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  107 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  108 |               <body name="p_left_ankle_link" pos="0 0 -0.4">
  109 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  110 |                 <joint name="p_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  111 |                 <geom class="visual" mesh="left_ankle_link" />
  112 |                 <geom class="foot1" />
  113 |                 <geom class="foot2" />
  114 |                 <geom class="foot3" />
  115 |               </body>
  116 |             </body>
  117 |           </body>
  118 |         </body>
  119 |       </body>
  120 |       <body name="p_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  121 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  122 |         <joint name="p_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  123 |         <geom class="visual" mesh="right_hip_yaw_link" />
  124 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  125 |         <body name="p_right_hip_roll_link" pos="0.039468 0 0">
  126 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0729075 0.701867 0.0438242 0.70721" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  127 |           <joint name="p_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  128 |           <geom class="visual" mesh="right_hip_roll_link" />
  129 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  130 |           <body name="p_right_hip_pitch_link" pos="0 -0.11536 0">
  131 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  132 |             <joint name="p_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  133 |             <geom class="visual" mesh="right_hip_pitch_link" />
  134 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  135 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  136 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  137 |             <body name="p_right_knee_link" pos="0 0 -0.4">
  138 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  139 |               <joint name="p_right_knee" axis="0 1 0" range="-0.26 2.05" />
  140 |               <geom class="visual" mesh="right_knee_link" />
  141 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  142 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  143 |               <body name="p_right_ankle_link" pos="0 0 -0.4">
  144 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  145 |                 <joint name="p_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  146 |                 <geom class="visual" mesh="right_ankle_link" />
  147 |                 <geom class="foot1" />
  148 |                 <geom class="foot2" />
  149 |                 <geom class="foot3" />
  150 |               </body>
  151 |             </body>
  152 |           </body>
  153 |         </body>
  154 |       </body>
  155 |       <body name="p_torso_link" pos="0 0 0">
  156 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00127082 -0.0043492 0.00149972" mass="17.789" diaginertia="0.487014 0.409608 0.127815" />
  157 |         <joint name="p_torso" axis="0 0 1" range="-2.35 2.35" />
  158 |         <geom class="visual" mesh="torso_link" />
  159 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.15 0.04 0 0.15" />
  160 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.25 0.04 0 0.25" />
  161 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.35 0.04 0 0.35" />
  162 |         <geom class="visual" mesh="logo_link" />
  163 |         <body name="p_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  164 |           <inertial pos="-0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  165 |           <joint name="p_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  166 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  167 |           <body name="p_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  168 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  169 |             <joint name="p_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  170 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  171 |             <geom name="p_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.07 -0.02 0 0.01 0.008" />
  172 |             <body name="p_left_shoulder_yaw_link" pos="0 0 -0.1343">
  173 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  174 |               <joint name="p_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  175 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  176 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  177 |               <body name="p_left_elbow_link" pos="0.0185 0 -0.198">
  178 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.684102 -0.0853116 -0.0765232 0.720327" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  179 |                 <joint name="p_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  180 |                 <geom class="visual" mesh="left_elbow_link" />
  181 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  182 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  183 |               </body>
  184 |             </body>
  185 |           </body>
  186 |         </body>
  187 |         <body name="p_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  188 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  189 |           <joint name="p_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  190 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  191 |           <body name="p_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  192 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  193 |             <joint name="p_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  194 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  195 |             <geom name="p_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  196 |             <body name="p_right_shoulder_yaw_link" pos="0 0 -0.1343">
  197 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  198 |               <joint name="p_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  199 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  200 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  201 |               <body name="p_right_elbow_link" pos="0.0185 0 -0.198">
  202 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  203 |                 <joint name="p_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  204 |                 <geom class="visual" mesh="right_elbow_link" />
  205 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  206 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  207 |                 <site name="p_pitcher_hand_site" pos="0.30 0 -0.015" size="0.01" />
  208 |               </body>
  209 |             </body>
  210 |           </body>
  211 |         </body>
  212 |       </body>
  213 |     </body>
  214 |     
  215 | <body name="c_pelvis" pos="0.0 -0.95 0.52" quat="0.7071068 0 0 0.7071068" childclass="h1">
  216 |       <freejoint name="c_pelvis_joint" />
  217 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
  218 |       <geom class="visual" mesh="pelvis" />
  219 |       <body name="c_left_hip_yaw_link" pos="0 0.0875 -0.1742">
  220 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  221 |         <joint name="c_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  222 |         <geom class="visual" mesh="left_hip_yaw_link" />
  223 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  224 |         <body name="c_left_hip_roll_link" pos="0.039468 0 0">
  225 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  226 |           <joint name="c_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  227 |           <geom class="visual" mesh="left_hip_roll_link" />
  228 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  229 |           <body name="c_left_hip_pitch_link" pos="0 0.11536 0">
  230 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  231 |             <joint name="c_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  232 |             <geom class="visual" mesh="left_hip_pitch_link" />
  233 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  234 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  235 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  236 |             <body name="c_left_knee_link" pos="0 0 -0.4">
  237 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  238 |               <joint name="c_left_knee" axis="0 1 0" range="-0.26 2.05" />
  239 |               <geom class="visual" mesh="left_knee_link" />
  240 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  241 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  242 |               <body name="c_left_ankle_link" pos="0 0 -0.4">
  243 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  244 |                 <joint name="c_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  245 |                 <geom class="visual" mesh="left_ankle_link" />
  246 |                 <geom class="foot1" />
  247 |                 <geom class="foot2" />
  248 |                 <geom class="foot3" />
  249 |               </body>
  250 |             </body>
  251 |           </body>
  252 |         </body>
  253 |       </body>
  254 |       <body name="c_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  255 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  256 |         <joint name="c_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  257 |         <geom class="visual" mesh="right_hip_yaw_link" />
  258 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  259 |         <body name="c_right_hip_roll_link" pos="0.039468 0 0">
  260 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0438242 0.70721 0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  261 |           <joint name="c_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  262 |           <geom class="visual" mesh="right_hip_roll_link" />
  263 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  264 |           <body name="c_right_hip_pitch_link" pos="0 -0.11536 0">
  265 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  266 |             <joint name="c_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  267 |             <geom class="visual" mesh="right_hip_pitch_link" />
  268 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  269 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  270 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  271 |             <body name="c_right_knee_link" pos="0 0 -0.4">
  272 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  273 |               <joint name="c_right_knee" axis="0 1 0" range="-0.26 2.05" />
  274 |               <geom class="visual" mesh="right_knee_link" />
  275 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  276 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  277 |               <body name="c_right_ankle_link" pos="0 0 -0.4">
  278 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  279 |                 <joint name="c_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  280 |                 <geom class="visual" mesh="right_ankle_link" />
  281 |                 <geom class="foot1" />
  282 |                 <geom class="foot2" />
  283 |                 <geom class="foot3" />
  284 |               </body>
  285 |             </body>
  286 |           </body>
  287 |         </body>
  288 |       </body>
  289 |       <body name="c_torso_link" pos="0 0 0">
  290 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00127082 -0.00434747 0.00162814" mass="17.789" diaginertia="0.487405 0.409312 0.127837" />
  291 |         <joint name="c_torso" axis="0 0 1" range="-2.35 2.35" />
  292 |         <geom class="visual" mesh="torso_link" />
  293 |         <geom class="visual" mesh="logo_link" />
  294 |         <geom class="collision" type="capsule" size="0.08" fromto="-0.03 0 0.05 -0.03 0 0.45" />
  295 |         <body name="c_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  296 |           <inertial pos="-0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  297 |           <joint name="c_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  298 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  299 |           <body name="c_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  300 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  301 |             <joint name="c_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  302 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  303 |             <geom name="c_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  304 |             <body name="c_left_shoulder_yaw_link" pos="0 0 -0.1343">
  305 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  306 |               <joint name="c_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  307 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  308 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  309 |               <body name="c_left_elbow_link" pos="0.0185 0 -0.198">
  310 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  311 |                 <joint name="c_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  312 |                 <geom class="visual" mesh="left_elbow_link" />
  313 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  314 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  315 |                 <site name="c_l_hand_grip" pos="0.30 0 0" size="0.01" />
  316 |               
  317 |         <body name="c_mitt" pos="0.22 0 0" quat="0.7071068 0 0.7071068 0">
  318 |           <geom name="c_mitt_geom" type="cylinder" size="0.14 0.04" pos="0 0 0" material="glove_mat" mass="0.45" contype="0" conaffinity="0" />
  319 |           <site name="c_mitt_site" type="sphere" size="0.05" pos="0 0 0" rgba="0.9 0.4 0.1 0.6" />
  320 |         </body>
  321 | </body>
  322 |             </body>
  323 |           </body>
  324 |         </body>
  325 |         <body name="c_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  326 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  327 |           <joint name="c_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  328 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  329 |           <body name="c_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  330 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  331 |             <joint name="c_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  332 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  333 |             <geom name="c_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  334 |             <body name="c_right_shoulder_yaw_link" pos="0 0 -0.1343">
  335 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  336 |               <joint name="c_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  337 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  338 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  339 |               <body name="c_right_elbow_link" pos="0.0185 0 -0.198">
  340 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  341 |                 <joint name="c_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  342 |                 <geom class="visual" mesh="right_elbow_link" />
  343 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  344 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  345 |                 
  346 |               </body>
  347 |             </body>
  348 |           </body>
  349 |         </body>
  350 |       </body>
  351 |     </body>
  352 |     
  353 |   <body name="b_pelvis" pos="-1.10 0.00 0.86" childclass="h1">
  354 |       <freejoint name="b_pelvis_joint" />
  355 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
  356 |       <geom class="visual" mesh="pelvis" />
  357 |       <body name="b_left_hip_yaw_link" pos="0 0.0875 -0.1742">
  358 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  359 |         <joint name="b_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  360 |         <geom class="visual" mesh="left_hip_yaw_link" />
  361 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  362 |         <body name="b_left_hip_roll_link" pos="0.039468 0 0">
  363 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  364 |           <joint name="b_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  365 |           <geom class="visual" mesh="left_hip_roll_link" />
  366 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  367 |           <body name="b_left_hip_pitch_link" pos="0 0.11536 0">
  368 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  369 |             <joint name="b_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  370 |             <geom class="visual" mesh="left_hip_pitch_link" />
  371 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  372 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  373 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  374 |             <body name="b_left_knee_link" pos="0 0 -0.4">
  375 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  376 |               <joint name="b_left_knee" axis="0 1 0" range="-0.26 2.05" />
  377 |               <geom class="visual" mesh="left_knee_link" />
  378 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  379 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  380 |               <body name="b_left_ankle_link" pos="0 0 -0.4">
  381 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  382 |                 <joint name="b_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  383 |                 <geom class="visual" mesh="left_ankle_link" />
  384 |                 <geom class="foot1" />
  385 |                 <geom class="foot2" />
  386 |                 <geom class="foot3" />
  387 |               </body>
  388 |             </body>
  389 |           </body>
  390 |         </body>
  391 |       </body>
  392 |       <body name="b_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  393 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  394 |         <joint name="b_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  395 |         <geom class="visual" mesh="right_hip_yaw_link" />
  396 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  397 |         <body name="b_right_hip_roll_link" pos="0.039468 0 0">
  398 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0438242 0.70721 0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  399 |           <joint name="b_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  400 |           <geom class="visual" mesh="right_hip_roll_link" />
  401 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  402 |           <body name="b_right_hip_pitch_link" pos="0 -0.11536 0">
  403 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  404 |             <joint name="b_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  405 |             <geom class="visual" mesh="right_hip_pitch_link" />
  406 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  407 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  408 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  409 |             <body name="b_right_knee_link" pos="0 0 -0.4">
  410 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  411 |               <joint name="b_right_knee" axis="0 1 0" range="-0.26 2.05" />
  412 |               <geom class="visual" mesh="right_knee_link" />
  413 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  414 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  415 |               <body name="b_right_ankle_link" pos="0 0 -0.4">
  416 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  417 |                 <joint name="b_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  418 |                 <geom class="visual" mesh="right_ankle_link" />
  419 |                 <geom class="foot1" />
  420 |                 <geom class="foot2" />
  421 |                 <geom class="foot3" />
  422 |               </body>
  423 |             </body>
  424 |           </body>
  425 |         </body>
  426 |       </body>
  427 |       <body name="b_torso_link">
  428 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00130808 -0.00282289 -0.00349105" mass="17.789" diaginertia="0.487315 0.409628 0.127837" />
  429 |         <joint name="b_torso" axis="0 0 1" range="-2.35 2.35" />
  430 |         <geom class="visual" mesh="torso_link" />
  431 |         <geom class="visual" material="white" mesh="logo_link" />
  432 |         <geom name="b_head" class="collision" type="capsule" size="0.06" fromto="0.05 0 0.68 0.05 0 0.6" />
  433 |         <geom name="b_helmet" class="collision" type="sphere" size="0.073" pos="0.045 0 0.68" />
  434 |         <geom name="b_torso" class="collision" type="box" size="0.07 0.1 0.22" pos="0 0 0.25" />
  435 |         <geom name="b_hip" class="collision" type="capsule" size="0.05" fromto="0 -0.1 -0.05 0 0.1 -0.05" />
  436 |         <site name="b_imu" pos="-0.04452 -0.01891 0.27756" />
  437 |         <body name="b_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  438 |           <inertial pos="0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 -0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  439 |           <joint name="b_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  440 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  441 |           <body name="b_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  442 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  443 |             <joint name="b_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  444 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  445 |             <geom name="b_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  446 |             <body name="b_left_shoulder_yaw_link" pos="0 0 -0.1343">
  447 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  448 |               <joint name="b_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  449 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  450 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  451 |               <body name="b_left_elbow_link" pos="0.0185 0 -0.198">
  452 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  453 |                 <joint name="b_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  454 |                 <geom class="visual" mesh="left_elbow_link" />
  455 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  456 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  457 |                 <site name="b_l_hand_grip" pos="0.30 0 0" size="0.01" />
  458 |               </body>
  459 |             </body>
  460 |           </body>
  461 |         </body>
  462 |         <body name="b_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  463 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  464 |           <joint name="b_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  465 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  466 |           <body name="b_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  467 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  468 |             <joint name="b_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  469 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  470 |             <geom name="b_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  471 |             <body name="b_right_shoulder_yaw_link" pos="0 0 -0.1343">
  472 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  473 |               <joint name="b_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  474 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  475 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  476 |               <body name="b_right_elbow_link" pos="0.0185 0 -0.198">
  477 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  478 |                 <joint name="b_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  479 |                 <geom class="visual" mesh="right_elbow_link" />
  480 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  481 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  482 |                 <body name="b_bat" pos="0.30 0 0" quat="0.7071068 0 0.7071068 0">
  483 |                   <geom name="bat_barrel" type="cylinder" size="0.032 0.45" pos="0 0 0.45" material="bat_mat" mass="0.90" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" />
  484 |                   <site name="bat_knob" pos="0 0 0.02" size="0.01" />
  485 |                   <site name="bat_grip_left" pos="0 0 0.08" size="0.01" />
  486 |                   <site name="bat_sweet_spot" pos="0 0 0.73" size="0.015" material="sweet_spot_mat" />
  487 |                   <site name="bat_tip" pos="0 0 0.90" size="0.01" />
  488 |                 </body>
  489 |               </body>
  490 |             </body>
  491 |           </body>
  492 |         </body>
  493 |       </body>
  494 |     </body>
  495 |     <camera name="duel_broadcast_cam" pos="-3.8 -4.2 2.6" xyaxes="0.74 -0.67 0 0.28 0.31 0.91" />
  496 |     <camera name="umpire_cam" pos="0.0 -2.4 1.4" xyaxes="1 0 0 0 0.45 0.89" />
  497 |     <camera name="batter_side_cam" pos="-3.2 0.0 1.2" xyaxes="0 1 0 0 0 1" />
  498 |     <camera name="cf_broadcast_cam" pos="0.0 6.0 2.0" xyaxes="-1 0 0 0 -0.22 0.975" fovy="45" />
  499 |     <camera name="catcher_framing_cam" pos="-1.5 -2.2 1.1" xyaxes="0.85 -0.53 0 0.18 0.29 0.94" fovy="42" />
  500 |     <geom name="batter_box" type="box" size="0.45 0.70 0.002" pos="-1.10 0 0.002" rgba="0.8 0.8 0.8 0.35" contype="0" conaffinity="0" />
  501 |   </worldbody>
  502 |   <contact>
  503 |         <exclude body1="p_torso_link" body2="p_right_shoulder_roll_link" />
  504 |         <exclude body1="p_torso_link" body2="p_left_shoulder_roll_link" />
  505 |         <exclude body1="c_torso_link" body2="c_right_shoulder_roll_link" />
  506 |         <exclude body1="c_torso_link" body2="c_left_shoulder_roll_link" />
  507 |         <exclude body1="baseball" body2="p_right_elbow_link" />
  508 |         <exclude body1="baseball" body2="c_right_elbow_link" />
  509 |         <exclude body1="baseball" body2="c_left_elbow_link" />
  510 |     <pair geom1="c_mitt_geom" geom2="ball_geom" solref="0.005 1" solimp="0.80 0.90 0.001 0.5 2" friction="0.8 0.02 0.001" />
  511 |   </contact>
  512 |   <equality>
  513 |     <weld name="pitch_weld" body1="baseball" body2="p_right_elbow_link" relpose="0.25 0 0 1 0 0 0" active="false" />
  514 |     <connect name="two_hand_grip" site1="b_l_hand_grip" site2="bat_grip_left" solref="0.005 1" solimp="0.95 0.99 0.001" active="true" />
  515 |   </equality>
  516 | <actuator>
  517 |     <motor class="h1" name="p_left_hip_yaw" joint="p_left_hip_yaw" ctrlrange="-200 200" />
  518 |     <motor class="h1" name="p_left_hip_roll" joint="p_left_hip_roll" ctrlrange="-200 200" />
  519 |     <motor class="h1" name="p_left_hip_pitch" joint="p_left_hip_pitch" ctrlrange="-200 200" />
  520 |     <motor class="h1" name="p_left_knee" joint="p_left_knee" ctrlrange="-300 300" />
  521 |     <motor class="h1" name="p_left_ankle" joint="p_left_ankle" ctrlrange="-40 40" />
  522 |     <motor class="h1" name="p_right_hip_yaw" joint="p_right_hip_yaw" ctrlrange="-200 200" />
  523 |     <motor class="h1" name="p_right_hip_roll" joint="p_right_hip_roll" ctrlrange="-200 200" />
  524 |     <motor class="h1" name="p_right_hip_pitch" joint="p_right_hip_pitch" ctrlrange="-200 200" />
  525 |     <motor class="h1" name="p_right_knee" joint="p_right_knee" ctrlrange="-300 300" />
  526 |     <motor class="h1" name="p_right_ankle" joint="p_right_ankle" ctrlrange="-40 40" />
  527 |     <motor class="h1" name="p_torso" joint="p_torso" ctrlrange="-200 200" />
  528 |     <motor class="h1" name="p_left_shoulder_pitch" joint="p_left_shoulder_pitch" ctrlrange="-40 40" />
  529 |     <motor class="h1" name="p_left_shoulder_roll" joint="p_left_shoulder_roll" ctrlrange="-40 40" />
  530 |     <motor class="h1" name="p_left_shoulder_yaw" joint="p_left_shoulder_yaw" ctrlrange="-18 18" />
  531 |     <motor class="h1" name="p_left_elbow" joint="p_left_elbow" ctrlrange="-18 18" />
  532 |     <motor class="h1" name="p_right_shoulder_pitch" joint="p_right_shoulder_pitch" ctrlrange="-40 40" />
  533 |     <motor class="h1" name="p_right_shoulder_roll" joint="p_right_shoulder_roll" ctrlrange="-40 40" />
  534 |     <motor class="h1" name="p_right_shoulder_yaw" joint="p_right_shoulder_yaw" ctrlrange="-18 18" />
  535 |     <motor class="h1" name="p_right_elbow" joint="p_right_elbow" ctrlrange="-18 18" />
  536 |     <motor class="h1" name="c_left_hip_yaw" joint="c_left_hip_yaw" ctrlrange="-200 200" />
  537 |     <motor class="h1" name="c_left_hip_roll" joint="c_left_hip_roll" ctrlrange="-200 200" />
  538 |     <motor class="h1" name="c_left_hip_pitch" joint="c_left_hip_pitch" ctrlrange="-200 200" />
  539 |     <motor class="h1" name="c_left_knee" joint="c_left_knee" ctrlrange="-300 300" />
  540 |     <motor class="h1" name="c_left_ankle" joint="c_left_ankle" ctrlrange="-40 40" />
  541 |     <motor class="h1" name="c_right_hip_yaw" joint="c_right_hip_yaw" ctrlrange="-200 200" />
  542 |     <motor class="h1" name="c_right_hip_roll" joint="c_right_hip_roll" ctrlrange="-200 200" />
  543 |     <motor class="h1" name="c_right_hip_pitch" joint="c_right_hip_pitch" ctrlrange="-200 200" />
  544 |     <motor class="h1" name="c_right_knee" joint="c_right_knee" ctrlrange="-300 300" />
  545 |     <motor class="h1" name="c_right_ankle" joint="c_right_ankle" ctrlrange="-40 40" />
  546 |     <motor class="h1" name="c_torso" joint="c_torso" ctrlrange="-200 200" />
  547 |     <motor class="h1" name="c_left_shoulder_pitch" joint="c_left_shoulder_pitch" ctrlrange="-40 40" />
  548 |     <motor class="h1" name="c_left_shoulder_roll" joint="c_left_shoulder_roll" ctrlrange="-40 40" />
  549 |     <motor class="h1" name="c_left_shoulder_yaw" joint="c_left_shoulder_yaw" ctrlrange="-18 18" />
  550 |     <motor class="h1" name="c_left_elbow" joint="c_left_elbow" ctrlrange="-18 18" />
  551 |     <motor class="h1" name="c_right_shoulder_pitch" joint="c_right_shoulder_pitch" ctrlrange="-40 40" />
  552 |     <motor class="h1" name="c_right_shoulder_roll" joint="c_right_shoulder_roll" ctrlrange="-40 40" />
  553 |     <motor class="h1" name="c_right_shoulder_yaw" joint="c_right_shoulder_yaw" ctrlrange="-18 18" />
  554 |     <motor class="h1" name="c_right_elbow" joint="c_right_elbow" ctrlrange="-18 18" />
  555 |   <motor class="h1" name="b_left_hip_yaw" joint="b_left_hip_yaw" ctrlrange="-200 200" />
  556 |     <motor class="h1" name="b_left_hip_roll" joint="b_left_hip_roll" ctrlrange="-200 200" />
  557 |     <motor class="h1" name="b_left_hip_pitch" joint="b_left_hip_pitch" ctrlrange="-200 200" />
  558 |     <motor class="h1" name="b_left_knee" joint="b_left_knee" ctrlrange="-300 300" />
  559 |     <motor class="h1" name="b_left_ankle" joint="b_left_ankle" ctrlrange="-40 40" />
  560 |     <motor class="h1" name="b_right_hip_yaw" joint="b_right_hip_yaw" ctrlrange="-200 200" />
  561 |     <motor class="h1" name="b_right_hip_roll" joint="b_right_hip_roll" ctrlrange="-200 200" />
  562 |     <motor class="h1" name="b_right_hip_pitch" joint="b_right_hip_pitch" ctrlrange="-200 200" />
  563 |     <motor class="h1" name="b_right_knee" joint="b_right_knee" ctrlrange="-300 300" />
  564 |     <motor class="h1" name="b_right_ankle" joint="b_right_ankle" ctrlrange="-40 40" />
  565 |     <motor class="h1" name="b_torso" joint="b_torso" ctrlrange="-200 200" />
  566 |     <motor class="h1" name="b_left_shoulder_pitch" joint="b_left_shoulder_pitch" ctrlrange="-40 40" />
  567 |     <motor class="h1" name="b_left_shoulder_roll" joint="b_left_shoulder_roll" ctrlrange="-40 40" />
  568 |     <motor class="h1" name="b_left_shoulder_yaw" joint="b_left_shoulder_yaw" ctrlrange="-18 18" />
  569 |     <motor class="h1" name="b_left_elbow" joint="b_left_elbow" ctrlrange="-18 18" />
  570 |     <motor class="h1" name="b_right_shoulder_pitch" joint="b_right_shoulder_pitch" ctrlrange="-40 40" />
  571 |     <motor class="h1" name="b_right_shoulder_roll" joint="b_right_shoulder_roll" ctrlrange="-40 40" />
  572 |     <motor class="h1" name="b_right_shoulder_yaw" joint="b_right_shoulder_yaw" ctrlrange="-18 18" />
  573 |     <motor class="h1" name="b_right_elbow" joint="b_right_elbow" ctrlrange="-18 18" />
  574 |   </actuator>
  575 | </mujoco>
````
