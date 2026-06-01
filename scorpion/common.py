"""Shared Scorpion utilities (no circular imports)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

ClaimLabel = Literal["asserted", "proven", "rejected"]


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


def derive_claim_status(labels: list[ClaimLabel]) -> ClaimLabel:
    if not labels:
        return "asserted"
    if "rejected" in labels:
        return "rejected"
    if all(item == "proven" for item in labels):
        return "proven"
    if "proven" in labels:
        return "asserted"
    return "asserted"
