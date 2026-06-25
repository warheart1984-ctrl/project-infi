"""Formal cog_runtime bridge types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CortexPlan:
    runtime_id: str
    artifact: dict[str, Any]
    session_trace: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "artifact": dict(self.artifact),
            "session_trace": list(self.session_trace),
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> CortexPlan:
        return cls(
            runtime_id=str(row.get("runtime_id") or "cognitive.planning"),
            artifact=dict(row.get("artifact") or row.get("planning_artifact") or row),
            session_trace=list(row.get("session_trace") or []),
        )


@dataclass(frozen=True, slots=True)
class CortexResult:
    runtime_id: str
    artifact: dict[str, Any]
    session_trace: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "artifact": dict(self.artifact),
            "session_trace": list(self.session_trace),
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> CortexResult:
        return cls(
            runtime_id=str(row.get("runtime_id") or "cognitive.execution"),
            artifact=dict(row.get("artifact") or row.get("execution_artifact") or row),
            session_trace=list(row.get("session_trace") or []),
        )
