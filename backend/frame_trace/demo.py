from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from frame_trace.clustering import DBSCANClusterEngine, pairwise_metrics
from frame_trace.persistence import Database

PERSONAS = [
    ("P001", "Mira"), ("P002", "Theo"), ("P003", "Nadia"),
    ("P004", "Jonah"), ("P005", "Leila"), ("P006", "Sam")
]
SOURCES = [
    ("S001", "Northstar Studio"), ("S002", "Redwood Athletics"),
    ("S003", "Harbour Creative"), ("S004", "Atlas Events")
]


def _avatar_svg(persona_id: str, label: str, index: int) -> str:
    hues = [196, 18, 280, 145, 42, 330]
    hue = hues[index % len(hues)]
    initials = "".join(part[0] for part in label.split())[:2].upper()
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<defs><linearGradient id="g" x1="0" x2="1"><stop stop-color="hsl({hue} 65% 36%)"/><stop offset="1" stop-color="hsl({(hue+35)%360} 75% 20%)"/></linearGradient></defs>
<rect width="512" height="512" rx="72" fill="#0b0d12"/><circle cx="256" cy="205" r="92" fill="url(#g)"/>
<path d="M102 470c24-106 94-154 154-154s130 48 154 154" fill="url(#g)"/>
<text x="256" y="492" text-anchor="middle" fill="#e8edf6" font-size="28" font-family="system-ui">{persona_id} · {initials}</text>
</svg>'''


def build_demo_assets(root: Path) -> None:
    media = root / "media"
    media.mkdir(parents=True, exist_ok=True)
    for idx, (persona_id, label) in enumerate(PERSONAS):
        (media / f"{persona_id.lower()}.svg").write_text(_avatar_svg(persona_id, label, idx))
    manifest = {
        "note": "Deterministic logic fixture. SVG avatars are UI fixtures, not SFace outputs.",
        "personas": [p[0] for p in PERSONAS],
        "sources": [s[0] for s in SOURCES],
    }
    (root / "ground_truth.json").write_text(json.dumps(manifest, indent=2))


def _centers(seed: int = 17, dim: int = 64) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    centers: dict[str, np.ndarray] = {}
    for persona_id, _ in PERSONAS:
        v = rng.normal(size=dim).astype(np.float32)
        centers[persona_id] = v / np.linalg.norm(v)
    return centers


def synthetic_vectors(seed: int = 17, per_persona: int = 6) -> tuple[list[str], np.ndarray, dict[str, str]]:
    rng = np.random.default_rng(seed)
    centers = _centers(seed)
    ids: list[str] = []
    vectors: list[np.ndarray] = []
    truth: dict[str, str] = {}
    for persona_id, _ in PERSONAS:
        for j in range(per_persona):
            item_id = f"{persona_id}-D{j+1:02d}"
            v = centers[persona_id] + rng.normal(scale=0.055, size=centers[persona_id].shape)
            v = v.astype(np.float32)
            v /= np.linalg.norm(v)
            ids.append(item_id)
            vectors.append(v)
            truth[item_id] = persona_id
    # Two deliberately ambiguous detections are left outside any dense neighborhood.
    for j in range(2):
        item_id = f"AMB-D{j+1:02d}"
        v = rng.normal(size=64).astype(np.float32)
        v /= np.linalg.norm(v)
        ids.append(item_id)
        vectors.append(v)
        truth[item_id] = f"AMB{j+1}"
    return ids, np.vstack(vectors), truth


def seed_demo(db: Database, demo_root: Path) -> dict:
    db.reset()
    build_demo_assets(demo_root)
    now = datetime.now(timezone.utc)
    for source_id, name in SOURCES:
        db.execute("INSERT INTO sources(id,name,source_type,platform_label,handle_label) VALUES(?,?,?,?,?)", (source_id, name, "demo", "social export", f"@{name.lower().replace(' ', '')}"))
    for idx, (persona_id, label) in enumerate(PERSONAS):
        db.execute("INSERT INTO personas(id,label,hidden,status,representative_detection_id) VALUES(?,?,?,?,?)", (persona_id, label, 0, "accepted", f"{persona_id}-D01"))

    ids, vectors, truth = synthetic_vectors()
    engine = DBSCANClusterEngine(eps=0.22, min_samples=2, membership_floor=0.72)
    assignments = engine.fit(ids, vectors)
    predicted: dict[str, str | None] = {}
    label_to_persona: dict[int, str] = {}
    for assignment in assignments:
        if assignment.cluster_id is not None and assignment.cluster_id not in label_to_persona:
            index = len(label_to_persona)
            label_to_persona[assignment.cluster_id] = PERSONAS[index][0] if index < len(PERSONAS) else f"PX{index:03d}"
        predicted[assignment.item_id] = label_to_persona.get(assignment.cluster_id) if assignment.state == "accepted" else None

    asset_counter = 1
    detection_cursor = 0
    source_cycle = ["S001", "S002", "S003", "S004"]
    co_assets: dict[tuple[str, str], set[str]] = {}
    random.seed(7)
    for day in range(18):
        source_id = source_cycle[day % len(source_cycle)]
        asset_id = f"A{asset_counter:03d}"
        asset_counter += 1
        captured = now - timedelta(days=(17-day)*17)
        participants = [PERSONAS[day % 6][0]]
        if day % 3 == 0:
            participants.append(PERSONAS[(day + 1) % 6][0])
        if day % 5 == 0:
            participants.append(PERSONAS[(day + 3) % 6][0])
        sha = hashlib.sha256(f"demo:{asset_id}".encode()).hexdigest()
        db.execute("INSERT INTO assets(id,source_id,kind,filename,sha256,captured_at,caption,duration_seconds) VALUES(?,?,?,?,?,?,?,?)", (asset_id, source_id, "image", f"demo_{asset_id.lower()}.jpg", sha, captured.isoformat(), "Synthetic authorized demo asset", None))
        frame_id = f"F-{asset_id}"
        db.execute("INSERT INTO frames(id,asset_id,frame_index,timestamp_seconds,width,height) VALUES(?,?,?,?,?,?)", (frame_id, asset_id, 0, 0.0, 1280, 800))
        for slot, persona_id in enumerate(participants):
            detection_cursor += 1
            detection_id = f"D{detection_cursor:04d}"
            bbox = [120 + slot*260, 160, 180, 220]
            db.execute("INSERT INTO detections(id,frame_id,bbox_json,confidence,landmarks_json,crop_path) VALUES(?,?,?,?,?,?)", (detection_id, frame_id, json.dumps(bbox), 0.95, "[]", f"demo/media/{persona_id.lower()}.svg"))
            vector = _centers()[persona_id].astype(np.float32).tobytes()
            db.execute("INSERT INTO embeddings(detection_id,model_id,model_sha256,dimension,normalization,vector_blob) VALUES(?,?,?,?,?,?)", (detection_id, "deterministic-demo-v1", "synthetic", 64, "l2", vector))
            db.execute("INSERT INTO memberships(detection_id,persona_id,state,similarity,method,cluster_run_id) VALUES(?,?,?,?,?,?)", (detection_id, persona_id, "accepted", 0.94, "fixture", "demo-ground-truth"))
            appearance_id = f"AP-{asset_id}-{persona_id}"
            db.execute("INSERT INTO appearances(id,persona_id,asset_id,start_seconds,end_seconds,representative_detection_id,confidence) VALUES(?,?,?,?,?,?,?)", (appearance_id, persona_id, asset_id, None, None, detection_id, 0.94))
        for i, a in enumerate(participants):
            for b in participants[i+1:]:
                key = tuple(sorted((a,b)))
                co_assets.setdefault(key, set()).add(asset_id)

    # Add two review items linked to ambiguous synthetic vectors.
    for j, candidate in enumerate(("P001", "P004"), start=1):
        source_id = "S004"
        asset_id = f"AR{j:02d}"
        sha = hashlib.sha256(f"review:{j}".encode()).hexdigest()
        db.execute("INSERT INTO assets(id,source_id,kind,filename,sha256,captured_at,caption,duration_seconds) VALUES(?,?,?,?,?,?,?,?)", (asset_id, source_id, "image", f"uncertain_{j}.jpg", sha, now.isoformat(), "Synthetic ambiguous review fixture", None))
        frame_id = f"F-{asset_id}"
        db.execute("INSERT INTO frames(id,asset_id,frame_index,timestamp_seconds,width,height) VALUES(?,?,?,?,?,?)", (frame_id, asset_id, 0, 0.0, 1000, 700))
        detection_id = f"REVIEW-D{j:02d}"
        db.execute("INSERT INTO detections(id,frame_id,bbox_json,confidence,landmarks_json,crop_path) VALUES(?,?,?,?,?,?)", (detection_id, frame_id, "[140,120,180,220]", 0.86, "[]", f"demo/media/{candidate.lower()}.svg"))
        db.execute("INSERT INTO memberships(detection_id,persona_id,state,similarity,method,cluster_run_id) VALUES(?,?,?,?,?,?)", (detection_id, candidate, "review_required", 0.71 - j*0.02, "machine", "demo-review"))

    for persona_id, _ in PERSONAS:
        first = db.one(
            "SELECT detection_id FROM memberships WHERE persona_id=? AND state='accepted' ORDER BY detection_id LIMIT 1",
            (persona_id,),
        )
        if first:
            db.execute(
                "UPDATE personas SET representative_detection_id=? WHERE id=?",
                (first["detection_id"], persona_id),
            )

    metrics = pairwise_metrics(truth, predicted)
    return {
        "sources": len(SOURCES),
        "personas": len(PERSONAS),
        "assets": 20,
        "detections": detection_cursor + 2,
        "review_items": 2,
        "evaluation": metrics,
        "fixture_type": "deterministic logic fixture",
    }
