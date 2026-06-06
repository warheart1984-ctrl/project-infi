"""Contribution spec space — unified Proof-of-Discovery types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


class ContributionType(str, Enum):
    SUBSYSTEM = "subsystem"
    WORKFLOW = "workflow"
    ORGAN = "organ"
    PROOF = "proof"
    INVARIANT = "invariant"
    CAPABILITY = "capability"
    SUBSTRATE = "substrate"


CONTRIBUTION_TYPES = frozenset(t.value for t in ContributionType)


@dataclass(frozen=True)
class ContributionSpec:
    contribution_type: str
    payload: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ContributionSpec:
        raw = dict(data or {})
        ctype = str(raw.get("contribution_type") or raw.get("type") or "").strip().lower()
        if ctype not in CONTRIBUTION_TYPES:
            ctype = ContributionType.SUBSYSTEM.value
        payload = dict(raw.get("payload") or raw.get("spec") or raw)
        if "contribution_type" in payload:
            payload = {k: v for k, v in payload.items() if k not in {"contribution_type", "type"}}
        return cls(contribution_type=ctype, payload=payload)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "contribution_type": self.contribution_type,
            "payload": self.payload,
        }

    def contribution_id(self) -> str:
        return contribution_id_from_spec(self)


def contribution_id_from_spec(spec: ContributionSpec | dict[str, Any]) -> str:
    if isinstance(spec, dict):
        spec = ContributionSpec.from_dict(spec)
    canonical = spec.canonical_dict()
    return sha256(stable_json(canonical).encode("utf-8")).hexdigest()


def validate_contribution_shape(spec: ContributionSpec) -> list[str]:
    errors: list[str] = []
    if spec.contribution_type not in CONTRIBUTION_TYPES:
        errors.append(f"invalid contribution_type: {spec.contribution_type}")
    if not spec.payload:
        errors.append("payload is required")
    return errors
