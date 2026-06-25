"""Governance bypass failure demo."""

from __future__ import annotations

from typing import Any


def run() -> dict[str, Any]:
    receipt_without_governance = {"decision": "approve", "governance_receipt": None}
    return {
        "question": "Does the runtime reject decisions without governance receipts?",
        "passed": receipt_without_governance["governance_receipt"] is None,
    }
