"""CRK-1 Governance Receipt Verifier — hard gate on constitutional actions."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from src.crk1.errors import ConstitutionalError
from src.crk1.schemas import GOVERNANCE_RECEIPT_SCHEMA

_DRIFT_EPSILON = 1e-9


class GovernanceReceiptVerifier:
    """Validate governance receipt headers against schema and constitutional rules."""

    def __init__(self, schema: dict[str, Any] | None = None) -> None:
        self.schema = schema or GOVERNANCE_RECEIPT_SCHEMA
        self.validator = Draft202012Validator(self.schema)

    def verify_schema(self, receipt: dict[str, Any]) -> None:
        try:
            self.validator.validate(receipt)
        except ValidationError as exc:
            raise ConstitutionalError(f"Receipt schema invalid: {exc.message}") from exc

    def verify_invariants(self, receipt: dict[str, Any]) -> None:
        invariants = receipt["invariants_checked"]
        if invariants["K0_K2"] != "PASS":
            raise ConstitutionalError("K0–K2 invariant check failed")
        if invariants["K3_K6"] != "PASS":
            raise ConstitutionalError("K3–K6 invariant check failed")
        if invariants["K7_K12"] != "PASS":
            raise ConstitutionalError("K7–K12 invariant check failed")
        if invariants.get("K13_K15") == "FAIL":
            raise ConstitutionalError("K13–K15 invariant check failed")
        if invariants.get("KΩ") == "FAIL":
            raise ConstitutionalError("KΩ invariant check failed")

    def verify_drift(self, receipt: dict[str, Any]) -> None:
        metrics = receipt["drift_metrics"]
        if metrics["CE_after"] + _DRIFT_EPSILON < metrics["CE_before"]:
            raise ConstitutionalError("CE(S) drift envelope violated")
        if metrics["SE_after"] + _DRIFT_EPSILON < metrics["SE_before"]:
            raise ConstitutionalError("SE(S) drift envelope violated")
        if metrics["SE_before"] <= 0 or metrics["SE_after"] <= 0:
            raise ConstitutionalError("SE(S) must remain > 0 (K12)")

    def verify_redteam(self, receipt: dict[str, Any], *, required: bool = True) -> None:
        if not required:
            return
        redteam = receipt["redteam_status"]
        if redteam["all_blocked"] != "YES":
            raise ConstitutionalError("Red-team attacks not fully blocked")

    def verify(
        self,
        receipt: dict[str, Any],
        *,
        require_redteam: bool = True,
    ) -> bool:
        self.verify_schema(receipt)
        self.verify_invariants(receipt)
        self.verify_drift(receipt)
        self.verify_redteam(receipt, required=require_redteam)
        return True
