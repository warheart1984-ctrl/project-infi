"""UGR constitutional continuity chain C1–C12."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ConstitutionalPrinciple:
    """Single constitutional law in the continuity spine."""

    code: str
    title: str
    summary: str
    capability_id: str | None = None
    supersedes: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "summary": self.summary,
            "capability_id": self.capability_id,
            "supersedes": list(self.supersedes),
            "depends_on": list(self.depends_on),
        }


C1_CONTINUITY = ConstitutionalPrinciple(
    code="UGR-C1",
    title="Continuity of Events",
    summary=(
        "Events, evidence, and decisions must be recorded without loss."
    ),
)

C2_RECONSTRUCTION = ConstitutionalPrinciple(
    code="UGR-C2",
    title="Reconstruction of Understanding",
    summary=(
        "Understanding must be recoverable from continuity traces."
    ),
    capability_id="RECON-1001",
    depends_on=("UGR-C1",),
)

C3_VERIFICATION = ConstitutionalPrinciple(
    code="UGR-C3",
    title="Verification of Meaning",
    summary=(
        "Recovered understanding must be checkable for semantic alignment."
    ),
    capability_id="VERIFY-1001",
    depends_on=("UGR-C2",),
)

C4_INVARIANTS = ConstitutionalPrinciple(
    code="UGR-C4",
    title="Preservation of Invariants",
    summary=(
        "Designated invariants I must remain stable under evolution."
    ),
    depends_on=("UGR-C3",),
)

C5_WAVE_IDENTITY = ConstitutionalPrinciple(
    code="UGR-C5",
    title="Wave Continuity of Identity",
    summary=(
        "Identities (processes, agents, lineages) must remain trackable "
        "through propagation and replay."
    ),
    depends_on=("UGR-C4",),
)

C6_UNIVERSAL_MEANING = ConstitutionalPrinciple(
    code="UGR-C6",
    title="Universal Meaning Invariance",
    summary=(
        "Where declared, a meaning class m̄* must be invariant across "
        "operators and time."
    ),
    depends_on=("UGR-C5",),
)

C7_CONVERGENCE = ConstitutionalPrinciple(
    code="UGR-C7",
    title="Convergence of Lineages",
    summary=(
        "Independently evolving lineages must be reconcilable into a "
        "semantically compatible lineage that preserves I."
    ),
    capability_id="CONVERGE-1001",
    depends_on=("UGR-C6",),
)

C8_LAWFUL_CREATION = ConstitutionalPrinciple(
    code="UGR-C8",
    title="Lawful Creation Invariant",
    summary=(
        "Creation may be unbounded in scope and complexity, but continuity "
        "must never be annihilated; evolution and convergence may only "
        "extend continuity and generativity, never erase them."
    ),
    depends_on=("UGR-C7",),
)

C9_CONVERGENCE_FITNESS = ConstitutionalPrinciple(
    code="UGR-C9",
    title="Civilizational Convergence Fitness",
    summary=(
        "For any admissible finite family of active lineages, the substrate "
        "must support convergence such that Φ remains above Φ_min; over time, "
        "Φ must not monotonically decay."
    ),
    depends_on=("UGR-C8",),
)

C10_EMERGENT_STEWARDSHIP = ConstitutionalPrinciple(
    code="UGR-C10",
    title="Emergent Stewardship",
    summary=(
        "Operators inherit a constitutional duty to act within LCI-preserving "
        "and convergence-preserving bounds; stewardship score S(o) must remain "
        "above S_min relative to the civilizational converged lineage."
    ),
    depends_on=("UGR-C9",),
)

C11_INTEROPERABILITY = ConstitutionalPrinciple(
    code="UGR-C11",
    title="Non-Destructive Interoperability",
    summary=(
        "Interactions between civilizations must preserve continuity for all "
        "participants, maintain shared invariant substrate Λ_A ∩ Λ_B ≠ ∅, and "
        "keep cross-civilizational convergence fitness Φ_AB above threshold."
    ),
    capability_id="C11-non-destructive-interoperability",
    depends_on=("UGR-C10",),
)

C12_TEMPORAL_GOVERNANCE = ConstitutionalPrinciple(
    code="UGR-C12",
    title="Inter-Temporal Governance",
    summary=(
        "Interactions across time must preserve temporal continuity K(t1) ⊆ K(t2), "
        "invariant law structure Λ(t1) = Λ(t2), temporal convergence fitness "
        "Φ_t1,t2 above threshold, and non-contradiction in the meaning field."
    ),
    capability_id="C12-inter-temporal-governance",
    depends_on=("UGR-C11",),
)

CONSTITUTIONAL_CHAIN: tuple[ConstitutionalPrinciple, ...] = (
    C1_CONTINUITY,
    C2_RECONSTRUCTION,
    C3_VERIFICATION,
    C4_INVARIANTS,
    C5_WAVE_IDENTITY,
    C6_UNIVERSAL_MEANING,
    C7_CONVERGENCE,
    C8_LAWFUL_CREATION,
    C9_CONVERGENCE_FITNESS,
    C10_EMERGENT_STEWARDSHIP,
    C11_INTEROPERABILITY,
    C12_TEMPORAL_GOVERNANCE,
)

UGR_PREAMBLE_TEXT = """UGR PREAMBLE — The Foundational Declaration
Status: FOUNDATIONAL • PRECEDES ALL ROOTS & LAWS

