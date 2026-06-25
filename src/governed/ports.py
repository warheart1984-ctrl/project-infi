"""Decoupling ports for Tri-Core (routing) vs Nexus OS (execution observability).

Four buckets — do not conflate:
  1. tri_core.routing   — Python thalamus lane (nova_face / composed runtime)
  2. tri_core.governance — TS @aaes-os/tri-core-protocol (patch approvals)
  3. nexus.execution    — AAES module + JSONL ledger (governed spine step 4)
  4. nexusos.continuity — FOS civilization wire (urg-wt; optional export)
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LawEvalPort(Protocol):
    def evaluate(
        self,
        *,
        text: str,
        steward_identity: dict[str, Any],
    ) -> dict[str, Any]: ...


@runtime_checkable
class UrgMissionPort(Protocol):
    def dispatch(
        self,
        *,
        law_eval: dict[str, Any],
        steward_identity: dict[str, Any],
        user_text: str,
    ) -> dict[str, Any]: ...


@runtime_checkable
class AaesExecutePort(Protocol):
    def execute(
        self,
        *,
        law_eval: dict[str, Any],
        urg_receipt: dict[str, Any],
        steward_identity: dict[str, Any],
        user_text: str,
    ) -> dict[str, Any]: ...


@runtime_checkable
class NexusRecordPort(Protocol):
    """Nexus execution observability — distinct from tri_core routing authority."""

    def record_execution(self, aaes_receipt: dict[str, Any]) -> dict[str, Any]: ...


@runtime_checkable
class NexusOsContinuityPort(Protocol):
    """Optional FOS/NexusOS civilization export (urg-wt wire)."""

    def export_mission_receipt(
        self,
        *,
        mission_id: str,
        law_eval: dict[str, Any],
        urg_receipt: dict[str, Any],
        aaes_receipt: dict[str, Any],
        nexus_event: dict[str, Any],
    ) -> dict[str, Any] | None: ...


BOUNDARY_BUCKET = (
    "tri_core.routing",
    "tri_core.governance",
    "nexus.execution",
    "nexusos.continuity",
)
