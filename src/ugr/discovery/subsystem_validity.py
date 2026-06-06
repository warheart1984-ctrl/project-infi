"""Validity function for Proof-of-Subsystem discovery."""

from __future__ import annotations

from dataclasses import dataclass, field
import uuid
from typing import Any

from src.cloud_forge.types import RAIL_ORDER, Rail, cap_rail_at_ceiling
from src.ugr.cloud_forge_bridge import (
    build_ugr_law_envelope,
    resolve_tenant_manifold_for_forge,
    schedule_rail_for_ugr,
)
from src.ugr.discovery.subsystem_spec import (
    RISK_CEILINGS,
    SubsystemSpec,
    role_to_capability,
    validate_spec_shape,
)
from src.ugr.invariants.cloud_invariants import (
    check_cloud_boundary,
    check_cloud_forge_rail,
    check_cloud_identity,
    has_hard_fail,
)
from src.ugr.invariants.cloud_manifold import build_cloud_manifold
from src.ugr.mission.provider_organ import ProviderOrgan, ProviderOrganRegistry
from src.ugr.platform.tenant_registry import TenantRegistry, normalize_tenant_id

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def expected_tenant_class(tenant_id: str) -> str:
    normalized = normalize_tenant_id(tenant_id)
    if normalized == "global":
        return "global"
    spec = TenantRegistry().get(normalized)
    if spec is None:
        return "restricted"
    providers = spec.allowed_providers
    if providers and len(providers) <= 1:
        return "restricted"
    return "standard"


@dataclass
class ValidityResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    invariants: list[dict[str, str]] = field(default_factory=list)
    organs_matched: list[dict[str, str]] = field(default_factory=list)
    rail_proof: dict[str, Any] = field(default_factory=dict)
    genome_metadata: dict[str, Any] = field(default_factory=dict)
    organ_id: str = ""
    region_id: str = ""


def _risk_allows(organ_ceiling: str, spec_ceiling: str) -> bool:
    organ_rank = RISK_ORDER.get(str(organ_ceiling or "high").lower(), 2)
    spec_rank = RISK_ORDER.get(str(spec_ceiling or "medium").lower(), 1)
    return organ_rank <= spec_rank


def _organ_matches_spec(organ: ProviderOrgan, spec: SubsystemSpec) -> bool:
    capability = role_to_capability(spec.role)
    caps = {str(c).strip().lower() for c in (organ.function.get("capabilities") or [])}
    domains = {str(d).strip().lower() for d in (organ.contract.get("allowed_domains") or [])}
    if capability not in caps and capability not in domains:
        return False
    if not _risk_allows(str(organ.contract.get("risk_ceiling") or "high"), spec.risk_ceiling):
        return False
    admissible = {str(r).upper() for r in (organ.contract.get("admissible_rails") or [])}
    if admissible and spec.rail_class not in admissible:
        return False
    return True


def match_organs(
    spec: SubsystemSpec,
    *,
    tenant_id: str,
    registry: ProviderOrganRegistry | None = None,
) -> list[ProviderOrgan]:
    reg = registry or ProviderOrganRegistry(tenant_id=tenant_id)
    matched = [organ for organ in reg.routable_organs() if _organ_matches_spec(organ, spec)]
    matched.sort(key=lambda o: o.organ_id)
    return matched


def _rail_rank(rail: str) -> int:
    try:
        return RAIL_ORDER[Rail(str(rail or "NORMAL").upper())]
    except ValueError:
        return RAIL_ORDER[Rail.NORMAL]


