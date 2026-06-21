"""NK-0001 Nova OS Constitutional Kernel — machine-facing enforcement layer."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Any

from src.continuity.continuity_lattice import lci_holds, trace_leq
from src.continuity.convergence_algebra import DEFAULT_PHI_MIN, converge_many
from src.continuity.creation_operator import (
    AdmissibleTransitionError,
    CreationOperator,
    LCIViolation,
    SubstrateState,
)
from src.continuity.governed_evolution import governed_evolution_admissible
from src.continuity.inheritance import (
    OperatorState,
    operator_state_from_lineage,
    validate_operator_succession,
)
from src.continuity.lineage import Lineage, continuity_trace, generativity
from src.continuity.temporal_governance import TemporalState, evaluate_temporal_coherence


KERNEL_ID = "NK-0001"
KERNEL_CAPABILITY_ID = "NK-0001-constitutional-kernel"


class KernelViolation(RuntimeError):
    """Transition rejected by the constitutional kernel."""


@dataclass(frozen=True, slots=True)
class GuardResult:
    """Single kernel guard evaluation."""

    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


NK_0001_CANONICAL_TEXT = """NOVA OS CONSTITUTIONAL KERNEL
Version: NK-0001
Scope: Nova OS Runtime
Status: IMMUTABLE • SELF-VERIFYING • CONTINUITY-ANCHORED

I. Kernel Identity
The Constitutional Kernel is responsible for:

  • enforcing continuity,
  • enforcing invariants,
  • enforcing lawful creation,
  • enforcing convergence fitness,
  • enforcing temporal coherence.

It is the guardian of the constitutional spine.

