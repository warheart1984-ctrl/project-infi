"""Cloud manifold SG_cloud — frozen I_cloud and B_cloud for a mission."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any

from src.ugr.platform.tenant_registry import normalize_tenant_id


CLOUD_INVARIANT_SET_VERSION = "1.5"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def compute_cloud_identity_hash(
    *,
    tenant_id: str,
    operator_id: str,
    mission_id: str,
    organ_ids: list[str],
    region_ids: list[str],
    aais_instance_id: str,
) -> str:
    """I_cloud(M) = SHA256(semantic cloud actor binding)."""
    payload = {
        "tenant_id": normalize_tenant_id(tenant_id),
        "operator_id": str(operator_id or "").strip(),
        "mission_id": str(mission_id or "").strip(),
        "organ_ids": sorted({str(o).strip() for o in organ_ids if str(o).strip()}),
        "region_ids": sorted({str(r).strip() for r in region_ids if str(r).strip()}),
        "aais_instance_id": str(aais_instance_id or "").strip(),
    }
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def build_boundary_set(
    *,
    region_id: str,
    rail: str,
    organ_providers: list[tuple[str, str]],
) -> list[dict[str, str]]:
    """B_cloud(M) as sorted admissible (region, provider, rail) tuples."""
    region = str(region_id or "").strip()
    rail_upper = str(rail or "NORMAL").upper()
    tuples: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for organ_id, provider in organ_providers:
        provider_name = str(provider or "local").strip()
        key = (region, provider_name, rail_upper)
        if key in seen:
            continue
        seen.add(key)
        tuples.append({"region": region, "provider": provider_name, "rail": rail_upper, "organ_id": str(organ_id)})
    tuples.sort(key=lambda item: (item["region"], item["provider"], item["rail"], item.get("organ_id", "")))
    return tuples


def compute_boundary_digest(boundary_set: list[dict[str, str]]) -> str:
    """SHA256 of canonical boundary set."""
    canonical = [
        {
            "region": item["region"],
            "provider": item["provider"],
            "rail": item["rail"],
        }
        for item in sorted(
            boundary_set,
            key=lambda x: (x.get("region", ""), x.get("provider", ""), x.get("rail", "")),
        )
    ]
    return sha256(_stable_json(canonical).encode("utf-8")).hexdigest()


@dataclass
class CloudManifoldState:
    """Frozen cloud manifold at mission open."""

    cloud_identity_hash: str
    boundary_digest: str
    invariant_version: str = CLOUD_INVARIANT_SET_VERSION
    boundary_set: list[dict[str, str]] = field(default_factory=list)
    tenant_id: str = ""
    operator_id: str = ""
    mission_id: str = ""
    aais_instance_id: str = ""
    region_id: str = ""
    rail: str = "NORMAL"
    organ_ids: list[str] = field(default_factory=list)

    def boundary_tuples(self) -> set[tuple[str, str, str]]:
        return {
            (str(item.get("region") or ""), str(item.get("provider") or ""), str(item.get("rail") or ""))
            for item in self.boundary_set
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "cloud_identity_hash": self.cloud_identity_hash,
            "boundary_digest": self.boundary_digest,
            "invariant_version": self.invariant_version,
            "boundary_set": list(self.boundary_set),
            "tenant_id": self.tenant_id,
            "operator_id": self.operator_id,
            "mission_id": self.mission_id,
            "aais_instance_id": self.aais_instance_id,
            "region_id": self.region_id,
            "rail": self.rail,
            "organ_ids": list(self.organ_ids),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CloudManifoldState:
        return cls(
            cloud_identity_hash=str(payload.get("cloud_identity_hash") or ""),
            boundary_digest=str(payload.get("boundary_digest") or ""),
            invariant_version=str(payload.get("invariant_version") or CLOUD_INVARIANT_SET_VERSION),
            boundary_set=list(payload.get("boundary_set") or []),
            tenant_id=str(payload.get("tenant_id") or ""),
            operator_id=str(payload.get("operator_id") or ""),
            mission_id=str(payload.get("mission_id") or ""),
            aais_instance_id=str(payload.get("aais_instance_id") or ""),
            region_id=str(payload.get("region_id") or ""),
            rail=str(payload.get("rail") or "NORMAL"),
            organ_ids=list(payload.get("organ_ids") or []),
        )


@dataclass
class MissionCloudState:
    """Runtime cloud state for ValidCloudTransition."""

    mission_id: str
    cloud_identity_hash: str
    boundary_digest: str
    step_ids_seen: list[str] = field(default_factory=list)
    ledger_action_ids: list[str] = field(default_factory=list)
    status: str = "open"
    invariant_version: str = CLOUD_INVARIANT_SET_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "cloud_identity_hash": self.cloud_identity_hash,
            "boundary_digest": self.boundary_digest,
            "step_ids_seen": list(self.step_ids_seen),
            "ledger_action_ids": list(self.ledger_action_ids),
            "status": self.status,
            "invariant_version": self.invariant_version,
        }


def build_cloud_manifold(
    *,
    request: dict[str, Any],
    ingress: dict[str, Any],
    organ_ids: list[str],
    rail: str = "NORMAL",
    organ_registry: Any | None = None,
) -> CloudManifoldState:
    """Compute and freeze I_cloud + B_cloud at mission open."""
    from src.ugr.mission.provider_organ import ProviderOrganRegistry

    registry = organ_registry or ProviderOrganRegistry()
    region_id = str(request.get("region_id") or "").strip()
    admitted = list(organ_ids) or registry.admitted_organ_ids()
    organ_providers: list[tuple[str, str]] = []
    for oid in admitted:
        organ = registry.get(oid)
        if organ:
            organ_providers.append((oid, organ.provider))

    boundary_set = build_boundary_set(
        region_id=region_id,
        rail=rail,
        organ_providers=organ_providers,
    )
    identity_hash = compute_cloud_identity_hash(
        tenant_id=str(request.get("tenant_id") or ingress.get("tenant_id") or "default"),
        operator_id=str(request.get("operator_id") or ingress.get("operator_id") or ""),
        mission_id=str(ingress.get("mission_id") or ""),
        organ_ids=admitted,
        region_ids=[region_id] if region_id else [],
        aais_instance_id=str(request.get("aais_instance_id") or ingress.get("aais_instance_id") or ""),
    )
    return CloudManifoldState(
        cloud_identity_hash=identity_hash,
        boundary_digest=compute_boundary_digest(boundary_set),
        boundary_set=boundary_set,
        tenant_id=normalize_tenant_id(request.get("tenant_id")),
        operator_id=str(request.get("operator_id") or ingress.get("operator_id") or ""),
        mission_id=str(ingress.get("mission_id") or ""),
        aais_instance_id=str(request.get("aais_instance_id") or ingress.get("aais_instance_id") or ""),
        region_id=region_id,
        rail=str(rail or "NORMAL").upper(),
        organ_ids=admitted,
    )


def manifold_from_ingress(ingress: dict[str, Any]) -> CloudManifoldState | None:
    """Load manifold stamped on ingress."""
    if not ingress.get("cloud_identity_hash"):
        return None
    return CloudManifoldState.from_dict(
        {
            "cloud_identity_hash": ingress.get("cloud_identity_hash"),
            "boundary_digest": ingress.get("boundary_digest"),
            "invariant_version": ingress.get("invariant_version"),
            "boundary_set": ingress.get("boundary_set"),
            "tenant_id": ingress.get("tenant_id"),
            "operator_id": ingress.get("operator_id"),
            "mission_id": ingress.get("mission_id"),
            "aais_instance_id": ingress.get("aais_instance_id"),
            "region_id": ingress.get("region_id"),
            "rail": ingress.get("rail"),
            "organ_ids": ingress.get("organ_ids"),
        }
    )