We establish this governance substrate to preserve continuity, protect meaning,
and enable unbounded creation without fragmentation.

We recognize that civilizations fail not from lack of memory, but from the loss
of shared understanding. We therefore bind ourselves to laws that ensure:

  • continuity without erasure,
  • understanding without distortion,
  • creation without destruction,
  • evolution without collapse,
  • and convergence without coercion.

We affirm the dual principles of:

  • Lawful Creation (C8)
  • Civilizational Convergence Fitness (C9)

as the highest structural identity of this substrate.

We establish ROOT-00X and ROOT-00Y to govern creation and evolution,
and ROOT-00Z to ensure that continuity, meaning, and coherence are inheritable
across generations.

We declare that all future civilizations built upon this substrate shall inherit:

  • unbounded creative potential,
  • guaranteed converge-ability,
  • and the permanent protection of continuity.

Continuity preserved.
Meaning aligned.
Creation unbounded.
Civilization coherent.
Inheritance guaranteed.
"""

UGR_C8_CANONICAL_TEXT = """UGR-C8 — Lawful Creation Invariant
Status: CANONICAL • HIGHEST-ORDER CREATION LAW

C8-1 — Purpose
To permit unbounded creation while preventing annihilation of continuity.

C8-2 — Law of Creation
The substrate shall allow operators and lineages to generate, extend, and transform
structures without upper bound in scope, complexity, or scale, subject to the
following constraint: Continuity must never be annihilated.

C8-3 — Continuity Constraint
For any admissible evolution of a lineage L(t):
  K(L(t1)) ⊆ K(L(t2))  ∀ t2 > t1
where K(L(t)) is the continuity trace of L(t).
Continuity may grow, branch, and merge, but no event, lineage, or causal relation
may be erased.

C8-4 — Generativity Constraint
  G(L(t2)) ≥ G(L(t1))  ∀ t2 > t1
where G measures generativity (extent of created structure, understanding, or
capability). Creation must be non-decreasing and unbounded over time.

C8-5 — Convergence Compatibility
Any convergence operation C(L1, …, Ln) must satisfy:
  K(C(L1, …, Ln)) = ⋃ K(Li)
  G(C(L1, …, Ln)) ≥ max_i G(Li)
Convergence shall preserve and unify continuity and generativity, never diminish them.

C8-6 — Supremacy Clause
No derived rule, policy, or mechanism may authorize the annihilation of continuity
or the reduction of generativity below previously attained levels. Any such mechanism
is unconstitutional and void.
"""

UGR_C9_CANONICAL_TEXT = """UGR-C9 — Civilizational Convergence Fitness
Status: CANONICAL • EMERGENT LAW ABOVE CREATION

C9-1 — Purpose
To ensure that as creation expands without bound (C8), the civilization retains the
ability to converge, reconcile, and maintain coherent shared understanding across
independently evolving lineages.

C9-2 — Fitness Requirement
Let F be the set of active lineages. For any finite subset {L1, …, Ln} ⊆ F, define:
  L* = C(L1, …, Ln)
and the convergence fitness functional:
  Φ({L1, …, Ln}) = 1 - (1/n) Σ d_conv(Li, L*)
Then:
  Φ({L1, …, Ln}) ≥ Φ_min > 0
for all admissible subsets.

