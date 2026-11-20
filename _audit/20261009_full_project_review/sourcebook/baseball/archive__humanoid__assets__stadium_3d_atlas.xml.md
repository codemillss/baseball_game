# baseball/archive/humanoid/assets/stadium_3d_atlas.xml

원본: [archive/humanoid/assets/stadium_3d_atlas.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/humanoid/assets/stadium_3d_atlas.xml)

SHA256: `295ab8664f14203965b9ef3fbca7a2d645d2881dacd9b7c0973ec43791da90e5`

전체 369행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <mujoco model="stadium_3d_baseball_pro">
    2 |   <compiler angle="degree" coordinate="local" inertiafromgeom="true" meshdir="atlas_repo/model/meshes/" />
    3 |   <option gravity="0 0 -9.81" timestep="0.002" integrator="RK4">
    4 |     <flag constraint="enable" energy="enable" />
    5 |   </option>
    6 |   <default>
    7 |     <joint limited="false" damping="0.01" />
    8 |     <geom condim="3" friction="0.5 0.1 0.1" solref="0.004 1" solimp="0.9 0.95 0.001" margin="0.001" />
    9 |     <default class="atlas">
   10 |       <default class="visual">
   11 |         <geom type="mesh" contype="0" conaffinity="0" group="2" density="0" material="white" />
   12 |       </default>
   13 |     </default>
   14 |   </default>
   15 |   <asset>
   16 |     <texture name="sky" type="skybox" builtin="gradient" rgb1="0.3 0.55 0.9" rgb2="0.05 0.12 0.3" width="512" height="512" />
   17 |     <texture name="grass_tex" type="2d" builtin="checker" rgb1="0.12 0.44 0.12" rgb2="0.09 0.36 0.09" width="256" height="256" />
   18 |     <texture name="dirt_tex" type="2d" builtin="flat" rgb1="0.62 0.38 0.22" width="128" height="128" />
   19 |     <texture name="wood_tex" type="2d" builtin="flat" rgb1="0.82 0.62 0.32" width="128" height="128" />
   20 |     <material name="grass" texture="grass_tex" texrepeat="35 35" reflectance="0.05" />
   21 |     <material name="infield_dirt_mat" texture="dirt_tex" reflectance="0.05" />
   22 |     <material name="warning_track_mat" rgba="0.68 0.42 0.25 1" reflectance="0.05" />
   23 |     <material name="wood" texture="wood_tex" reflectance="0.3" />
   24 |     <material name="ball_mat" rgba="0.98 0.98 0.95 1" reflectance="0.4" />
   25 |     <material name="plate_mat" rgba="0.95 0.95 0.95 1" />
   26 |     <material name="foul_line_mat" rgba="1 1 1 0.9" />
   27 |     <material name="foul_pole_mat" rgba="0.95 0.85 0.1 1" />
   28 |     <material name="strike_zone_mat" rgba="1 0.15 0.15 0.22" />
   29 |     <material name="fence_mat" rgba="0.1 0.25 0.14 1" />
   30 |     <material name="batters_eye_mat" rgba="0.05 0.12 0.08 1" />
   31 |     <material name="backstop_mat" rgba="0.15 0.15 0.18 1" />
   32 |     <material name="ad_board_samsung" rgba="0.02 0.22 0.65 1" />
   33 |     <material name="ad_board_lg" rgba="0.65 0.08 0.2 1" />
   34 |     <material name="ad_board_hyundai" rgba="0.05 0.15 0.4 1" />
   35 |     <material name="ad_board_kakao" rgba="0.95 0.82 0.05 1" />
   36 |     <material name="scoreboard_mat" rgba="0.08 0.1 0.14 1" />
   37 |     <material name="scoreboard_screen" rgba="0.15 0.85 0.35 1" />
   38 |     <material name="seats_blue" rgba="0.15 0.35 0.65 1" />
   39 |     <material name="seats_navy" rgba="0.08 0.18 0.38 1" />
   40 |     <material name="seats_red" rgba="0.75 0.18 0.18 1" />
   41 |     <material name="concrete_concourse" rgba="0.45 0.48 0.52 1" />
   42 |     <material name="entry_tunnel" rgba="0.08 0.08 0.1 1" />
   43 |     <material name="dugout_roof" rgba="0.2 0.22 0.25 1" />
   44 |     <mesh name="r_clav" file="r_clav.obj" />
   45 |     <mesh name="l_foot" file="l_foot.obj" />
   46 |     <mesh name="r_larm" file="r_larm.obj" />
   47 |     <mesh name="r_hand" file="r_hand.obj" />
   48 |     <mesh name="l_lglut" file="l_lglut.obj" />
   49 |     <mesh name="l_lleg" file="l_lleg.obj" />
   50 |     <mesh name="r_scap" file="r_scap.obj" />
   51 |     <mesh name="l_talus" file="l_talus.obj" />
   52 |     <mesh name="r_uarm" file="r_uarm.obj" />
   53 |     <mesh name="r_farm" file="r_farm.obj" />
   54 |     <mesh name="l_uglut" file="l_uglut.obj" />
   55 |     <mesh name="l_uleg" file="l_uleg.obj" />
   56 |     <mesh name="ltorso" file="ltorso.obj" />
   57 |     <mesh name="mtorso" file="mtorso.obj" />
   58 |     <mesh name="pelvis" file="pelvis.obj" />
   59 |     <mesh name="r_foot" file="r_foot.obj" />
   60 |     <mesh name="r_lglut" file="r_lglut.obj" />
   61 |     <mesh name="r_lleg" file="r_lleg.obj" />
   62 |     <mesh name="r_talus" file="r_talus.obj" />
   63 |     <mesh name="r_uglut" file="r_uglut.obj" />
   64 |     <mesh name="r_uleg" file="r_uleg.obj" />
   65 |     <mesh name="utorso" file="utorso.obj" />
   66 |     <mesh name="head" file="head.obj" />
   67 |     <mesh name="head_camera" file="head_camera.obj" />
   68 |     <material name="white" rgba="1 1 1 1" specular="0.4" shininess="0.6" />
   69 |   </asset>
   70 |   <worldbody>
   71 |     <light name="light_main" pos="0 25 35" dir="0 -0.5 -1" directional="true" diffuse="0.9 0.9 0.95" specular="0.3 0.3 0.3" />
   72 |     <light name="light_left" pos="-35 50 30" dir="0.5 -0.5 -1" directional="true" diffuse="0.6 0.6 0.65" />
   73 |     <light name="light_right" pos="35 50 30" dir="-0.5 -0.5 -1" directional="true" diffuse="0.6 0.6 0.65" />
   74 |     <geom name="outfield_grass" type="plane" size="130 130 0.1" pos="0 35 0" material="grass" />
   75 |     <geom name="pitcher_mound" type="cylinder" size="2.74 0.25" pos="0 18.44 0" material="infield_dirt_mat" />
   76 |     <geom name="pitcher_rubber" type="box" size="0.30 0.07 0.02" pos="0 18.44 0.26" material="plate_mat" />
   77 |     <geom name="path_home_1st" type="box" size="0.9 9.7 0.003" pos="9.7 9.7 0.003" euler="0 0 -45" material="infield_dirt_mat" />
   78 |     <geom name="path_home_3rd" type="box" size="0.9 9.7 0.003" pos="-9.7 9.7 0.003" euler="0 0 45" material="infield_dirt_mat" />
   79 |     <geom name="path_1st_2nd" type="box" size="0.9 9.7 0.003" pos="9.7 27.7 0.003" euler="0 0 45" material="infield_dirt_mat" />
   80 |     <geom name="path_3rd_2nd" type="box" size="0.9 9.7 0.003" pos="-9.7 27.7 0.003" euler="0 0 -45" material="infield_dirt_mat" />
   81 |     <geom name="infield_skin_dirt" type="cylinder" size="19.0 0.004" pos="0 18.44 0.004" material="infield_dirt_mat" />
   82 |     <geom name="home_plate" type="box" size="0.216 0.216 0.01" pos="0 0 0.005" material="plate_mat" />
   83 |     <geom name="left_batter_box" type="box" size="0.6 1.2 0.002" pos="-0.85 0.25 0.002" material="infield_dirt_mat" />
   84 |     <geom name="right_batter_box" type="box" size="0.6 1.2 0.002" pos="0.85 0.25 0.002" material="infield_dirt_mat" />
   85 |     <geom name="strike_zone_box" type="box" size="0.216 0.01 0.30" pos="0 0 0.75" material="strike_zone_mat" contype="0" conaffinity="0" />
   86 |     <geom name="base_1st" type="box" size="0.19 0.19 0.04" pos="13.72 13.72 0.04" euler="0 0 45" material="plate_mat" />
   87 |     <geom name="base_2nd" type="box" size="0.19 0.19 0.04" pos="0 27.43 0.04" euler="0 0 45" material="plate_mat" />
   88 |     <geom name="base_3rd" type="box" size="0.19 0.19 0.04" pos="-13.72 13.72 0.04" euler="0 0 45" material="plate_mat" />
   89 |     <geom name="dugout_1st_roof" type="box" size="1.2 8.0 0.6" pos="16.5 6.0 0.6" material="dugout_roof" />
   90 |     <geom name="dugout_3rd_roof" type="box" size="1.2 8.0 0.6" pos="-16.5 6.0 0.6" material="dugout_roof" />
   91 |     <geom name="warning_track" type="box" size="70 3.5 0.004" pos="0 72 0.004" material="warning_track_mat" />
   92 |     <geom name="fence_left_wall" type="box" size="26 0.4 2.2" pos="-45 60 2.2" euler="0 0 25" material="fence_mat" />
   93 |     <geom name="fence_center_wall" type="box" size="22 0.4 2.5" pos="0 75 2.5" material="fence_mat" />
   94 |     <geom name="fence_right_wall" type="box" size="26 0.4 2.2" pos="45 60 2.2" euler="0 0 -25" material="fence_mat" />
   95 |     <geom name="ad_samsung" type="box" size="6.0 0.05 1.0" pos="-35 55.2 2.2" euler="0 0 25" material="ad_board_samsung" />
   96 |     <geom name="ad_lg" type="box" size="6.0 0.05 1.0" pos="-20 62.2 2.2" euler="0 0 25" material="ad_board_lg" />
   97 |     <geom name="ad_hyundai" type="box" size="6.0 0.05 1.2" pos="0 74.5 2.5" material="ad_board_hyundai" />
   98 |     <geom name="ad_kakao" type="box" size="6.0 0.05 1.0" pos="20 62.2 2.2" euler="0 0 -25" material="ad_board_kakao" />
   99 |     <geom name="ad_sponsor_right" type="box" size="6.0 0.05 1.0" pos="35 55.2 2.2" euler="0 0 -25" material="ad_board_samsung" />
  100 |     <geom name="batters_eye" type="box" size="12 0.2 6.0" pos="0 77 6.0" material="batters_eye_mat" />
  101 |     <geom name="jumbo_scoreboard" type="box" size="16 0.5 6.0" pos="0 79 14.0" material="scoreboard_mat" />
  102 |     <geom name="scoreboard_display" type="box" size="14 0.05 4.5" pos="0 78.7 14.0" material="scoreboard_screen" />
  103 |     <geom name="foul_pole_left" type="cylinder" size="0.15 7.0" pos="-58 60 7.0" material="foul_pole_mat" />
  104 |     <geom name="foul_pole_right" type="cylinder" size="0.15 7.0" pos="58 60 7.0" material="foul_pole_mat" />
  105 |     <geom name="foul_line_left" type="box" size="0.06 43 0.003" pos="-21.5 21.5 0.003" euler="0 0 -45" material="foul_line_mat" contype="0" conaffinity="0" />
  106 |     <geom name="foul_line_right" type="box" size="0.06 43 0.003" pos="21.5 21.5 0.003" euler="0 0 45" material="foul_line_mat" contype="0" conaffinity="0" />
  107 |     <geom name="backstop_wall" type="box" size="12 0.5 2.5" pos="0 -4.0 2.5" material="backstop_mat" />
  108 |     <geom name="stand_1st_lower" type="box" size="10 30 3.0" pos="32 20 3.0" euler="-12 0 -25" material="seats_navy" />
  109 |     <geom name="stand_1st_upper" type="box" size="12 35 6.0" pos="50 18 10.0" euler="-22 0 -25" material="seats_blue" />
  110 |     <geom name="portal_1st_1" type="box" size="1.8 1.5 2.2" pos="30 15 2.2" euler="0 0 -25" material="entry_tunnel" />
  111 |     <geom name="portal_1st_2" type="box" size="1.8 1.5 2.2" pos="34 25 3.2" euler="0 0 -25" material="entry_tunnel" />
  112 |     <geom name="stand_3rd_lower" type="box" size="10 30 3.0" pos="-32 20 3.0" euler="-12 0 25" material="seats_navy" />
  113 |     <geom name="stand_3rd_upper" type="box" size="12 35 6.0" pos="-50 18 10.0" euler="-22 0 25" material="seats_red" />
  114 |     <geom name="portal_3rd_1" type="box" size="1.8 1.5 2.2" pos="-30 15 2.2" euler="0 0 25" material="entry_tunnel" />
  115 |     <geom name="portal_3rd_2" type="box" size="1.8 1.5 2.2" pos="-34 25 3.2" euler="0 0 25" material="entry_tunnel" />
  116 |     <geom name="stand_home_grand" type="box" size="18 8.0 5.0" pos="0 -12 6.0" euler="-25 0 0" material="seats_navy" />
  117 |     <geom name="portal_home_center" type="box" size="2.5 1.5 2.5" pos="0 -10 3.5" material="entry_tunnel" />
  118 |     <body name="pitcher_placeholder" pos="0 18.44 0">
  119 |       <geom type="capsule" size="0.2 0.8" pos="0 0 0.8" material="seats_red" />
  120 |     </body>
  121 |     <camera name="pitcher_cam" pos="0 20.0 2.0" euler="90 0 180" fovy="60" />
  122 |     <camera name="catcher_cam" pos="0 -2.0 1.2" euler="90 0 0" fovy="60" />
  123 |     <camera name="broadcaster_cam" pos="0 -10.0 8.0" euler="65 0 0" fovy="50" />
  124 |     <camera name="top_down_cam" pos="0 9.0 25.0" euler="0 0 0" fovy="70" />
  125 |     <body name="baseball" pos="0 18.44 1.8">
  126 |       <freejoint name="ball_joint" />
  127 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" condim="3" friction="0.3 0.05 0.05" solref="0.015 1" />
  128 |     </body>
  129 |     <body name="fielder_cf" pos="0 60 0.5">
  130 |       <joint name="cf_slide_x" type="slide" axis="1 0 0" damping="50" armature="1.0" />
  131 |       <joint name="cf_slide_y" type="slide" axis="0 1 0" damping="50" armature="1.0" />
  132 |       <geom name="cf_base" type="cylinder" size="0.3 0.2" material="seats_blue" mass="30.0" contype="0" conaffinity="0" />
  133 |       <geom name="cf_head" type="sphere" size="0.15" pos="0 0 1.0" material="plate_mat" mass="5.0" contype="0" conaffinity="0" />
  134 |       <body name="cf_arm" pos="0 -0.3 0.8">
  135 |         <joint name="cf_arm_pitch" type="hinge" axis="1 0 0" range="-45 45" damping="2.0" armature="0.1" />
  136 |         <geom name="cf_glove" type="sphere" size="0.2" material="wood" mass="2.0" condim="3" friction="1.0 0.5 0.5" />
  137 |       </body>
  138 |     </body>
  139 |     <body name="pelvis" pos="0.5 -0.2 0.95" euler="0 0 90">
  140 |       <freejoint />
  141 |       <geom class="visual" mesh="pelvis" />
  142 |       <inertial pos="0.0111 0 0.0271" quat="0.698584 0.713914 0.0424837 -0.0224092" mass="9.509" diaginertia="0.124488 0.116646 0.0957666" />
  143 |       <body name="ltorso" pos="-0.0125 0 0">
  144 |         <inertial pos="-0.0112984 -3.15366e-06 0.0746835" quat="0.997071 0.000128212 0.076485 -0.00012406" mass="2.27" diaginertia="0.003962 0.00341694 0.00169212" />
  145 |         <joint name="back_bkz" pos="0 0 0" axis="0 0 1" range="-0.663225 0.663225" damping="0.1" />
  146 |         <geom class="visual" mesh="ltorso" />
  147 |         <body name="mtorso" pos="0 0 0.162">
  148 |           <inertial pos="-0.00816266 -0.0131245 0.0305974" quat="0.108378 0.49314 0.746335 0.433648" mass="0.799" diaginertia="0.000536243 0.000487378 0.000358057" />
  149 |           <joint name="back_bky" pos="0 0 0" axis="0 1 0" range="-0.219388 0.538783" damping="0.1" />
  150 |           <geom class="visual" mesh="mtorso" />
  151 |           <body name="utorso" pos="0 0 0.05">
  152 |             <inertial pos="-0.0616866 0.00229456 0.316809" quat="0.483464 -0.0233226 -0.0389662 0.874186" mass="84.609" diaginertia="1.67522 1.61265 0.568768" />
  153 |             <joint name="back_bkx" pos="0 0 0" axis="1 0 0" range="-0.523599 0.523599" damping="0.1" />
  154 |             <geom class="visual" mesh="utorso" />
  155 |             <geom size="0.005 0.005 0.005" pos="0.155 -0.121 0.785" quat="0.793352 0 0 -0.608763" type="box" contype="0" conaffinity="0" group="1" density="0" />
  156 |             <geom size="0.005 0.005 0.005" pos="0.155 0.121 0.785" quat="0.793352 0 0 0.608763" type="box" contype="0" conaffinity="0" group="1" density="0" />
  157 |             <body name="l_clav" pos="0.1406 0.2256 0.4776" quat="0 0 0 1">
  158 |               <inertial pos="0 0 -0.084" quat="0.684588 0.177029 -0.177029 0.684588" mass="4.466" diaginertia="0.011217 0.011 0.00178301" />
  159 |               <joint name="l_arm_shz" pos="0 0 0" axis="0 0 1" range="-1.5708 0.785398" damping="0.1" />
  160 |               <geom class="visual" mesh="r_clav" />
  161 |               <body name="l_scap" pos="0 -0.11 -0.245">
  162 |                 <inertial pos="0 0 0" quat="0.5 0.5 0.5 0.5" mass="3.899" diaginertia="0.00583 0.00583 0.00319" />
  163 |                 <joint name="l_arm_shx" pos="0 0 0" axis="-1 0 0" range="-1.5708 1.5708" damping="0.1" />
  164 |                 <geom class="visual" mesh="r_scap" />
  165 |                 <body name="l_uarm" pos="0 -0.187 -0.016">
  166 |                   <inertial pos="0 0.065 0" quat="0.707107 0.707107 0 0" mass="4.386" diaginertia="0.00656 0.00656 0.00358" />
  167 |                   <joint name="l_arm_ely" pos="0 0 0" axis="0 -1 0" range="0 3.14159" damping="0.1" />
  168 |                   <geom class="visual" mesh="r_uarm" />
  169 |                   <body name="l_larm" pos="0 -0.119 0.0092">
  170 |                     <inertial pos="0 0 0" quat="0.5 0.5 0.5 0.5" mass="3.248" diaginertia="0.00446 0.00446 0.00265" />
  171 |                     <joint name="l_arm_elx" pos="0 0 0" axis="-1 0 0" range="0 2.35619" damping="0.1" />
  172 |                     <geom class="visual" mesh="r_larm" />
  173 |                     <body name="l_ufarm" pos="0 -0.29955 -0.00921" quat="0 0 1 0">
  174 |                       <inertial pos="0.00015 0.08296 0.00037" quat="0.707107 0.707107 0 0" mass="2.4798" diaginertia="0.012731 0.011948 0.002857" />
  175 |                       <joint name="l_arm_uwy" pos="0 0 0" axis="0 -1 0" range="-3.011 3.011" damping="0.1" />
  176 |                       <geom class="visual" mesh="r_farm" />
  177 |                       <body name="l_lfarm">
  178 |                         <inertial pos="0.00017 -0.02515 0.00163" quat="0.5 0.5 -0.5 0.5" mass="0.648" diaginertia="0.000825 0.000764 0.000429" />
  179 |                         <joint name="l_arm_mwx" pos="0 0 0" axis="1 0 0" range="-1.7628 1.7628" damping="0.1" />
  180 |                         <geom class="visual" mesh="r_hand" />
  181 |                         <body name="l_hand" quat="0 0 1 0">
  182 |                           <inertial pos="0.000136605 -0.0878643 1.70756e-05" quat="0.706663 0.707538 -0.00305426 -0.0030225" mass="0.6839" diaginertia="0.000555209 0.000546206 0.000486997" />
  183 |                           <joint name="l_arm_lwy" pos="0 0 0" axis="0 -1 0" range="-2.9671 2.9671" damping="0.1" />
  184 |                           <geom size="0.005 0.005 0.005" pos="0 -0.1245 0" quat="3.26795e-07 0 0 1" type="box" contype="0" conaffinity="0" group="1" density="0" />
  185 |                         </body>
  186 |                       </body>
  187 |                     </body>
  188 |                   </body>
  189 |                 </body>
  190 |               </body>
  191 |             </body>
  192 |             <body name="head" pos="0.2546 0 0.6215">
  193 |               <inertial pos="-0.0526114 3.39872e-05 0.0260689" quat="-0.00433632 0.59051 -0.00248869 0.807015" mass="2.08756" diaginertia="0.0135173 0.0133409 0.0119567" />
  194 |               <joint name="neck_ay" pos="0 0 0" axis="0 1 0" range="-0.602139 1.14319" damping="0.1" />
  195 |               <geom class="visual" rgba="0.9098 0.44314 0.031373 1" mesh="head" />
  196 |               <geom pos="0.0004 -0.0261018 0.00457631" quat="0.987701 -0.156356 0 0" type="mesh" contype="0" conaffinity="0" group="1" density="0" rgba="0.72941 0.35686 0.023529 1" mesh="head_camera" />
  197 |               <camera name="batter_cam" pos="0.15 0 0.1" euler="90 0 90" fovy="75" />
  198 |             </body>
  199 |             <body name="r_clav" pos="0.1406 -0.2256 0.4776">
  200 |               <inertial pos="0 0 -0.084" quat="0.684588 0.177029 -0.177029 0.684588" mass="4.466" diaginertia="0.011217 0.011 0.00178301" />
  201 |               <joint name="r_arm_shz" pos="0 0 0" axis="0 0 1" range="-0.785398 1.5708" damping="0.1" />
  202 |               <geom class="visual" mesh="r_clav" />
  203 |               <body name="r_scap" pos="0 -0.11 -0.245">
  204 |                 <inertial pos="0 0 0" quat="0.5 0.5 0.5 0.5" mass="3.899" diaginertia="0.00583 0.00583 0.00319" />
  205 |                 <joint name="r_arm_shx" pos="0 0 0" axis="1 0 0" range="-1.5708 1.5708" damping="0.1" />
  206 |                 <geom class="visual" mesh="r_scap" />
  207 |                 <body name="r_uarm" pos="0 -0.187 -0.016">
  208 |                   <inertial pos="0 0.065 0" quat="0.707107 0.707107 0 0" mass="4.386" diaginertia="0.00656 0.00656 0.00358" />
  209 |                   <joint name="r_arm_ely" pos="0 0 0" axis="0 1 0" range="0 3.14159" damping="0.1" />
  210 |                   <geom class="visual" mesh="r_uarm" />
  211 |                   <body name="r_larm" pos="0 -0.119 0.0092">
  212 |                     <inertial pos="0 0 0" quat="0.5 0.5 0.5 0.5" mass="3.248" diaginertia="0.00446 0.00446 0.00265" />
  213 |                     <joint name="r_arm_elx" pos="0 0 0" axis="1 0 0" range="-2.35619 0" damping="0.1" />
  214 |                     <geom class="visual" mesh="r_larm" />
  215 |                     <body name="r_ufarm" pos="0 -0.29955 -0.00921">
  216 |                       <inertial pos="0.00015 0.08296 0.00037" quat="0.707107 0.707107 0 0" mass="2.4798" diaginertia="0.012731 0.011948 0.002857" />
  217 |                       <joint name="r_arm_uwy" pos="0 0 0" axis="0 1 0" range="-3.011 3.011" damping="0.1" />
  218 |                       <geom class="visual" mesh="r_farm" />
  219 |                       <body name="r_lfarm">
  220 |                         <inertial pos="0.00017 -0.02515 0.00163" quat="0.5 0.5 -0.5 0.5" mass="0.648" diaginertia="0.000825 0.000764 0.000429" />
  221 |                         <joint name="r_arm_mwx" pos="0 0 0" axis="1 0 0" range="-1.7628 1.7628" damping="0.1" />
  222 |                         <geom class="visual" mesh="r_hand" />
  223 |                         <body name="r_hand">
  224 |                           <inertial pos="0.000136605 -0.0878643 1.70756e-05" quat="0.706663 0.707538 -0.00305426 -0.0030225" mass="0.6839" diaginertia="0.000555209 0.000546206 0.000486997" />
  225 |                           <joint name="r_arm_lwy" pos="0 0 0" axis="0 1 0" range="-2.9671 2.9671" damping="0.1" />
  226 |                           <geom size="0.005 0.005 0.005" pos="0 -0.1245 0" quat="3.26795e-07 0 0 1" type="box" contype="0" conaffinity="0" group="1" density="0" />
  227 |                           <body name="bat" pos="0.0 -0.15 0.0" euler="0 90 0">
  228 |                             <geom name="bat_knob" type="cylinder" size="0.025 0.015" pos="0 0.015 0" euler="90 0 0" material="wood" mass="0.05" />
  229 |                             <geom name="bat_handle" type="cylinder" size="0.014 0.2" pos="0 0.2 0" euler="90 0 0" material="wood" mass="0.25" />
  230 |                             <geom name="bat_taper" type="capsule" size="0.024 0.1" pos="0 0.45 0" euler="90 0 0" material="wood" mass="0.2" />
  231 |                             <geom name="bat_barrel" type="cylinder" size="0.034 0.25" pos="0 0.675 0" euler="90 0 0" material="wood" mass="0.5" condim="3" friction="0.6 0.1 0.1" solref="0.015 1" />
  232 |                           </body>
  233 |                         </body>
  234 |                       </body>
  235 |                     </body>
  236 |                   </body>
  237 |                 </body>
  238 |               </body>
  239 |             </body>
  240 |           </body>
  241 |         </body>
  242 |       </body>
  243 |       <body name="l_uglut" pos="0 0.089 0">
  244 |         <inertial pos="0.00529262 -0.00344732 0.00313046" quat="0.999122 -7.72169e-05 0.0419028 -0.000305187" mass="1.959" diaginertia="0.000745109 0.000688179 0.000410071" />
  245 |         <joint name="l_leg_hpz" pos="0 0 0" axis="0 0 1" range="-0.174358 0.786794" damping="0.1" />
  246 |         <geom class="visual" mesh="l_uglut" />
  247 |         <body name="l_lglut">
  248 |           <inertial pos="0.0133341 0.0170484 -0.0312052" quat="0.353465 0.600383 0.388609 0.602981" mass="0.898" diaginertia="0.00133867 0.000995812 0.000690275" />
  249 |           <joint name="l_leg_hpx" pos="0 0 0" axis="1 0 0" range="-0.523599 0.523599" damping="0.1" />
  250 |           <geom class="visual" mesh="l_lglut" />
  251 |           <body name="l_uleg" pos="0.05 0.0225 -0.066">
  252 |             <inertial pos="0 0 -0.21" mass="8.204" diaginertia="0.09 0.09 0.02" />
  253 |             <joint name="l_leg_hpy" pos="0 0 0" axis="0 1 0" range="-1.61234 0.65764" damping="0.1" />
  254 |             <geom class="visual" mesh="l_uleg" />
  255 |             <body name="l_lleg" pos="-0.05 0 -0.374">
  256 |               <inertial pos="0.001 0 -0.187" quat="0.999751 0 0.0223266 0" mass="4.515" diaginertia="0.0771341 0.076 0.00986594" />
  257 |               <joint name="l_leg_kny" pos="0 0 0" axis="0 1 0" range="0 2.35637" damping="0.1" />
  258 |               <geom class="visual" mesh="l_lleg" />
  259 |               <body name="l_talus" pos="0 0 -0.422">
  260 |                 <inertial pos="0 0 0" quat="0.5 0.5 -0.5 0.5" mass="0.125" diaginertia="1.30101e-05 1.01674e-05 8.42775e-06" />
  261 |                 <joint name="l_leg_aky" pos="0 0 0" axis="0 1 0" range="-1 0.7" damping="0.1" />
  262 |                 <geom class="visual" mesh="l_talus" />
  263 |                 <body name="l_foot">
  264 |                   <inertial pos="0.027 0 -0.067" quat="0 0.707107 0 0.707107" mass="2.41" diaginertia="0.008 0.007 0.002" />
  265 |                   <joint name="l_leg_akx" pos="0 0 0" axis="1 0 0" range="-0.8 0.8" damping="0.1" />
  266 |                   <geom class="visual" mesh="l_foot" />
  267 |                   <geom size="0.0001" pos="-0.0876 0.066 -0.07645" />
  268 |                   <geom size="0.01" pos="-0.0876 0.066 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  269 |                   <geom size="0.0001" pos="-0.0876 -0.0626 -0.07645" />
  270 |                   <geom size="0.01" pos="-0.0876 -0.0626 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  271 |                   <geom size="0.0001" pos="0.1728 0.066 -0.07645" />
  272 |                   <geom size="0.01" pos="0.1728 0.066 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  273 |                   <geom size="0.0001" pos="0.1728 -0.0626 -0.07645" />
  274 |                   <geom size="0.01" pos="0.1728 -0.0626 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  275 |                   <geom size="0.0001" pos="0.086 0.066 -0.07645" />
  276 |                   <geom size="0.01" pos="0.086 0.066 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  277 |                   <geom size="0.0001" pos="0.086 -0.0626 -0.07645" />
  278 |                   <geom size="0.01" pos="0.086 -0.0626 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  279 |                   <geom size="0.0001" pos="-0.0008 0.066 -0.07645" />
  280 |                   <geom size="0.01" pos="-0.0008 0.066 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  281 |                   <geom size="0.0001" pos="-0.0008 -0.0626 -0.07645" />
  282 |                   <geom size="0.01" pos="-0.0008 -0.0626 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  283 |                 </body>
  284 |               </body>
  285 |             </body>
  286 |           </body>
  287 |         </body>
  288 |       </body>
  289 |       <body name="r_uglut" pos="0 -0.089 0">
  290 |         <inertial pos="0.00529262 0.00344732 0.00313046" quat="0.999122 7.72169e-05 0.0419028 0.000305187" mass="1.959" diaginertia="0.000745109 0.000688179 0.000410071" />
  291 |         <joint name="r_leg_hpz" pos="0 0 0" axis="0 0 1" range="-0.786794 0.174358" damping="0.1" />
  292 |         <geom class="visual" mesh="r_uglut" />
  293 |         <body name="r_lglut">
  294 |           <inertial pos="0.0133341 -0.0170484 -0.0312052" quat="0.602981 0.388609 0.600383 0.353465" mass="0.898" diaginertia="0.00133867 0.000995812 0.000690275" />
  295 |           <joint name="r_leg_hpx" pos="0 0 0" axis="1 0 0" range="-0.523599 0.523599" damping="0.1" />
  296 |           <geom class="visual" mesh="r_lglut" />
  297 |           <body name="r_uleg" pos="0.05 -0.0225 -0.066">
  298 |             <inertial pos="0 0 -0.21" mass="8.204" diaginertia="0.09 0.09 0.02" />
  299 |             <joint name="r_leg_hpy" pos="0 0 0" axis="0 1 0" range="-1.61234 0.65764" damping="0.1" />
  300 |             <geom class="visual" mesh="r_uleg" />
  301 |             <body name="r_lleg" pos="-0.05 0 -0.374">
  302 |               <inertial pos="0.001 0 -0.187" quat="0.999751 0 0.0223266 0" mass="4.515" diaginertia="0.0771341 0.076 0.00986594" />
  303 |               <joint name="r_leg_kny" pos="0 0 0" axis="0 1 0" range="0 2.35637" damping="0.1" />
  304 |               <geom class="visual" mesh="r_lleg" />
  305 |               <body name="r_talus" pos="0 0 -0.422">
  306 |                 <inertial pos="0 0 0" quat="0.5 0.5 -0.5 0.5" mass="0.125" diaginertia="1.30101e-05 1.01674e-05 8.42775e-06" />
  307 |                 <joint name="r_leg_aky" pos="0 0 0" axis="0 1 0" range="-1 0.7" damping="0.1" />
  308 |                 <geom class="visual" mesh="r_talus" />
  309 |                 <body name="r_foot">
  310 |                   <inertial pos="0.027 0 -0.067" quat="0 0.707107 0 0.707107" mass="2.41" diaginertia="0.008 0.007 0.002" />
  311 |                   <joint name="r_leg_akx" pos="0 0 0" axis="1 0 0" range="-0.8 0.8" damping="0.1" />
  312 |                   <geom class="visual" mesh="r_foot" />
  313 |                   <geom size="0.0001" pos="-0.0876 0.0626 -0.07645" />
  314 |                   <geom size="0.01" pos="-0.0876 0.0626 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  315 |                   <geom size="0.0001" pos="-0.0876 -0.066 -0.07645" />
  316 |                   <geom size="0.01" pos="-0.0876 -0.066 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  317 |                   <geom size="0.0001" pos="0.1728 0.0626 -0.07645" />
  318 |                   <geom size="0.01" pos="0.1728 0.0626 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  319 |                   <geom size="0.0001" pos="0.1728 -0.066 -0.07645" />
  320 |                   <geom size="0.01" pos="0.1728 -0.066 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  321 |                   <geom size="0.0001" pos="0.086 0.0626 -0.07645" />
  322 |                   <geom size="0.01" pos="0.086 0.0626 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  323 |                   <geom size="0.0001" pos="0.086 -0.066 -0.07645" />
  324 |                   <geom size="0.01" pos="0.086 -0.066 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  325 |                   <geom size="0.0001" pos="-0.0008 0.0626 -0.07645" />
  326 |                   <geom size="0.01" pos="-0.0008 0.0626 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  327 |                   <geom size="0.0001" pos="-0.0008 -0.066 -0.07645" />
  328 |                   <geom size="0.01" pos="-0.0008 -0.066 -0.07645" contype="0" conaffinity="0" group="1" density="0" />
  329 |                 </body>
  330 |               </body>
  331 |             </body>
  332 |           </body>
  333 |         </body>
  334 |       </body>
  335 |     </body>
  336 |   </worldbody>
  337 |   <actuator>
  338 |     <motor name="back_bkz_motor" joint="back_bkz" />
  339 |     <motor name="back_bky_motor" joint="back_bky" />
  340 |     <motor name="back_bkx_motor" joint="back_bkx" />
  341 |     <motor name="l_arm_shz_motor" joint="l_arm_shz" />
  342 |     <motor name="l_arm_shx_motor" joint="l_arm_shx" />
  343 |     <motor name="l_arm_ely_motor" joint="l_arm_ely" />
  344 |     <motor name="l_arm_elx_motor" joint="l_arm_elx" />
  345 |     <motor name="l_arm_uwy_motor" joint="l_arm_uwy" />
  346 |     <motor name="l_arm_mwx_motor" joint="l_arm_mwx" />
  347 |     <motor name="l_arm_lwy_motor" joint="l_arm_lwy" />
  348 |     <motor name="neck_ay_motor" joint="neck_ay" />
  349 |     <motor name="r_arm_shz_motor" joint="r_arm_shz" />
  350 |     <motor name="r_arm_shx_motor" joint="r_arm_shx" />
  351 |     <motor name="r_arm_ely_motor" joint="r_arm_ely" />
  352 |     <motor name="r_arm_elx_motor" joint="r_arm_elx" />
  353 |     <motor name="r_arm_uwy_motor" joint="r_arm_uwy" />
  354 |     <motor name="r_arm_mwx_motor" joint="r_arm_mwx" />
  355 |     <motor name="r_arm_lwy_motor" joint="r_arm_lwy" />
  356 |     <motor name="l_leg_hpz_motor" joint="l_leg_hpz" />
  357 |     <motor name="l_leg_hpx_motor" joint="l_leg_hpx" />
  358 |     <motor name="l_leg_hpy_motor" joint="l_leg_hpy" />
  359 |     <motor name="l_leg_kny_motor" joint="l_leg_kny" />
  360 |     <motor name="l_leg_aky_motor" joint="l_leg_aky" />
  361 |     <motor name="l_leg_akx_motor" joint="l_leg_akx" />
  362 |     <motor name="r_leg_hpz_motor" joint="r_leg_hpz" />
  363 |     <motor name="r_leg_hpx_motor" joint="r_leg_hpx" />
  364 |     <motor name="r_leg_hpy_motor" joint="r_leg_hpy" />
  365 |     <motor name="r_leg_kny_motor" joint="r_leg_kny" />
  366 |     <motor name="r_leg_aky_motor" joint="r_leg_aky" />
  367 |     <motor name="r_leg_akx_motor" joint="r_leg_akx" />
  368 |   </actuator>
  369 | </mujoco>
````
