# baseball/archive/legacy_scripts/convert_videos.py

원본: [archive/legacy_scripts/convert_videos.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_scripts/convert_videos.py)

SHA256: `a35ee34ae64175374e4e3958e3670bff405bfadce839f3b697489ba53b2e5ad7`

전체 50행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `convert_mp4v_to_h264_or_gif` | FunctionDef | 6 | 47 |

## 전체 원문

````text
    1 | import cv2
    2 | import os
    3 | import glob
    4 | from pathlib import Path
    5 | 
    6 | def convert_mp4v_to_h264_or_gif():
    7 |     video_files = glob.glob("videos/*.mp4")
    8 |     print(f"Found {len(video_files)} video files to re-encode...")
    9 | 
   10 |     for v_path in video_files:
   11 |         cap = cv2.VideoCapture(v_path)
   12 |         if not cap.isOpened():
   13 |             continue
   14 | 
   15 |         frames = []
   16 |         fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
   17 |         width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
   18 |         height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
   19 | 
   20 |         while True:
   21 |             ret, frame = cap.read()
   22 |             if not ret:
   23 |                 break
   24 |             frames.append(frame)
   25 |         cap.release()
   26 | 
   27 |         if not frames:
   28 |             continue
   29 | 
   30 |         # Re-write with 'avc1' (H.264) or 'XVID' or 'VP80'
   31 |         # Try avc1 first, fallback to mp4v if not available
   32 |         temp_out = v_path + ".tmp.mp4"
   33 |         fourcc = cv2.VideoWriter_fourcc(*"avc1")
   34 |         out = cv2.VideoWriter(temp_out, fourcc, fps, (width, height))
   35 | 
   36 |         if not out.isOpened():
   37 |             # Fallback to VP80 for WebM or H264
   38 |             fourcc = cv2.VideoWriter_fourcc(*"H264")
   39 |             out = cv2.VideoWriter(temp_out, fourcc, fps, (width, height))
   40 | 
   41 |         for f in frames:
   42 |             out.write(f)
   43 |         out.release()
   44 | 
   45 |         if os.path.exists(temp_out) and os.path.getsize(temp_out) > 0:
   46 |             os.replace(temp_out, v_path)
   47 |             print(f"Successfully re-encoded: {v_path}")
   48 | 
   49 | if __name__ == "__main__":
   50 |     convert_mp4v_to_h264_or_gif()
````
