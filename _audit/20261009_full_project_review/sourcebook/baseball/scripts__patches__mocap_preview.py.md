# baseball/scripts/patches/mocap_preview.py

원본: [scripts/patches/mocap_preview.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/mocap_preview.py)

SHA256: `80f7018f496b9ecd0b94eeac8c45b78389db948104eb16972f1f0f184953b9f2`

전체 110행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `set_kf` | FunctionDef | 22 | 25 |

## 전체 원문

````text
    1 | import mujoco
    2 | import numpy as np
    3 | import cv2
    4 | import imageio_ffmpeg
    5 | import os
    6 | from scipy.interpolate import CubicSpline
    7 | 
    8 | # Joint order mapping
    9 | JOINT_NAMES = [
   10 |     "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
   11 |     "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
   12 |     "torso",
   13 |     "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
   14 |     "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"
   15 | ]
   16 | 
   17 | # Define Pro Pitching Keyframes (Ohtani Style High-Leg Kick)
   18 | # 6 Keyframes, 19 joints each
   19 | # Note: pitch < 0 is lifting leg up for hip, knee > 0 is bending
   20 | keyframes = np.zeros((6, 19))
   21 | 
   22 | def set_kf(idx, **kwargs):
   23 |     for k, v in kwargs.items():
   24 |         j_idx = JOINT_NAMES.index(k)
   25 |         keyframes[idx, j_idx] = v
   26 | 
   27 | # KF 0: Set Position (Side Stance)
   28 | set_kf(0, torso=-1.57, left_elbow=1.5, right_elbow=1.5)
   29 | 
   30 | # KF 1: High Leg Kick
   31 | set_kf(1, torso=-1.57, left_hip_pitch=-1.5, left_knee=1.8, 
   32 |        left_elbow=1.5, right_elbow=1.5)
   33 | 
   34 | # KF 2: Stride & Hand Separation
   35 | set_kf(2, torso=-1.57, left_hip_pitch=-0.5, left_knee=0.2,
   36 |        left_shoulder_pitch=-0.5, left_elbow=0.5,
   37 |        right_shoulder_pitch=-1.0, right_shoulder_roll=-1.0, right_elbow=0.5)
   38 | 
   39 | # KF 3: Foot Plant & Arm Cocking (Max External Rotation)
   40 | set_kf(3, torso=-0.5, left_hip_pitch=0.0, left_knee=0.2,
   41 |        left_shoulder_pitch=-1.5, left_elbow=0.2,
   42 |        right_shoulder_pitch=-2.0, right_shoulder_roll=-1.5, right_shoulder_yaw=1.0, right_elbow=1.5)
   43 | 
   44 | # KF 4: Acceleration & Release
   45 | set_kf(4, torso=0.5, left_hip_pitch=0.0, left_knee=0.1,
   46 |        left_shoulder_pitch=1.0, left_elbow=0.5,
   47 |        right_shoulder_pitch=1.5, right_shoulder_roll=-0.2, right_shoulder_yaw=0.0, right_elbow=0.1,
   48 |        right_hip_pitch=0.5)
   49 | 
   50 | # KF 5: Follow-through
   51 | set_kf(5, torso=1.2, left_hip_pitch=0.0, left_knee=0.3,
   52 |        left_shoulder_pitch=1.5, left_elbow=1.0,
   53 |        right_shoulder_pitch=2.2, right_shoulder_roll=-1.0, right_shoulder_yaw=-0.5, right_elbow=0.5,
   54 |        right_hip_pitch=1.0, right_knee=1.0)
   55 | 
   56 | # Times for each keyframe (in seconds)
   57 | times = np.array([0.0, 0.5, 0.9, 1.1, 1.25, 1.6])
   58 | 
   59 | # Interpolate smoothly using CubicSpline
   60 | cs = CubicSpline(times, keyframes, axis=0, bc_type='clamped')
   61 | 
   62 | # Setup MuJoCo
   63 | model = mujoco.MjModel.from_xml_path("shared_assets/h1_pitcher.xml")
   64 | data = mujoco.MjData(model)
   65 | 
   66 | renderer = mujoco.Renderer(model, 480, 640)
   67 | camera = mujoco.MjvCamera()
   68 | camera.azimuth = 140
   69 | camera.elevation = -10
   70 | camera.distance = 4.0
   71 | camera.lookat[:] = [0, 10.0, 1.0]
   72 | 
   73 | fps = 30
   74 | dt = 1.0 / fps
   75 | total_frames = int(times[-1] * fps)
   76 | 
   77 | video_path = "mocap_preview_temp.mp4"
   78 | fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   79 | writer = cv2.VideoWriter(video_path, fourcc, fps, (640, 480))
   80 | 
   81 | # Kinematic playback (Dry-run)
   82 | for i in range(total_frames + 30): # extra 30 frames to pause at end
   83 |     t = min(i * dt, times[-1])
   84 |     q_target = cs(t)
   85 |     
   86 |     # Manually set joint positions (ignoring physics to just preview kinematics)
   87 |     for j_name in JOINT_NAMES:
   88 |         j_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, j_name)
   89 |         q_adr = model.jnt_qposadr[j_id]
   90 |         data.qpos[q_adr] = q_target[JOINT_NAMES.index(j_name)]
   91 |         
   92 |     mujoco.mj_forward(model, data)
   93 |     
   94 |     renderer.update_scene(data, camera=camera)
   95 |     frame = renderer.render()
   96 |     writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
   97 | 
   98 | writer.release()
   99 | 
  100 | # Convert to H.264
  101 | ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
  102 | final_path = "/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7/mocap_preview.mp4"
  103 | cmd = [
  104 |     ffmpeg_exe, "-y", "-i", video_path,
  105 |     "-c:v", "libx264", "-pix_fmt", "yuv420p",
  106 |     final_path
  107 | ]
  108 | os.system(f"{ffmpeg_exe} -y -i {video_path} -c:v libx264 -pix_fmt yuv420p {final_path} >/dev/null 2>&1")
  109 | os.remove(video_path)
  110 | print(f"Generated {final_path}")
````
