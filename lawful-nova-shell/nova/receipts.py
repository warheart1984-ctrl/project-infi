from __future__ import annotations

import json
import time
from hashlib import sha256
from typing import Any


def make_receipt(
    *,
    provider: str,
    model: str,
    governed_request: dict[str, Any],
    raw_provider_response: dict[str, Any],
    normalized_completion: dict[str, Any],
    deterministic_core: bool,
    rsl_version: str,
    slice_id: str | None = None,
    slice_version: str | None = None,
    continuity_hash: str | None = None,
    governance_path: list[str] | None = None,
) -> dict[str, Any]:
    evidence = {
        "request_sha256": _hash_json(governed_request),
        "response_sha256": _hash_json(raw_provider_response),
        "completion_sha256": _hash_json(normalized_completion),
    }
    return {
        "provider": provider,
        "model": model,
        "governed_request": governed_request,
        "raw_provider_response": raw_provider_response,
        "normalized_completion": normalized_completion,
        "deterministic_core": deterministic_core,
        "rsl_version": rsl_version,
        "slice_id": slice_id,
        "slice_version": slice_version,
        "continuity_hash": continuity_hash,
        "governance_path": governance_path or [],
        "timestamp": int(time.time()),
        "evidence_chain": evidence,
    }


def _hash_json(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(data.encode("utf-8")).hexdigest()
