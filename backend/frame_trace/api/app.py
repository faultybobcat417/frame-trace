from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from frame_trace import __version__
from frame_trace.config import Settings, settings as default_settings
from frame_trace.persistence import Database
from frame_trace.services import FrameTraceService, VisionIngestService


class PersonaPatch(BaseModel):
    label: str | None = None
    hidden: bool | None = None


class ReviewBody(BaseModel):
    decision: str


class ImportBody(BaseModel):
    path: str | None = None


def create_app(settings: Settings = default_settings) -> FastAPI:
    settings.ensure_dirs()
    db = Database(settings.database_path)
    service = FrameTraceService(db, settings)
    app = FastAPI(title="Frame Trace", version=__version__, description="Local-first visual relationship explorer for authorized media.")
    app.state.db = db
    app.state.service = service
    app.state.settings = settings
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__, "mode": "local"}

    @app.get("/api/personas")
    def personas() -> list[dict]:
        return service.list_personas()

    @app.get("/api/personas/{persona_id}")
    def persona(persona_id: str) -> dict:
        result = service.persona_detail(persona_id)
        if not result:
            raise HTTPException(404, "persona not found")
        return result

    @app.patch("/api/personas/{persona_id}")
    def persona_patch(persona_id: str, body: PersonaPatch) -> dict:
        result = service.update_persona(persona_id, body.label, body.hidden)
        if not result:
            raise HTTPException(404, "persona not found")
        return result

    @app.get("/api/personas/{persona_id}/appearances")
    def appearances(persona_id: str) -> list[dict]:
        return service.appearances(persona_id)

    @app.get("/api/personas/{persona_id}/neighbors")
    def neighbors(persona_id: str) -> list[dict]:
        return service.neighbors(persona_id)

    @app.get("/api/assets")
    def assets() -> list[dict]:
        return service.list_assets()

    @app.get("/api/assets/{asset_id}")
    def asset(asset_id: str) -> dict:
        result = service.asset_detail(asset_id)
        if not result:
            raise HTTPException(404, "asset not found")
        return result

    @app.get("/api/graph/persona/{persona_id}")
    def graph(persona_id: str) -> dict:
        try:
            return service.graph.persona_graph(persona_id).model_dump()
        except KeyError:
            raise HTTPException(404, "persona not found") from None

    @app.get("/api/review")
    def review() -> list[dict]:
        return service.review_queue()

    @app.post("/api/review/{detection_id}/decision")
    def review_decision(detection_id: str, body: ReviewBody) -> dict:
        try:
            return service.decide_review(detection_id, body.decision)
        except KeyError:
            raise HTTPException(404, "review item not found") from None
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None

    @app.post("/api/import")
    async def create_import(body: ImportBody) -> dict:
        if not body.path:
            raise HTTPException(400, "a local authorized-media path is required")
        run = service.new_import_run(body.path)
        asyncio.create_task(_run_import(service, VisionIngestService(db, settings), run["id"], body.path))
        return run

    @app.get("/api/import/{run_id}")
    def import_status(run_id: str) -> dict:
        result = service.import_run(run_id)
        if not result:
            raise HTTPException(404, "import run not found")
        return result

    @app.websocket("/ws/import/{run_id}")
    async def import_ws(websocket: WebSocket, run_id: str) -> None:
        await websocket.accept()
        try:
            while True:
                result = service.import_run(run_id)
                if not result:
                    await websocket.send_json({"error": "run not found"})
                    break
                await websocket.send_json(result)
                if result["status"] in {"complete", "failed"}:
                    break
                await asyncio.sleep(0.25)
        except WebSocketDisconnect:
            return
        finally:
            try:
                await websocket.close()
            except RuntimeError:
                pass

    @app.post("/api/reset-demo")
    def reset_demo() -> dict:
        return service.seed_demo()

    media_path = settings.demo_dir / "media"
    media_path.mkdir(parents=True, exist_ok=True)
    artifacts_path = settings.data_dir
    artifacts_path.mkdir(parents=True, exist_ok=True)
    app.mount("/demo-media", StaticFiles(directory=media_path), name="demo-media")
    app.mount("/local-artifacts", StaticFiles(directory=artifacts_path), name="local-artifacts")
    return app


async def _run_import(service: FrameTraceService, vision: VisionIngestService, run_id: str, path: str) -> None:
    stages = ["DISCOVER", "HASH", "DECODE", "SAMPLE", "DETECT", "EMBED", "CLUSTER", "PROJECT"]
    try:
        for idx, stage in enumerate(stages):
            service.update_import_run(run_id, "running", stage, idx / (len(stages) + 1), f"{stage.title()} stage")
            await asyncio.sleep(0.03)
        summary = await asyncio.to_thread(vision.import_path, Path(path))
        service.update_import_run(run_id, "complete", "COMPLETE", 1.0, f"Imported {summary['imported_assets']} asset(s), {summary['detections']} detection(s)")
    except Exception as exc:
        service.update_import_run(run_id, "failed", "FAILED", 1.0, str(exc))
