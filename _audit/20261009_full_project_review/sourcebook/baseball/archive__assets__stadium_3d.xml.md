# baseball/archive/assets/stadium_3d.xml

원본: [archive/assets/stadium_3d.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/assets/stadium_3d.xml)

SHA256: `a46ed2bddaa70aa101a7cc2d42f0487771073db52b634484a3333b9a12b96914`

전체 274행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <mujoco model="stadium_3d_baseball_pro">
    2 |   <compiler angle="degree" coordinate="local" inertiafromgeom="true"/>
    3 | 
    4 |   <option gravity="0 0 -9.81" timestep="0.002" integrator="RK4">
    5 |     <flag constraint="enable" energy="enable"/>
    6 |   </option>
    7 | 
    8 |   <default>
    9 |     <joint limited="false" damping="0.01"/>
   10 |     <geom condim="3" friction="0.5 0.1 0.1" solref="0.004 1" solimp="0.9 0.95 0.001" margin="0.001"/>
   11 |   </default>
   12 | 
   13 |   <asset>
   14 |     <!-- Sky & Textures -->
   15 |     <texture name="sky" type="skybox" builtin="gradient" rgb1="0.3 0.55 0.9" rgb2="0.05 0.12 0.3" width="512" height="512"/>
   16 |     <texture name="grass_tex" type="2d" builtin="checker" rgb1="0.12 0.44 0.12" rgb2="0.09 0.36 0.09" width="256" height="256"/>
   17 |     <texture name="dirt_tex" type="2d" builtin="flat" rgb1="0.62 0.38 0.22" width="128" height="128"/>
   18 |     <texture name="wood_tex" type="2d" builtin="flat" rgb1="0.82 0.62 0.32" width="128" height="128"/>
   19 | 
   20 |     <!-- Materials -->
   21 |     <material name="grass" texture="grass_tex" texrepeat="35 35" reflectance="0.05"/>
   22 |     <material name="infield_dirt_mat" texture="dirt_tex" reflectance="0.05"/>
   23 |     <material name="warning_track_mat" rgba="0.68 0.42 0.25 1" reflectance="0.05"/>
   24 |     <material name="wood" texture="wood_tex" reflectance="0.3"/>
   25 |     <material name="ball_mat" rgba="0.98 0.98 0.95 1" reflectance="0.4"/>
   26 |     <material name="plate_mat" rgba="0.95 0.95 0.95 1"/>
   27 |     <material name="foul_line_mat" rgba="1 1 1 0.9"/>
   28 |     <material name="foul_pole_mat" rgba="0.95 0.85 0.1 1"/>
   29 |     <material name="strike_zone_mat" rgba="1 0.15 0.15 0.22"/>
   30 | 
   31 |     <!-- Stadium Materials -->
   32 |     <material name="fence_mat" rgba="0.1 0.25 0.14 1"/>
   33 |     <material name="batters_eye_mat" rgba="0.05 0.12 0.08 1"/> <!-- Dark Matte Centerfield Batter's Eye -->
   34 |     <material name="backstop_mat" rgba="0.15 0.15 0.18 1"/>
   35 | 
   36 |     <!-- Outfield Sponsor Ad Billboards -->
   37 |     <material name="ad_board_samsung" rgba="0.02 0.22 0.65 1"/> <!-- Blue Samsung Ad -->
   38 |     <material name="ad_board_lg" rgba="0.65 0.08 0.2 1"/>      <!-- Red LG Ad -->
   39 |     <material name="ad_board_hyundai" rgba="0.05 0.15 0.4 1"/>  <!-- Navy Hyundai Ad -->
   40 |     <material name="ad_board_kakao" rgba="0.95 0.82 0.05 1"/>   <!-- Yellow Kakao Ad -->
   41 |     <material name="scoreboard_mat" rgba="0.08 0.1 0.14 1"/>   <!-- Giant Centerfield Scoreboard -->
   42 |     <material name="scoreboard_screen" rgba="0.15 0.85 0.35 1"/>
   43 | 
   44 |     <!-- Seating Bleachers & Entry Tunnels -->
   45 |     <material name="seats_blue" rgba="0.15 0.35 0.65 1"/>
   46 |     <material name="seats_navy" rgba="0.08 0.18 0.38 1"/>
   47 |     <material name="seats_red" rgba="0.75 0.18 0.18 1"/>
   48 |     <material name="concrete_concourse" rgba="0.45 0.48 0.52 1"/>
   49 |     <material name="entry_tunnel" rgba="0.08 0.08 0.1 1"/>     <!-- Dark Portal Interior -->
   50 |     <material name="dugout_roof" rgba="0.2 0.22 0.25 1"/>
   51 |   </asset>
   52 | 
   53 |   <worldbody>
   54 |     <!-- Lighting: Realistic Stadium Floodlights -->
   55 |     <light name="light_main" pos="0 25 35" dir="0 -0.5 -1" directional="true" diffuse="0.9 0.9 0.95" specular="0.3 0.3 0.3"/>
   56 |     <light name="light_left" pos="-35 50 30" dir="0.5 -0.5 -1" directional="true" diffuse="0.6 0.6 0.65"/>
   57 |     <light name="light_right" pos="35 50 30" dir="-0.5 -0.5 -1" directional="true" diffuse="0.6 0.6 0.65"/>
   58 | 
   59 |     <!-- Outfield Grass Surface -->
   60 |     <geom name="outfield_grass" type="plane" size="130 130 0.1" pos="0 35 0" material="grass"/>
   61 | 
   62 |     <!-- Infield Pitcher's Mound & Plate -->
   63 |     <geom name="pitcher_mound" type="cylinder" size="2.74 0.25" pos="0 18.44 0" material="infield_dirt_mat"/>
   64 |     <geom name="pitcher_rubber" type="box" size="0.30 0.07 0.02" pos="0 18.44 0.26" material="plate_mat"/>
   65 | 
   66 |     <!-- Infield Diamond Base Paths -->
   67 |     <geom name="path_home_1st" type="box" size="0.9 9.7 0.003" pos="9.7 9.7 0.003" euler="0 0 -45" material="infield_dirt_mat"/>
   68 |     <geom name="path_home_3rd" type="box" size="0.9 9.7 0.003" pos="-9.7 9.7 0.003" euler="0 0 45" material="infield_dirt_mat"/>
   69 |     <geom name="path_1st_2nd" type="box" size="0.9 9.7 0.003" pos="9.7 27.7 0.003" euler="0 0 45" material="infield_dirt_mat"/>
   70 |     <geom name="path_3rd_2nd" type="box" size="0.9 9.7 0.003" pos="-9.7 27.7 0.003" euler="0 0 -45" material="infield_dirt_mat"/>
   71 |     <geom name="infield_skin_dirt" type="cylinder" size="19.0 0.004" pos="0 18.44 0.004" material="infield_dirt_mat"/>
   72 | 
   73 |     <!-- Home Plate & Batter's Boxes -->
   74 |     <geom name="home_plate" type="box" size="0.216 0.216 0.01" pos="0 0 0.005" material="plate_mat"/>
   75 |     <geom name="left_batter_box" type="box" size="0.6 1.2 0.002" pos="-0.85 0.25 0.002" material="infield_dirt_mat"/>
   76 |     <geom name="right_batter_box" type="box" size="0.6 1.2 0.002" pos="0.85 0.25 0.002" material="infield_dirt_mat"/>
   77 |     
   78 |     <!-- Tee-Ball Stand -->
   79 |     <geom name="tee_stand_base" type="cylinder" size="0.1 0.02" pos="0 0 0.02" material="wood" contype="0" conaffinity="0"/>
   80 |     <geom name="tee_stand_pole" type="cylinder" size="0.02 0.48" pos="0 0 0.5" material="wood" contype="0" conaffinity="0"/>
   81 | 
   82 |     <!-- 3D Strike Zone Volume Visualization (Sensor Region) -->
   83 |     <geom name="strike_zone_box" type="box" size="0.216 0.01 0.30" pos="0 0 0.75" material="strike_zone_mat" contype="0" conaffinity="0"/>
   84 | 
   85 |     <!-- Bases (1st, 2nd, 3rd Base Bags) -->
   86 |     <geom name="base_1st" type="box" size="0.19 0.19 0.04" pos="13.72 13.72 0.04" euler="0 0 45" material="plate_mat"/>
   87 |     <geom name="base_2nd" type="box" size="0.19 0.19 0.04" pos="0 27.43 0.04" euler="0 0 45" material="plate_mat"/>
   88 |     <geom name="base_3rd" type="box" size="0.19 0.19 0.04" pos="-13.72 13.72 0.04" euler="0 0 45" material="plate_mat"/>
   89 | 
   90 |     <!-- 1st Base & 3rd Base Dugouts -->
   91 |     <geom name="dugout_1st_roof" type="box" size="1.2 8.0 0.6" pos="16.5 6.0 0.6" material="dugout_roof"/>
   92 |     <geom name="dugout_3rd_roof" type="box" size="1.2 8.0 0.6" pos="-16.5 6.0 0.6" material="dugout_roof"/>
   93 | 
   94 |     <!-- Outfield Warning Track & Curved Wall Fences -->
   95 |     <geom name="warning_track" type="box" size="70 3.5 0.004" pos="0 72 0.004" material="warning_track_mat"/>
   96 |     <geom name="fence_left_wall" type="box" size="26 0.4 2.2" pos="-45 60 2.2" euler="0 0 25" material="fence_mat"/>
   97 |     <geom name="fence_center_wall" type="box" size="22 0.4 2.5" pos="0 75 2.5" material="fence_mat"/>
   98 |     <geom name="fence_right_wall" type="box" size="26 0.4 2.2" pos="45 60 2.2" euler="0 0 -25" material="fence_mat"/>
   99 | 
  100 |     <!-- Outfield Sponsor Ad Billboards Mounted on Wall -->
  101 |     <geom name="ad_samsung" type="box" size="6.0 0.05 1.0" pos="-35 55.2 2.2" euler="0 0 25" material="ad_board_samsung"/>
  102 |     <geom name="ad_lg" type="box" size="6.0 0.05 1.0" pos="-20 62.2 2.2" euler="0 0 25" material="ad_board_lg"/>
  103 |     <geom name="ad_hyundai" type="box" size="6.0 0.05 1.2" pos="0 74.5 2.5" material="ad_board_hyundai"/>
  104 |     <geom name="ad_kakao" type="box" size="6.0 0.05 1.0" pos="20 62.2 2.2" euler="0 0 -25" material="ad_board_kakao"/>
  105 |     <geom name="ad_sponsor_right" type="box" size="6.0 0.05 1.0" pos="35 55.2 2.2" euler="0 0 -25" material="ad_board_samsung"/>
  106 | 
  107 |     <!-- Centerfield Giant Scoreboard & Batter's Eye -->
  108 |     <geom name="batters_eye" type="box" size="12 0.2 6.0" pos="0 77 6.0" material="batters_eye_mat"/>
  109 |     <geom name="jumbo_scoreboard" type="box" size="16 0.5 6.0" pos="0 79 14.0" material="scoreboard_mat"/>
  110 |     <geom name="scoreboard_display" type="box" size="14 0.05 4.5" pos="0 78.7 14.0" material="scoreboard_screen"/>
  111 | 
  112 |     <!-- Yellow Foul Poles (Left & Right Field) -->
  113 |     <geom name="foul_pole_left" type="cylinder" size="0.15 7.0" pos="-58 60 7.0" material="foul_pole_mat"/>
  114 |     <geom name="foul_pole_right" type="cylinder" size="0.15 7.0" pos="58 60 7.0" material="foul_pole_mat"/>
  115 | 
  116 |     <!-- Foul Lines -->
  117 |     <geom name="foul_line_left" type="box" size="0.06 43 0.003" pos="-21.5 21.5 0.003" euler="0 0 -45" material="foul_line_mat" contype="0" conaffinity="0"/>
  118 |     <geom name="foul_line_right" type="box" size="0.06 43 0.003" pos="21.5 21.5 0.003" euler="0 0 45" material="foul_line_mat" contype="0" conaffinity="0"/>
  119 | 
  120 |     <!-- Backstop Wall & Net Behind Home Plate -->
  121 |     <geom name="backstop_wall" type="box" size="12 0.5 2.5" pos="0 -4.0 2.5" material="backstop_mat"/>
  122 | 
  123 |     <!-- Multi-tiered Stadium Seating Stands & Concourse Entry Portals -->
  124 |     <!-- 1st Base Seating Bleachers -->
  125 |     <geom name="stand_1st_lower" type="box" size="10 30 3.0" pos="32 20 3.0" euler="-12 0 -25" material="seats_navy"/>
  126 |     <geom name="stand_1st_upper" type="box" size="12 35 6.0" pos="50 18 10.0" euler="-22 0 -25" material="seats_blue"/>
  127 |     <!-- Entry Portals / Tunnels on 1st Base Stand -->
  128 |     <geom name="portal_1st_1" type="box" size="1.8 1.5 2.2" pos="30 15 2.2" euler="0 0 -25" material="entry_tunnel"/>
  129 |     <geom name="portal_1st_2" type="box" size="1.8 1.5 2.2" pos="34 25 3.2" euler="0 0 -25" material="entry_tunnel"/>
  130 | 
  131 |     <!-- 3rd Base Seating Bleachers -->
  132 |     <geom name="stand_3rd_lower" type="box" size="10 30 3.0" pos="-32 20 3.0" euler="-12 0 25" material="seats_navy"/>
  133 |     <geom name="stand_3rd_upper" type="box" size="12 35 6.0" pos="-50 18 10.0" euler="-22 0 25" material="seats_red"/>
  134 |     <!-- Entry Portals / Tunnels on 3rd Base Stand -->
  135 |     <geom name="portal_3rd_1" type="box" size="1.8 1.5 2.2" pos="-30 15 2.2" euler="0 0 25" material="entry_tunnel"/>
  136 |     <geom name="portal_3rd_2" type="box" size="1.8 1.5 2.2" pos="-34 25 3.2" euler="0 0 25" material="entry_tunnel"/>
  137 | 
  138 |     <!-- Home Plate Grandstand & Press Box -->
  139 |     <geom name="stand_home_grand" type="box" size="18 8.0 5.0" pos="0 -12 6.0" euler="-25 0 0" material="seats_navy"/>
  140 |     <geom name="portal_home_center" type="box" size="2.5 1.5 2.5" pos="0 -10 3.5" material="entry_tunnel"/>
  141 | 
  142 |     <!-- ⚾ 투수 로봇 (8 DOF: 어깨3 + 팔꿈치2 + 손목2 + 릴리즈1) -->
  143 |     <body name="pitcher_base" pos="0 18.44 0.26">
  144 |       <geom type="box" size="0.4 0.3 0.25" mass="80.0" material="seats_navy"/>
  145 |       <body name="pitcher_shoulder" pos="0 0 1.2">
  146 |         <joint name="p_shoulder_pitch" type="hinge" axis="1 0 0" range="-30 210" damping="5.0" armature="0.5"/>
  147 |         <joint name="p_shoulder_yaw" type="hinge" axis="0 0 1" range="-45 45" damping="3.0" armature="0.3"/>
  148 |         <joint name="p_shoulder_roll" type="hinge" axis="0 1 0" range="-120 120" damping="3.0" armature="0.3"/>
  149 |         <geom name="p_shoulder_geom" type="sphere" size="0.1" material="plate_mat" mass="2.0"/>
  150 |         <geom name="p_upper_arm" type="capsule" size="0.07 0.225" pos="0 0 -0.225" material="plate_mat" mass="6.0"/>
  151 |         <body name="pitcher_elbow" pos="0 0 -0.45">
  152 |           <joint name="p_elbow_flex" type="hinge" axis="1 0 0" range="0 150" damping="3.0" armature="0.3"/>
  153 |           <joint name="p_elbow_pronate" type="hinge" axis="0 0 1" range="-90 90" damping="1.0" armature="0.1"/>
  154 |           <geom name="p_elbow_geom" type="sphere" size="0.08" material="plate_mat" mass="1.0"/>
  155 |           <geom name="p_forearm" type="capsule" size="0.06 0.2" pos="0 0 -0.2" material="plate_mat" mass="3.0"/>
  156 |           <body name="pitcher_wrist" pos="0 0 -0.4">
  157 |             <joint name="p_wrist_flex" type="hinge" axis="1 0 0" range="-70 70" damping="1.0" armature="0.1"/>
  158 |             <joint name="p_wrist_dev" type="hinge" axis="0 1 0" range="-30 30" damping="1.0" armature="0.1"/>
  159 |             <geom name="p_wrist_geom" type="sphere" size="0.06" material="plate_mat" mass="1.0"/>
  160 |             <!-- 볼은 별도 freejoint(baseball)이므로 투수 손 끝에는 릴리즈용 위치 마커만 둠 -->
  161 |             <site name="p_release_site" pos="0 0 -0.1" size="0.02" rgba="1 0 0 1"/>
  162 |           </body>
  163 |         </body>
  164 |       </body>
  165 |     </body>
  166 | 
  167 |     <!-- 🎥 멀티뷰 카메라들 -->
  168 |     <camera name="pitcher_cam" pos="0 20.0 2.0" xyaxes="-1 0 0 0 0 1" fovy="60"/>
  169 |     <camera name="catcher_cam" pos="0 -2.0 1.2" xyaxes="1 0 0 0 0 1" fovy="60"/>
  170 |     <camera name="broadcaster_cam" pos="0 -10.0 8.0" euler="65 0 0" fovy="50"/>
  171 |     <camera name="top_down_cam" pos="0 9.0 25.0" euler="0 0 0" fovy="70"/>
  172 | 
  173 |     <!-- Baseball Object (Free Joint, 3D Dynamic Sphere) -->
  174 |     <body name="baseball" pos="0 18.44 1.8">
  175 |       <freejoint name="ball_joint"/>
  176 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" condim="3" friction="0.3 0.05 0.05"/>
  177 |     </body>
  178 | 
  179 |     <!-- Realistic Batter Model: 9-DOF Robot (7-DOF Arm + 2-DOF Neck) -->
  180 |     <body name="batter_torso" pos="-0.85 -0.1 0">
  181 |       <geom name="torso_geom" type="capsule" size="0.15 0.3" pos="0 0 1.1" material="seats_navy" mass="20.0" contype="0" conaffinity="0"/>
  182 |       
  183 |       <!-- Neck & Head (2 DOF) -->
  184 |       <body name="neck" pos="0 0 1.6">
  185 |         <joint name="head_yaw" type="hinge" axis="0 0 1" range="-90 90" damping="0.5" armature="0.05"/>
  186 |         <joint name="head_pitch" type="hinge" axis="0 1 0" range="-45 45" damping="0.5" armature="0.05"/>
  187 |         <geom name="head_geom" type="sphere" size="0.1" material="plate_mat" mass="1.0" contype="0" conaffinity="0"/>
  188 |         <!-- 1인칭 카메라 (머리와 함께 회전) -->
  189 |         <camera name="batter_cam" pos="0 0 0" xyaxes="1 0 0 0 0 1" fovy="90"/>
  190 |       </body>
  191 |       
  192 |       <!-- Shoulder (3 DOF) -->
  193 |       <body name="shoulder" pos="0 -0.2 1.3">
  194 |         <joint name="shoulder_yaw" type="hinge" axis="0 0 1" range="-90 120" damping="2.0" armature="0.1"/>
  195 |         <joint name="shoulder_pitch" type="hinge" axis="1 0 0" range="-90 90" damping="2.0" armature="0.1"/>
  196 |         <joint name="shoulder_roll" type="hinge" axis="0 1 0" range="-90 90" damping="2.0" armature="0.1"/>
  197 |         <geom name="shoulder_geom" type="sphere" size="0.1" material="plate_mat" mass="3.0" contype="0" conaffinity="0"/>
  198 |         <geom name="upper_arm_geom" type="capsule" size="0.06" fromto="0 0 0  0 -0.1 -0.3" material="plate_mat" mass="3.0" contype="0" conaffinity="0"/>
  199 |         
  200 |         <!-- Elbow (1 DOF) -->
  201 |         <body name="elbow" pos="0 -0.1 -0.3">
  202 |           <joint name="elbow_flex" type="hinge" axis="0.53 -0.80 0.27" range="-150 150" damping="2.0" armature="0.1"/>
  203 |           <geom name="elbow_geom" type="sphere" size="0.08" material="plate_mat" mass="2.0" contype="0" conaffinity="0"/>
  204 |           <geom name="forearm_geom" type="capsule" size="0.05" fromto="0 0 0  0.3 0.3 0.3" material="plate_mat" mass="2.0" contype="0" conaffinity="0"/>
  205 |           
  206 |           <!-- Wrist (3 DOF) -->
  207 |           <body name="wrist" pos="0.3 0.3 0.3">
  208 |             <joint name="wrist_yaw" type="hinge" axis="0 0 1" range="-90 90" damping="1.0" armature="0.1"/>
  209 |             <joint name="wrist_pitch" type="hinge" axis="1 0 0" range="-90 90" damping="1.0" armature="0.1"/>
  210 |             <joint name="wrist_roll" type="hinge" axis="0 1 0" range="-90 90" damping="1.0" armature="0.1"/>
  211 |             <geom name="wrist_geom" type="sphere" size="0.06" material="plate_mat" mass="1.0" contype="0" conaffinity="0"/>
  212 |             
  213 |             <!-- Bat (Points UP and BACK in resting stance) -->
  214 |             <body name="bat" pos="0 0 0" euler="-45 0 0">
  215 |               <geom name="bat_knob" type="cylinder" size="0.025 0.015" pos="0 0 -0.015" material="wood" mass="0.05"/>
  216 |               <geom name="bat_handle" type="cylinder" size="0.014 0.2" pos="0 0 0.2" material="wood" mass="0.25"/>
  217 |               <geom name="bat_taper" type="capsule" size="0.024 0.1" pos="0 0 0.45" material="wood" mass="0.2"/>
  218 |               <geom name="bat_barrel" type="cylinder" size="0.034 0.25" pos="0 0 0.675" material="wood" mass="0.5" condim="3" friction="0.6 0.1 0.1"/>
  219 |             </body>
  220 |           </body>
  221 |         </body>
  222 |       </body>
  223 |     </body>
  224 | 
  225 |     <!-- Mobile Center Fielder Robot -->
  226 |     <body name="fielder_cf" pos="0 60 0.5">
  227 |       <joint name="cf_slide_x" type="slide" axis="1 0 0" damping="50" armature="1.0"/>
  228 |       <joint name="cf_slide_y" type="slide" axis="0 1 0" damping="50" armature="1.0"/>
  229 |       
  230 |       <!-- Base Chassis -->
  231 |       <geom name="cf_base" type="cylinder" size="0.3 0.2" material="seats_blue" mass="30.0" contype="0" conaffinity="0"/>
  232 |       <body name="cf_head_body" pos="0 0 1.0">
  233 |         <geom name="cf_head" type="sphere" size="0.15" material="plate_mat" mass="5.0" contype="0" conaffinity="0"/>
  234 |         <!-- 1인칭 카메라 (중견수 시야) -->
  235 |         <camera name="fielder_cam" pos="0 0 0" xyaxes="-1 0 0 0 0 1" fovy="90"/>
  236 |       </body>
  237 |       
  238 |       <!-- Simple Catching Arm / Glove -->
  239 |       <body name="cf_arm" pos="0 -0.3 0.8">
  240 |         <joint name="cf_arm_pitch" type="hinge" axis="1 0 0" range="-45 45" damping="2.0" armature="0.1"/>
  241 |         <geom name="cf_glove" type="sphere" size="0.2" material="wood" mass="2.0" condim="3" friction="1.0 0.5 0.5"/>
  242 |       </body>
  243 |     </body>
  244 |   </worldbody>
  245 | 
  246 |   <actuator>
  247 |     <!-- Batter Actuators -->
  248 |     <motor joint="shoulder_yaw" ctrlrange="-200 200" gear="2.0"/>
  249 |     <motor joint="shoulder_pitch" ctrlrange="-200 200" gear="2.0"/>
  250 |     <motor joint="shoulder_roll" ctrlrange="-200 200" gear="2.0"/>
  251 |     <motor joint="elbow_flex" ctrlrange="-150 150" gear="2.0"/>
  252 |     <motor joint="wrist_yaw" ctrlrange="-50 50" gear="1.0"/>
  253 |     <motor joint="wrist_pitch" ctrlrange="-50 50" gear="1.0"/>
  254 |     <motor joint="wrist_roll" ctrlrange="-50 50" gear="1.0"/>
  255 |     
  256 |     <!-- Pitcher Actuators -->
  257 |     <motor joint="p_shoulder_pitch" ctrlrange="-250 250" gear="2.5"/>
  258 |     <motor joint="p_shoulder_yaw" ctrlrange="-250 250" gear="2.5"/>
  259 |     <motor joint="p_shoulder_roll" ctrlrange="-250 250" gear="2.5"/>
  260 |     <motor joint="p_elbow_flex" ctrlrange="-150 150" gear="2.0"/>
  261 |     <motor joint="p_elbow_pronate" ctrlrange="-150 150" gear="2.0"/>
  262 |     <motor joint="p_wrist_flex" ctrlrange="-50 50" gear="1.0"/>
  263 |     <motor joint="p_wrist_dev" ctrlrange="-50 50" gear="1.0"/>
  264 |     
  265 |     <!-- Fielder Actuators -->
  266 |     <motor joint="cf_slide_x" ctrlrange="-200 200" gear="1.0"/>
  267 |     <motor joint="cf_slide_y" ctrlrange="-200 200" gear="1.0"/>
  268 |     <motor joint="cf_arm_pitch" ctrlrange="-50 50" gear="1.0"/>
  269 |     
  270 |     <!-- Neck Actuators -->
  271 |     <motor joint="head_yaw" ctrlrange="-50 50" gear="1.0"/>
  272 |     <motor joint="head_pitch" ctrlrange="-50 50" gear="1.0"/>
  273 |   </actuator>
  274 | </mujoco>
````
