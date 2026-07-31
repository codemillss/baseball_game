import cv2
import os
import glob
from pathlib import Path

def convert_mp4v_to_h264_or_gif():
    video_files = glob.glob("videos/*.mp4")
    print(f"Found {len(video_files)} video files to re-encode...")

    for v_path in video_files:
        cap = cv2.VideoCapture(v_path)
        if not cap.isOpened():
            continue

        frames = []
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()

        if not frames:
            continue

        # Re-write with 'avc1' (H.264) or 'XVID' or 'VP80'
        # Try avc1 first, fallback to mp4v if not available
        temp_out = v_path + ".tmp.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        out = cv2.VideoWriter(temp_out, fourcc, fps, (width, height))

        if not out.isOpened():
            # Fallback to VP80 for WebM or H264
            fourcc = cv2.VideoWriter_fourcc(*"H264")
            out = cv2.VideoWriter(temp_out, fourcc, fps, (width, height))

        for f in frames:
            out.write(f)
        out.release()

        if os.path.exists(temp_out) and os.path.getsize(temp_out) > 0:
            os.replace(temp_out, v_path)
            print(f"Successfully re-encoded: {v_path}")

if __name__ == "__main__":
    convert_mp4v_to_h264_or_gif()
