"""Unified pattern ledger v0.5 — AAIS, UGR, and Wolf CoG adapter."""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
from hashlib import sha256
import json
import os
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4


UNIFIED_LEDGER_ID = "aais.unified_pattern_ledger"
UNIFIED_LEDGER_VERSION = "0.5"

RECORD_TYPES = frozenset({"claim", "evidence", "provenance_link", "pattern_event"})
CLAIM_STATUSES = frozenset({"proposed", "accepted", "rejected", "contested"})
CLASSIFICATIONS = frozenset(
    {
        "success",
        "failure",
        "near_miss",
        "recovered_failure",
        "unresolved",
        "pending_review",
    }
)
SUPPORT_TYPES = frozenset({"supports", "contradicts", "refines"})


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _default_runtime_root() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[2] / ".runtime"


def normalize_cogos_pattern_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Wolf CoG cogos daemon pattern row into v0.5 pattern_event shape."""
    payload = dict(record or {})
    classification = str(payload.get("classification") or "pending_review").strip().lower()
    if classification not in CLASSIFICATIONS:
        classification = "pending_review"
    pattern_id = str(payload.get("pattern_id") or f"pattern-{uuid4().hex[:12]}")
    return {
        "record_type": "pattern_event",
        "ledger_version": UNIFIED_LEDGER_VERSION,
        "timestamp": str(payload.get("timestamp") or _utc_now_iso()),
        "origin": "cogos",
        "pattern_id": pattern_id,
        "event_type": str(payload.get("event") or payload.get("source") or "pattern.classified"),
        "classification": classification,
        "severity": str(payload.get("severity") or "S1"),
        "subject": str(payload.get("subject") or ""),
        "summary": str(payload.get("summary") or "")[:240],
        "signature_only": True,
        "tenant_scope": str(payload.get("tenant_scope") or "global"),
        "evidence_refs": [pattern_id],
        "source_payload": {
            "source": payload.get("source"),
            "status": payload.get("status"),
            "signature": payload.get("signature"),
        },
    }


def normalize_detachment_pattern_event(entry: dict[str, Any]) -> dict[str, Any]:
    """Normalize AAIS detachment guard entries into v0.5 pattern_event shape."""
    payload = dict(entry or {})
    decision = str(payload.get("decision") or "blocked").strip().lower()
    classification = "near_miss" if decision == "blocked" else "success"
    event_id = str(payload.get("event_id") or f"cpl_{uuid4().hex[:12]}")
    return {
        "record_type": "pattern_event",
        "ledger_version": UNIFIED_LEDGER_VERSION,
        "timestamp": str(payload.get("timestamp") or _utc_now_iso()),
        "origin": "detachment_guard",
        "pattern_id": event_id,
        "event_type": str(payload.get("type") or "detachment_attempt"),
        "classification": classification,
        "severity": str(payload.get("severity") or "S3"),
        "subject": str(payload.get("source_class") or "unknown_source"),
        "summary": str(payload.get("vector") or payload.get("decision") or "")[:240],
        "signature_only": bool(payload.get("signature_only", True)),
        "tenant_scope": "global",
        "evidence_refs": [event_id],
        "source_payload": {
            "vector": payload.get("vector"),
            "packet_type": payload.get("packet_type"),
            "runtime_context": payload.get("runtime_context"),
            "source_fingerprint": payload.get("source_fingerprint"),
        },
    }


class UnifiedPatternLedger:
    """Canonical append-only ledger for claims, evidence, provenance, and events."""

    def __init__(self, runtime_root: str | Path | None = None):
        self.runtime_root = Path(runtime_root or _default_runtime_root())
        self.unified_dir = self.runtime_root / "collective-pattern-ledger" / "unified"
        self.legacy_detachment_path = self.runtime_root / "collective-pattern-ledger" / "detachment-patterns.jsonl"
        self._lock = threading.Lock()
        self.unified_dir.mkdir(parents=True, exist_ok=True)
        self.legacy_detachment_path.parent.mkdir(parents=True, exist_ok=True)

    def configure_runtime_root(self, runtime_root: str | Path) -> None:
        with self._lock:
            self.runtime_root = Path(runtime_root)
            self.unified_dir = self.runtime_root / "collective-pattern-ledger" / "unified"
            self.legacy_detachment_path = self.runtime_root / "collective-pattern-ledger" / "detachment-patterns.jsonl"
            self.unified_dir.mkdir(parents=True, exist_ok=True)
            self.legacy_detachment_path.parent.mkdir(parents=True, exist_ok=True)

    def _path_for(self, record_type: str) -> Path:
        mapping = {
            "claim": self.unified_dir / "claims.jsonl",
            "evidence": self.unified_dir / "evidence.jsonl",
            "provenance_link": self.unified_dir / "provenance.jsonl",
            "pattern_event": self.unified_dir / "pattern_events.jsonl",
        }
        return mapping[str(record_type)]

    @property
    def claims_path(self) -> Path:
        return self._path_for("claim")

    def _append_jsonl(self, path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(_stable_json(record) + "\n")

    def _validate_record(self, record: dict[str, Any]) -> dict[str, Any]:
        record_type = str(record.get("record_type") or "").strip().lower()
        if record_type not in RECORD_TYPES:
            raise ValueError(f"invalid record_type: {record_type}")
        payload = {
            **record,
            "record_type": record_type,
            "ledger_version": UNIFIED_LEDGER_VERSION,
            "timestamp": str(record.get("timestamp") or _utc_now_iso()),
            "ledger_id": UNIFIED_LEDGER_ID,
        }
        if record_type == "claim":
            status = str(payload.get("status") or "proposed").strip().lower()
            if status not in CLAIM_STATUSES:
                raise ValueError(f"invalid claim status: {status}")
            payload["status"] = status
        if record_type == "evidence":
            classification = str(payload.get("classification") or "pending_review").strip().lower()
            if classification not in CLASSIFICATIONS:
                classification = "pending_review"
            payload["classification"] = classification
        if record_type == "provenance_link":
            support = str(payload.get("support_type") or "supports").strip().lower()
            if support not in SUPPORT_TYPES:
                raise ValueError(f"invalid support_type: {support}")
            payload["support_type"] = support
        return payload

    def append_record(self, record: dict[str, Any]) -> dict[str, Any]:
        payload = self._validate_record(record)
        with self._lock:
            self._append_jsonl(self._path_for(payload["record_type"]), payload)
        return payload

    def append_claim(self, claim: dict[str, Any], *, origin: str = "ugr") -> dict[str, Any]:
        claim_id = str(
            claim.get("claim_id")
            or sha256(
                _stable_json(
                    {
                        "subject": claim.get("subject"),
                        "predicate": claim.get("predicate"),
                        "object": claim.get("object"),
                        "source_lane": claim.get("source_lane"),
                    }
                ).encode("utf-8")
            ).hexdigest()[:16]
        )
        evidence_refs = list(claim.get("evidence_refs") or [])
        record = self.append_record(
            {
                "record_type": "claim",
                "origin": origin,
                "claim_id": f"claim-{claim_id}" if not str(claim_id).startswith("claim-") else claim_id,
                "subject": claim.get("subject"),
                "predicate": claim.get("predicate"),
                "object": claim.get("object"),
                "confidence": float(claim.get("confidence") or 0.0),
                "source_lane": claim.get("source_lane"),
                "status": claim.get("status") or "proposed",
                "tenant_scope": claim.get("tenant_scope") or "global",
                "evidence_refs": evidence_refs,
            }
        )
        for ref in evidence_refs:
            if str(ref).startswith("evidence-"):
                self.append_provenance_link(
                    node_or_edge_id=record["claim_id"],
                    evidence_id=str(ref),
                    support_type="supports",
                    weight=float(claim.get("confidence") or 0.5),
                )
        if str(record.get("status") or "") == "accepted":
            try:
                from src.ugr.rewards.reward_hooks import emit_pattern_claim_accepted

                emit_pattern_claim_accepted(
                    tenant_id=str(record.get("tenant_scope") or "global"),
                    operator_id=str(claim.get("operator_id") or "operator"),
                    claim_id=str(record.get("claim_id") or ""),
                    classification="accepted",
                )
            except Exception:
                pass
        return record

    def append_evidence(
        self,
        *,
        source_type: str,
        source_uri: str,
        classification: str,
        summary: str,
        tenant_scope: str = "global",
        parsed_claims: list[dict[str, Any]] | None = None,
        origin: str = "ugr",
    ) -> dict[str, Any]:
        evidence_id = sha256(
            _stable_json({"source_type": source_type, "source_uri": source_uri, "summary": summary[:240]}).encode(
                "utf-8"
            )
        ).hexdigest()[:16]
        return self.append_record(
            {
                "record_type": "evidence",
                "origin": origin,
                "evidence_id": f"evidence-{evidence_id}",
                "source_type": source_type,
                "source_uri": source_uri,
                "classification": classification,
                "summary": summary[:240],
                "tenant_scope": tenant_scope,
                "parsed_claims": list(parsed_claims or []),
            }
        )

    def append_provenance_link(
        self,
        *,
        node_or_edge_id: str,
        evidence_id: str,
        support_type: str = "supports",
        weight: float = 0.5,
        origin: str = "ugr",
    ) -> dict[str, Any]:
        provenance_id = sha256(
            _stable_json(
                {
                    "node_or_edge_id": node_or_edge_id,
                    "evidence_id": evidence_id,
                    "support_type": support_type,
                }
            ).encode("utf-8")
        ).hexdigest()[:16]
        return self.append_record(
            {
                "record_type": "provenance_link",
                "origin": origin,
                "provenance_id": f"prov-{provenance_id}",
                "node_or_edge_id": node_or_edge_id,
                "evidence_id": evidence_id,
                "support_type": support_type,
                "weight": round(max(0.0, min(1.0, float(weight))), 3),
            }
        )

    def append_pattern_event(self, entry: dict[str, Any], *, mirror_legacy: bool = True) -> dict[str, Any]:
        if entry.get("record_type") == "pattern_event":
            normalized = self._validate_record(entry)
        elif entry.get("type") in {"detachment_attempt", "detachment_readmission"}:
            normalized = normalize_detachment_pattern_event(entry)
        elif entry.get("pattern_id") and entry.get("classification"):
            normalized = normalize_cogos_pattern_record(entry)
        else:
            normalized = normalize_detachment_pattern_event(entry)
        with self._lock:
            self._append_jsonl(self._path_for("pattern_event"), normalized)
            if mirror_legacy and normalized.get("origin") == "detachment_guard":
                self._append_jsonl(self.legacy_detachment_path, dict(entry))
        return normalized

    def _read_jsonl(self, path: Path, *, limit: int = 200) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows[-max(1, int(limit or 200)) :]

    def read_claims(self, *, tenant_scope: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        rows = self._read_jsonl(self._path_for("claim"), limit=limit)
        if tenant_scope:
            return [row for row in rows if row.get("tenant_scope") == tenant_scope][-limit:]
        return rows

    def query_related(self, terms: list[str], *, tenant_scope: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        normalized = [" ".join(str(term).split()).strip().lower() for term in terms if str(term).strip()]
        if not normalized:
            return []
        claims = self.read_claims(tenant_scope=tenant_scope, limit=max(limit * 4, 80))
        matches: list[dict[str, Any]] = []
        for row in claims:
            haystack = " ".join(
                [str(row.get("subject") or ""), str(row.get("predicate") or ""), str(row.get("object") or "")]
            ).lower()
            if any(term in haystack for term in normalized):
                matches.append(row)
        return matches[-limit:]


unified_pattern_ledger = UnifiedPatternLedger()
