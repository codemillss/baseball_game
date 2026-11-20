# bipedal/models/h1_duel_match.xml

원본: [models/h1_duel_match.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/models/h1_duel_match.xml)

SHA256: `a9cd898415f694dfdb7ffe7f60ad6eb13de5c6c8123de426cebb19824ae19a62`

전체 406행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <?xml version='1.0' encoding='utf-8'?>
    2 | <mujoco model="h1_duel_match">
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
   63 |     <material name="foul_line_mat" rgba="0.9 0.9 0.9 0.8" />
   64 |   </asset>
   65 |   <worldbody>
   66 |     <light directional="true" diffuse="0.85 0.85 0.85" specular="0.25 0.25 0.25" pos="0 5 12" dir="0 0 -1" />
   67 |     <light directional="true" diffuse="0.4 0.4 0.4" pos="-5 -5 10" dir="1 1 -1" />
   68 |     <geom name="ground" type="plane" size="40 40 0.1" material="matplane" />
   69 |     <geom name="home_plate" type="box" size="0.216 0.216 0.005" pos="0 0 0.005" material="home_plate_mat" />
   70 |     <geom name="pitcher_mound" type="cylinder" size="1.2 0.02" pos="0 10.0 0.01" material="home_plate_mat" />
   71 |     <geom name="pitcher_rubber" type="box" size="0.30 0.07 0.008" pos="0 10.0 0.025" material="home_plate_mat" />
   72 |     <site name="strike_zone_target" type="box" size="0.216 0.02 0.22" pos="0 0.0 0.80" material="target_zone_mat" />
   73 |     <site name="pitch_target_point" type="sphere" size="0.04" pos="0 0.0 0.80" material="strike_zone_target_mat" />
   74 |     <camera name="duel_broadcast_cam" pos="-9.0 5.0 3.6" xyaxes="0 -1 0 0.35 0 0.94" fovy="68" />
   75 |     <camera name="side_cam" pos="-3.5 0.5 1.4" xyaxes="0 -1 0 0.15 0 0.98" fovy="48" />
   76 |     <camera name="pitcher_cam" pos="0 11.5 1.8" xyaxes="1 0 0 0 -0.2 0.98" fovy="55" />
   77 |     <camera name="catcher_cam" mode="targetbody" target="p_pelvis" pos="0 -1.5 1.0" fovy="45" />
   78 |     <body name="p_pelvis" pos="0 10.0 0.82" quat="0.7071068 0 0 -0.7071068" childclass="h1">
   79 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
   80 |       <geom class="visual" mesh="pelvis" />
   81 |       <body name="p_left_hip_yaw_link" pos="0 0.0875 -0.1742">
   82 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
   83 |         <joint name="p_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
   84 |         <geom class="visual" mesh="left_hip_yaw_link" />
   85 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
   86 |         <body name="p_left_hip_roll_link" pos="0.039468 0 0">
   87 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
   88 |           <joint name="p_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
   89 |           <geom class="visual" mesh="left_hip_roll_link" />
   90 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
   91 |           <body name="p_left_hip_pitch_link" pos="0 0.11536 0">
   92 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
   93 |             <joint name="p_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
   94 |             <geom class="visual" mesh="left_hip_pitch_link" />
   95 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
   96 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
   97 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
   98 |             <body name="p_left_knee_link" pos="0 0 -0.4">
   99 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  100 |               <joint name="p_left_knee" axis="0 1 0" range="-0.26 2.05" />
  101 |               <geom class="visual" mesh="left_knee_link" />
  102 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  103 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  104 |               <body name="p_left_ankle_link" pos="0 0 -0.4">
  105 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  106 |                 <joint name="p_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  107 |                 <geom class="visual" mesh="left_ankle_link" />
  108 |                 <geom class="foot1" />
  109 |                 <geom class="foot2" />
  110 |                 <geom class="foot3" />
  111 |               </body>
  112 |             </body>
  113 |           </body>
  114 |         </body>
  115 |       </body>
  116 |       <body name="p_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  117 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  118 |         <joint name="p_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  119 |         <geom class="visual" mesh="right_hip_yaw_link" />
  120 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  121 |         <body name="p_right_hip_roll_link" pos="0.039468 0 0">
  122 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0729075 0.701867 0.0438242 0.70721" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  123 |           <joint name="p_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  124 |           <geom class="visual" mesh="right_hip_roll_link" />
  125 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  126 |           <body name="p_right_hip_pitch_link" pos="0 -0.11536 0">
  127 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  128 |             <joint name="p_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  129 |             <geom class="visual" mesh="right_hip_pitch_link" />
  130 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  131 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  132 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  133 |             <body name="p_right_knee_link" pos="0 0 -0.4">
  134 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  135 |               <joint name="p_right_knee" axis="0 1 0" range="-0.26 2.05" />
  136 |               <geom class="visual" mesh="right_knee_link" />
  137 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  138 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  139 |               <body name="p_right_ankle_link" pos="0 0 -0.4">
  140 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  141 |                 <joint name="p_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  142 |                 <geom class="visual" mesh="right_ankle_link" />
  143 |                 <geom class="foot1" />
  144 |                 <geom class="foot2" />
  145 |                 <geom class="foot3" />
  146 |               </body>
  147 |             </body>
  148 |           </body>
  149 |         </body>
  150 |       </body>
  151 |       <body name="p_torso_link" pos="0 0 0">
  152 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00127082 -0.0043492 0.00149972" mass="17.789" diaginertia="0.487014 0.409608 0.127815" />
  153 |         <joint name="p_torso" axis="0 0 1" range="-2.35 2.35" />
  154 |         <geom class="visual" mesh="torso_link" />
  155 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.15 0.04 0 0.15" />
  156 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.25 0.04 0 0.25" />
  157 |         <geom class="collision" type="capsule" size="0.06" fromto="-0.04 0 0.35 0.04 0 0.35" />
  158 |         <geom class="visual" mesh="logo_link" />
  159 |         <body name="p_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  160 |           <inertial pos="-0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  161 |           <joint name="p_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  162 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  163 |           <body name="p_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  164 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  165 |             <joint name="p_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  166 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  167 |             <geom name="p_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.07 -0.02 0 0.01 0.008" />
  168 |             <body name="p_left_shoulder_yaw_link" pos="0 0 -0.1343">
  169 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  170 |               <joint name="p_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  171 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  172 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  173 |               <body name="p_left_elbow_link" pos="0.0185 0 -0.198">
  174 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.684102 -0.0853116 -0.0765232 0.720327" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  175 |                 <joint name="p_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  176 |                 <geom class="visual" mesh="left_elbow_link" />
  177 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  178 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  179 |               </body>
  180 |             </body>
  181 |           </body>
  182 |         </body>
  183 |         <body name="p_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  184 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  185 |           <joint name="p_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  186 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  187 |           <body name="p_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  188 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  189 |             <joint name="p_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  190 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  191 |             <geom name="p_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  192 |             <body name="p_right_shoulder_yaw_link" pos="0 0 -0.1343">
  193 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  194 |               <joint name="p_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  195 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  196 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  197 |               <body name="p_right_elbow_link" pos="0.0185 0 -0.198">
  198 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  199 |                 <joint name="p_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  200 |                 <geom class="visual" mesh="right_elbow_link" />
  201 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  202 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  203 |                 <site name="p_pitcher_hand_site" pos="0.30 0 -0.015" size="0.01" />
  204 |               </body>
  205 |             </body>
  206 |           </body>
  207 |         </body>
  208 |       </body>
  209 |     </body>
  210 |     <body name="b_pelvis" pos="-0.90 0.00 0.95" childclass="h1">
  211 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
  212 |       <geom class="visual" mesh="pelvis" />
  213 |       <body name="b_left_hip_yaw_link" pos="0 0.0875 -0.1742">
  214 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  215 |         <joint name="b_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  216 |         <geom class="visual" mesh="left_hip_yaw_link" />
  217 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  218 |         <body name="b_left_hip_roll_link" pos="0.039468 0 0">
  219 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  220 |           <joint name="b_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  221 |           <geom class="visual" mesh="left_hip_roll_link" />
  222 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
  223 |           <body name="b_left_hip_pitch_link" pos="0 0.11536 0">
  224 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  225 |             <joint name="b_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  226 |             <geom class="visual" mesh="left_hip_pitch_link" />
  227 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  228 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  229 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
  230 |             <body name="b_left_knee_link" pos="0 0 -0.4">
  231 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  232 |               <joint name="b_left_knee" axis="0 1 0" range="-0.26 2.05" />
  233 |               <geom class="visual" mesh="left_knee_link" />
  234 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  235 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  236 |               <body name="b_left_ankle_link" pos="0 0 -0.4">
  237 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  238 |                 <joint name="b_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  239 |                 <geom class="visual" mesh="left_ankle_link" />
  240 |                 <geom class="foot1" />
  241 |                 <geom class="foot2" />
  242 |                 <geom class="foot3" />
  243 |               </body>
  244 |             </body>
  245 |           </body>
  246 |         </body>
  247 |       </body>
  248 |       <body name="b_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  249 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  250 |         <joint name="b_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  251 |         <geom class="visual" mesh="right_hip_yaw_link" />
  252 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  253 |         <body name="b_right_hip_roll_link" pos="0.039468 0 0">
  254 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0438242 0.70721 0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  255 |           <joint name="b_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  256 |           <geom class="visual" mesh="right_hip_roll_link" />
  257 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  258 |           <body name="b_right_hip_pitch_link" pos="0 -0.11536 0">
  259 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  260 |             <joint name="b_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  261 |             <geom class="visual" mesh="right_hip_pitch_link" />
  262 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  263 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  264 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  265 |             <body name="b_right_knee_link" pos="0 0 -0.4">
  266 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  267 |               <joint name="b_right_knee" axis="0 1 0" range="-0.26 2.05" />
  268 |               <geom class="visual" mesh="right_knee_link" />
  269 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  270 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  271 |               <body name="b_right_ankle_link" pos="0 0 -0.4">
  272 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  273 |                 <joint name="b_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  274 |                 <geom class="visual" mesh="right_ankle_link" />
  275 |                 <geom class="foot1" />
  276 |                 <geom class="foot2" />
  277 |                 <geom class="foot3" />
  278 |               </body>
  279 |             </body>
  280 |           </body>
  281 |         </body>
  282 |       </body>
  283 |       <body name="b_torso_link">
  284 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00130808 -0.00282289 -0.00349105" mass="17.789" diaginertia="0.487315 0.409628 0.127837" />
  285 |         <joint name="b_torso" axis="0 0 1" range="-2.35 2.35" />
  286 |         <geom class="visual" mesh="torso_link" />
  287 |         <geom class="visual" material="white" mesh="logo_link" />
  288 |         <geom name="b_head" class="collision" type="capsule" size="0.06" fromto="0.05 0 0.68 0.05 0 0.6" />
  289 |         <geom name="b_helmet" class="collision" type="sphere" size="0.073" pos="0.045 0 0.68" />
  290 |         <geom name="b_torso" class="collision" type="box" size="0.07 0.1 0.22" pos="0 0 0.25" />
  291 |         <geom name="b_hip" class="collision" type="capsule" size="0.05" fromto="0 -0.1 -0.05 0 0.1 -0.05" />
  292 |         <site name="b_imu" pos="-0.04452 -0.01891 0.27756" />
  293 |         <body name="b_left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  294 |           <inertial pos="0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 -0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  295 |           <joint name="b_left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  296 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  297 |           <body name="b_left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  298 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  299 |             <joint name="b_left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  300 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  301 |             <geom name="b_left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  302 |             <body name="b_left_shoulder_yaw_link" pos="0 0 -0.1343">
  303 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  304 |               <joint name="b_left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  305 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  306 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  307 |               <body name="b_left_elbow_link" pos="0.0185 0 -0.198">
  308 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  309 |                 <joint name="b_left_elbow" axis="0 1 0" range="-1.25 2.61" />
  310 |                 <geom class="visual" mesh="left_elbow_link" />
  311 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  312 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  313 |                 <site name="b_l_hand_grip" pos="0.30 0 0" size="0.01" />
  314 |               </body>
  315 |             </body>
  316 |           </body>
  317 |         </body>
  318 |         <body name="b_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  319 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  320 |           <joint name="b_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  321 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  322 |           <body name="b_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  323 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  324 |             <joint name="b_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  325 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  326 |             <geom name="b_right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  327 |             <body name="b_right_shoulder_yaw_link" pos="0 0 -0.1343">
  328 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  329 |               <joint name="b_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  330 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  331 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  332 |               <body name="b_right_elbow_link" pos="0.0185 0 -0.198">
  333 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  334 |                 <joint name="b_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  335 |                 <geom class="visual" mesh="right_elbow_link" />
  336 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  337 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  338 |                 <body name="b_bat" pos="0.30 0 0" quat="0.7071068 0 0.7071068 0">
  339 |                   <geom name="bat_barrel" type="cylinder" size="0.032 0.45" pos="0 0 0.45" material="bat_mat" mass="0.90" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" />
  340 |                   <site name="bat_knob" pos="0 0 0.02" size="0.01" />
  341 |                   <site name="bat_grip_left" pos="0 0 0.08" size="0.01" />
  342 |                   <site name="bat_sweet_spot" pos="0 0 0.73" size="0.015" material="sweet_spot_mat" />
  343 |                   <site name="bat_tip" pos="0 0 0.90" size="0.01" />
  344 |                 </body>
  345 |               </body>
  346 |             </body>
  347 |           </body>
  348 |         </body>
  349 |       </body>
  350 |     </body>
  351 |     <body name="baseball" pos="0 10.0 1.2">
  352 |       <freejoint name="ball_joint" />
  353 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" />
  354 |       <site name="ball_site" pos="0 0 0" size="0.01" />
  355 |     </body>
  356 |   </worldbody>
  357 |   <contact>
  358 |     <exclude body1="p_torso_link" body2="p_right_shoulder_roll_link" />
  359 |     <exclude body1="b_torso_link" body2="b_right_shoulder_roll_link" />
  360 |     <exclude body1="baseball" body2="p_right_elbow_link" />
  361 |     <pair geom1="bat_barrel" geom2="ball_geom" solref="0.0015 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.4 0.01 0.001" />
  362 |   </contact>
  363 |   <actuator>
  364 |     <motor class="h1" name="p_left_hip_yaw" joint="p_left_hip_yaw" ctrlrange="-200 200" />
  365 |     <motor class="h1" name="p_left_hip_roll" joint="p_left_hip_roll" ctrlrange="-200 200" />
  366 |     <motor class="h1" name="p_left_hip_pitch" joint="p_left_hip_pitch" ctrlrange="-200 200" />
  367 |     <motor class="h1" name="p_left_knee" joint="p_left_knee" ctrlrange="-300 300" />
  368 |     <motor class="h1" name="p_left_ankle" joint="p_left_ankle" ctrlrange="-40 40" />
  369 |     <motor class="h1" name="p_right_hip_yaw" joint="p_right_hip_yaw" ctrlrange="-200 200" />
  370 |     <motor class="h1" name="p_right_hip_roll" joint="p_right_hip_roll" ctrlrange="-200 200" />
  371 |     <motor class="h1" name="p_right_hip_pitch" joint="p_right_hip_pitch" ctrlrange="-200 200" />
  372 |     <motor class="h1" name="p_right_knee" joint="p_right_knee" ctrlrange="-300 300" />
  373 |     <motor class="h1" name="p_right_ankle" joint="p_right_ankle" ctrlrange="-40 40" />
  374 |     <motor class="h1" name="p_torso" joint="p_torso" ctrlrange="-200 200" />
  375 |     <motor class="h1" name="p_left_shoulder_pitch" joint="p_left_shoulder_pitch" ctrlrange="-40 40" />
  376 |     <motor class="h1" name="p_left_shoulder_roll" joint="p_left_shoulder_roll" ctrlrange="-40 40" />
  377 |     <motor class="h1" name="p_left_shoulder_yaw" joint="p_left_shoulder_yaw" ctrlrange="-18 18" />
  378 |     <motor class="h1" name="p_left_elbow" joint="p_left_elbow" ctrlrange="-18 18" />
  379 |     <motor class="h1" name="p_right_shoulder_pitch" joint="p_right_shoulder_pitch" ctrlrange="-40 40" />
  380 |     <motor class="h1" name="p_right_shoulder_roll" joint="p_right_shoulder_roll" ctrlrange="-40 40" />
  381 |     <motor class="h1" name="p_right_shoulder_yaw" joint="p_right_shoulder_yaw" ctrlrange="-18 18" />
  382 |     <motor class="h1" name="p_right_elbow" joint="p_right_elbow" ctrlrange="-18 18" />
  383 |     <motor class="h1" name="b_left_hip_yaw" joint="b_left_hip_yaw" ctrlrange="-200 200" />
  384 |     <motor class="h1" name="b_left_hip_roll" joint="b_left_hip_roll" ctrlrange="-200 200" />
  385 |     <motor class="h1" name="b_left_hip_pitch" joint="b_left_hip_pitch" ctrlrange="-200 200" />
  386 |     <motor class="h1" name="b_left_knee" joint="b_left_knee" ctrlrange="-300 300" />
  387 |     <motor class="h1" name="b_left_ankle" joint="b_left_ankle" ctrlrange="-40 40" />
  388 |     <motor class="h1" name="b_right_hip_yaw" joint="b_right_hip_yaw" ctrlrange="-200 200" />
  389 |     <motor class="h1" name="b_right_hip_roll" joint="b_right_hip_roll" ctrlrange="-200 200" />
  390 |     <motor class="h1" name="b_right_hip_pitch" joint="b_right_hip_pitch" ctrlrange="-200 200" />
  391 |     <motor class="h1" name="b_right_knee" joint="b_right_knee" ctrlrange="-300 300" />
  392 |     <motor class="h1" name="b_right_ankle" joint="b_right_ankle" ctrlrange="-40 40" />
  393 |     <motor class="h1" name="b_torso" joint="b_torso" ctrlrange="-200 200" />
  394 |     <motor class="h1" name="b_left_shoulder_pitch" joint="b_left_shoulder_pitch" ctrlrange="-40 40" />
  395 |     <motor class="h1" name="b_left_shoulder_roll" joint="b_left_shoulder_roll" ctrlrange="-40 40" />
  396 |     <motor class="h1" name="b_left_shoulder_yaw" joint="b_left_shoulder_yaw" ctrlrange="-18 18" />
  397 |     <motor class="h1" name="b_left_elbow" joint="b_left_elbow" ctrlrange="-18 18" />
  398 |     <motor class="h1" name="b_right_shoulder_pitch" joint="b_right_shoulder_pitch" ctrlrange="-40 40" />
  399 |     <motor class="h1" name="b_right_shoulder_roll" joint="b_right_shoulder_roll" ctrlrange="-40 40" />
  400 |     <motor class="h1" name="b_right_shoulder_yaw" joint="b_right_shoulder_yaw" ctrlrange="-18 18" />
  401 |     <motor class="h1" name="b_right_elbow" joint="b_right_elbow" ctrlrange="-18 18" />
  402 |   </actuator>
  403 |   <equality>
  404 |     <weld name="p_ball_weld" site1="p_pitcher_hand_site" site2="ball_site" />
  405 |   </equality>
  406 | </mujoco>
````
