from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AssetKind(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class AssignmentState(StrEnum):
    ACCEPTED = "accepted"
    REVIEW_REQUIRED = "review_required"
    UNASSIGNED = "unassigned"


class Source(BaseModel):
    id: str
    name: str
    source_type: str = "local"
    platform_label: str | None = None
    handle_label: str | None = None


class Asset(BaseModel):
    id: str
    source_id: str
    kind: AssetKind
    filename: str
    sha256: str
    captured_at: datetime | None = None
    caption: str | None = None
    duration_seconds: float | None = None


class Frame(BaseModel):
    id: str
    asset_id: str
    frame_index: int
    timestamp_seconds: float
    width: int
    height: int


class FaceDetection(BaseModel):
    id: str
    frame_id: str
    bbox: tuple[float, float, float, float]
    confidence: float = Field(ge=0, le=1)
    landmarks: list[tuple[float, float]] = Field(default_factory=list)


class Persona(BaseModel):
    id: str
    label: str | None = None
    hidden: bool = False
    status: AssignmentState = AssignmentState.ACCEPTED
    representative_detection_id: str | None = None


class PersonaMembership(BaseModel):
    detection_id: str
    persona_id: str | None
    state: AssignmentState
    similarity: float | None = None
    method: str = "machine"


class Appearance(BaseModel):
    id: str
    persona_id: str
    asset_id: str
    start_seconds: float | None = None
    end_seconds: float | None = None
    representative_detection_id: str | None = None
    confidence: float | None = None


class CoOccurrence(BaseModel):
    persona_a: str
    persona_b: str
    shared_asset_count: int
    shared_appearance_count: int
    first_seen: datetime | None = None
    last_seen: datetime | None = None


class ReviewDecision(BaseModel):
    id: str
    detection_id: str
    candidate_persona_id: str | None
    decision: str
    similarity: float | None = None
    created_at: datetime


class ImportRun(BaseModel):
    id: str
    status: str
    stage: str
    progress: float = Field(ge=0, le=1)
    message: str = ""
    created_at: datetime
    completed_at: datetime | None = None


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    data: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    data: dict[str, Any] = Field(default_factory=dict)


class GraphPayload(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
