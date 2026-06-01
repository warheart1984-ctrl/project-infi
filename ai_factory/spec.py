"""AI Build Spec — load, validate, and canonicalize factory order forms."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from ai_factory.common import json_stable, sha256_text, write_json

SPEC_VERSION = "ai_factory.ai_build_spec.v1"
DEFAULT_ENABLED_LOBES: tuple[str, ...] = (
    "jarvis.reasoning",
    "cognitive.attention",
    "cognitive.memory",
    "cognitive.deliberation",
    "cognitive.reflection",
    "cognitive.planning",
    "cognitive.execution",
    "speaking.runtime",
)
VALID_COMPOSE_MODES = ("instant", "fast", "full")
VALID_RISK_LEVELS = ("low", "medium", "high")
VALID_DATA_SENSITIVITY = ("public", "operator", "restricted")


class CapabilitiesSpec(BaseModel):
    enabled_lobes: list[str] = Field(default_factory=lambda: list(DEFAULT_ENABLED_LOBES))
    compose_mode: Literal["instant", "fast", "full"] = "full"

    @field_validator("enabled_lobes")
    @classmethod
    def _non_empty_lobes(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("enabled_lobes must contain at least one lobe id")
        return sorted(set(cleaned))


class ProhibitionsSpec(BaseModel):
    forbidden_tools: list[str] = Field(default_factory=list)
    high_impact_actions_blocked: bool = True


class OversightSpec(BaseModel):
    require_speaking: bool = True
    require_agency_check: bool = True
    require_generation_gate: bool = True


class InterfacesSpec(BaseModel):
    face_id: str = "nova"
    speaking_mode: str = "governed"


class AIBuildSpec(BaseModel):
    spec_version: str = SPEC_VERSION
    build_id: str
    intent_summary: str
    risk_level: Literal["low", "medium", "high"] = "low"
    capabilities: CapabilitiesSpec = Field(default_factory=CapabilitiesSpec)
    prohibitions: ProhibitionsSpec = Field(default_factory=ProhibitionsSpec)
    oversight: OversightSpec = Field(default_factory=OversightSpec)
    data_sensitivity: Literal["public", "operator", "restricted"] = "operator"
    interfaces: InterfacesSpec = Field(default_factory=InterfacesSpec)
    tools_allowed: list[str] = Field(default_factory=list)

    @field_validator("spec_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != SPEC_VERSION:
            raise ValueError(f"unsupported spec_version: {value}")
        return value

    @field_validator("build_id", "intent_summary")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def content_hash(self) -> str:
        return sha256_text(json_stable(self.to_dict()))


class SpecStationError(ValueError):
    """Raised when a build spec fails validation."""


def _load_raw_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise SpecStationError(
                "PyYAML is required to load YAML specs. Install pyyaml or use a .json spec."
            ) from exc
        payload = yaml.safe_load(text)
    else:
        raise SpecStationError(f"unsupported spec format: {path.suffix}")
    if not isinstance(payload, dict):
        raise SpecStationError("spec root must be a mapping")
    return payload


def load_build_spec(path: str | Path) -> AIBuildSpec:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise SpecStationError(f"spec not found: {source}")
    try:
        return AIBuildSpec.model_validate(_load_raw_mapping(source))
    except Exception as exc:
        raise SpecStationError(str(exc)) from exc


def run_spec_station(
    *,
    spec_path: str | Path,
    output_dir: Path,
) -> tuple[AIBuildSpec, dict[str, Any]]:
    """Validate spec and write canonical AI_BUILD_SPEC.json."""

    spec = load_build_spec(spec_path)
    target = output_dir / "AI_BUILD_SPEC.json"
    write_json(target, spec.to_dict())
    receipt = {
        "station": "spec",
        "station_version": "ai_factory.spec_station.v1",
        "status": "ok",
        "build_id": spec.build_id,
        "source_spec": str(Path(spec_path).resolve()),
        "output": str(target.resolve()),
        "content_hash": spec.content_hash(),
        "trace": [
            "load_spec",
            "validate_pydantic",
            "write_canonical_json",
        ],
    }
    return spec, receipt
