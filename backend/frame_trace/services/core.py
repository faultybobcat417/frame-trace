from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from frame_trace.config import Settings
from frame_trace.demo import seed_demo
from frame_trace.graph import GraphProjector
from frame_trace.persistence import Database


class FrameTraceService:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings
        self.graph = GraphProjector(db)

    def seed_demo(self) -> dict:
        return seed_demo(self.db, self.settings.demo_dir)

    def list_personas(self) -> list[dict]:
        return self.db.query(
            """
            SELECT p.id, p.label, p.hidden, p.status, p.representative_detection_id,
                   COUNT(DISTINCT ap.id) appearance_count,
                   COUNT(DISTINCT a.source_id) source_count,
                   MIN(a.captured_at) first_seen,
                   MAX(a.captured_at) last_seen,
                   COALESCE(d.crop_path, '') representative_crop
            FROM personas p
            LEFT JOIN appearances ap ON ap.persona_id=p.id
            LEFT JOIN assets a ON a.id=ap.asset_id
            LEFT JOIN detections d ON d.id=p.representative_detection_id
            WHERE p.hidden=0
            GROUP BY p.id
            ORDER BY appearance_count DESC, p.id
            """
        )

    def persona_detail(self, persona_id: str) -> dict | None:
        rows = [p for p in self.list_personas() if p["id"] == persona_id]
        if not rows:
            return None
        item = rows[0]
        item["appearances"] = self.appearances(persona_id)
        item["neighbors"] = self.neighbors(persona_id)
        item["sources"] = self.db.query(
            """
            SELECT s.id, s.name, COUNT(*) appearance_count
            FROM appearances ap JOIN assets a ON a.id=ap.asset_id JOIN sources s ON s.id=a.source_id
            WHERE ap.persona_id=? GROUP BY s.id,s.name ORDER BY appearance_count DESC
            """,
            (persona_id,),
        )
        return item

    def update_persona(self, persona_id: str, label: str | None = None, hidden: bool | None = None) -> dict | None:
        current = self.db.one("SELECT * FROM personas WHERE id=?", (persona_id,))
        if not current:
            return None
        new_label = current["label"] if label is None else label
        new_hidden = current["hidden"] if hidden is None else int(hidden)
        self.db.execute("UPDATE personas SET label=?,hidden=? WHERE id=?", (new_label, new_hidden, persona_id))
        return self.db.one("SELECT * FROM personas WHERE id=?", (persona_id,))

    def appearances(self, persona_id: str) -> list[dict]:
        return self.db.query(
            """
            SELECT ap.*, a.filename, a.kind, a.captured_at, a.caption,
                   s.id source_id, s.name source_name, d.crop_path
            FROM appearances ap
            JOIN assets a ON a.id=ap.asset_id
            JOIN sources s ON s.id=a.source_id
            LEFT JOIN detections d ON d.id=ap.representative_detection_id
            WHERE ap.persona_id=? ORDER BY a.captured_at DESC
            """,
            (persona_id,),
        )

    def neighbors(self, persona_id: str) -> list[dict]:
        return self.db.query(
            """
            SELECT p2.id, p2.label, COUNT(DISTINCT ap2.asset_id) shared_asset_count,
                   MIN(a.captured_at) first_seen, MAX(a.captured_at) last_seen
            FROM appearances ap1
            JOIN appearances ap2 ON ap1.asset_id=ap2.asset_id AND ap1.persona_id<>ap2.persona_id
            JOIN personas p2 ON p2.id=ap2.persona_id
            JOIN assets a ON a.id=ap1.asset_id
            WHERE ap1.persona_id=?
            GROUP BY p2.id,p2.label ORDER BY shared_asset_count DESC
            """,
            (persona_id,),
        )

    def list_assets(self) -> list[dict]:
        return self.db.query(
            """
            SELECT a.*, s.name source_name,
                   COUNT(DISTINCT ap.persona_id) persona_count,
                   GROUP_CONCAT(DISTINCT ap.persona_id) persona_ids
            FROM assets a JOIN sources s ON s.id=a.source_id
            LEFT JOIN appearances ap ON ap.asset_id=a.id
            GROUP BY a.id ORDER BY a.captured_at DESC, a.id
            """
        )

    def asset_detail(self, asset_id: str) -> dict | None:
        asset = self.db.one("SELECT a.*,s.name source_name FROM assets a JOIN sources s ON s.id=a.source_id WHERE a.id=?", (asset_id,))
        if not asset:
            return None
        asset["detections"] = self.db.query(
            """
            SELECT d.*, m.persona_id, m.state, m.similarity, m.method
            FROM frames f JOIN detections d ON d.frame_id=f.id
            LEFT JOIN memberships m ON m.detection_id=d.id
            WHERE f.asset_id=? ORDER BY f.frame_index,d.id
            """,
            (asset_id,),
        )
        for detection in asset["detections"]:
            detection["bbox"] = json.loads(detection.pop("bbox_json"))
            detection["landmarks"] = json.loads(detection.pop("landmarks_json"))
        return asset

    def review_queue(self) -> list[dict]:
        return self.db.query(
            """
            SELECT m.detection_id, m.persona_id candidate_persona_id, m.similarity,
                   d.crop_path, a.id asset_id, a.filename, s.name source_name,
                   p.label candidate_label
            FROM memberships m
            JOIN detections d ON d.id=m.detection_id
            JOIN frames f ON f.id=d.frame_id
            JOIN assets a ON a.id=f.asset_id
            JOIN sources s ON s.id=a.source_id
            LEFT JOIN personas p ON p.id=m.persona_id
            WHERE m.state='review_required'
            ORDER BY m.similarity DESC
            """
        )

    def decide_review(self, detection_id: str, decision: str) -> dict:
        row = self.db.one("SELECT * FROM memberships WHERE detection_id=?", (detection_id,))
        if not row:
            raise KeyError(detection_id)
        if decision not in {"same", "different", "unknown"}:
            raise ValueError("decision must be same, different, or unknown")
        decision_id = f"R-{uuid.uuid4().hex[:12]}"
        self.db.execute(
            "INSERT INTO review_decisions(id,detection_id,candidate_persona_id,decision,similarity,created_at) VALUES(?,?,?,?,?,?)",
            (decision_id, detection_id, row["persona_id"], decision, row["similarity"], datetime.now(timezone.utc).isoformat()),
        )
        if decision == "same":
            self.db.execute("UPDATE memberships SET state='accepted',method='human' WHERE detection_id=?", (detection_id,))
        elif decision == "different":
            self.db.execute("UPDATE memberships SET persona_id=NULL,state='unassigned',method='human' WHERE detection_id=?", (detection_id,))
        return {"id": decision_id, "detection_id": detection_id, "decision": decision}

    def new_import_run(self, message: str = "Import queued") -> dict:
        run_id = f"I-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute("INSERT INTO import_runs(id,status,stage,progress,message,created_at) VALUES(?,?,?,?,?,?)", (run_id, "queued", "DISCOVER", 0.0, message, now))
        return self.import_run(run_id)

    def update_import_run(self, run_id: str, status: str, stage: str, progress: float, message: str) -> None:
        completed = datetime.now(timezone.utc).isoformat() if status in {"complete", "failed"} else None
        self.db.execute("UPDATE import_runs SET status=?,stage=?,progress=?,message=?,completed_at=? WHERE id=?", (status, stage, progress, message, completed, run_id))

    def import_run(self, run_id: str) -> dict | None:
        return self.db.one("SELECT * FROM import_runs WHERE id=?", (run_id,))
