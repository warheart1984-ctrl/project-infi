"""OTEM autonomic routines — low-risk governed reflexes (Release 33)."""

# Mythic: Otem Autonomic Routines
# Engineering: OtemAutonomicRoutinesEngine
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ARC_ORDER = {"ARC-0": 0, "ARC-1": 1, "ARC-2": 2}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def autonomic_enabled() -> bool:
    return os.getenv("AAIS_OTEM_AUTONOMIC_ENABLED", "0").lower() in {"1", "true", "yes", "on"}


def arc_ceiling() -> str:
    return os.getenv("AAIS_OTEM_AUTONOMIC_ARC_CEILING", "ARC-1").strip().upper()


def load_routines_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "otem_autonomic_routines.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def routine_by_id(routine_id: str) -> dict[str, Any] | None:
    doc = load_routines_registry()
    for routine in list(doc.get("routines") or []):
        if str(routine.get("routine_id") or "") == routine_id:
            return routine
    return None


def arc_allowed(routine_arc: str) -> bool:
    ceiling = arc_ceiling()
    return ARC_ORDER.get(str(routine_arc or "").upper(), 99) <= ARC_ORDER.get(ceiling, 1)


def execute_autonomic_routine(
    routine_id: str,
    *,
    session_id: str = "global",
    args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not autonomic_enabled():
        return {"outcome": "blocked", "reason": "AAIS_OTEM_AUTONOMIC_ENABLED=0"}
    routine = routine_by_id(routine_id)
    if not routine:
        return {"outcome": "not_found", "routine_id": routine_id}
    routine_arc = str(routine.get("arc_class") or "ARC-2")
    if not arc_allowed(routine_arc):
        return {"outcome": "blocked", "reason": "arc_ceiling", "routine_id": routine_id, "arc_class": routine_arc}
    if routine_arc == "ARC-2":
        return {"outcome": "blocked", "reason": "requires_operator_approval", "routine_id": routine_id}

    handler = str(routine.get("handler") or "")
    result: dict[str, Any]
    if handler == "operator_somatic_health":
        from src.operator_somatic_health import build_somatic_health_snapshot

        result = {"snapshot": build_somatic_health_snapshot()}
    elif handler == "aais_doctor":
        from src.aais_doctor_organ import build_aais_doctor_status

        result = {"doctor": build_aais_doctor_status()}
    elif handler == "ledger_digest":
        from src.operator_decision_ledger import operator_decision_ledger_store

        scope = session_id or "global"
        result = {"digest": operator_decision_ledger_store.build_digest_summary(scope)}
    elif handler == "workflow_chain_dry_run":
        from src.workflow_chain_executor import workflow_chain_executor

        workflow_id = str((args or {}).get("workflow_id") or "research_brief")
        result = {
            "run": workflow_chain_executor.execute(
                workflow_id,
                args={"session_id": session_id, **dict(args or {})},
                operator_approved=True,
                dry_run=True,
            )
        }
    else:
        return {"outcome": "blocked", "reason": "unknown_handler", "handler": handler}

    receipt = None
    try:
        from src.operator_decision_ledger import append_autonomic_routine_event

        receipt = append_autonomic_routine_event(
            session_id,
            routine_id=routine_id,
            arc_class=routine_arc,
            outcome="completed",
        )
    except Exception:
        pass

    return {
        "outcome": "completed",
        "routine_id": routine_id,
        "arc_class": routine_arc,
        "handler": handler,
        "result": result,
        "ledger_receipt": receipt,
    }