def validate_subsystem_spec(
    spec: SubsystemSpec,
    *,
    tenant_id: str,
    operator_id: str,
    aais_instance_id: str,
    constraints: dict[str, Any] | None = None,
    organ_registry: ProviderOrganRegistry | None = None,
) -> ValidityResult:
    """Fail-closed validity: organ graph, invariants, rail, tenant_class."""
    result = ValidityResult(valid=False)
    shape_errors = validate_spec_shape(spec)
    if shape_errors:
        result.errors.extend(shape_errors)
        return result

    normalized_tenant = normalize_tenant_id(tenant_id)
    tenant_spec = TenantRegistry().get(normalized_tenant)
    if tenant_spec is None and normalized_tenant != "global":
        result.errors.append(f"unknown tenant: {normalized_tenant}")
        return result
    if tenant_spec is not None and not tenant_spec.enabled:
        result.errors.append(f"tenant disabled: {normalized_tenant}")
        return result

    allowed_classes = list((constraints or {}).get("tenant_classes") or [])
    expected = expected_tenant_class(normalized_tenant)
    if allowed_classes and spec.tenant_class not in {str(c).lower() for c in allowed_classes}:
        result.errors.append(f"tenant_class {spec.tenant_class} not in constraint allow-list")
        return result
    if spec.tenant_class != expected and not allowed_classes:
        result.errors.append(f"tenant_class mismatch: spec={spec.tenant_class} expected={expected}")
        return result

    organs = match_organs(spec, tenant_id=normalized_tenant, registry=organ_registry)
    if not organs:
        result.errors.append("no admitted organ matches role/io_shape/rail/risk")
        result.invariants.append({"family": "organ_graph", "status": "hard_fail", "details": "no match"})
        return result

    organ = organs[0]
    result.organ_id = organ.organ_id
    regions = list((tenant_spec.allowed_regions if tenant_spec else ()) or organ.contract.get("allowed_regions") or [])
    result.region_id = str(regions[0] if regions else "local-primary")
    result.organs_matched = [
        {
            "organ_id": o.organ_id,
            "provider": o.provider,
            "risk_ceiling": str(o.contract.get("risk_ceiling") or ""),
            "rail": spec.rail_class,
        }
        for o in organs[:3]
    ]
    result.invariants.append({"family": "organ_graph", "status": "pass", "details": f"matched={organ.organ_id}"})

    try:
        from src.governance_organs.genome_engine import GenomeEngine

        gene = GenomeEngine.resolve_gene(spec.role)
        if gene:
            genome = GenomeEngine.registry().genomes.get(gene) or {}
            identity = dict(genome.get("identity") or {})
            result.genome_metadata = {
                "gene": gene,
                "stage": str(identity.get("stage") or ""),
                "version": str(identity.get("version") or ""),
            }
    except Exception:
        pass

    mission_id = str(uuid.uuid4())
    ingress = {
        "mission_id": mission_id,
        "tenant_id": normalized_tenant,
        "operator_id": operator_id,
        "aais_instance_id": aais_instance_id,
        "organ_ids": [organ.organ_id],
    }
    request = {
        "tenant_id": normalized_tenant,
        "operator_id": operator_id,
        "aais_instance_id": aais_instance_id,
        "region_id": result.region_id,
        "intent": role_to_capability(spec.role),
        "constraints": {"risk_ceiling": spec.risk_ceiling},
    }
    reg = organ_registry or ProviderOrganRegistry(tenant_id=normalized_tenant)
    manifold = build_cloud_manifold(
        request=request,
        ingress=ingress,
        organ_ids=[organ.organ_id],
        rail=spec.rail_class,
        organ_registry=reg,
    )
    mission_state = {
        "request": request,
        "ingress": ingress,
        "cloud_manifold": manifold.to_dict(),
        "region_id": result.region_id,
        "organ_ids": [organ.organ_id],
    }
    step_assignment = {
        "organ_id": organ.organ_id,
        "provider": organ.provider,
        "rail": spec.rail_class,
    }

    identity_results = check_cloud_identity(mission_state, manifold=manifold)
    boundary_results = check_cloud_boundary(mission_state, step_assignment, manifold=manifold)
    forge_results = check_cloud_forge_rail(mission_state, step_assignment, manifold=manifold)
    for item in identity_results + boundary_results + forge_results:
        result.invariants.append(
            {
                "family": str(item.get("family") or ""),
                "status": str(item.get("status") or ""),
                "details": str(item.get("details") or ""),
            }
        )
    if has_hard_fail(identity_results + boundary_results + forge_results):
        result.errors.append("cloud invariant hard_fail")
        return result

    trace_id = f"discover-{mission_id[:8]}"
    deliberation_request = {
        "tenant_id": normalized_tenant,
        "operator_id": operator_id,
        "intent": role_to_capability(spec.role),
        "question": f"subsystem discovery probe for {spec.role}",
        "constraints": {"risk_ceiling": spec.risk_ceiling},
        "context": {"mutation_scope": "read", "subsystem_discovery": True},
    }
    tenant_manifold = resolve_tenant_manifold_for_forge(deliberation_request)
    bundle = schedule_rail_for_ugr(
        deliberation_request,
        trace_id=trace_id,
        tenant_manifold=tenant_manifold,
    )
    if not bundle:
        result.errors.append("rail scheduling unavailable (Cloud Forge disabled)")
        result.invariants.append({"family": "rail_schedule", "status": "hard_fail", "details": "no bundle"})
        return result

    decision = dict(bundle.get("rail_decision") or {})
    scheduled = str(decision.get("rail") or "NORMAL").upper()
    requested_rail = Rail(spec.rail_class)
    scheduled_rail = Rail(scheduled) if scheduled in {r.value for r in Rail} else Rail.NORMAL
    capped = cap_rail_at_ceiling(scheduled_rail, requested_rail)
    if _rail_rank(capped.value) > _rail_rank(spec.rail_class):
        result.errors.append(f"scheduled rail {capped.value} exceeds requested {spec.rail_class}")
        result.invariants.append(
            {
                "family": "rail_compatibility",
                "status": "hard_fail",
                "details": f"scheduled={capped.value} requested={spec.rail_class}",
            }
        )
        return result

    law = build_ugr_law_envelope(deliberation_request, tenant_manifold=tenant_manifold)
    result.rail_proof = {
        "requested": spec.rail_class,
        "scheduled": capped.value,
        "codes": list(decision.get("rationale_codes") or []),
        "law_id": law.get("law_id"),
        "law_version": law.get("law_version"),
    }
    result.invariants.append(
        {
            "family": "rail_compatibility",
            "status": "pass",
            "details": f"scheduled={capped.value}",
        }
    )

    result.valid = True
    return result
