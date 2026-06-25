"""Receipt v2 stream access for constitutional state aggregation (ledger-only inputs)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from constitutional.runtime.receipts_v2 import (
    AmendmentReceiptV2,
    ArbitrationReceiptV2,
    BaseReceiptV2,
    ClosureReceiptV2,
    DivergenceReceiptV2,
    RemediationReceiptV2,
    TransitionReceiptV2,
)

ALL_RECEIPTS_PATH = Path(".runtime/receipts/all_receipts.jsonl")

_RECEIPT_TYPES: tuple[type[BaseReceiptV2], ...] = (
    TransitionReceiptV2,
    DivergenceReceiptV2,
    RemediationReceiptV2,
    ClosureReceiptV2,
    ArbitrationReceiptV2,
    AmendmentReceiptV2,
)


def _parse_timestamp(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=UTC)


def _parse_receipt_line(payload: dict[str, Any]) -> BaseReceiptV2 | None:
    action_type = payload.get("action_type", "")
    if action_type == "state_transition":
        return TransitionReceiptV2.model_validate(payload)
    if action_type == "constitutional_amendment":
        return AmendmentReceiptV2.model_validate(payload)
    if action_type == "constitutional_risk_forecast" or "constitutional_risk" in payload:
        from constitutional.runtime.receipts_v2 import RiskReceiptV2

        return RiskReceiptV2.model_validate(payload)
    if "divergence" in payload:
        return DivergenceReceiptV2.model_validate(payload)
    if "remediation" in payload:
        return RemediationReceiptV2.model_validate(payload)
    if "closure" in payload:
        return ClosureReceiptV2.model_validate(payload)
    if "conflict" in payload and "resolution" in payload:
        return ArbitrationReceiptV2.model_validate(payload)
    for model in _RECEIPT_TYPES:
        try:
            return model.model_validate(payload)
        except Exception:
            continue
    return None


def load_receipts_from_disk(
    *,
    path: Path | None = None,
    up_to: datetime | None = None,
) -> list[BaseReceiptV2]:
    """Load cumulative receipt stream R = { receipts with timestamp ≤ up_to }."""
    target = path or ALL_RECEIPTS_PATH
    if not target.is_file():
        return []

    cutoff = up_to
    receipts: list[BaseReceiptV2] = []
    with target.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            receipt = _parse_receipt_line(payload)
            if receipt is None:
                continue
            if cutoff is not None and _parse_timestamp(receipt.timestamp) > cutoff:
                continue
            receipts.append(receipt)
    return receipts


def max_receipt_timestamp(receipts: list[BaseReceiptV2]) -> datetime | None:
    if not receipts:
        return None
    return max(_parse_timestamp(r.timestamp) for r in receipts)
