"""Rail credit purchase receipt — ledger-only off-platform payment anchor."""

from __future__ import annotations

import hmac
import time
from hashlib import sha256
from typing import Any
from uuid import uuid4

from src.ugr.rewards.reward_attribution import stable_json
from src.ugr.mission.receipt_signing import load_urg_receipt_signing_key


PURCHASE_RECEIPT_SCHEMA_VERSION = "1.0"
ALGORITHM_HMAC = "hmac-sha256"
ALGORITHM_CONTENT_ONLY = "content-sha256"


def build_purchase_receipt_canonical(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_schema_version": receipt.get("receipt_schema_version"),
        "purchase_id": receipt.get("purchase_id"),
        "tenant_id": receipt.get("tenant_id"),
        "operator_id": receipt.get("operator_id"),
        "amount": receipt.get("amount"),
        "currency": receipt.get("currency"),
        "payment_reference": receipt.get("payment_reference"),
        "issued_at": receipt.get("issued_at"),
    }


def build_purchase_receipt(
    *,
    tenant_id: str,
    operator_id: str,
    amount: float,
    payment_reference: str,
    currency: str = "USD",
    runtime_dir: str | None = None,
    create_key_if_missing: bool = True,
) -> dict[str, Any]:
    purchase_id = str(uuid4())
    receipt: dict[str, Any] = {
        "receipt_schema_version": PURCHASE_RECEIPT_SCHEMA_VERSION,
        "purchase_id": purchase_id,
        "tenant_id": tenant_id,
        "operator_id": operator_id,
        "amount": float(amount),
        "currency": currency,
        "payment_reference": str(payment_reference or "").strip(),
        "issued_at": time.time(),
    }
    _, urg_key_id = load_urg_receipt_signing_key(
        runtime_dir=runtime_dir,
        create_if_missing=create_key_if_missing,
    )
    if urg_key_id:
        receipt["urg_key_id"] = urg_key_id
    receipt_sig, algorithm = _sign_purchase_body(receipt, runtime_dir=runtime_dir, create_key=create_key_if_missing)
    receipt["receipt_sig"] = receipt_sig
    receipt["receipt_algorithm"] = algorithm
    receipt["purchase_digest"] = sha256(
        stable_json(build_purchase_receipt_canonical(receipt)).encode("utf-8")
    ).hexdigest()
    return receipt


def _sign_purchase_body(
    receipt: dict[str, Any],
    *,
    runtime_dir: str | None,
    create_key: bool,
) -> tuple[str, str]:
    canonical = stable_json(build_purchase_receipt_canonical(receipt))
    key, _ = load_urg_receipt_signing_key(runtime_dir=runtime_dir, create_if_missing=create_key)
    if key:
        mac = hmac.new(key.encode("utf-8"), canonical.encode("utf-8"), sha256).hexdigest()
        return mac, ALGORITHM_HMAC
    digest = sha256(canonical.encode("utf-8")).hexdigest()
    return digest, ALGORITHM_CONTENT_ONLY


def verify_purchase_receipt(
    receipt: dict[str, Any],
    *,
    runtime_dir: str | None = None,
) -> tuple[bool, str]:
    canonical = stable_json(build_purchase_receipt_canonical(receipt))
    sig = str(receipt.get("receipt_sig") or "")
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
