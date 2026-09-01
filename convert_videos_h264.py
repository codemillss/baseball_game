import os
import subprocess
import imageio_ffmpeg

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

dirs_to_convert = [
    "/Users/jin10000/Desktop/mini-project/baseball/data/eval_videos",
    "/Users/jin10000/.gemini/antigravity/brain/3b74ebd0-a1ce-4525-b312-c5db96bec2d7"
]

for d in dirs_to_convert:
    for f in os.listdir(d):
        if f.endswith(".mp4") and not f.endswith("_h264.mp4"):
            src_path = os.path.join(d, f)
            tmp_path = os.path.join(d, f.replace(".mp4", "_h264.mp4"))
            print(f"Converting {src_path} -> H.264...")
            cmd = [
                ffmpeg_exe, "-y", "-i", src_path,
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                tmp_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode == 0:
                os.replace(tmp_path, src_path)
                print(f" Successfully converted {f} to H.264 (yuv420p)")
            else:
                print(f" Failed to convert {f}: {res.stderr.decode()[:200]}")

print("All video conversions completed!")
