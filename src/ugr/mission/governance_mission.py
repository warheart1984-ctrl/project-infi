"""Governance mutation missions — URG config changes under cloud_mutation law."""

from __future__ import annotations

from hashlib import sha256
import json
import os
import time
from pathlib import Path
from typing import Any

from src.ugr.invariants.cloud_invariants import check_cloud_mutation, has_hard_fail
from src.ugr.mission.composite_mission import attach_gcm_to_response, decompose_mission
from src.ugr.mission.ingress import UrgIngressLaw
from src.ugr.invariants.cloud_manifold import build_cloud_manifold
from src.ugr.mission.marketplace import apply_provider_organ_mutation
from src.ugr.mission.mission_ledger import MissionLedger
from src.ugr.mission.provider_organ import ProviderOrganRegistry
from src.ugr.mission.tenant_manifold import tenant_path_slug, validate_tenant_for_mission
from src.ugr.platform.tenant_registry import TenantRegistry, normalize_tenant_id


GOVERNANCE_DEPLOY_ROOT = Path(__file__).resolve().parents[3] / "deploy" / "ugr"

MUTATION_PATHS = {
    "provider_organs": GOVERNANCE_DEPLOY_ROOT / "provider-organs.json",
    "regions": GOVERNANCE_DEPLOY_ROOT / "regions.json",
    "aais_instances": GOVERNANCE_DEPLOY_ROOT / "aais-instances.json",
    "invariant_definitions": Path(__file__).resolve().parents[2] / "invariants" / "cloud_invariants.py",
    "tenant_config": GOVERNANCE_DEPLOY_ROOT / "tenants.json",
}

MARKETPLACE_OPS = frozenset({
    "organ_admit",
    "organ_suspend",
    "organ_evict",
    "organ_query",
    "federation_organ_admit",
    "federation_organ_suspend",
})
FEDERATION_GOVERNANCE_OPS = frozenset({"federation_organ_admit", "federation_organ_suspend"})
CLOUD_FORGE_PROFILE_OPS = frozenset({"cloud_forge_profile_update"})


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _file_digest(path: Path) -> str:
    if not path.exists():
        return ""
    return sha256(path.read_bytes()).hexdigest()


def _tenant_overlay_path(tenant_id: str) -> Path:
    slug = tenant_path_slug(normalize_tenant_id(tenant_id))
    return GOVERNANCE_DEPLOY_ROOT / "tenants" / slug / "provider-organs.json"


def is_governance_mission(request: dict[str, Any]) -> bool:
    return str(request.get("mission_kind") or "").strip() == "governance_mutation"


