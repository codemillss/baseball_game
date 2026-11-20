# baseball/archive/humanoid/assets/stadium_3d_humanoid.xml

원본: [archive/humanoid/assets/stadium_3d_humanoid.xml](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/humanoid/assets/stadium_3d_humanoid.xml)

SHA256: `3fcc20c4f4df8ee917e390460f457ed804b7fd2cdfae828b6f2c366c70ad9c04`

전체 296행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <mujoco model="stadium_3d_baseball_pro">
    2 |   <compiler angle="degree" coordinate="local" inertiafromgeom="true" />
    3 |   <option gravity="0 0 -9.81" timestep="0.002" integrator="RK4">
    4 |     <flag constraint="enable" energy="enable" />
    5 |   </option>
    6 |   <default>
    7 |     <joint limited="false" damping="0.01" />
    8 |     <geom condim="3" friction="0.5 0.1 0.1" solref="0.004 1" solimp="0.9 0.95 0.001" margin="0.001" />
    9 |     <motor ctrlrange="-1 1" ctrllimited="true" />
   10 |     <default class="body">
   11 |       <geom type="capsule" condim="1" friction=".7" solimp=".9 .99 .003" solref=".015 1" material="body" group="1" />
   12 |       <default class="thigh">
   13 |         <geom size=".06" />
   14 |       </default>
   15 |       <default class="shin">
   16 |         <geom fromto="0 0 0 0 0 -.3" size=".049" />
   17 |       </default>
   18 |       <default class="foot">
   19 |         <geom size=".027" />
   20 |         <default class="foot1">
   21 |           <geom fromto="-.07 -.01 0 .14 -.03 0" />
   22 |         </default>
   23 |         <default class="foot2">
   24 |           <geom fromto="-.07 .01 0 .14  .03 0" />
   25 |         </default>
   26 |       </default>
   27 |       <default class="arm_upper">
   28 |         <geom size=".04" />
   29 |       </default>
   30 |       <default class="arm_lower">
   31 |         <geom size=".031" />
   32 |       </default>
   33 |       <default class="hand">
   34 |         <geom type="sphere" size=".04" />
   35 |       </default>
   36 |       <joint type="hinge" damping=".2" stiffness="1" armature=".01" limited="true" solimplimit="0 .99 .01" />
   37 |       <default class="joint_big">
   38 |         <joint damping="5" stiffness="10" />
   39 |         <default class="hip_x">
   40 |           <joint range="-30 10" />
   41 |         </default>
   42 |         <default class="hip_z">
   43 |           <joint range="-60 35" />
   44 |         </default>
   45 |         <default class="hip_y">
   46 |           <joint axis="0 1 0" range="-150 20" />
   47 |         </default>
   48 |         <default class="joint_big_stiff">
   49 |           <joint stiffness="20" />
   50 |         </default>
   51 |       </default>
   52 |       <default class="knee">
   53 |         <joint pos="0 0 .02" axis="0 -1 0" range="-160 2" />
   54 |       </default>
   55 |       <default class="ankle">
   56 |         <joint range="-50 50" />
   57 |         <default class="ankle_y">
   58 |           <joint pos="0 0 .08" axis="0 1 0" stiffness="6" />
   59 |         </default>
   60 |         <default class="ankle_x">
   61 |           <joint pos="0 0 .04" stiffness="3" />
   62 |         </default>
   63 |       </default>
   64 |       <default class="shoulder">
   65 |         <joint range="-85 60" />
   66 |       </default>
   67 |       <default class="elbow">
   68 |         <joint range="-100 50" stiffness="0" />
   69 |       </default>
   70 |     </default>
   71 |   </default>
   72 |   <asset>
   73 |     <texture name="sky" type="skybox" builtin="gradient" rgb1="0.3 0.55 0.9" rgb2="0.05 0.12 0.3" width="512" height="512" />
   74 |     <texture name="grass_tex" type="2d" builtin="checker" rgb1="0.12 0.44 0.12" rgb2="0.09 0.36 0.09" width="256" height="256" />
   75 |     <texture name="dirt_tex" type="2d" builtin="flat" rgb1="0.62 0.38 0.22" width="128" height="128" />
   76 |     <texture name="wood_tex" type="2d" builtin="flat" rgb1="0.82 0.62 0.32" width="128" height="128" />
   77 |     <material name="grass" texture="grass_tex" texrepeat="35 35" reflectance="0.05" />
   78 |     <material name="infield_dirt_mat" texture="dirt_tex" reflectance="0.05" />
   79 |     <material name="warning_track_mat" rgba="0.68 0.42 0.25 1" reflectance="0.05" />
   80 |     <material name="wood" texture="wood_tex" reflectance="0.3" />
   81 |     <material name="ball_mat" rgba="0.98 0.98 0.95 1" reflectance="0.4" />
   82 |     <material name="plate_mat" rgba="0.95 0.95 0.95 1" />
   83 |     <material name="foul_line_mat" rgba="1 1 1 0.9" />
   84 |     <material name="foul_pole_mat" rgba="0.95 0.85 0.1 1" />
   85 |     <material name="strike_zone_mat" rgba="1 0.15 0.15 0.22" />
   86 |     <material name="fence_mat" rgba="0.1 0.25 0.14 1" />
   87 |     <material name="batters_eye_mat" rgba="0.05 0.12 0.08 1" />
   88 |     <material name="backstop_mat" rgba="0.15 0.15 0.18 1" />
   89 |     <material name="ad_board_samsung" rgba="0.02 0.22 0.65 1" />
   90 |     <material name="ad_board_lg" rgba="0.65 0.08 0.2 1" />
   91 |     <material name="ad_board_hyundai" rgba="0.05 0.15 0.4 1" />
   92 |     <material name="ad_board_kakao" rgba="0.95 0.82 0.05 1" />
   93 |     <material name="scoreboard_mat" rgba="0.08 0.1 0.14 1" />
   94 |     <material name="scoreboard_screen" rgba="0.15 0.85 0.35 1" />
   95 |     <material name="seats_blue" rgba="0.15 0.35 0.65 1" />
   96 |     <material name="seats_navy" rgba="0.08 0.18 0.38 1" />
   97 |     <material name="seats_red" rgba="0.75 0.18 0.18 1" />
   98 |     <material name="concrete_concourse" rgba="0.45 0.48 0.52 1" />
   99 |     <material name="entry_tunnel" rgba="0.08 0.08 0.1 1" />
  100 |     <material name="dugout_roof" rgba="0.2 0.22 0.25 1" />
  101 |     <texture type="skybox" builtin="gradient" rgb1=".3 .5 .7" rgb2="0 0 0" width="32" height="512" />
  102 |     <texture name="body" type="cube" builtin="flat" mark="cross" width="128" height="128" rgb1="0.8 0.6 0.4" rgb2="0.8 0.6 0.4" markrgb="1 1 1" />
  103 |     <material name="body" texture="body" texuniform="true" rgba="0.8 0.6 .4 1" />
  104 |   </asset>
  105 |   <worldbody>
  106 |     <light name="light_main" pos="0 25 35" dir="0 -0.5 -1" directional="true" diffuse="0.9 0.9 0.95" specular="0.3 0.3 0.3" />
  107 |     <light name="light_left" pos="-35 50 30" dir="0.5 -0.5 -1" directional="true" diffuse="0.6 0.6 0.65" />
  108 |     <light name="light_right" pos="35 50 30" dir="-0.5 -0.5 -1" directional="true" diffuse="0.6 0.6 0.65" />
  109 |     <geom name="outfield_grass" type="plane" size="130 130 0.1" pos="0 35 0" material="grass" />
  110 |     <geom name="pitcher_mound" type="cylinder" size="2.74 0.25" pos="0 18.44 0" material="infield_dirt_mat" />
  111 |     <geom name="pitcher_rubber" type="box" size="0.30 0.07 0.02" pos="0 18.44 0.26" material="plate_mat" />
  112 |     <geom name="path_home_1st" type="box" size="0.9 9.7 0.003" pos="9.7 9.7 0.003" euler="0 0 -45" material="infield_dirt_mat" />
  113 |     <geom name="path_home_3rd" type="box" size="0.9 9.7 0.003" pos="-9.7 9.7 0.003" euler="0 0 45" material="infield_dirt_mat" />
  114 |     <geom name="path_1st_2nd" type="box" size="0.9 9.7 0.003" pos="9.7 27.7 0.003" euler="0 0 45" material="infield_dirt_mat" />
  115 |     <geom name="path_3rd_2nd" type="box" size="0.9 9.7 0.003" pos="-9.7 27.7 0.003" euler="0 0 -45" material="infield_dirt_mat" />
  116 |     <geom name="infield_skin_dirt" type="cylinder" size="19.0 0.004" pos="0 18.44 0.004" material="infield_dirt_mat" />
  117 |     <geom name="home_plate" type="box" size="0.216 0.216 0.01" pos="0 0 0.005" material="plate_mat" />
  118 |     <geom name="left_batter_box" type="box" size="0.6 1.2 0.002" pos="-0.85 0.25 0.002" material="infield_dirt_mat" />
  119 |     <geom name="right_batter_box" type="box" size="0.6 1.2 0.002" pos="0.85 0.25 0.002" material="infield_dirt_mat" />
  120 |     <geom name="strike_zone_box" type="box" size="0.216 0.01 0.30" pos="0 0 0.75" material="strike_zone_mat" contype="0" conaffinity="0" />
  121 |     <geom name="base_1st" type="box" size="0.19 0.19 0.04" pos="13.72 13.72 0.04" euler="0 0 45" material="plate_mat" />
  122 |     <geom name="base_2nd" type="box" size="0.19 0.19 0.04" pos="0 27.43 0.04" euler="0 0 45" material="plate_mat" />
  123 |     <geom name="base_3rd" type="box" size="0.19 0.19 0.04" pos="-13.72 13.72 0.04" euler="0 0 45" material="plate_mat" />
  124 |     <geom name="dugout_1st_roof" type="box" size="1.2 8.0 0.6" pos="16.5 6.0 0.6" material="dugout_roof" />
  125 |     <geom name="dugout_3rd_roof" type="box" size="1.2 8.0 0.6" pos="-16.5 6.0 0.6" material="dugout_roof" />
  126 |     <geom name="warning_track" type="box" size="70 3.5 0.004" pos="0 72 0.004" material="warning_track_mat" />
  127 |     <geom name="fence_left_wall" type="box" size="26 0.4 2.2" pos="-45 60 2.2" euler="0 0 25" material="fence_mat" />
  128 |     <geom name="fence_center_wall" type="box" size="22 0.4 2.5" pos="0 75 2.5" material="fence_mat" />
  129 |     <geom name="fence_right_wall" type="box" size="26 0.4 2.2" pos="45 60 2.2" euler="0 0 -25" material="fence_mat" />
  130 |     <geom name="ad_samsung" type="box" size="6.0 0.05 1.0" pos="-35 55.2 2.2" euler="0 0 25" material="ad_board_samsung" />
  131 |     <geom name="ad_lg" type="box" size="6.0 0.05 1.0" pos="-20 62.2 2.2" euler="0 0 25" material="ad_board_lg" />
  132 |     <geom name="ad_hyundai" type="box" size="6.0 0.05 1.2" pos="0 74.5 2.5" material="ad_board_hyundai" />
  133 |     <geom name="ad_kakao" type="box" size="6.0 0.05 1.0" pos="20 62.2 2.2" euler="0 0 -25" material="ad_board_kakao" />
  134 |     <geom name="ad_sponsor_right" type="box" size="6.0 0.05 1.0" pos="35 55.2 2.2" euler="0 0 -25" material="ad_board_samsung" />
  135 |     <geom name="batters_eye" type="box" size="12 0.2 6.0" pos="0 77 6.0" material="batters_eye_mat" />
  136 |     <geom name="jumbo_scoreboard" type="box" size="16 0.5 6.0" pos="0 79 14.0" material="scoreboard_mat" />
  137 |     <geom name="scoreboard_display" type="box" size="14 0.05 4.5" pos="0 78.7 14.0" material="scoreboard_screen" />
  138 |     <geom name="foul_pole_left" type="cylinder" size="0.15 7.0" pos="-58 60 7.0" material="foul_pole_mat" />
  139 |     <geom name="foul_pole_right" type="cylinder" size="0.15 7.0" pos="58 60 7.0" material="foul_pole_mat" />
  140 |     <geom name="foul_line_left" type="box" size="0.06 43 0.003" pos="-21.5 21.5 0.003" euler="0 0 -45" material="foul_line_mat" contype="0" conaffinity="0" />
  141 |     <geom name="foul_line_right" type="box" size="0.06 43 0.003" pos="21.5 21.5 0.003" euler="0 0 45" material="foul_line_mat" contype="0" conaffinity="0" />
  142 |     <geom name="backstop_wall" type="box" size="12 0.5 2.5" pos="0 -4.0 2.5" material="backstop_mat" />
  143 |     <geom name="stand_1st_lower" type="box" size="10 30 3.0" pos="32 20 3.0" euler="-12 0 -25" material="seats_navy" />
  144 |     <geom name="stand_1st_upper" type="box" size="12 35 6.0" pos="50 18 10.0" euler="-22 0 -25" material="seats_blue" />
  145 |     <geom name="portal_1st_1" type="box" size="1.8 1.5 2.2" pos="30 15 2.2" euler="0 0 -25" material="entry_tunnel" />
  146 |     <geom name="portal_1st_2" type="box" size="1.8 1.5 2.2" pos="34 25 3.2" euler="0 0 -25" material="entry_tunnel" />
  147 |     <geom name="stand_3rd_lower" type="box" size="10 30 3.0" pos="-32 20 3.0" euler="-12 0 25" material="seats_navy" />
  148 |     <geom name="stand_3rd_upper" type="box" size="12 35 6.0" pos="-50 18 10.0" euler="-22 0 25" material="seats_red" />
  149 |     <geom name="portal_3rd_1" type="box" size="1.8 1.5 2.2" pos="-30 15 2.2" euler="0 0 25" material="entry_tunnel" />
  150 |     <geom name="portal_3rd_2" type="box" size="1.8 1.5 2.2" pos="-34 25 3.2" euler="0 0 25" material="entry_tunnel" />
  151 |     <geom name="stand_home_grand" type="box" size="18 8.0 5.0" pos="0 -12 6.0" euler="-25 0 0" material="seats_navy" />
  152 |     <geom name="portal_home_center" type="box" size="2.5 1.5 2.5" pos="0 -10 3.5" material="entry_tunnel" />
  153 |     <body name="pitcher_placeholder" pos="0 18.44 0">
  154 |       <geom type="capsule" size="0.2 0.8" pos="0 0 0.8" material="seats_red" />
  155 |     </body>
  156 |     <camera name="pitcher_cam" pos="0 20.0 2.0" euler="90 0 180" fovy="60" />
  157 |     <camera name="catcher_cam" pos="0 -2.0 1.2" euler="90 0 0" fovy="60" />
  158 |     <camera name="broadcaster_cam" pos="0 -10.0 8.0" euler="65 0 0" fovy="50" />
  159 |     <camera name="top_down_cam" pos="0 9.0 25.0" euler="0 0 0" fovy="70" />
  160 |     <body name="baseball" pos="0 18.44 1.8">
  161 |       <freejoint name="ball_joint" />
  162 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" condim="3" friction="0.3 0.05 0.05" solref="0.015 1" />
  163 |     </body>
  164 |     <body name="fielder_cf" pos="0 60 0.5">
  165 |       <joint name="cf_slide_x" type="slide" axis="1 0 0" damping="50" armature="1.0" />
  166 |       <joint name="cf_slide_y" type="slide" axis="0 1 0" damping="50" armature="1.0" />
  167 |       <geom name="cf_base" type="cylinder" size="0.3 0.2" material="seats_blue" mass="30.0" contype="0" conaffinity="0" />
  168 |       <geom name="cf_head" type="sphere" size="0.15" pos="0 0 1.0" material="plate_mat" mass="5.0" contype="0" conaffinity="0" />
  169 |       <body name="cf_arm" pos="0 -0.3 0.8">
  170 |         <joint name="cf_arm_pitch" type="hinge" axis="1 0 0" range="-45 45" damping="2.0" armature="0.1" />
  171 |         <geom name="cf_glove" type="sphere" size="0.2" material="wood" mass="2.0" condim="3" friction="1.0 0.5 0.5" />
  172 |       </body>
  173 |     </body>
  174 |     <body name="torso" pos="0.6 -0.1 1.2" childclass="body">
  175 |       <camera name="back" pos="-3 0 1" xyaxes="0 -1 0 1 0 2" mode="trackcom" />
  176 |       <camera name="side" pos="0 -3 1" xyaxes="1 0 0 0 1 2" mode="trackcom" />
  177 |       <geom name="torso" fromto="0 -.07 0 0 .07 0" size=".07" />
  178 |       <geom name="waist_upper" fromto="-.01 -.06 -.12 -.01 .06 -.12" size=".06" />
  179 |       <body name="head" pos="0 0 .19">
  180 |         <geom name="head" type="sphere" size=".09" />
  181 |         <camera name="batter_cam" pos="0.1 0 0" euler="90 0 90" fovy="75" />
  182 |       </body>
  183 |       <body name="waist_lower" pos="-.01 0 -.26">
  184 |         <geom name="waist_lower" fromto="0 -.06 0 0 .06 0" size=".06" />
  185 |         <joint name="abdomen_z" pos="0 0 .065" axis="0 0 1" range="-45 45" class="joint_big_stiff" />
  186 |         <joint name="abdomen_y" pos="0 0 .065" axis="0 1 0" range="-75 30" class="joint_big" />
  187 |         <body name="pelvis" pos="0 0 -.165">
  188 |           <joint name="abdomen_x" pos="0 0 .1" axis="1 0 0" range="-35 35" class="joint_big" />
  189 |           <geom name="butt" fromto="-.02 -.07 0 -.02 .07 0" size=".09" />
  190 |           <body name="thigh_right" pos="0 -.1 -.04">
  191 |             <joint name="hip_x_right" axis="1 0 0" class="hip_x" />
  192 |             <joint name="hip_z_right" axis="0 0 1" class="hip_z" />
  193 |             <joint name="hip_y_right" class="hip_y" />
  194 |             <geom name="thigh_right" fromto="0 0 0 0 .01 -.34" class="thigh" />
  195 |             <body name="shin_right" pos="0 .01 -.4">
  196 |               <joint name="knee_right" class="knee" />
  197 |               <geom name="shin_right" class="shin" />
  198 |               <body name="foot_right" pos="0 0 -.39">
  199 |                 <joint name="ankle_y_right" class="ankle_y" />
  200 |                 <joint name="ankle_x_right" class="ankle_x" axis="1 0 .5" />
  201 |                 <geom name="foot1_right" class="foot1" />
  202 |                 <geom name="foot2_right" class="foot2" />
  203 |               </body>
  204 |             </body>
  205 |           </body>
  206 |           <body name="thigh_left" pos="0 .1 -.04">
  207 |             <joint name="hip_x_left" axis="-1 0 0" class="hip_x" />
  208 |             <joint name="hip_z_left" axis="0 0 -1" class="hip_z" />
  209 |             <joint name="hip_y_left" class="hip_y" />
  210 |             <geom name="thigh_left" fromto="0 0 0 0 -.01 -.34" class="thigh" />
  211 |             <body name="shin_left" pos="0 -.01 -.4">
  212 |               <joint name="knee_left" class="knee" />
  213 |               <geom name="shin_left" fromto="0 0 0 0 0 -.3" class="shin" />
  214 |               <body name="foot_left" pos="0 0 -.39">
  215 |                 <joint name="ankle_y_left" class="ankle_y" />
  216 |                 <joint name="ankle_x_left" class="ankle_x" axis="-1 0 -.5" />
  217 |                 <geom name="foot1_left" class="foot1" />
  218 |                 <geom name="foot2_left" class="foot2" />
  219 |               </body>
  220 |             </body>
  221 |           </body>
  222 |         </body>
  223 |       </body>
  224 |       <body name="upper_arm_right" pos="0 -.17 .06">
  225 |         <joint name="shoulder1_right" axis="2 1 1" class="shoulder" />
  226 |         <joint name="shoulder2_right" axis="0 -1 1" class="shoulder" />
  227 |         <geom name="upper_arm_right" fromto="0 0 0 .16 -.16 -.16" class="arm_upper" />
  228 |         <body name="lower_arm_right" pos=".18 -.18 -.18">
  229 |           <joint name="elbow_right" axis="0 -1 1" class="elbow" />
  230 |           <geom name="lower_arm_right" fromto=".01 .01 .01 .17 .17 .17" class="arm_lower" />
  231 |           <body name="hand_right" pos=".18 .18 .18">
  232 |             <geom name="hand_right" zaxis="1 1 1" class="hand" />
  233 |             <body name="bat" pos="0.1 0 0" euler="0 90 0">
  234 |               <geom name="bat_knob" type="cylinder" size="0.025 0.015" pos="0 0.015 0" euler="90 0 0" material="wood" mass="0.05" />
  235 |               <geom name="bat_handle" type="cylinder" size="0.014 0.2" pos="0 0.2 0" euler="90 0 0" material="wood" mass="0.25" />
  236 |               <geom name="bat_taper" type="capsule" size="0.024 0.1" pos="0 0.45 0" euler="90 0 0" material="wood" mass="0.2" />
  237 |               <geom name="bat_barrel" type="cylinder" size="0.034 0.25" pos="0 0.675 0" euler="90 0 0" material="wood" mass="0.5" condim="3" friction="0.6 0.1 0.1" solref="0.015 1" />
  238 |             </body>
  239 |           </body>
  240 |         </body>
  241 |       </body>
  242 |       <body name="upper_arm_left" pos="0 .17 .06">
  243 |         <joint name="shoulder1_left" axis="-2 1 -1" class="shoulder" />
  244 |         <joint name="shoulder2_left" axis="0 -1 -1" class="shoulder" />
  245 |         <geom name="upper_arm_left" fromto="0 0 0 .16 .16 -.16" class="arm_upper" />
  246 |         <body name="lower_arm_left" pos=".18 .18 -.18">
  247 |           <joint name="elbow_left" axis="0 -1 -1" class="elbow" />
  248 |           <geom name="lower_arm_left" fromto=".01 -.01 .01 .17 -.17 .17" class="arm_lower" />
  249 |           <body name="hand_left" pos=".18 -.18 .18">
  250 |             <geom name="hand_left" zaxis="1 -1 1" class="hand" />
  251 |           </body>
  252 |         </body>
  253 |       </body>
  254 |     </body>
  255 |   </worldbody>
  256 |   <actuator>
  257 |     <motor joint="cf_slide_x" ctrlrange="-200 200" gear="1.0" />
  258 |     <motor joint="cf_slide_y" ctrlrange="-200 200" gear="1.0" />
  259 |     <motor joint="cf_arm_pitch" ctrlrange="-50 50" gear="1.0" />
  260 |     <motor name="abdomen_z" gear="40" joint="abdomen_z" />
  261 |     <motor name="abdomen_y" gear="40" joint="abdomen_y" />
  262 |     <motor name="abdomen_x" gear="40" joint="abdomen_x" />
  263 |     <motor name="hip_x_right" gear="40" joint="hip_x_right" />
  264 |     <motor name="hip_z_right" gear="40" joint="hip_z_right" />
  265 |     <motor name="hip_y_right" gear="120" joint="hip_y_right" />
  266 |     <motor name="knee_right" gear="80" joint="knee_right" />
  267 |     <motor name="ankle_y_right" gear="20" joint="ankle_y_right" />
  268 |     <motor name="ankle_x_right" gear="20" joint="ankle_x_right" />
  269 |     <motor name="hip_x_left" gear="40" joint="hip_x_left" />
  270 |     <motor name="hip_z_left" gear="40" joint="hip_z_left" />
  271 |     <motor name="hip_y_left" gear="120" joint="hip_y_left" />
  272 |     <motor name="knee_left" gear="80" joint="knee_left" />
  273 |     <motor name="ankle_y_left" gear="20" joint="ankle_y_left" />
  274 |     <motor name="ankle_x_left" gear="20" joint="ankle_x_left" />
  275 |     <motor name="shoulder1_right" gear="20" joint="shoulder1_right" />
  276 |     <motor name="shoulder2_right" gear="20" joint="shoulder2_right" />
  277 |     <motor name="elbow_right" gear="40" joint="elbow_right" />
  278 |     <motor name="shoulder1_left" gear="20" joint="shoulder1_left" />
  279 |     <motor name="shoulder2_left" gear="20" joint="shoulder2_left" />
  280 |     <motor name="elbow_left" gear="40" joint="elbow_left" />
  281 |   </actuator>
  282 |   <contact>
  283 |     <exclude body1="waist_lower" body2="thigh_right" />
  284 |     <exclude body1="waist_lower" body2="thigh_left" />
  285 |   </contact>
  286 |   <tendon>
  287 |     <fixed name="hamstring_right" limited="true" range="-0.3 2">
  288 |       <joint joint="hip_y_right" coef=".5" />
  289 |       <joint joint="knee_right" coef="-.5" />
  290 |     </fixed>
  291 |     <fixed name="hamstring_left" limited="true" range="-0.3 2">
  292 |       <joint joint="hip_y_left" coef=".5" />
  293 |       <joint joint="knee_left" coef="-.5" />
  294 |     </fixed>
  295 |   </tendon>
  296 | </mujoco>
````
