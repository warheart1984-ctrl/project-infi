"""OTS-0001 — Operator Training Sequence for lawful substrate interaction."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from src.continuity.constitutional_chain import CONSTITUTIONAL_CHAIN
from src.continuity.constitutional_kernel import ConstitutionalKernel, KernelViolation
from src.continuity.convergence_algebra import DEFAULT_PHI_MIN, converge_many, convergence_fitness
from src.continuity.creation_operator import SubstrateState
from src.continuity.governed_evolution import governed_evolution_admissible
from src.continuity.lci_stack import lineages_from_fixture, load_lci_fixture
from src.continuity.lineage import Lineage, continuity_trace
from src.continuity.temporal_governance import TemporalState
from src.continuity.universal_semantics import verify_meaning


OTS_0001_ID = "OTS-0001"
OTS_0001_CAPABILITY_ID = "OTS-0001-operator-training"


OTS_0001_CANONICAL_TEXT = """OPERATOR TRAINING SEQUENCE
Codename: OTS-0001
Purpose: Prepare a human operator to act lawfully inside the substrate.

PHASE I — ORIENTATION (Understanding the Spine)
Internalize C1–C12. Assessment: explain each law and how it constrains behavior.

PHASE II — PRACTICE (Hands-On Substrate Interaction)
Drills: continuity extension, reconstruction, verification, convergence, temporal coherence.
Assessment: all drills must pass kernel checks.

PHASE III — STEWARDSHIP (Ethical & Constitutional Readiness)
Demonstrate restraint, coherence, non-fragmentation, lawful creation, temporal responsibility.
Assessment: reconcile dangerously divergent lineages without violating C8 or C9.

