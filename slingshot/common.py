"""Shared AI Slingshot utilities."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Literal

ClaimLabel = Literal["asserted", "proven", "rejected"]

FRAME_VERSION = "slingshot.frame.v1"
PACKET_VERSION = "slingshot.packet.v1"
IMPACT_VERSION = "slingshot.impact_receipt.v1"
DEFAULT_SLINGSHOT_ROOT = Path(".runtime/slingshot")
DEFAULT_MECHANIC_ROOT = Path(".runtime/mechanic")
DEFAULT_PACKET_TTL_MINUTES = 15


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_stable(payload: dict[str, Any], *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(payload, sort_keys=True, indent=2)
    return json.dumps(payload, sort_keys=True)


def slingshot_case_dir(case_id: str, *, runtime_root: Path | None = None) -> Path:
    root = runtime_root or DEFAULT_SLINGSHOT_ROOT
    return root / case_id


def mechanic_case_dir(case_id: str, *, runtime_root: Path | None = None) -> Path:
    root = runtime_root or DEFAULT_MECHANIC_ROOT
    return root / case_id


def frame_path(case_id: str, *, runtime_root: Path | None = None) -> Path:
    return slingshot_case_dir(case_id, runtime_root=runtime_root) / "SLINGSHOT_FRAME.v1.json"


def packet_path(case_id: str, *, runtime_root: Path | None = None) -> Path:
    return slingshot_case_dir(case_id, runtime_root=runtime_root) / "SLINGSHOT_PACKET.v1.json"


def ledger_path(case_id: str, *, runtime_root: Path | None = None) -> Path:
    return slingshot_case_dir(case_id, runtime_root=runtime_root) / "slingshot_ledger.jsonl"


def receipts_dir(case_id: str, *, runtime_root: Path | None = None) -> Path:
    return slingshot_case_dir(case_id, runtime_root=runtime_root) / "receipts"


_SLINGSHOT_JSON_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def slingshot_cache_ttl_sec() -> float:
    """Seconds to reuse slingshot frame/packet JSON loads (0 disables). Default 30."""
    raw = os.environ.get("AAIS_SLINGSHOT_CACHE_SEC", "30").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 30.0


def clear_slingshot_json_cache() -> None:
    """Clear in-process slingshot JSON cache (tests)."""
    _SLINGSHOT_JSON_CACHE.clear()


def _slingshot_cache_get(cache_key: str) -> dict[str, Any] | None:
    ttl = slingshot_cache_ttl_sec()
    if ttl <= 0:
        return None
    cached = _SLINGSHOT_JSON_CACHE.get(cache_key)
    if not cached or (time.monotonic() - cached[0]) >= ttl:
        return None
    return copy.deepcopy(cached[1])


def _slingshot_cache_put(cache_key: str, payload: dict[str, Any]) -> None:
    ttl = slingshot_cache_ttl_sec()
    if ttl <= 0:
        return
    _SLINGSHOT_JSON_CACHE[cache_key] = (time.monotonic(), copy.deepcopy(payload))


def slingshot_json_cache_key(kind: str, path: Path) -> str:
    """Build a cache key that invalidates when the on-disk artifact changes."""
    resolved = path.resolve()
    try:
        mtime_ns = resolved.stat().st_mtime_ns
    except OSError:
        mtime_ns = 0
    return f"{kind}|{resolved}|{mtime_ns}"
