"""Temporal workflow definition for governed OTEM approve → apply."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

try:
    from temporalio import workflow
    from temporalio.common import RetryPolicy

    with workflow.unsafe.imports_passed_through():
        from src.otem_temporal.activities import otem_substrate_apply, otem_substrate_approve

    @workflow.defn(name="OTEMExecutionTemporalWorkflow")
    class OTEMExecutionTemporalWorkflow:
        """Durable OTEM path: wait for operator signal, then run substrate approve/apply."""

        def __init__(self) -> None:
            self._decision: str | None = None

        @workflow.signal
        async def operator_decision(self, action: str) -> None:
            self._decision = str(action or "").strip().lower()

        @workflow.query
        def decision(self) -> str | None:
            return self._decision

        @workflow.run
        async def run(self, workflow_id: str, proposal: dict[str, Any]) -> dict[str, Any]:
            del proposal  # persisted on substrate row at enqueue time
            await workflow.wait_condition(lambda: self._decision is not None)
            if self._decision == "reject":
                return {
                    "status": "rejected",
                    "workflow_id": workflow_id,
                    "substrate": None,
                }
            if self._decision != "approve":
                raise ValueError(f"Unsupported operator decision: {self._decision!r}")

            approved = await workflow.execute_activity(
                otem_substrate_approve,
                workflow_id,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            applied = await workflow.execute_activity(
                otem_substrate_apply,
                workflow_id,
                start_to_close_timeout=timedelta(minutes=30),
                heartbeat_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )
            return {
                "status": "approved",
                "workflow_id": workflow_id,
                "substrate_approved": approved,
                "substrate": applied,
            }

except ImportError:  # pragma: no cover
    OTEMExecutionTemporalWorkflow = None  # type: ignore[assignment,misc]
