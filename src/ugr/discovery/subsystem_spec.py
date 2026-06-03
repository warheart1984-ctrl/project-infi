"""Subsystem spec space — normalization and canonical hash identity."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any


RAIL_CLASSES = frozenset({"SAFE", "NORMAL", "EXPRESS"})
RISK_CEILINGS = frozenset({"low", "medium", "high"})
TENANT_CLASSES = frozenset({"global", "standard", "restricted"})

ROLE_CAPABILITY_ALIASES: dict[str, str] = {
    "llm_executor": "general_qa",
    "llm_provider": "general_qa",
    "router": "governed_super_router_demo",
    "explainer": "explain",
    "ingest_worker": "general_qa",
}


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _normalize_rail(value: Any) -> str:
    rail = str(value or "NORMAL").strip().upper()
    return rail if rail in RAIL_CLASSES else "NORMAL"


def _normalize_risk(value: Any) -> str:
    risk = str(value or "medium").strip().lower()
    return risk if risk in RISK_CEILINGS else "medium"


def _normalize_tenant_class(value: Any) -> str:
    tc = str(value or "standard").strip().lower()
    return tc if tc in TENANT_CLASSES else "standard"


def _normalize_io_shape(value: Any) -> dict[str, list[str]]:
    raw = dict(value or {}) if isinstance(value, dict) else {}
    inputs = [str(item).strip() for item in (raw.get("inputs") or []) if str(item).strip()]
    outputs = [str(item).strip() for item in (raw.get("outputs") or []) if str(item).strip()]
    return {"inputs": inputs, "outputs": outputs}


def role_to_capability(role: str) -> str:
    key = str(role or "").strip().lower().replace("-", "_")
    return ROLE_CAPABILITY_ALIASES.get(key, key)


@dataclass(frozen=True)
class SubsystemSpec:
    role: str
    io_shape: dict[str, list[str]]
    rail_class: str
    risk_ceiling: str
    tenant_class: str

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SubsystemSpec:
        raw = dict(data or {})
        return cls(
            role=str(raw.get("role") or "").strip().lower().replace("-", "_"),
            io_shape=_normalize_io_shape(raw.get("io_shape")),
            rail_class=_normalize_rail(raw.get("rail_class")),
            risk_ceiling=_normalize_risk(raw.get("risk_ceiling")),
            tenant_class=_normalize_tenant_class(raw.get("tenant_class")),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "io_shape": {
                "inputs": list(self.io_shape.get("inputs") or []),
                "outputs": list(self.io_shape.get("outputs") or []),
            },
            "rail_class": self.rail_class,
            "risk_ceiling": self.risk_ceiling,
            "tenant_class": self.tenant_class,
        }

    def is_complete(self) -> bool:
        return bool(self.role) and bool(self.io_shape.get("inputs") or self.io_shape.get("outputs"))

    def merge_partial(self, other: SubsystemSpec | dict[str, Any] | None) -> SubsystemSpec:
        if other is None:
            return self
        base = self.canonical_dict()
        patch = SubsystemSpec.from_dict(other).canonical_dict() if isinstance(other, dict) else other.canonical_dict()
        merged: dict[str, Any] = {}
        for key in ("role", "rail_class", "risk_ceiling", "tenant_class"):
            merged[key] = patch.get(key) or base.get(key)
        io_base = dict(base.get("io_shape") or {})
        io_patch = dict(patch.get("io_shape") or {})
        merged["io_shape"] = {
            "inputs": io_patch.get("inputs") or io_base.get("inputs") or [],
            "outputs": io_patch.get("outputs") or io_base.get("outputs") or [],
        }
        return SubsystemSpec.from_dict(merged)


def subsystem_id_from_spec(spec: SubsystemSpec | dict[str, Any]) -> str:
    normalized = spec.canonical_dict() if isinstance(spec, SubsystemSpec) else SubsystemSpec.from_dict(spec).canonical_dict()
    return sha256(stable_json(normalized).encode("utf-8")).hexdigest()


def validate_spec_shape(spec: SubsystemSpec) -> list[str]:
    errors: list[str] = []
    if not spec.role:
        errors.append("role is required")
    if not spec.io_shape.get("inputs") and not spec.io_shape.get("outputs"):
        errors.append("io_shape requires at least one input or output")
    if spec.rail_class not in RAIL_CLASSES:
        errors.append(f"invalid rail_class: {spec.rail_class}")
    if spec.risk_ceiling not in RISK_CEILINGS:
        errors.append(f"invalid risk_ceiling: {spec.risk_ceiling}")
    if spec.tenant_class not in TENANT_CLASSES:
        errors.append(f"invalid tenant_class: {spec.tenant_class}")
    return errors
