#!/usr/bin/env python3
"""Register a world event as a WorldMemoryRecord."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.cori.world.models import WorldEventRecord  # noqa: E402
from src.cori.world.register import register_world_event  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: world_register.py <event.json>", file=sys.stderr)
        return 1
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if "timestamp" in payload and isinstance(payload["timestamp"], str):
        ts = payload["timestamp"]
        normalized = ts[:-1] + "+00:00" if ts.endswith("Z") else ts
        payload["timestamp"] = datetime.fromisoformat(normalized)
        if payload["timestamp"].tzinfo is None:
            payload["timestamp"] = payload["timestamp"].replace(tzinfo=UTC)
    event = WorldEventRecord.model_validate(payload)
    memory = register_world_event(event)
    print(json.dumps(memory.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
