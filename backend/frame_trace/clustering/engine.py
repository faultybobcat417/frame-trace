from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.cluster import DBSCAN


@dataclass(frozen=True)
class ClusterAssignment:
    item_id: str
    cluster_id: int | None
    state: str
    similarity_to_medoid: float | None


class DBSCANClusterEngine:
    def __init__(self, eps: float = 0.33, min_samples: int = 2, membership_floor: float = 0.58):
        self.eps = eps
        self.min_samples = min_samples
        self.membership_floor = membership_floor

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        vectors = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    def fit(self, item_ids: list[str], vectors: np.ndarray) -> list[ClusterAssignment]:
        if len(item_ids) != len(vectors):
            raise ValueError("item_ids and vectors must have identical lengths")
        if not item_ids:
            return []
        x = self._normalize(vectors)
        labels = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric="cosine").fit_predict(x)
        assignments: list[ClusterAssignment] = []
        for idx, label in enumerate(labels):
            if label < 0:
                assignments.append(ClusterAssignment(item_ids[idx], None, "unassigned", None))
                continue
            members = np.where(labels == label)[0]
            cluster = x[members]
            sims = cluster @ cluster.T
            medoid_local = int(np.argmax(sims.mean(axis=1)))
            medoid = cluster[medoid_local]
            similarity = float(x[idx] @ medoid)
            state = "accepted" if similarity >= self.membership_floor else "review_required"
            assignments.append(ClusterAssignment(item_ids[idx], int(label), state, similarity))
        return assignments
