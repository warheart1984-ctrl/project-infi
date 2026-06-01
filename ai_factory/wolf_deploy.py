"""AI Factory v1.1 — promote verified builds into Wolf CoG OS payload."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ai_factory.common import json_stable, sha256_file, write_json
from ai_factory.orchestrator import FactoryBuildError

WOLF_DEPLOY_VERSION = "ai_factory.wolf_deploy.v1"
DEFAULT_WOLF_PAYLOAD = Path("wolf-cog-os/payload/opt/cogos/config")
DEFAULT_WOLF_RUNTIME = Path("wolf-cog-os/payload/opt/cogos/runtime/factory")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _preflight_build(source_dir: Path) -> dict[str, Any]:
    receipt_path = source_dir / "AI_BUILD_RECEIPT.json"
    proof_path = source_dir / "proof_manifest.json"
    if not receipt_path.is_file():
        raise FactoryBuildError(f"missing receipt: {receipt_path}")
    receipt = _load_json(receipt_path)
    if str(receipt.get("lifecycle_status") or "") == "revoked":
        raise FactoryBuildError(f"build revoked: {receipt.get('build_id')}")
    proof = _load_json(proof_path) if proof_path.is_file() else {}
    if proof.get("deploy_blocked"):
        raise FactoryBuildError("proof manifest blocks deploy")
    required = (
        "AI_BUILD_SPEC.json",
        "SpineProfile.json",
        "CORTEX_RUNTIME_BUNDLE.json",
        "AI_BUILD_RECEIPT.json",
    )
    missing = [name for name in required if not (source_dir / name).is_file()]
    if missing:
        raise FactoryBuildError(f"build missing artifacts: {', '.join(missing)}")
    return {"receipt": receipt, "proof": proof}


def deploy_build_to_wolf_payload(
    *,
    build_id: str,
    runtime_root: Path,
    repo_root: Path,
    wolf_payload_root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Copy factory build artifacts into wolf-cog-os payload (v1.1 path)."""
    source = runtime_root.expanduser().resolve() / build_id
    if not source.is_dir():
        raise FactoryBuildError(f"build output not found: {source}")

    preflight = _preflight_build(source)
    receipt = preflight["receipt"]
    bundle = _load_json(source / "CORTEX_RUNTIME_BUNDLE.json")
    spine = _load_json(source / "SpineProfile.json")
    spec = _load_json(source / "AI_BUILD_SPEC.json")

    repo = repo_root.expanduser().resolve()
    payload_root = (wolf_payload_root or repo / DEFAULT_WOLF_PAYLOAD).expanduser().resolve()
    factory_runtime = (repo / DEFAULT_WOLF_RUNTIME).expanduser().resolve()

    family_spec = dict(bundle.get("family_spec") or {})
    if not family_spec.get("family_id"):
        raise FactoryBuildError("CORTEX_RUNTIME_BUNDLE missing family_spec")

    targets = {
        "cognitive_runtime_family": payload_root / "cognitive_runtime_family.json",
        "ai_factory_spine_profile": payload_root / "ai_factory_spine_profile.json",
        "ai_factory_active_build": payload_root / "ai_factory_active_build.json",
    }
    runtime_targets = {
        "CORTEX_RUNTIME_BUNDLE.json": factory_runtime / "CORTEX_RUNTIME_BUNDLE.json",
        "SpineProfile.json": factory_runtime / "SpineProfile.json",
        "AI_BUILD_RECEIPT.json": factory_runtime / "AI_BUILD_RECEIPT.json",
        "AI_BUILD_SPEC.json": factory_runtime / "AI_BUILD_SPEC.json",
    }

    deploy_receipt: dict[str, Any] = {
        "deploy_version": WOLF_DEPLOY_VERSION,
        "build_id": build_id,
        "claim_label": "asserted",
        "dry_run": dry_run,
        "source_dir": str(source),
        "targets": {key: str(path) for key, path in targets.items()},
        "runtime_targets": {key: str(path) for key, path in runtime_targets.items()},
        "hash_manifest": [],
    }

    if not dry_run:
        payload_root.mkdir(parents=True, exist_ok=True)
        factory_runtime.mkdir(parents=True, exist_ok=True)
        write_json(targets["cognitive_runtime_family"], family_spec)
        write_json(targets["ai_factory_spine_profile"], spine)
        write_json(
            targets["ai_factory_active_build"],
            {
                "build_id": build_id,
                "receipt_path": str((source / "AI_BUILD_RECEIPT.json").resolve()),
                "spec_intent": spec.get("intent_summary"),
                "spine_profile_id": spine.get("profile_id"),
                "bundle_id": bundle.get("bundle_id"),
            },
        )
        for name, dest in runtime_targets.items():
            shutil.copy2(source / name, dest)
            deploy_receipt["hash_manifest"].append(
                {"artifact": name, "path": str(dest), "sha256": sha256_file(dest)}
            )

    deploy_receipt_path = source / "WOLF_DEPLOY_RECEIPT.json"
    if not dry_run:
        write_json(deploy_receipt_path, deploy_receipt)

    return deploy_receipt
