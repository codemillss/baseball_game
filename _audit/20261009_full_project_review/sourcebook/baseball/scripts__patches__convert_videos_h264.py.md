# baseball/scripts/patches/convert_videos_h264.py

원본: [scripts/patches/convert_videos_h264.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/scripts/patches/convert_videos_h264.py)

SHA256: `0f57c91f6021ab84bac399c4b1f90165faf9d33823421b25d3c969717bae392a`

전체 31행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | import os
    2 | import subprocess
    3 | import imageio_ffmpeg
    4 | 
    5 | ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    6 | 
    7 | dirs_to_convert = [
    8 |     "/Users/jin10000/Desktop/mini-project/baseball/data/eval_videos",
    9 |     "/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7"
   10 | ]
   11 | 
   12 | for d in dirs_to_convert:
   13 |     for f in os.listdir(d):
   14 |         if f.endswith(".mp4") and not f.endswith("_h264.mp4"):
   15 |             src_path = os.path.join(d, f)
   16 |             tmp_path = os.path.join(d, f.replace(".mp4", "_h264.mp4"))
   17 |             print(f"Converting {src_path} -> H.264...")
   18 |             cmd = [
   19 |                 ffmpeg_exe, "-y", "-i", src_path,
   20 |                 "-c:v", "libx264", "-pix_fmt", "yuv420p",
   21 |                 "-movflags", "+faststart",
   22 |                 tmp_path
   23 |             ]
   24 |             res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   25 |             if res.returncode == 0:
   26 |                 os.replace(tmp_path, src_path)
   27 |                 print(f" Successfully converted {f} to H.264 (yuv420p)")
   28 |             else:
   29 |                 print(f" Failed to convert {f}: {res.stderr.decode()[:200]}")
   30 | 
   31 | print("All video conversions completed!")
````
