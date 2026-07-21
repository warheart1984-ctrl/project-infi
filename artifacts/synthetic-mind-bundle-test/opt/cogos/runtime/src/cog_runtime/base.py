"""Shared governed spine for cognitive runtimes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class StageRecord:
    runtime_id: str
    stage: str
    trace_id: str
    started_at: str
    ended_at: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "stage": self.stage,
            "trace_id": self.trace_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "payload": dict(self.payload or {}),
            "result": dict(self.result or {}),
        }


@dataclass
class CogRuntimeSession:
    """Per-turn ledger shared across cognitive runtimes."""

    runtime_id: str
    user_message: str
    context: dict[str, Any] = field(default_factory=dict)
    required_stages: tuple[str, ...] = ()
    stage_order: tuple[str, ...] = ()
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    ledger: list[StageRecord] = field(default_factory=list)
    _open_stages: dict[str, StageRecord] = field(default_factory=dict, repr=False)

    def start_stage(self, name: str, payload: dict[str, Any] | None = None) -> StageRecord:
        stage = str(name or "").strip()
        if not stage:
            raise ValueError("stage name required")
        if stage in self._open_stages:
            raise ValueError(f"stage already open: {stage}")
        record = StageRecord(
            runtime_id=self.runtime_id,
            stage=stage,
            trace_id=uuid.uuid4().hex[:12],
            started_at=_utc_now(),
            payload=dict(payload or {}),
        )
        self._open_stages[stage] = record
        return record

    def end_stage(self, name: str, result: dict[str, Any] | None = None) -> StageRecord:
        stage = str(name or "").strip()
        record = self._open_stages.pop(stage, None)
        if record is None:
            raise ValueError(f"stage not open: {stage}")
        record.ended_at = _utc_now()
        record.result = dict(result or {})
        self.append_ledger_entry(record)
        return record

    def append_ledger_entry(self, entry: StageRecord | dict[str, Any]) -> None:
        if isinstance(entry, StageRecord):
            self.ledger.append(entry)
            return
        if isinstance(entry, dict):
            self.ledger.append(
                StageRecord(
                    runtime_id=str(entry.get("runtime_id") or self.runtime_id),
                    stage=str(entry.get("stage") or ""),
                    trace_id=str(entry.get("trace_id") or uuid.uuid4().hex[:12]),
                    started_at=str(entry.get("started_at") or _utc_now()),
                    ended_at=entry.get("ended_at"),
                    payload=dict(entry.get("payload") or {}),
                    result=dict(entry.get("result") or {}),
                )
            )
            return
        raise TypeError("entry must be StageRecord or dict")

    def validate_turn(self) -> dict[str, Any]:
        issues: list[str] = []
        if self._open_stages:
            issues.append(f"open_stages:{','.join(sorted(self._open_stages))}")

        completed = [item.stage for item in self.ledger if item.ended_at]
        missing_required = [stage for stage in self.required_stages if stage not in completed]
        if missing_required:
            issues.append(f"missing_required:{','.join(missing_required)}")

        if self.stage_order:
            order_index = {stage: idx for idx, stage in enumerate(self.stage_order)}
            last_idx = -1
            for item in self.ledger:
                idx = order_index.get(item.stage)
                if idx is None:
                    continue
                if idx < last_idx:
                    issues.append(f"stage_order_violation:{item.stage}")
                    break
                last_idx = idx

        return {
            "valid": not issues,
            "issues": issues,
            "completed_stages": completed,
            "required_stages": list(self.required_stages),
            "ledger_count": len(self.ledger),
        }

    def export_ledger(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.ledger]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "runtime_id": self.runtime_id,
            "user_message": self.user_message,
            "context": dict(self.context or {}),
            "ledger": self.export_ledger(),
            "validation": self.validate_turn(),
        }


def runtime_spec_template(
    *,
    runtime_id: str,
    version: str,
    summary: str,
    stages: tuple[str, ...],
    required_turn_stages: tuple[str, ...],
    invariants: tuple[dict[str, str], ...],
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    doc: str,
    capability_metric: str,
    baseline_substitute: str,
    evidence_status: str,
    sunset_trigger: str,
    capability_role: str = "agency",
) -> dict[str, Any]:
    return {
        "id": runtime_id,
        "version": version,
        "summary": summary,
        "capability_role": capability_role,
        "capability_metric": capability_metric,
        "baseline_substitute": baseline_substitute,
        "evidence_status": evidence_status,
        "sunset_trigger": sunset_trigger,
        "stages": list(stages),
        "required_turn_stages": list(required_turn_stages),
        "invariants": [dict(item) for item in invariants],
        "inputs": dict(inputs),
        "outputs": dict(outputs),
        "ledger_format": {
            "runtime_id": "string",
            "stage": "string",
            "trace_id": "string",
            "started_at": "iso8601",
            "ended_at": "iso8601|null",
            "payload": "object",
            "result": "object",
        },
        "doc": doc,
    }
