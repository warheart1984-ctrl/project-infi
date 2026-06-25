"""Canonical normalization for PEL artifact ingestion."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.cori.pel.pel_verify import canonical_payload_hash

TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".csv", ".html", ".xml"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _guess_mime(path: Path) -> str:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return "text/plain"
    return "application/octet-stream"


def normalize_file(path: Path) -> dict[str, Any]:
    """Read file bytes, compute hash, and produce a canonical payload summary."""
    canonical_bytes = path.read_bytes()
    resolved = path.resolve()
    return {
        "canonical_bytes": canonical_bytes,
        "hash": sha256_bytes(canonical_bytes),
        "title": path.name,
        "payload_summary": {
            "size": len(canonical_bytes),
            "mime": _guess_mime(path),
            "path": str(resolved),
        },
        "source_uri": resolved.as_uri(),
    }


def normalize_url(url: str, *, title: str | None = None) -> dict[str, Any]:
    """Normalize a URL reference (metadata only; content hash is the URL string)."""
    canonical_bytes = url.strip().encode("utf-8")
    parsed = urlparse(url)
    return {
        "canonical_bytes": canonical_bytes,
        "hash": sha256_bytes(canonical_bytes),
        "title": title or parsed.path.rsplit("/", 1)[-1] or parsed.netloc or "url",
        "payload_summary": {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "path": parsed.path,
        },
        "source_uri": url,
    }


def normalize_json_object(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a JSON object (continuity/panel export row) with canonical JSON hashing."""
    payload_bytes = json.dumps(row, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    title = str(row.get("id") or row.get("event_type") or row.get("panel_id") or "json_row")
    return {
        "canonical_bytes": payload_bytes,
        "hash": canonical_payload_hash(row),
        "title": title,
        "payload_summary": {
            "keys": sorted(row.keys()),
            "event_type": row.get("event_type"),
            "panel_id": row.get("panel_id"),
        },
        "source_uri": row.get("source_uri"),
    }


def normalize_jsonl_row(row: dict[str, Any]) -> dict[str, Any]:
    """Alias for JSONL continuity/panel exports."""
    return normalize_json_object(row)


def normalize_continuity_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a continuity store row export."""
    enriched = dict(row)
    enriched.setdefault("artifact_kind", "continuity_row")
    if enriched.get("source_uri") is None and row.get("id"):
        enriched["source_uri"] = f"continuity://event/{row['id']}"
    return normalize_json_object(enriched)


def normalize_panel_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a panel store row export."""
    enriched = dict(row)
    enriched.setdefault("artifact_kind", "panel_row")
    if enriched.get("source_uri") is None:
        panel_id = row.get("panel_id") or row.get("id")
        if panel_id:
            enriched["source_uri"] = f"panel://{panel_id}"
    return normalize_json_object(enriched)


def normalize_text(text: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize inline text content."""
    meta = meta or {}
    canonical_bytes = text.encode("utf-8")
    return {
        "canonical_bytes": canonical_bytes,
        "hash": sha256_bytes(canonical_bytes),
        "title": meta.get("title", "inline_text"),
        "payload_summary": {"length": len(text)},
        "source_uri": meta.get("source_uri"),
    }
