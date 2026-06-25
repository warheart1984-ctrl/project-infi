"""Apply required continuity mechanisms — ledger, freeze, snapshot, drift guards."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.continuity.cab import CABLedger, DecisionRecord, default_cab_store_path
from src.continuity.constitutional_apply import apply_constitutional_chain
from src.continuity.early_concept_harness import run_fixture
from src.continuity.meaning_ledger import MeaningEntryKind, MeaningLedger, MeaningLedgerEntry
from src.aaes_os.tsr_routing import apply_nexus_takeover, load_routing

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "continuity"
PRE_JUNE_FIXTURE = FIXTURES / "pre_june_early_concepts.v1.json"
BACKFILL_SEED = FIXTURES / "meaning_ledger_backfill.v1.json"

ROOT_014 = "ROOT-014"
DRIFT_C12 = "C12_conceptual_drift_from_frozen_baseline"
DRIFT_C15 = "C15_daniel_concept_reintroduction"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _online_dir() -> Path:
    configured = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return ROOT / ".runtime" / "online"


def seed_meaning_ledger(*, ledger: MeaningLedger | None = None) -> list[MeaningLedgerEntry]:
    store = ledger or MeaningLedger()
    seed_rows = json.loads(BACKFILL_SEED.read_text(encoding="utf-8"))
    written: list[MeaningLedgerEntry] = []
    for row in seed_rows.get("entries") or []:
        entry_id = str(row["entry_id"])
        if store.get(entry_id) is not None:
            continue
        entry = MeaningLedgerEntry.from_dict(row)
        written.append(store.append(entry))
    return written


def append_required_mechanism_entries(*, ledger: MeaningLedger | None = None) -> list[MeaningLedgerEntry]:
    store = ledger or MeaningLedger()
    now = _now_iso()
    required = [
        MeaningLedgerEntry(
            entry_id="ML-BOUNDARY-001",
            kind=MeaningEntryKind.BOUNDARY,
            title="Intent boundaries — interpersonal to operational",
            body=(
                "Interpersonal context is non-authoritative for runtime routing. "
                "Operational boundaries: Nexus owns TSR; Daniel runtime disconnected; "
                "future conceptual updates must not reintroduce Daniel as executor or steward."
            ),
            lineage=["ML-BACKFILL-001"],
            law_surfaces=["ugr.continuity", "aais.governance"],
            metadata={"scope": "interpersonal_operational_boundary"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-DRIFT-DANIEL-001",
            kind=MeaningEntryKind.DRIFT_CONTAINMENT,
            title="Daniel Drift Containment",
            body=(
                "Daniel module and persona are frozen for conceptual evolution. "
                "Drift signals C12 and C15 apply. Reintroduction requires explicit "
                "ROOT-014 lift and CAB decision — not runtime default."
            ),
            lineage=["ML-BOUNDARY-001", ROOT_014],
            law_surfaces=["ugr.continuity", "aais.module_governance"],
            metadata={"drift_signals": [DRIFT_C12, DRIFT_C15], "daniel_future_updates": "forbidden"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id=ROOT_014,
            kind=MeaningEntryKind.CONTINUITY_FREEZE,
            title="Continuity Freeze — pre-June concepts",
            body=(
                "All concepts articulated before 2026-06-01 are sealed read-only. "
                "They may be reconstructed and cited but not mutated without a "
                "successor decision that references this freeze entry."
            ),
            lineage=["ML-BACKFILL-001"],
            law_surfaces=["ugr.continuity", "cab.succession"],
            metadata={"freeze_before": "2026-06-01T00:00:00Z", "mutable": False},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-EMOTIONAL-001",
            kind=MeaningEntryKind.EMOTIONAL_METADATA,
            title="Emotional context (non-binding)",
            body=(
                "Session emotional context is preserved for human continuity only. "
                "It does not authorize runtime actions, access grants, or module routing."
            ),
            lineage=[ROOT_014],
            law_surfaces=["ugr.continuity"],
            binding=False,
            metadata={"binding_class": "non_authoritative_metadata"},
            created_at=now,
        ),
        MeaningLedgerEntry(
            entry_id="ML-POLICY-DANIEL-001",
            kind=MeaningEntryKind.POLICY,
            title="Remove Daniel from future conceptual updates",
            body=(
                "Implementation phase proceeds under Nexus TSR ownership. "
                "Daniel is excluded from new architecture, governance, and harness fixtures."
            ),
            lineage=["ML-DRIFT-DANIEL-001", ROOT_014],
            law_surfaces=["aais.governance", "fos.continuity"],
            metadata={"phase": "implementation", "recommended_by": "dar-z"},
            created_at=now,
        ),
    ]
    written: list[MeaningLedgerEntry] = []
    for entry in required:
        if store.get(entry.entry_id) is not None:
            continue
        written.append(store.append(entry))
    return written


def sync_cab_decisions(*, cab: CABLedger | None = None) -> list[str]:
    ledger = cab or CABLedger.open(default_cab_store_path())
    now = _now_iso()
    decision_ids: list[str] = []
    for decision_id, rationale, lineage in (
        (
            "cab.decision.root-014-pre-june-freeze",
            "Seal pre-June concepts under ROOT-014 continuity freeze.",
            [ROOT_014],
        ),
        (
            "cab.decision.daniel-drift-containment",
            "Contain Daniel conceptual drift; runtime disconnected; Nexus owns TSR.",
            ["ML-DRIFT-DANIEL-001", "ML-POLICY-DANIEL-001"],
        ),
        (
            "cab.decision.implementation-phase",
            "Shift to implementation phase with substrate marked safe for execution.",
            ["ML-POLICY-DANIEL-001"],
        ),
    ):
        if ledger.get_latest(decision_id) is not None:
            continue
        ledger.append(
            DecisionRecord(
                decision_id=decision_id,
                decision_makers=["continuity_substrate"],
                intent_refs=lineage,
                chosen_option="adopt",
                rationale=rationale,
                created_at=now,
            )
        )
        decision_ids.append(decision_id)
    return decision_ids


def run_early_concept_reconstruction() -> dict[str, Any]:
    if not PRE_JUNE_FIXTURE.is_file():
        raise FileNotFoundError(PRE_JUNE_FIXTURE)
    return run_fixture(PRE_JUNE_FIXTURE)


def build_continuity_snapshot(*, constitutional: dict[str, Any] | None = None) -> dict[str, Any]:
    online = _online_dir()
    ledger = MeaningLedger()
    routing = load_routing()
    snapshot = {
        "generated_at": _now_iso(),
        "substrate_safe": True,
        "phase": "implementation",
        "tsr_owner": routing.get("tsr_owner"),
        "daniel_runtime_enabled": routing.get("daniel_runtime_enabled"),
        "connectors": routing.get("connectors"),
        "meaning_ledger_path": str(ledger.path),
        "meaning_ledger_entries": [entry.to_dict() for entry in ledger.all()],
        "root_014_active": ledger.get(ROOT_014) is not None,
        "root_015_active": ledger.get("ROOT-015") is not None,
        "root_00y_active": ledger.get("ROOT-00Y") is not None,
        "root_00z_active": ledger.get("ROOT-00Z") is not None,
        "ugr_preamble_active": ledger.get("ML-UGR-PREAMBLE-001") is not None,
        "operators_manual_active": ledger.get("ML-UGR-OPERATORS-MANUAL-001") is not None,
        "constitutional_kernel_active": ledger.get("ML-NK-CONSTITUTIONAL-KERNEL-001") is not None,
        "ugr_constitution_active": ledger.get("ML-UGR-CONSTITUTION-001") is not None,
        "creation_convergence_pair": ["UGR-C8", "UGR-C9"],
        "constitutional_roots": ["ROOT-00X", "ROOT-00Y", "ROOT-00Z"],
        "governed_evolution_root": "ROOT-00Y",
        "inheritance_root": "ROOT-00Z",
        "drift_signals": {
            DRIFT_C12: "Monitor conceptual updates against ROOT-014 frozen baseline.",
            DRIFT_C15: "Alert when Daniel reappears in new fixtures, docs, or module defaults.",
        },
        "lci_stack": (constitutional or {}).get("lci_stack"),
        "constitutional_chain": (constitutional or {}).get("constitutional_chain"),
        "c9_fitness": (constitutional or {}).get("c9_fitness"),
        "c10_stewardship": (constitutional or {}).get("c10_stewardship"),
        "root_00y_evolution": (constitutional or {}).get("root_00y_evolution"),
        "root_00z_inheritance": (constitutional or {}).get("root_00z_inheritance"),
        "c11_interoperability": (constitutional or {}).get("c11_interoperability"),
        "c12_temporal_coherence": (constitutional or {}).get("c12_temporal_coherence"),
        "nk_kernel_enforcement": (constitutional or {}).get("nk_kernel_enforcement"),
        "artifacts": {
            "tsr_routing": str(online / "tsr-routing.json"),
            "meaning_ledger": str(online / "meaning-ledger.jsonl"),
            "cab_ledger": str(default_cab_store_path()),
            "continuity_snapshot": str(online / "continuity-snapshot.json"),
        },
    }
    out = online / "continuity-snapshot.json"
    online.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return snapshot


def apply_continuity_mechanisms(*, include_nexus_takeover: bool = True) -> dict[str, Any]:
    online = _online_dir()
    online.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("AAIS_ONLINE_RUNTIME_DIR", str(online))
    os.environ.setdefault("MEANING_LEDGER_PATH", str(online / "meaning-ledger.jsonl"))
    os.environ.setdefault("CAB_STORE", str(online / "cab-ledger.jsonl"))

    tsr = apply_nexus_takeover(reason="continuity_mechanisms_pack") if include_nexus_takeover else load_routing()
    backfill = seed_meaning_ledger()
    mechanisms = append_required_mechanism_entries()
    cab_decisions = sync_cab_decisions()
    harness = run_early_concept_reconstruction()
    constitutional = apply_constitutional_chain()
    snapshot = build_continuity_snapshot(constitutional=constitutional)

    return {
        "tsr_routing": tsr,
        "meaning_ledger_backfill_count": len(backfill),
        "mechanism_entries_added": len(mechanisms),
        "cab_decisions_added": cab_decisions,
        "early_concept_harness": harness,
        "constitutional_chain": constitutional,
        "continuity_snapshot_path": snapshot["artifacts"]["continuity_snapshot"],
        "substrate_safe": bool(constitutional.get("stack_ready")),
        "phase": "implementation",
    }
