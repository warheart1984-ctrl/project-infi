"""Constitutional Runtime v0.1 — kernel state machine and contracts."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.continuity.crk1_compliance import (
    CANONICAL_CONTRACTS,
    CANONICAL_OBJECTS,
    CANONICAL_RUNTIME_METHODS,
    check_contracts,
    check_objects,
    check_runtime_methods,
)

from src.continuity.crk2_boundary_control import BoundaryController, BoundaryControlConfig
from src.kernel.governance import Governance
from src.continuity.decision_ledger import (
    DecisionLedgerStore,
    DecisionRecord,
    DecisionStatus,
    bootstrap_decision_ledger,
)
from src.continuity.outcome_fitness import OutcomeConfig
from src.continuity.outcome_ledger import OutcomeLedgerStore, bootstrap_outcome_ledger
from src.continuity.resource_contract import ResourceContract
from src.continuity.resource_ledger import ResourceLedgerStore, bootstrap_resource_ledger

logger = logging.getLogger(__name__)


from src.continuity.identity_object import DEFAULT_IDENTITY, IdentityObject
class EvidenceContract:
    """EIT-1 / EIT-2 admissibility for decisions."""

    def __init__(self, *, evidence_store: Any, min_confidence: float = 0.5) -> None:
        self.evidence_store = evidence_store
        self.min_confidence = min_confidence

    def check_decision_evidence(self, decision: DecisionRecord) -> None:
        if not decision.evidence_refs:
            raise ValueError("Evidence contract: decision requires evidence_refs")
        for evidence_id in decision.evidence_refs:
            record = self.evidence_store.get_evidence(evidence_id)
            if record is None:
                raise ValueError(f"Evidence contract: missing evidence {evidence_id}")
            if float(record.confidence) < self.min_confidence:
                raise ValueError(f"Evidence contract: confidence below threshold for {evidence_id}")


class GovernanceContract:
    """Authority and invariant checks for decisions."""

    def __init__(self, identity: IdentityObject) -> None:
        self.identity = identity

    def check_invariants(self, decision: DecisionRecord) -> None:
        intent_lower = decision.intent.lower()
        for invariant in self.identity.invariants:
            token = invariant.split()[0].lower() if invariant else ""
            if token and token in intent_lower and "without" in invariant.lower():
                raise ValueError(f"Governance contract: intent may violate invariant — {invariant}")

    def check_authority(self, decision: DecisionRecord) -> None:
        roles = self.identity.authority_model.get(decision.actor_id) or {}
        allowed = roles.get("approve") or []
        if decision.type not in allowed and "*" not in allowed:
            raise ValueError(
                f"Governance contract: actor {decision.actor_id} lacks authority for {decision.type}"
            )

    def current_kernel_version(self) -> int:
        return Governance.current().current_kernel_version()

    def amendment_store(self) -> Any:
        return Governance.current().amendment_store()

    def propose_kernel_amendment(
        self,
        *,
        reason: str,
        signals: list[float],
        insufficiency: float,
        ratify: bool = False,
    ) -> bool:
        return Governance.current().propose_kernel_amendment(
            reason=reason,
            signals=signals,
            insufficiency=insufficiency,
            ratify=ratify,
        )


class RuntimeContract:
    """Epoch admissibility — spine health + outcome drift."""

    def build_spine_health(self, **kwargs: Any) -> dict[str, Any]:
        from src.continuity.evidence_fitness import build_spine_health

        return build_spine_health(**kwargs)

    def check_ready(
        self,
        decision: DecisionRecord,
        *,
        resource_contract: ResourceContract | None = None,
    ) -> None:
        if decision.status not in {DecisionStatus.APPROVED, DecisionStatus.EXECUTING}:
            raise ValueError("Runtime contract: decision must be approved before execution")
        if resource_contract is not None:
            resource_contract.verify_decision_allocations(decision)


def check_crk1_invariants(runtime: ConstitutionalRuntime | None = None) -> dict[str, Any]:
    """Runtime CRK-1 compliance report — objects, contracts, canonical transitions."""
    missing_objects, extra_objects = check_objects()
    missing_contracts = check_contracts()
    missing_transitions = check_runtime_methods()
    objects_ok = not missing_objects and not extra_objects
    contracts_ok = not missing_contracts
    transitions_ok = not missing_transitions
    ledgers_ok = True
    if runtime is not None:
        ledgers_ok = all(
            [
                runtime.ledgers.identity is not None,
                runtime.decisions is not None,
                runtime.resources is not None,
                runtime.outcomes is not None,
            ]
        )
        contracts_bound = set(runtime.contracts.keys()) >= {
            "evidence",
            "governance",
            "resource",
            "runtime",
        }
        contracts_ok = contracts_ok and contracts_bound
    compliant = objects_ok and contracts_ok and transitions_ok and ledgers_ok
    report = {
        "compliant": compliant,
        "objects_ok": objects_ok,
        "contracts_ok": contracts_ok,
        "transitions_ok": transitions_ok,
        "ledgers_ok": ledgers_ok,
        "missing_objects": sorted(missing_objects),
        "extra_objects": sorted(extra_objects),
        "missing_contracts": sorted(missing_contracts),
        "missing_transitions": sorted(missing_transitions),
        "canonical_objects": sorted(CANONICAL_OBJECTS),
        "canonical_contracts": sorted(CANONICAL_CONTRACTS),
        "canonical_transitions": sorted(CANONICAL_RUNTIME_METHODS),
    }
    logger.info("CRK-1-COMPLIANT: %s", compliant)
    return report


@dataclass
class ConstitutionalLedgers:
    identity: IdentityObject = field(default_factory=lambda: DEFAULT_IDENTITY)
    decisions: DecisionLedgerStore | None = None
    resources: ResourceLedgerStore | None = None
    outcomes: OutcomeLedgerStore | None = None
    law_store: Any | None = None
    evidence_store: Any | None = None
    comprehension_store: Any | None = None
    mit_store: Any | None = None
    sit_store: Any | None = None
    git_store: Any | None = None
    epoch: int = 0


class ConstitutionalRuntime:
    """Minimal constitutional kernel — Identity → Evidence → Decision → Outcome → Epoch."""

    def __init__(
        self,
        ledgers: ConstitutionalLedgers,
        *,
        evidence_contract: EvidenceContract | None = None,
        governance_contract: GovernanceContract | None = None,
        resource_contract: ResourceContract | None = None,
        runtime_contract: RuntimeContract | None = None,
        outcome_config: OutcomeConfig | None = None,
        boundary_config: BoundaryControlConfig | None = None,
    ) -> None:
        self.ledgers = ledgers
        self.decisions = ledgers.decisions or DecisionLedgerStore()
        self.resources = ledgers.resources or ResourceLedgerStore()
        self.outcomes = ledgers.outcomes or OutcomeLedgerStore(config=outcome_config or OutcomeConfig())
        self.outcome_config = outcome_config or OutcomeConfig()
        bootstrap_decision_ledger(self.decisions, epoch=ledgers.epoch or 17)
        bootstrap_resource_ledger(self.resources, epoch=ledgers.epoch or 17)
        bootstrap_outcome_ledger(self.outcomes, epoch=ledgers.epoch or 17)
        self.contracts = {
            "evidence": evidence_contract
            or EvidenceContract(evidence_store=ledgers.evidence_store),
            "governance": governance_contract or GovernanceContract(ledgers.identity),
            "resource": resource_contract
            or ResourceContract(self.resources, decision_ledger=self.decisions),
            "runtime": runtime_contract or RuntimeContract(),
        }
        self._crk1_report = check_crk1_invariants(self)
        self.boundary_controller = BoundaryController(
            config=boundary_config or BoundaryControlConfig(),
            governance=Governance.current(),
        )

    def propose_decision(self, draft: DecisionRecord) -> DecisionRecord:
        self.contracts["governance"].check_invariants(draft)
        if draft.evidence_refs:
            self.contracts["evidence"].check_decision_evidence(draft)
        return self.decisions.propose(draft)

    def approve_decision(self, decision_id: str) -> DecisionRecord:
        decision = self.decisions.get(decision_id)
        if decision is None:
            raise KeyError(decision_id)
        self.contracts["governance"].check_authority(decision)
        self.contracts["evidence"].check_decision_evidence(decision)
        return self.decisions.approve(decision_id)

    def allocate_resources_for_decision(self, decision_id: str, plan: list[dict[str, Any]] | None = None) -> None:
        decision = self.decisions.get(decision_id)
        if decision is None:
            raise KeyError(decision_id)
        if plan is not None:
            patched = DecisionRecord.from_dict(
                {
                    **decision.to_dict(),
                    "resource_plan": {
                        **decision.resource_plan,
                        "allocations": plan,
                    },
                }
            )
            self.contracts["resource"].allocate_for_decision(patched)
            return
        self.contracts["resource"].allocate_for_decision(decision)

    def execute_decision(
        self,
        decision_id: str,
        *,
        expected: dict[str, Any],
        observed: dict[str, Any],
        lessons: list[str] | None = None,
    ) -> Any:
        decision = self.decisions.get(decision_id)
        if decision is None:
            raise KeyError(decision_id)
        self.contracts["runtime"].check_ready(
            decision,
            resource_contract=self.contracts["resource"],
        )
        outcome = self.outcomes.record(
            decision_id=decision_id,
            expected=expected,
            observed=observed,
            epoch=decision.epoch,
            lessons=lessons,
        )
        self.decisions.mark_executed(decision_id)
        return outcome

    def advance_epoch(self) -> dict[str, Any]:
        health = self.contracts["runtime"].build_spine_health(
            law_store=self.ledgers.law_store,
            evidence_store=self.ledgers.evidence_store,
            comprehension_store=self.ledgers.comprehension_store,
            mit_store=self.ledgers.mit_store,
            sit_store=self.ledgers.sit_store,
            git_store=self.ledgers.git_store,
            outcome_store=self.outcomes,
        )
        if health.get("epoch_commit_blocked"):
            raise RuntimeError(
                f"Spine unhealthy; epoch blocked: {health.get('block_reasons')}"
            )
        boundary = self.boundary_controller.observe_spine(health)
        self.ledgers.epoch += 1
        from src.kernel.governance import Governance as KernelGovernance
        from src.kernel.identity_history_ledger import shared_identity_ledger

        shared_identity_ledger().append(
            identity=self.ledgers.identity,
            epoch=self.ledgers.epoch,
            kernel_version=KernelGovernance.current().current_kernel_version(),
            reason="epoch-advance",
        )
        return {
            "epoch": self.ledgers.epoch,
            "spine_health": health,
            "boundary_detection": boundary,
        }
