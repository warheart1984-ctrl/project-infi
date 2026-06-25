"""AAES Alpha HTTP surface — health + cognitive orchestrator routes."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from src.aaes_os.api import router as aaes_os_router

app = FastAPI(title="AAES", version="0.1.0")
app.include_router(aaes_os_router)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "aaes"}
