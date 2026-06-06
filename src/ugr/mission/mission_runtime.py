"""URG mission runtime — Governed Composite Mission v1.2."""

# Mythic: Mission Runtime
# Engineering: MissionRuntimeEngine
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.cognitive_bridge import DECISION_BLOCK, CognitiveBridgeService
from src.ugr.cloud_forge_bridge import schedule_rail_for_ugr
from src.ugr.mission.aais_instance_registry import AaisInstanceRegistry
from src.ugr.mission.aais_step_bridge import (
    bootstrap_mission_aais,
    mission_step_bridge_enabled,
    run_mission_step_deliberation,
)
from src.ugr.invariants.cloud_invariants import (
    CloudCausalityFault,
    CloudInvariantEvaluator,
    check_cloud_causality,
    check_cloud_identity,
    valid_cloud_transition,
)
from src.ugr.invariants.cloud_manifold import (
    CloudManifoldState,
    MissionCloudState,
    build_cloud_manifold,
)
from src.ugr.mission.governance_mission import is_governance_mission, run_governance_mission
from src.ugr.mission.composite_mission import (
    assign_organs,
    attach_gcm_to_response,
    decompose_mission,
)
from src.ugr.mission.ingress import UrgIngressLaw
from src.ugr.mission.mission_ledger import MissionLedger
from src.ugr.mission.organ_matcher import apply_auto_assignments_to_steps
from src.ugr.mission.provider_organ import ProviderOrgan, ProviderOrganRegistry
from src.ugr.unified_runtime import UnifiedGovernedRuntime


URG_MISSION_RUNTIME_ID = "aais.urg.mission_runtime"
URG_MISSION_RUNTIME_VERSION = "1.9"


