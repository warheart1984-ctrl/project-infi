"""Cloud invariant checks for URG super-cloud missions."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.ugr.invariants.cloud_manifold import (
    CLOUD_INVARIANT_SET_VERSION,
    CloudManifoldState,
    MissionCloudState,
    compute_cloud_identity_hash,
)
from src.ugr.mission.provider_organ import ProviderOrgan, ProviderOrganRegistry
from src.ugr.platform.tenant_registry import normalize_tenant_id


RISK_ORDER = {"low": 0, "medium": 1, "high": 2}

GOVERNANCE_MUTATION_TARGETS = frozenset(
    {"provider_organs", "regions", "aais_instances", "invariant_definitions"}
)


class CloudCausalityFault(RuntimeError):
    """Ledger or step causality violation (fail-closed)."""


def _regions_path() -> Path:
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "regions.json"


def _load_regions() -> dict[str, Any]:
    path = _regions_path()
    if not path.exists():
        return {}
    return dict(json.loads(path.read_text(encoding="utf-8")).get("regions") or {})


def _invariant(name: str, status: str, details: str = "") -> dict[str, Any]:
    return {"family": name, "status": status, "details": details}


def has_hard_fail(results: list[dict[str, Any]]) -> bool:
    return any(item.get("status") == "hard_fail" for item in results)


def check_cloud_identity(
    mission_state: dict[str, Any],
    *,
    manifold: CloudManifoldState | None = None,
    authorized_rebind: bool = False,
) -> list[dict[str, Any]]:
    """Verify I_cloud unchanged across mission lifecycle."""
    results: list[dict[str, Any]] = []
    request = dict(mission_state.get("request") or {})
    ingress = dict(mission_state.get("ingress") or {})
    frozen = manifold or CloudManifoldState.from_dict(mission_state.get("cloud_manifold") or {})

    operator_id = str(request.get("operator_id") or ingress.get("operator_id") or "").strip()
    aais_id = str(request.get("aais_instance_id") or ingress.get("aais_instance_id") or "").strip()
    if not operator_id or not aais_id:
        results.append(_invariant("cloud_identity", "hard_fail", "operator_id and aais_instance_id required"))
        return results

    organ_ids = list(frozen.organ_ids or mission_state.get("organ_ids") or [])
    if not organ_ids and frozen.cloud_identity_hash:
        organ_ids = list((mission_state.get("ingress") or {}).get("organ_ids") or [])
    current = compute_cloud_identity_hash(
        tenant_id=str(request.get("tenant_id") or ingress.get("tenant_id") or "default"),
        operator_id=operator_id,
        mission_id=str(ingress.get("mission_id") or ""),
        organ_ids=organ_ids,
        region_ids=[str(request.get("region_id") or frozen.region_id or "")],
        aais_instance_id=aais_id,
    )
    if frozen.cloud_identity_hash and not authorized_rebind and current != frozen.cloud_identity_hash:
        results.append(
            _invariant(
                "cloud_identity",
                "hard_fail",
                f"I_cloud mismatch: expected {frozen.cloud_identity_hash[:16]} got {current[:16]}",
            )
        )
    else:
        results.append(_invariant("cloud_identity", "pass", f"hash={current[:16]}"))
    return results


def check_cloud_boundary(
    mission_state: dict[str, Any],
    step_assignment: dict[str, Any],
    *,
    manifold: CloudManifoldState | None = None,
) -> list[dict[str, Any]]:
    """Verify step assignment lies inside B_cloud(M)."""
    results: list[dict[str, Any]] = []
    frozen = manifold or CloudManifoldState.from_dict(mission_state.get("cloud_manifold") or {})
    allowed = frozen.boundary_tuples()
    region_id = str(mission_state.get("region_id") or frozen.region_id or "").strip()
    provider = str(step_assignment.get("provider") or "").strip()
    rail = str(step_assignment.get("rail") or frozen.rail or "NORMAL").upper()
    organ_id = str(step_assignment.get("organ_id") or "").strip()

    if not organ_id:
        results.append(_invariant("cloud_boundary", "hard_fail", "no organ assigned"))
        return results

    key = (region_id, provider, rail)
    if allowed and key not in allowed:
        results.append(_invariant("cloud_boundary", "hard_fail", f"({region_id},{provider},{rail}) not in B_cloud"))
    else:
        results.append(_invariant("cloud_boundary", "pass", f"organ={organ_id} in B_cloud"))
    return results


def check_cloud_continuity(
    prev_state: dict[str, Any] | MissionCloudState | None,
    next_state: dict[str, Any] | MissionCloudState,
) -> list[dict[str, Any]]:
    """ValidCloudTransition continuity checks."""
    results: list[dict[str, Any]] = []
    prev = prev_state.to_dict() if isinstance(prev_state, MissionCloudState) else dict(prev_state or {})
    nxt = next_state.to_dict() if isinstance(next_state, MissionCloudState) else dict(next_state)

    if str(prev.get("mission_id") or "") and prev.get("mission_id") != nxt.get("mission_id"):
        results.append(_invariant("cloud_continuity", "hard_fail", "mission_id changed"))
        return results

    prev_steps = set(prev.get("step_ids_seen") or [])
    nxt_steps = list(nxt.get("step_ids_seen") or [])
    if nxt.get("status") == "step_append" and nxt_steps:
        new_step = nxt_steps[-1]
        if new_step in prev_steps:
            results.append(_invariant("cloud_continuity", "hard_fail", f"duplicate step_id {new_step}"))
            return results

    if str(prev.get("cloud_identity_hash") or "") and prev.get("cloud_identity_hash") != nxt.get("cloud_identity_hash"):
        results.append(_invariant("cloud_continuity", "hard_fail", "identity hash drift without rebind"))

    results.append(_invariant("cloud_continuity", "pass", str(nxt.get("mission_id") or "")))
    return results


def check_cloud_causality(
    mission_ledger: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    *,
    mission_id: str,
) -> list[dict[str, Any]]:
    """Every ok step has exactly one ledger entry; unique step_ids."""
    results: list[dict[str, Any]] = []
    ledger_by_action = {
        str(r.get("action_id") or ""): r
        for r in mission_ledger
        if str(r.get("type") or "") == "urg_mission_action"
    }
    seen_step_ids: set[str] = set()

    for step in steps:
        step_id = str(step.get("step_id") or "").strip()
        if not step_id:
            results.append(_invariant("cloud_causality", "hard_fail", "missing step_id"))
            continue
        if step_id in seen_step_ids:
            results.append(_invariant("cloud_causality", "hard_fail", f"duplicate step_id {step_id}"))
            return results
        seen_step_ids.add(step_id)

        if step.get("status") != "ok":
            continue
        action_id = str(step.get("action_id") or "")
        if not action_id.startswith(mission_id):
            results.append(_invariant("cloud_causality", "hard_fail", f"action_id {action_id} invalid"))
            return results
        if action_id not in ledger_by_action:
            results.append(_invariant("cloud_causality", "hard_fail", f"missing ledger entry for {action_id}"))
            return results

    results.append(_invariant("cloud_causality", "pass", f"steps={len(seen_step_ids)} ledger={len(mission_ledger)}"))
    return results


def _governance_allowlist() -> set[str]:
    raw = os.getenv("URG_GOVERNANCE_OPERATOR_ALLOWLIST", "").strip()
    if not raw:
        return set()
    return {item.strip() for item in raw.split(",") if item.strip()}


def check_cloud_mutation(governance_change: dict[str, Any]) -> list[dict[str, Any]]:
    """URG governance mutations only via authorized governance missions."""
    results: list[dict[str, Any]] = []
    target = str(governance_change.get("mutation_target") or "").strip()
    operator_id = str(governance_change.get("operator_id") or "").strip()
    mission_kind = str(governance_change.get("mission_kind") or "").strip()

    if mission_kind != "governance_mutation":
        results.append(
            _invariant("cloud_mutation", "hard_fail", "governance changes require mission_kind=governance_mutation")
        )
        return results

    if target not in GOVERNANCE_MUTATION_TARGETS:
        results.append(_invariant("cloud_mutation", "hard_fail", f"unsupported mutation_target {target!r}"))
        return results

    allowlist = _governance_allowlist()
    token = str(governance_change.get("governance_authority") or "").strip()
    env_token = os.getenv("URG_GOVERNANCE_AUTHORITY_TOKEN", "").strip()
    authorized = operator_id in allowlist or (token and env_token and token == env_token)
    if not authorized:
        results.append(_invariant("cloud_mutation", "hard_fail", "operator not in governance allowlist"))
        return results

    results.append(_invariant("cloud_mutation", "pass", f"governance mutation {target}"))
    return results


def valid_cloud_transition(
    prev_state: dict[str, Any] | MissionCloudState | None,
    next_state: dict[str, Any] | MissionCloudState,
    *,
    mission_state: dict[str, Any] | None = None,
    authorized_rebind: bool = False,
) -> tuple[bool, str]:
    """Composite transition gate."""
    continuity = check_cloud_continuity(prev_state, next_state)
    if has_hard_fail(continuity):
        return False, continuity[0].get("details", "continuity_fail")

    if mission_state:
        identity = check_cloud_identity(mission_state, authorized_rebind=authorized_rebind)
        if has_hard_fail(identity):
            return False, identity[0].get("details", "identity_fail")

    prev = prev_state.to_dict() if isinstance(prev_state, MissionCloudState) else dict(prev_state or {})
    nxt = next_state.to_dict() if isinstance(next_state, MissionCloudState) else dict(next_state)
    if prev.get("boundary_digest") and prev.get("boundary_digest") != nxt.get("boundary_digest"):
        return False, "boundary_digest_changed"

    return True, "ok"


class CloudInvariantEvaluator:
    """Evaluate six cloud invariant families for a mission or step."""

    def __init__(
        self,
        *,
        organ_registry: ProviderOrganRegistry | None = None,
    ):
        self.organs = organ_registry or ProviderOrganRegistry()
        self._regions = _load_regions()

    def evaluate_mission_open(
        self,
        request: dict[str, Any],
        *,
        ingress: dict[str, Any],
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        operator_id = str(request.get("operator_id") or "").strip()
        aais_id = str(request.get("aais_instance_id") or "").strip()
        tenant_id = normalize_tenant_id(request.get("tenant_id"))

        if not operator_id or not aais_id:
            results.append(_invariant("cloud_identity", "hard_fail", "operator_id and aais_instance_id required"))
        else:
            results.append(_invariant("cloud_identity", "pass", f"tenant={tenant_id} operator={operator_id}"))

        region_id = str(request.get("region_id") or "").strip()
        constraints = dict(request.get("constraints") or {})
        required_region = str(constraints.get("required_region") or "").strip()
        if region_id not in self._regions:
            results.append(_invariant("cloud_boundary", "hard_fail", f"unknown region {region_id!r}"))
        elif required_region and region_id != required_region:
            results.append(
                _invariant("cloud_boundary", "hard_fail", f"region {region_id} != required {required_region}")
            )
        else:
            results.append(_invariant("cloud_boundary", "pass", f"region={region_id}"))

        mission_id = str(ingress.get("mission_id") or "").strip()
        if not mission_id:
            results.append(_invariant("cloud_continuity", "hard_fail", "missing mission_id"))
        else:
            results.append(_invariant("cloud_continuity", "pass", mission_id))

        results.append(_invariant("cloud_causality", "pass", "action_ids assigned per step"))
        results.append(_invariant("cloud_mutation", "pass", "no governance mutation at open"))
        results.append(_invariant("cloud_composite", "pass", "pending step execution"))
        return results

    def evaluate_step(
        self,
        *,
        request: dict[str, Any],
        ingress: dict[str, Any],
        step: dict[str, Any],
        organ: ProviderOrgan,
        action_id: str,
        prior_action_id: str | None,
        cost_spent: float,
        rail: str = "NORMAL",
        manifold: CloudManifoldState | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        region_id = str(request.get("region_id") or "").strip()
        intent = str(request.get("intent") or "general_qa").strip().lower()
        from src.ugr.mission.cost_routing import resolve_mission_budget

        constraints = dict(request.get("constraints") or {})
        budget = resolve_mission_budget({"constraints": constraints})
        max_total = budget.hard_ceil
        risk_ceiling = str(constraints.get("risk_ceiling") or "high").lower()

        mission_state = {
            "request": request,
            "ingress": ingress,
            "region_id": region_id,
            "cloud_manifold": (manifold or CloudManifoldState.from_dict(ingress)).to_dict()
            if ingress.get("cloud_identity_hash")
            else {},
        }
        if manifold:
            mission_state["cloud_manifold"] = manifold.to_dict()

        admitted = set(self.organs.admitted_organ_ids())
        if organ.organ_id not in admitted:
            results.append(_invariant("cloud_identity", "hard_fail", f"organ {organ.organ_id} not admitted"))
        else:
            results.append(_invariant("cloud_identity", "pass", organ.organ_id))

        boundary_results = check_cloud_boundary(
            mission_state,
            {"organ_id": organ.organ_id, "provider": organ.provider, "rail": rail},
            manifold=manifold,
        )
        results.extend(boundary_results)

        allowed_regions = list(organ.contract.get("allowed_regions") or [])
        if region_id not in allowed_regions:
            if not any(r.get("family") == "cloud_boundary" and r.get("status") == "hard_fail" for r in results):
                results.append(
                    _invariant("cloud_boundary", "hard_fail", f"organ denies region {region_id}")
                )
        else:
            admissible_rails = [str(r).upper() for r in (organ.contract.get("admissible_rails") or [])]
            rail_upper = str(rail or "NORMAL").upper()
            if admissible_rails and rail_upper not in admissible_rails:
                if not any(r.get("family") == "cloud_boundary" and r.get("status") == "hard_fail" for r in results):
                    results.append(
                        _invariant("cloud_boundary", "hard_fail", f"rail {rail_upper} not in {admissible_rails}")
                    )

        step_id = str(step.get("step_id") or "").strip()
        mission_id = str(ingress.get("mission_id") or "").strip()
        if not step_id or not action_id.startswith(mission_id):
            results.append(_invariant("cloud_continuity", "hard_fail", "step/mission id mismatch"))
        else:
            results.append(_invariant("cloud_continuity", "pass", step_id))

        if prior_action_id:
            results.append(_invariant("cloud_causality", "pass", f"prior={prior_action_id}"))
        else:
            results.append(_invariant("cloud_causality", "pass", "root_action"))

        allowed_domains = [str(d).lower() for d in (organ.contract.get("allowed_domains") or [])]
        organ_risk = str(organ.contract.get("risk_ceiling") or "high").lower()
        step_cost = organ.max_cost_units
        if intent not in allowed_domains:
            results.append(_invariant("cloud_contract", "hard_fail", f"intent {intent} not in {allowed_domains}"))
        elif RISK_ORDER.get(organ_risk, 2) > RISK_ORDER.get(risk_ceiling, 2):
            results.append(
                _invariant("cloud_contract", "hard_fail", f"organ risk {organ_risk} > ceiling {risk_ceiling}")
            )
        elif cost_spent + step_cost > max_total:
            results.append(
                _invariant(
                    "cloud_contract",
                    "hard_fail",
                    f"cost budget exceeded ({cost_spent + step_cost} > {max_total})",
                )
            )
            results.append(_invariant("cloud_budget", "hard_fail", "mission hard_ceil exceeded"))
        else:
            results.append(_invariant("cloud_contract", "pass", f"cost_delta={step_cost}"))
            results.append(_invariant("cloud_budget", "pass", f"remaining={max_total - cost_spent - step_cost:.2f}"))

        results.append(_invariant("cloud_composite", "pass", action_id))
        return results

    @staticmethod
    def has_hard_fail(results: list[dict[str, Any]]) -> bool:
        return has_hard_fail(results)
