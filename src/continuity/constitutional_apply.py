"""Apply constitutional chain C1–C12, roots, preamble, oath, and fitness proofs."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dataclasses import replace

from src.continuity.constitutional_chain import (
    CONSTITUTIONAL_CHAIN,
    OPERATORS_MANUAL_TEXT,
    OPERATORS_OATH_TEXT,
    ROOT_00X,
    ROOT_00Y,
    ROOT_00Y_CANONICAL_TEXT,
    ROOT_00Z,
    ROOT_00Z_CANONICAL_TEXT,
    ROOT_015,
    ROOT_015_CANONICAL_TEXT,
    UGR_C10_CANONICAL_TEXT,
    UGR_C11_CANONICAL_TEXT,
    UGR_C12_CANONICAL_TEXT,
    UGR_CONSTITUTION_ASSEMBLED_TEXT,
    UGR_C8_CANONICAL_TEXT,
    UGR_C9_CANONICAL_TEXT,
    UGR_PREAMBLE_TEXT,
    chain_index,
    validate_chain_dependencies,
)
from src.continuity.convergence_algebra import (
    DEFAULT_DELTA_MAX,
    DEFAULT_PHI_MIN,
    convergence_fitness,
    fitness_within_tolerance,
)
from src.continuity.creation_operator import CreationOperator, SubstrateState
from src.continuity.governed_evolution import (
    DEFAULT_S_MIN,
    evaluate_stewardship,
    governed_evolution_admissible,
)
from src.continuity.inheritance import operator_state_from_lineage, validate_operator_succession
from src.continuity.inter_civilizational import Civilization, evaluate_interoperability
from src.continuity.boot_ceremony import BOOT_0001_CANONICAL_TEXT, run_boot_ceremony_proof
from src.continuity.constitutional_kernel import NK_0001_CANONICAL_TEXT, run_kernel_enforcement_proof
from src.continuity.continuity_math import CM_0001_CANONICAL_TEXT, run_continuity_math_proof
from src.continuity.generative_law import UGR_GIT_1_CANONICAL_TEXT, run_git_1_proof
from src.continuity.genesis_lineage import LINEAGE_0001_CANONICAL_TEXT, run_genesis_lineage_proof
from src.continuity.invariant_engine import IE_0001_CANONICAL_TEXT, run_invariant_engine_proof
from src.continuity.operator_kernel_interface import OKI_0001_CANONICAL_TEXT, run_operator_kernel_interface_proof
from src.continuity.operator_training import OTS_0001_CANONICAL_TEXT, run_ots_training_proof
from src.continuity.temporal_governance import TemporalState, evaluate_temporal_coherence
from src.continuity.law_ledger import LAW_LEDGER_0001_CANONICAL_TEXT, run_law_ledger_proof
from src.continuity.evidence_ledger import UGR_EIT_1_CANONICAL_TEXT, run_eit_proof
from src.continuity.comprehension_fitness import (
    UGR_CIT_1_CANONICAL_TEXT,
    UGR_CIT_2_CANONICAL_TEXT,
)
from src.continuity.comprehension_ledger import run_cit_proof
from src.continuity.meaning_fitness import UGR_MIT_1_CANONICAL_TEXT
from src.continuity.mit_ledger import run_mit_proof
from src.continuity.evidence_fitness import UGR_EIT_2_CANONICAL_TEXT, run_eit2_proof
from src.continuity.lci_stack import (
    LCI_FIXTURE,
    apply_lci_stack,
    lineages_from_fixture,
    load_lci_fixture,
)
from src.continuity.meaning_ledger import MeaningEntryKind, MeaningLedger, MeaningLedgerEntry


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "continuity"
CHAIN_FIXTURE = FIXTURES / "constitutional_chain.v1.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _online_dir() -> Path:
    configured = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return ROOT / ".runtime" / "online"


def _fitness_history_path() -> Path:
    override = os.environ.get("CONVERGENCE_FITNESS_HISTORY_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _online_dir() / "convergence-fitness-history.jsonl"


def load_fitness_history(path: Path | None = None) -> list[float]:
    target = path or _fitness_history_path()
    if not target.is_file():
        return []
    values: list[float] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        row = json.loads(cleaned)
        values.append(float(row["phi"]))
    return values


def append_fitness_observation(
    phi: float,
    *,
    path: Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target = path or _fitness_history_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "observed_at": _now_iso(),
        "phi": round(phi, 6),
        "metadata": dict(metadata or {}),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def append_constitutional_chain_entries(*, ledger: MeaningLedger | None = None) -> list[MeaningLedgerEntry]:
    store = ledger or MeaningLedger()
    now = _now_iso()
    index = chain_index()
    required = [
        MeaningLedgerEntry(
            entry_id="ML-UGR-PREAMBLE-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR Preamble — The Foundational Declaration",
            body=UGR_PREAMBLE_TEXT,
            lineage=["ML-BACKFILL-001"],
            law_surfaces=["ugr.preamble", "ugr.constitution", "ugr.continuity"],
            metadata={"status": "FOUNDATIONAL", "binds": "all operators and lineages"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-CHAIN-003",
            kind=MeaningEntryKind.POLICY,
            title="UGR Constitutional Continuity Chain C1–C12",
            body=(
                "Canonical spine: C1 continuity → C2 reconstruction → C3 verification → "
                "C4 invariants → C5 wave identity → C6 universal meaning → C7 convergence → "
                "C8 lawful creation → C9 civilizational convergence fitness → "
                "C10 emergent stewardship → C11 non-destructive interoperability → "
                "C12 inter-temporal governance."
            ),
            lineage=["ML-UGR-PREAMBLE-001", "ML-UGR-CHAIN-002"],
            law_surfaces=["ugr.continuity", "ugr.constitution"],
            metadata={"chain": index},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-CHAIN-002",
            kind=MeaningEntryKind.POLICY,
            title="UGR Constitutional Continuity Chain C1–C11",
            body=(
                "Canonical spine: C1 continuity → C2 reconstruction → C3 verification → "
                "C4 invariants → C5 wave identity → C6 universal meaning → C7 convergence → "
                "C8 lawful creation → C9 civilizational convergence fitness → "
                "C10 emergent stewardship → C11 non-destructive interoperability."
            ),
            lineage=["ML-UGR-PREAMBLE-001", "ML-UGR-CHAIN-001"],
            law_surfaces=["ugr.continuity", "ugr.constitution"],
            metadata={"chain": index, "superseded_by": "ML-UGR-CHAIN-003"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-CHAIN-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR Constitutional Continuity Chain C1–C10",
            body=(
                "Canonical spine: C1 continuity → C2 reconstruction → C3 verification → "
                "C4 invariants → C5 wave identity → C6 universal meaning → C7 convergence → "
                "C8 lawful creation → C9 civilizational convergence fitness → "
                "C10 emergent stewardship."
            ),
            lineage=["ML-UGR-PREAMBLE-001"],
            law_surfaces=["ugr.continuity", "ugr.constitution"],
            metadata={"chain": index, "superseded_by": "ML-UGR-CHAIN-002"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-C8-CANONICAL-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C8 — Lawful Creation Invariant (CANONICAL)",
            body=UGR_C8_CANONICAL_TEXT,
            lineage=["ML-UGR-CHAIN-003", "ML-UGR-C8-001"],
            law_surfaces=["UGR-C8", "ugr.continuity", "cab.succession"],
            metadata={"status": "CANONICAL", "supremacy_clause": "C8-6"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-C9-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C9 — Civilizational Convergence Fitness",
            body=(
                "For any admissible finite family of active lineages F, the substrate must "
                "support convergence with Φ(F) = 1 - (1/|F|) Σ d_conv(Li, C(F)) above Φ_min. "
                "Over time, Φ(t2) ≮ Φ(t1) - Δ_max."
            ),
            lineage=["ML-UGR-C8-CANONICAL-001"],
            law_surfaces=["UGR-C9", "ugr.continuity"],
            metadata={
                "phi_min_default": DEFAULT_PHI_MIN,
                "delta_max_default": DEFAULT_DELTA_MAX,
                "fitness_functional": "Phi",
                "depends_on": ["UGR-C8", "CONVERGE-1001"],
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-C9-CANONICAL-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C9 — Civilizational Convergence Fitness (CANONICAL)",
            body=UGR_C9_CANONICAL_TEXT,
            lineage=["ML-UGR-C9-001"],
            law_surfaces=["UGR-C9", "ugr.continuity"],
            metadata={"status": "CANONICAL", "supremacy_clause": "C9-5", "delta_max_default": DEFAULT_DELTA_MAX},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id=ROOT_015,
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="ROOT-015 — Law of Infinite Creation and Coherent Return",
            body=ROOT_015_CANONICAL_TEXT,
            lineage=["ML-UGR-C8-CANONICAL-001", "ML-UGR-C9-CANONICAL-001"],
            law_surfaces=[ROOT_015, ROOT_00X, "UGR-C8", "UGR-C9", "ugr.continuity", "cab.succession"],
            metadata={
                "status": "ROOT-LEVEL",
                "permanent": True,
                "designators": [ROOT_015, ROOT_00X],
                "creation_convergence_pair": ["UGR-C8", "UGR-C9"],
                "mutable": False,
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-C10-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C10 — Emergent Stewardship",
            body=(
                "Every operator inherits stewardship duty: Actions(o) ⊆ LCI-preserving ∩ "
                "Convergence-preserving. Stewardship metric S(o) = 1 - d_conv(L_o, L*) "
                "must remain ≥ S_min."
            ),
            lineage=["ML-UGR-C9-CANONICAL-001", ROOT_015],
            law_surfaces=["UGR-C10", "ugr.continuity"],
            metadata={
                "s_min_default": DEFAULT_S_MIN,
                "stewardship_functional": "S",
                "depends_on": ["UGR-C8", "UGR-C9"],
                "emergent_from": ["UGR-C8", "UGR-C9"],
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-C10-CANONICAL-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C10 — The Law of Emergent Stewardship (CANONICAL)",
            body=UGR_C10_CANONICAL_TEXT,
            lineage=["ML-UGR-C10-001"],
            law_surfaces=["UGR-C10", "ugr.continuity"],
            metadata={"status": "CANONICAL", "supremacy_clause": "C10-5", "s_min_default": DEFAULT_S_MIN},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id=ROOT_00Y,
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="ROOT-00Y — Operational Root of Governed Evolution",
            body=ROOT_00Y_CANONICAL_TEXT,
            lineage=[ROOT_015, "ML-UGR-C10-CANONICAL-001"],
            law_surfaces=[ROOT_00Y, ROOT_00X, "UGR-C8", "UGR-C9", "UGR-C10", "ugr.continuity"],
            metadata={
                "status": "ROOT-LEVEL",
                "operational": True,
                "follows": ROOT_00X,
                "follows_entry": ROOT_015,
                "governed_evolution": "Creation ∩ Convergence",
                "mutable": False,
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id=ROOT_00Z,
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="ROOT-00Z — The Law of Inheritable Continuity",
            body=ROOT_00Z_CANONICAL_TEXT,
            lineage=[ROOT_00Y, ROOT_015, "ML-UGR-C10-CANONICAL-001"],
            law_surfaces=[ROOT_00Z, ROOT_00Y, ROOT_00X, "UGR-C8", "UGR-C9", "UGR-C10", "ugr.continuity", "cab.succession"],
            metadata={
                "status": "ROOT-LEVEL",
                "permanent": True,
                "follows": [ROOT_00X, ROOT_00Y],
                "inheritance_principle": "K_o(t) ⊆ K_o'(t)",
                "mutable": False,
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-C11-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C11 — Non-Destructive Interoperability",
            body=(
                "Inter-civilizational interactions must preserve continuity for all "
                "participants, satisfy Λ_A ∩ Λ_B ≠ ∅, and maintain Φ_AB = 1 - d_conv(L_A, L_B) "
                "≥ Φ_min(A,B)."
            ),
            lineage=["ML-UGR-C10-CANONICAL-001", ROOT_00Z],
            law_surfaces=["UGR-C11", "ugr.continuity"],
            metadata={
                "phi_min_ab_default": DEFAULT_PHI_MIN,
                "depends_on": ["UGR-C10", "ROOT-00Z"],
                "emergent_from": ["UGR-C8", "UGR-C9", "UGR-C10"],
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-C11-CANONICAL-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C11 — The Law of Non-Destructive Interoperability (CANONICAL)",
            body=UGR_C11_CANONICAL_TEXT,
            lineage=["ML-UGR-C11-001"],
            law_surfaces=["UGR-C11", "ugr.continuity"],
            metadata={"status": "CANONICAL", "supremacy_clause": "C11-6"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-C12-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C12 — Inter-Temporal Governance",
            body=(
                "Temporal interactions must satisfy K(t1) ⊆ K(t2), Λ(t1) = Λ(t2), "
                "Φ_t1,t2 = 1 - d_conv(L(t1), L(t2)) ≥ Φ_min(T), and non-contradiction "
                "in the meaning field."
            ),
            lineage=["ML-UGR-C11-CANONICAL-001"],
            law_surfaces=["UGR-C12", "ugr.continuity"],
            metadata={
                "phi_min_t_default": DEFAULT_PHI_MIN,
                "depends_on": ["UGR-C11"],
                "temporal_analog_of": "UGR-C11",
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-C12-CANONICAL-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C12 — The Law of Temporal Non-Interference & Coherence (CANONICAL)",
            body=UGR_C12_CANONICAL_TEXT,
            lineage=["ML-UGR-C12-001"],
            law_surfaces=["UGR-C12", "ugr.continuity"],
            metadata={"status": "CANONICAL", "supremacy_clause": "C12-6"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-OPERATORS-OATH-001",
            kind=MeaningEntryKind.POLICY,
            title="Operator's Oath",
            body=OPERATORS_OATH_TEXT,
            lineage=[ROOT_00Z, "ML-UGR-C10-CANONICAL-001"],
            law_surfaces=["ugr.operators", "ugr.constitution", ROOT_00Z],
            metadata={
                "status": "REQUIRED",
                "binds": "all operators",
                "bound_to": ROOT_00Z,
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-OPERATORS-MANUAL-001",
            kind=MeaningEntryKind.POLICY,
            title="The Operator's Manual (OM-0001)",
            body=OPERATORS_MANUAL_TEXT,
            lineage=["ML-UGR-OPERATORS-OATH-001", ROOT_00Z],
            law_surfaces=["ugr.operators", "ugr.doctrine", "OM-0001"],
            metadata={
                "status": "REQUIRED",
                "version": "OM-0001",
                "audience": "human-facing",
                "binds": "all operators",
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-NK-CONSTITUTIONAL-KERNEL-001",
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="Nova OS Constitutional Kernel (NK-0001)",
            body=NK_0001_CANONICAL_TEXT,
            lineage=[
                "ML-UGR-C12-CANONICAL-001",
                ROOT_00Y,
                ROOT_00Z,
                "ML-UGR-OPERATORS-OATH-001",
            ],
            law_surfaces=["NK-0001", "nova.kernel", "ugr.continuity"],
            metadata={
                "status": "IMMUTABLE",
                "version": "NK-0001",
                "audience": "machine-facing",
                "guards": [
                    "continuity_guard",
                    "invariant_guard",
                    "creation_guard",
                    "convergence_guard",
                    "temporal_guard",
                ],
                "operators": ["Create", "Evolve", "Converge", "Inherit", "TemporalSync"],
                "mutable": False,
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-OTS-OPERATOR-TRAINING-001",
            kind=MeaningEntryKind.POLICY,
            title="Operator Training Sequence (OTS-0001)",
            body=OTS_0001_CANONICAL_TEXT,
            lineage=["ML-UGR-OPERATORS-MANUAL-001", "ML-UGR-OPERATORS-OATH-001", ROOT_00Z],
            law_surfaces=["OTS-0001", "ugr.operators", "ugr.training"],
            metadata={
                "status": "REQUIRED",
                "version": "OTS-0001",
                "phases": ["I", "II", "III", "IV"],
                "prerequisite_for": "substrate access",
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-LINEAGE-GENESIS-001",
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="The First Lineage (LINEAGE-0001)",
            body=LINEAGE_0001_CANONICAL_TEXT,
            lineage=[ROOT_015, ROOT_00Z, "ML-UGR-C8-CANONICAL-001"],
            law_surfaces=["LINEAGE-0001", "ugr.continuity", "ugr.genesis"],
            metadata={
                "status": "FOUNDATIONAL",
                "version": "LINEAGE-0001",
                "genesis_event": "E0-continuity-civilization-establishment",
                "founding_phi": 1.0,
                "mutable": False,
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-BOOT-CEREMONY-001",
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="Nova OS Boot Ceremony (BOOT-0001)",
            body=BOOT_0001_CANONICAL_TEXT,
            lineage=[
                "ML-LINEAGE-GENESIS-001",
                "ML-NK-CONSTITUTIONAL-KERNEL-001",
                "ML-OTS-OPERATOR-TRAINING-001",
                ROOT_00X,
                ROOT_00Y,
                ROOT_00Z,
            ],
            law_surfaces=["BOOT-0001", "nova.boot", "ugr.initiation"],
            metadata={
                "status": "REQUIRED",
                "version": "BOOT-0001",
                "steps": 6,
                "binds": ["operator", "lineage", "kernel"],
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-CM-CONTINUITY-MATH-001",
            kind=MeaningEntryKind.POLICY,
            title="Continuity Math (CM-0001)",
            body=CM_0001_CANONICAL_TEXT,
            lineage=["ML-UGR-CHAIN-003", "ML-NK-CONSTITUTIONAL-KERNEL-001"],
            law_surfaces=["CM-0001", "ugr.continuity", "ugr.math"],
            metadata={"status": "FOUNDATIONAL", "version": "CM-0001"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-IE-INVARIANT-ENGINE-001",
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="Invariant Engine (IE-0001)",
            body=IE_0001_CANONICAL_TEXT,
            lineage=["ML-CM-CONTINUITY-MATH-001", "ML-UGR-C8-CANONICAL-001"],
            law_surfaces=["IE-0001", "UGR-C8", "nova.invariants"],
            metadata={"status": "IMMUTABLE", "version": "IE-0001", "highest_law": "UGR-C8"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-OKI-OPERATOR-KERNEL-001",
            kind=MeaningEntryKind.POLICY,
            title="Operator-Kernel Interface (OKI-0001)",
            body=OKI_0001_CANONICAL_TEXT,
            lineage=["ML-NK-CONSTITUTIONAL-KERNEL-001", "ML-IE-INVARIANT-ENGINE-001"],
            law_surfaces=["OKI-0001", "nova.kernel", "ugr.operators"],
            metadata={"status": "REQUIRED", "version": "OKI-0001", "feedback": ["ACCEPTED", "REJECTED", "REPAIR_REQUIRED", "TEMPORAL_WARNING"]},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-GIT-1-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-GIT-1 — Generative Law Invariance",
            body=UGR_GIT_1_CANONICAL_TEXT,
            lineage=["ML-UGR-CHAIN-003", "ML-CM-CONTINUITY-MATH-001"],
            law_surfaces=["UGR-GIT-1", "ugr.generative_law", "ugr.continuity"],
            metadata={"status": "EMERGENT", "supra_structural": True, "above": "SIT"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-LAW-LEDGER-001",
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="Law Ledger (LAW-LEDGER-0001)",
            body=LAW_LEDGER_0001_CANONICAL_TEXT,
            lineage=["ML-IE-INVARIANT-ENGINE-001", "ML-UGR-GIT-1-001", ROOT_015],
            law_surfaces=["LAW-LEDGER", "SIT-1", "GIT-1", "PIT-1", "ugr.law_ledger"],
            metadata={
                "status": "SOVEREIGN",
                "version": "LAW-LEDGER-0001",
                "genesis_entry": "LAW-LEDGER-0000",
                "founding_laws": ["SIT-1", "GIT-1", "PIT-1"],
                "mutable": False,
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-EIT-1-001",
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="UGR-EIT-1 — Evidence Invariance Theory",
            body=UGR_EIT_1_CANONICAL_TEXT,
            lineage=["ML-LAW-LEDGER-001", "ML-IE-INVARIANT-ENGINE-001", "ML-UGR-GIT-1-001"],
            law_surfaces=["UGR-EIT-1", "EVIDENCE-LEDGER", "ugr.evidence", "ugr.continuity"],
            metadata={
                "status": "PROOF-LAYER",
                "version": "EIT-1",
                "genesis_entry": "EVIDENCE-LEDGER-0000",
                "binds_decisions": ["LAW_EVAL", "LAW_STATUS_CHANGE"],
                "mutable": False,
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-CIT-1-001",
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="UGR-CIT-1/2 — Comprehension Invariance and Drift Bounds",
            body=f"{UGR_CIT_1_CANONICAL_TEXT}\n\n{UGR_CIT_2_CANONICAL_TEXT}",
            lineage=["ML-LAW-LEDGER-001", "ML-UGR-EIT-1-001"],
            law_surfaces=["UGR-CIT-1", "UGR-CIT-2", "COMPREHENSION-LEDGER", "ugr.comprehension"],
            metadata={
                "status": "PROOF-LAYER",
                "version": "CIT-1/2",
                "genesis_entry": "COMPREHENSION-LEDGER-0000",
                "mutable": False,
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-MIT-1-001",
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="UGR-MIT-1 — Meaning Invariance Theory",
            body=UGR_MIT_1_CANONICAL_TEXT,
            lineage=["ML-LAW-LEDGER-001", "ML-UGR-CIT-1-001"],
            law_surfaces=["UGR-MIT-1", "MIT-LEDGER", "ugr.meaning"],
            metadata={
                "status": "PROOF-LAYER",
                "version": "MIT-1",
                "genesis_entry": "MIT-LEDGER-0000",
                "mutable": False,
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-EIT-2-001",
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="UGR-EIT-2 — Evidence Lineage Convergence",
            body=UGR_EIT_2_CANONICAL_TEXT,
            lineage=["ML-UGR-EIT-1-001", "ML-UGR-CIT-1-001"],
            law_surfaces=["UGR-EIT-2", "EVIDENCE-LEDGER", "ugr.evidence_fitness"],
            metadata={
                "status": "PROOF-LAYER",
                "version": "EIT-2",
                "fitness_functional": "Omega(E)",
                "mutable": False,
            },
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-CONSTITUTION-001",
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="Unified Governance Runtime (UGR) Constitution — Assembled",
            body=UGR_CONSTITUTION_ASSEMBLED_TEXT,
            lineage=[
                "ML-UGR-PREAMBLE-001",
                ROOT_015,
                ROOT_00Y,
                ROOT_00Z,
                "ML-UGR-CHAIN-003",
                "ML-UGR-OPERATORS-OATH-001",
                "ML-UGR-OPERATORS-MANUAL-001",
                "ML-NK-CONSTITUTIONAL-KERNEL-001",
                "ML-OTS-OPERATOR-TRAINING-001",
                "ML-LINEAGE-GENESIS-001",
                "ML-BOOT-CEREMONY-001",
                "ML-CM-CONTINUITY-MATH-001",
                "ML-IE-INVARIANT-ENGINE-001",
                "ML-OKI-OPERATOR-KERNEL-001",
                "ML-UGR-GIT-1-001",
                "ML-LAW-LEDGER-001",
                "ML-UGR-EIT-1-001",
                "ML-UGR-CIT-1-001",
                "ML-UGR-MIT-1-001",
                "ML-UGR-EIT-2-001",
            ],
            law_surfaces=["ugr.constitution", "ugr.continuity", "ugr.preamble"],
            metadata={
                "status": "COMPLETE",
                "canonical": True,
                "principle_count": len(CONSTITUTIONAL_CHAIN),
                "roots": [ROOT_00X, ROOT_00Y, ROOT_00Z],
            },
            created_at=now,
        ),
    ]
    written: list[MeaningLedgerEntry] = []
    for entry in required:
        if store.get(entry.entry_id) is not None:
            continue
        written.append(store.append(entry))
    return written


def run_c9_fitness_proof(
    *,
    phi_min: float = DEFAULT_PHI_MIN,
    delta_max: float = DEFAULT_DELTA_MAX,
) -> dict[str, Any]:
    fixture = load_lci_fixture(LCI_FIXTURE)
    lineages = lineages_from_fixture(fixture)
    epsilon = float(fixture.get("epsilon") or 0.35)
    fitness = convergence_fitness(lineages, epsilon=epsilon, phi_min=phi_min)
    history = load_fitness_history()
    tolerance_ok = fitness_within_tolerance(history, float(fitness["phi"]), delta_max=delta_max)
    return {
        **fitness,
        "delta_max": delta_max,
        "tolerance_ok": tolerance_ok,
        "history_length": len(history),
        "passed": bool(fitness["passed"]) and tolerance_ok,
    }


def run_c10_stewardship_proof(*, s_min: float = DEFAULT_S_MIN) -> dict[str, Any]:
    lineages = lineages_from_fixture(load_lci_fixture(LCI_FIXTURE))
    return evaluate_stewardship(lineages, s_min=s_min)


def run_root_00y_evolution_proof(*, phi_min: float = DEFAULT_PHI_MIN) -> dict[str, Any]:
    fixture = load_lci_fixture(LCI_FIXTURE)
    lineages = lineages_from_fixture(fixture)
    target = lineages[0]
    state = SubstrateState(state_id=f"gov-{target.lineage_id}", lineage=target)
    operator = CreationOperator()
    extended = operator.create(
        state,
        add_events=frozenset({f"gov-evolved-{target.lineage_id}"}),
        generativity_delta=1.0,
    )
    return governed_evolution_admissible(
        target,
        extended.lineage,
        lineages,
        phi_min=phi_min,
    )


def run_root_00z_inheritance_proof(*, phi_min: float = DEFAULT_PHI_MIN) -> dict[str, Any]:
    fixture = load_lci_fixture(LCI_FIXTURE)
    lineages = lineages_from_fixture(fixture)
    predecessor_lineage = lineages[0]
    predecessor = operator_state_from_lineage(predecessor_lineage)
    state = SubstrateState(state_id=f"inherit-{predecessor_lineage.lineage_id}", lineage=predecessor_lineage)
    operator = CreationOperator()
    extended = operator.create(
        state,
        add_events=frozenset({f"inherit-succession-{predecessor_lineage.lineage_id}"}),
        generativity_delta=0.5,
        attribute_patch={"successor": True},
    )
    successor = operator_state_from_lineage(
        replace(
            extended.lineage,
            metadata={
                **extended.lineage.metadata,
                "operator_id": f"{predecessor.operator_id}-successor",
            },
        )
    )
    return validate_operator_succession(predecessor, successor, lineages, phi_min=phi_min)


def run_c11_interoperability_proof(*, phi_min_ab: float = DEFAULT_PHI_MIN) -> dict[str, Any]:
    lineages = lineages_from_fixture(load_lci_fixture(LCI_FIXTURE))
    alpha, beta, gamma = lineages[0], lineages[1], lineages[2]
    shared_bridge = replace(
        alpha,
        lineage_id="L-shared-bridge",
        event_ids=alpha.event_ids | frozenset({"evt-converge-seed", "evt-nexus-handoff"}),
        generativity=max(alpha.generativity, beta.generativity),
        metadata={**alpha.metadata, "bridge": "inter-civilizational"},
    )
    civilization_a = Civilization(civilization_id="civ-governance", lineages=(alpha, beta))
    civilization_b = Civilization(civilization_id="civ-runtime-bridge", lineages=(shared_bridge, gamma))
    return evaluate_interoperability(civilization_a, civilization_b, phi_min_ab=phi_min_ab)


def run_c12_temporal_proof(*, phi_min_t: float = DEFAULT_PHI_MIN) -> dict[str, Any]:
    fixture = load_lci_fixture(LCI_FIXTURE)
    lineages = lineages_from_fixture(fixture)
    past_lineage = lineages[0]
    past = TemporalState(temporal_id="t1", lineage=past_lineage)
    state = SubstrateState(state_id=f"temporal-{past_lineage.lineage_id}", lineage=past_lineage)
    operator = CreationOperator()
    extended = operator.create(
        state,
        add_events=frozenset({f"temporal-layer-{past_lineage.lineage_id}"}),
        generativity_delta=0.5,
    )
    future = TemporalState(temporal_id="t2", lineage=extended.lineage)
    return evaluate_temporal_coherence(past, future, phi_min_t=phi_min_t)


def apply_constitutional_chain(*, ledger: MeaningLedger | None = None) -> dict[str, Any]:
    chain_validation = validate_chain_dependencies()
    lci_stack = apply_lci_stack(ledger=ledger)
    chain_entries = append_constitutional_chain_entries(ledger=ledger)
    fitness = run_c9_fitness_proof()
    stewardship = run_c10_stewardship_proof()
    governed_evolution = run_root_00y_evolution_proof()
    inheritance = run_root_00z_inheritance_proof()
    interoperability = run_c11_interoperability_proof()
    temporal = run_c12_temporal_proof()
    kernel = run_kernel_enforcement_proof()
    ots = run_ots_training_proof()
    genesis = run_genesis_lineage_proof()
    boot = run_boot_ceremony_proof()
    continuity_math = run_continuity_math_proof()
    invariant_engine = run_invariant_engine_proof()
    oki = run_operator_kernel_interface_proof()
    git_1 = run_git_1_proof()
    law_ledger = run_law_ledger_proof()
    eit_1 = run_eit_proof()
    cit_1 = run_cit_proof()
    mit_1 = run_mit_proof()
    eit_2 = run_eit2_proof()
    from src.continuity.nova_kernel_loop import run_genesis_kernel_loop_proof

    kernel_loop = run_genesis_kernel_loop_proof()
    append_fitness_observation(
        float(fitness["phi"]),
        metadata={
            "lineage_count": fitness.get("lineage_count"),
            "phi_min": fitness.get("phi_min"),
            "passed": fitness.get("passed"),
        },
    )
    index = chain_index()
    return {
        "constitutional_chain": index,
        "chain_validation": chain_validation,
        "chain_entries_added": len(chain_entries),
        "principle_count": len(CONSTITUTIONAL_CHAIN),
        "lci_stack": lci_stack,
        "c9_fitness": fitness,
        "c10_stewardship": stewardship,
        "root_00y_evolution": governed_evolution,
        "root_00z_inheritance": inheritance,
        "c11_interoperability": interoperability,
        "c12_temporal_coherence": temporal,
        "nk_kernel_enforcement": kernel,
        "ots_training": ots,
        "genesis_lineage": genesis,
        "boot_ceremony": boot,
        "continuity_math": continuity_math,
        "invariant_engine": invariant_engine,
        "operator_kernel_interface": oki,
        "generative_law_git_1": git_1,
        "law_ledger": law_ledger,
        "evidence_invariance_eit_1": eit_1,
        "comprehension_invariance_cit_1": cit_1,
        "meaning_invariance_mit_1": mit_1,
        "evidence_convergence_eit_2": eit_2,
        "genesis_kernel_loop": kernel_loop,
        "creation_convergence_root": ROOT_015,
        "creation_convergence_root_alias": ROOT_00X,
        "governed_evolution_root": ROOT_00Y,
        "inheritance_root": ROOT_00Z,
        "substrate_laws": index["ordered_codes"],
        "stack_ready": (
            chain_validation["passed"]
            and lci_stack.get("stack_ready", False)
            and fitness.get("passed", False)
            and stewardship.get("passed", False)
            and governed_evolution.get("passed", False)
            and inheritance.get("passed", False)
            and interoperability.get("passed", False)
            and temporal.get("passed", False)
            and kernel.get("passed", False)
            and ots.get("passed", False)
            and genesis.get("passed", False)
            and boot.get("passed", False)
            and continuity_math.get("passed", False)
            and invariant_engine.get("passed", False)
            and oki.get("passed", False)
            and git_1.get("passed", False)
            and law_ledger.get("passed", False)
            and eit_1.get("passed", False)
            and cit_1.get("passed", False)
            and mit_1.get("passed", False)
            and eit_2.get("passed", False)
            and kernel_loop.get("passed", False)
        ),
    }