def run_governance_mission(
    request: dict[str, Any],
    *,
    runtime: Any,
) -> dict[str, Any]:
    """Execute authorized governance mutation; returns mission response with receipt."""
    payload = dict(request or {})
    target = str(payload.get("mutation_target") or "").strip()
    mutation_op = str(payload.get("mutation_op") or "").strip().lower()
    operator_id = str(payload.get("operator_id") or "").strip()

    mutation_check = check_cloud_mutation(
        {
            "mission_kind": "governance_mutation",
            "mutation_target": target,
            "operator_id": operator_id,
            "governance_authority": payload.get("governance_authority"),
        }
    )
    if has_hard_fail(mutation_check):
        from src.ugr.mission.mission_runtime import URG_MISSION_RUNTIME_ID, URG_MISSION_RUNTIME_VERSION

        return {
            "runtime_id": URG_MISSION_RUNTIME_ID,
            "runtime_version": URG_MISSION_RUNTIME_VERSION,
            "status": "rejected",
            "summary": mutation_check[0].get("details", "governance not authorized"),
            "cloud_invariants": {"governance_open": mutation_check},
        }

    ingress_law = runtime.ingress_law if hasattr(runtime, "ingress_law") else UrgIngressLaw()
    ingress = ingress_law.stamp_mission(payload)
    ok, reason = ingress_law.validate_stamp(ingress)
    if not ok:
        return {
            "status": "rejected",
            "summary": reason,
            "urg_ingress": ingress,
        }

    runtime_dir = getattr(runtime, "runtime_dir", None)
    tenant_manifold, tenant_results = validate_tenant_for_mission(
        payload, runtime_dir=runtime_dir
    )
    if tenant_manifold is None:
        from src.ugr.mission.mission_runtime import URG_MISSION_RUNTIME_ID, URG_MISSION_RUNTIME_VERSION

        return {
            "runtime_id": URG_MISSION_RUNTIME_ID,
            "runtime_version": URG_MISSION_RUNTIME_VERSION,
            "status": "rejected",
            "summary": tenant_results[0].get("details", "tenant rejected"),
            "urg_ingress": ingress,
        }

    if hasattr(runtime, "_bind_tenant"):
        runtime._bind_tenant(tenant_manifold.tenant_id)
    ingress = dict(ingress)
    ingress.update(tenant_manifold.to_dict())

    mission_id = ingress["mission_id"]
    ledger = runtime.ledger if hasattr(runtime, "ledger") else MissionLedger(
        runtime_dir=runtime_dir,
        tenant_id=tenant_manifold.tenant_id,
    )
    organs = ProviderOrganRegistry(tenant_id=tenant_manifold.tenant_id)
    manifold = build_cloud_manifold(
        request=payload,
        ingress=ingress,
        organ_ids=organs.admitted_organ_ids(),
        rail="NORMAL",
        organ_registry=organs,
    )
    ingress.update(manifold.to_dict())

    path = MUTATION_PATHS.get(target)
    if path is None and target != "provider_organs":
        return {
            "status": "rejected",
            "summary": f"unknown mutation_target {target}",
            "mission_id": mission_id,
        }

    if target == "tenant_config" and mutation_op in CLOUD_FORGE_PROFILE_OPS:
        from src.ugr.platform.tenant_config import apply_cloud_forge_profile_update

        tenants_path = TenantRegistry().path
        before_digest = _file_digest(tenants_path)
        after_digest = before_digest
        apply_note = "audit_only"
        profile = dict(payload.get("cloud_forge") or {})
        if os.getenv("URG_GOVERNANCE_APPLY", "").strip().lower() in {"1", "true", "yes", "on"}:
            ok_apply, msg, after_digest = apply_cloud_forge_profile_update(
                tenant_manifold.tenant_id,
                profile,
            )
            apply_note = msg if ok_apply else f"apply_failed: {msg}"
            if not ok_apply:
                return {
                    "status": "blocked",
                    "summary": msg,
                    "mission_id": mission_id,
                }
    elif target == "provider_organs" and mutation_op in MARKETPLACE_OPS:
        overlay_path = _tenant_overlay_path(tenant_manifold.tenant_id)
        before_digest = _file_digest(overlay_path) or _file_digest(GOVERNANCE_DEPLOY_ROOT / "provider-organs.json")
        apply_note = "audit_only"
        after_digest = before_digest
        peer_tenant = str(payload.get("federation_peer_tenant") or "").strip()
        federation_grant_id = str(payload.get("federation_grant_id") or "").strip()
        if mutation_op in FEDERATION_GOVERNANCE_OPS:
            from src.ugr.mission.federation_grants import (
                CAP_GOVERNANCE_COSIGN,
                FederationGrantStore,
            )

            peer_norm = normalize_tenant_id(peer_tenant)
            store = FederationGrantStore(runtime_dir)
            _grant, grant_err = store.verify_step_capability(
                home_tenant=tenant_manifold.tenant_id,
                peer_tenant=peer_tenant,
                grant_id=federation_grant_id,
                capability=CAP_GOVERNANCE_COSIGN,
            )
            if grant_err:
                return {
                    "status": "blocked",
                    "summary": grant_err,
                    "mission_id": mission_id,
                }
            base_op = "organ_admit" if mutation_op == "federation_organ_admit" else "organ_suspend"
            if mutation_op != "organ_query":
                ok_apply, msg, after_digest = apply_provider_organ_mutation(
                    tenant_id=tenant_manifold.tenant_id,
                    mutation_op=base_op,
                    organ_spec=dict(payload.get("organ_spec") or {}),
                    organ_id=str(payload.get("organ_id") or ""),
                )
                apply_note = msg if ok_apply else f"apply_failed: {msg}"
                if ok_apply and peer_tenant:
                    ok_peer, msg_peer, _ = apply_provider_organ_mutation(
                        tenant_id=peer_norm,
                        mutation_op=base_op,
                        organ_spec=dict(payload.get("organ_spec") or {}),
                        organ_id=str(payload.get("organ_id") or ""),
                    )
                    apply_note = f"{apply_note}; peer: {msg_peer if ok_peer else msg_peer}"
                if mutation_op in FEDERATION_GOVERNANCE_OPS and ok_apply:
                    from src.ugr.mission.step_execution import (
                        append_federation_governance_inbound_ledger,
                        append_federation_governance_ledger,
                    )

                    peer_ledger = MissionLedger(runtime_dir=runtime_dir, tenant_id=peer_norm)
                    fed_action = f"{mission_id}:governance-federation:1"
                    append_federation_governance_ledger(
                        ledger,
                        mission_id=mission_id,
                        action_id=fed_action,
                        mutation_op=mutation_op,
                        federation_grant_id=federation_grant_id,
                        federation_peer_tenant=peer_norm,
                        home_tenant_id=tenant_manifold.tenant_id,
                        extra={"mutation_digest_after": after_digest},
                    )
                    append_federation_governance_inbound_ledger(
                        peer_ledger,
                        home_mission_id=mission_id,
                        home_tenant_id=tenant_manifold.tenant_id,
                        grant_id=federation_grant_id,
                        mutation_op=mutation_op,
                        peer_tenant_id=peer_norm,
                        extra={"mutation_digest_after": after_digest},
                    )
                if not ok_apply and os.getenv("URG_GOVERNANCE_APPLY", "").strip().lower() in {"1", "true", "yes", "on"}:
                    return {
                        "status": "blocked",
                        "summary": msg,
                        "mission_id": mission_id,
                    }
        elif mutation_op != "organ_query":
            ok_apply, msg, after_digest = apply_provider_organ_mutation(
                tenant_id=tenant_manifold.tenant_id,
                mutation_op=mutation_op,
                organ_spec=dict(payload.get("organ_spec") or {}),
                organ_id=str(payload.get("organ_id") or ""),
            )
            apply_note = msg if ok_apply else f"apply_failed: {msg}"
            if not ok_apply and os.getenv("URG_GOVERNANCE_APPLY", "").strip().lower() in {"1", "true", "yes", "on"}:
                return {
                    "status": "blocked",
                    "summary": msg,
                    "mission_id": mission_id,
                }
    else:
        path = path or MUTATION_PATHS["provider_organs"]
        before_digest = _file_digest(path)
        after_digest = before_digest
        apply_note = "governance_mutation audit (whole-file target)"

    action_id = f"{mission_id}:governance-mutation:1"
    ledger.append_governance_mutation(
        {
            "type": "governance_mutation",
            "mission_id": mission_id,
            "action_id": action_id,
            "mutation_target": target,
            "mutation_op": mutation_op or None,
            "mutation_digest_before": before_digest,
            "mutation_digest_after": after_digest,
            "operator_id": operator_id,
            "tenant_id": tenant_manifold.tenant_id,
            "status": "recorded",
            "note": apply_note,
        }
    )

    steps = [
        {
            "step_id": "governance-mutation",
            "status": "ok",
            "action_id": action_id,
            "invariant_results": mutation_check,
        }
    ]
    assignment = {
        "phase": "assign",
        "assignments": [],
        "participating_organs": [],
        "auto_assign_meta": [],
    }
    decomposition = decompose_mission({"steps": steps, **payload})
    payload = dict(payload)
    payload["mission_kind"] = "governance_mutation"
    payload["mutation_target"] = target
    payload.setdefault("intent", "governance_mutation")
    payload.setdefault("aais_instance_id", "aais-primary")
    payload["tenant_id"] = tenant_manifold.tenant_id

    from src.ugr.mission.mission_runtime import URG_MISSION_RUNTIME_ID, URG_MISSION_RUNTIME_VERSION

    response = {
        "runtime_id": URG_MISSION_RUNTIME_ID,
        "runtime_version": URG_MISSION_RUNTIME_VERSION,
        "mission_id": mission_id,
        "status": "ok",
        "summary": f"governance {mutation_op or 'mutation'} recorded for {target}",
        "urg_ingress": ingress,
        "cloud_invariants": {"governance_open": mutation_check},
        "steps": steps,
        "ledger_refs": [action_id],
        "governance": {
            "mutation_target": target,
            "mutation_op": mutation_op,
            "mutation_digest_before": before_digest,
            "mutation_digest_after": after_digest,
        },
    }
    ledger_rows = ledger.list_for_mission(mission_id)
    return attach_gcm_to_response(
        response,
        request=payload,
        ingress=ingress,
        decomposition=decomposition,
        assignment=assignment,
        mission_open=mutation_check,
        ledger_rows=ledger_rows,
    )
