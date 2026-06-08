"""Temporal client helpers for OTEM execution (async API + sync bridge wrappers)."""

from __future__ import annotations

import asyncio
from typing import Any

from src.otem_temporal.config import (
    OTEM_TEMPORAL_NAMESPACE,
    OTEM_TEMPORAL_TASK_QUEUE,
    TEMPORAL_ADDRESS,
    otem_temporal_enabled,
)


def _require_temporal() -> None:
    if not otem_temporal_enabled():
        raise RuntimeError(
            "OTEM Temporal is not enabled (set AAIS_OTEM_TEMPORAL_ENABLED=1 and install temporalio)"
        )


async def _connect():
    from temporalio.client import Client

    return await Client.connect(TEMPORAL_ADDRESS, namespace=OTEM_TEMPORAL_NAMESPACE)


async def start_otem_workflow_async(workflow_id: str, proposal: dict[str, Any]) -> str:
    """Start durable OTEM workflow; id matches substrate workflow_id."""
    _require_temporal()
    from src.otem_temporal.workflows import OTEMExecutionTemporalWorkflow

    client = await _connect()
    await client.start_workflow(
        OTEMExecutionTemporalWorkflow.run,
        args=[workflow_id, dict(proposal)],
        id=workflow_id,
        task_queue=OTEM_TEMPORAL_TASK_QUEUE,
    )
    return workflow_id


async def resolve_otem_workflow_async(workflow_id: str, action: str) -> dict[str, Any]:
    """Signal operator decision and wait for workflow completion."""
    _require_temporal()
    from src.otem_temporal.workflows import OTEMExecutionTemporalWorkflow

    client = await _connect()
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal(OTEMExecutionTemporalWorkflow.operator_decision, action)
    return await handle.result()


def start_otem_workflow(workflow_id: str, proposal: dict[str, Any]) -> str:
    return asyncio.run(start_otem_workflow_async(workflow_id, proposal))


def resolve_otem_workflow(workflow_id: str, action: str) -> dict[str, Any]:
    return asyncio.run(resolve_otem_workflow_async(workflow_id, action))
