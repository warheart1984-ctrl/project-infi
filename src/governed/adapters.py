"""Default in-process adapters for governed spine ports."""

from __future__ import annotations

from typing import Any

from src.governed.ports import NexusOsContinuityPort, NexusRecordPort


class LocalNexusRecordAdapter:
    """Default: AAES Nexus module JSONL ledger (nexus.execution bucket)."""

    def record_execution(self, aaes_receipt: dict[str, Any]) -> dict[str, Any]:
        from src.aaes_os.modules.nexus import record_execution

        event = record_execution(aaes_receipt)
        event["event_type"] = "execution"
        event["event_id"] = str(
            event.get("event_id")
            or event.get("aaes_trace_id")
            or aaes_receipt.get("execution_id")
            or aaes_receipt.get("trace_id")
            or event.get("recorded_at")
            or ""
        )
        return event


class NullNexusRecordAdapter:
    """Decoupled mode: spine continues without Nexus execution ledger writes."""

    def record_execution(self, aaes_receipt: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_type": "execution",
            "event_id": str(aaes_receipt.get("execution_id") or aaes_receipt.get("trace_id") or ""),
            "status": "skipped",
            "reason": "nexus_record_mode=disabled",
            "mission_id": aaes_receipt.get("mission_id"),
            "law_eval_id": aaes_receipt.get("law_eval_id"),
        }


class NullNexusOsContinuityAdapter:
    """No FOS civilization export until NexusOS adapter is wired."""

    def export_mission_receipt(
        self,
        *,
        mission_id: str,
        law_eval: dict[str, Any],
        urg_receipt: dict[str, Any],
        aaes_receipt: dict[str, Any],
        nexus_event: dict[str, Any],
    ) -> dict[str, Any] | None:
        return None


def get_nexus_record_adapter(mode: str) -> NexusRecordPort:
    cleaned = str(mode or "in_process").strip().lower()
    if cleaned in {"disabled", "off", "none"}:
        return NullNexusRecordAdapter()
    return LocalNexusRecordAdapter()


def get_nexusos_continuity_adapter(enabled: bool) -> NexusOsContinuityPort:
    if not enabled:
        return NullNexusOsContinuityAdapter()
    try:
        from src.governed.nexusos_export import UrgWtNexusOsContinuityAdapter

        return UrgWtNexusOsContinuityAdapter()
    except ImportError:
        return NullNexusOsContinuityAdapter()
