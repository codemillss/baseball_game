# baseball/archive/training/logger.py

원본: [archive/training/logger.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/training/logger.py)

SHA256: `f40b8cd2312fdbd1fa1cd3c0d5aa9a03fed719e7a156553222d73b1ec2db292e`

전체 72행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `DashboardLogger` | ClassDef | 6 | 72 |
| `__init__` | FunctionDef | 7 | 23 |
| `_read_json` | FunctionDef | 25 | 30 |
| `_write_json` | FunctionDef | 32 | 34 |
| `log_episode_stats` | FunctionDef | 36 | 52 |
| `log_video` | FunctionDef | 54 | 72 |

## 전체 원문

````text
    1 | import json
    2 | import os
    3 | from pathlib import Path
    4 | from typing import Dict, Any
    5 | 
    6 | class DashboardLogger:
    7 |     def __init__(self, log_dir: str = "logs", video_dir: str = "videos"):
    8 |         self.log_dir = Path(log_dir)
    9 |         self.video_dir = Path(video_dir)
   10 |         
   11 |         self.log_dir.mkdir(parents=True, exist_ok=True)
   12 |         self.video_dir.mkdir(parents=True, exist_ok=True)
   13 |         
   14 |         self.stats_file = self.log_dir / "training_stats.json"
   15 |         self.video_file = self.video_dir / "video_manifest.json"
   16 |         
   17 |         # Initialize stats if not exist
   18 |         if not self.stats_file.exists():
   19 |             self._write_json(self.stats_file, {"episodes": [], "metrics": {}})
   20 |             
   21 |         # Initialize video manifest if not exist
   22 |         if not self.video_file.exists():
   23 |             self._write_json(self.video_file, {"videos": []})
   24 | 
   25 |     def _read_json(self, filepath: Path) -> Dict[str, Any]:
   26 |         try:
   27 |             with open(filepath, "r") as f:
   28 |                 return json.load(f)
   29 |         except (FileNotFoundError, json.JSONDecodeError):
   30 |             return {}
   31 | 
   32 |     def _write_json(self, filepath: Path, data: Dict[str, Any]):
   33 |         with open(filepath, "w") as f:
   34 |             json.dump(data, f, indent=2)
   35 | 
   36 |     def log_episode_stats(self, episode: int, stats: Dict[str, float]):
   37 |         """Logs episode metrics like Contact Rate, Loss, Reward."""
   38 |         data = self._read_json(self.stats_file)
   39 |         
   40 |         if "episodes" not in data:
   41 |             data["episodes"] = []
   42 |             
   43 |         record = {"episode": episode}
   44 |         record.update(stats)
   45 |         
   46 |         data["episodes"].append(record)
   47 |         
   48 |         # Keep only the last 500 episodes to prevent huge files
   49 |         if len(data["episodes"]) > 500:
   50 |             data["episodes"] = data["episodes"][-500:]
   51 |             
   52 |         self._write_json(self.stats_file, data)
   53 | 
   54 |     def log_video(self, episode: int, stage: int, filename: str):
   55 |         """Logs a newly recorded video."""
   56 |         data = self._read_json(self.video_file)
   57 |         
   58 |         if "videos" not in data:
   59 |             data["videos"] = []
   60 |             
   61 |         # Add new video to the front (latest first)
   62 |         data["videos"].insert(0, {
   63 |             "episode": episode,
   64 |             "stage": stage,
   65 |             "filename": filename
   66 |         })
   67 |         
   68 |         # Keep only the last 20 videos
   69 |         if len(data["videos"]) > 20:
   70 |             data["videos"] = data["videos"][:20]
   71 |             
   72 |         self._write_json(self.video_file, data)
````
