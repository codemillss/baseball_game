import re

with open("cognitive_ai/envs/baseball_match_env.py", "r") as f:
    content = f.read()

# Replace Pitcher Joints
new_p_joints = """self.p_joint_names = [
            "p_left_hip_yaw", "p_left_hip_roll", "p_left_hip_pitch", "p_left_knee", "p_left_ankle",
            "p_right_hip_yaw", "p_right_hip_roll", "p_right_hip_pitch", "p_right_knee", "p_right_ankle",
            "p_torso",
            "p_left_shoulder_pitch", "p_left_shoulder_roll", "p_left_shoulder_yaw", "p_left_elbow",
            "p_right_shoulder_pitch", "p_right_shoulder_roll", "p_right_shoulder_yaw", "p_right_elbow"
        ]"""
content = re.sub(r'self\.p_joint_names = \[\s*"p_torso".*?\]', new_p_joints, content, flags=re.DOTALL)

# Replace Pitcher Keyframes
new_p_keyframes = """self.p_base_keyframes = np.zeros((6, 19))
        def set_pkf(idx, **kwargs):
            for k, v in kwargs.items():
                j_idx = self.p_joint_names.index("p_" + k)
                self.p_base_keyframes[idx, j_idx] = v
        set_pkf(0, torso=-1.57, left_elbow=1.5, right_elbow=1.5)
        set_pkf(1, torso=-1.57, left_hip_pitch=-1.5, left_knee=1.8, left_elbow=1.5, right_elbow=1.5)
        set_pkf(2, torso=-1.57, left_hip_pitch=-0.5, left_knee=0.2, left_shoulder_pitch=-0.5, left_elbow=0.5, right_shoulder_pitch=-1.0, right_shoulder_roll=-1.0, right_elbow=0.5)
        set_pkf(3, torso=-0.5, left_hip_pitch=0.0, left_knee=0.2, left_shoulder_pitch=-1.5, left_elbow=0.2, right_shoulder_pitch=-2.0, right_shoulder_roll=-1.5, right_shoulder_yaw=1.0, right_elbow=1.5)
        set_pkf(4, torso=0.5, left_hip_pitch=0.0, left_knee=0.1, left_shoulder_pitch=1.0, left_elbow=0.5, right_shoulder_pitch=1.5, right_shoulder_roll=-0.2, right_shoulder_yaw=0.0, right_elbow=0.1, right_hip_pitch=0.5)
        set_pkf(5, torso=1.2, left_hip_pitch=0.0, left_knee=0.3, left_shoulder_pitch=1.5, left_elbow=1.0, right_shoulder_pitch=2.2, right_shoulder_roll=-1.0, right_shoulder_yaw=-0.5, right_elbow=0.5, right_hip_pitch=1.0, right_knee=1.0)"""
content = re.sub(r'self\.p_base_keyframes = np\.array\(\[.*?\]\)', new_p_keyframes, content, flags=re.DOTALL)

# Replace Batter Joints
new_b_joints = """self.b_joint_names = [
            "b_left_hip_yaw", "b_left_hip_roll", "b_left_hip_pitch", "b_left_knee", "b_left_ankle",
            "b_right_hip_yaw", "b_right_hip_roll", "b_right_hip_pitch", "b_right_knee", "b_right_ankle",
            "b_torso",
            "b_left_shoulder_pitch", "b_left_shoulder_roll", "b_left_shoulder_yaw", "b_left_elbow",
            "b_right_shoulder_pitch", "b_right_shoulder_roll", "b_right_shoulder_yaw", "b_right_elbow"
        ]"""
content = re.sub(r'self\.b_joint_names = \[.*?\]', new_b_joints, content, flags=re.DOTALL)

