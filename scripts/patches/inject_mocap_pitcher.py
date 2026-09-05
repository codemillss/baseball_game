import re

with open("cognitive_ai/envs/pitcher_env.py", "r") as f:
    content = f.read()

# Replace joint names
new_joints = """self.joint_names = [
            "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
            "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
            "torso",
            "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
            "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"
        ]"""
content = re.sub(r'self\.joint_names = \[\s*"torso".*?\]', new_joints, content, flags=re.DOTALL)

# Replace base_keyframes
new_keyframes = """self.base_keyframes = np.zeros((6, 19))
        def set_kf(idx, **kwargs):
            for k, v in kwargs.items():
                j_idx = self.joint_names.index(k)
                self.base_keyframes[idx, j_idx] = v
        set_kf(0, torso=-1.57, left_elbow=1.5, right_elbow=1.5)
        set_kf(1, torso=-1.57, left_hip_pitch=-1.5, left_knee=1.8, left_elbow=1.5, right_elbow=1.5)
        set_kf(2, torso=-1.57, left_hip_pitch=-0.5, left_knee=0.2, left_shoulder_pitch=-0.5, left_elbow=0.5, right_shoulder_pitch=-1.0, right_shoulder_roll=-1.0, right_elbow=0.5)
        set_kf(3, torso=-0.5, left_hip_pitch=0.0, left_knee=0.2, left_shoulder_pitch=-1.5, left_elbow=0.2, right_shoulder_pitch=-2.0, right_shoulder_roll=-1.5, right_shoulder_yaw=1.0, right_elbow=1.5)
        set_kf(4, torso=0.5, left_hip_pitch=0.0, left_knee=0.1, left_shoulder_pitch=1.0, left_elbow=0.5, right_shoulder_pitch=1.5, right_shoulder_roll=-0.2, right_shoulder_yaw=0.0, right_elbow=0.1, right_hip_pitch=0.5)
        set_kf(5, torso=1.2, left_hip_pitch=0.0, left_knee=0.3, left_shoulder_pitch=1.5, left_elbow=1.0, right_shoulder_pitch=2.2, right_shoulder_roll=-1.0, right_shoulder_yaw=-0.5, right_elbow=0.5, right_hip_pitch=1.0, right_knee=1.0)"""

content = re.sub(r'self\.base_keyframes = np\.array\(\[.*?\]\)', new_keyframes, content, flags=re.DOTALL)

# In step(), update aim indices
# self.current_keyframes[2:, 0] += x_aim -> torso is index 10
# self.current_keyframes[2:, 1] += z_aim -> right_shoulder_pitch is index 15
# self.current_keyframes[2:, 2] -= x_aim * 0.5 -> right_shoulder_roll is index 16
content = content.replace("self.current_keyframes[2:, 0] += x_aim", "self.current_keyframes[2:, 10] += x_aim")
content = content.replace("self.current_keyframes[2:, 1] += z_aim", "self.current_keyframes[2:, 15] += z_aim")
content = content.replace("self.current_keyframes[2:, 2] -= x_aim * 0.5", "self.current_keyframes[2:, 16] -= x_aim * 0.5")

with open("cognitive_ai/envs/pitcher_env.py", "w") as f:
    f.write(content)