def _runtime_dir(explicit: str | Path | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / ".runtime"


class UGRMissionRuntime:
    """Mission-level switchboard: GCM with AAIS bridge, auto-assign, HMAC receipt."""

    def __init__(
        self,
        *,
        ingress: UrgIngressLaw | None = None,
        organs: ProviderOrganRegistry | None = None,
        invariants: CloudInvariantEvaluator | None = None,
        ledger: MissionLedger | None = None,
        bridge: CognitiveBridgeService | None = None,
        ugr_runtime: UnifiedGovernedRuntime | None = None,
        runtime_dir: str | Path | None = None,
        aais_registry: AaisInstanceRegistry | None = None,
    ):
        self.runtime_dir = _runtime_dir(runtime_dir)
        self.ingress_law = ingress or UrgIngressLaw()
        self.organs = organs or ProviderOrganRegistry()
        self.invariants = invariants or CloudInvariantEvaluator(organ_registry=self.organs)
        self.ledger = ledger or MissionLedger(runtime_dir=self.runtime_dir)
        self._bridge = bridge
        self._ugr_runtime = ugr_runtime
        self.aais_registry = aais_registry or AaisInstanceRegistry()
        self._tenant_id: str | None = None
        self._federation_context: list[dict[str, Any]] = []

    def _bind_tenant(self, tenant_id: str) -> None:
        """Scope ledger, organs, and invariants to one tenant partition."""
        from src.ugr.platform.tenant_registry import normalize_tenant_id

        self._tenant_id = normalize_tenant_id(tenant_id)
        self.organs = ProviderOrganRegistry(tenant_id=self._tenant_id)
        self.invariants = CloudInvariantEvaluator(organ_registry=self.organs)
        self.ledger = MissionLedger(runtime_dir=self.runtime_dir, tenant_id=self._tenant_id)

    def _ensure_aais(
        self,
        instance_id: str | None = None,
    ) -> tuple[CognitiveBridgeService, UnifiedGovernedRuntime]:
        iid = str(instance_id or "").strip()
        if iid and iid in self.aais_registry.list_instance_ids():
            return self.aais_registry.get_bridge_pair(iid)
        if self._bridge is not None and self._ugr_runtime is not None:
            return self._bridge, self._ugr_runtime
        bridge, ugr = bootstrap_mission_aais(self.runtime_dir)
        self._bridge = self._bridge or bridge
        self._ugr_runtime = self._ugr_runtime or ugr
        return self._bridge, self._ugr_runtime

    @staticmethod
    def _step_aais_instance_id(step: dict[str, Any], ingress: dict[str, Any], request: dict[str, Any]) -> str:
        return (
            str(step.get("aais_instance_id") or "").strip()
            or str(ingress.get("aais_instance_id") or "").strip()
            or str(request.get("aais_instance_id") or "").strip()
            or "aais-primary"
        )

    @staticmethod
    def _build_block_context(
        *,
        summary: str,
        invariant_results: list[dict[str, Any]] | None = None,
        assignment: dict[str, Any] | None = None,
        step_id: str | None = None,
        match_reason: str | None = None,
    ) -> dict[str, Any]:
        ctx: dict[str, Any] = {"summary": summary}
        if invariant_results:
            ctx["invariant_results"] = list(invariant_results)
        if assignment:
            ctx["auto_assign_meta"] = list(assignment.get("auto_assign_meta") or [])
            if step_id:
                for item in assignment.get("assignments") or []:
                    if str(item.get("step_id") or "") == step_id:
                        ctx["match_reason"] = str(item.get("match_reason") or "")
                        break
        if match_reason:
            ctx["match_reason"] = match_reason
        return ctx

    def run_mission(self, request: dict[str, Any] | None) -> dict[str, Any]:
        payload = dict(request or {})
        if is_governance_mission(payload):
            return run_governance_mission(payload, runtime=self)

        from src.ugr.mission.execution_policy import (
            operator_abort_requested,
            reject_new_mission,
            resolve_execution_mode,
            should_force_provider_execute,
        )

        rejected, reject_reason = reject_new_mission(request=payload)
        if rejected:
            return {
                "runtime_id": URG_MISSION_RUNTIME_ID,
                "runtime_version": URG_MISSION_RUNTIME_VERSION,
                "status": "rejected",
                "summary": reject_reason,
                **self.ingress_law.reject_bypass(reason="mission_kill_switch"),
            }

        execution_mode = resolve_execution_mode(payload)

        steps = list(payload.get("steps") or [])
        if not steps:
            return {
                "runtime_id": URG_MISSION_RUNTIME_ID,
                "runtime_version": URG_MISSION_RUNTIME_VERSION,
                "status": "rejected",
                "summary": "mission requires at least one step",
                **self.ingress_law.reject_bypass(reason="empty_mission"),
            }

        ingress = self.ingress_law.stamp_mission(payload)
        ok, reason = self.ingress_law.validate_stamp(ingress)
        if not ok:
            return {
                "runtime_id": URG_MISSION_RUNTIME_ID,
                "runtime_version": URG_MISSION_RUNTIME_VERSION,
                "status": "rejected",
                "summary": reason,
                "urg_ingress": ingress,
            }

        from src.ugr.mission.mission_receipt import FAILURE_REASON_GATE_REJECTION
        from src.ugr.mission.tenant_manifold import validate_tenant_for_mission

        self._federation_context = []
        tenant_manifold, tenant_results = validate_tenant_for_mission(
            payload, runtime_dir=self.runtime_dir
        )
        if tenant_manifold is None:
            return {
                "runtime_id": URG_MISSION_RUNTIME_ID,
                "runtime_version": URG_MISSION_RUNTIME_VERSION,
                "status": "rejected",
                "summary": tenant_results[0].get("details", "tenant rejected"),
                "urg_ingress": ingress,
                "cloud_invariants": {"tenant_open": tenant_results},
                "failure_reason": FAILURE_REASON_GATE_REJECTION,
            }

        self._bind_tenant(tenant_manifold.tenant_id)
        payload = dict(payload)
        payload["tenant_id"] = tenant_manifold.tenant_id

        mission_id = ingress["mission_id"]
        ingress = dict(ingress)
        ingress.update(tenant_manifold.to_dict())
        provisional_manifold = build_cloud_manifold(
            request=payload,
            ingress=ingress,
            organ_ids=self.organs.admitted_organ_ids(),
            rail="NORMAL",
            organ_registry=self.organs,
        )
        ingress.update(provisional_manifold.to_dict())

        decomposition = decompose_mission(payload)
        open_results = self.invariants.evaluate_mission_open(payload, ingress=ingress)
        if self.invariants.has_hard_fail(open_results):
            return self._blocked(
                mission_id,
                ingress,
                open_results,
                summary="mission blocked at open: cloud invariants failed",
                steps=[],
                request=payload,
                decomposition=decomposition,
                assignment={"phase": "assign", "assignments": [], "participating_organs": []},
                block_context=self._build_block_context(
                    summary="mission blocked at open: cloud invariants failed",
                    invariant_results=open_results,
                ),
            )

        halt_on_failure = bool(payload.get("halt_on_failure", True))
        intent = str(payload.get("intent") or "governed_super_router_demo").strip().lower()
        use_aais_bridge = mission_step_bridge_enabled(payload)
        seen_step_ids: set[str] = set()
        step_outcomes: list[dict[str, Any]] = []
        ledger_refs: list[str] = []
        from src.ugr.mission.cost_routing import (
            BudgetLedger,
            compute_budget_digest,
            estimate_step_cost,
            resolve_mission_budget,
        )

        mission_budget = resolve_mission_budget(payload, tenant_manifold=tenant_manifold)
        budget_ledger = BudgetLedger(mission_budget)
        ingress["budget_digest"] = compute_budget_digest(mission_budget)
        cost_spent = 0.0
        prior_action_id: str | None = None
        prior_step_summary: str | None = None

        context = dict(payload.get("context") or {})
        constraints = dict(payload.get("constraints") or {})
        if str(constraints.get("risk_ceiling") or "").lower() in {"low", "medium"}:
            context.setdefault("forbid_express", True)
        cloud_forge = schedule_rail_for_ugr(
            {
                "question": str(payload.get("objective") or "")[:500],
                "intent": intent,
                "tenant_id": payload.get("tenant_id"),
                "context": context,
            },
            trace_id=mission_id,
            bridge_result={"decision": "ALLOW", "execution_allowed": True},
        )
        rail_decision = dict((cloud_forge or {}).get("rail_decision") or {})
        rail = str(rail_decision.get("rail") or "NORMAL")
        if rail == "EXPRESS" and context.get("forbid_express"):
            rail = "NORMAL"
        explicit_rail = str(
            payload.get("rail") or constraints.get("rail") or constraints.get("required_rail") or ""
        ).strip().upper()
        if explicit_rail in {"SAFE", "NORMAL", "EXPRESS"}:
            rail = explicit_rail

        manifold = build_cloud_manifold(
            request=payload,
            ingress=ingress,
            organ_ids=self.organs.admitted_organ_ids(),
            rail=rail,
            organ_registry=self.organs,
        )
        ingress = dict(ingress)
        ingress.update(manifold.to_dict())
        cloud_state = MissionCloudState(
            mission_id=mission_id,
            cloud_identity_hash=manifold.cloud_identity_hash,
            boundary_digest=manifold.boundary_digest,
        )
        boundary_tuples = manifold.boundary_tuples()

        from src.ugr.mission.step_execution import append_mission_ingress_ledger, append_organ_assignment_ledger

        append_mission_ingress_ledger(
            self.ledger,
            mission_id=mission_id,
            ingress=ingress,
            cloud_manifold=manifold.to_dict(),
        )

        updated_steps, auto_meta = apply_auto_assignments_to_steps(
            payload,
            decomposition,
            organ_registry=self.organs,
            rail=rail,
            cost_spent=0.0,
            boundary_tuples=boundary_tuples,
            mission_budget=mission_budget,
            tenant_manifold=tenant_manifold,
        )
        payload = dict(payload)
        payload["steps"] = updated_steps
        decomposition = decompose_mission(payload)
        assignment = assign_organs(
            decomposition,
            organ_registry=self.organs,
            auto_assign_meta=auto_meta,
        )

        for ordinal, step in enumerate(updated_steps, start=1):
            step = dict(step)
            step_id = str(step.get("step_id") or f"step-{ordinal}").strip()
            if step_id in seen_step_ids:
                return self._blocked(
                    mission_id,
                    ingress,
                    [_fail("cloud_continuity", f"duplicate step_id {step_id}")],
                    summary="duplicate step_id",
                    steps=step_outcomes,
                    request=payload,
                    decomposition=decomposition,
                    assignment=assignment,
                    block_context=self._build_block_context(
                        summary="duplicate step_id",
                        invariant_results=[_fail("cloud_continuity", f"duplicate step_id {step_id}")],
                    ),
                )
            seen_step_ids.add(step_id)

            organ_id = str(step.get("organ_id") or "").strip()
            peer_tenant_raw = str(step.get("federation_peer_tenant") or "").strip()
            federation_grant_id = str(step.get("federation_grant_id") or "").strip()
            step_organ_registry = self.organs
            federation_peer_tenant: str | None = None
            if peer_tenant_raw:
                from src.ugr.mission.federation_grants import (
                    CAP_ROUTE_STEP,
                    FederationGrantStore,
                )
                from src.ugr.platform.tenant_registry import normalize_tenant_id

                store = FederationGrantStore(self.runtime_dir)
                grant, grant_err = store.verify_step_capability(
                    home_tenant=tenant_manifold.tenant_id,
                    peer_tenant=peer_tenant_raw,
                    grant_id=federation_grant_id,
                    capability=CAP_ROUTE_STEP,
                )
                if grant_err:
                    outcome = self._step_blocked(
                        mission_id,
                        step_id,
                        ordinal,
                        organ_id,
                        prior_action_id,
                        reason=grant_err,
                    )
                    step_outcomes.append(outcome)
                    if halt_on_failure:
                        return self._finalize(
                            mission_id,
                            ingress,
                            open_results,
                            step_outcomes,
                            ledger_refs,
                            cost_spent,
                            status="blocked",
                            summary=f"blocked at step {step_id}: {grant_err}",
                            request=payload,
                            decomposition=decomposition,
                            assignment=assignment,
                            block_context=self._build_block_context(
                                summary=f"blocked at step {step_id}: federation",
                                step_id=step_id,
                            ),
                        )
                    continue
                federation_peer_tenant = normalize_tenant_id(peer_tenant_raw)
                step_organ_registry = ProviderOrganRegistry(tenant_id=federation_peer_tenant)

            organ = step_organ_registry.get(organ_id)
            if organ is None:
                outcome = self._step_blocked(
                    mission_id,
                    step_id,
                    ordinal,
                    organ_id,
                    prior_action_id,
                    reason=f"no organ resolved for step (tier/auto-assign failed)",
                )
                step_outcomes.append(outcome)
                if halt_on_failure:
                    return self._finalize(
                        mission_id,
                        ingress,
                        open_results,
                        step_outcomes,
                        ledger_refs,
                        cost_spent,
                        status="blocked",
                        summary=f"blocked at step {step_id}: organ not resolved",
                        request=payload,
                        decomposition=decomposition,
                        assignment=assignment,
                        block_context=self._build_block_context(
                            summary=f"blocked at step {step_id}: organ not resolved",
                            assignment=assignment,
                            step_id=step_id,
                            match_reason="no_admissible_organ_for_tier",
                        ),
                    )
                continue

            region_id = str(payload.get("region_id") or "")
            est_step_cost = estimate_step_cost(organ, region_id=region_id)
            if budget_ledger.would_exceed_hard(est_step_cost):
                if halt_on_failure:
                    ingress["soft_ceil_breached"] = budget_ledger.soft_ceil_breached
                    return self._finalize(
                        mission_id,
                        ingress,
                        open_results,
                        step_outcomes,
                        ledger_refs,
                        budget_ledger.spent,
                        status="blocked",
                        summary=f"blocked at step {step_id}: mission budget_exceeded",
                        request=payload,
                        decomposition=decomposition,
                        assignment=assignment,
                        block_context=self._build_block_context(
                            summary=f"blocked at step {step_id}: budget_exceeded",
                            step_id=step_id,
                        ),
                    )
                continue

            action_id = f"{mission_id}:{step_id}:{ordinal}"
            append_organ_assignment_ledger(
                self.ledger,
                mission_id=mission_id,
                step_id=step_id,
                organ_id=organ.organ_id,
                provider=organ.provider,
                ordinal=ordinal,
            )
            step_invariants = self.invariants.evaluate_step(
                request=payload,
                ingress=ingress,
                step=step,
                organ=organ,
                action_id=action_id,
                prior_action_id=prior_action_id,
                cost_spent=cost_spent,
                rail=rail,
                manifold=manifold,
            )
            if self.invariants.has_hard_fail(step_invariants):
                outcome = {
                    "step_id": step_id,
                    "action_id": action_id,
                    "organ_id": organ_id,
                    "provider": organ.provider,
                    "status": "blocked",
                    "cost_units": 0,
                    "invariant_results": step_invariants,
                    "prior_action_id": prior_action_id,
                    "proposal": None,
                    "aais_deliberation": None,
                }
                step_outcomes.append(outcome)
                if halt_on_failure:
                    return self._finalize(
                        mission_id,
                        ingress,
                        open_results,
                        step_outcomes,
                        ledger_refs,
                        cost_spent,
                        status="blocked",
                        summary=f"blocked at step {step_id}: cloud invariants",
                        request=payload,
                        decomposition=decomposition,
                        assignment=assignment,
                        block_context=self._build_block_context(
                            summary=f"blocked at step {step_id}: cloud invariants",
                            invariant_results=step_invariants,
                            assignment=assignment,
                            step_id=step_id,
                        ),
                    )
                continue

            proposal = None
            aais_deliberation = None
            step_status = "ok"
            execution_state = None
            execution_committed = False
            shadow_step = False
            step_aais_id = self._step_aais_instance_id(step, ingress, payload)

            if use_aais_bridge:
                from src.ugr.mission.aais_step_bridge import STEP_MODE_FULL_DELIBERATE, resolve_step_deliberation_mode
                from src.ugr.mission.step_execution import run_step_execution

                from src.ugr.mission.organ_trust import effective_trust, resolve_execution_mode_for_organ

                bridge_svc, ugr_rt = self._ensure_aais(step_aais_id)
                organ_trust = effective_trust(
                    organ.trust_score, tenant_manifold.tenant_id, organ.organ_id
                )
                step_exec_mode = resolve_execution_mode_for_organ(execution_mode, organ_trust)
                force_exec = should_force_provider_execute(step_exec_mode)
                deliberation_mode = resolve_step_deliberation_mode(payload)

                def _run_bridge() -> dict[str, Any]:
                    return run_mission_step_deliberation(
                        mission_request=payload,
                        ingress=ingress,
                        step=step,
                        organ=organ,
                        action_id=action_id,
                        mission_id=mission_id,
                        prior_action_id=prior_action_id,
                        prior_step_summary=prior_step_summary,
                        bridge=bridge_svc,
                        ugr_runtime=ugr_rt,
                        runtime_dir=self.runtime_dir,
                        force_execute=force_exec,
                    )

                if deliberation_mode == STEP_MODE_FULL_DELIBERATE:
                    aais_deliberation = _run_bridge()
                    proposal = aais_deliberation.get("proposal")
                    if not proposal:
                        proposal = self.organs.build_proposal(
                            organ,
                            mission_id=mission_id,
                            action_id=action_id,
                            step=step,
                            intent=intent,
                        )
                    bridge_decision = str(aais_deliberation.get("bridge_decision") or "").upper()
                    if aais_deliberation.get("status") == "blocked" or bridge_decision == DECISION_BLOCK:
                        step_status = "blocked"
                    prior_step_summary = str(aais_deliberation.get("summary") or "")[:200]
                else:
                    exec_result = run_step_execution(
                        execution_mode=step_exec_mode,
                        mission_request=payload,
                        step=step,
                        organ=organ,
                        action_id=action_id,
                        mission_id=mission_id,
                        ingress=ingress,
                        manifold=manifold,
                        invariants=self.invariants,
                        ledger=self.ledger,
                        prior_action_id=prior_action_id,
                        rail=rail,
                        run_bridge_fn=_run_bridge,
                        step_invariants=step_invariants,
                    )
                    step_status = str(exec_result.get("step_status") or "ok")
                    aais_deliberation = exec_result.get("aais_deliberation")
                    proposal = exec_result.get("proposal")
                    execution_state = exec_result.get("execution_state")
                    execution_committed = bool(exec_result.get("execution_committed"))
                    shadow_step = bool(exec_result.get("shadow"))
                    if not proposal:
                        proposal = self.organs.build_proposal(
                            organ,
                            mission_id=mission_id,
                            action_id=action_id,
                            step=step,
                            intent=intent,
                        )
                    prior_step_summary = str((aais_deliberation or {}).get("summary") or "")[:200]
            else:
                proposal = self.organs.build_proposal(
                    organ,
                    mission_id=mission_id,
                    action_id=action_id,
                    step=step,
                    intent=intent,
                )

            cost_units = est_step_cost if step_status == "ok" else 0.0
            if step_status == "ok":
                actual_cost = est_step_cost
                if aais_deliberation:
                    for lane in list(aais_deliberation.get("lane_results") or []):
                        execution = dict((lane.get("payload") or {}).get("governed_llm_execution") or {})
                        tokens = int(execution.get("tokens_used") or 0)
                        if tokens > 0:
                            from src.ugr.mission.cost_routing import OrganCostContract

                            contract = OrganCostContract.from_organ(organ)
                            if contract.cost_per_token:
                                actual_cost = contract.cost_per_call + contract.cost_per_token * tokens
                            break
                budget_ledger.charge(actual_cost)
                cost_spent = budget_ledger.spent
                cost_units = actual_cost
                ingress["soft_ceil_breached"] = budget_ledger.soft_ceil_breached

            ledger_record = {
                "type": "urg_mission_action",
                "mission_id": mission_id,
                "action_id": action_id,
                "prior_action_id": prior_action_id,
                "step_id": step_id,
                "organ_id": organ.organ_id,
                "provider": organ.provider,
                "tenant_id": ingress.get("tenant_id"),
                "operator_id": ingress.get("operator_id"),
                "aais_instance_id": step_aais_id,
                "region_id": payload.get("region_id"),
                "cost_units": cost_units,
                "rail": rail,
                "status": step_status,
                "proposal_status": (proposal or {}).get("status"),
                "aais_step_bridge": use_aais_bridge,
                "step_deliberation_mode": aais_deliberation.get("step_deliberation_mode") if aais_deliberation else None,
                "governed_llm_status": (aais_deliberation or {}).get("governed_llm_status"),
                "execution_state": execution_state,
                "execution_committed": execution_committed,
                "shadow": shadow_step,
                "execution_mode": execution_mode,
            }
            if step_status == "ok":
                next_cloud = MissionCloudState(
                    mission_id=mission_id,
                    cloud_identity_hash=manifold.cloud_identity_hash,
                    boundary_digest=manifold.boundary_digest,
                    step_ids_seen=cloud_state.step_ids_seen + [step_id],
                    ledger_action_ids=cloud_state.ledger_action_ids,
                    status="step_append",
                )
                ok_transition, transition_reason = valid_cloud_transition(
                    cloud_state,
                    next_cloud,
                    mission_state={
                        "request": payload,
                        "ingress": ingress,
                        "cloud_manifold": manifold.to_dict(),
                        "organ_ids": manifold.organ_ids,
                    },
                    authorized_rebind=bool(payload.get("authorized_identity_mutation")),
                )
                if not ok_transition:
                    return self._blocked(
                        mission_id,
                        ingress,
                        [_fail("cloud_continuity", transition_reason)],
                        summary=f"invalid cloud transition at {step_id}",
                        steps=step_outcomes,
                        request=payload,
                        decomposition=decomposition,
                        assignment=assignment,
                    )
                try:
                    ref = self.ledger.append_action(ledger_record)
                    if federation_peer_tenant and federation_grant_id:
                        from src.ugr.mission.step_execution import (
                            append_federation_inbound_ledger,
                            append_federation_step_ledger,
                        )

                        peer_ledger = MissionLedger(
                            runtime_dir=self.runtime_dir,
                            tenant_id=federation_peer_tenant,
                        )
                        append_federation_step_ledger(
                            self.ledger,
                            mission_id=mission_id,
                            step_id=step_id,
                            action_id=action_id,
                            federation_grant_id=federation_grant_id,
                            federation_peer_tenant=federation_peer_tenant,
                            organ_id=organ.organ_id,
                            provider=organ.provider,
                            home_tenant_id=tenant_manifold.tenant_id,
                        )
                        append_federation_inbound_ledger(
                            peer_ledger,
                            home_mission_id=mission_id,
                            home_tenant_id=tenant_manifold.tenant_id,
                            step_id=step_id,
                            grant_id=federation_grant_id,
                            organ_id=organ.organ_id,
                            provider=organ.provider,
                            peer_tenant_id=federation_peer_tenant,
                        )
                        self._federation_context.append(
                            {
                                "grant_id": federation_grant_id,
                                "peer_tenant": federation_peer_tenant,
                                "step_id": step_id,
                            }
                        )
                except CloudCausalityFault as exc:
                    return self._blocked(
                        mission_id,
                        ingress,
                        [_fail("cloud_causality", str(exc))],
                        summary=f"ledger write failed at {step_id}",
                        steps=step_outcomes,
                        request=payload,
                        decomposition=decomposition,
                        assignment=assignment,
                    )
                ledger_refs.append(ref)
                cloud_state = MissionCloudState(
                    mission_id=mission_id,
                    cloud_identity_hash=manifold.cloud_identity_hash,
                    boundary_digest=manifold.boundary_digest,
                    step_ids_seen=next_cloud.step_ids_seen,
                    ledger_action_ids=cloud_state.ledger_action_ids + [ref],
                    status="active",
                )
                prior_action_id = action_id

            step_outcome: dict[str, Any] = {
                "step_id": step_id,
                "action_id": action_id,
                "organ_id": organ.organ_id,
                "provider": organ.provider,
                "status": step_status,
                "cost_units": cost_units,
                "invariant_results": step_invariants,
                "prior_action_id": ledger_record.get("prior_action_id"),
                "proposal": proposal,
                "organ": organ.to_dict(),
                "aais_deliberation": aais_deliberation,
                "execution_state": execution_state,
                "execution_committed": execution_committed,
                "shadow": shadow_step,
            }
            if federation_peer_tenant:
                step_outcome["federation_peer_tenant"] = federation_peer_tenant
                step_outcome["federation_grant_id"] = federation_grant_id
            step_outcomes.append(step_outcome)

            if step_status == "blocked" and halt_on_failure:
                return self._finalize(
                    mission_id,
                    ingress,
                    open_results,
                    step_outcomes,
                    ledger_refs,
                    cost_spent,
                    status="blocked",
                    summary=f"blocked at step {step_id}: AAIS bridge",
                    cloud_forge=cloud_forge,
                    request=payload,
                    decomposition=decomposition,
                    assignment=assignment,
                    block_context=self._build_block_context(
                        summary=f"blocked at step {step_id}: AAIS bridge",
                        assignment=assignment,
                        step_id=step_id,
                    ),
                )

        ok_steps = [s for s in step_outcomes if s.get("status") == "ok"]
        final_status = "ok" if len(ok_steps) == len(step_outcomes) else "blocked"
        identity_check = check_cloud_identity(
            {
                "request": payload,
                "ingress": ingress,
                "cloud_manifold": manifold.to_dict(),
                "organ_ids": manifold.organ_ids,
            },
            manifold=manifold,
            authorized_rebind=bool(payload.get("authorized_identity_mutation")),
        )
        if self.invariants.has_hard_fail(identity_check):
            return self._blocked(
                mission_id,
                ingress,
                identity_check,
                summary="cloud identity compromised",
                steps=step_outcomes,
                request=payload,
                decomposition=decomposition,
                assignment=assignment,
            )

        return self._finalize(
            mission_id,
            ingress,
            open_results,
            step_outcomes,
            ledger_refs,
            cost_spent,
            status=final_status,
            summary=(
                f"Mission completed: {len(ok_steps)} step(s) across "
                f"{len({s.get('provider') for s in ok_steps})} provider(s), "
                f"cost_units={cost_spent}, aais_bridge={use_aais_bridge}."
            ),
            cloud_forge=cloud_forge,
            request=payload,
            decomposition=decomposition,
            assignment=assignment,
            cloud_manifold=manifold,
            rail=rail,
        )

    def _finalize(
        self,
        mission_id: str,
        ingress: dict[str, Any],
        open_results: list[dict[str, Any]],
        steps: list[dict[str, Any]],
        ledger_refs: list[str],
        cost_spent: float,
        *,
        status: str,
        summary: str,
        cloud_forge: dict[str, Any] | None = None,
        request: dict[str, Any] | None = None,
        decomposition: dict[str, Any] | None = None,
        assignment: dict[str, Any] | None = None,
        block_context: dict[str, Any] | None = None,
        cloud_manifold: CloudManifoldState | None = None,
        rail: str = "NORMAL",
    ) -> dict[str, Any]:
        composite = {
            "mission_id": mission_id,
            "step_count": len(steps),
            "providers_used": sorted({str(s.get("provider") or "") for s in steps if s.get("status") == "ok"}),
            "total_cost_units": cost_spent,
            "all_invariants_passed": status == "ok",
            "law": "urg_composite_mission_merge",
        }
        payload = dict(request or {})
        decomp = decomposition or decompose_mission(payload)
        assign = assignment or assign_organs(decomp, organ_registry=self.organs)
        ledger_rows = self.ledger.list_for_mission(mission_id) if mission_id else []

        req = dict(request or {})
        exec_mode = str(req.get("execution_mode") or os.getenv("URG_EXECUTION_MODE", "DRY_RUN")).strip().upper()

        response = {
            "runtime_id": URG_MISSION_RUNTIME_ID,
            "runtime_version": URG_MISSION_RUNTIME_VERSION,
            "mission_id": mission_id,
            "status": status,
            "summary": summary,
            "execution_mode": exec_mode,
            "urg_ingress": ingress,
            "cloud_invariants": {"mission_open": open_results},
            "steps": steps,
            "ledger_refs": ledger_refs,
            "composite": composite,
            "cloud_forge": cloud_forge,
            "switchboard": {
                "role": "lawbook_not_model",
                "atomic_unit": "governed_composite_mission",
                "organs_admitted": self.organs.admitted_organ_ids(),
                "aais_step_bridge": mission_step_bridge_enabled(payload),
            },
        }
        if cloud_manifold:
            response["cloud_manifold"] = cloud_manifold.to_dict()
        response["cloud_rail"] = rail
        if self._federation_context:
            ingress["federation_context"] = list(self._federation_context)
        return attach_gcm_to_response(
            response,
            request=payload,
            ingress=ingress,
            decomposition=decomp,
            assignment=assign,
            mission_open=open_results,
            ledger_rows=ledger_rows,
            block_context=block_context,
            steps=steps,
            rail=rail,
            runtime_dir=str(self.runtime_dir),
            federation_context=list(self._federation_context),
        )

    def _blocked(
        self,
        mission_id: str,
        ingress: dict[str, Any],
        results: list[dict[str, Any]],
        *,
        summary: str,
        steps: list[dict[str, Any]],
        request: dict[str, Any] | None = None,
        decomposition: dict[str, Any] | None = None,
        assignment: dict[str, Any] | None = None,
        block_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ctx = block_context or self._build_block_context(
            summary=summary,
            invariant_results=results,
            assignment=assignment,
        )
        return self._finalize(
            mission_id,
            ingress,
            results,
            steps,
            [],
            0.0,
            status="blocked",
            summary=summary,
            request=request,
            decomposition=decomposition,
            assignment=assignment,
            block_context=ctx,
        )

    @staticmethod
    def _step_blocked(
        mission_id: str,
        step_id: str,
        ordinal: int,
        organ_id: str,
        prior_action_id: str | None,
        *,
        reason: str,
    ) -> dict[str, Any]:
        return {
            "step_id": step_id,
            "action_id": f"{mission_id}:{step_id}:{ordinal}",
            "organ_id": organ_id,
            "provider": None,
            "status": "blocked",
            "cost_units": 0,
            "invariant_results": [_fail("cloud_identity", reason)],
            "prior_action_id": prior_action_id,
            "proposal": None,
            "aais_deliberation": None,
        }


def _fail(family: str, details: str) -> dict[str, Any]:
    return {"family": family, "status": "hard_fail", "details": details}


def build_mission_runtime(runtime_dir: str | Path | None = None) -> UGRMissionRuntime:
    return UGRMissionRuntime(runtime_dir=runtime_dir)
