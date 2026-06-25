"""FastAPI routes for AAES-OS cognitive orchestrator."""

# Mythic: AAES-OS Interface layer
# Engineering: AaesOsApiRouter
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.aaes_os.orchestrator import CognitiveOrchestrator
from src.aaes_os.pipeline_types import AAESRequest
from src.aaes_os.trace_store import TraceStore
from src.aaes_os.tsr_routing import trace_store_path


router = APIRouter(prefix="/aaes", tags=["aaes-os"])


def _default_trace_store_path() -> Path:
    return trace_store_path()


_orchestrator = CognitiveOrchestrator(trace_store=TraceStore(path=_default_trace_store_path()))


class AaesExecuteRequestBody(BaseModel):
    prompt: str
    actor_id: str
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None


def get_orchestrator() -> CognitiveOrchestrator:
    return _orchestrator


@router.post("/execute")
def aaes_execute(body: AaesExecuteRequestBody) -> dict[str, Any]:
    request = AAESRequest(
        prompt=body.prompt,
        actor_id=body.actor_id,
        session_id=body.session_id,
        metadata=dict(body.metadata),
        trace_id=body.trace_id,
    )
    try:
        result = get_orchestrator().execute(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "trace_id": result.trace_id,
        "span_id": result.span_id,
        "status": result.status,
        "blocked": result.blocked,
        "block_code": result.block_code,
        "explanation": result.explanation,
        "outcome": result.outcome,
        "steps": [
            {
                "step_id": step.step_id,
                "step_type": step.step_type.value,
                "summary": step.summary,
                "payload": step.payload,
            }
            for step in result.steps
        ],
        "decision": (
            {
                "verdict": result.decision.verdict.value,
                "reason": result.decision.reason,
                "policy_id": result.decision.policy_id,
            }
            if result.decision
            else None
        ),
    }


@router.get("/trace/{trace_id}")
def aaes_get_trace(trace_id: str) -> dict[str, Any]:
    record = get_orchestrator().trace_store.get(trace_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"trace not found: {trace_id}")
    return record
