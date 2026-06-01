"""Ingestion invariant gate — fail closed before ledger mutation."""

from __future__ import annotations

from typing import Any

from src.ugr.ingestion.config import IngestionSource
from src.ugr.ingestion.sanitize import contains_blocked_secret


def validate_event(event: dict[str, Any], source: IngestionSource) -> dict[str, Any]:
    checks = {
        "source_enabled": source.enabled,
        "source_uri_present": bool(str(event.get("source_uri") or "").strip()),
        "title_present": bool(str(event.get("title") or "").strip()),
        "tenant_scope_present": bool(str(event.get("tenant_scope") or source.tenant_scope).strip()),
        "no_blocked_secrets": not contains_blocked_secret(
            " ".join(
                [
                    str(event.get("title") or ""),
                    str(event.get("summary") or ""),
                    str(event.get("raw_excerpt") or ""),
                ]
            )
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "status": "pass" if not failed else "fail",
        "allows": not failed,
        "checked_invariants": checks,
        "failed_invariants": failed,
    }


def validate_proposal(proposal: dict[str, Any], source: IngestionSource) -> dict[str, Any]:
    claim = dict(proposal.get("claim") or {})
    checks = {
        "claim_subject_present": bool(str(claim.get("subject") or "").strip()),
        "claim_predicate_present": bool(str(claim.get("predicate") or "").strip()),
        "claim_object_present": bool(str(claim.get("object") or "").strip()),
        "provenance_present": bool(proposal.get("event_id")) and bool(proposal.get("source_uri")),
        "confidence_bounded": 0.0 <= float(claim.get("confidence") or 0.0) <= 1.0,
        "source_enabled": source.enabled,
        "no_blocked_secrets": not contains_blocked_secret(
            " ".join([str(claim.get("subject") or ""), str(claim.get("object") or "")])
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "status": "pass" if not failed else "fail",
        "allows": not failed,
        "checked_invariants": checks,
        "failed_invariants": failed,
    }
