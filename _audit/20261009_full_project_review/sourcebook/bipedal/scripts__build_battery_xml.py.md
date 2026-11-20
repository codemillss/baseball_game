# bipedal/scripts/build_battery_xml.py

원본: [scripts/build_battery_xml.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/bipedal_baseball/scripts/build_battery_xml.py)

SHA256: `af36ae4ee5990bc66f73a5571ba04db77934614ffba09c3e5a858c6f3c7c1da7`

전체 174행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import re
    2 | 
    3 | # Read h1_infield_defense.xml
    4 | with open("models/h1_infield_defense.xml", "r") as f:
    5 |     xml = f.read()
    6 | 
    7 | # Let's extract:
    8 | # 1. header and asset
    9 | # 2. worldbody basics (ground, home_plate, pitcher_mound, pitcher_rubber, strike_zone, baseball)
   10 | # 3. p_pelvis (pitcher)
   11 | # 4. c_pelvis (converted from b_pelvis)
   12 | # 5. actuators for p_ and c_
   13 | # 6. excludes for p_ and c_
   14 | 
   15 | # Let's inspect the bodies in h1_infield_defense.xml
   16 | # p_pelvis starts at: <body name="p_pelvis"
   17 | # b_pelvis starts at: <body name="b_pelvis"
   18 | # f_pelvis starts at: <body name="f_pelvis"
   19 | 
   20 | p_start = xml.find('<body name="p_pelvis"')
   21 | b_start = xml.find('<body name="b_pelvis"')
   22 | f_start = xml.find('<body name="f_pelvis"')
   23 | 
   24 | # p_pelvis goes from p_start to b_start
   25 | p_body = xml[p_start:b_start]
   26 | 
   27 | # b_body goes from b_start to f_start
   28 | b_body = xml[b_start:f_start]
   29 | 
   30 | # Convert b_body to c_body
   31 | c_body = b_body.replace('b_', 'c_')
   32 | 
   33 | # In c_body, set initial position to x=0.0, y=-0.95, z=0.52, quat facing pitcher (facing +y)
   34 | # quat="0.7071068 0 0 0.7071068" rotates 90 deg CCW around Z axis
   35 | c_body = re.sub(
   36 |     r'<body name="c_pelvis" pos="[^"]*"[^>]*>',
   37 |     '<body name="c_pelvis" pos="0.0 -0.95 0.52" quat="0.7071068 0 0 0.7071068" childclass="h1">',
   38 |     c_body
   39 | )
   40 | 
   41 | # Replace held bat in c_body with c_mitt on left arm!
   42 | # Note: in b_body, held_bat was on b_right_elbow_link.
   43 | # In baseball, a catcher catches with the LEFT hand!
   44 | # So we remove held bat from right arm, and add c_mitt to c_left_elbow_link.
   45 | 
   46 | # Remove held bat from right arm:
   47 | c_body = re.sub(
   48 |     r'<body name="c_held_bat".*?</body>\s*</geom>',
   49 |     '</geom>',
   50 |     c_body,
   51 |     flags=re.DOTALL
   52 | )
   53 | # If held bat was inside c_right_elbow_link:
   54 | c_body = re.sub(
   55 |     r'<body name="c_held_bat".*?</body>',
   56 |     '',
   57 |     c_body,
   58 |     flags=re.DOTALL
   59 | )
   60 | 
   61 | # Add c_mitt to c_left_elbow_link:
   62 | mitt_xml = '''
   63 |         <body name="c_mitt" pos="0.22 0 0" quat="0.7071068 0 0.7071068 0">
   64 |           <geom name="c_mitt_geom" type="cylinder" size="0.14 0.04" pos="0 0 0" material="glove_mat" mass="0.45" contype="0" conaffinity="0" />
   65 |           <site name="c_mitt_site" type="sphere" size="0.05" pos="0 0 0" rgba="0.9 0.4 0.1 0.6" />
   66 |         </body>
   67 | '''
   68 | 
   69 | # Insert mitt_xml inside c_left_elbow_link before its closing </body>
   70 | # Find c_left_elbow_link
   71 | idx = c_body.find('<body name="c_left_elbow_link"')
   72 | # Find the next </body> for c_left_elbow_link
   73 | idx2 = c_body.find('</body>', idx)
   74 | c_body = c_body[:idx2] + mitt_xml + c_body[idx2:]
   75 | 
   76 | # Now extract actuators for p_ and b_ (rename b_ -> c_)
   77 | act_start = xml.find('<actuator>')
   78 | act_end = xml.find('</actuator>') + len('</actuator>')
   79 | act_xml = xml[act_start:act_end]
   80 | 
   81 | # Filter actuators: keep p_ and b_ (rename b_ -> c_), discard f_
   82 | act_lines = []
   83 | for line in act_xml.splitlines():
   84 |     if 'name="f_' in line or 'joint="f_' in line:
   85 |         continue
   86 |     act_lines.append(line.replace('name="b_', 'name="c_').replace('joint="b_', 'joint="c_'))
   87 | new_act_xml = '\n'.join(act_lines)
   88 | 
   89 | # Also ensure left arm motors exist for c_
   90 | if 'c_left_elbow' not in new_act_xml:
   91 |     left_arm_motors = '''
   92 |     <motor class="h1" name="c_left_shoulder_pitch" joint="c_left_shoulder_pitch" ctrlrange="-40 40" />
   93 |     <motor class="h1" name="c_left_shoulder_roll" joint="c_left_shoulder_roll" ctrlrange="-40 40" />
   94 |     <motor class="h1" name="c_left_shoulder_yaw" joint="c_left_shoulder_yaw" ctrlrange="-18 18" />
   95 |     <motor class="h1" name="c_left_elbow" joint="c_left_elbow" ctrlrange="-18 18" />
   96 | '''
   97 |     new_act_xml = new_act_xml.replace('</actuator>', left_arm_motors + '\n  </actuator>')
   98 | 
   99 | # Now extract contact / equality / exclude
  100 | contact_start = xml.find('<contact>')
  101 | if contact_start >= 0:
  102 |     contact_end = xml.find('</equality>') + len('</equality>') if '</equality>' in xml else xml.find('</contact>') + len('</contact>')
  103 |     # Let's clean up pair geoms: keep ball and mitt pair, remove held_bat pair
  104 |     contact_xml = '''  <contact>
  105 |     <pair geom1="c_mitt_geom" geom2="ball_geom" solref="0.005 1" solimp="0.80 0.90 0.001 0.5 2" friction="0.8 0.02 0.001" />
  106 |   </contact>
  107 |   <equality>
  108 |     <weld name="pitch_weld" body1="baseball" body2="p_right_elbow_link" relpose="0.25 0 0 1 0 0 0" active="false" />
  109 |   </equality>'''
  110 | else:
  111 |     contact_xml = ''
  112 | 
  113 | # Excludes: keep p_ and convert b_ -> c_, discard f_
  114 | exclude_start = xml.find('<contact>') if xml.find('<contact>') >= 0 else xml.find('<actuator>')
  115 | # Actually excludes are inside <contact> or after worldbody
  116 | # In h1_infield_defense.xml, let's see where excludes are:
  117 | ex_lines = []
  118 | for line in xml.splitlines():
  119 |     if '<exclude ' in line:
  120 |         if 'f_' in line:
  121 |             continue
  122 |         ex_lines.append(line.replace('b_', 'c_'))
  123 | 
  124 | all_excludes = '\n    '.join(ex_lines)
  125 | 
  126 | # Cameras for battery duel:
  127 | cameras_xml = '''
  128 |     <camera name="battery_broadcast_cam" pos="-3.8 4.8 2.6" xyaxes="0.78 -0.62 0 0.28 0.35 0.89" fovy="58" />
  129 |     <camera name="umpire_cam" pos="0.0 -2.4 1.4" xyaxes="1 0 0 0 0.35 0.94" fovy="48" />
  130 |     <camera name="pitcher_cam" pos="0.0 11.5 1.8" xyaxes="-1 0 0 0 -0.22 0.97" fovy="50" />
  131 |     <camera name="catcher_closeup" pos="-1.5 -0.5 1.2" xyaxes="0.7071 -0.7071 0 0.35 0.35 0.87" fovy="45" />
  132 | '''
  133 | 
  134 | # Strike zone site: center z=0.85m (standard belt-high strike zone, width=0.43m, height=0.40m)
  135 | worldbody_prefix = f'''  <worldbody>
  136 |     <light directional="true" diffuse="0.85 0.85 0.85" specular="0.25 0.25 0.25" pos="2 5 14" dir="0 0 -1" />
  137 |     <light directional="true" diffuse="0.45 0.45 0.45" pos="-5 -5 10" dir="1 1 -1" />
  138 |     <geom name="ground" type="plane" size="50 50 0.1" material="matplane" />
  139 |     <geom name="home_plate" type="box" size="0.216 0.216 0.005" pos="0 0 0.005" material="home_plate_mat" contype="0" conaffinity="0" />
  140 |     <geom name="pitcher_mound" type="cylinder" size="1.2 0.01" pos="0 10.0 0.005" material="home_plate_mat" contype="0" conaffinity="0" />
  141 |     <geom name="pitcher_rubber" type="box" size="0.30 0.07 0.008" pos="0 10.0 0.015" material="home_plate_mat" contype="0" conaffinity="0" />
  142 |     <geom name="catcher_box" type="box" size="0.50 0.60 0.002" pos="0 -0.95 0.002" rgba="0.8 0.8 0.8 0.25" contype="0" conaffinity="0" />
  143 |     <site name="strike_zone" type="box" size="0.216 0.02 0.20" pos="0 0 0.85" material="strike_zone_mat" />
  144 |     <site name="pitch_target_point" type="sphere" size="0.04" pos="0 0.0 0.85" rgba="0.9 0.2 0.2 0.4" />
  145 | {cameras_xml}
  146 |     <body name="baseball" pos="0 10.0 1.48">
  147 |       <freejoint name="ball_joint" />
  148 |       <geom name="ball_geom" type="sphere" size="0.037" mass="0.145" material="ball_mat" solref="0.002 1" solimp="0.95 0.99 0.001 0.5 2" friction="0.4 0.02 0.001" />
  149 |       <site name="ball_site" pos="0 0 0" size="0.01" />
  150 |     </body>
  151 | '''
  152 | 
  153 | # Assets & Header:
  154 | header_and_asset = xml[:xml.find('<worldbody>')]
  155 | 
  156 | final_xml = f'''{header_and_asset}
  157 | {worldbody_prefix}
  158 | {p_body}
  159 | {c_body}
  160 |   </worldbody>
  161 |   <contact>
  162 |     {all_excludes}
  163 |     <pair geom1="c_mitt_geom" geom2="ball_geom" solref="0.005 1" solimp="0.80 0.90 0.001 0.5 2" friction="0.8 0.02 0.001" />
  164 |   </contact>
  165 |   <equality>
  166 |     <weld name="pitch_weld" body1="baseball" body2="p_right_elbow_link" relpose="0.25 0 0 1 0 0 0" active="false" />
  167 |   </equality>
  168 | {new_act_xml}
  169 | </mujoco>'''
  170 | 
  171 | with open("models/h1_battery_pitch_catch.xml", "w") as f:
  172 |     f.write(final_xml)
  173 | 
  174 | print("Saved models/h1_battery_pitch_catch.xml successfully.")
````
