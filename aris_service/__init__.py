"""Standalone ARIS admission service (FastAPI)."""

# Mythic: Aris Standalone Service
# Engineering: ArisStandaloneServiceEngine
from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError:  # pragma: no cover - optional runtime dep
    FastAPI = None  # type: ignore[misc, assignment]
    BaseModel = object  # type: ignore[misc, assignment]

from src.aris_integration import ARIS_CONTRACT_VERSION, ARIS_RUNTIME_PROFILE, build_aris_enforcement


class AdmitRequest(BaseModel):
    packet: dict[str, Any]


def create_app() -> Any:
    if FastAPI is None:
        raise RuntimeError("fastapi is required for aris_service")
    app = FastAPI(title="ARIS Standalone Service", version="1.0.0")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "runtime_profile": ARIS_RUNTIME_PROFILE,
            "contract_version": ARIS_CONTRACT_VERSION,
            "standalone_service": True,
        }

    @app.post("/v1/admit")
    def admit(request: AdmitRequest) -> dict[str, Any]:
        result = build_aris_enforcement(request.packet)
        result["standalone_service"] = True
        result["service"] = "aris_standalone"
        return result

    return app


app = create_app() if FastAPI is not None else None
