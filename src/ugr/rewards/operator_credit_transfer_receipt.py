"""Signed operator rail credit transfer receipt v1."""

from __future__ import annotations

import time
from typing import Any

from src.ugr.mission.receipt_signing import load_urg_receipt_signing_key, sign_urg_receipt


TRANSFER_RECEIPT_SCHEMA_VERSION = "1.0"


def build_credit_transfer_receipt(
    *,
    transfer_id: str,
    tenant_id: str,
    from_operator_id: str,
    to_operator_id: str,
    amount: float,
    fee: float,
    trace_id: str,
    memo: str | None = None,
    exchange_id: str | None = None,
    issued_at: float | None = None,
    runtime_dir: str | None = None,
    create_key_if_missing: bool = True,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "receipt_schema_version": TRANSFER_RECEIPT_SCHEMA_VERSION,
        "transfer_id": transfer_id,
        "tenant_id": tenant_id,
        "from_operator_id": from_operator_id,
        "to_operator_id": to_operator_id,
        "amount": amount,
        "fee": fee,
        "trace_id": trace_id,
        "memo": memo,
        "exchange_id": exchange_id,
        "issued_at": issued_at if issued_at is not None else time.time(),
    }
    _, urg_key_id = load_urg_receipt_signing_key(
        runtime_dir=runtime_dir,
        create_if_missing=create_key_if_missing,
    )
    if urg_key_id:
        receipt["urg_key_id"] = urg_key_id
    receipt_sig, algorithm, _ = sign_urg_receipt(
        receipt,
        runtime_dir=runtime_dir,
        create_key_if_missing=create_key_if_missing,
    )
    receipt["receipt_sig"] = receipt_sig
    receipt["receipt_algorithm"] = algorithm
    return receipt


def verify_credit_transfer_receipt(
    receipt: dict[str, Any],
    *,
    runtime_dir: str | None = None,
) -> tuple[bool, str]:
    from hashlib import sha256
    import hmac

    from src.ugr.mission.receipt_signing import (
        ALGORITHM_CONTENT_ONLY,
        ALGORITHM_HMAC,
        build_urg_receipt_canonical,
        load_urg_receipt_signing_key,
    )

    from src.ugr.rewards.reward_attribution import stable_json

    if not receipt:
        return False, "empty receipt"
    sig = str(receipt.get("receipt_sig") or "")
    if not sig:
        return False, "missing receipt_sig"
    canonical = stable_json(build_urg_receipt_canonical(receipt))
    algorithm = str(receipt.get("receipt_algorithm") or ALGORITHM_CONTENT_ONLY)
    key, _ = load_urg_receipt_signing_key(runtime_dir=runtime_dir, create_if_missing=False)
    if algorithm == ALGORITHM_HMAC and key:
        expected = hmac.new(key.encode("utf-8"), canonical.encode("utf-8"), sha256).hexdigest()
        if hmac.compare_digest(expected, sig):
            return True, "ok"
        return False, "receipt_sig mismatch"
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if hmac.compare_digest(expected, sig):
        return True, "ok"
    return False, "receipt_sig mismatch"
