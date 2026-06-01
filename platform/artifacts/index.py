"""Platform artifact federation index."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from src.datetime_compat import UTC

from platform.auth.audit import append_audit_event
from platform.auth.rbac import Principal
from platform.common import REF_VERSION, ClaimLabel, Subsystem, new_id, sha256_file
from platform.routing.region import artifact_storage_prefix
from platform.store import PlatformStore


class ArtifactIndex:
    def __init__(self, *, store: PlatformStore, audit_path: Path | None = None) -> None:
        self.store = store
        self.audit_path = audit_path

    def build_ref(
        self,
        *,
        org_id: str,
        subsystem: Subsystem,
        logical_path: str,
        storage_uri: str,
        sha256: str,
        job_id: str = "",
        correlation_id: str = "",
        claim_label: ClaimLabel = "asserted",
        lineage_parent_refs: list[str] | None = None,
        ttl_days: int = 0,
        metadata: dict[str, Any] | None = None,
        visibility: str = "org",
        retention_class: str = "standard",
        artifact_type: str = "bundle",
    ) -> dict[str, Any]:
        return {
            "ref_version": REF_VERSION,
            "ref_id": new_id("art"),
            "org_id": org_id,
            "job_id": job_id,
            "correlation_id": correlation_id,
            "subsystem": subsystem,
            "logical_path": logical_path,
            "storage_uri": storage_uri,
            "sha256": sha256,
            "claim_label": claim_label,
            "lineage_parent_refs": lineage_parent_refs or [],
            "visibility": visibility,
            "retention_class": retention_class,
            "artifact_type": artifact_type,
            "acl": {"org_id": org_id, "visibility": visibility},
            "registered_at": datetime.now(UTC).isoformat(),
            "ttl_days": ttl_days,
            "metadata": metadata or {},
        }

    def register(
        self,
        *,
        principal: Principal,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if payload.get("org_id") != principal.org_id and not principal.is_platform_admin():
            raise PermissionError("cross-org artifact registration denied")
        ref = dict(payload)
        if not ref.get("ref_id"):
            ref["ref_id"] = new_id("art")
        ref["ref_version"] = REF_VERSION
        ref.setdefault("acl", {"org_id": ref["org_id"], "visibility": "org_private"})
        ref.setdefault("registered_at", datetime.now(UTC).isoformat())
        self.store.upsert_artifact_ref(ref)
        if self.audit_path:
            append_audit_event(
                audit_path=self.audit_path,
                org_id=principal.org_id,
                principal_id=principal.principal_id,
                action="artifact.register",
                ref_id=str(ref["ref_id"]),
                store=self.store,
            )
        return ref

    def get_ref(self, ref_id: str, *, org_id: str, platform_admin: bool = False) -> dict[str, Any] | None:
        ref = self.store.get_artifact_ref(ref_id)
        if not ref:
            return None
        if ref.get("org_id") != org_id and not platform_admin:
            return None
        return ref

    def lineage(self, ref_id: str, *, org_id: str, platform_admin: bool = False) -> dict[str, Any]:
        root = self.get_ref(ref_id, org_id=org_id, platform_admin=platform_admin)
        if not root:
            return {"ref_id": ref_id, "nodes": [], "edges": []}
        nodes = [root]
        edges: list[dict[str, str]] = []
        for parent_id in root.get("lineage_parent_refs") or []:
            parent = self.store.get_artifact_ref(str(parent_id))
            if parent and (parent.get("org_id") == org_id or platform_admin):
                nodes.append(parent)
                edges.append({"from": parent_id, "to": ref_id, "type": "lineage"})
        return {"ref_id": ref_id, "nodes": nodes, "edges": edges}

    def list_refs(
        self,
        *,
        org_id: str,
        subsystem: str = "",
        correlation_id: str = "",
        job_id: str = "",
        artifact_type: str = "",
        visibility: str = "",
    ) -> list[dict[str, Any]]:
        return self.store.list_artifact_refs(
            org_id=org_id,
            subsystem=subsystem,
            correlation_id=correlation_id,
            job_id=job_id,
            artifact_type=artifact_type,
            visibility=visibility,
        )

    def register_directory(
        self,
        *,
        principal: Principal,
        subsystem: Subsystem,
        directory: Path,
        job_id: str = "",
        correlation_id: str = "",
        lineage_parent_refs: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        refs: list[dict[str, Any]] = []
        if not directory.is_dir():
            return refs
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".json", ".jsonl", ".md", ".txt"}:
                continue
            atype = "receipt" if "receipt" in path.name.lower() else "scan" if "scan" in path.name.lower() else "bundle"
            org = self.store.get_org(principal.org_id) or {}
            region = str(org.get("region") or "us")
            prefix = artifact_storage_prefix(
                region=region,
                org_id=principal.org_id,
                subsystem=subsystem,
                job_id=job_id or "none",
            )
            ref = self.build_ref(
                org_id=principal.org_id,
                subsystem=subsystem,
                logical_path=str(path.relative_to(directory)),
                storage_uri=f"{prefix}{path.name}",
                sha256=sha256_file(path),
                job_id=job_id,
                correlation_id=correlation_id,
                lineage_parent_refs=lineage_parent_refs,
                artifact_type=atype,
            )
            refs.append(self.register(principal=principal, payload=ref))
        return refs