# Replace Batter Keyframes
# 6 frames: Stance, Load, Stride, HipTurn, Contact, FollowThrough
new_b_keyframes = """self.b_base_keyframes = np.zeros((6, 19))
        def set_bkf(idx, **kwargs):
            for k, v in kwargs.items():
                j_idx = self.b_joint_names.index("b_" + k)
                self.b_base_keyframes[idx, j_idx] = v
        # Stance (Load) - weight on back leg (right knee slightly bent)
        set_bkf(0, torso=0.5, right_knee=0.3, left_shoulder_pitch=0.2, left_elbow=2.0, right_shoulder_pitch=-0.2, right_elbow=1.8)
        # Leg Kick / Tap
        set_bkf(1, torso=0.8, left_hip_pitch=-0.5, left_knee=0.5, right_knee=0.4, left_shoulder_pitch=0.2, left_elbow=2.0, right_shoulder_pitch=-0.2, right_elbow=1.8)
        # Stride
        set_bkf(2, torso=0.8, left_hip_pitch=-0.2, left_knee=0.2, right_knee=0.4, left_shoulder_pitch=0.3, left_elbow=1.8, right_shoulder_pitch=-0.3, right_elbow=1.6)
        # Hip Turn (Torso rotates to -0.5, bat lag - shoulders stay back slightly)
        set_bkf(3, torso=-0.2, left_hip_pitch=0.0, left_knee=0.1, right_knee=0.2, left_shoulder_pitch=0.5, left_shoulder_roll=-1.0, left_elbow=1.2, right_shoulder_pitch=-0.5, right_elbow=1.0)
        # Contact
        set_bkf(4, torso=-1.0, left_hip_pitch=0.0, left_knee=0.0, right_knee=0.1, left_shoulder_pitch=1.5, left_shoulder_roll=-1.5, left_elbow=0.2, right_shoulder_pitch=-1.0, right_elbow=0.2)
        # Follow Through
        set_bkf(5, torso=-1.5, left_hip_pitch=0.0, left_knee=0.0, right_knee=0.0, left_shoulder_pitch=2.0, left_shoulder_roll=-0.5, left_elbow=1.5, right_shoulder_pitch=-0.5, right_elbow=1.5)"""
content = re.sub(r'self\.b_base_keyframes = np\.array\(\[.*?\]\)', new_b_keyframes, content, flags=re.DOTALL)

# In step(), update aim indices for Pitcher
content = content.replace("self.p_current_keyframes[2:, 0] += p_x_aim", "self.p_current_keyframes[2:, 10] += p_x_aim")
content = content.replace("self.p_current_keyframes[2:, 1] += p_z_aim", "self.p_current_keyframes[2:, 15] += p_z_aim")
content = content.replace("self.p_current_keyframes[2:, 2] -= p_x_aim * 0.5", "self.p_current_keyframes[2:, 16] -= p_x_aim * 0.5")

# In step(), update aim indices for Batter
# self.b_current_keyframes[3, 0] += b_torso_adj -> b_torso is index 10
# self.b_current_keyframes[4, 0] += b_torso_adj -> b_torso is index 10
# self.b_current_keyframes[3, 1] += b_pitch_adj -> left_shoulder_pitch is index 11?
# Wait, let's see what index 1 was in original b_base_keyframes.
# Original: "b_torso", "b_right_shoulder_pitch" (1), "b_right_shoulder_roll" (2), "b_right_shoulder_yaw" (3), "b_right_elbow" (4)
# Actually, the original just added to index 1 which was right_shoulder_pitch. 
# But in our new MoCap form, we'll just add it to b_torso (10) and right_shoulder_pitch (15) and left_shoulder_pitch (11).
content = content.replace("self.b_current_keyframes[3, 0] += b_torso_adj", "self.b_current_keyframes[3, 10] += b_torso_adj")
content = content.replace("self.b_current_keyframes[4, 0] += b_torso_adj", "self.b_current_keyframes[4, 10] += b_torso_adj")
content = content.replace("self.b_current_keyframes[3, 1] += b_pitch_adj", "self.b_current_keyframes[3, 15] += b_pitch_adj; self.b_current_keyframes[3, 11] -= b_pitch_adj")
content = content.replace("self.b_current_keyframes[4, 1] += b_pitch_adj", "self.b_current_keyframes[4, 15] += b_pitch_adj; self.b_current_keyframes[4, 11] -= b_pitch_adj")

with open("cognitive_ai/envs/baseball_match_env.py", "w") as f:
    f.write(content)
