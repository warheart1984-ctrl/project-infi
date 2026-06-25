"""AgentFaultJournal — append-only NDJSON fault log for agent runs."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

JOURNAL_VERSION = "agent_fault_journal.v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentFaultJournal:
    """Record input/output deviations with operator-assigned fault codes."""

    def __init__(self, path: Path | str | None = None) -> None:
        self._lock = threading.Lock()
        self._path = Path(path) if path else None

    def configure_path(self, path: Path | str | None) -> None:
        self._path = Path(path) if path else None

    def _resolve_path(self) -> Path:
        if self._path is None:
            runtime = Path(__file__).resolve().parents[1] / ".runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            return runtime / "agent-faults.ndjson"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        return self._path

    def record(
        self,
        *,
        run_id: str,
        phase: str,
        input_ref: str,
        output_ref: str,
        expected: str = "",
        actual: str = "",
        fault_code: str = "",
        severity: str = "medium",
        loop_stage: str = "detect",
        notes: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entry = {
            "journal_version": JOURNAL_VERSION,
            "event_id": f"fault_{uuid4().hex}",
            "ts": _utc_now(),
            "run_id": str(run_id or "").strip() or "unknown",
            "phase": str(phase or "output").strip() or "output",
            "input_ref": str(input_ref or "")[:500],
            "output_ref": str(output_ref or "")[:500],
            "expected": str(expected or "")[:500],
            "actual": str(actual or "")[:500],
            "fault_code": str(fault_code or "").strip(),
            "severity": str(severity or "medium").strip() or "medium",
            "loop_stage": str(loop_stage or "detect").strip() or "detect",
            "notes": str(notes or "")[:1000],
            "metadata": dict(metadata or {}),
        }
        with self._lock:
            path = self._resolve_path()
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def record_agent_failure(
        self,
        *,
        run_id: str,
        goal: str,
        error: str,
        fault_code: str = "AGENT_RUN_FAILED",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        return self.record(
            run_id=run_id,
            phase="execution",
            input_ref=goal[:500],
            output_ref=error[:500],
            expected="successful agent completion",
            actual=error[:500],
            fault_code=fault_code,
            severity="high",
            loop_stage="detect",
            metadata={"session_id": session_id or ""},
        )
