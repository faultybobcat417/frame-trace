from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from frame_trace.clustering import DBSCANClusterEngine
from frame_trace.config import Settings
from frame_trace.cv import SFaceEmbedder, VisionPipeline, YuNetFaceDetector, model_fingerprint
from frame_trace.ingest import FolderAdapter, ManifestPackageAdapter, sha256_file
from frame_trace.persistence import Database


class VisionIngestService:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings

    def import_path(self, path: Path) -> dict:
        path = Path(path).expanduser().resolve()
        adapter = ManifestPackageAdapter() if (path / "manifest.json").exists() else FolderAdapter()
        assets = adapter.discover(path)
        yunet = self.settings.model_dir / "face_detection_yunet_2023mar.onnx"
        sface = self.settings.model_dir / "face_recognition_sface_2021dec.onnx"
        detector = YuNetFaceDetector(yunet, self.settings.detection_threshold)
        embedder = SFaceEmbedder(sface)
        pipeline = VisionPipeline(detector, embedder, self.settings.video_sample_seconds)
        model_sha = model_fingerprint(sface)
        crop_dir = self.settings.data_dir / "crops"
        crop_dir.mkdir(parents=True, exist_ok=True)

        detection_ids: list[str] = []
        vectors: list[np.ndarray] = []
        detection_meta: dict[str, tuple[str, float, str | None]] = {}
        source_seen: set[str] = set()
        imported_assets = 0
        skipped_duplicates = 0

        for item in assets:
            if item.source_id not in source_seen:
                self.db.execute(
                    "INSERT OR IGNORE INTO sources(id,name,source_type,platform_label,handle_label) VALUES(?,?,?,?,?)",
                    (item.source_id, item.source_name, "authorized_import", None, None),
                )
                source_seen.add(item.source_id)
            sha = sha256_file(item.path)
            if self.db.one("SELECT id FROM assets WHERE sha256=?", (sha,)):
                skipped_duplicates += 1
                continue
            asset_id = f"A-{sha[:16]}"
            self.db.execute(
                "INSERT INTO assets(id,source_id,kind,filename,sha256,captured_at,caption,duration_seconds) VALUES(?,?,?,?,?,?,?,?)",
                (asset_id, item.source_id, item.kind, item.path.name, sha, item.captured_at, item.caption, None),
            )
            imported_assets += 1
            try:
                records = pipeline.process_image(item.path) if item.kind == "image" else pipeline.process_video(item.path)
            except ValueError:
                continue
            by_frame: dict[tuple[int, float], list] = defaultdict(list)
            for record in records:
                by_frame[(record.frame_index, record.timestamp_seconds)].append(record)
            for (frame_index, timestamp), frame_records in by_frame.items():
                image = self._load_frame(item.path, item.kind, frame_index)
                if image is None:
                    continue
                h, w = image.shape[:2]
                frame_id = f"F-{asset_id}-{frame_index}"
                self.db.execute(
                    "INSERT OR IGNORE INTO frames(id,asset_id,frame_index,timestamp_seconds,width,height) VALUES(?,?,?,?,?,?)",
                    (frame_id, asset_id, frame_index, timestamp, w, h),
                )
                for local_idx, record in enumerate(frame_records):
                    detection_id = f"D-{asset_id}-{frame_index}-{local_idx}"
                    crop_rel = self._save_crop(image, record.bbox, crop_dir, detection_id)
                    self.db.execute(
                        "INSERT INTO detections(id,frame_id,bbox_json,confidence,landmarks_json,crop_path) VALUES(?,?,?,?,?,?)",
                        (detection_id, frame_id, json.dumps(record.bbox), record.detection_confidence, "[]", crop_rel),
                    )
                    vector = record.embedding.astype(np.float32)
                    self.db.execute(
                        "INSERT INTO embeddings(detection_id,model_id,model_sha256,dimension,normalization,vector_blob) VALUES(?,?,?,?,?,?)",
                        (detection_id, "sface-2021dec", model_sha, len(vector), "l2", vector.tobytes()),
                    )
                    detection_ids.append(detection_id)
                    vectors.append(vector)
                    detection_meta[detection_id] = (asset_id, timestamp, crop_rel)

        if vectors:
            engine = DBSCANClusterEngine(
                eps=self.settings.cluster_eps,
                min_samples=self.settings.cluster_min_samples,
                membership_floor=self.settings.membership_floor,
            )
            assignments = engine.fit(detection_ids, np.vstack(vectors))
            cluster_personas: dict[int, str] = {}
            for assignment in assignments:
                persona_id = None
                if assignment.cluster_id is not None:
                    persona_id = cluster_personas.setdefault(
                        assignment.cluster_id,
                        f"P-{hashlib.sha1(f'{path}:{assignment.cluster_id}'.encode()).hexdigest()[:8].upper()}",
                    )
                    self.db.execute(
                        "INSERT OR IGNORE INTO personas(id,label,hidden,status,representative_detection_id) VALUES(?,?,?,?,?)",
                        (persona_id, None, 0, assignment.state, assignment.item_id),
                    )
                self.db.execute(
                    "INSERT OR REPLACE INTO memberships(detection_id,persona_id,state,similarity,method,cluster_run_id) VALUES(?,?,?,?,?,?)",
                    (assignment.item_id, persona_id, assignment.state, assignment.similarity_to_medoid, "machine", "authorized-import"),
                )
            self._build_appearances()

        return {
            "discovered_assets": len(assets),
            "imported_assets": imported_assets,
            "skipped_duplicates": skipped_duplicates,
            "detections": len(detection_ids),
            "personas": len(self.db.query("SELECT id FROM personas")),
        }

    def _build_appearances(self) -> None:
        self.db.execute("DELETE FROM appearances WHERE id LIKE 'AP-CV-%'")
        rows = self.db.query(
            """
            SELECT m.persona_id, f.asset_id, MIN(f.timestamp_seconds) start_seconds,
                   MAX(f.timestamp_seconds) end_seconds, MIN(d.id) representative_detection_id,
                   AVG(m.similarity) confidence
            FROM memberships m
            JOIN detections d ON d.id=m.detection_id
            JOIN frames f ON f.id=d.frame_id
            WHERE m.persona_id IS NOT NULL AND m.state IN ('accepted','review_required')
            GROUP BY m.persona_id,f.asset_id
            """
        )
        for row in rows:
            appearance_id = f"AP-CV-{row['persona_id']}-{row['asset_id']}"
            self.db.execute(
                "INSERT OR REPLACE INTO appearances(id,persona_id,asset_id,start_seconds,end_seconds,representative_detection_id,confidence) VALUES(?,?,?,?,?,?,?)",
                (appearance_id, row["persona_id"], row["asset_id"], row["start_seconds"], row["end_seconds"], row["representative_detection_id"], row["confidence"]),
            )

    @staticmethod
    def _load_frame(path: Path, kind: str, frame_index: int):
        if kind == "image":
            return cv2.imread(str(path))
        cap = cv2.VideoCapture(str(path))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()
        cap.release()
        return frame if ok else None

    @staticmethod
    def _save_crop(image: np.ndarray, bbox: tuple[float, float, float, float], crop_dir: Path, detection_id: str) -> str | None:
        x, y, w, h = [int(round(v)) for v in bbox]
        ih, iw = image.shape[:2]
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(iw, x + w), min(ih, y + h)
        if x1 <= x0 or y1 <= y0:
            return None
        crop = image[y0:y1, x0:x1]
        target = crop_dir / f"{detection_id}.jpg"
        if not cv2.imwrite(str(target), crop):
            return None
        return f"local-artifacts/crops/{target.name}"
