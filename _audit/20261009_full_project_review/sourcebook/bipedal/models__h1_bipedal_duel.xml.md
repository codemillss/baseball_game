# bipedal/models/h1_bipedal_duel.xml

원본: [models/h1_bipedal_duel.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/models/h1_bipedal_duel.xml)

SHA256: `1963f90f122d965d3209edf51879776c78e595a3c9fdf64ba7a288459d1a810f`

전체 412행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <?xml version='1.0' encoding='utf-8'?>
    2 | <mujoco model="h1_bipedal_duel">
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
   14 |           <geom type="capsule" size=".014" />
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
   34 |     <material name="ball_mat" rgba="0.98 0.98 0.95 1" reflectance="0.4" />
   35 |     <material name="target_zone_mat" rgba="0.2 0.8 0.3 0.35" />
   36 |     <material name="strike_zone_target_mat" rgba="0.9 0.2 0.2 0.4" />
   37 |     <mesh file="pelvis.stl" />
   38 |     <mesh file="left_hip_yaw_link.stl" />
   39 |     <mesh file="left_hip_roll_link.stl" />
   40 |     <mesh file="left_hip_pitch_link.stl" />
   41 |     <mesh file="left_knee_link.stl" />
   42 |     <mesh file="left_ankle_link.stl" />
   43 |     <mesh file="right_hip_yaw_link.stl" />
   44 |     <mesh file="right_hip_roll_link.stl" />
   45 |     <mesh file="right_hip_pitch_link.stl" />
   46 |     <mesh file="right_knee_link.stl" />
   47 |     <mesh file="right_ankle_link.stl" />
   48 |     <mesh file="torso_link.stl" />
   49 |     <mesh file="left_shoulder_pitch_link.stl" />
   50 |     <mesh file="left_shoulder_roll_link.stl" />
   51 |     <mesh file="left_shoulder_yaw_link.stl" />
   52 |     <mesh file="left_elbow_link.stl" />
   53 |     <mesh file="right_shoulder_pitch_link.stl" />
   54 |     <mesh file="right_shoulder_roll_link.stl" />
   55 |     <mesh file="right_shoulder_yaw_link.stl" />
   56 |     <mesh file="right_elbow_link.stl" />
   57 |     <mesh file="logo_link.stl" />
   58 |     <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="512" />
   59 |     <texture name="texplane" type="2d" builtin="checker" rgb1="0.15 0.45 0.15" rgb2="0.12 0.38 0.12" width="512" height="512" />
   60 |     <material name="bat_mat" rgba="0.82 0.55 0.28 1" reflectance="0.3" />
   61 |     <material name="strike_zone_mat" rgba="0.2 0.8 0.3 0.25" />
   62 |     <material name="sweet_spot_mat" rgba="0.9 0.1 0.1 0.7" />
   63 |   </asset>
   64 |   <worldbody>
   65 |     <light directional="true" diffuse="0.85 0.85 0.85" specular="0.25 0.25 0.25" pos="0 5 12" dir="0 0 -1" />
   66 |     <light directional="true" diffuse="0.4 0.4 0.4" pos="-5 -5 10" dir="1 1 -1" />
   67 |     <geom name="ground" type="plane" size="40 40 0.1" material="matplane" />
   68 |     <geom name="home_plate" type="box" size="0.216 0.216 0.005" pos="0 0 0.005" material="home_plate_mat" />
   69 |     <geom name="pitcher_mound" type="cylinder" size="1.2 0.02" pos="0 10.0 0.01" material="home_plate_mat" />
   70 |     <geom name="pitcher_rubber" type="box" size="0.30 0.07 0.008" pos="0 10.0 0.025" material="home_plate_mat" />
   71 |     <site name="strike_zone_target" type="box" size="0.216 0.02 0.22" pos="0 0.0 0.80" material="target_zone_mat" />
   72 |     <site name="pitch_target_point" type="sphere" size="0.04" pos="0 0.0 0.80" material="strike_zone_target_mat" />
   73 |     <geom name="left_box" type="box" size="0.45 0.9 0.002" pos="-0.85 0 0.002" rgba="0.8 0.8 0.8 0.3" />
   74 |     <camera name="duel_broadcast_cam" pos="-9.0 5.0 3.6" xyaxes="0 -1 0 0.35 0 0.94" fovy="68" />
   75 |     <camera name="side_cam" pos="-3.5 0.5 1.4" xyaxes="0 -1 0 0.15 0 0.98" fovy="48" />
   76 |     <camera name="pitcher_cam" pos="0 11.5 1.8" xyaxes="1 0 0 0 -0.2 0.98" fovy="55" />
   77 |     <camera name="catcher_cam" mode="targetbody" target="p_pelvis" pos="0 -1.5 1.0" fovy="45" />
   78 |     <camera name="batter_cam" pos="-2.8 -2.0 1.8" xyaxes="0.75 -0.66 0 0.25 0.28 0.93" fovy="48" />
   79 |     <body name="p_pelvis" pos="0 10.0 0.82" quat="0.7071068 0 0 -0.7071068" childclass="h1">
   80 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
   81 |       <geom class="visual" mesh="pelvis" />
   82 |       <body name="p_left_hip_yaw_link" pos="0 0.0875 -0.1742">
   83 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
   84 |         <joint name="p_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
   85 |         <geom class="visual" mesh="left_hip_yaw_link" />
   86 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
   87 |         <body name="p_left_hip_roll_link" pos="0.039468 0 0">
   88 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
   89 |           <joint name="p_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
   90 |           <geom class="visual" mesh="left_hip_roll_link" />
   91 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
   92 |           <body name="p_left_hip_pitch_link" pos="0 0.11536 0">
   93 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
   94 |             <joint name="p_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
   95 |             <geom class="visual" mesh="left_hip_pitch_link" />
   96 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
   97 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
   98 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
   99 |             <body name="p_left_knee_link" pos="0 0 -0.4">
  100 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  101 |               <joint name="p_left_knee" axis="0 1 0" range="-0.26 2.05" />
  102 |               <geom class="visual" mesh="left_knee_link" />
  103 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  104 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  105 |               <body name="p_left_ankle_link" pos="0 0 -0.4">
  106 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  107 |                 <joint name="p_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  108 |                 <geom class="visual" mesh="left_ankle_link" />
  109 |                 <geom class="foot1" />
  110 |                 <geom class="foot2" />
  111 |                 <geom class="foot3" />
  112 |               </body>
  113 |             </body>
  114 |           </body>
  115 |         </body>
  116 |       </body>
  117 |       <body name="p_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  118 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  119 |         <joint name="p_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  120 |         <geom class="visual" mesh="right_hip_yaw_link" />
  121 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  122 |         <body name="p_right_hip_roll_link" pos="0.039468 0 0">
  123 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0729075 0.701867 0.0438242 0.70721" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  124 |           <joint name="p_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  125 |           <geom class="visual" mesh="right_hip_roll_link" />
  126 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  127 |           <body name="p_right_hip_pitch_link" pos="0 -0.11536 0">
  128 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  129 |             <joint name="p_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  130 |             <geom class="visual" mesh="right_hip_pitch_link" />
  131 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  132 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  133 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  134 |             <body name="p_right_knee_link" pos="0 0 -0.4">
  135 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  136 |               <joint name="p_right_knee" axis="0 1 0" range="-0.26 2.05" />
  137 |               <geom class="visual" mesh="right_knee_link" />
  138 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  139 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  140 |               <body name="p_right_ankle_link" pos="0 0 -0.4">
  141 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  142 |                 <joint name="p_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  143 |                 <geom class="visual" mesh="right_ankle_link" />
  144 |                 <geom class="foot1" />
  145 |                 <geom class="foot2" />
  146 |                 <geom class="foot3" />
  147 |               </body>
  148 |             </body>
  149 |           </body>
  150 |         </body>
  151 |       </body>
  152 |       <body name="p_torso_link" pos="0 0 0">
  153 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00127082 -0.0043492 0.00149972" mass="17.789" diaginertia="0.487014 0.409608 0.127815" />
  154 |         <joint name="p_torso" axis="0 0 1" range="-2.35 2.35" />
  155 |         <geom class="visual" mesh="torso_link" />
  156 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.15 0.04 0 0.15" />
  157 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.25 0.04 0 0.25" />
  158 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.35 0.04 0 0.35" />
  159 |         <geom class="visual" mesh="logo_link" />
  160 |         <body name="p_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  161 |           <inertial pos="-0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  162 |           <joint name="p_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  163 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  164 |           <body name="p_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  165 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  166 |             <joint name="p_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  167 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  168 |             <geom name="p_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.07 -0.02 0 0.01 0.008" />
  169 |             <body name="p_left_shoulder_yaw_link" pos="0 0 -0.1343">
  170 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  171 |               <joint name="p_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  172 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  173 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  174 |               <body name="p_left_elbow_link" pos="0.0185 0 -0.198">
  175 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.684102 -0.0853116 -0.0765232 0.720327" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  176 |                 <joint name="p_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  177 |                 <geom class="visual" mesh="left_elbow_link" />
  178 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  179 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  180 |               </body>
  181 |             </body>
  182 |           </body>
  183 |         </body>
  184 |         <body name="p_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  185 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  186 |           <joint name="p_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  187 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  188 |           <body name="p_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  189 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  190 |             <joint name="p_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  191 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  192 |             <geom name="p_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  193 |             <body name="p_right_shoulder_yaw_link" pos="0 0 -0.1343">
  194 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  195 |               <joint name="p_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  196 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  197 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  198 |               <body name="p_right_elbow_link" pos="0.0185 0 -0.198">
  199 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  200 |                 <joint name="p_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  201 |                 <geom class="visual" mesh="right_elbow_link" />
  202 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  203 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  204 |                 <site name="p_pitcher_hand_site" pos="0.30 0 -0.015" size="0.01" />
  205 |               </body>
  206 |             </body>
  207 |           </body>
  208 |         </body>
  209 |       </body>
  210 |     </body>
  211 |     <body name="b_pelvis" pos="-0.85 0.00 0.88" childclass="h1">
  212 |       <freejoint name="b_pelvis_joint" />
  213 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
  214 |       <geom class="visual" mesh="pelvis" />
  215 |       <body name="b_left_hip_yaw_link" pos="0 0.0875 -0.1742">
  216 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  217 |         <joint name="b_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  218 |         <geom class="visual" mesh="left_hip_yaw_link" />
  219 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  220 |         <body name="b_left_hip_roll_link" pos="0.039468 0 0">
  221 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  222 |           <joint name="b_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  223 |           <geom class="visual" mesh="left_hip_roll_link" />
  224 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  225 |           <body name="b_left_hip_pitch_link" pos="0 0.11536 0">
  226 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  227 |             <joint name="b_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  228 |             <geom class="visual" mesh="left_hip_pitch_link" />
  229 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  230 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  231 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  232 |             <body name="b_left_knee_link" pos="0 0 -0.4">
  233 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  234 |               <joint name="b_left_knee" axis="0 1 0" range="-0.26 2.05" />
  235 |               <geom class="visual" mesh="left_knee_link" />
  236 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  237 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  238 |               <body name="b_left_ankle_link" pos="0 0 -0.4">
  239 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  240 |                 <joint name="b_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  241 |                 <geom class="visual" mesh="left_ankle_link" />
  242 |                 <geom class="foot1" />
  243 |                 <geom class="foot2" />
  244 |                 <geom class="foot3" />
  245 |               </body>
  246 |             </body>
  247 |           </body>
  248 |         </body>
  249 |       </body>
  250 |       <body name="b_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  251 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  252 |         <joint name="b_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  253 |         <geom class="visual" mesh="right_hip_yaw_link" />
  254 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  255 |         <body name="b_right_hip_roll_link" pos="0.039468 0 0">
  256 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0438242 0.70721 0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  257 |           <joint name="b_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  258 |           <geom class="visual" mesh="right_hip_roll_link" />
  259 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  260 |           <body name="b_right_hip_pitch_link" pos="0 -0.11536 0">
  261 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  262 |             <joint name="b_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  263 |             <geom class="visual" mesh="right_hip_pitch_link" />
  264 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  265 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  266 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  267 |             <body name="b_right_knee_link" pos="0 0 -0.4">
  268 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  269 |               <joint name="b_right_knee" axis="0 1 0" range="-0.26 2.05" />
  270 |               <geom class="visual" mesh="right_knee_link" />
  271 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  272 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  273 |               <body name="b_right_ankle_link" pos="0 0 -0.4">
  274 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  275 |                 <joint name="b_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  276 |                 <geom class="visual" mesh="right_ankle_link" />
  277 |                 <geom class="foot1" />
  278 |                 <geom class="foot2" />
  279 |                 <geom class="foot3" />
  280 |               </body>
  281 |             </body>
  282 |           </body>
  283 |         </body>
  284 |       </body>
  285 |       <body name="b_torso_link">
  286 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00130808 -0.00282289 -0.00349105" mass="17.789" diaginertia="0.487315 0.409628 0.127837" />
  287 |         <joint name="b_torso" axis="0 0 1" range="-2.35 2.35" />
  288 |         <geom class="visual" mesh="torso_link" />
  289 |         <geom class="visual" material="white" mesh="logo_link" />
  290 |         <geom name="b_head" class="collision" type="capsule" size="0.06" fromto="0.05 0 0.68 0.05 0 0.6" />
  291 |         <geom name="b_helmet" class="collision" type="sphere" size="0.073" pos="0.045 0 0.68" />
  292 |         <geom name="b_torso" class="collision" type="box" size="0.07 0.1 0.22" pos="0 0 0.25" />
  293 |         <geom name="b_hip" class="collision" type="capsule" size="0.05" fromto="0 -0.1 -0.05 0 0.1 -0.05" />
  294 |         <site name="b_imu" pos="-0.04452 -0.01891 0.27756" />
  295 |         <body name="b_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  296 |           <inertial pos="0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 -0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  297 |           <joint name="b_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  298 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  299 |           <body name="b_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  300 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  301 |             <joint name="b_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  302 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  303 |             <geom name="b_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  304 |             <body name="b_left_shoulder_yaw_link" pos="0 0 -0.1343">
  305 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  306 |               <joint name="b_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  307 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  308 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  309 |               <body name="b_left_elbow_link" pos="0.0185 0 -0.198">
  310 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  311 |                 <joint name="b_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  312 |                 <geom class="visual" mesh="left_elbow_link" />
  313 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  314 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  315 |                 <site name="b_l_hand_grip" pos="0.30 0 0" size="0.01" />
  316 |               </body>
  317 |             </body>
  318 |           </body>
  319 |         </body>
  320 |         <body name="b_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  321 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  322 |           <joint name="b_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  323 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  324 |           <body name="b_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  325 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  326 |             <joint name="b_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  327 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  328 |             <geom name="b_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  329 |             <body name="b_right_shoulder_yaw_link" pos="0 0 -0.1343">
  330 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  331 |               <joint name="b_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  332 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  333 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  334 |               <body name="b_right_elbow_link" pos="0.0185 0 -0.198">
  335 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  336 |                 <joint name="b_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  337 |                 <geom class="visual" mesh="right_elbow_link" />
  338 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  339 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  340 |                 <body name="b_bat" pos="0.30 0 0" quat="0.7071068 0 0.7071068 0">
  341 |                   <geom name="bat_barrel" type="cylinder" size="0.032 0.45" pos="0 0 0.45" material="bat_mat" mass="0.90" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" />
  342 |                   <site name="bat_knob" pos="0 0 0.02" size="0.01" />
  343 |                   <site name="bat_grip_left" pos="0 0 0.08" size="0.01" />
  344 |                   <site name="bat_sweet_spot" pos="0 0 0.73" size="0.015" material="sweet_spot_mat" />
  345 |                   <site name="bat_tip" pos="0 0 0.90" size="0.01" />
  346 |                 </body>
  347 |               </body>
  348 |             </body>
  349 |           </body>
  350 |         </body>
  351 |       </body>
  352 |     </body>
  353 |     <body name="baseball" pos="0 10.0 1.2">
  354 |       <freejoint name="ball_joint" />
  355 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" />
  356 |       <site name="ball_site" pos="0 0 0" size="0.01" />
  357 |     </body>
  358 |   </worldbody>
  359 |   <contact>
  360 |     <exclude body1="p_torso_link" body2="p_right_shoulder_roll_link" />
  361 |     <exclude body1="p_torso_link" body2="p_left_shoulder_roll_link" />
  362 |     <exclude body1="b_torso_link" body2="b_right_shoulder_roll_link" />
  363 |     <exclude body1="b_torso_link" body2="b_left_shoulder_roll_link" />
  364 |     <exclude body1="baseball" body2="p_right_elbow_link" />
  365 |     <exclude body1="baseball" body2="b_right_elbow_link" />
  366 |     <exclude body1="baseball" body2="b_left_elbow_link" />
  367 |     <pair geom1="bat_barrel" geom2="ball_geom" solref="0.0015 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.4 0.01 0.001" />
  368 |   </contact>
  369 |   <actuator>
  370 |     <motor class="h1" name="p_left_hip_yaw" joint="p_left_hip_yaw" ctrlrange="-200 200" />
  371 |     <motor class="h1" name="p_left_hip_roll" joint="p_left_hip_roll" ctrlrange="-200 200" />
  372 |     <motor class="h1" name="p_left_hip_pitch" joint="p_left_hip_pitch" ctrlrange="-200 200" />
  373 |     <motor class="h1" name="p_left_knee" joint="p_left_knee" ctrlrange="-300 300" />
  374 |     <motor class="h1" name="p_left_ankle" joint="p_left_ankle" ctrlrange="-40 40" />
  375 |     <motor class="h1" name="p_right_hip_yaw" joint="p_right_hip_yaw" ctrlrange="-200 200" />
  376 |     <motor class="h1" name="p_right_hip_roll" joint="p_right_hip_roll" ctrlrange="-200 200" />
  377 |     <motor class="h1" name="p_right_hip_pitch" joint="p_right_hip_pitch" ctrlrange="-200 200" />
  378 |     <motor class="h1" name="p_right_knee" joint="p_right_knee" ctrlrange="-300 300" />
  379 |     <motor class="h1" name="p_right_ankle" joint="p_right_ankle" ctrlrange="-40 40" />
  380 |     <motor class="h1" name="p_torso" joint="p_torso" ctrlrange="-200 200" />
  381 |     <motor class="h1" name="p_left_shoulder_pitch" joint="p_left_shoulder_pitch" ctrlrange="-40 40" />
  382 |     <motor class="h1" name="p_left_shoulder_roll" joint="p_left_shoulder_roll" ctrlrange="-40 40" />
  383 |     <motor class="h1" name="p_left_shoulder_yaw" joint="p_left_shoulder_yaw" ctrlrange="-18 18" />
  384 |     <motor class="h1" name="p_left_elbow" joint="p_left_elbow" ctrlrange="-18 18" />
  385 |     <motor class="h1" name="p_right_shoulder_pitch" joint="p_right_shoulder_pitch" ctrlrange="-40 40" />
  386 |     <motor class="h1" name="p_right_shoulder_roll" joint="p_right_shoulder_roll" ctrlrange="-40 40" />
  387 |     <motor class="h1" name="p_right_shoulder_yaw" joint="p_right_shoulder_yaw" ctrlrange="-18 18" />
  388 |     <motor class="h1" name="p_right_elbow" joint="p_right_elbow" ctrlrange="-18 18" />
  389 |     <motor class="h1" name="b_left_hip_yaw" joint="b_left_hip_yaw" ctrlrange="-200 200" />
  390 |     <motor class="h1" name="b_left_hip_roll" joint="b_left_hip_roll" ctrlrange="-200 200" />
  391 |     <motor class="h1" name="b_left_hip_pitch" joint="b_left_hip_pitch" ctrlrange="-200 200" />
  392 |     <motor class="h1" name="b_left_knee" joint="b_left_knee" ctrlrange="-300 300" />
  393 |     <motor class="h1" name="b_left_ankle" joint="b_left_ankle" ctrlrange="-40 40" />
  394 |     <motor class="h1" name="b_right_hip_yaw" joint="b_right_hip_yaw" ctrlrange="-200 200" />
  395 |     <motor class="h1" name="b_right_hip_roll" joint="b_right_hip_roll" ctrlrange="-200 200" />
  396 |     <motor class="h1" name="b_right_hip_pitch" joint="b_right_hip_pitch" ctrlrange="-200 200" />
  397 |     <motor class="h1" name="b_right_knee" joint="b_right_knee" ctrlrange="-300 300" />
  398 |     <motor class="h1" name="b_right_ankle" joint="b_right_ankle" ctrlrange="-40 40" />
  399 |     <motor class="h1" name="b_torso" joint="b_torso" ctrlrange="-200 200" />
  400 |     <motor class="h1" name="b_left_shoulder_pitch" joint="b_left_shoulder_pitch" ctrlrange="-40 40" />
  401 |     <motor class="h1" name="b_left_shoulder_roll" joint="b_left_shoulder_roll" ctrlrange="-40 40" />
  402 |     <motor class="h1" name="b_left_shoulder_yaw" joint="b_left_shoulder_yaw" ctrlrange="-18 18" />
  403 |     <motor class="h1" name="b_left_elbow" joint="b_left_elbow" ctrlrange="-18 18" />
  404 |     <motor class="h1" name="b_right_shoulder_pitch" joint="b_right_shoulder_pitch" ctrlrange="-40 40" />
  405 |     <motor class="h1" name="b_right_shoulder_roll" joint="b_right_shoulder_roll" ctrlrange="-40 40" />
  406 |     <motor class="h1" name="b_right_shoulder_yaw" joint="b_right_shoulder_yaw" ctrlrange="-18 18" />
  407 |     <motor class="h1" name="b_right_elbow" joint="b_right_elbow" ctrlrange="-18 18" />
  408 |   </actuator>
  409 |   <equality>
  410 |     <weld name="p_ball_weld" site1="p_pitcher_hand_site" site2="ball_site" />
  411 |   </equality>
  412 | </mujoco>
````