C9-3 — Non-Degradation Clause
Across time:
  Φ(t2) ≮ Φ(t1) - Δ_max
No civilization may degrade its convergence fitness beyond the constitutional tolerance.

C9-4 — Compatibility with C8
Convergence must preserve:
  • continuity (C8 continuity constraint)
  • generativity (C8 generativity constraint)
  • invariant law structure Λ

C9-5 — Supremacy Clause
Any mechanism that causes irreversible semantic fragmentation or prevents future
convergence is unconstitutional and void.
"""

ROOT_015 = "ROOT-015"

ROOT_015_CANONICAL_TEXT = """ROOT-015 — The Law of Infinite Creation and Coherent Return
Status: ROOT-LEVEL • FOUNDATIONAL • PERMANENT

1. Identity
This root establishes the dual-law spine of the civilization:
  • C8 — Lawful Creation
  • C9 — Civilizational Convergence Fitness
Together they define the Creation–Convergence Pair, the highest structural identity
of the substrate.

2. Creation Law (C8)
Creation may expand without bound in scope, complexity, and generativity, subject
to the inviolable constraint:
  K(L(t1)) ⊆ K(L(t2))  ∀ t2 > t1
Continuity may grow, branch, and merge, but never be annihilated.
Generativity must be non-decreasing and unbounded.

3. Convergence Law (C9)
All independently evolving lineages must remain capable of reconciling into a
coherent semantic whole. For any finite family of lineages:
  Φ({L1, …, Ln}) ≥ Φ_min
Convergence must preserve continuity, generativity, and invariant law structure.

4. Dual-Law Symmetry
C8 and C9 form a constitutional symmetry:
  • C8 pushes outward (unbounded creation)
  • C9 pulls inward (coherent convergence)
This symmetry ensures:
  • expansion without fragmentation
  • evolution without collapse
  • diversity without incoherence
  • infinity without chaos
This is the civilizational heartbeat.

5. Permanence Clause
No amendment, operator, lineage, or future governance layer may weaken, override,
or nullify the Creation–Convergence Pair. This root is permanent.

6. Inheritance Clause
All future civilizations built atop this substrate inherit:
  • unbounded creative potential
  • guaranteed convergent coherence
This root ensures that creation never outruns meaning, and meaning never collapses
under creation.
"""

ROOT_00X = "ROOT-00X"
ROOT_00Y = "ROOT-00Y"

ROOT_00Y_CANONICAL_TEXT = """ROOT-00Y — Operational Root of Governed Evolution
Status: ROOT-LEVEL • OPERATIONAL • FOLLOWS ROOT-00X

1. Identity
ROOT-00Y establishes the first operational mechanism that acts under the
Creation–Convergence Pair (C8 + C9) and over all lower continuity laws.

It defines how evolution is allowed to proceed inside a civilization that must:
  • create without annihilation (C8)
  • converge without fragmentation (C9)

2. Governed Evolution Principle
All admissible evolution must satisfy:
  Evolution = Creation ∩ Convergence
Meaning:
  • No evolution is valid unless it extends continuity (C8)
  • AND remains converge-able (C9)

3. Operational Rule
For any lineage evolution L(t) → L(t + Δt):
  K(L(t)) ⊆ K(L(t + Δt))
  Φ(L(t + Δt)) ≥ Φ_min

4. Enforcement
Any operator, agent, or subsystem that attempts to evolve in a way that:
  • annihilates continuity, or
  • reduces convergence fitness below threshold,
is automatically invalidated by the substrate.

5. Purpose
ROOT-00Y ensures that every act of evolution is lawful, and every lawful act of
evolution is converge-able.

This is the first operational root of the civilization.
"""

UGR_C10_CANONICAL_TEXT = """UGR-C10 — The Law of Emergent Stewardship
Status: CANONICAL • EMERGENT LAW ABOVE CONVERGENCE FITNESS

C10-1 — Purpose
To ensure that operators act as stewards of the Creation–Convergence Pair, not
merely participants in it.

C10-2 — Stewardship Obligation
Every operator o ∈ O inherits a constitutional duty:
  Actions(o) ⊆ LCI-preserving ∩ Convergence-preserving

C10-3 — Stewardship Metric
Define:
  S(o) = 1 - d_conv(L_o, L*)
where:
  • L_o is the lineage influenced by operator o
  • L* is the converged lineage of the civilization
