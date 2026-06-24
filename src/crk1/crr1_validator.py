"""CRR-1 validation — wire schema and optional legacy digest check."""

from __future__ import annotations

from typing import Any

from src.crk1.correction_object import CalibrationCorrectionReceipt, _sha256_payload
from src.crk1.schema_validator import CRK1SchemaValidator


def validate_crr1(
    crr1: dict[str, Any] | CalibrationCorrectionReceipt,
    *,
    schema_validator: CRK1SchemaValidator | None = None,
) -> bool:
    """
    Validate a CRR-1 receipt.

    Accepts flat wire dict (calibration_reconstruction_receipt schema) or
  legacy CalibrationCorrectionReceipt with reconstruction digest.
    """
    validator = schema_validator or CRK1SchemaValidator()

    if isinstance(crr1, CalibrationCorrectionReceipt):
        payload = crr1.to_dict()
        digest = crr1.reconstruction_digest
        correction_payload = crr1.correction.to_dict()
        try:
            validator.validate("CalibrationCorrectionReceipt", payload)
        except Exception:
            return False
        if not digest:
            return False
        return digest == _sha256_payload(correction_payload)

    payload = dict(crr1)
    if payload.get("receipt_type") == "CRR-1" or payload.get("schema_version"):
        try:
            validator.validate("calibration_reconstruction_receipt", payload)
            return True
        except Exception:
            return False

    if payload.get("type") == "CalibrationCorrectionReceipt" and "correction" in payload:
        try:
            validator.validate("CalibrationCorrectionReceipt", payload)
        except Exception:
            return False
        digest = payload.get("reconstruction_digest", "")
        if not digest:
            return False
        return digest == _sha256_payload(payload["correction"])

    return False
