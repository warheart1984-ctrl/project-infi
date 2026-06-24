"""CRK-1 JSON Schema registry — governance receipt and object wire formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "fixtures" / "crk1"
GOVERNANCE_RECEIPT_SCHEMA_PATH = SCHEMA_DIR / "governance_receipt_header.schema.json"


def load_governance_receipt_schema() -> dict[str, Any]:
    return json.loads(GOVERNANCE_RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))


GOVERNANCE_RECEIPT_SCHEMA: dict[str, Any] = load_governance_receipt_schema()
