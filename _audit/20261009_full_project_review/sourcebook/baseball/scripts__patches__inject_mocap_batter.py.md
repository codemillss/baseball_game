# baseball/scripts/patches/inject_mocap_batter.py

원본: [scripts/patches/inject_mocap_batter.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/inject_mocap_batter.py)

SHA256: `e958a944ae0597a10f1363390d7b83caedf36f83538a515595bab3b36050b992`

전체 80행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import re
    2 | 
    3 | with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    4 |     content = f.read()
    5 | 
    6 | # Replace Pitcher Joints
    7 | new_p_joints = """self.p_joint_names = [
    8 |             "p_left_hip_yaw", "p_left_hip_roll", "p_left_hip_pitch", "p_left_knee", "p_left_ankle",
    9 |             "p_right_hip_yaw", "p_right_hip_roll", "p_right_hip_pitch", "p_right_knee", "p_right_ankle",
   10 |             "p_torso",
   11 |             "p_left_shoulder_pitch", "p_left_shoulder_roll", "p_left_shoulder_yaw", "p_left_elbow",
   12 |             "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"
   13 |         ]"""
   14 | content = re.sub(r'self\.p_joint_names = \[\s*"p_torso".*?\]', new_p_joints, content, flags=re.DOTALL)
   15 | 
   16 | # Replace Pitcher Keyframes
   17 | new_p_keyframes = """self.p_base_keyframes = np.zeros((6, 19))
   18 |         def set_pkf(idx, **kwargs):
   19 |             for k, v in kwargs.items():
   20 |                 j_idx = self.p_joint_names.index("p_" + k)
   21 |                 self.p_base_keyframes[idx, j_idx] = v
   22 |         set_pkf(0, torso=-1.57, left_elbow=1.5, right_elbow=1.5)
   23 |         set_pkf(1, torso=-1.57, left_hip_pitch=-1.5, left_knee=1.8, left_elbow=1.5, right_elbow=1.5)
   24 |         set_pkf(2, torso=-1.57, left_hip_pitch=-0.5, left_knee=0.2, left_shoulder_pitch=-0.5, left_elbow=0.5, right_shoulder_pitch=-1.0, right_shoulder_roll=-1.0, right_elbow=0.5)
   25 |         set_pkf(3, torso=-0.5, left_hip_pitch=0.0, left_knee=0.2, left_shoulder_pitch=-1.5, left_elbow=0.2, right_shoulder_pitch=-2.0, right_shoulder_roll=-1.5, right_shoulder_yaw=1.0, right_elbow=1.5)
   26 |         set_pkf(4, torso=0.5, left_hip_pitch=0.0, left_knee=0.1, left_shoulder_pitch=1.0, left_elbow=0.5, right_shoulder_pitch=1.5, right_shoulder_roll=-0.2, right_shoulder_yaw=0.0, right_elbow=0.1, right_hip_pitch=0.5)
   27 |         set_pkf(5, torso=1.2, left_hip_pitch=0.0, left_knee=0.3, left_shoulder_pitch=1.5, left_elbow=1.0, right_shoulder_pitch=2.2, right_shoulder_roll=-1.0, right_shoulder_yaw=-0.5, right_elbow=0.5, right_hip_pitch=1.0, right_knee=1.0)"""
   28 | content = re.sub(r'self\.p_base_keyframes = np\.array\(\[.*?\]\)', new_p_keyframes, content, flags=re.DOTALL)
   29 | 
   30 | # Replace Batter Joints
   31 | new_b_joints = """self.b_joint_names = [
   32 |             "b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle",
   33 |             "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle",
   34 |             "b_torso",
   35 |             "b_left_shoulder_pitch", "b_left_shoulder_roll", "b_left_shoulder_yaw", "b_left_elbow",
   36 |             "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"
   37 |         ]"""
   38 | content = re.sub(r'self\.b_joint_names = \[.*?\]', new_b_joints, content, flags=re.DOTALL)
   39 | 
   40 | # Replace Batter Keyframes
   41 | # 6 frames: Stance, Load, Stride, HipTurn, Contact, FollowThrough
   42 | new_b_keyframes = """self.b_base_keyframes = np.zeros((6, 19))
   43 |         def set_bkf(idx, **kwargs):
   44 |             for k, v in kwargs.items():
   45 |                 j_idx = self.b_joint_names.index("b_" + k)
   46 |                 self.b_base_keyframes[idx, j_idx] = v
   47 |         # Stance (Load) - weight on back leg (right knee slightly bent)
   48 |         set_bkf(0, torso=0.5, right_knee=0.3, left_shoulder_pitch=0.2, left_elbow=2.0, right_shoulder_pitch=-0.2, right_elbow=1.8)
   49 |         # Leg Kick / Tap
   50 |         set_bkf(1, torso=0.8, left_hip_pitch=-0.5, left_knee=0.5, right_knee=0.4, left_shoulder_pitch=0.2, left_elbow=2.0, right_shoulder_pitch=-0.2, right_elbow=1.8)
   51 |         # Stride
   52 |         set_bkf(2, torso=0.8, left_hip_pitch=-0.2, left_knee=0.2, right_knee=0.4, left_shoulder_pitch=0.3, left_elbow=1.8, right_shoulder_pitch=-0.3, right_elbow=1.6)
   53 |         # Hip Turn (Torso rotates to -0.5, bat lag - shoulders stay back slightly)
   54 |         set_bkf(3, torso=-0.2, left_hip_pitch=0.0, left_knee=0.1, right_knee=0.2, left_shoulder_pitch=0.5, left_shoulder_roll=-1.0, left_elbow=1.2, right_shoulder_pitch=-0.5, right_elbow=1.0)
   55 |         # Contact
   56 |         set_bkf(4, torso=-1.0, left_hip_pitch=0.0, left_knee=0.0, right_knee=0.1, left_shoulder_pitch=1.5, left_shoulder_roll=-1.5, left_elbow=0.2, right_shoulder_pitch=-1.0, right_elbow=0.2)
   57 |         # Follow Through
   58 |         set_bkf(5, torso=-1.5, left_hip_pitch=0.0, left_knee=0.0, right_knee=0.0, left_shoulder_pitch=2.0, left_shoulder_roll=-0.5, left_elbow=1.5, right_shoulder_pitch=-0.5, right_elbow=1.5)"""
   59 | content = re.sub(r'self\.b_base_keyframes = np\.array\(\[.*?\]\)', new_b_keyframes, content, flags=re.DOTALL)
   60 | 
   61 | # In step(), update aim indices for Pitcher
   62 | content = content.replace("self.p_current_keyframes[2:, 0] += p_x_aim", "self.p_current_keyframes[2:, 10] += p_x_aim")
   63 | content = content.replace("self.p_current_keyframes[2:, 1] += p_z_aim", "self.p_current_keyframes[2:, 15] += p_z_aim")
   64 | content = content.replace("self.p_current_keyframes[2:, 2] -= p_x_aim * 0.5", "self.p_current_keyframes[2:, 16] -= p_x_aim * 0.5")
   65 | 
   66 | # In step(), update aim indices for Batter
   67 | # self.b_current_keyframes[3, 0] += b_torso_adj -> b_torso is index 10
   68 | # self.b_current_keyframes[4, 0] += b_torso_adj -> b_torso is index 10
   69 | # self.b_current_keyframes[3, 1] += b_pitch_adj -> left_shoulder_pitch is index 11?
   70 | # Wait, let's see what index 1 was in original b_base_keyframes.
   71 | # Original: "b_torso", "b_right_shoulder_pitch" (1), "b_right_shoulder_roll" (2), "b_right_shoulder_yaw" (3), "b_right_elbow" (4)
   72 | # Actually, the original just added to index 1 which was right_shoulder_pitch. 
   73 | # But in our new MoCap form, we'll just add it to b_torso (10) and right_shoulder_pitch (15) and left_shoulder_pitch (11).
   74 | content = content.replace("self.b_current_keyframes[3, 0] += b_torso_adj", "self.b_current_keyframes[3, 10] += b_torso_adj")
   75 | content = content.replace("self.b_current_keyframes[4, 0] += b_torso_adj", "self.b_current_keyframes[4, 10] += b_torso_adj")
   76 | content = content.replace("self.b_current_keyframes[3, 1] += b_pitch_adj", "self.b_current_keyframes[3, 15] += b_pitch_adj; self.b_current_keyframes[3, 11] -= b_pitch_adj")
   77 | content = content.replace("self.b_current_keyframes[4, 1] += b_pitch_adj", "self.b_current_keyframes[4, 15] += b_pitch_adj; self.b_current_keyframes[4, 11] -= b_pitch_adj")
   78 | 
   79 | with open("cognitive_ai/envs/baseball_match_env.py", "w") as f:
   80 |     f.write(content)
````
