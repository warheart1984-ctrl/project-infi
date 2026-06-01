"""Lab capability profile — resolved instrument registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_factory.common import sha256_text

from lab.common import CAPABILITY_FILENAME, CAPABILITY_VERSION, json_stable, write_json
from lab.spec import LabProjectSpec


def build_capability_profile(spec: LabProjectSpec) -> dict[str, Any]:
    instruments: list[dict[str, Any]] = []
    for item in spec.instruments:
        payload = item.model_dump(mode="json")
        payload["content_hash"] = sha256_text(json_stable(payload))
        instruments.append(payload)
    return {
        "profile_version": CAPABILITY_VERSION,
        "project_id": spec.project_id,
        "instruments": instruments,
        "instrument_count": len(instruments),
        "network_policy": "allow" if spec.prohibitions.network_allowed else "deny",
    }


def write_capability_profile(spec: LabProjectSpec, output_dir: Path) -> Path:
    profile = build_capability_profile(spec)
    target = output_dir / CAPABILITY_FILENAME
    write_json(target, profile)
    return target
