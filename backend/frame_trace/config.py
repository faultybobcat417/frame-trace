from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    data_dir: Path = ROOT / "data"
    database_path: Path = ROOT / "data" / "frame_trace.sqlite3"
    model_dir: Path = ROOT / "models" / "weights"
    demo_dir: Path = ROOT / "demo"
    detection_threshold: float = 0.88
    minimum_face_size: int = 40
    cluster_eps: float = 0.33
    cluster_min_samples: int = 2
    membership_floor: float = 0.58
    ambiguity_margin: float = 0.05
    video_sample_seconds: float = 1.0

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
