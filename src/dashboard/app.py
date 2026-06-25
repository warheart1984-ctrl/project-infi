"""Standalone CORI dashboard API for CI and the React trace viewer."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.dashboard.api import router as dashboard_router
from src.dashboard.claims_api import router as claims_router
from src.dashboard.evidence_api import router as evidence_router
from src.dashboard.pel_api import router as pel_router

app = FastAPI(title="CORI Dashboard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(pel_router)
app.include_router(claims_router)
app.include_router(evidence_router)


@app.get("/health")
def root_health() -> dict[str, Any]:
    return {"status": "ok", "service": "cori_dashboard"}
