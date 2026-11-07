from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import AppConfig
from .queue import AnalysisWorker
from .storage import JobStore


class AlertPayload(BaseModel):
    event_id: str = Field(min_length=1, max_length=256)
    triggered_at: str
    window_seconds: int = Field(default=900, ge=30, le=3600)
    metric: dict[str, Any]
    result: dict[str, Any]
    related_metrics: list[dict[str, Any]] = Field(default_factory=list)
    incident: dict[str, Any] | None = None
    grafana_root_url: str = ""


def create_app(
    config: AppConfig,
    store: JobStore,
    worker: AnalysisWorker | None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if worker is not None:
            worker.start()
        try:
            yield
        finally:
            if worker is not None:
                worker.stop()

    app = FastAPI(
        title="MERN AI Model",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.config = config
    app.state.store = store
    app.state.worker = worker

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "model": config.ollama.model,
            "ollama_url": config.ollama.url,
            "pending_jobs": store.pending_count(),
            "window_seconds": config.collection.window_seconds,
        }

    @app.post("/analyze", status_code=202)
    def analyze(payload: AlertPayload) -> JSONResponse:
        job_id, created = store.enqueue(payload.model_dump())
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "status": "queued" if created else "duplicate",
            },
        )

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return job

    return app
