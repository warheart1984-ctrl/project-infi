"""Synthetic Mind refs — platform index only (MA-13: no cortex execution here)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from src.datetime_compat import UTC

from platform.common import sha256_file
from platform.store import PlatformStore

REF_VERSION = "platform.synthetic_mind_ref.v1"


def _bundle_hash_from_manifest(manifest_path: Path) -> str:
    if not manifest_path.is_file():
        return "0" * 64
    import json

    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    bundle_sha = str(manifest.get("bundle_sha256") or "")
    if bundle_sha:
        return bundle_sha
    return sha256_file(manifest_path)


def build_synthetic_mind_ref(
    *,
    org_id: str,
    build_id: str,
    family_id: str = "nova.cortex",
    family_version: str = "",
    spark_pipeline_id: str = "nova.spark.v1",
    bundle_hash: str = "",
    deploy_target: str = "artifact_index",
    storage_uri: str = "",
    job_id: str = "",
    claim_label: str = "asserted",
    read_only_projection_sample: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sample = read_only_projection_sample or {
        "projection_version": "1.0",
        "read_only": True,
    }
    return {
        "ref_version": REF_VERSION,
        "org_id": org_id,
        "build_id": build_id,
        "bundle_hash": bundle_hash or ("0" * 64),
        "family_id": family_id,
        "family_version": family_version,
        "spark_pipeline_id": spark_pipeline_id,
        "deploy_target": deploy_target,
        "storage_uri": storage_uri,
        "job_id": job_id,
        "claim_label": claim_label,
        "read_only_projection_sample": sample,
        "registered_at": datetime.now(UTC).isoformat(),
        "metadata": metadata or {},
    }


def register_synthetic_mind_for_org(
    *,
    store: PlatformStore,
    org_id: str,
    ref: dict[str, Any],
) -> dict[str, Any]:
    org = store.get_org(org_id) or {"org_id": org_id}
    org = dict(org)
    org["synthetic_mind_ref"] = ref
    org["synthetic_mind_active_build_id"] = ref.get("build_id")
    store.upsert_org(org)
    return ref


def get_synthetic_mind_ref(store: PlatformStore, org_id: str) -> dict[str, Any] | None:
    org = store.get_org(org_id)
    if not org:
        return None
    ref = org.get("synthetic_mind_ref")
    return dict(ref) if isinstance(ref, dict) else None


def ref_from_ai_factory_result(
    *,
    org_id: str,
    result: dict[str, Any],
    job_id: str = "",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    build_id = str(result.get("build_id") or "")
    receipt = dict(result.get("receipt") or {})
    output_dir = Path(str(result.get("output_dir") or "."))
    bundle_path = output_dir / "CORTEX_RUNTIME_BUNDLE.json"
    family_id = "nova.cortex"
    family_version = ""
    if bundle_path.is_file():
        import json

        bundle = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
        family = dict(bundle.get("family_spec") or {})
        family_id = str(family.get("family_id") or family_id)
        family_version = str(family.get("version") or "")

    manifest_path = (
        (repo_root or Path(".")).resolve()
        / "artifacts/synthetic-mind-bundle/synthetic_mind_manifest.json"
    )
    bundle_hash = _bundle_hash_from_manifest(manifest_path)
    if bundle_hash == "0" * 64:
        for entry in result.get("hash_manifest") or []:
            if str(entry.get("artifact") or "") == "CORTEX_RUNTIME_BUNDLE.json":
                bundle_hash = str(entry.get("sha256") or bundle_hash)
                break

    return build_synthetic_mind_ref(
        org_id=org_id,
        build_id=build_id,
        family_id=family_id,
        family_version=family_version,
        bundle_hash=bundle_hash,
        deploy_target="artifact_index",
        storage_uri=output_dir.resolve().as_uri() if output_dir.exists() else "",
        job_id=job_id,
        metadata={
            "intent_summary": receipt.get("intent_summary"),
            "lifecycle_status": receipt.get("lifecycle_status"),
        },
    )
