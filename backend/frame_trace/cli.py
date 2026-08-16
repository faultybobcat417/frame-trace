from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import cv2
import numpy as np
import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from frame_trace import __version__
from frame_trace.api import create_app
from frame_trace.clustering import DBSCANClusterEngine, pairwise_metrics
from frame_trace.config import settings
from frame_trace.demo import seed_demo, synthetic_vectors
from frame_trace.persistence import Database

app = typer.Typer(name="frame-trace", help="Local-first visual relationship explorer for authorized media.", no_args_is_help=True)
console = Console()


def _db() -> Database:
    settings.ensure_dirs()
    return Database(settings.database_path)


@app.command()
def doctor() -> None:
    """Verify local dependencies, storage and optional model artifacts."""
    settings.ensure_dirs()
    table = Table(title="Frame Trace Environment")
    table.add_column("Check")
    table.add_column("Value")
    table.add_row("Version", __version__)
    table.add_row("Python", sys.version.split()[0])
    table.add_row("Architecture", platform.machine())
    table.add_row("OpenCV", cv2.__version__)
    table.add_row("NumPy", np.__version__)
    table.add_row("Database", str(settings.database_path))
    yunet = settings.model_dir / "face_detection_yunet_2023mar.onnx"
    sface = settings.model_dir / "face_recognition_sface_2021dec.onnx"
    table.add_row("YuNet", "ready" if yunet.exists() else "not downloaded")
    table.add_row("SFace", "ready" if sface.exists() else "not downloaded")
    table.add_row("Network behavior", "none unless scripts/fetch_models.py is run")
    console.print(table)
    console.print("[green]Core environment ready.[/green] Optional CV weights are checksum-pinned in models/manifest.json.")


@app.command()
def demo() -> None:
    """Load the deterministic authorized-media demonstration fixture."""
    summary = seed_demo(_db(), settings.demo_dir)
    console.print("[bold green]Demo initialized.[/bold green]")
    console.print_json(json.dumps(summary))
    console.print("Run [bold]frame-trace serve[/bold] and open http://127.0.0.1:8000/docs or the frontend dev server.")


@app.command()
def evaluate() -> None:
    """Evaluate clustering against deterministic ground truth."""
    ids, vectors, truth = synthetic_vectors()
    assignments = DBSCANClusterEngine(eps=0.22, min_samples=2, membership_floor=0.72).fit(ids, vectors)
    cluster_map: dict[int, str] = {}
    predicted: dict[str, str | None] = {}
    for assignment in assignments:
        if assignment.cluster_id is None or assignment.state != "accepted":
            predicted[assignment.item_id] = None
            continue
        cluster_map.setdefault(assignment.cluster_id, truth[assignment.item_id])
        predicted[assignment.item_id] = cluster_map[assignment.cluster_id]
    console.print_json(json.dumps(pairwise_metrics(truth, predicted), indent=2))


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Serve the local API."""
    uvicorn.run("frame_trace.main:app", host=host, port=port, reload=reload)


@app.command("reset")
def reset() -> None:
    """Delete local product state and recreate the empty schema."""
    _db().reset()
    console.print("[green]Local database reset.[/green]")


@app.command("recluster")
def recluster() -> None:
    """Run the deterministic clustering reference fixture."""
    evaluate()


@app.command("import")
def import_path(path: Path) -> None:
    """Validate a local authorized-media path before CV ingestion."""
    from frame_trace.ingest import FolderAdapter, ManifestPackageAdapter
    path = path.expanduser().resolve()
    adapter = ManifestPackageAdapter() if (path / "manifest.json").exists() else FolderAdapter()
    assets = adapter.discover(path)
    console.print(f"Discovered [bold]{len(assets)}[/bold] supported authorized-media asset(s).")
    yunet = settings.model_dir / "face_detection_yunet_2023mar.onnx"
    sface = settings.model_dir / "face_recognition_sface_2021dec.onnx"
    if not yunet.exists() or not sface.exists():
        raise typer.BadParameter("CV weights are missing. Run python scripts/fetch_models.py first.")
    from frame_trace.services import VisionIngestService
    summary = VisionIngestService(_db(), settings).import_path(path)
    console.print_json(json.dumps(summary, indent=2))
