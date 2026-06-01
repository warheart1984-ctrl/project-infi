"""Deployment envelope — build receipt and artifact hash manifest."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from ai_factory.common import (
    ClaimLabel,
    derive_claim_status,
    hash_manifest_entry,
    write_json,
)
from ai_factory.spec import AIBuildSpec
from src.datetime_compat import UTC

RECEIPT_VERSION = "ai_factory.build_receipt.v1"

ARTIFACT_NAMES: tuple[tuple[str, str], ...] = (
    ("build_spec", "AI_BUILD_SPEC.json"),
    ("spine_profile", "SpineProfile.json"),
    ("cortex_bundle", "CORTEX_RUNTIME_BUNDLE.json"),
    ("bound_capability", "BOUND_CAPABILITY_PROFILE.json"),
    ("proof_bundle_md", "AI_PROOF_BUNDLE.md"),
    ("proof_manifest", "proof_manifest.json"),
)


def build_hash_manifest(output_dir: Path, *, claim_label: ClaimLabel) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for artifact, filename in ARTIFACT_NAMES:
        path = output_dir / filename
        label: ClaimLabel = claim_label if path.is_file() else "rejected"
        entries.append(hash_manifest_entry(artifact=artifact, path=path, claim_label=label))
    return sorted(entries, key=lambda item: str(item["artifact"]))


def build_receipt(
    *,
    spec: AIBuildSpec,
    spine_profile: dict[str, Any],
    proof_manifest: dict[str, Any],
    output_dir: Path,
    station_receipts: dict[str, dict[str, Any]],
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at_utc or datetime.now(UTC).isoformat()
    claim_label = derive_claim_status(
        [
            str(proof_manifest.get("claim_label") or "asserted"),  # type: ignore[arg-type]
        ]
    )
    hash_manifest = build_hash_manifest(output_dir, claim_label=claim_label)
    manifest_claims: list[ClaimLabel] = [str(item["claim_label"]) for item in hash_manifest]  # type: ignore[arg-type]
    overall = derive_claim_status(manifest_claims + [claim_label])

    return {
        "receipt_version": RECEIPT_VERSION,
        "build_id": spec.build_id,
        "generated_at_utc": generated_at,
        "claim_label": overall,
        "risk_rating": spec.risk_level,
        "lifecycle_status": "active",
        "spine_profile_id": spine_profile.get("profile_id"),
        "proof_bundle_ref": str((output_dir / "AI_PROOF_BUNDLE.md").resolve()),
        "proof_manifest_ref": str((output_dir / "proof_manifest.json").resolve()),
        "deploy_blocked": bool(proof_manifest.get("deploy_blocked")),
        "hash_manifest": hash_manifest,
        "station_receipts": station_receipts,
        "output_dir": str(output_dir.resolve()),
    }


def run_envelope_station(
    *,
    spec: AIBuildSpec,
    spine_profile: dict[str, Any],
    proof_manifest: dict[str, Any],
    output_dir: Path,
    station_receipts: dict[str, dict[str, Any]],
    generated_at_utc: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = build_receipt(
        spec=spec,
        spine_profile=spine_profile,
        proof_manifest=proof_manifest,
        output_dir=output_dir,
        station_receipts=station_receipts,
        generated_at_utc=generated_at_utc,
    )
    receipt_path = output_dir / "AI_BUILD_RECEIPT.json"
    write_json(receipt_path, receipt)

    station_receipt_dir = output_dir / "station_receipts"
    station_receipt_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in station_receipts.items():
        write_json(station_receipt_dir / f"{name}.json", payload)

    envelope_receipt = {
        "station": "envelope",
        "station_version": "ai_factory.envelope_station.v1",
        "status": "ok",
        "build_id": spec.build_id,
        "claim_label": receipt.get("claim_label"),
        "output": str(receipt_path.resolve()),
        "trace": ["build_hash_manifest", "write_build_receipt", "write_station_receipts"],
    }
    return receipt, envelope_receipt


def revoke_build_receipt(output_dir: Path) -> dict[str, Any]:
    receipt_path = output_dir / "AI_BUILD_RECEIPT.json"
    if not receipt_path.is_file():
        raise FileNotFoundError(f"missing receipt: {receipt_path}")
    import json

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["lifecycle_status"] = "revoked"
    write_json(receipt_path, receipt)
    return receipt
