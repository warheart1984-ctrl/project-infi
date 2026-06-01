"""Lab project spec — load, validate, and canonicalize lab order forms."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from lab.common import SPEC_VERSION, json_stable, sha256_text, write_json

VALID_RISK_LEVELS = ("low", "medium", "high")
BUILTIN_INSTRUMENT_KINDS = ("filesystem_read", "filesystem_write", "filesystem_list", "grep")


class ProhibitionsSpec(BaseModel):
    forbidden_commands: list[str] = Field(default_factory=lambda: ["rm -rf", "git clean -fdx", "curl", "wget"])
    network_allowed: bool = False
    high_impact_patterns: list[str] = Field(default_factory=list)
    read_only_paths: list[str] = Field(default_factory=list)


class InstrumentSpec(BaseModel):
    name: str
    kind: str | None = None
    command: list[str] = Field(default_factory=list)
    max_runtime_s: int = 60
    allowed_paths: list[str] = Field(default_factory=list)
    requires_network: bool = False
    requires_confirmation_paths: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _non_empty_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("instrument name must be non-empty")
        return cleaned

    @field_validator("max_runtime_s")
    @classmethod
    def _positive_runtime(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_runtime_s must be >= 1")
        return value


class LabProjectSpec(BaseModel):
    spec_version: str = SPEC_VERSION
    project_id: str
    intent_summary: str = ""
    source_repo: str = "."
    risk_level: Literal["low", "medium", "high"] = "low"
    prohibitions: ProhibitionsSpec = Field(default_factory=ProhibitionsSpec)
    instruments: list[InstrumentSpec] = Field(default_factory=list)
    require_session_summary: bool = False

    @field_validator("spec_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != SPEC_VERSION:
            raise ValueError(f"unsupported spec_version: {value}")
        return value

    @field_validator("project_id", "intent_summary")
    @classmethod
    def _strip_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("project_id")
    @classmethod
    def _non_empty_project(cls, value: str) -> str:
        if not value:
            raise ValueError("project_id must be non-empty")
        return value

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def content_hash(self) -> str:
        return sha256_text(json_stable(self.to_dict()))


class SpecLoadError(ValueError):
    """Raised when a lab spec fails validation."""


def _load_raw_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise SpecLoadError(
                "PyYAML is required to load YAML specs. Install pyyaml or use a .json spec."
            ) from exc
        payload = yaml.safe_load(text)
    else:
        raise SpecLoadError(f"unsupported spec format: {path.suffix}")
    if not isinstance(payload, dict):
        raise SpecLoadError("spec root must be a mapping")
    return payload


def load_lab_spec(path: str | Path) -> LabProjectSpec:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise SpecLoadError(f"spec not found: {source}")
    try:
        raw = _load_raw_mapping(source)
        return LabProjectSpec.model_validate(raw)
    except Exception as exc:
        raise SpecLoadError(str(exc)) from exc


def default_instruments() -> list[InstrumentSpec]:
    return [
        InstrumentSpec(name="read_file", kind="filesystem_read"),
        InstrumentSpec(name="write_file", kind="filesystem_write"),
        InstrumentSpec(
            name="list_dir",
            kind="filesystem_list",
        ),
        InstrumentSpec(name="grep", kind="grep"),
        InstrumentSpec(
            name="run_pytest",
            command=["python", "-m", "pytest"],
            max_runtime_s=120,
            allowed_paths=["tests/", "src/", "ai_factory/", "lab/"],
        ),
        InstrumentSpec(
            name="run_make",
            command=["make"],
            max_runtime_s=180,
            allowed_paths=["Makefile"],
        ),
    ]


def ensure_default_instruments(spec: LabProjectSpec) -> LabProjectSpec:
    if spec.instruments:
        return spec
    return spec.model_copy(update={"instruments": default_instruments()})


def write_spec_canonical(spec: LabProjectSpec, output_dir: Path) -> Path:
    target = output_dir / "LAB_PROJECT_SPEC.json"
    write_json(target, spec.to_dict())
    return target