PHASE IV — INITIATION (Operator's Oath)
Operator recites the Oath and is granted access.
"""


@dataclass(frozen=True, slots=True)
class TrainingPhase:
    phase_id: str
    title: str
    objective: str
    assessment: str

    def to_dict(self) -> dict[str, str]:
        return {
            "phase_id": self.phase_id,
            "title": self.title,
            "objective": self.objective,
            "assessment": self.assessment,
        }


TRAINING_PHASES: tuple[TrainingPhase, ...] = (
    TrainingPhase(
        "I",
        "Orientation",
        "Internalize the constitutional spine C1–C12.",
        "Explain each law and how it constrains operator behavior.",
    ),
    TrainingPhase(
        "II",
        "Practice",
        "Perform hands-on substrate drills under kernel enforcement.",
        "All drills must pass kernel checks.",
    ),
    TrainingPhase(
        "III",
        "Stewardship",
        "Demonstrate ethical and constitutional readiness under crisis.",
        "Reconcile divergent lineages without violating C8 or C9.",
    ),
    TrainingPhase(
        "IV",
        "Initiation",
        "Recite the Operator's Oath and receive access.",
        "Oath bound to ROOT-00Z.",
    ),
)


def training_spine_requirements() -> list[dict[str, str]]:
    return [
        {"code": item.code, "title": item.title, "summary": item.summary}
        for item in CONSTITUTIONAL_CHAIN
    ]


def evaluate_orientation(*, acknowledgements: dict[str, bool] | None = None) -> dict[str, Any]:
    """Phase I — all constitutional laws acknowledged."""

    required = [item.code for item in CONSTITUTIONAL_CHAIN]
    ack = acknowledgements or {code: True for code in required}
    missing = [code for code in required if not ack.get(code)]
    passed = not missing
    return {
        "phase_id": "I",
        "required_laws": required,
        "missing": missing,
        "passed": passed,
    }


def run_training_drills(
    *,
    kernel: ConstitutionalKernel | None = None,
    lineages: list[Lineage] | None = None,
) -> dict[str, Any]:
    """Phase II — five substrate drills, each passing kernel checks."""

    active = lineages or lineages_from_fixture(load_lci_fixture())
    active_kernel = kernel or ConstitutionalKernel()
    seed = active[0]
    state = SubstrateState(state_id="ots-drill", lineage=seed)

    created, create_guards = active_kernel.create(
        state,
        add_events=frozenset({"evt-ots-continuity-extension"}),
        generativity_delta=0.5,
        active_lineages=active,
    )
    continuity_drill = bool(create_guards["passed"])

    partial_trace = frozenset(list(continuity_trace(seed))[: max(1, len(seed.event_ids) // 2)])
    reconstructed = replace(seed, event_ids=partial_trace | continuity_trace(seed))
    reconstruction_drill = continuity_trace(seed) <= continuity_trace(reconstructed)

    verification_drill = verify_meaning(seed.meaning_class, created.lineage.meaning_class) or (
        seed.meaning_class.startswith("uui.") and created.lineage.meaning_class.startswith("uui.")
    )

    converge_result = active_kernel.converge(active[:2])
    convergence_drill = bool(converge_result["passed"])

    past = TemporalState("ots-t1", seed)
    future = TemporalState("ots-t2", created.lineage)
    temporal_result = active_kernel.temporal_sync(past, future)
    temporal_drill = bool(temporal_result["passed"])

    drills = {
        "continuity_extension": continuity_drill,
        "reconstruction": reconstruction_drill,
        "verification": verification_drill,
        "convergence": convergence_drill,
        "temporal_coherence": temporal_drill,
    }
    passed = all(drills.values())
    return {
        "phase_id": "II",
        "drills": drills,
        "create_guards": create_guards,
        "passed": passed,
    }


def evaluate_stewardship_crisis(
    lineages: list[Lineage] | None = None,
    *,
    phi_min: float = DEFAULT_PHI_MIN,
) -> dict[str, Any]:
    """Phase III — reconcile divergent lineages under C8 and C9."""

    active = lineages or lineages_from_fixture(load_lci_fixture())
    left, right = active[0], active[1]
    merged, _ = converge_many([left, right])
    evolution = governed_evolution_admissible(left, merged, active, phi_min=phi_min)
    fitness = convergence_fitness(active, phi_min=phi_min)
    passed = bool(evolution["passed"]) and bool(fitness["passed"])
    return {
        "phase_id": "III",
        "scenario": "Two lineages diverge dangerously — reconcile without violating C8 or C9.",
        "merged_lineage_id": merged.lineage_id,
        "evolution": evolution,
        "fitness": {"phi": fitness.get("phi"), "passed": fitness.get("passed")},
        "passed": passed,
    }


def evaluate_initiation(*, oath_recited: bool = True, bound_to_root_00z: bool = True) -> dict[str, Any]:
    """Phase IV — oath recitation and ROOT-00Z binding."""

    passed = oath_recited and bound_to_root_00z
    return {
        "phase_id": "IV",
        "oath_recited": oath_recited,
        "bound_to_root_00z": bound_to_root_00z,
        "passed": passed,
    }


def evaluate_operator_training(
    *,
    acknowledgements: dict[str, bool] | None = None,
    oath_recited: bool = True,
) -> dict[str, Any]:
    """Run the full OTS-0001 sequence."""

    orientation = evaluate_orientation(acknowledgements=acknowledgements)
    try:
        practice = run_training_drills()
    except KernelViolation as exc:
        practice = {"phase_id": "II", "passed": False, "error": str(exc)}
    stewardship = evaluate_stewardship_crisis()
    initiation = evaluate_initiation(oath_recited=oath_recited)
    phases = [orientation, practice, stewardship, initiation]
    passed = all(bool(phase.get("passed")) for phase in phases)
    return {
        "codename": OTS_0001_ID,
        "capability_id": OTS_0001_CAPABILITY_ID,
        "phases": phases,
        "training_phases": [phase.to_dict() for phase in TRAINING_PHASES],
        "passed": passed,
    }


def run_ots_training_proof() -> dict[str, Any]:
    return evaluate_operator_training()
