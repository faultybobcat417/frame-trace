from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}


@dataclass(frozen=True)
class IngestAsset:
    path: Path
    source_id: str
    source_name: str
    kind: str
    captured_at: str | None = None
    caption: str | None = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_child(root: Path, relative: str) -> Path:
    root = root.resolve()
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"manifest path escapes package root: {relative}")
    return candidate


class FolderAdapter:
    def discover(self, path: Path, source_name: str | None = None) -> list[IngestAsset]:
        root = Path(path).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"folder does not exist: {root}")
        name = source_name or root.name
        items: list[IngestAsset] = []
        for file in sorted(root.rglob("*")):
            if not file.is_file():
                continue
            suffix = file.suffix.lower()
            if suffix in IMAGE_EXTENSIONS:
                kind = "image"
            elif suffix in VIDEO_EXTENSIONS:
                kind = "video"
            else:
                continue
            items.append(IngestAsset(file, f"folder:{name}", name, kind))
        return items


class ManifestPackageAdapter:
    def discover(self, path: Path) -> list[IngestAsset]:
        root = Path(path).resolve()
        manifest_path = root / "manifest.json"
        if not manifest_path.exists():
            raise ValueError("manifest.json is required")
        data = json.loads(manifest_path.read_text())
        source_id = str(data["source_id"])
        source_name = str(data["source_name"])
        items: list[IngestAsset] = []
        for item in data.get("assets", []):
            file = safe_child(root, str(item["path"]))
            if not file.exists() or not file.is_file():
                raise ValueError(f"asset is missing: {item['path']}")
            suffix = file.suffix.lower()
            kind = item.get("kind") or ("image" if suffix in IMAGE_EXTENSIONS else "video" if suffix in VIDEO_EXTENSIONS else None)
            if kind not in {"image", "video"}:
                raise ValueError(f"unsupported asset type: {item['path']}")
            items.append(IngestAsset(file, source_id, source_name, kind, item.get("captured_at"), item.get("caption")))
        return items
