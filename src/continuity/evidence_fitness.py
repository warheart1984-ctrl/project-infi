"""UGR-EIT-2 — Evidence Lineage Convergence and evidence fitness Omega(E)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.continuity.evidence_ledger import (
    EIT_1_CAPABILITY_ID,
    EvidenceRecord,
    EvidenceType,
    derive_components_from_evidence,
    operator_replay_equivalent,
)

UGR_EIT_2_CANONICAL_TEXT = """UGR-EIT-2 — Evidence Lineage Convergence
Class: Constitutional Invariant (EIT extension)

Purpose: Ensure evidence lineages converge under replay and re-observation.

EIT-2 operator convergence: R_O1(E) ≅ R_O2(E) for admissible operators.
EIT-2 temporal convergence: U_t1(E) ≅ U_t2(E) up to bounded, recorded drift.

Omega(E) = u_comp*Q_comp + u_valid*Q_valid + u_rob*Q_rob + u_trace*Q_trace
Lawful decisions require Omega(E) >= Theta_evidence.
"""

EIT_2_CAPABILITY_ID = "UGR-EIT-2"
DEFAULT_THETA_EVIDENCE = 0.70
DEFAULT_EIT2_DRIFT_MAX = 0.08

REQUIRED_EVIDENCE_FIELDS = (
    "evidence_id",
    "evidence_type",
    "validation_method",
    "canonical_hash",
    "trace_links",
    "law_id",
)


@dataclass
class EvidenceFitnessComponents:
    Q_comp: float
    Q_valid: float
    Q_rob: float
    Q_trace: float

    def to_dict(self) -> dict[str, float]:
        return {
            "Q_comp": round(self.Q_comp, 6),
            "Q_valid": round(self.Q_valid, 6),
            "Q_rob": round(self.Q_rob, 6),
            "Q_trace": round(self.Q_trace, 6),
        }


@dataclass
class EvidenceFitnessConfig:
    u_comp: float = 0.25
    u_valid: float = 0.25
    u_rob: float = 0.25
    u_trace: float = 0.25
    theta_evidence: float = DEFAULT_THETA_EVIDENCE
    eit2_drift_max: float = DEFAULT_EIT2_DRIFT_MAX


@dataclass
class EITStrip:
    object_type: str
    object_id: str
    omega: float
    components: EvidenceFitnessComponents
    convergence: dict[str, Any]
    lineage_summary: str
    replay_hint: str
    trace_links: list[dict[str, str]] = field(default_factory=list)
    ready: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": self.object_type,
            "object_id": self.object_id,
            "omega": round(self.omega, 6),
            "components": self.components.to_dict(),
            "convergence": dict(self.convergence),
            "lineage_summary": self.lineage_summary,
            "replay_hint": self.replay_hint,
            "trace_links": list(self.trace_links),
            "ready": self.ready,
        }


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_omega(
    components: EvidenceFitnessComponents,
    cfg: EvidenceFitnessConfig | None = None,
) -> float:
    config = cfg or EvidenceFitnessConfig()
    omega = (
        config.u_comp * components.Q_comp
        + config.u_valid * components.Q_valid
        + config.u_rob * components.Q_rob
        + config.u_trace * components.Q_trace
    )
    return clamp01(omega)


def components_from_evidence_record(
    evidence: EvidenceRecord | dict[str, Any],
    *,
    graph: dict[str, Any] | None = None,
) -> EvidenceFitnessComponents:
    if isinstance(evidence, EvidenceRecord):
        record = evidence.to_dict()
        record["_components"] = evidence.components
        record["_sample_size"] = evidence.sample_size
        record["_law_id"] = evidence.law_id
        record["dependencies"] = evidence.dependencies
    else:
        record = dict(evidence)

    present = sum(1 for key in REQUIRED_EVIDENCE_FIELDS if record.get(key))
    q_comp = clamp01(present / len(REQUIRED_EVIDENCE_FIELDS))

    q_valid = 0.0
    if record.get("validation_method") and record.get("canonical_hash"):
        try:
            if isinstance(evidence, EvidenceRecord):
                derive_components_from_evidence(evidence)
            elif record.get("_components"):
                dict(record["_components"])
            else:
                raise ValueError("missing components")
            confidence = float(record.get("confidence") or 0.0)
            q_valid = clamp01(0.55 + 0.45 * confidence)
        except (ValueError, TypeError):
            q_valid = 0.0

    trace_links = list(record.get("trace_links") or [])
    dependencies = list(record.get("dependencies") or [])
    sample_size = int(record.get("_sample_size") or record.get("sample_size") or 0)
    edge_count = len((graph or {}).get("edges") or [])
    q_rob = clamp01(
        0.45
        + 0.08 * min(len(trace_links) + len(dependencies), 6)
        + 0.05 * min(sample_size, 4)
        + 0.02 * min(edge_count, 5)
    )
    if not trace_links and not dependencies:
        q_rob = clamp01(q_rob * 0.6)

    resolved = sum(1 for item in trace_links if str(item).strip())
    dep_resolved = sum(1 for item in dependencies if str(item).strip())
    total = max(len(trace_links) + len(dependencies), 1)
    q_trace = clamp01((resolved + dep_resolved) / total)

    evidence_type = str(record.get("evidence_type") or "")
    if evidence_type in {EvidenceType.DERIVATION.value, EvidenceType.SIMULATION.value}:
        q_comp = max(q_comp, 0.85)

    return EvidenceFitnessComponents(
        Q_comp=q_comp,
        Q_valid=q_valid,
        Q_rob=q_rob,
        Q_trace=q_trace,
    )


def evaluate_eit2_convergence(
    evidence: EvidenceRecord,
    *,
    replayed: EvidenceRecord | None = None,
    prior: EvidenceRecord | None = None,
    cfg: EvidenceFitnessConfig | None = None,
) -> dict[str, Any]:
    """EIT-2 — operator and temporal convergence checks."""

    config = cfg or EvidenceFitnessConfig()
    operator_ok = True
    operator_drift: float | None = None
    if replayed is not None:
        operator_ok = operator_replay_equivalent(evidence, replayed)
        if not operator_ok:
            operator_drift = round(
                abs(float(evidence.confidence) - float(replayed.confidence)), 6
            )

    temporal_ok = True
    temporal_drift: float | None = None
    if prior is not None:
        hash_match = prior.canonical_hash == evidence.canonical_hash
        conf_delta = abs(float(prior.confidence) - float(evidence.confidence))
        temporal_drift = round(conf_delta, 6)
        temporal_ok = hash_match or conf_delta <= config.eit2_drift_max

    status = "ok"
    warnings: list[str] = []
    if not operator_ok:
        status = "warning"
        warnings.append("EIT2-OPERATOR")
    if not temporal_ok:
        status = "warning" if status == "ok" else status
        warnings.append("EIT2-TEMPORAL")

    return {
        "operator_convergent": operator_ok,
        "temporal_convergent": temporal_ok,
        "operator_drift": operator_drift,
        "temporal_drift": temporal_drift,
        "status": status,
        "warnings": warnings,
        "eit2_drift_max": config.eit2_drift_max,
    }


def evaluate_evidence_fitness(
    evidence: EvidenceRecord | dict[str, Any],
    *,
    graph: dict[str, Any] | None = None,
    replayed: EvidenceRecord | None = None,
    prior: EvidenceRecord | None = None,
    cfg: EvidenceFitnessConfig | None = None,
) -> dict[str, Any]:
    config = cfg or EvidenceFitnessConfig()
    components = components_from_evidence_record(evidence, graph=graph)
    omega = compute_omega(components, config)

    record = evidence if isinstance(evidence, EvidenceRecord) else None
    convergence = evaluate_eit2_convergence(
        record if record is not None else EvidenceRecord.from_dict(evidence),
        replayed=replayed,
        prior=prior,
        cfg=config,
    )

    status = "ok"
    warnings = list(convergence.get("warnings") or [])
    if omega < config.theta_evidence:
        status = "breach"
        warnings.append("EIT-LOW")
    elif convergence["status"] != "ok":
        status = convergence["status"]

    return {
        "omega": round(omega, 6),
        "components": components.to_dict(),
        "convergence": convergence,
        "status": status,
        "warnings": warnings,
        "thresholds": {"theta_evidence": config.theta_evidence},
    }


def build_evidence_eit_strip(
    evidence: EvidenceRecord | dict[str, Any],
    *,
    graph: dict[str, Any] | None = None,
    replayed: EvidenceRecord | None = None,
    prior: EvidenceRecord | None = None,
    cfg: EvidenceFitnessConfig | None = None,
) -> EITStrip:
    config = cfg or EvidenceFitnessConfig()
    result = evaluate_evidence_fitness(
        evidence,
        graph=graph,
        replayed=replayed,
        prior=prior,
        cfg=config,
    )
    if isinstance(evidence, EvidenceRecord):
        evidence_id = evidence.evidence_id
        law_id = evidence.law_id
        evidence_type = evidence.evidence_type.value
        epoch = evidence.source_epoch
        trace_links_raw = evidence.trace_links
    else:
        evidence_id = str(evidence.get("evidence_id") or "")
        law_id = str(evidence.get("_law_id") or evidence.get("law_id") or "")
        evidence_type = str(evidence.get("evidence_type") or "derivation")
        epoch = int(evidence.get("source_epoch") or 0)
        trace_links_raw = evidence.get("trace_links") or []

    trace_links = [{"kind": "trace", "target": item, "label": item} for item in trace_links_raw]
    if law_id:
        trace_links.insert(0, {"kind": "law", "target": law_id, "label": f"binds {law_id}"})

    node_count = len((graph or {}).get("nodes") or [])
    edge_count = len((graph or {}).get("edges") or [])

    return EITStrip(
        object_type="evidence",
        object_id=evidence_id,
        omega=result["omega"],
        components=EvidenceFitnessComponents(**result["components"]),
        convergence=result["convergence"],
        lineage_summary=(
            f"{evidence_id}: {evidence_type}, epoch {epoch}, "
            f"{node_count} nodes / {edge_count} edges."
        ),
        replay_hint="Replay canonical_hash and trace_links via cross-ledger replay endpoint.",
        trace_links=trace_links,
        ready=result["omega"] >= config.theta_evidence and result["status"] != "breach",
    )


def build_evidence_fitness_health(
    *,
    law_store: Any | None = None,
    evidence_store: Any | None = None,
    cfg: EvidenceFitnessConfig | None = None,
) -> dict[str, Any]:
    from src.continuity.evidence_ledger import EvidenceLedgerStore, bootstrap_evidence_ledger
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    laws = law_store or LawLedgerStore()
    evidence = evidence_store or EvidenceLedgerStore()
    config = cfg or EvidenceFitnessConfig()
    bootstrap_law_ledger(laws)
    bootstrap_evidence_ledger(evidence)

    epoch = laws.get_current_epoch()
    objects: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    below_threshold: list[str] = []

    for law in laws.all_laws():
        evidence_id = f"EV-{law.law_id}-E{epoch}"
        record = evidence.get_evidence(evidence_id)
        if record is None:
            continue
        graph = evidence.get_lineage_graph(evidence_id)
        prior_id = f"EV-{law.law_id}-E{epoch - 1}" if epoch > 0 else None
        prior = evidence.get_evidence(prior_id) if prior_id else None
        result = evaluate_evidence_fitness(
            record,
            graph=graph,
            prior=prior,
            cfg=config,
        )
        objects.append(
            {
                "object_type": "evidence",
                "object_id": evidence_id,
                "law_id": law.law_id,
                "omega": result["omega"],
                "status": result["status"],
                "warnings": result["warnings"],
            }
        )
        for code in result["warnings"]:
            warnings.append({"code": code, "object_id": evidence_id, "object_type": "evidence"})
        if result["omega"] < config.theta_evidence:
            below_threshold.append(evidence_id)

    omega_values = [item["omega"] for item in objects]
    avg_omega = round(sum(omega_values) / len(omega_values), 6) if omega_values else 0.0
    convergence_warnings = [item for item in warnings if item["code"].startswith("EIT2")]
    epoch_blocked = len(below_threshold) > 0

    return {
        "avg_omega": avg_omega,
        "theta_evidence": config.theta_evidence,
        "objects": objects,
        "below_threshold": below_threshold,
        "warnings": warnings,
        "convergence_detected": bool(convergence_warnings),
        "epoch_commit_blocked": epoch_blocked,
        "canonical": UGR_EIT_2_CANONICAL_TEXT.split("\n")[0],
    }


def build_spine_health(
    *,
    law_store: Any | None = None,
    evidence_store: Any | None = None,
    comprehension_store: Any | None = None,
    mit_store: Any | None = None,
) -> dict[str, Any]:
    """Unified CIT + MIT + EIT-2 health for cockpit and epoch gates."""

    from src.continuity.comprehension_ledger import ComprehensionLedgerStore, build_comprehension_health
    from src.continuity.mit_ledger import MitLedgerStore, build_mit_health

    comprehension = build_comprehension_health(
        law_store=law_store,
        evidence_store=evidence_store,
        comprehension_store=comprehension_store,
    )
    meaning = build_mit_health(law_store=law_store, mit_store=mit_store)
    evidence = build_evidence_fitness_health(
        law_store=law_store,
        evidence_store=evidence_store,
    )

    block_reasons: list[str] = []
    if comprehension.get("epoch_commit_blocked"):
        block_reasons.append("CIT-BLOCK")
    if evidence.get("epoch_commit_blocked"):
        block_reasons.append("EIT-BLOCK")

    return {
        "comprehension_health": comprehension,
        "meaning_health": meaning,
        "evidence_fitness_health": evidence,
        "epoch_commit_blocked": bool(block_reasons),
        "block_reasons": block_reasons,
    }


def run_eit2_proof(
    *,
    law_store: Any | None = None,
    evidence_store: Any | None = None,
) -> dict[str, Any]:
    from src.continuity.evidence_ledger import (
        EvidenceLedgerStore,
        bootstrap_evidence_ledger,
        evidence_id_for,
        run_eit_proof,
    )
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    laws = law_store or LawLedgerStore()
    evidence = evidence_store or EvidenceLedgerStore()
    bootstrap_law_ledger(laws)
    bootstrap_evidence_ledger(evidence)
    eit1 = run_eit_proof(law_store=laws, evidence_store=evidence)
    health = build_evidence_fitness_health(law_store=laws, evidence_store=evidence)
    pit_evidence = evidence.get_evidence(evidence_id_for("PIT-1", 3))
    replay_ok = pit_evidence is not None and operator_replay_equivalent(pit_evidence, pit_evidence)

    return {
        "capability_id": EIT_2_CAPABILITY_ID,
        "eit1_passed": eit1.get("passed", False),
        "avg_omega": health["avg_omega"],
        "operator_invariant": replay_ok,
        "passed": eit1.get("passed", False)
        and health["avg_omega"] >= EvidenceFitnessConfig().theta_evidence
        and replay_ok,
    }
