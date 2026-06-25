#!/usr/bin/env python3
"""RP-1.0 — reproduce Bone King continuity package from BK-PKG-1.json (stdlib only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_BUNDLE = Path(__file__).resolve().parent
_KIT = _BUNDLE / "observer-kit"
if str(_KIT) not in sys.path:
    sys.path.insert(0, str(_KIT))

from verify import reproduce_package  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python bone_king_reproduce.py BK-PKG-1.json", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    package = json.loads(path.read_text(encoding="utf-8"))
    result = reproduce_package(package)

    print(f"protocol: {result['protocol']}")
    print(f"observer: {result['observer']}")
    print(f"package_id: {result['package_id']}")
    print(f"result: {result['result']}")
    details = result["details"]
    print(f"canonical_hash_match: {details['canonical_hash_match']}")
    print(f"event_hash_match: {details['event_hash_match']}")
    print(f"replay_state_match: {details['replay_state_match']}")
    print(f"recomputed_hash: {details['recomputed_hash']}")

    return 0 if result["result"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
