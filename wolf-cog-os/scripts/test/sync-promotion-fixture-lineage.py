#!/usr/bin/env python3
"""Sync promotion fixture forge-build-state lineage_id from forge-lineage.json."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "test" / "fixtures" / "promotion-forge-rc"


def main() -> int:
    lineage = json.loads((FIXTURE / "forge-lineage.json").read_text(encoding="utf-8"))
    state_path = FIXTURE / "forge-build-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["lineage_id"] = lineage["lineage_id"]
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"synced lineage_id to {state_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
