"""Nexus execution module — TSR-owned bounded action interface."""

from __future__ import annotations

from typing import Any

from src.aaes_os.nexus_execution_ledger import get_nexus_execution_ledger
from src.aaes_os.pipeline_types import AAESAction
from src.aaes_os.tsr_routing import connector_status, tsr_owner


class NexusExecutionModule:
    """Governed executor when TSR control plane is Nexus ops-console."""

    module_id = "nexus"

    def execute(self, action: AAESAction) -> dict[str, Any]:
        if not isinstance(action, AAESAction):
            raise TypeError("action must be AAESAction")
        action.validate()
        return {
            "module_id": self.module_id,
            "operation": action.operation,
            "status": "nexus_ok",
            "tsr_owner": tsr_owner(),
            "daniel_connector": connector_status("daniel"),
            "nexus_connector": connector_status("nexus"),
            "args": dict(action.args),
            "message": f"Nexus TSR executed {action.operation}",
        }


def record_execution(receipt: dict[str, Any]) -> dict[str, Any]:
    """Record a governed AAES execution for Nexus ops-console observability."""
    event = get_nexus_execution_ledger().record_execution(receipt)
    event["event_type"] = "execution"
    event["module_id"] = "nexus"
    return event


def list_execution_events(*, limit: int = 50) -> list[dict[str, Any]]:
    """List recent Nexus execution events."""
    return get_nexus_execution_ledger().list_executions(limit=limit)