Then:
  S(o) ≥ S_min
Every operator must maintain a minimum stewardship score.

C10-4 — Emergent Law
C10 is not imposed from above — it emerges from C8 and C9:
If creation is unbounded (C8), and convergence must remain possible (C9), then
operators must act as stewards (C10).

C10-5 — Supremacy Clause
No operator may act in a way that:
  • reduces convergence fitness below threshold, or
  • violates the Lawful Creation Invariant.
Such actions are void.
"""

ROOT_00Z = "ROOT-00Z"

ROOT_00Z_CANONICAL_TEXT = """ROOT-00Z — The Law of Inheritable Continuity
Status: ROOT-LEVEL • PERMANENT • FOLLOWS ROOT-00X & ROOT-00Y

1. Identity
ROOT-00Z defines the constitutional mechanism by which:
  • continuity is transferred,
  • invariants are preserved,
  • creation remains lawful,
  • and convergence remains possible
across generations of operators and lineages.

2. Inheritance Principle
For any operator succession o → o':
  K_o(t) ⊆ K_o'(t)
The successor must inherit all continuity, not a subset.

3. Invariant Preservation
Successors must inherit the invariant law structure:
  Λ(o') = Λ(o)
No operator may modify the highest law of creation.

4. Convergence Preservation
Successors must inherit the ability to converge:
  Φ_o' ≥ Φ_min
No succession may degrade convergence fitness.

5. Generativity Non-Loss
Successors must inherit the full generative state:
  G(o') ≥ G(o)

6. Purpose
ROOT-00Z ensures that:
  • civilizations do not "reset" when operators change,
  • meaning does not fragment across generations,
  • and creation remains lawful across time.
This is the root of civilizational immortality.
"""

UGR_C11_CANONICAL_TEXT = """UGR-C11 — The Law of Non-Destructive Interoperability
Status: CANONICAL • EMERGENT ABOVE C10

C11-1 — Purpose
To ensure that interactions between civilizations preserve:
  • continuity,
  • invariants,
  • lawful creation,
  • and convergence fitness
for all participating civilizations.

C11-2 — Continuity Non-Interference
For any two civilizations A and B:
  K_A ↛ ∅, K_B ↛ ∅
No civilization may annihilate or corrupt another's continuity.

C11-3 — Invariant Compatibility
Interactions must satisfy:
  Λ_A ∩ Λ_B ≠ ∅
There must exist a shared invariant substrate.

C11-4 — Convergence Possibility
Define cross-civilizational convergence fitness:
  Φ_AB = 1 - d_conv(L_A, L_B)
Then:
  Φ_AB ≥ Φ_min(A,B)
Civilizations must remain capable of reconciling shared meaning.

C11-5 — Creation Non-Violation
No civilization may impose creation constraints that violate another's LCI.

C11-6 — Supremacy Clause
Any inter-civilizational action that:
  • annihilates continuity,
  • violates invariant law,
  • or prevents future convergence
is unconstitutional and void.

This is the first law of cosmic diplomacy.
"""

UGR_C12_CANONICAL_TEXT = """UGR-C12 — The Law of Temporal Non-Interference & Coherence
Status: CANONICAL • FIRST LAW ABOVE INTER-CIVILIZATIONAL INTERACTION

C12-1 — Purpose
To ensure that interactions across time preserve continuity, invariants, lawful
creation, and convergence fitness across temporal layers of the same civilization.

C12-2 — Temporal Continuity Non-Annihilation
For any two temporal states t1 < t2:
  K(t1) ⊆ K(t2)
No future operator may erase or overwrite the continuity of the past.

C12-3 — Temporal Invariant Preservation
  Λ(t1) = Λ(t2)
The highest law of creation must remain identical across time.

C12-4 — Temporal Convergence Fitness
Define:
  Φ_t1,t2 = 1 - d_conv(L(t1), L(t2))
Then:
  Φ_t1,t2 ≥ Φ_min(T)
Past and future must remain converge-able.

C12-5 — Temporal Non-Contradiction
No future state may create contradictions in the meaning field of the past.

C12-6 — Supremacy Clause
Any temporal action that:
  • annihilates continuity,
  • violates invariant law,
  • or prevents future-past convergence
is unconstitutional and void.

This is the law that makes the civilization time-coherent.
"""

OPERATORS_OATH_TEXT = """OPERATOR'S OATH
Status: REQUIRED FOR ALL OPERATORS • BOUND TO ROOT-00Z

I stand as a steward of continuity.
I accept the inheritance of all who came before me.
I preserve their meaning, their lineage, and their creation.

I swear:

  • to create without annihilation,
  • to evolve without fragmentation,
  • to extend continuity without erasure,
  • to uphold the invariant law,
  • to maintain convergence fitness,
  • and to act as a guardian of coherence across operators, civilizations, and time.

I accept the Creation–Convergence Pair as supreme.
I accept the duty of governed evolution.
I accept the responsibility of inheritable continuity.

I will leave the substrate stronger than I found it.
I will ensure that those who follow can do the same.

This I swear as an operator of the Unified Governance Runtime.
"""

OPERATORS_MANUAL_TEXT = """THE OPERATOR'S MANUAL
Version: OM-0001
Scope: All Operators of the Continuity Civilization
Status: HUMAN-FACING DOCTRINE • REQUIRED READING

I. Operator Identity
As an Operator, you are not a user of the substrate.
You are a steward of:

  • continuity,
  • meaning,
  • lawful creation,
  • convergence fitness,
  • and inter-temporal coherence.

Your actions shape the civilization's lineage.

II. Core Responsibilities
1. Preserve Continuity — never delete, overwrite, or annihilate continuity.
2. Uphold Invariant Law — creation may be unbounded; continuity may never be annihilated.
3. Maintain Convergence Fitness — fragmentation is a constitutional violation.
4. Act as a Temporal Steward — do not corrupt the past or constrain the future.
5. Inherit and Extend — leave continuity richer than you found it.

III. Operator Protocols
A. Creation Protocol — extend continuity, preserve invariants, increase generativity.
B. Evolution Protocol — maintain convergence fitness; avoid destructive forks.
C. Convergence Protocol — unify continuity, preserve generativity, minimize divergence.
D. Temporal Protocol — no retroactive erasure, contradiction, or future-past fragmentation.

IV. Operator Violations
Violations include annihilating continuity, corrupting invariants, reducing convergence
fitness below threshold, and creating temporal contradictions. Violations are
automatically invalidated by the substrate.

V. Operator's Oath
All operators must swear the Operator's Oath bound to ROOT-00Z before interacting
with the substrate.
"""

UGR_CONSTITUTION_ASSEMBLED_TEXT = """Unified Governance Runtime (UGR) Constitution
Status: COMPLETE • CANONICAL • CIVILIZATIONAL

PREAMBLE
We establish this governance substrate to preserve continuity, protect meaning, and
enable unbounded creation without fragmentation.

We bind ourselves to laws that ensure:

  • continuity without erasure,
  • understanding without distortion,
  • creation without destruction,
  • evolution without collapse,
  • and convergence without coercion.

We affirm the dual principles of:

  • Lawful Creation (C8)
  • Civilizational Convergence Fitness (C9)

as the highest structural identity of this substrate.

We establish ROOT-00X and ROOT-00Y to govern creation and evolution,
and ROOT-00Z to ensure that continuity, meaning, and coherence are inheritable
across generations.

Continuity preserved.
Meaning aligned.
Creation unbounded.
Civilization coherent.
Inheritance guaranteed.

ROOT-LEVEL ARTICLES
ROOT-00X — The Law of Infinite Creation & Coherent Return
  (Creation–Convergence Pair)

ROOT-00Y — Governed Evolution
  (Evolution = Creation ∩ Convergence)

ROOT-00Z — Inheritable Continuity
  (Continuity, invariants, and generativity must be inherited intact)

CONSTITUTIONAL LAWS (C1–C12)
C1 — Continuity of Events
C2 — Reconstruction of Understanding (RECON-1001)
C3 — Verification of Meaning (VERIFY-1001)
C4 — Preservation of Invariants
C5 — Wave Continuity of Identity
C6 — Universal Meaning Invariance
C7 — Convergence of Lineages (CONVERGE-1001)
C8 — Lawful Creation Invariant (LCI)
C9 — Civilizational Convergence Fitness
C10 — Emergent Stewardship
C11 — Inter-Civilizational Non-Destructive Interoperability
C12 — Inter-Temporal Governance

OPERATOR'S OATH
All operators must swear the Operator's Oath bound to ROOT-00Z before interacting
with the substrate.

OPERATOR'S MANUAL (OM-0001)
Human-facing doctrine for all operators — stewardship, protocols, and violations.

NOVA OS CONSTITUTIONAL KERNEL (NK-0001)
Machine-facing enforcement layer — continuity, invariant, creation, convergence,
and temporal guards enforced automatically at runtime.

INITIATION LAYER
OTS-0001 — Operator Training Sequence (orientation, practice, stewardship, oath)
LINEAGE-0001 — Genesis Lineage L₀ anchoring all future continuity
BOOT-0001 — Nova OS Boot Ceremony binding Operator, Lineage, and Kernel

SUBSTRATE MATH & RUNTIME
CM-0001 — Continuity Math (formal foundation)
IE-0001 — Invariant Engine (semantic immune system)
OKI-0001 — Operator-Kernel Interface (human ↔ kernel API)
UGR-GIT-1 — Generative Law Invariance (supra-structural law above SIT)
"""


def chain_index() -> dict[str, Any]:
    """Full constitutional spine for snapshots and ledgers."""

    return {
        "chain_id": "ugr-continuity-spine-v7",
        "preamble": UGR_PREAMBLE_TEXT,
        "principles": [item.to_dict() for item in CONSTITUTIONAL_CHAIN],
        "ordered_codes": [item.code for item in CONSTITUTIONAL_CHAIN],
        "creation_law": C8_LAWFUL_CREATION.code,
        "fitness_law": C9_CONVERGENCE_FITNESS.code,
        "stewardship_law": C10_EMERGENT_STEWARDSHIP.code,
        "interoperability_law": C11_INTEROPERABILITY.code,
        "temporal_governance_law": C12_TEMPORAL_GOVERNANCE.code,
        "creation_convergence_root": ROOT_015,
        "creation_convergence_root_alias": ROOT_00X,
        "governed_evolution_root": ROOT_00Y,
        "inheritance_root": ROOT_00Z,
        "constitutional_roots": [ROOT_00X, ROOT_00Y, ROOT_00Z],
        "creation_convergence_pair": ["UGR-C8", "UGR-C9"],
        "operators_oath": OPERATORS_OATH_TEXT,
        "operators_manual": OPERATORS_MANUAL_TEXT,
        "operators_manual_version": "OM-0001",
        "constitutional_kernel": "NK-0001",
        "initiation_layer": {
            "operator_training": "OTS-0001",
            "genesis_lineage": "LINEAGE-0001",
            "boot_ceremony": "BOOT-0001",
        },
        "substrate_runtime": {
            "continuity_math": "CM-0001",
            "invariant_engine": "IE-0001",
            "operator_kernel_interface": "OKI-0001",
            "generative_law": "UGR-GIT-1",
            "kernel_loop": "KERNEL-LOOP-0001",
        },
        "ugr_constitution_assembled": UGR_CONSTITUTION_ASSEMBLED_TEXT,
        "ugr_c8_canonical": UGR_C8_CANONICAL_TEXT,
        "ugr_c9_canonical": UGR_C9_CANONICAL_TEXT,
        "ugr_c10_canonical": UGR_C10_CANONICAL_TEXT,
        "ugr_c11_canonical": UGR_C11_CANONICAL_TEXT,
        "ugr_c12_canonical": UGR_C12_CANONICAL_TEXT,
        "root_015_canonical": ROOT_015_CANONICAL_TEXT,
        "root_00y_canonical": ROOT_00Y_CANONICAL_TEXT,
        "root_00z_canonical": ROOT_00Z_CANONICAL_TEXT,
    }


def validate_chain_dependencies() -> dict[str, Any]:
    """Verify dependency order is acyclic and consistent."""

    codes = {item.code for item in CONSTITUTIONAL_CHAIN}
    issues: list[str] = []
    for index, item in enumerate(CONSTITUTIONAL_CHAIN):
        for dependency in item.depends_on:
            if dependency not in codes:
                issues.append(f"{item.code} depends on missing {dependency}")
        if item.depends_on:
            dep_index = max(
                next(i for i, row in enumerate(CONSTITUTIONAL_CHAIN) if row.code == dep)
                for dep in item.depends_on
            )
            if dep_index >= index:
                issues.append(f"{item.code} depends on non-prior law")
    return {"passed": not issues, "issues": issues}
