"""Shared paths and helpers for triangulation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

DEFAULT_MECHANIC_ROOT = Path(".runtime/mechanic")
DEFAULT_SCORPION_ROOT = Path(".runtime/scorpion")
DEFAULT_SLINGSHOT_ROOT = Path(".runtime/slingshot")
DEFAULT_TRIANGULATION_ROOT = Path(".runtime/triangulation")
PACKAGE_ROOT = Path(__file__).resolve().parent
FIXTURE_ROOT = PACKAGE_ROOT / "fixtures"
BRIDGE_MAP_PATH = PACKAGE_ROOT / "bridge_map.json"
SCHEMA_PATH = PACKAGE_ROOT / "schemas" / "triangulation.v1.json"


def triangulation_case_dir(case_id: str, *, runtime_root: Path | None = None) -> Path:
    root = (runtime_root or DEFAULT_TRIANGULATION_ROOT).expanduser().resolve()
    return root / case_id


def triangulation_artifact_path(case_id: str, *, runtime_root: Path | None = None) -> Path:
    return triangulation_case_dir(case_id, runtime_root=runtime_root) / "triangulation.v1.json"


def correlation_ledger_path(case_id: str, *, runtime_root: Path | None = None) -> Path:
    return triangulation_case_dir(case_id, runtime_root=runtime_root) / "correlation_ledger.jsonl"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_ref(path: Path, *, present: bool = True) -> dict[str, object]:
    if not path.is_file():
        return {"artifact_path": str(path), "content_hash": "", "present": False}
    return {
        "artifact_path": str(path),
        "content_hash": sha256_file(path),
        "present": present,
    }


def json_stable(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
