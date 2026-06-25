"""Register runtime AuditRecords as canonical PELRecords."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx

from src.cori.pel.ingest import pel_from_loop
from src.cori.pel.models import PELRecord
from src.cori.pel.storage import PelStorage, RuntimeClient


def runtime_base_url() -> str:
    return os.environ.get("RUNTIME_BASE_URL", "http://localhost:8000").rstrip("/")


def fetch_audit_record(
    audit_id: str,
    *,
    base_url: str | None = None,
    client: RuntimeClient | httpx.Client | None = None,
) -> dict[str, Any]:
    path = f"/v1/audit/{audit_id}"
    if client is not None:
        response = client.get(path)
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()
            return response.json()
        if getattr(response, "status_code", 500) != 200:
            raise RuntimeError(f"GET {path} failed: {getattr(response, 'text', response)}")
        return response.json()

    url_base = (base_url or runtime_base_url()).rstrip("/")
    with httpx.Client(base_url=url_base, timeout=10.0) as http:
        response = http.get(path)
        response.raise_for_status()
        return response.json()


def _parse_observed_at(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def audit_to_pel(audit: dict[str, Any]) -> PELRecord:
    """Map a runtime audit JSON document to a canonical PELRecord."""
    return pel_from_loop(
        audit_id=audit["audit_id"],
        subject_id=UUID(str(audit["subject_id"])),
        asset_id=UUID(str(audit["asset_id"])),
        evidence_id=UUID(str(audit["evidence_id"])),
        validation_id=UUID(str(audit["validation_id"])),
        decision=audit["decision"],
        loop_hash=audit["loop_hash"],
        observed_at=_parse_observed_at(audit["created_at"]),
    )


def register_pel_record(
    audit_id: str,
    storage: PelStorage,
    *,
    base_url: str | None = None,
    client: RuntimeClient | httpx.Client | None = None,
) -> PELRecord:
    """Fetch audit from runtime, convert to PEL, persist, and return."""
    audit = fetch_audit_record(audit_id, base_url=base_url, client=client)
    pel = audit_to_pel(audit)
    storage.save_pel_record(pel)
    return pel
