"""CRK-1 K0–K3 JSON Schema validation for consequence transmission objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "fixtures" / "crk1"

_SCHEMA_FILES = {
    "OutcomeObject": "outcome_object.schema.json",
    "EvidenceObject": "evidence_object.schema.json",
    "DecisionObject": "decision_object.schema.json",
    "IdentityObject": "identity_object.schema.json",
    "InterpretationObject": "interpretation_object.schema.json",
    "PredictionObject": "prediction_object.schema.json",
    "ReconstructionObject": "reconstruction_object.schema.json",
    "GovernanceReceiptHeader": "governance_receipt_header.schema.json",
    "JudgmentTrace": "judgment_trace.schema.json",
    "TransmissionMonitorRecord": "transmission_monitor_record.schema.json",
    "GovernanceReconstructionReceipt": "governance_reconstruction_receipt.schema.json",
    "ReconstructionTrace": "reconstruction_trace.schema.json",
    "KernelChallengeReceipt": "kernel_challenge_receipt.schema.json",
    "DriftObservation": "drift_observation.schema.json",
    "InvariantProposal": "invariant_proposal.schema.json",
    "InvariantTestSuite": "invariant_test_suite.schema.json",
    "ReproductionSeal": "reproduction_seal.schema.json",
    "ReproductionPacket": "reproduction_packet.schema.json",
    "CorrectionObject": "correction_object.schema.json",
    "CalibrationCorrectionReceipt": "calibration_correction_receipt.schema.json",
    "CalibrationReconstructionReceipt": "calibration_reconstruction_receipt.schema.json",
    "calibration_reconstruction_receipt": "crr1_wire_v1.schema.json",
    "CRR1WireV1": "crr1_wire_v1.schema.json",
    "GovernanceReceiptHeaderV12": "governance_receipt_header.v12.schema.json",
}


class SchemaValidationError(ValueError):
    """Raised when a payload violates a CRK-1 K0–K3 object schema."""


class CRK1SchemaValidator:
    """Validates wire-level CRK-1 objects against constitutional JSON schemas."""

    def __init__(self, schema_dir: Path | None = None) -> None:
        base = schema_dir or SCHEMA_DIR
        self._validators: dict[str, Draft202012Validator] = {}
        for name, filename in _SCHEMA_FILES.items():
            path = base / filename
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            self._validators[name] = Draft202012Validator(schema)

    def validate(self, schema_name: str, payload: dict[str, Any]) -> None:
        validator = self._validators.get(schema_name)
        if validator is None:
            raise KeyError(f"Unknown CRK-1 schema: {schema_name}")
        errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
        if errors:
            first = errors[0]
            path = ".".join(str(part) for part in first.path) or "(root)"
            raise SchemaValidationError(
                f"{schema_name} validation failed at {path}: {first.message}"
            )

    @classmethod
    def validate_schema(cls, schema_name: str, payload: dict[str, Any]) -> None:
        """Class-level convenience wrapper for schema validation."""
        cls().validate(schema_name, payload)
