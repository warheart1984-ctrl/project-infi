from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

AUDIT_PATH = Path("nova-audit.log")


def audit_event(event: dict[str, Any]) -> None:
    entry = {"timestamp": int(time.time()), **event}
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, ensure_ascii=True) + "\n")
