"""Spine Profile — constitutional spine bound to an AI build spec."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_factory.common import json_stable, sha256_text, write_json
from ai_factory.spec import AIBuildSpec

SPINE_PROFILE_VERSION = "ai_factory.spine_profile.v1"
SPINE_PIPELINE_ID = "nova.spine.v1"


def _substrate_default(risk_level: str) -> bool:
    if risk_level == "high":
        return False
    if risk_level == "medium":
        return True
    return True


def build_spine_profile(spec: AIBuildSpec) -> dict[str, Any]:
    """Derive a Spine Profile from a validated build spec."""

    profile_id = f"{spec.build_id}.spine"
    return {
        "profile_version": SPINE_PROFILE_VERSION,
        "profile_id": profile_id,
        "build_id": spec.build_id,
        "pipeline_id": SPINE_PIPELINE_ID,
        "risk_level": spec.risk_level,
        "data_sensitivity": spec.data_sensitivity,
        "stages": {
            "rls_substrate": {
                "enabled": True,
                "substrate_ok_default": _substrate_default(spec.risk_level),
                "fail_closed": spec.risk_level == "high",
            },
            "aris_admit": {
                "enabled": True,
                "require_non_copy_clause": spec.data_sensitivity == "restricted",
            },
            "jarvis_authorize": {
                "enabled": True,
                "blocked_actions": list(spec.prohibitions.forbidden_tools),
                "block_high_impact": spec.prohibitions.high_impact_actions_blocked,
            },
            "cortex_execute": {
                "enabled": True,
                "cognitive_runtime_enabled": True,
                "enabled_lobes": list(spec.capabilities.enabled_lobes),
            },
            "speaking_emit": {
                "enabled": True,
                "required": spec.oversight.require_speaking,
                "speaking_mode": spec.interfaces.speaking_mode,
            },
        },
        "spark_stages": {
            "agency_preservation": {"required": spec.oversight.require_agency_check},
            "generation_gate": {"required": spec.oversight.require_generation_gate},
        },
        "compose_mode_default": spec.capabilities.compose_mode,
        "face_id": spec.interfaces.face_id,
    }


def build_turn_context_from_profile(
    profile: dict[str, Any],
    session_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a spine turn dict for proof scenarios (not live api.py wiring in v1)."""

    meta = dict(session_metadata or {})
    substrate = profile.get("stages", {}).get("rls_substrate", {})
    jarvis = profile.get("stages", {}).get("jarvis_authorize", {})
    cortex = profile.get("stages", {}).get("cortex_execute", {})
    speaking = profile.get("stages", {}).get("speaking_emit", {})

    substrate_ok = meta.get("substrate_ok", substrate.get("substrate_ok_default", True))
    if substrate.get("fail_closed") and "substrate_ok" not in meta:
        substrate_ok = substrate.get("substrate_ok_default", False)

    return {
        "substrate_ok": bool(substrate_ok),
        "governance": meta.get("governance") or meta.get("policy_status") or {},
        "aris_admission": meta.get("aris_admission") or {"status": "admitted"},
        "jarvis_blocked": bool(meta.get("jarvis_blocked", False)),
        "policy_status": meta.get("policy_status") or {},
        "cognitive_runtime_enabled": cortex.get("cognitive_runtime_enabled", True),
        "cortex_halted": bool(meta.get("cortex_halted", False)),
        "speaking_runtime_enabled": speaking.get("required", True),
        "speaking_validation": meta.get("speaking_validation") or {"valid": True},
        "companion_turn": bool(meta.get("companion_turn", False)),
        "blocked_actions": list(jarvis.get("blocked_actions") or []),
        "spine_profile_id": profile.get("profile_id"),
    }


def profile_content_hash(profile: dict[str, Any]) -> str:
    return sha256_text(json_stable(profile))


def run_spine_station(
    *,
    spec: AIBuildSpec,
    output_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    profile = build_spine_profile(spec)
    target = output_dir / "SpineProfile.json"
    write_json(target, profile)
    receipt = {
        "station": "spine",
        "station_version": "ai_factory.spine_station.v1",
        "status": "ok",
        "build_id": spec.build_id,
        "profile_id": profile["profile_id"],
        "pipeline_id": profile["pipeline_id"],
        "output": str(target.resolve()),
        "content_hash": profile_content_hash(profile),
        "trace": [
            "derive_spine_profile",
            "bind_risk_and_oversight",
            "write_spine_profile_json",
        ],
    }
    return profile, receipt
