"""Nexus ops-console API — execution ledger observability."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from src.aaes_os.modules.nexus import list_execution_events

app = FastAPI(title="Nexus Ops Console", version="0.1.0")


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "nexus_dashboard"}


@app.get("/api/nexus/executions")
def list_nexus_executions(limit: int = 50) -> dict[str, Any]:
    """Match AAIS response shape for cross-port observability."""
    return {"executions": list_execution_events(limit=limit)}
