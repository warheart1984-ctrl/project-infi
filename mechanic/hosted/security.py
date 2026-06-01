"""Hosted Mechanic security primitives."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from src.datetime_compat import UTC

SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|private[_-]?key)([\"'\s:=]+)([^\"'\s,}]+)"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}"),
)


def verify_api_key(*, provided: str, expected_hash: str) -> bool:
    if not provided or not expected_hash:
        return False
    digest = hashlib.sha256(provided.encode("utf-8")).hexdigest()
    return hmac.compare_digest(digest, expected_hash)


def hash_api_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_github_webhook_signature(*, body: bytes, signature_header: str, webhook_secret: str) -> bool:
    if not webhook_secret:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def redact_text(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda m: f"{m.group(1) if m.lastindex and m.lastindex >= 1 else 'secret'}{m.group(2) if m.lastindex and m.lastindex >= 2 else '='}[REDACTED]", redacted)
    return redacted


def redact_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        result: dict[str, Any] = {}
        for key, value in payload.items():
            if re.search(r"(?i)(api[_-]?key|token|secret|password|private[_-]?key)", str(key)):
                result[key] = "[REDACTED]"
            else:
                result[key] = redact_json(value)
        return result
    if isinstance(payload, list):
        return [redact_json(item) for item in payload]
    if isinstance(payload, str):
        return redact_text(payload)
    return payload


def scrub_artifact_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() not in {".json", ".jsonl", ".md", ".txt", ".ndjson"}:
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
            scrubbed = json.dumps(redact_json(payload), sort_keys=True, indent=2)
        except json.JSONDecodeError:
            scrubbed = redact_text(text)
    else:
        scrubbed = redact_text(text)
    if scrubbed != text:
        path.write_text(scrubbed, encoding="utf-8")
        return True
    return False


def scrub_artifact_tree(case_dir: Path) -> list[str]:
    changed: list[str] = []
    for path in sorted(case_dir.rglob("*")):
        if scrub_artifact_file(path):
            changed.append(str(path))
    return changed


def append_audit_event(path: Path, *, event_type: str, actor: str, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "actor": actor,
        "payload": redact_json(payload),
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True))
        handle.write("\n")
