"""JSON Schema validation for CRK-1 v0.1 wire objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from src.crk1.schema_validator import SchemaValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
V01_SCHEMA_DIR = REPO_ROOT / "fixtures" / "crk1" / "v01"
V01_SCHEMA_BASE = "https://crk1.local/schemas/v01/"

_V01_SCHEMA_FILES: dict[str, str] = {
    "CRK1IdentityV01": "identity.v01.schema.json",
    "CRK1DecisionV01": "decision.v01.schema.json",
    "CRK1OutcomeV01": "outcome.v01.schema.json",
    "CRK1EvidenceV01": "evidence.v01.schema.json",
    "CRK1InterpretationV01": "interpretation.v01.schema.json",
    "CRK1ReceiptV01": "receipt.v01.schema.json",
}

_TYPE_TO_SCHEMA: dict[str, str] = {
    "Identity": "CRK1IdentityV01",
    "Decision": "CRK1DecisionV01",
    "Outcome": "CRK1OutcomeV01",
    "Evidence": "CRK1EvidenceV01",
    "Interpretation": "CRK1InterpretationV01",
    "Receipt": "CRK1ReceiptV01",
}


def _build_v01_registry(schema_dir: Path) -> Registry:
    """Register all v0.1 schemas so relative $ref paths resolve."""
    registry = Registry()
    for path in sorted(schema_dir.glob("*.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(schema, default_specification=DRAFT202012)
        registry = registry.with_resource(path.resolve().as_uri(), resource)
        registry = registry.with_resource(V01_SCHEMA_BASE + path.name, resource)
        schema_id = schema.get("$id")
        if schema_id:
            registry = registry.with_resource(schema_id, resource)
    return registry


class CRK1WireV01Validator:
    """Validates Continuity API v0.1 wire objects."""

    def __init__(self, schema_dir: Path | None = None) -> None:
        base = schema_dir or V01_SCHEMA_DIR
        registry = _build_v01_registry(base)
        self._validators: dict[str, Draft202012Validator] = {}
        for name, filename in _V01_SCHEMA_FILES.items():
            path = base / filename
            schema = json.loads(path.read_text(encoding="utf-8"))
            self._validators[name] = Draft202012Validator(schema, registry=registry)

    def schema_name_for(self, payload: dict[str, Any]) -> str:
        object_type = payload.get("type")
        schema = _TYPE_TO_SCHEMA.get(str(object_type))
        if schema is None:
            raise SchemaValidationError(f"Unknown CRK-1 wire type: {object_type}")
        return schema

    def validate(self, payload: dict[str, Any]) -> str:
        schema_name = self.schema_name_for(payload)
        validator = self._validators[schema_name]
        errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
        if errors:
            first = errors[0]
            path = ".".join(str(part) for part in first.path) or "(root)"
            raise SchemaValidationError(
                f"{schema_name} validation failed at {path}: {first.message}"
            )
        return schema_name

    def validate_all(self, objects: list[dict[str, Any]]) -> list[str]:
        return [self.validate(item) for item in objects]
