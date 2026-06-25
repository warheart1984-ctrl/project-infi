#!/usr/bin/env python3
"""Verify BK-PKG-1 canonical hash and invariants (stdlib only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_BUNDLE = Path(__file__).resolve().parent
_KIT = _BUNDLE / "observer-kit"
if str(_KIT) not in sys.path:
    sys.path.insert(0, str(_KIT))

from verify import verify_package  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python continuity_verify.py BK-PKG-1.json", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    package = json.loads(path.read_text(encoding="utf-8"))
    result = verify_package(package)

    print(f"status: {result['status']}")
    print(f"canonical_hash: {result['canonical_hash']}")

    if result["status"] != "verified":
        print(f"recomputed_hash: {result['recomputed_hash']}", file=sys.stderr)
        print(f"canonical_hash_match: {result['canonical_hash_match']}", file=sys.stderr)
        print(f"event_hash_match: {result['event_hash_match']}", file=sys.stderr)
        print(f"replay_state_match: {result['replay_state_match']}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
