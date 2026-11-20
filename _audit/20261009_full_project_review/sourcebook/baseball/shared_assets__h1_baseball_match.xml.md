# baseball/shared_assets/h1_baseball_match.xml

원본: [shared_assets/h1_baseball_match.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/shared_assets/h1_baseball_match.xml)

SHA256: `7267f7ed66d77c93b1e2825c3953ced1693520cb9db9a2bd723165015b3fcfba`

전체 282행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <mujoco model="h1_baseball_match">
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
   35 |     <material name="pitcher_mat" rgba="0.15 0.3 0.6 1" />
   36 |     <material name="batter_mat" rgba="0.7 0.2 0.2 1" />
   37 | 
   38 |     <mesh file="pelvis.stl" />
   39 |     <mesh file="left_hip_yaw_link.stl" />
   40 |     <mesh file="left_hip_roll_link.stl" />
   41 |     <mesh file="left_hip_pitch_link.stl" />
   42 |     <mesh file="left_knee_link.stl" />
   43 |     <mesh file="left_ankle_link.stl" />
   44 |     <mesh file="right_hip_yaw_link.stl" />
   45 |     <mesh file="right_hip_roll_link.stl" />
   46 |     <mesh file="right_hip_pitch_link.stl" />
   47 |     <mesh file="right_knee_link.stl" />
   48 |     <mesh file="right_ankle_link.stl" />
   49 |     <mesh file="torso_link.stl" />
   50 |     <mesh file="left_shoulder_pitch_link.stl" />
   51 |     <mesh file="left_shoulder_roll_link.stl" />
   52 |     <mesh file="left_shoulder_yaw_link.stl" />
   53 |     <mesh file="left_elbow_link.stl" />
   54 |     <mesh file="right_shoulder_pitch_link.stl" />
   55 |     <mesh file="right_shoulder_roll_link.stl" />
   56 |     <mesh file="right_shoulder_yaw_link.stl" />
   57 |     <mesh file="right_elbow_link.stl" />
   58 |     <mesh file="logo_link.stl" />
   59 |     
   60 |     <texture type="skybox" builtin="gradient" rgb1="0.4 0.6 0.9" rgb2="0.1 0.2 0.3" width="512" height="512" />
   61 |     
   62 |     <texture name="grass_tex" type="2d" file="../data/textures/grass.png" />
   63 |     <material name="grass_mat" texture="grass_tex" texrepeat="25 25" texuniform="true" reflectance="0.05" />
   64 |     
   65 |     <texture name="dirt_tex" type="2d" file="../data/textures/dirt.png" />
   66 |     <material name="dirt_mat" texture="dirt_tex" texrepeat="8 8" texuniform="true" reflectance="0.02" />
   67 |     
   68 |     <material name="base_mat" rgba="0.95 0.95 0.95 1" reflectance="0.3" />
   69 |     <material name="foul_line_mat" rgba="0.95 0.95 0.95 1" />
   70 |     <material name="wall_mat" rgba="0.08 0.2 0.12 1" reflectance="0.1" />
   71 |     
   72 |     <material name="home_plate_mat" rgba="0.9 0.9 0.9 1" reflectance="0.2" />
   73 |     <material name="ball_mat" rgba="0.98 0.98 0.95 1" reflectance="0.4" />
   74 |     <material name="bat_mat" rgba="0.8 0.6 0.3 1" reflectance="0.3" />
   75 |     <material name="target_zone_mat" rgba="0.2 0.8 0.2 0.3" />
   76 |   </asset>
   77 |   <worldbody>
   78 |     <light directional="true" diffuse="0.9 0.9 0.8" specular="0.3 0.3 0.3" pos="0 -10 20" dir="0 1 -1.5" />
   79 |     
   80 |     
   81 |     <geom name="grass_field" type="plane" size="60 60 0.1" pos="0 40 0" material="grass_mat" />
   82 |     
   83 |     
   84 |     <geom name="dirt_infield" type="cylinder" size="18 0.005" pos="0 14.0 0.005" material="dirt_mat" />
   85 |     <geom name="dirt_infield_base" type="box" size="12.7 12.7 0.005" pos="0 12.7 0.005" quat="0.707 0 0 0.707" material="dirt_mat" />
   86 |     
   87 |     
   88 |     
   89 |     
   90 |     <geom name="first_base" type="box" size="0.2 0.2 0.025" pos="19.4 19.4 0.025" quat="0.9238 0 0 0.3826" material="base_mat" />
   91 |     
   92 |     <geom name="second_base" type="box" size="0.2 0.2 0.025" pos="0 38.8 0.025" quat="0.707 0 0 0.707" material="base_mat" />
   93 |     
   94 |     <geom name="third_base" type="box" size="0.2 0.2 0.025" pos="-19.4 19.4 0.025" quat="0.9238 0 0 -0.3826" material="base_mat" />
   95 |     
   96 |     
   97 |     <geom name="home_plate" type="box" size="0.22 0.22 0.006" pos="0 0 0.006" quat="0.707 0 0 0.707" material="home_plate_mat" />
   98 |     
   99 |     <geom name="pitcher_mound" type="cylinder" size="1.5 0.08" pos="0 10.0 0.0" material="dirt_mat" />
  100 |     <geom name="pitcher_plate" type="box" size="0.3 0.08 0.005" pos="0 10.0 0.085" material="home_plate_mat" />
  101 | 
  102 |     
  103 |     <geom name="rf_foul_line" type="box" size="0.05 40 0.008" pos="28.28 28.28 0.008" quat="0.9238 0 0 0.3826" material="foul_line_mat" />
  104 |     <geom name="lf_foul_line" type="box" size="0.05 40 0.008" pos="-28.28 28.28 0.008" quat="0.9238 0 0 -0.3826" material="foul_line_mat" />
  105 | 
  106 |     
  107 |     
  108 |     <geom name="lf_wall" type="box" size="25 0.5 2.5" pos="-25 60 2.5" quat="0.980 0 0 -0.195" material="wall_mat" />
  109 |     
  110 |     <geom name="cf_wall" type="box" size="20 0.5 2.5" pos="0 65 2.5" material="wall_mat" />
  111 |     
  112 |     <geom name="rf_wall" type="box" size="25 0.5 2.5" pos="25 60 2.5" quat="0.980 0 0 0.195" material="wall_mat" />
  113 | 
  114 |     <site name="strike_zone_target" type="box" size="0.20 0.02 0.27" pos="0 0.0 0.815" material="target_zone_mat" />
  115 | 
  116 |     
  117 |     <camera name="broadcast_cam" pos="-5.0 5.0 3.0" xyaxes="0.89 -0.45 0 0.22 0.44 0.87" fovy="55" />
  118 |     <camera name="batter_focus_cam" pos="-2.2 -1.8 1.4" xyaxes="0.74 -0.67 0 0.15 0.16 0.97" fovy="48" />
  119 |     <camera name="pitcher_focus_cam" pos="1.5 12.5 2.0" xyaxes="-0.8 -0.6 0 0.3 -0.4 0.9" fovy="48" />
  120 |     <camera name="catcher_cam" pos="0 -2.5 1.5" xyaxes="1 0 0 0 0.2 0.98" fovy="52" />
  121 | 
  122 |     
  123 |     <body name="pitcher_pelvis" pos="0 10.0 0.82" quat="0.7071068 0 0 -0.7071068" childclass="h1">
  124 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.049 0.044 0.008" />
  125 |       <geom class="visual" mesh="pelvis" material="pitcher_mat" />
  126 |       
  127 |       <body name="p_left_hip_yaw_link" pos="0 0.0875 -0.1742">
  128 |         <joint name="p_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  129 |         <geom class="visual" mesh="left_hip_yaw_link" material="pitcher_mat" />
  130 |         <body name="p_left_hip_roll_link" pos="0.039468 0 0">
  131 |           <joint name="p_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  132 |           <geom class="visual" mesh="left_hip_roll_link" material="pitcher_mat" />
  133 |           <body name="p_left_hip_pitch_link" pos="0 0.11536 0">
  134 |             <joint name="p_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  135 |             <geom class="visual" mesh="left_hip_pitch_link" material="pitcher_mat" />
  136 |             <body name="p_left_knee_link" pos="0 0 -0.4">
  137 |               <joint name="p_left_knee" axis="0 1 0" range="-0.26 2.05" />
  138 |               <geom class="visual" mesh="left_knee_link" material="pitcher_mat" />
  139 |               <body name="p_left_ankle_link" pos="0 0 -0.4">
  140 |                 <joint name="p_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  141 |                 <geom class="visual" mesh="left_ankle_link" material="pitcher_mat" />
  142 |                 <geom class="foot1" /><geom class="foot2" /><geom class="foot3" />
  143 |               </body>
  144 |             </body>
  145 |           </body>
  146 |         </body>
  147 |       </body>
  148 | 
  149 |       <body name="p_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  150 |         <joint name="p_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  151 |         <geom class="visual" mesh="right_hip_yaw_link" material="pitcher_mat" />
  152 |         <body name="p_right_hip_roll_link" pos="0.039468 0 0">
  153 |           <joint name="p_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  154 |           <geom class="visual" mesh="right_hip_roll_link" material="pitcher_mat" />
  155 |           <body name="p_right_hip_pitch_link" pos="0 -0.11536 0">
  156 |             <joint name="p_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  157 |             <geom class="visual" mesh="right_hip_pitch_link" material="pitcher_mat" />
  158 |             <body name="p_right_knee_link" pos="0 0 -0.4">
  159 |               <joint name="p_right_knee" axis="0 1 0" range="-0.26 2.05" />
  160 |               <geom class="visual" mesh="right_knee_link" material="pitcher_mat" />
  161 |               <body name="p_right_ankle_link" pos="0 0 -0.4">
  162 |                 <joint name="p_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  163 |                 <geom class="visual" mesh="right_ankle_link" material="pitcher_mat" />
  164 |                 <geom class="foot1" /><geom class="foot2" /><geom class="foot3" />
  165 |               </body>
  166 |             </body>
  167 |           </body>
  168 |         </body>
  169 |       </body>
  170 | 
  171 |       <body name="p_torso_link">
  172 |         <joint name="p_torso" axis="0 0 1" range="-2.35 2.35" />
  173 |         <geom class="visual" mesh="torso_link" material="pitcher_mat" />
  174 |         <geom class="visual" material="white" mesh="logo_link" />
  175 |         <body name="p_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  176 |           <joint name="p_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  177 |           <geom class="visual" mesh="right_shoulder_pitch_link" material="pitcher_mat" />
  178 |           <body name="p_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  179 |             <joint name="p_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  180 |             <geom class="visual" mesh="right_shoulder_roll_link" material="pitcher_mat" />
  181 |             <body name="p_right_shoulder_yaw_link" pos="0 0 -0.1343">
  182 |               <joint name="p_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  183 |               <geom class="visual" mesh="right_shoulder_yaw_link" material="pitcher_mat" />
  184 |               <body name="p_right_elbow_link" pos="0.0185 0 -0.198">
  185 |                 <joint name="p_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  186 |                 <geom class="visual" mesh="right_elbow_link" material="pitcher_mat" />
  187 |                 <site name="pitcher_hand_site" pos="0.30 0 -0.015" size="0.01" />
  188 |               </body>
  189 |             </body>
  190 |           </body>
  191 |         </body>
  192 |       </body>
  193 |     </body>
  194 | 
  195 |     
  196 |     <body name="batter_pelvis" pos="-0.70 -0.45 0.82" childclass="h1">
  197 |       <inertial pos="-0.0002 4e-05 -0.04522" quat="0.498303 0.499454 -0.500496 0.501741" mass="5.39" diaginertia="0.049 0.044 0.008" />
  198 |       <geom class="visual" mesh="pelvis" material="batter_mat" />
  199 |       
  200 |       <body name="b_left_hip_yaw_link" pos="0 0.0875 -0.1742">
  201 |         <joint name="b_left_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  202 |         <geom class="visual" mesh="left_hip_yaw_link" material="batter_mat" />
  203 |         <body name="b_left_hip_roll_link" pos="0.039468 0 0">
  204 |           <joint name="b_left_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  205 |           <geom class="visual" mesh="left_hip_roll_link" material="batter_mat" />
  206 |           <body name="b_left_hip_pitch_link" pos="0 0.11536 0">
  207 |             <joint name="b_left_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  208 |             <geom class="visual" mesh="left_hip_pitch_link" material="batter_mat" />
  209 |             <body name="b_left_knee_link" pos="0 0 -0.4">
  210 |               <joint name="b_left_knee" axis="0 1 0" range="-0.26 2.05" />
  211 |               <geom class="visual" mesh="left_knee_link" material="batter_mat" />
  212 |               <body name="b_left_ankle_link" pos="0 0 -0.4">
  213 |                 <joint name="b_left_ankle" axis="0 1 0" range="-0.87 0.52" />
  214 |                 <geom class="visual" mesh="left_ankle_link" material="batter_mat" />
  215 |                 <geom class="foot1" /><geom class="foot2" /><geom class="foot3" />
  216 |               </body>
  217 |             </body>
  218 |           </body>
  219 |         </body>
  220 |       </body>
  221 | 
  222 |       <body name="b_right_hip_yaw_link" pos="0 -0.0875 -0.1742">
  223 |         <joint name="b_right_hip_yaw" axis="0 0 1" range="-0.43 0.43" />
  224 |         <geom class="visual" mesh="right_hip_yaw_link" material="batter_mat" />
  225 |         <body name="b_right_hip_roll_link" pos="0.039468 0 0">
  226 |           <joint name="b_right_hip_roll" axis="1 0 0" range="-0.43 0.43" />
  227 |           <geom class="visual" mesh="right_hip_roll_link" material="batter_mat" />
  228 |           <body name="b_right_hip_pitch_link" pos="0 -0.11536 0">
  229 |             <joint name="b_right_hip_pitch" axis="0 1 0" range="-1.57 1.57" />
  230 |             <geom class="visual" mesh="right_hip_pitch_link" material="batter_mat" />
  231 |             <body name="b_right_knee_link" pos="0 0 -0.4">
  232 |               <joint name="b_right_knee" axis="0 1 0" range="-0.26 2.05" />
  233 |               <geom class="visual" mesh="right_knee_link" material="batter_mat" />
  234 |               <body name="b_right_ankle_link" pos="0 0 -0.4">
  235 |                 <joint name="b_right_ankle" axis="0 1 0" range="-0.87 0.52" />
  236 |                 <geom class="visual" mesh="right_ankle_link" material="batter_mat" />
  237 |                 <geom class="foot1" /><geom class="foot2" /><geom class="foot3" />
  238 |               </body>
  239 |             </body>
  240 |           </body>
  241 |         </body>
  242 |       </body>
  243 | 
  244 |       <body name="b_torso_link">
  245 |         <joint name="b_torso" axis="0 0 1" range="-2.35 2.35" />
  246 |         <geom class="visual" mesh="torso_link" material="batter_mat" />
  247 |         <geom class="visual" material="white" mesh="logo_link" />
  248 |         <body name="b_right_shoulder_pitch_link" pos="0.0055 -0.15535 0.42999" quat="0.976296 -0.216438 0 0">
  249 |           <joint name="b_right_shoulder_pitch" axis="0 1 0" range="-2.87 2.87" />
  250 |           <geom class="visual" mesh="right_shoulder_pitch_link" material="batter_mat" />
  251 |           <body name="b_right_shoulder_roll_link" pos="-0.0055 -0.0565 -0.0165" quat="0.976296 0.216438 0 0">
  252 |             <joint name="b_right_shoulder_roll" axis="1 0 0" range="-3.11 0.34" />
  253 |             <geom class="visual" mesh="right_shoulder_roll_link" material="batter_mat" />
  254 |             <body name="b_right_shoulder_yaw_link" pos="0 0 -0.1343">
  255 |               <joint name="b_right_shoulder_yaw" axis="0 0 1" range="-4.45 1.3" />
  256 |               <geom class="visual" mesh="right_shoulder_yaw_link" material="batter_mat" />
  257 |               <body name="b_right_elbow_link" pos="0.0185 0 -0.198">
  258 |                 <joint name="b_right_elbow" axis="0 1 0" range="-1.25 2.61" />
  259 |                 <geom class="visual" mesh="right_elbow_link" material="batter_mat" />
  260 |                 
  261 |                 <body name="bat" pos="0.3 0 0" quat="0.707 0 0.707 0">
  262 |                   <geom name="bat_barrel" type="cylinder" size="0.035 0.45" pos="0 0 0.45" material="bat_mat" mass="0.9" />
  263 |                 </body>
  264 |               </body>
  265 |             </body>
  266 |           </body>
  267 |         </body>
  268 |       </body>
  269 |     </body>
  270 | 
  271 |     
  272 |     <body name="baseball" pos="0 10.0 1.2">
  273 |       <freejoint name="ball_joint" />
  274 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" />
  275 |       <site name="ball_site" pos="0 0 0" size="0.01" />
  276 |     </body>
  277 |   <site name="strike_zone" type="box" size="0.215 0.215 0.3" pos="0 0 0.8" rgba="0 1 0 0.2" /><geom name="foul_line_1b" type="cylinder" size="0.05 40" pos="28.28 28.28 0.01" xyaxes="-0.707 0.707 0 0 0 1" rgba="1 1 1 1" /><geom name="foul_line_3b" type="cylinder" size="0.05 40" pos="-28.28 28.28 0.01" xyaxes="0.707 0.707 0 0 0 1" rgba="1 1 1 1" /></worldbody>
  278 | 
  279 |   <equality>
  280 |     <weld name="pitcher_ball_weld" site1="pitcher_hand_site" site2="ball_site" />
  281 |   </equality>
  282 | </mujoco>
````
