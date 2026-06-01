"""Normalize sanitized ingestion records into governed event documents."""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
from hashlib import sha256
from typing import Any

from src.ugr.ingestion.config import IngestionSource


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _stable_json(value: Any) -> str:
    import json

    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def normalize_records(records: list[dict[str, Any]], source: IngestionSource) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        payload = dict(record or {})
        source_uri = str(payload.get("source_uri") or payload.get("id") or f"{source.source_id}:{index}")
        event_id = sha256(_stable_json({"source": source.source_id, "uri": source_uri}).encode("utf-8")).hexdigest()[
            :16
        ]
        normalized.append(
            {
                "event_id": f"ingest-{event_id}",
                "timestamp": str(payload.get("published_at") or _utc_now_iso()),
                "source_id": source.source_id,
                "source_type": source.source_type,
                "source_uri": source_uri,
                "title": str(payload.get("title") or payload.get("name") or "untitled"),
                "summary": str(payload.get("summary") or payload.get("body") or payload.get("description") or ""),
                "actors": list(payload.get("actors") or []),
                "tags": list(payload.get("tags") or []),
                "tenant_scope": source.tenant_scope,
                "raw_excerpt": str(payload.get("summary") or payload.get("body") or "")[:240],
            }
        )
    return normalized
