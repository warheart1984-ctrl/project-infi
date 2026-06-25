"""Lab spine profile — constitutional tool policy bound to a project spec."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lab.common import SPINE_FILENAME, SPINE_VERSION, write_json
from lab.spec import LabProjectSpec


def build_lab_spine_profile(spec: LabProjectSpec) -> dict[str, Any]:
    profile_id = f"{spec.project_id}.spine"
    instrument_names = sorted({item.name for item in spec.instruments})
    return {
        "profile_version": SPINE_VERSION,
        "profile_id": profile_id,
        "project_id": spec.project_id,
        "risk_level": spec.risk_level,
        "stages": {
            "rls_substrate": {
                "enabled": True,
                "network_allowed": spec.prohibitions.network_allowed,
                "workspace_only_writes": True,
                "fail_closed": spec.risk_level == "high",
            },
            "jarvis_authorize": {
                "enabled": True,
                "blocked_actions": list(spec.prohibitions.forbidden_commands),
                "read_only_paths": list(spec.prohibitions.read_only_paths),
                "high_impact_patterns": list(spec.prohibitions.high_impact_patterns),
            },
            "cortex_execute": {
                "enabled": True,
                "enabled_instruments": instrument_names,
            },
            "speaking_emit": {
                "enabled": spec.require_session_summary,
                "required": spec.require_session_summary,
            },
        },
    }


def write_spine_profile(spec: LabProjectSpec, output_dir: Path) -> Path:
    profile = build_lab_spine_profile(spec)
    target = output_dir / SPINE_FILENAME
    write_json(target, profile)
    return target
