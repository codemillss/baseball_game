import mujoco
import numpy as np
import cv2
import imageio_ffmpeg
import os
from scipy.interpolate import CubicSpline

# Joint order mapping
JOINT_NAMES = [
    "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
    "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
    "torso",
    "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
    "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"
]

# Define Pro Pitching Keyframes (Ohtani Style High-Leg Kick)
# 6 Keyframes, 19 joints each
# Note: pitch < 0 is lifting leg up for hip, knee > 0 is bending
keyframes = np.zeros((6, 19))

def set_kf(idx, **kwargs):
    for k, v in kwargs.items():
        j_idx = JOINT_NAMES.index(k)
        keyframes[idx, j_idx] = v

# KF 0: Set Position (Side Stance)
set_kf(0, torso=-1.57, left_elbow=1.5, right_elbow=1.5)

# KF 1: High Leg Kick
set_kf(1, torso=-1.57, left_hip_pitch=-1.5, left_knee=1.8, 
       left_elbow=1.5, right_elbow=1.5)

# KF 2: Stride & Hand Separation
set_kf(2, torso=-1.57, left_hip_pitch=-0.5, left_knee=0.2,
       left_shoulder_pitch=-0.5, left_elbow=0.5,
       right_shoulder_pitch=-1.0, right_shoulder_roll=-1.0, right_elbow=0.5)

# KF 3: Foot Plant & Arm Cocking (Max External Rotation)
set_kf(3, torso=-0.5, left_hip_pitch=0.0, left_knee=0.2,
       left_shoulder_pitch=-1.5, left_elbow=0.2,
       right_shoulder_pitch=-2.0, right_shoulder_roll=-1.5, right_shoulder_yaw=1.0, right_elbow=1.5)

# KF 4: Acceleration & Release
set_kf(4, torso=0.5, left_hip_pitch=0.0, left_knee=0.1,
       left_shoulder_pitch=1.0, left_elbow=0.5,
       right_shoulder_pitch=1.5, right_shoulder_roll=-0.2, right_shoulder_yaw=0.0, right_elbow=0.1,
       right_hip_pitch=0.5)

# KF 5: Follow-through
set_kf(5, torso=1.2, left_hip_pitch=0.0, left_knee=0.3,
       left_shoulder_pitch=1.5, left_elbow=1.0,
       right_shoulder_pitch=2.2, right_shoulder_roll=-1.0, right_shoulder_yaw=-0.5, right_elbow=0.5,
       right_hip_pitch=1.0, right_knee=1.0)

# Times for each keyframe (in seconds)
times = np.array([0.0, 0.5, 0.9, 1.1, 1.25, 1.6])

# Interpolate smoothly using CubicSpline
cs = CubicSpline(times, keyframes, axis=0, bc_type='clamped')

# Setup MuJoCo
model = mujoco.MjModel.from_xml_path("shared_assets/h1_pitcher.xml")
data = mujoco.MjData(model)

renderer = mujoco.Renderer(model, 480, 640)
camera = mujoco.MjvCamera()
camera.azimuth = 140
camera.elevation = -10
camera.distance = 4.0
camera.lookat[:] = [0, 10.0, 1.0]

fps = 30
dt = 1.0 / fps
total_frames = int(times[-1] * fps)

video_path = "mocap_preview_temp.mp4"
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
writer = cv2.VideoWriter(video_path, fourcc, fps, (640, 480))

# Kinematic playback (Dry-run)
for i in range(total_frames + 30): # extra 30 frames to pause at end
    t = min(i * dt, times[-1])
    q_target = cs(t)
    
    # Manually set joint positions (ignoring physics to just preview kinematics)
    for j_name in JOINT_NAMES:
        j_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, j_name)
        q_adr = model.jnt_qposadr[j_id]
        data.qpos[q_adr] = q_target[JOINT_NAMES.index(j_name)]
        
    mujoco.mj_forward(model, data)
    
    renderer.update_scene(data, camera=camera)
    frame = renderer.render()
    writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

writer.release()

# Convert to H.264
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
final_path = "/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/mocap_preview.mp4"
cmd = [
    ffmpeg_exe, "-y", "-i", video_path,
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    final_path
]
os.system(f"{ffmpeg_exe} -y -i {video_path} -c:v libx264 -pix_fmt yuv420p {final_path} >/dev/null 2>&1")
os.remove(video_path)
print(f"Generated {final_path}")
