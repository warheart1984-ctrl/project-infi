"""Temporal activities — thin wrappers around OTEMExecutionSubstrate."""

from __future__ import annotations

from typing import Any


def _substrate_approve(workflow_id: str) -> dict[str, Any]:
    from src.otem.execution import get_otem_execution_substrate

    return get_otem_execution_substrate().approve(
        workflow_id,
        runtime_context="operator_runtime",
    )


def _substrate_apply(workflow_id: str) -> dict[str, Any]:
    from src.otem.execution import get_otem_execution_substrate

    return get_otem_execution_substrate().apply(
        workflow_id,
        runtime_context="operator_runtime",
    )


try:
    from temporalio import activity

    @activity.defn(name="otem_substrate_approve")
    async def otem_substrate_approve(workflow_id: str) -> dict[str, Any]:
        return _substrate_approve(workflow_id)

    @activity.defn(name="otem_substrate_apply")
    async def otem_substrate_apply(workflow_id: str) -> dict[str, Any]:
        return _substrate_apply(workflow_id)

    OTEM_ACTIVITIES = [otem_substrate_approve, otem_substrate_apply]
except ImportError:  # pragma: no cover - exercised when temporalio not installed
    otem_substrate_approve = None  # type: ignore[assignment,misc]
    otem_substrate_apply = None  # type: ignore[assignment,misc]
    OTEM_ACTIVITIES: list[Any] = []
