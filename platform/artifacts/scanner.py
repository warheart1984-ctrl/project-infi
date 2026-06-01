"""Ingest hash manifests from subsystem receipts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from platform.artifacts.index import ArtifactIndex
from platform.auth.rbac import Principal
from platform.common import sha256_file


def ingest_hash_manifest(
    *,
    index: ArtifactIndex,
    principal: Principal,
    subsystem: str,
    job_id: str,
    correlation_id: str,
    manifest: list[dict[str, Any]],
    base_dir: Path | None = None,
    lineage_parent_refs: list[str] | None = None,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for entry in manifest:
        artifact = str(entry.get("artifact") or entry.get("name") or "unknown")
        rel_path = str(entry.get("path") or artifact)
        path = Path(rel_path)
        if base_dir and not path.is_absolute():
            path = base_dir / path
        storage_uri = path.as_uri() if path.exists() else f"file://{rel_path}"
        sha = str(entry.get("sha256") or "")
        if not sha and path.is_file():
            sha = sha256_file(path)
        ref_payload = index.build_ref(
            org_id=principal.org_id,
            subsystem=subsystem,  # type: ignore[arg-type]
            logical_path=rel_path,
            storage_uri=storage_uri,
            sha256=sha or "0" * 64,
            job_id=job_id,
            correlation_id=correlation_id,
            claim_label=str(entry.get("claim_label") or "asserted"),  # type: ignore[arg-type]
            lineage_parent_refs=lineage_parent_refs,
            metadata={"artifact": artifact},
        )
        refs.append(index.register(principal=principal, payload=ref_payload))
    return refs
