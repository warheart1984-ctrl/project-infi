"""Graph index sync — load claims from canonical JSONL paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def discover_claim_paths(runtime_root: Path) -> list[Path]:
    """Find all canonical claim JSONL files under the runtime ledger tree."""
    base = Path(runtime_root) / "collective-pattern-ledger"
    if not base.exists():
        return []
    paths = sorted({path for path in base.glob("**/claims.jsonl") if path.is_file()})
    unified = base / "unified" / "claims.jsonl"
    if unified.exists() and unified not in paths:
        paths.append(unified)
    return paths


def _read_claim_file(path: Path, *, max_rows: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if str(payload.get("record_type") or "") == "claim":
                rows.append(payload)
    if max_rows is not None and max_rows > 0:
        return rows[-max_rows:]
    return rows


def load_claims_from_paths(
    paths: list[Path],
    *,
    max_rows_per_path: int | None = None,
) -> list[dict[str, Any]]:
    """Load claim records from one or more JSONL paths with stable dedupe order."""
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        for row in _read_claim_file(path, max_rows=max_rows_per_path):
            claim_id = str(row.get("claim_id") or "")
            key = claim_id or str(row.get("timestamp") or "")
            if key in seen:
                continue
            seen.add(key)
            merged.append(row)
    return merged
