"""Append-only diagnostic claim ledger."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

ClaimLabel = Literal["asserted", "proven", "rejected"]
LEDGER_VERSION = "mechanic.ledger.v1"


@dataclass(slots=True)
class DiagnosticClaimRecord:
    record_id: str
    case_id: str
    mode: str
    invariant_id: str
    code: str
    claim_status: ClaimLabel
    claim_label: ClaimLabel
    reviewer: str
    reason: str
    drift_summary: str
    evidence_hash: str
    recorded_at_utc: str
    reconstruction_plan_ref: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    ledger_version: str = LEDGER_VERSION

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_claim_record(
    *,
    case_id: str,
    mode: str,
    invariant_id: str,
    code: str,
    claim_label: ClaimLabel,
    reviewer: str,
    reason: str,
    drift_summary: str,
    evidence_hash: str,
    reconstruction_plan_ref: str = "",
    evidence_refs: list[str] | None = None,
) -> DiagnosticClaimRecord:
    recorded_at = datetime.now(UTC).isoformat()
    seed = _hash_text(
        json.dumps(
            {
                "case_id": case_id,
                "code": code,
                "drift_summary": drift_summary,
                "evidence_hash": evidence_hash,
                "recorded_at_utc": recorded_at,
            },
            sort_keys=True,
        )
    )
    return DiagnosticClaimRecord(
        record_id=f"mc-{seed[:16]}",
        case_id=case_id,
        mode=mode,
        invariant_id=invariant_id,
        code=code,
        claim_status=claim_label,
        claim_label=claim_label,
        reviewer=reviewer,
        reason=reason,
        drift_summary=drift_summary,
        evidence_hash=evidence_hash,
        recorded_at_utc=recorded_at,
        reconstruction_plan_ref=reconstruction_plan_ref,
        evidence_refs=list(evidence_refs or []),
    )


def append_claim_record(record: DiagnosticClaimRecord, ledger_path: Path) -> None:
    target = ledger_path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.model_dump(), sort_keys=True))
        handle.write("\n")


def ledger_summary(ledger_path: Path) -> dict[str, Any]:
    target = ledger_path.expanduser().resolve()
    if not target.exists():
        return {"exists": False, "entries": 0}
    entries = 0
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries += 1
    return {"exists": True, "entries": entries, "path": str(target)}
