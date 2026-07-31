import json
import os
from pathlib import Path
from typing import Dict, Any

class DashboardLogger:
    def __init__(self, log_dir: str = "logs", video_dir: str = "videos"):
        self.log_dir = Path(log_dir)
        self.video_dir = Path(video_dir)
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.video_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats_file = self.log_dir / "training_stats.json"
        self.video_file = self.video_dir / "video_manifest.json"
        
        # Initialize stats if not exist
        if not self.stats_file.exists():
            self._write_json(self.stats_file, {"episodes": [], "metrics": {}})
            
        # Initialize video manifest if not exist
        if not self.video_file.exists():
            self._write_json(self.video_file, {"videos": []})

    def _read_json(self, filepath: Path) -> Dict[str, Any]:
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_json(self, filepath: Path, data: Dict[str, Any]):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def log_episode_stats(self, episode: int, stats: Dict[str, float]):
        """Logs episode metrics like Contact Rate, Loss, Reward."""
        data = self._read_json(self.stats_file)
        
        if "episodes" not in data:
            data["episodes"] = []
            
        record = {"episode": episode}
        record.update(stats)
        
        data["episodes"].append(record)
        
        # Keep only the last 500 episodes to prevent huge files
        if len(data["episodes"]) > 500:
            data["episodes"] = data["episodes"][-500:]
            
        self._write_json(self.stats_file, data)

    def log_video(self, episode: int, stage: int, filename: str):
        """Logs a newly recorded video."""
        data = self._read_json(self.video_file)
        
        if "videos" not in data:
            data["videos"] = []
            
        # Add new video to the front (latest first)
        data["videos"].insert(0, {
            "episode": episode,
            "stage": stage,
            "filename": filename
        })
        
        # Keep only the last 20 videos
        if len(data["videos"]) > 20:
            data["videos"] = data["videos"][:20]
            
        self._write_json(self.video_file, data)