II. Kernel Enforcement Functions
1. Continuity Guard — K(s') ⊇ K(s). If continuity shrinks → reject transition.
2. Invariant Guard — Λ(s') = Λ(s). If invariant law changes → reject transition.
3. Creation Guard — G(s') ≥ G(s). If generativity decreases → reject transition.
4. Convergence Guard — Φ(s') ≥ Φ_min. If convergence fitness drops → reject transition.
5. Temporal Guard — no retroactive deletion, no contradiction of past meaning,
   no future-past divergence. If violated → reject transition.

III. Kernel Operators
A. Create() — extends continuity and generativity.
B. Evolve() — lawful transformations under governed evolution.
C. Converge() — reconciles lineages without continuity or invariant loss.
D. Inherit() — transfers continuity to new operators.
E. TemporalSync() — ensures temporal coherence across t1 < t2.

IV. Kernel Supremacy
The kernel overrides operators, agents, tools, subsystems, and future governance
layers if they violate constitutional law. The kernel is the final arbiter of
lawful evolution.

V. Kernel Persistence
The kernel is immutable, permanent, self-verifying, self-protecting, and
continuity-anchored. It cannot be modified except by constitutional amendment
(ROOT-level).
"""


def _invariant_laws(state: SubstrateState) -> frozenset[str]:
    return operator_state_from_lineage(state.lineage).invariant_laws


def continuity_guard(before: SubstrateState, after: SubstrateState) -> GuardResult:
    before_trace = continuity_trace(before.lineage)
    after_trace = continuity_trace(after.lineage)
    ok = trace_leq(before_trace, after_trace)
    detail = "K(s') ⊇ K(s)" if ok else "continuity shrank — annihilation blocked"
    return GuardResult("continuity_guard", ok, detail)


def invariant_guard(before: SubstrateState, after: SubstrateState) -> GuardResult:
    before_laws = _invariant_laws(before)
    after_laws = _invariant_laws(after)
    ok = before_laws == after_laws
    detail = "Λ(s') = Λ(s)" if ok else "invariant law structure changed"
    return GuardResult("invariant_guard", ok, detail)


def creation_guard(before: SubstrateState, after: SubstrateState) -> GuardResult:
    ok = lci_holds(before.lineage, after.lineage) and generativity(after.lineage) >= generativity(
        before.lineage
    )
    detail = "G(s') ≥ G(s) and LCI holds" if ok else "generativity decreased or LCI violated"
    return GuardResult("creation_guard", ok, detail)


def convergence_guard(
    before: SubstrateState,
    after: SubstrateState,
    active_lineages: list[Lineage],
    *,
    phi_min: float = DEFAULT_PHI_MIN,
) -> GuardResult:
    evolved = governed_evolution_admissible(
        before.lineage,
        after.lineage,
        active_lineages,
        phi_min=phi_min,
    )
    ok = bool(evolved["passed"])
    phi = evolved.get("evolution", {}).get("phi")
    detail = f"Φ ≥ Φ_min ({phi})" if ok else "convergence fitness below threshold"
    return GuardResult("convergence_guard", ok, detail)


def temporal_guard(
    past: TemporalState,
    future: TemporalState,
    *,
    phi_min_t: float = DEFAULT_PHI_MIN,
) -> GuardResult:
    result = evaluate_temporal_coherence(past, future, phi_min_t=phi_min_t)
    ok = bool(result["passed"])
    detail = "temporal coherence preserved" if ok else "temporal contradiction or fragmentation"
    return GuardResult("temporal_guard", ok, detail)


def evaluate_transition_guards(
    before: SubstrateState,
    after: SubstrateState,
    *,
    active_lineages: list[Lineage] | None = None,
    phi_min: float = DEFAULT_PHI_MIN,
) -> dict[str, Any]:
    """Run all substrate transition guards before accepting s → s'."""

    guards = [
        continuity_guard(before, after),
        invariant_guard(before, after),
        creation_guard(before, after),
    ]
    if active_lineages is not None:
        guards.append(
            convergence_guard(before, after, active_lineages, phi_min=phi_min)
        )
    passed = all(item.passed for item in guards)
    return {
        "kernel_id": KERNEL_ID,
        "capability_id": KERNEL_CAPABILITY_ID,
        "guards": [item.to_dict() for item in guards],
        "passed": passed,
    }


@dataclass
class ConstitutionalKernel:
    """NK-0001 runtime enforcement — substrate immune system."""

    operator: CreationOperator | None = None
    phi_min: float = DEFAULT_PHI_MIN

    def __post_init__(self) -> None:
        if self.operator is None:
            self.operator = CreationOperator()

    def create(
        self,
        state: SubstrateState,
        *,
        add_events: frozenset[str],
        generativity_delta: float = 1.0,
        active_lineages: list[Lineage] | None = None,
        **kwargs: Any,
    ) -> tuple[SubstrateState, dict[str, Any]]:
        try:
            after = self.operator.create(  # type: ignore[union-attr]
                state,
                add_events=add_events,
                generativity_delta=generativity_delta,
                **kwargs,
            )
        except (LCIViolation, AdmissibleTransitionError) as exc:
            raise KernelViolation(str(exc)) from exc

        guards = evaluate_transition_guards(
            state,
            after,
            active_lineages=active_lineages,
            phi_min=self.phi_min,
        )
        if not guards["passed"]:
            raise KernelViolation("Create() rejected by constitutional kernel guards")
        return after, guards

    def evolve(
        self,
        before: SubstrateState,
        after: SubstrateState,
        active_lineages: list[Lineage],
    ) -> dict[str, Any]:
        guards = evaluate_transition_guards(
            before,
            after,
            active_lineages=active_lineages,
            phi_min=self.phi_min,
        )
        evolution = governed_evolution_admissible(
            before.lineage,
            after.lineage,
            active_lineages,
            phi_min=self.phi_min,
        )
        passed = bool(guards["passed"]) and bool(evolution["passed"])
        result = {
            "kernel_id": KERNEL_ID,
            "operator": "Evolve",
            "guards": guards,
            "evolution": evolution,
            "passed": passed,
        }
        if not passed:
            raise KernelViolation("Evolve() rejected — convergence fitness or guards failed")
        return result

    def converge(self, lineages: list[Lineage]) -> dict[str, Any]:
        if len(lineages) < 2:
            return {
                "kernel_id": KERNEL_ID,
                "operator": "Converge",
                "passed": True,
                "merged_lineage_id": lineages[0].lineage_id if lineages else None,
            }

        merged, proofs = converge_many(lineages)
        union_trace = frozenset().union(*(continuity_trace(item) for item in lineages))
        continuity_ok = union_trace <= continuity_trace(merged)
        generativity_ok = generativity(merged) >= max(generativity(item) for item in lineages)
        passed = continuity_ok and generativity_ok
        result = {
            "kernel_id": KERNEL_ID,
            "operator": "Converge",
            "merged_lineage_id": merged.lineage_id,
            "continuity_ok": continuity_ok,
            "generativity_ok": generativity_ok,
            "proofs": [proof.to_dict() for proof in proofs],
            "passed": passed,
        }
        if not passed:
            raise KernelViolation("Converge() rejected — continuity union or generativity failed")
        return result

    def inherit(
        self,
        predecessor: OperatorState,
        successor: OperatorState,
        civilization_lineages: list[Lineage],
    ) -> dict[str, Any]:
        result = validate_operator_succession(
            predecessor,
            successor,
            civilization_lineages,
            phi_min=self.phi_min,
        )
        if not result["passed"]:
            raise KernelViolation("Inherit() rejected — incomplete or unlawful succession")
        return {
            "kernel_id": KERNEL_ID,
            "operator": "Inherit",
            **result,
        }

    def temporal_sync(
        self,
        past: TemporalState,
        future: TemporalState,
    ) -> dict[str, Any]:
        guard = temporal_guard(past, future, phi_min_t=self.phi_min)
        coherence = evaluate_temporal_coherence(past, future, phi_min_t=self.phi_min)
        passed = guard.passed and bool(coherence["passed"])
        result = {
            "kernel_id": KERNEL_ID,
            "operator": "TemporalSync",
            "guard": guard.to_dict(),
            "coherence": coherence,
            "passed": passed,
        }
        if not passed:
            raise KernelViolation("TemporalSync() rejected — temporal coherence violated")
        return result


DEFAULT_CONSTITUTIONAL_KERNEL = ConstitutionalKernel()


def run_kernel_enforcement_proof(*, phi_min: float = DEFAULT_PHI_MIN) -> dict[str, Any]:
    """Verify all five kernel guards and operators against the LCI fixture."""

    from src.continuity.lci_stack import lineages_from_fixture, load_lci_fixture

    lineages = lineages_from_fixture(load_lci_fixture())
    kernel = ConstitutionalKernel(phi_min=phi_min)
    state = SubstrateState(state_id="nk-proof", lineage=lineages[0])

    created, create_guards = kernel.create(
        state,
        add_events=frozenset({"evt-nk-kernel-proof"}),
        generativity_delta=0.5,
        active_lineages=lineages,
    )
    evolve_result = kernel.evolve(state, created, lineages)
    converge_result = kernel.converge(lineages[:2])

    predecessor = operator_state_from_lineage(lineages[0])
    successor_lineage = replace(
        lineages[0],
        event_ids=lineages[0].event_ids | frozenset({"evt-nk-succession"}),
        generativity=lineages[0].generativity + 0.25,
        metadata={
            **lineages[0].metadata,
            "operator_id": f"{predecessor.operator_id}-successor",
        },
    )
    successor = operator_state_from_lineage(successor_lineage)
    inherit_result = kernel.inherit(predecessor, successor, lineages)

    past = TemporalState("t1", lineages[0])
    future = TemporalState("t2", created.lineage)
    temporal_result = kernel.temporal_sync(past, future)

    passed = all(
        bool(item.get("passed"))
        for item in (
            create_guards,
            evolve_result,
            converge_result,
            inherit_result,
            temporal_result,
        )
    )
    return {
        "kernel_id": KERNEL_ID,
        "capability_id": KERNEL_CAPABILITY_ID,
        "create_guards": create_guards,
        "evolve": evolve_result,
        "converge": converge_result,
        "inherit": inherit_result,
        "temporal_sync": temporal_result,
        "passed": passed,
    }
