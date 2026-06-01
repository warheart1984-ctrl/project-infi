"""Cognitive runtime bundle assembly from certified Nova modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_factory.common import json_stable, sha256_text, write_json
from ai_factory.spec import AIBuildSpec

BUNDLE_VERSION = "ai_factory.cortex_bundle.v1"
DEFAULT_PROOF_REFS: tuple[str, ...] = (
    "docs/proof/cognitive_runtime/FAMILY_V3_0_PROOF_BUNDLE.md",
    "docs/proof/cognitive_runtime/SPARK_V1_PROOF_BUNDLE.md",
    "docs/proof/cognitive_runtime/COMPOSED_TURN_V1_PROOF_BUNDLE.md",
)


def build_cortex_runtime_bundle(
    *,
    spec: AIBuildSpec,
    spine_profile: dict[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    from src.aais_composed_runtime import composed_runtime_spec
    from src.cog_runtime import nova_cortex_spec
    from src.cog_runtime.capability_governance import (
        CORTEX_MODULE_CAPABILITY_MATRIX,
        NOVA_LOBE_CAPABILITY_MATRIX,
    )
    from src.cog_runtime.formal.activation_predicates import activation_predicate_spec

    family = nova_cortex_spec()
    enabled = set(spec.capabilities.enabled_lobes)
    runtimes = [
        item
        for item in family.get("runtimes") or []
        if str(item.get("runtime_id") or item.get("id") or "") in enabled
    ]
    lobe_matrix = {
        key: value
        for key, value in NOVA_LOBE_CAPABILITY_MATRIX.items()
        if key in enabled
    }

    bundle_id = f"{spec.build_id}.cortex"
    return {
        "bundle_version": BUNDLE_VERSION,
        "bundle_id": bundle_id,
        "build_id": spec.build_id,
        "family_spec": family,
        "composed_spec": composed_runtime_spec(),
        "activation_predicates": activation_predicate_spec(),
        "enabled_runtimes": sorted(enabled),
        "filtered_runtimes": runtimes,
        "capability_matrix": {
            "lobes": lobe_matrix,
            "modules": dict(CORTEX_MODULE_CAPABILITY_MATRIX),
        },
        "compose_mode_default": spec.capabilities.compose_mode,
        "spine_profile_id": spine_profile.get("profile_id"),
        "spine_profile_ref": "SpineProfile.json",
        "proof_refs": list(DEFAULT_PROOF_REFS),
        "repo_root": str((repo_root or Path(".")).resolve()),
    }


def bundle_content_hash(bundle: dict[str, Any]) -> str:
    slim = {
        "bundle_version": bundle.get("bundle_version"),
        "bundle_id": bundle.get("bundle_id"),
        "build_id": bundle.get("build_id"),
        "enabled_runtimes": bundle.get("enabled_runtimes"),
        "spine_profile_id": bundle.get("spine_profile_id"),
    }
    return sha256_text(json_stable(slim))


def run_runtime_station(
    *,
    spec: AIBuildSpec,
    spine_profile: dict[str, Any],
    output_dir: Path,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    bundle = build_cortex_runtime_bundle(
        spec=spec,
        spine_profile=spine_profile,
        repo_root=repo_root,
    )
    target = output_dir / "CORTEX_RUNTIME_BUNDLE.json"
    write_json(target, bundle)
    receipt = {
        "station": "runtime",
        "station_version": "ai_factory.runtime_station.v1",
        "status": "ok",
        "build_id": spec.build_id,
        "bundle_id": bundle["bundle_id"],
        "enabled_runtime_count": len(bundle.get("enabled_runtimes") or []),
        "output": str(target.resolve()),
        "content_hash": bundle_content_hash(bundle),
        "trace": [
            "aggregate_nova_cortex_spec",
            "aggregate_composed_runtime_spec",
            "filter_enabled_lobes",
            "write_cortex_runtime_bundle",
        ],
    }
    return bundle, receipt
