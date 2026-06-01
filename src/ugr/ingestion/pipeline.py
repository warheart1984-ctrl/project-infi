"""Governed ingestion pipeline — fetch to ledger without touching models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable
import os

from src.ugr.ingestion.config import IngestionConfig, IngestionSource
from src.ugr.ingestion.extract import extract_signals
from src.ugr.ingestion.fetchers import fetch_source
from src.ugr.ingestion.invariants import validate_event, validate_proposal
from src.ugr.ingestion.normalize import normalize_records
from src.ugr.ingestion.sanitize import contains_blocked_secret, sanitize_record
from src.ugr.pattern_ledger import PatternLedgerStore


INGESTION_PIPELINE_ID = "aais.ugr.ingestion"
INGESTION_PIPELINE_VERSION = "0.1"

FetchFn = Callable[[IngestionSource], list[dict[str, Any]]]


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _default_runtime_root() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / ".runtime"


@dataclass
class IngestionRunResult:
    run_id: str
    source_id: str
    status: str
    fetched_count: int
    accepted_count: int
    rejected_count: int
    dry_run: bool
    events: list[dict[str, Any]] = field(default_factory=list)
    accepted: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_id": INGESTION_PIPELINE_ID,
            "pipeline_version": INGESTION_PIPELINE_VERSION,
            "run_id": self.run_id,
            "source_id": self.source_id,
            "status": self.status,
            "fetched_count": self.fetched_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "dry_run": self.dry_run,
            "events": self.events,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "trace": self.trace,
        }


class GovernedIngestionPipeline:
    """Curated internet digestion with invariant gate and ledger proposals."""

    def __init__(
        self,
        *,
        config: IngestionConfig | None = None,
        ledger: PatternLedgerStore | None = None,
        runtime_root: str | Path | None = None,
        fetch_fn: FetchFn | None = None,
    ):
        root = Path(runtime_root or _default_runtime_root())
        self.config = config or IngestionConfig()
        self.ledger = ledger or PatternLedgerStore(runtime_dir=root)
        self.runtime_root = root
        self.fetch_fn = fetch_fn or fetch_source
        self.runs_path = root / "ugr" / "ingestion" / "runs.jsonl"
        self.runs_path.parent.mkdir(parents=True, exist_ok=True)

    def _append_run_log(self, result: IngestionRunResult) -> None:
        with self.runs_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(result.to_dict(), sort_keys=True, default=str) + "\n")

    def run_source(
        self,
        source_id: str,
        *,
        dry_run: bool = False,
        records: list[dict[str, Any]] | None = None,
    ) -> IngestionRunResult:
        source = self.config.get(source_id)
        run_id = sha256(f"{source_id}:{_utc_now_iso()}".encode("utf-8")).hexdigest()[:16]
        trace: list[dict[str, Any]] = []

        if source is None:
            result = IngestionRunResult(
                run_id=run_id,
                source_id=source_id,
                status="rejected",
                fetched_count=0,
                accepted_count=0,
                rejected_count=0,
                dry_run=dry_run,
                trace=[{"stage": "config", "error": "unknown_source"}],
            )
            self._append_run_log(result)
            return result

        if not source.enabled:
            result = IngestionRunResult(
                run_id=run_id,
                source_id=source_id,
                status="rejected",
                fetched_count=0,
                accepted_count=0,
                rejected_count=0,
                dry_run=dry_run,
                trace=[{"stage": "policy", "error": "source_disabled"}],
            )
            self._append_run_log(result)
            return result

        raw_records = list(records if records is not None else self.fetch_fn(source))
        trace.append({"stage": "fetch", "count": len(raw_records)})

        sanitized: list[dict[str, Any]] = []
        quarantined_fetch = 0
        for record in raw_records:
            raw_blob = json.dumps(record, default=str)
            if contains_blocked_secret(raw_blob):
                quarantined_fetch += 1
                trace.append({"stage": "sanitize", "quarantined": True, "reason": "blocked_secret_pattern"})
                continue
            sanitized.append(sanitize_record(record))
        trace.append({"stage": "sanitize", "count": len(sanitized), "quarantined": quarantined_fetch})

        events = normalize_records(sanitized, source)
        gated_events: list[dict[str, Any]] = []
        for event in events:
            gate = validate_event(event, source)
            trace.append({"stage": "event_invariants", "event_id": event.get("event_id"), "gate": gate})
            if gate["allows"]:
                gated_events.append(event)

        proposals = extract_signals(gated_events)
        trace.append({"stage": "extract", "proposal_count": len(proposals)})

        accepted: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for proposal in proposals:
            gate = validate_proposal(proposal, source)
            if not gate["allows"]:
                rejected.append({**proposal, "gate": gate})
                continue
            claim = dict(proposal.get("claim") or {})
            claim["tenant_scope"] = source.tenant_scope
            claim["claim_id"] = self.ledger.make_claim_id(
                str(claim.get("subject") or ""),
                str(claim.get("predicate") or ""),
                str(claim.get("object") or ""),
                "ingestion",
            )
            if dry_run:
                accepted.append({"proposal": proposal, "gate": gate, "dry_run": True})
                continue
            evidence = self.ledger.append_evidence(
                source_type=source.source_type,
                source_uri=str(proposal.get("source_uri") or ""),
                classification="pending_review",
                summary=str(proposal.get("claim", {}).get("object") or "")[:240],
                tenant_scope=source.tenant_scope,
                parsed_claims=[claim],
            )
            claim["evidence_refs"] = [evidence.get("evidence_id", proposal.get("event_id"))]
            record = self.ledger.append_claim(claim)
            accepted.append({"claim": record, "evidence": evidence, "gate": gate})

        status = "ok" if accepted else "no_accepted_proposals"
        if quarantined_fetch and not accepted:
            status = "quarantined"
        elif quarantined_fetch and accepted:
            status = "ok"
        if not gated_events and raw_records and quarantined_fetch == len(raw_records):
            status = "quarantined"

        result = IngestionRunResult(
            run_id=run_id,
            source_id=source_id,
            status=status,
            fetched_count=len(raw_records),
            accepted_count=len(accepted),
            rejected_count=len(rejected),
            dry_run=dry_run,
            events=gated_events,
            accepted=accepted,
            rejected=rejected,
            trace=trace,
        )
        self._append_run_log(result)
        return result

    def run_enabled_sources(self, *, dry_run: bool = False) -> list[dict[str, Any]]:
        return [self.run_source(source.source_id, dry_run=dry_run).to_dict() for source in self.config.enabled_sources()]
