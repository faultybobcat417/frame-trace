from __future__ import annotations

import numpy as np


class ExactCosineIndex:
    def __init__(self, vectors: np.ndarray | None = None, ids: list[str] | None = None):
        self.ids: list[str] = ids or []
        self.vectors = np.empty((0, 0), dtype=np.float32) if vectors is None else self._normalize(vectors)

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        arr = np.asarray(vectors, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr[None, :]
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return arr / norms

    def add(self, ids: list[str], vectors: np.ndarray) -> None:
        normalized = self._normalize(vectors)
        if self.vectors.size == 0:
            self.vectors = normalized
        else:
            if self.vectors.shape[1] != normalized.shape[1]:
                raise ValueError("embedding dimension mismatch")
            self.vectors = np.vstack([self.vectors, normalized])
        self.ids.extend(ids)

    def search(self, query: np.ndarray, k: int = 5) -> list[tuple[str, float]]:
        if not self.ids:
            return []
        q = self._normalize(query)[0]
        scores = self.vectors @ q
        order = np.argsort(scores)[::-1][: max(0, min(k, len(scores)))]
        return [(self.ids[i], float(scores[i])) for i in order]
