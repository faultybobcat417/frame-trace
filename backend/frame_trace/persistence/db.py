from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  platform_label TEXT,
  handle_label TEXT
);
CREATE TABLE IF NOT EXISTS assets (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  filename TEXT NOT NULL,
  sha256 TEXT NOT NULL UNIQUE,
  captured_at TEXT,
  caption TEXT,
  duration_seconds REAL
);
CREATE INDEX IF NOT EXISTS idx_assets_source ON assets(source_id);
CREATE TABLE IF NOT EXISTS frames (
  id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  frame_index INTEGER NOT NULL,
  timestamp_seconds REAL NOT NULL,
  width INTEGER NOT NULL,
  height INTEGER NOT NULL,
  UNIQUE(asset_id, frame_index)
);
CREATE TABLE IF NOT EXISTS detections (
  id TEXT PRIMARY KEY,
  frame_id TEXT NOT NULL REFERENCES frames(id) ON DELETE CASCADE,
  bbox_json TEXT NOT NULL,
  confidence REAL NOT NULL,
  landmarks_json TEXT NOT NULL,
  crop_path TEXT
);
CREATE INDEX IF NOT EXISTS idx_detections_frame ON detections(frame_id);
CREATE TABLE IF NOT EXISTS embeddings (
  detection_id TEXT PRIMARY KEY REFERENCES detections(id) ON DELETE CASCADE,
  model_id TEXT NOT NULL,
  model_sha256 TEXT NOT NULL,
  dimension INTEGER NOT NULL,
  normalization TEXT NOT NULL,
  vector_blob BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS personas (
  id TEXT PRIMARY KEY,
  label TEXT,
  hidden INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  representative_detection_id TEXT
);
CREATE TABLE IF NOT EXISTS memberships (
  detection_id TEXT PRIMARY KEY REFERENCES detections(id) ON DELETE CASCADE,
  persona_id TEXT REFERENCES personas(id) ON DELETE SET NULL,
  state TEXT NOT NULL,
  similarity REAL,
  method TEXT NOT NULL,
  cluster_run_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_memberships_persona ON memberships(persona_id);
CREATE TABLE IF NOT EXISTS appearances (
  id TEXT PRIMARY KEY,
  persona_id TEXT NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
  asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  start_seconds REAL,
  end_seconds REAL,
  representative_detection_id TEXT,
  confidence REAL
);
CREATE INDEX IF NOT EXISTS idx_appearances_persona ON appearances(persona_id);
CREATE INDEX IF NOT EXISTS idx_appearances_asset ON appearances(asset_id);
CREATE TABLE IF NOT EXISTS review_decisions (
  id TEXT PRIMARY KEY,
  detection_id TEXT NOT NULL,
  candidate_persona_id TEXT,
  decision TEXT NOT NULL,
  similarity REAL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS import_runs (
  id TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  stage TEXT NOT NULL,
  progress REAL NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL,
  completed_at TEXT
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def reset(self) -> None:
        with self.connect() as conn:
            rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            conn.execute("PRAGMA foreign_keys = OFF")
            for row in rows:
                conn.execute(f'DROP TABLE IF EXISTS "{row[0]}"')
            conn.execute("PRAGMA foreign_keys = ON")
        self.initialize()

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self.connect() as conn:
            conn.execute(sql, params)

    def executemany(self, sql: str, rows: list[tuple]) -> None:
        with self.connect() as conn:
            conn.executemany(sql, rows)

    def query(self, sql: str, params: tuple = ()) -> list[dict]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def one(self, sql: str, params: tuple = ()) -> dict | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None


def dumps(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)
