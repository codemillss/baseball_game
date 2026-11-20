# baseball/scripts/patches/inject_mocap_pitcher.py

원본: [scripts/patches/inject_mocap_pitcher.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/inject_mocap_pitcher.py)

SHA256: `4305d5b40bb22207d50cbf43b546ad54eadb074b1dfb1666eb825cd6898795cf`

전체 40행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import re
    2 | 
    3 | with open("cognitive_ai/envs/pitcher_env.py", "r") as f:
    4 |     content = f.read()
    5 | 
    6 | # Replace joint names
    7 | new_joints = """self.joint_names = [
    8 |             "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
    9 |             "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
   10 |             "torso",
   11 |             "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
   12 |             "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"
   13 |         ]"""
   14 | content = re.sub(r'self\.joint_names = \[\s*"torso".*?\]', new_joints, content, flags=re.DOTALL)
   15 | 
   16 | # Replace base_keyframes
   17 | new_keyframes = """self.base_keyframes = np.zeros((6, 19))
   18 |         def set_kf(idx, **kwargs):
   19 |             for k, v in kwargs.items():
   20 |                 j_idx = self.joint_names.index(k)
   21 |                 self.base_keyframes[idx, j_idx] = v
   22 |         set_kf(0, torso=-1.57, left_elbow=1.5, right_elbow=1.5)
   23 |         set_kf(1, torso=-1.57, left_hip_pitch=-1.5, left_knee=1.8, left_elbow=1.5, right_elbow=1.5)
   24 |         set_kf(2, torso=-1.57, left_hip_pitch=-0.5, left_knee=0.2, left_shoulder_pitch=-0.5, left_elbow=0.5, right_shoulder_pitch=-1.0, right_shoulder_roll=-1.0, right_elbow=0.5)
   25 |         set_kf(3, torso=-0.5, left_hip_pitch=0.0, left_knee=0.2, left_shoulder_pitch=-1.5, left_elbow=0.2, right_shoulder_pitch=-2.0, right_shoulder_roll=-1.5, right_shoulder_yaw=1.0, right_elbow=1.5)
   26 |         set_kf(4, torso=0.5, left_hip_pitch=0.0, left_knee=0.1, left_shoulder_pitch=1.0, left_elbow=0.5, right_shoulder_pitch=1.5, right_shoulder_roll=-0.2, right_shoulder_yaw=0.0, right_elbow=0.1, right_hip_pitch=0.5)
   27 |         set_kf(5, torso=1.2, left_hip_pitch=0.0, left_knee=0.3, left_shoulder_pitch=1.5, left_elbow=1.0, right_shoulder_pitch=2.2, right_shoulder_roll=-1.0, right_shoulder_yaw=-0.5, right_elbow=0.5, right_hip_pitch=1.0, right_knee=1.0)"""
   28 | 
   29 | content = re.sub(r'self\.base_keyframes = np\.array\(\[.*?\]\)', new_keyframes, content, flags=re.DOTALL)
   30 | 
   31 | # In step(), update aim indices
   32 | # self.current_keyframes[2:, 0] += x_aim -> torso is index 10
   33 | # self.current_keyframes[2:, 1] += z_aim -> right_shoulder_pitch is index 15
   34 | # self.current_keyframes[2:, 2] -= x_aim * 0.5 -> right_shoulder_roll is index 16
   35 | content = content.replace("self.current_keyframes[2:, 0] += x_aim", "self.current_keyframes[2:, 10] += x_aim")
   36 | content = content.replace("self.current_keyframes[2:, 1] += z_aim", "self.current_keyframes[2:, 15] += z_aim")
   37 | content = content.replace("self.current_keyframes[2:, 2] -= x_aim * 0.5", "self.current_keyframes[2:, 16] -= x_aim * 0.5")
   38 | 
   39 | with open("cognitive_ai/envs/pitcher_env.py", "w") as f:
   40 |     f.write(content)
````
