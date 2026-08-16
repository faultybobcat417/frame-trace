#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "models" / "manifest.json"
DEST = ROOT / "models" / "weights"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    data = json.loads(MANIFEST.read_text())
    for model in data["models"]:
        target = DEST / model["filename"]
        if target.exists() and digest(target) == model["sha256"]:
            print(f"verified {target.name}")
            continue
        tmp = target.with_suffix(target.suffix + ".part")
        print(f"downloading {model['name']}...")
        with urllib.request.urlopen(model["url"], timeout=120) as response, tmp.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        actual = digest(tmp)
        if actual != model["sha256"]:
            tmp.unlink(missing_ok=True)
            raise SystemExit(f"checksum mismatch for {model['filename']}: {actual}")
        tmp.replace(target)
        print(f"verified {target.name}")


if __name__ == "__main__":
    main()
