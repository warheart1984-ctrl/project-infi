"""Durable OTEM substrate store co-located with workflow DB (Release 31 circulation)."""

# Mythic: Otem Substrate Store
# Engineering: OtemSubstrateStoreEngine
from __future__ import annotations

from typing import Any

from app.config import OTEM_SUBSTRATE_USE_DB


def substrate_db_enabled() -> bool:
    return OTEM_SUBSTRATE_USE_DB


def persist_substrate_workflow(workflow_dict: dict[str, Any]) -> dict[str, Any] | None:
    if not substrate_db_enabled():
        return None
    from app.db import upsert_otem_substrate_workflow

    return upsert_otem_substrate_workflow(workflow_dict)


def load_substrate_workflow(workflow_id: str) -> dict[str, Any] | None:
    if not substrate_db_enabled():
        return None
    from app.db import get_otem_substrate_workflow

    return get_otem_substrate_workflow(workflow_id)


def load_all_substrate_workflows(limit: int = 500) -> list[dict[str, Any]]:
    if not substrate_db_enabled():
        return []
    from app.db import list_otem_substrate_workflows

    return list_otem_substrate_workflows(limit=limit)


def rehydrate_substrate_workflow_from_proposal(
    workflow_id: str,
    proposal: dict[str, Any],
    *,
    stage: str = "proposal",
) -> dict[str, Any]:
    """Rehydrate in-memory + durable substrate from approval payload snapshot."""
    from src.otem.execution import (
        OTEMExecutionWorkflow,
        get_otem_execution_substrate,
    )

    substrate = get_otem_execution_substrate()
    workflow = OTEMExecutionWorkflow(
        workflow_id=workflow_id,
        stage=stage,
        proposal=dict(proposal),
    )
    substrate._workflows[workflow_id] = workflow
    row = workflow.to_dict()
    persist_substrate_workflow(row)
    return row
