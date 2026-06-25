"""CORI Alpha observability API — read-only FastAPI routes over SQLite stores."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.cori.governance_invariants import run_governance_invariants
from src.cori.store_paths import continuity_store_path, law_ledger_path, panel_store_path
from src.dashboard import queries

router = APIRouter(prefix="/dashboard", tags=["cori-dashboard"])


class MissionSummary(BaseModel):
    time: str | None = None
    steward: str | None = None
    mission_id: str | None = None
    law_eval_id: str | None = None
    aaes_exec_id: str | None = None
    nexus_event_id: str | None = None
    status: str | None = None


def _db_paths() -> dict[str, str]:
    return {
        "panel_store": str(panel_store_path()),
        "continuity": str(continuity_store_path()),
        "law_ledger": str(law_ledger_path()),
    }


@router.get("/health")
def dashboard_health() -> dict[str, Any]:
    missing = [name for name, path in _db_paths().items() if not __import__("pathlib").Path(path).is_file()]
    return {"ok": not missing, "stores": _db_paths(), "missing": missing}


@router.get("/missions", response_model=list[MissionSummary])
def list_missions(limit: int = 100) -> list[MissionSummary]:
    try:
        return [MissionSummary(**row) for row in queries.list_mission_summaries(limit=limit)]
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/trace/{mission_id}")
def trace_mission(mission_id: str) -> dict[str, Any]:
    try:
        trace = queries.trace_mission_events(mission_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not trace:
        raise HTTPException(status_code=404, detail="Mission trace not found")
    panels = queries.panels_referencing(mission_id)
    return {"mission_id": mission_id, "trace": trace, "panels": panels}


@router.get("/law_kernel")
def law_kernel_summary(limit: int = 50) -> dict[str, Any]:
    try:
        return queries.law_kernel_rows(limit=limit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/evidence_density/{asset_id}")
def evidence_density(asset_id: str) -> dict[str, Any]:
    try:
        return queries.evidence_density_for_asset(asset_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/evidence_density")
def evidence_density_all(limit: int = 50) -> dict[str, Any]:
    """List all registered assets with evidence counts (extended endpoint)."""
    from src.cori.asset_registry import get_asset_registry

    try:
        _ = continuity_store_path()
        assets = get_asset_registry().list_assets(limit=limit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    rows = [queries.evidence_density_for_asset(asset["id"]) for asset in assets]
    return {"assets": rows}


@router.get("/invariants")
def dashboard_invariants() -> dict[str, Any]:
    from src.cori.governance_invariants import GovernanceInvariantChecker

    try:
        checker = GovernanceInvariantChecker()
        status = checker.list_status()
        if not status:
            return run_governance_invariants(persist=True)
        return {
            "all_passed": all(row["status"] == "pass" for row in status),
            "invariants": status,
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/invariants/run")
def dashboard_run_invariants() -> dict[str, Any]:
    try:
        return run_governance_invariants(persist=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
