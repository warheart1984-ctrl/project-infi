"""Model and tools binding station — v1 contract stub."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_factory.common import json_stable, sha256_text, write_json
from ai_factory.spec import AIBuildSpec

BINDING_VERSION = "ai_factory.bound_capability_profile.v1"


def build_bound_capability_profile(spec: AIBuildSpec) -> dict[str, Any]:
    return {
        "profile_version": BINDING_VERSION,
        "build_id": spec.build_id,
        "model_policy": "inherit_jarvis_default",
        "tools_allowed": list(spec.tools_allowed),
        "tools_forbidden": list(spec.prohibitions.forbidden_tools),
        "constraints": {
            "high_impact_actions_blocked": spec.prohibitions.high_impact_actions_blocked,
            "data_sensitivity": spec.data_sensitivity,
            "risk_level": spec.risk_level,
        },
        "note": "v1 stub — no model zoo or dynamic tool binding engine",
    }


def run_binding_station(
    *,
    spec: AIBuildSpec,
    output_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    profile = build_bound_capability_profile(spec)
    target = output_dir / "BOUND_CAPABILITY_PROFILE.json"
    write_json(target, profile)
    receipt = {
        "station": "binding",
        "station_version": "ai_factory.binding_station.v1",
        "status": "ok",
        "build_id": spec.build_id,
        "output": str(target.resolve()),
        "content_hash": sha256_text(json_stable(profile)),
        "trace": ["build_bound_capability_profile", "write_json"],
    }
    return profile, receipt
