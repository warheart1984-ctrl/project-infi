"""Append-only fault journal — runtime invariant violations with run/span linkage."""

# Mythic: Fault Journal
# Engineering: FaultJournalStore
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from src.datetime_compat import UTC
import json
import os
import threading
from pathlib import Path
from typing import Any, TypedDict
from uuid import uuid4

FAULT_JOURNAL_VERSION = "1.0"
FAULT_JOURNAL_FILENAME = "faults.jsonl"

FAULT_CODE_INVARIANT_BREACH = "INVARIANT_BREACH"
FAULT_CODE_BRIDGE_BINDING_MISMATCH = "BRIDGE_BINDING_MISMATCH"
FAULT_CODE_AUTHORITY_MISMATCH = "AUTHORITY_MISMATCH"
FAULT_CODE_SPAN_ORPHAN = "SPAN_ORPHAN"
FAULT_CODE_RUNTIME_TIMEOUT = "RUNTIME_TIMEOUT"

FAULT_CODES: frozenset[str] = frozenset(
    {
        FAULT_CODE_INVARIANT_BREACH,
        FAULT_CODE_BRIDGE_BINDING_MISMATCH,
        FAULT_CODE_AUTHORITY_MISMATCH,
        FAULT_CODE_SPAN_ORPHAN,
        FAULT_CODE_RUNTIME_TIMEOUT,
    }
)

SPINE_HALT_TO_INVARIANT_ID: dict[str, str] = {
    "rls_substrate": "operator_instant_compose",
    "aris_admit": "aris_before_cortex",
    "jarvis_authorize": "jarvis_authority",
    "cortex_execute": "operator_fast_compose",
    "speaking_emit": "jarvis_authority",
}

SPINE_HALT_TO_FAULT_CODE: dict[str, str] = {
    "rls_substrate": FAULT_CODE_INVARIANT_BREACH,
    "aris_admit": FAULT_CODE_INVARIANT_BREACH,
    "jarvis_authorize": FAULT_CODE_AUTHORITY_MISMATCH,
    "cortex_execute": FAULT_CODE_INVARIANT_BREACH,
    "speaking_emit": FAULT_CODE_INVARIANT_BREACH,
}

_LOCK = threading.Lock()
_DEFAULT_STORE: FaultJournalStore | None = None


class FaultRecordV1(TypedDict, total=False):
    record_id: str
    journal_version: str
    run_id: str
    span_id: str
    invariant_id: str
    fault_code: str
    occurred_at: str
    detail: dict[str, Any]
    evidence_ref: str


@dataclass(slots=True)
class ExecutionContext:
    run_id: str
    span_id: str
    span_orphan: bool = False
    runtime_dir: str | Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "span_id": self.span_id,
            "span_orphan": self.span_orphan,
        }


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _default_runtime_root() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def resolve_execution_context(metadata: dict[str, Any] | None) -> ExecutionContext:
    """Resolve RUN_ID and SPAN_ID from session or turn metadata."""
    meta = dict(metadata or {})
    run_id = str(
        meta.get("run_id")
        or meta.get("jarvis_run_id")
        or meta.get("active_run_id")
        or meta.get("composed_run_id")
        or ""
    ).strip()
    if not run_id:
        run_id = f"run-{uuid4().hex[:16]}"

    span_id = str(
        meta.get("span_id")
        or meta.get("governed_span_id")
        or meta.get("composed_span_id")
        or meta.get("nova_face_id")
        or ""
    ).strip()
    span_orphan = False
    if not span_id:
        face = meta.get("nova_face") or {}
        if isinstance(face, dict):
            span_id = str(face.get("face_id") or "").strip()
    if not span_id:
        span_id = f"orphan-span-{uuid4().hex[:12]}"
        span_orphan = True

    runtime_dir = meta.get("fault_journal_runtime_dir") or meta.get("runtime_dir")
    return ExecutionContext(
        run_id=run_id,
        span_id=span_id,
        span_orphan=span_orphan,
        runtime_dir=runtime_dir,
    )


