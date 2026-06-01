"""Sanitize raw ingestion payloads before normalization."""

from __future__ import annotations

import re
from typing import Any

MAX_EXCERPT_CHARS = 480
SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*\S+"),
    re.compile(r"-----BEGIN [A-Z ]+-----"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
)
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _clip(text: str, limit: int = MAX_EXCERPT_CHARS) -> str:
    normalized = " ".join(str(text or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def contains_blocked_secret(text: str) -> bool:
    haystack = str(text or "")
    return any(pattern.search(haystack) for pattern in SECRET_PATTERNS)


def sanitize_text(text: str) -> str:
    cleaned = EMAIL_PATTERN.sub("[redacted-email]", str(text or ""))
    for pattern in SECRET_PATTERNS:
        cleaned = pattern.sub("[redacted-secret]", cleaned)
    return _clip(cleaned)


def sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    payload = dict(record or {})
    sanitized = {}
    for key, value in payload.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_text(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_text(item) if isinstance(item, str) else item for item in value]
        else:
            sanitized[key] = value
    sanitized["sanitized"] = True
    return sanitized
