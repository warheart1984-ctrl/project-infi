"""UGR-PIT-1 — Proof Invariance Theory and sovereign selection fitness F(G)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

UGR_PIT_1_CANONICAL_TEXT = """UGR-PIT-1 — Proof Invariance Theory
Class: Constitutional Invariant
Purpose: Gate sovereign law selection via fitness F(G) backed by evidence and operator consensus.

Phi(G) = v_sel*F_sel + v_evidence*F_evidence + v_stability*F_stability + v_consensus*F_consensus
Only laws with Phi(G) >= Theta_PIT influence epoch commit and sovereign admission.
"""

PIT_1_CAPABILITY_ID = "UGR-PIT-1"
DEFAULT_THETA_PIT = 0.70


@dataclass
class PitComponents:
    F_sel: float
    F_evidence: float
    F_stability: float
    F_consensus: float

    def to_dict(self) -> dict[str, float]:
        return {
            "F_sel": round(self.F_sel, 6),
            "F_evidence": round(self.F_evidence, 6),
            "F_stability": round(self.F_stability, 6),
            "F_consensus": round(self.F_consensus, 6),
        }


@dataclass
class PitConfig:
    v_sel: float = 0.25
    v_evidence: float = 0.25
    v_stability: float = 0.25
    v_consensus: float = 0.25
    theta_pit: float = DEFAULT_THETA_PIT


@dataclass
class PITStrip:
    object_type: str
    object_id: str
    phi: float
    fitness_current: float
    selection_note: str
    evidence_coupling: str
    consensus_note: str
    components: PitComponents
    ready: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": self.object_type,
            "object_id": self.object_id,
            "phi": round(self.phi, 6),
            "fitness_current": round(self.fitness_current, 6),
            "selection_note": self.selection_note,
            "evidence_coupling": self.evidence_coupling,
            "consensus_note": self.consensus_note,
            "components": self.components.to_dict(),
            "ready": self.ready,
        }


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_phi(components: PitComponents, cfg: PitConfig | None = None) -> float:
    config = cfg or PitConfig()
    phi = (
        config.v_sel * components.F_sel
        + config.v_evidence * components.F_evidence
        + config.v_stability * components.F_stability
        + config.v_consensus * components.F_consensus
    )
    return clamp01(phi)


def components_from_law_pit(
    law_record: dict[str, Any],
    *,
    omega: float | None = None,
) -> PitComponents:
    fitness = float(
        (law_record.get("fitness") or {}).get("current")
        or law_record.get("current_fitness")
        or 0.0
    )
    thresholds = law_record.get("fitness") or {}
    admit = float(
        thresholds.get("thresholds", {}).get("admit")
        or law_record.get("admit_threshold")
        or 0.75
    )
    status = str(law_record.get("status") or "")

    f_sel = clamp01(fitness)
    f_evidence = clamp01(omega if omega is not None else 0.55 + 0.35 * fitness)
    f_stability = 0.92 if status == "sovereign" else clamp01(0.65 + 0.2 * fitness)
    f_consensus = clamp01(fitness / admit) if admit > 0 else clamp01(fitness)

    return PitComponents(
        F_sel=f_sel,
        F_evidence=f_evidence,
        F_stability=f_stability,
        F_consensus=f_consensus,
    )


def build_law_pit_strip(
    law_record: dict[str, Any],
    *,
    omega: float | None = None,
    cfg: PitConfig | None = None,
) -> PITStrip:
    config = cfg or PitConfig()
    law_id = str(law_record.get("law_id") or "")
    fitness = float(
        (law_record.get("fitness") or {}).get("current")
        or law_record.get("current_fitness")
        or 0.0
    )
    components = components_from_law_pit(law_record, omega=omega)
    phi = compute_phi(components, config)
    status = str(law_record.get("status") or "")

    return PITStrip(
        object_type="law",
        object_id=law_id,
        phi=phi,
        fitness_current=fitness,
        selection_note=(
            f"Sovereign selection F={fitness:.3f} — kernel admissible."
            if status == "sovereign"
            else f"Experimental F={fitness:.3f} — quarantine band active."
        ),
        evidence_coupling=(
            f"Evidence fitness Omega={omega:.3f} bound to law evaluations."
            if omega is not None
            else "Evidence coupling pending next evaluation cycle."
        ),
        consensus_note=(
            "Operator consensus above admit threshold."
            if components.F_consensus >= 1.0
            else "Consensus below admit threshold — steward override may apply."
        ),
        components=components,
        ready=phi >= config.theta_pit,
    )


def evaluate_law_pit(
    law_record: dict[str, Any],
    *,
    omega: float | None = None,
    cfg: PitConfig | None = None,
) -> dict[str, Any]:
    strip = build_law_pit_strip(law_record, omega=omega, cfg=cfg)
    status = "ok" if strip.phi >= (cfg or PitConfig()).theta_pit else "breach"
    return {"pit_strip": strip.to_dict(), "phi": strip.phi, "status": status}


def build_pit_health(
    *,
    law_store: Any | None = None,
    evidence_store: Any | None = None,
    cfg: PitConfig | None = None,
) -> dict[str, Any]:
    from src.continuity.evidence_ledger import EvidenceLedgerStore, bootstrap_evidence_ledger, evidence_id_for
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    laws = law_store or LawLedgerStore()
    evidence = evidence_store or EvidenceLedgerStore()
    config = cfg or PitConfig()
    bootstrap_law_ledger(laws)
    bootstrap_evidence_ledger(evidence)

    epoch = laws.get_current_epoch()
    objects: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    below_threshold: list[str] = []

    for law in laws.all_laws():
        law_dict = law.to_dict()
        evidence_id = evidence_id_for(law.law_id, epoch)
        ev = evidence.get_evidence(evidence_id)
        omega: float | None = None
        if ev is not None:
            from src.continuity.evidence_fitness import evaluate_evidence_fitness

            graph = evidence.get_lineage_graph(evidence_id)
            omega = evaluate_evidence_fitness(ev, graph=graph)["omega"]

        result = evaluate_law_pit(law_dict, omega=omega, cfg=config)
        status = result["status"]
        phi = result["phi"]
        objects.append(
            {
                "object_type": "law",
                "object_id": law.law_id,
                "phi": phi,
                "fitness": law.current_fitness,
                "status": status,
            }
        )
        if status == "breach":
            below_threshold.append(law.law_id)
            warnings.append({"code": "PIT-LOW", "object_id": law.law_id, "object_type": "law"})

    phi_values = [item["phi"] for item in objects]
    avg_phi = round(sum(phi_values) / len(phi_values), 6) if phi_values else 0.0
    fitness_values = [item["fitness"] for item in objects if item["fitness"] > 0]
    avg_fitness = round(sum(fitness_values) / len(fitness_values), 6) if fitness_values else 0.0

    return {
        "avg_phi": avg_phi,
        "avg_fitness": avg_fitness,
        "theta_pit": config.theta_pit,
        "objects": objects,
        "below_threshold": below_threshold,
        "warnings": warnings,
        "epoch_commit_blocked": len(below_threshold) > 0,
        "canonical": UGR_PIT_1_CANONICAL_TEXT.split("\n")[0],
    }


def run_pit_proof(
    *,
    law_store: Any | None = None,
    evidence_store: Any | None = None,
) -> dict[str, Any]:
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger, run_law_ledger_proof

    laws = law_store or LawLedgerStore()
    bootstrap_law_ledger(laws)
    law_proof = run_law_ledger_proof(store=laws)
    health = build_pit_health(law_store=laws, evidence_store=evidence_store)
    pit = next((item for item in health["objects"] if item["object_id"] == "PIT-1"), None)
    return {
        "capability_id": PIT_1_CAPABILITY_ID,
        "law_ledger_passed": law_proof.get("passed", False),
        "avg_phi": health["avg_phi"],
        "pit_phi": pit["phi"] if pit else None,
        "passed": law_proof.get("passed", False)
        and health["avg_phi"] >= PitConfig().theta_pit
        and pit is not None,
    }
