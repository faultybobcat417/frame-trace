from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .models import SFaceEmbedder, YuNetFaceDetector


@dataclass(frozen=True)
class VisionRecord:
    asset_path: str
    frame_index: int
    timestamp_seconds: float
    bbox: tuple[float, float, float, float]
    detection_confidence: float
    embedding: np.ndarray


class VisionPipeline:
    def __init__(self, detector: YuNetFaceDetector, embedder: SFaceEmbedder, sample_seconds: float = 1.0):
        self.detector = detector
        self.embedder = embedder
        self.sample_seconds = max(0.1, sample_seconds)

    def process_image(self, path: Path) -> list[VisionRecord]:
        image = cv2.imread(str(path))
        if image is None:
            raise ValueError(f"unable to decode image: {path}")
        return self._process_frame(path, image, 0, 0.0)

    def process_video(self, path: Path) -> list[VisionRecord]:
        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise ValueError(f"unable to decode video: {path}")
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        stride = max(1, int(round(fps * self.sample_seconds))) if fps > 0 else 1
        records: list[VisionRecord] = []
        frame_index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % stride == 0:
                timestamp = frame_index / fps if fps > 0 else float(frame_index)
                records.extend(self._process_frame(path, frame, frame_index, timestamp))
            frame_index += 1
        capture.release()
        return records

    def _process_frame(self, path: Path, image: np.ndarray, frame_index: int, timestamp: float) -> list[VisionRecord]:
        out: list[VisionRecord] = []
        for face in self.detector.detect(image):
            embedding = self.embedder.embed(image, face)
            out.append(VisionRecord(str(path), frame_index, timestamp, face.bbox, face.confidence, embedding))
        return out


def model_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
