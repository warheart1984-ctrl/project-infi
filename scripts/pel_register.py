#!/usr/bin/env python3
"""Register a runtime audit record as a canonical PELRecord."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.cori.pel.pel_register import register_pel_record  # noqa: E402
from src.cori.pel.storage import PelStorage  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("Usage: pel_register.py <audit_id>", file=sys.stderr)
        return 1

    audit_id = args[0]
    storage = PelStorage()
    pel = register_pel_record(audit_id, storage)
    print(json.dumps(pel.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
