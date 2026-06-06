"""Temporal replay ingestors for operator accountability timelines."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.temporal_replay.event import (
    CLOUD_INVARIANT_SET_VERSION,
    PROJECT_INFI_CONTRACT_VERSION,
    new_event_id,
    payload_hash,
    resolve_emitter,
)
from src.temporal_replay.paths import default_runtime_dir, operator_ledger_path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class OperatorDecisionIngestor:
    """Read operator ledger JSONL rows and emit temporal replay envelopes."""

    def __init__(self, *, runtime_dir: Path | None = None):
        self._runtime_dir = runtime_dir or default_runtime_dir()

    def ingest(self, scope_id: str, *, start_sequence: int = 0) -> list[dict[str, Any]]:
        path = operator_ledger_path(scope_id, runtime_dir=self._runtime_dir)
        if not path.is_file():
            return []
        events: list[dict[str, Any]] = []
        seq = start_sequence
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                emitter = resolve_emitter("operator_decision")
                events.append(
                    {
                        "event_id": new_event_id(
                            "operator_decision",
                            str(row.get("decision_id") or scope_id),
                            seq,
                        ),
                        "subject_type": "operator_session",
                        "subject_id": scope_id,
                        "timestamp_utc": str(row.get("recorded_at") or _utc_now_iso()),
                        "sequence": seq,
                        "kind": "operator_decision",
                        "summary": str(
                            row.get("summary") or row.get("decision_kind") or "operator decision"
                        ),
                        "emitter": emitter,
                        "law_context": {
                            "law_id": "project_infi_law",
                            "law_version": "",
                            "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                            "invariant_version": CLOUD_INVARIANT_SET_VERSION,
                        },
                        "boundary": {
                            "tenant_id": str(row.get("tenant_id") or ""),
                            "boundary_digest": "",
                            "cloud_identity_hash": "",
                        },
                        "causal_parents": list(row.get("causal_parents") or []),
                        "payload_ref": {
                            "store": "operator_ledger",
                            "path": str(path),
                            "hash": payload_hash(row),
                            "decision_id": str(row.get("decision_id") or ""),
                        },
                        "receipt_ref": (
                            {
                                "mission_id": str(row.get("mission_id") or ""),
                                "ledger_root": "",
                                "receipt_sig": "",
                            }
                            if row.get("mission_id")
                            else None
                        ),
                    }
                )
                seq += 1
        return events

    def backfill_receipts(
        self,
        scope_id: str,
        *,
        runtime_dir: Path | None = None,
        tenant_id: str | None = None,
        start_sequence: int = 0,
    ) -> list[dict[str, Any]]:
        """Idempotent backfill from mission receipt store when live emit missed."""
        from src.operator_decision_ledger import append_urg_receipt_event

        root = runtime_dir or self._runtime_dir
        try:
            from src.ugr.mission.mission_receipt_store import MissionReceiptStore

            store = MissionReceiptStore(runtime_dir=str(root), tenant_id=tenant_id)
            receipts = store._iter_records()[-50:]
        except Exception:
            return []

        events: list[dict[str, Any]] = []
        seq = start_sequence
        for envelope in receipts:
            schema = dict(envelope.get("mission_receipt_schema") or envelope.get("schema") or {})
            mission_id = str(envelope.get("mission_id") or schema.get("mission_id") or "")
            if not mission_id:
                continue
            federation = None
            if schema.get("federation_digest"):
                federation = {
                    "federation_digest": str(schema.get("federation_digest") or ""),
                    "counterparty_receipt_ref": dict(schema.get("counterparty_receipt_ref") or {}),
                }
            row = append_urg_receipt_event(
                mission_id=mission_id,
                tenant_id=str(envelope.get("tenant_id") or tenant_id or ""),
                session_id=scope_id if scope_id != "global" else None,
                outcome="completed" if str(schema.get("outcome") or "") == "completed" else "failed",
                federation=federation,
            )
            if not row:
                continue
            emitter = resolve_emitter("operator_decision")
            events.append(
                {
                    "event_id": new_event_id("operator_decision", mission_id, seq),
                    "subject_type": "operator_session",
                    "subject_id": scope_id,
                    "timestamp_utc": str(row.get("recorded_at") or _utc_now_iso()),
                    "sequence": seq,
                    "kind": "operator_decision",
                    "summary": str(row.get("summary") or "urg receipt backfill"),
                    "emitter": emitter,
                    "law_context": {
                        "law_id": "urg.cloud_forge",
                        "law_version": str(schema.get("urg_version") or ""),
                        "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                        "invariant_version": str(
                            schema.get("invariant_version") or CLOUD_INVARIANT_SET_VERSION
                        ),
                    },
                    "boundary": {
                        "tenant_id": str(envelope.get("tenant_id") or ""),
                        "boundary_digest": str(schema.get("boundary_digest") or ""),
                        "cloud_identity_hash": str(schema.get("cloud_identity_hash") or ""),
                    },
                    "causal_parents": list(row.get("causal_parents") or []),
                    "payload_ref": {
                        "store": "operator_ledger",
                        "path": str(operator_ledger_path(scope_id, runtime_dir=root)),
                        "hash": payload_hash(row),
                        "decision_id": str(row.get("decision_id") or ""),
                    },
                    "receipt_ref": {
                        "mission_id": mission_id,
                        "ledger_root": str(schema.get("ledger_root") or ""),
                        "receipt_sig": str(schema.get("receipt_sig") or ""),
                    },
                }
            )
            seq += 1
        return events


def ingest_subject(
    subject_type: str,
    subject_id: str,
    *,
    runtime_dir: Path | None = None,
    tenant_id: str | None = None,
    workflow_run: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Ingest temporal replay events for a subject scope."""
    _ = workflow_run
    root = runtime_dir or default_runtime_dir()
    events: list[dict[str, Any]] = []
    seq = 0

    if subject_type in {"operator_session", "session"}:
        ingestor = OperatorDecisionIngestor(runtime_dir=root)
        events.extend(ingestor.ingest(subject_id, start_sequence=seq))
        seq = len(events)
        events.extend(
            ingestor.backfill_receipts(
                subject_id,
                runtime_dir=root,
                tenant_id=tenant_id,
                start_sequence=seq,
            )
        )
    return events