class FaultJournalStore:
    """Append-only JSONL writer and reader for fault recurrence metrics."""

    def __init__(self, runtime_root: str | Path | None = None) -> None:
        self.runtime_root = Path(runtime_root or _default_runtime_root())
        self.journal_dir = self.runtime_root / "fault-journal"
        self.journal_path = self.journal_dir / FAULT_JOURNAL_FILENAME
        self._lock = threading.Lock()
        self.journal_dir.mkdir(parents=True, exist_ok=True)

    def configure_runtime_root(self, runtime_root: str | Path) -> None:
        with self._lock:
            self.runtime_root = Path(runtime_root)
            self.journal_dir = self.runtime_root / "fault-journal"
            self.journal_path = self.journal_dir / FAULT_JOURNAL_FILENAME
            self.journal_dir.mkdir(parents=True, exist_ok=True)

    def append(self, record: FaultRecordV1) -> FaultRecordV1:
        payload = self._normalize_record(record)
        line = _stable_json(payload)
        with self._lock:
            self.journal_dir.mkdir(parents=True, exist_ok=True)
            with self.journal_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        return payload

    def read_recent(self, *, limit: int = 500) -> list[FaultRecordV1]:
        normalized_limit = max(1, min(int(limit or 500), 10_000))
        with self._lock:
            if not self.journal_path.exists():
                return []
            lines = self.journal_path.read_text(encoding="utf-8").splitlines()
        records: list[FaultRecordV1] = []
        for line in lines[-normalized_limit:]:
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                records.append(parsed)  # type: ignore[arg-type]
        return records

    def aggregate_recurrence(
        self,
        *,
        limit: int = 500,
    ) -> dict[str, Any]:
        records = self.read_recent(limit=limit)
        by_fault_code: dict[str, int] = {}
        by_invariant_fault: dict[str, int] = {}
        for row in records:
            code = str(row.get("fault_code") or "unknown")
            by_fault_code[code] = by_fault_code.get(code, 0) + 1
            inv = str(row.get("invariant_id") or "unknown")
            pair_key = f"{inv}|{code}"
            by_invariant_fault[pair_key] = by_invariant_fault.get(pair_key, 0) + 1
        return {
            "journal_version": FAULT_JOURNAL_VERSION,
            "record_count": len(records),
            "by_fault_code": by_fault_code,
            "by_invariant_fault": by_invariant_fault,
        }

    def _normalize_record(self, record: FaultRecordV1) -> FaultRecordV1:
        fault_code = str(record.get("fault_code") or FAULT_CODE_INVARIANT_BREACH).strip().upper()
        if fault_code not in FAULT_CODES:
            raise ValueError(f"invalid fault_code: {fault_code}")
        run_id = str(record.get("run_id") or "").strip()
        span_id = str(record.get("span_id") or "").strip()
        invariant_id = str(record.get("invariant_id") or "unknown").strip()
        if not run_id:
            raise ValueError("run_id is required")
        if not span_id:
            raise ValueError("span_id is required")
        detail = record.get("detail")
        if detail is not None and not isinstance(detail, dict):
            raise ValueError("detail must be a dict when provided")
        evidence_ref = record.get("evidence_ref")
        if evidence_ref is not None:
            evidence_ref = str(evidence_ref).strip() or None
        return FaultRecordV1(
            record_id=str(record.get("record_id") or f"fault-{uuid4().hex}"),
            journal_version=FAULT_JOURNAL_VERSION,
            run_id=run_id,
            span_id=span_id,
            invariant_id=invariant_id,
            fault_code=fault_code,
            occurred_at=str(record.get("occurred_at") or _utc_now_iso()),
            detail=dict(detail) if isinstance(detail, dict) else None,
            evidence_ref=evidence_ref,
        )


def get_fault_journal_store(runtime_root: str | Path | None = None) -> FaultJournalStore:
    global _DEFAULT_STORE
    if runtime_root is not None:
        return FaultJournalStore(runtime_root=runtime_root)
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = FaultJournalStore()
    return _DEFAULT_STORE


def record_fault(
    *,
    run_id: str,
    span_id: str,
    invariant_id: str,
    fault_code: str,
    detail: dict[str, Any] | None = None,
    evidence_ref: str | None = None,
    occurred_at: str | None = None,
    store: FaultJournalStore | None = None,
    runtime_root: str | Path | None = None,
) -> FaultRecordV1:
    """Append one fault record to the journal."""
    journal = store or get_fault_journal_store(runtime_root)
    return journal.append(
        FaultRecordV1(
            run_id=run_id,
            span_id=span_id,
            invariant_id=invariant_id,
            fault_code=fault_code,
            occurred_at=occurred_at or _utc_now_iso(),
            detail=detail,
            evidence_ref=evidence_ref,
        )
    )


def record_fault_from_context(
    *,
    metadata: dict[str, Any] | None,
    invariant_id: str,
    fault_code: str,
    detail: dict[str, Any] | None = None,
    evidence_ref: str | None = None,
    store: FaultJournalStore | None = None,
) -> FaultRecordV1:
    """Record a fault using RUN_ID/SPAN_ID resolved from execution metadata."""
    ctx = resolve_execution_context(metadata)
    merged_detail = dict(detail or {})
    if ctx.span_orphan:
        merged_detail.setdefault("span_resolution", "orphan_synthesized")
    journal = store or get_fault_journal_store(ctx.runtime_dir)
    return record_fault(
        run_id=ctx.run_id,
        span_id=ctx.span_id,
        invariant_id=invariant_id,
        fault_code=fault_code,
        detail=merged_detail or None,
        evidence_ref=evidence_ref,
        store=journal,
    )


def record_spine_invariant_fault(
    *,
    halt_stage: str,
    metadata: dict[str, Any] | None,
    spine_trace: list[dict[str, Any]] | None = None,
    store: FaultJournalStore | None = None,
) -> FaultRecordV1 | None:
    """Record a spine pipeline invariant breach at the evaluation boundary."""
    stage = str(halt_stage or "").strip()
    if not stage:
        return None
    invariant_id = SPINE_HALT_TO_INVARIANT_ID.get(stage, "unknown_invariant")
    fault_code = SPINE_HALT_TO_FAULT_CODE.get(stage, FAULT_CODE_INVARIANT_BREACH)
    meta = dict(metadata or {})
    if meta.get("bridge_binding_mismatch"):
        fault_code = FAULT_CODE_BRIDGE_BINDING_MISMATCH
    return record_fault_from_context(
        metadata=meta,
        invariant_id=invariant_id,
        fault_code=fault_code,
        detail={
            "halt_stage": stage,
            "spine_trace": list(spine_trace or []),
            "source": "spine_pipeline",
        },
        store=store,
    )


def query_recurrence(
    *,
    limit: int = 500,
    store: FaultJournalStore | None = None,
    runtime_root: str | Path | None = None,
) -> dict[str, Any]:
    """Public recurrence aggregation over recent fault records."""
    journal = store or get_fault_journal_store(runtime_root)
    return journal.aggregate_recurrence(limit=limit)


def reset_fault_journal(*, runtime_root: str | Path | None = None) -> None:
    """Test helper — remove journal file (not for production mutation paths)."""
    journal = get_fault_journal_store(runtime_root)
    with journal._lock:
        if journal.journal_path.exists():
            journal.journal_path.unlink()
