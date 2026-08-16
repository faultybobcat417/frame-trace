from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class DetectedFace:
    bbox: tuple[float, float, float, float]
    confidence: float
    landmarks: list[tuple[float, float]]
    raw: np.ndarray


class YuNetFaceDetector:
    def __init__(self, model_path: Path, score_threshold: float = 0.88, nms_threshold: float = 0.3, top_k: int = 5000):
        if not Path(model_path).exists():
            raise FileNotFoundError(f"YuNet model missing: {model_path}")
        self.detector = cv2.FaceDetectorYN.create(
            str(model_path), "", (320, 320), score_threshold, nms_threshold, top_k
        )

    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        if image is None or image.ndim != 3:
            raise ValueError("expected a BGR image")
        height, width = image.shape[:2]
        self.detector.setInputSize((width, height))
        _, faces = self.detector.detect(image)
        if faces is None:
            return []
        results: list[DetectedFace] = []
        for row in faces:
            x, y, w, h = [float(v) for v in row[:4]]
            landmarks = [(float(row[i]), float(row[i + 1])) for i in range(4, 14, 2)]
            results.append(DetectedFace((x, y, w, h), float(row[-1]), landmarks, row.copy()))
        return results


class SFaceEmbedder:
    def __init__(self, model_path: Path):
        if not Path(model_path).exists():
            raise FileNotFoundError(f"SFace model missing: {model_path}")
        self.recognizer = cv2.FaceRecognizerSF.create(str(model_path), "")

    def embed(self, image: np.ndarray, face: DetectedFace) -> np.ndarray:
        aligned = self.recognizer.alignCrop(image, face.raw)
        feature = self.recognizer.feature(aligned).reshape(-1).astype(np.float32)
        norm = float(np.linalg.norm(feature))
        if norm == 0:
            raise ValueError("SFace returned a zero embedding")
        return feature / norm
