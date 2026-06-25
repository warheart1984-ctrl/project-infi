"""Standalone runtime orchestrator service."""

from __future__ import annotations

from fastapi import FastAPI

from services.runtime.app.api import audit_router, router

app = FastAPI(title="CORI Runtime Orchestrator", version="0.1.0")
app.include_router(router)
app.include_router(audit_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "runtime_orchestrator"}
