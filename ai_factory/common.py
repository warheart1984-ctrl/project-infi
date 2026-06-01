"""Shared AI Factory utilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

ClaimLabel = Literal["asserted", "proven", "rejected"]

DEFAULT_RUNTIME_ROOT = Path(".runtime/ai_factory")
DEFAULT_LEDGER_PATH = DEFAULT_RUNTIME_ROOT / "factory_ledger.jsonl"
DEFAULT_ACTIVE_POINTER = DEFAULT_RUNTIME_ROOT / "active" / "build_id.txt"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def json_stable(payload: Any, *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False)
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_stable(payload, pretty=True) + "\n", encoding="utf-8")


def derive_claim_status(labels: list[ClaimLabel]) -> ClaimLabel:
    if not labels:
        return "asserted"
    if "rejected" in labels:
        return "rejected"
    if all(item == "proven" for item in labels):
        return "proven"
    return "asserted"


def hash_manifest_entry(*, artifact: str, path: Path, claim_label: ClaimLabel) -> dict[str, Any]:
    exists = path.is_file()
    return {
        "artifact": artifact,
        "path": str(path.resolve()),
        "exists": exists,
        "claim_label": claim_label,
        "sha256": sha256_file(path) if exists else "",
    }
