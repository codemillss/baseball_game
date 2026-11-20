# baseball/shared_assets/h1_baseball.xml

원본: [shared_assets/h1_baseball.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/shared_assets/h1_baseball.xml)

SHA256: `dbe97cb1638ff3384e53c82a1bb8c820060b6884cc05a53bc8091cfdbfc37008`

전체 217행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <mujoco model="h1">
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
   57 |   <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="512" /><texture name="texplane" type="2d" builtin="checker" rgb1="0.2 0.3 0.4" rgb2="0.1 0.15 0.2" width="512" height="512" /><material name="matplane" reflectance="0.3" texture="texplane" texrepeat="1 1" texuniform="true" /><material name="home_plate_mat" rgba="0.9 0.9 0.9 1" reflectance="0.2" /><material name="ball_mat" rgba="0.98 0.98 0.95 1" reflectance="0.4" /><material name="bat_mat" rgba="0.8 0.6 0.3 1" reflectance="0.3" /></asset>
   58 | 
   59 |   <worldbody>
   60 |     <body name="pelvis" pos="-0.85 0 0.82" childclass="h1">
   61 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.0490211 0.0445821 0.00824619" />
   62 |       <geom class="visual" mesh="pelvis" />
   63 |       <body name="left_hip_yaw_link" pos="0 0.0875 -0.1742">
   64 |         <inertial pos="-0.04923 0.0001 0.0072" quat="0.69699 0.219193 0.233287 0.641667" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
   65 |         <joint name="left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
   66 |         <geom class="visual" mesh="left_hip_yaw_link" />
   67 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
   68 |         <body name="left_hip_roll_link" pos="0.039468 0 0">
   69 |           <inertial pos="-0.0058 -0.00319 -9e-05" quat="0.0438242 0.70721 -0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
   70 |           <joint name="left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
   71 |           <geom class="visual" mesh="left_hip_roll_link" />
   72 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 -0.02 0" />
   73 |           <body name="left_hip_pitch_link" pos="0 0.11536 0">
   74 |             <inertial pos="0.00746 -0.02346 -0.08193" quat="0.979828 0.0513522 -0.0169854 -0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
   75 |             <joint name="left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
   76 |             <geom class="visual" mesh="left_hip_pitch_link" />
   77 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
   78 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
   79 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 -0.07 0" />
   80 |             <body name="left_knee_link" pos="0 0 -0.4">
   81 |               <inertial pos="-0.00136 -0.00512 -0.1384" quat="0.626132 -0.034227 -0.0416277 0.777852" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
   82 |               <joint name="left_knee" axis="0 1 0" range="-0.26 2.05" />
   83 |               <geom class="visual" mesh="left_knee_link" />
   84 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
   85 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
   86 |               <body name="left_ankle_link" pos="0 0 -0.4">
   87 |                 <inertial pos="0.06722 0.00015 -0.04497" quat="0.489101 0.503197 0.565782 0.432972" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
   88 |                 <joint name="left_ankle" axis="0 1 0" range="-0.87 0.52" />
   89 |                 <geom class="visual" mesh="left_ankle_link" />
   90 |                 <geom class="foot1" />
   91 |                 <geom class="foot2" />
   92 |                 <geom class="foot3" />
   93 |               </body>
   94 |             </body>
   95 |           </body>
   96 |         </body>
   97 |       </body>
   98 |       <body name="right_hip_yaw_link" pos="0 -0.0875 -0.1742">
   99 |         <inertial pos="-0.04923 -0.0001 0.0072" quat="0.641667 0.233287 0.219193 0.69699" mass="2.244" diaginertia="0.00304494 0.00296885 0.00189201" />
  100 |         <joint name="right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  101 |         <geom class="visual" mesh="right_hip_yaw_link" />
  102 |         <geom size="0.06 0.035" pos="-0.067 0 0" quat="0.707123 0 0.70709 0" type="cylinder" class="collision" />
  103 |         <body name="right_hip_roll_link" pos="0.039468 0 0">
  104 |           <inertial pos="-0.0058 0.00319 -9e-05" quat="-0.0438242 0.70721 0.0729075 0.701867" mass="2.232" diaginertia="0.00243264 0.00225325 0.00205492" />
  105 |           <joint name="right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  106 |           <geom class="visual" mesh="right_hip_roll_link" />
  107 |           <geom class="collision" type="cylinder" size="0.05 0.03" quat="1 1 0 0" pos="0 0.02 0" />
  108 |           <body name="right_hip_pitch_link" pos="0 -0.11536 0">
  109 |             <inertial pos="0.00746 0.02346 -0.08193" quat="0.979828 -0.0513522 -0.0169854 0.192382" mass="4.152" diaginertia="0.0829503 0.0821457 0.00510909" />
  110 |             <joint name="right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  111 |             <geom class="visual" mesh="right_hip_pitch_link" />
  112 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 -0.02 0 0.02" />
  113 |             <geom class="collision" type="capsule" size="0.03" fromto="0.02 0 -0.4 0.02 0 0.02" />
  114 |             <geom class="collision" type="cylinder" size="0.05 0.02" quat="1 1 0 0" pos="0 0.07 0" />
  115 |             <body name="right_knee_link" pos="0 0 -0.4">
  116 |               <inertial pos="-0.00136 0.00512 -0.1384" quat="0.777852 -0.0416277 -0.034227 0.626132" mass="1.721" diaginertia="0.0125237 0.0123104 0.0019428" />
  117 |               <joint name="right_knee" axis="0 1 0" range="-0.26 2.05" />
  118 |               <geom class="visual" mesh="right_knee_link" />
  119 |               <geom class="collision" type="capsule" size="0.025" fromto="0.02 0 -0.4 0.02 0 0" />
  120 |               <geom class="collision" type="sphere" size="0.05" pos="0 0 -0.115" />
  121 |               <body name="right_ankle_link" pos="0 0 -0.4">
  122 |                 <inertial pos="0.06722 -0.00015 -0.04497" quat="0.432972 0.565782 0.503197 0.489101" mass="0.446" diaginertia="0.00220848 0.00218961 0.000214202" />
  123 |                 <joint name="right_ankle" axis="0 1 0" range="-0.87 0.52" />
  124 |                 <geom class="visual" mesh="right_ankle_link" />
  125 |                 <geom class="foot1" />
  126 |                 <geom class="foot2" />
  127 |                 <geom class="foot3" />
  128 |               </body>
  129 |             </body>
  130 |           </body>
  131 |         </body>
  132 |       </body>
  133 |       <body name="torso_link">
  134 |         <inertial pos="0.000489 0.002797 0.20484" quat="0.999989 -0.00130808 -0.00282289 -0.00349105" mass="17.789" diaginertia="0.487315 0.409628 0.127837" />
  135 |         <joint name="torso" axis="0 0 1" range="-2.35 2.35" />
  136 |         <geom class="visual" mesh="torso_link" />
  137 |         <geom class="visual" material="white" mesh="logo_link" />
  138 |         <geom name="head" class="collision" type="capsule" size="0.06" fromto="0.05 0 0.68 0.05 0 0.6" />
  139 |         <geom name="helmet" class="collision" type="sphere" size="0.073" pos="0.045 0 0.68" />
  140 |         <geom name="torso" class="collision" type="box" size="0.07 0.1 0.22" pos="0 0 0.25" />
  141 |         <geom name="hip" class="collision" type="capsule" size="0.05" fromto="0 -0.1 -0.05 0 0.1 -0.05" />
  142 |         <site name="imu" pos="-0.04452 -0.01891 0.27756" />
  143 |         <body name="left_shoulder_pitch_link" pos="0.0055 0.15535 0.42999" quat="0.976296 0.216438 0 0">
  144 |           <inertial pos="0.005045 0.053657 -0.015715" quat="0.814858 0.579236 -0.0201072 -0.00936488" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  145 |           <joint name="left_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  146 |           <geom class="visual" mesh="left_shoulder_pitch_link" />
  147 |           <body name="left_shoulder_roll_link" pos="-0.0055 0.0565 -0.0165" quat="0.976296 -0.216438 0 0">
  148 |             <inertial pos="0.000679 0.00115 -0.094076" quat="0.732491 0.00917179 0.0766656 0.676384" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  149 |             <joint name="left_shoulder_roll" axis="1 0 0" range="-0.34 3.11" />
  150 |             <geom class="visual" mesh="left_shoulder_roll_link" />
  151 |             <geom name="left_shoulder" class="collision" type="capsule" size="0.04" fromto="0 0.01 0.008 0 -0.07 -0.02" />
  152 |             <body name="left_shoulder_yaw_link" pos="0 0 -0.1343">
  153 |               <inertial pos="0.01365 0.002767 -0.16266" quat="0.703042 -0.0331229 -0.0473362 0.708798" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  154 |               <joint name="left_shoulder_yaw" axis="0 0 1" range="-1.3 4.45" />
  155 |               <geom class="visual" mesh="left_shoulder_yaw_link" />
  156 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  157 |               <body name="left_elbow_link" pos="0.0185 0 -0.198">
  158 |                 <inertial pos="0.15908 -0.000144 -0.015776" quat="0.0765232 0.720327 0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  159 |                 <joint name="left_elbow" axis="0 1 0" range="-1.25 2.61" />
  160 |                 <geom class="visual" mesh="left_elbow_link" />
  161 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  162 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  163 |               <site name="l_hand_grip" pos="0.3 0 0" size="0.01" /></body>
  164 |             </body>
  165 |           </body>
  166 |         </body>
  167 |         <body name="right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  168 |           <inertial pos="0.005045 -0.053657 -0.015715" quat="0.579236 0.814858 0.00936488 0.0201072" mass="1.033" diaginertia="0.00129936 0.000987113 0.000858198" />
  169 |           <joint name="right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  170 |           <geom class="visual" mesh="right_shoulder_pitch_link" />
  171 |           <body name="right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  172 |             <inertial pos="0.000679 -0.00115 -0.094076" quat="0.676384 0.0766656 0.00917179 0.732491" mass="0.793" diaginertia="0.00170388 0.00158256 0.00100336" />
  173 |             <joint name="right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  174 |             <geom class="visual" mesh="right_shoulder_roll_link" />
  175 |             <geom name="right_shoulder" class="collision" type="capsule" size="0.04" fromto="0 -0.01 0.008 0 0.07 -0.02" />
  176 |             <body name="right_shoulder_yaw_link" pos="0 0 -0.1343">
  177 |               <inertial pos="0.01365 -0.002767 -0.16266" quat="0.708798 -0.0473362 -0.0331229 0.703042" mass="0.839" diaginertia="0.00408038 0.00370367 0.000622687" />
  178 |               <joint name="right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  179 |               <geom class="visual" mesh="right_shoulder_yaw_link" />
  180 |               <geom class="collision" type="capsule" size="0.03" fromto="0 0 0.15 0 0 -0.2" />
  181 |               <body name="right_elbow_link" pos="0.0185 0 -0.198">
  182 |                 <inertial pos="0.15908 0.000144 -0.015776" quat="-0.0765232 0.720327 -0.0853116 0.684102" mass="0.669" diaginertia="0.00601829 0.00600579 0.000408305" />
  183 |                 <joint name="right_elbow" axis="0 1 0" range="-1.25 2.61" />
  184 |                 <geom class="visual" mesh="right_elbow_link" />
  185 |                 <geom class="collision" type="capsule" size="0.025" fromto="0 0 0 0.28 0 -0.015" />
  186 |                 <geom class="collision" type="sphere" size="0.033" pos="0.28 0 -0.015" />
  187 |               <body name="bat" pos="0.3 0 0" quat="0.707 0 0.707 0"><geom name="bat_barrel" type="cylinder" size="0.03 0.45" pos="0 0 0.45" material="bat_mat" mass="0.9" /><site name="bat_grip_left" pos="0 0 0.05" size="0.01" /></body></body>
  188 |             </body>
  189 |           </body>
  190 |         </body>
  191 |       </body>
  192 |     </body>
  193 |   <light directional="true" diffuse="0.8 0.8 0.8" specular="0.2 0.2 0.2" pos="0 0 10" dir="0 0 -1" /><geom name="ground" type="plane" size="30 30 0.1" material="matplane" /><geom name="home_plate" type="box" size="0.22 0.22 0.005" pos="0 0 0.005" material="home_plate_mat" /><geom name="pitcher_mound" type="box" size="0.3 0.1 0.005" pos="0 18.44 0.005" material="home_plate_mat" /><camera name="pitcher_cam" pos="0 20.0 2.0" xyaxes="-1 0 0 0 0 1" fovy="60" /><camera name="batter_cam" pos="-0.85 -0.5 1.7" xyaxes="1 0 0 0 0 1" fovy="90" /><camera name="side_cam" pos="-2.2 -1.8 1.4" xyaxes="0.74 -0.67 0 0.15 0.16 0.97" fovy="45" /><camera name="front_cam" pos="-0.4 2.8 1.1" xyaxes="-1 0 0 0 -0.15 0.98" fovy="45" /><body name="baseball" pos="0 15 1.5"><freejoint name="ball_joint" /><geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" /></body></worldbody>
  194 | 
  195 |   <contact>
  196 |     <exclude body1="torso_link" body2="left_shoulder_roll_link" />
  197 |     <exclude body1="torso_link" body2="right_shoulder_roll_link" />
  198 |   </contact>
  199 | 
  200 |   <actuator>
  201 |     <motor class="h1" name="left_hip_yaw" joint="left_hip_yaw" ctrlrange="-200 200" />
  202 |     <motor class="h1" name="left_hip_roll" joint="left_hip_roll" ctrlrange="-200 200" />
  203 |     <motor class="h1" name="left_hip_pitch" joint="left_hip_pitch" ctrlrange="-200 200" />
  204 |     <motor class="h1" name="left_knee" joint="left_knee" ctrlrange="-300 300" />
  205 |     <motor class="h1" name="left_ankle" joint="left_ankle" ctrlrange="-40 40" />
  206 |     <motor class="h1" name="right_hip_yaw" joint="right_hip_yaw" ctrlrange="-200 200" />
  207 |     <motor class="h1" name="right_hip_roll" joint="right_hip_roll" ctrlrange="-200 200" />
  208 |     <motor class="h1" name="right_hip_pitch" joint="right_hip_pitch" ctrlrange="-200 200" />
  209 |     <motor class="h1" name="right_knee" joint="right_knee" ctrlrange="-300 300" />
  210 |     <motor class="h1" name="right_ankle" joint="right_ankle" ctrlrange="-40 40" />
  211 |     <motor class="h1" name="torso" joint="torso" ctrlrange="-200 200" />
  212 |     <motor class="h1" name="right_shoulder_pitch" joint="right_shoulder_pitch" ctrlrange="-40 40" />
  213 |     <motor class="h1" name="right_shoulder_roll" joint="right_shoulder_roll" ctrlrange="-40 40" />
  214 |     <motor class="h1" name="right_shoulder_yaw" joint="right_shoulder_yaw" ctrlrange="-18 18" />
  215 |     <motor class="h1" name="right_elbow" joint="right_elbow" ctrlrange="-18 18" />
  216 |   </actuator>
  217 | <equality><connect name="left_hand_to_bat" site1="l_hand_grip" site2="bat_grip_left" /></equality></mujoco>
````
